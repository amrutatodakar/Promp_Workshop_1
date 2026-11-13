import axios from 'axios';

// VITE_API_URL must be set in Vercel project settings to https://promp-workshop-1.onrender.com
// For local development it falls back to localhost:8000
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 60000, // 60s timeout for large multi-page OCR + Gemini processing
});

export const checkHealth = async () => {
  const response = await client.get('/api/health');
  return response.data;
};

export const extractReport = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  // Do NOT manually set Content-Type — axios sets it automatically with the
  // correct multipart boundary when FormData is passed. Setting it manually
  // strips the boundary and causes the backend to reject the upload.
  const response = await client.post('/api/reports/extract', formData);
  return response.data;
};

export const analyzeReport = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  // Do NOT manually set Content-Type — same reason as above.
  const response = await client.post('/api/reports/analyze', formData);
  return response.data;
};

export default {
  checkHealth,
  extractReport,
  analyzeReport,
};
