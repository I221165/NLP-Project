/**
 * Quiz Page - Generate and take quizzes
 */
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Layout from '../components/Layout';
import { quiz as quizApi, pdf } from '../api/client';

function QuizPage() {
    const { pdfId } = useParams();
    const navigate = useNavigate();
    const [pdfs, setPdfs] = useState([]);
    const [selectedPdf, setSelectedPdf] = useState(pdfId || '');
    const [topic, setTopic] = useState('');
    const [numQuestions, setNumQuestions] = useState(5);
    const [quiz, setQuiz] = useState(null);
    const [userAnswers, setUserAnswers] = useState({});
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);

    useEffect(() => {
        loadPdfs();
    }, []);

    const loadPdfs = async () => {
        try {
            const response = await pdf.list();
            setPdfs(response.data);
        } catch (error) {
            console.error('Failed to load PDFs:', error);
        }
    };

    const handleGenerate = async (e) => {
        e.preventDefault();
        setLoading(true);
        setResult(null);

        try {
            const response = await quizApi.generate(selectedPdf, topic, numQuestions);
            setQuiz(response.data);
            setUserAnswers({});
        } catch (error) {
            alert('Failed to generate quiz: ' + (error.response?.data?.detail || error.message));
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async () => {
        setLoading(true);
        try {
            const response = await quizApi.submit(quiz.quiz_id, userAnswers);
            setResult(response.data);
        } catch (error) {
            alert('Failed to submit quiz: ' + error.message);
        } finally {
            setLoading(false);
        }
    };

    const handleAnswerSelect = (questionId, answer) => {
        setUserAnswers((prev) => ({
            ...prev,
            [questionId]: answer,
        }));
    };

    return (
        <Layout>
            <div className="max-w-4xl mx-auto">
                <h2 className="text-3xl font-bold mb-6">Quiz Generator</h2>

                {!quiz ? (
                    /* Quiz Generation Form */
                    <div className="card">
                        <form onSubmit={handleGenerate} className="space-y-4">
                            <div>
                                <label className="block text-sm font-semibold mb-2">Select PDF</label>
                                <select
                                    value={selectedPdf}
                                    onChange={(e) => setSelectedPdf(e.target.value)}
                                    required
                                    className="input-field"
                                >
                                    <option value="">Choose a PDF...</option>
                                    {pdfs.map((p) => (
                                        <option key={p.id} value={p.id}>
                                            {p.filename}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            <div>
                                <label className="block text-sm font-semibold mb-2">Topic</label>
                                <input
                                    type="text"
                                    value={topic}
                                    onChange={(e) => setTopic(e.target.value)}
                                    required
                                    className="input-field"
                                    placeholder="e.g., Machine Learning basics"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-semibold mb-2">Number of Questions</label>
                                <input
                                    type="number"
                                    min="1"
                                    max="10"
                                    value={numQuestions}
                                    onChange={(e) => setNumQuestions(parseInt(e.target.value))}
                                    className="input-field"
                                />
                            </div>

                            <button type="submit" disabled={loading} className="btn-primary w-full">
                                {loading ? 'Generating...' : '🎯 Generate Quiz'}
                            </button>
                        </form>
                    </div>
                ) : !result ? (
                    /* Quiz Questions */
                    <div className="space-y-6">
                        <div className="card bg-primary text-white">
                            <h3 className="text-xl font-bold mb-2">{quiz.topic}</h3>
                            <p>{quiz.questions.length} questions</p>
                        </div>

                        {quiz.questions.map((q, idx) => (
                            <div key={q.id} className="card">
                                <p className="font-semibold mb-4">
                                    {idx + 1}. {q.question}
                                </p>
                                <div className="space-y-2">
                                    {q.options.map((option, optIdx) => (
                                        <label
                                            key={optIdx}
                                            className={`block p-3 border-2 rounded-lg cursor-pointer transition-all ${userAnswers[q.id] === option
                                                    ? 'border-primary bg-primary/10'
                                                    : 'border-neutral-200 hover:border-primary/50'
                                                }`}
                                        >
                                            <input
                                                type="radio"
                                                name={`question-${q.id}`}
                                                value={option}
                                                checked={userAnswers[q.id] === option}
                                                onChange={() => handleAnswerSelect(q.id, option)}
                                                className="mr-3"
                                            />
                                            {option}
                                        </label>
                                    ))}
                                </div>
                            </div>
                        ))}

                        <div className="flex gap-4">
                            <button onClick={() => setQuiz(null)} className="btn-secondary flex-1">
                                Cancel
                            </button>
                            <button
                                onClick={handleSubmit}
                                disabled={Object.keys(userAnswers).length !== quiz.questions.length || loading}
                                className="btn-primary flex-1"
                            >
                                {loading ? 'Submitting...' : 'Submit Quiz'}
                            </button>
                        </div>
                    </div>
                ) : (
                    /* Quiz Results */
                    <div className="space-y-6">
                        <div className={`card text-white ${result.score >= 70 ? 'bg-success' : 'bg-error'}`}>
                            <h3 className="text-3xl font-bold mb-2">{Math.round(result.score)}%</h3>
                            <p>
                                {result.correct_answers} / {result.total_questions} correct
                            </p>
                        </div>

                        {result.weak_concepts && result.weak_concepts.length > 0 && (
                            <div className="card">
                                <h4 className="font-semibold mb-3">Areas to Review:</h4>
                                <div className="flex flex-wrap gap-2">
                                    {result.weak_concepts.map((concept, idx) => (
                                        <span key={idx} className="badge-pill bg-error/10 text-error">
                                            {concept}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}

                        <button
                            onClick={() => {
                                setQuiz(null);
                                setResult(null);
                                setUserAnswers({});
                            }}
                            className="btn-primary w-full"
                        >
                            Take Another Quiz
                        </button>
                    </div>
                )}
            </div>
        </Layout>
    );
}

export default QuizPage;
