/**
 * API Client with Axios - Handles all backend communication
 */
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

// Create axios instance
const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

// Handle 401 errors (redirect to login)
apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
            window.location.href = '/login';
        }
        return Promise.reject(error);
    }
);

// Auth API
export const auth = {
    register: (email, password) =>
        apiClient.post('/auth/register', { email, password }),

    login: (email, password) =>
        apiClient.post('/auth/login', { email, password }),

    getMe: () =>
        apiClient.get('/auth/me'),
};

// PDF API
export const pdf = {
    upload: (file) => {
        const formData = new FormData();
        formData.append('file', file);
        return apiClient.post('/pdf/upload', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
    },

    list: () =>
        apiClient.get('/pdf/list'),

    summarize: (pdfId) =>
        apiClient.post(`/pdf/summarize/${pdfId}`),

    delete: (pdfId) =>
        apiClient.delete(`/pdf/${pdfId}`),
};

// Chat API
export const chat = {
    ask: (pdfId, question) =>
        apiClient.post('/chat/ask', { pdf_id: pdfId, question }),

    getHistory: (pdfId) =>
        apiClient.get(`/chat/history/${pdfId}`),

    clearChat: (chatId) =>
        apiClient.delete(`/chat/${chatId}`),
};

// Quiz API
export const quiz = {
    generate: (pdfId, topic, numQuestions = 5) =>
        apiClient.post('/quiz/generate', {
            pdf_id: pdfId,
            topic,
            num_questions: numQuestions,
        }),

    submit: (quizId, userAnswers) =>
        apiClient.post('/quiz/submit', {
            quiz_id: quizId,
            user_answers: userAnswers,
        }),

    getHistory: () =>
        apiClient.get('/quiz/history'),
};

// Analytics API
export const analytics = {
    getWeaknesses: () =>
        apiClient.get('/analytics/weaknesses'),

    getProgress: () =>
        apiClient.get('/analytics/progress'),
};

export default apiClient;
