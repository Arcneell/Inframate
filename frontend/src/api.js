import axios from 'axios';

const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: apiUrl
});

// Request interceptor: Attach Token
api.interceptors.request.use(
    config => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
    },
    error => Promise.reject(error)
);

// Response interceptor: Handle 401
api.interceptors.response.use(
    response => response,
    error => {
        // If 401 Unauthorized
        if (error.response && error.response.status === 401) {
            // Only redirect if we are not already on the login page to avoid loops
            if (!window.location.pathname.includes('/login')) {
                localStorage.removeItem('token');
                localStorage.removeItem('username');
                localStorage.removeItem('user');
                window.location.href = '/login';
            }
        }
        return Promise.reject(error);
    }
);

export default api;