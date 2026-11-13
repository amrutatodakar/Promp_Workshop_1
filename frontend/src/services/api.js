import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 45000, // 45s timeout for large multi-page OCR
});

export const checkHealth = async () => {
  const response = await client.get('/api/health');
  return response.data;
};

export const extractReport = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await client.post('/api/reports/extract', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const analyzeReport = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await client.post('/api/reports/analyze', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export default {
  checkHealth,
  extractReport,
  analyzeReport,
};
