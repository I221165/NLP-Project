/**
 * Analytics Page - Weakness tracking and progress stats
 */
import { useState, useEffect } from 'react';
import Layout from '../components/Layout';
import { analytics } from '../api/client';

function AnalyticsPage() {
    const [weaknesses, setWeaknesses] = useState([]);
    const [progress, setProgress] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadAnalytics();
    }, []);

    const loadAnalytics = async () => {
        try {
            const [weaknessRes, progressRes] = await Promise.all([
                analytics.getWeaknesses(),
                analytics.getProgress(),
            ]);
            setWeaknesses(weaknessRes.data);
            setProgress(progressRes.data);
        } catch (error) {
            console.error('Failed to load analytics:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <Layout>
                <div className="text-center py-12">
                    <div className="text-4xl mb-4">📊</div>
                    <p className="text-neutral-600">Loading analytics...</p>
                </div>
            </Layout>
        );
    }

    return (
        <Layout>
            <div>
                <h2 className="text-3xl font-bold mb-8">Your Analytics</h2>

                {/* Progress Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="card bg-gradient-to-br from-blue-500 to-blue-600 text-white">
                        <p className="text-sm opacity-90 mb-1">Total Quizzes</p>
                        <p className="text-4xl font-bold">{progress?.total_quizzes || 0}</p>
                    </div>
                    <div className="card bg-gradient-to-br from-green-500 to-green-600 text-white">
                        <p className="text-sm opacity-90 mb-1">Average Score</p>
                        <p className="text-4xl font-bold">{Math.round(progress?.average_score || 0)}%</p>
                    </div>
                    <div className="card bg-gradient-to-br from-purple-500 to-purple-600 text-white">
                        <p className="text-sm opacity-90 mb-1">Total PDFs</p>
                        <p className="text-4xl font-bold">{progress?.total_pdfs || 0}</p>
                    </div>
                </div>

                {/* Weak Concepts */}
                <div className="card">
                    <h3 className="text-2xl font-semibold mb-6">Concepts to Review</h3>

                    {weaknesses.length === 0 ? (
                        <div className="text-center py-8 text-neutral-600">
                            <div className="text-4xl mb-4">🎉</div>
                            <p>No weak concepts identified yet!</p>
                            <p className="text-sm">Take some quizzes to get personalized recommendations</p>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {weaknesses.map((weakness, idx) => (
                                <div
                                    key={idx}
                                    className="flex items-center justify-between p-4 bg-neutral-50 rounded-lg"
                                >
                                    <div className="flex-1">
                                        <p className="font-semibold text-lg">{weakness.concept}</p>
                                        <p className="text-sm text-neutral-600">
                                            Last incorrect: {new Date(weakness.last_incorrect).toLocaleDateString()}
                                        </p>
                                    </div>
                                    <div className="text-right">
                                        <div className="inline-flex items-center gap-2 px-4 py-2 bg-error/10 rounded-full">
                                            <span className="text-error font-semibold">{weakness.frequency}</span>
                                            <span className="text-error text-sm">times wrong</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Study Recommendations */}
                {weaknesses.length > 0 && (
                    <div className="mt-6 card bg-primary/5 border-2 border-primary">
                        <h4 className="font-semibold text-primary mb-3">💡 Study Recommendations</h4>
                        <ul className="space-y-2 text-neutral-700">
                            <li>• Focus on: <strong>{weaknesses[0]?.concept}</strong> (most frequent weakness)</li>
                            <li>• Review related PDFs and take targeted quizzes</li>
                            <li>• Use the chat feature to ask specific questions</li>
                        </ul>
                    </div>
                )}
            </div>
        </Layout>
    );
}

export default AnalyticsPage;
