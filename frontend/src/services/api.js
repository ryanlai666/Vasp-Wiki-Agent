import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const queryAPI = async (query, topK = null) => {
  try {
    const response = await apiClient.post('/api/query', {
      query,
      top_k: topK,
    });
    return response.data;
  } catch (error) {
    if (error.response) {
      throw new Error(error.response.data.detail || 'Error querying API');
    } else if (error.request) {
      throw new Error('No response from server. Is the backend running?');
    } else {
      throw new Error(error.message || 'Unknown error');
    }
  }
};

export const healthCheck = async () => {
  try {
    const response = await apiClient.get('/api/health');
    return response.data;
  } catch (error) {
    throw new Error('Health check failed');
  }
};

export default apiClient;
