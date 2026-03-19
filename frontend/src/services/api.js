import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (credentials) => api.post('/auth/login/', credentials),
  register: (userData) => api.post('/auth/register/', userData),
  logout: () => api.post('/auth/logout/'),
  getCurrentUser: () => api.get('/auth/me/'),
  getProfile: () => api.get('/auth/profile/'),
  updateProfile: (data) => api.put('/auth/profile/', data),
};

// Resume API
export const resumeAPI = {
  upload: (formData) => api.post('/resumes/upload/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }),
  getList: () => api.get('/resumes/'),
  getDetail: (id) => api.get(`/resumes/${id}/`),
  delete: (id) => api.delete(`/resumes/${id}/`),
  getAnalysis: (id) => api.get(`/resumes/${id}/analysis/`),
  reprocess: (id) => api.post(`/resumes/${id}/reprocess/`),
  getSkillProfile: () => api.get('/resumes/skill-profile/'),
  updateSkillProfile: (data) => api.put('/resumes/skill-profile/', data),
  getSkillGapAnalysis: (jobId) => api.get(`/resumes/skill-gap/?job_id=${jobId}`),
};

// Jobs API
export const jobsAPI = {
  getList: (params) => api.get('/jobs/', { params }),
  getDetail: (id) => api.get(`/jobs/${id}/`),
  create: (data) => api.post('/jobs/create/', data),
  update: (id, data) => api.put(`/jobs/${id}/update/`, data),
  delete: (id) => api.delete(`/jobs/${id}/delete/`),
  getRecommendations: () => api.get('/jobs/dynamic-recommendations/'),
  getRecommendedJobs: () => api.get('/ml/recommended-jobs/'),
  getMyPostedJobs: () => api.get('/jobs/my-posted/'),
  rankCandidates: (jobId, threshold) => api.post(`/jobs/${jobId}/rank-candidates/`, { threshold }),
  getCategories: () => api.get('/jobs/categories/'),
  getSkills: () => api.get('/jobs/skills/'),
};

// Applications API
export const applicationsAPI = {
  getList: (params) => api.get('/applications/', { params }),
  create: (data) => api.post('/applications/create/', data),
  getDetail: (id) => api.get(`/applications/${id}/`),
  update: (id, data) => api.put(`/applications/${id}/`, data),
  delete: (id) => api.delete(`/applications/${id}/`),
  changeStatus: (id, status, notes) => api.post(`/applications/${id}/status/`, { status, notes }),
  withdraw: (id) => api.post(`/applications/${id}/withdraw/`),
  getDocuments: (applicationId) => api.get(`/applications/${applicationId}/documents/`),
  uploadDocument: (applicationId, formData) => api.post(`/applications/${applicationId}/documents/`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }),
  getInterview: (applicationId) => api.get(`/applications/${applicationId}/interview/`),
  updateInterview: (applicationId, data) => api.put(`/applications/${applicationId}/interview/`, data),
  confirmInterview: (applicationId) => api.post(`/applications/${applicationId}/interview/confirm/`),
  getFeedback: (applicationId) => api.get(`/applications/${applicationId}/feedback/`),
  addFeedback: (applicationId, data) => api.post(`/applications/${applicationId}/feedback/`, data),
  getStatistics: () => api.get('/applications/statistics/'),
};

// ML Engine API
export const mlAPI = {
  extractSkills: (data) => api.post('/ml/extract-skills/', data),
  calculateMatch: (data) => api.post('/ml/calculate-match/', data),
  getRecommendations: (type) => api.get(`/ml/recommendations/?type=${type}`),
  getUpskillingSuggestions: () => api.get('/ml/upskilling/'),
  markSuggestionCompleted: (id, data) => api.post(`/ml/upskilling/${id}/complete/`, data),
  getAnalytics: () => api.get('/ml/analytics/'),
  getModels: () => api.get('/ml/models/'),
  getTrainingLogs: (modelId) => api.get(`/ml/training-logs/?model_id=${modelId}`),
};

export default api;
