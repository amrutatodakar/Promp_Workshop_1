import React, { useState, useEffect } from 'react';
import { Activity, CheckCircle2, AlertTriangle, RefreshCw, Cpu, Server, FileText } from 'lucide-react';
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function HealthStatus() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const checkHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE}/api/health`, { timeout: 4000 });
      setHealth(response.data);
    } catch (err) {
      console.error('Failed to reach backend:', err);
      setError(err.message || 'Cannot reach backend server');
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 max-w-2xl mx-auto">
      <div className="flex items-center justify-between pb-4 border-b border-slate-100">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-lg bg-teal-50 text-teal-700">
            <Activity className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900">System Connectivity Check</h2>
            <p className="text-xs text-slate-500">Testing communication between React frontend and FastAPI backend</p>
          </div>
        </div>
        <button
          onClick={checkHealth}
          disabled={loading}
          className="flex items-center space-x-1 px-3 py-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Test Ping</span>
        </button>
      </div>

      <div className="mt-4">
        {loading && !health ? (
          <div className="py-8 flex flex-col items-center justify-center space-y-2 text-slate-400">
            <RefreshCw className="w-6 h-6 animate-spin text-teal-600" />
            <span className="text-xs">Connecting to {API_BASE}/api/health...</span>
          </div>
        ) : error ? (
          <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-800">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold">Backend Unreachable</p>
                <p className="text-xs text-amber-700 mt-0.5">
                  Could not reach <code className="bg-amber-100 px-1 py-0.5 rounded">{API_BASE}</code>. Make sure the FastAPI backend is running.
                </p>
                <p className="text-xs text-amber-600 mt-2 font-mono">{error}</p>
              </div>
            </div>
          </div>
        ) : health ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 rounded-xl bg-emerald-50 border border-emerald-200/80">
              <div className="flex items-center space-x-2.5">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                <div>
                  <span className="text-sm font-semibold text-emerald-900">FastAPI Backend Connected</span>
                  <p className="text-xs text-emerald-700">Environment: {health.environment} | Version: {health.version}</p>
                </div>
              </div>
              <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-200 text-emerald-800 uppercase tracking-wider">
                {health.status}
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Server className="w-4 h-4 text-slate-500" />
                  <span className="text-xs font-medium text-slate-700">API Gateway</span>
                </div>
                <span className="text-xs font-semibold text-emerald-600 uppercase">
                  {health.services?.api}
                </span>
              </div>

              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Cpu className="w-4 h-4 text-slate-500" />
                  <span className="text-xs font-medium text-slate-700">Tesseract OCR</span>
                </div>
                <span className={`text-xs font-semibold uppercase ${health.services?.tesseract_ocr === 'available' ? 'text-emerald-600' : 'text-amber-600'}`}>
                  {health.services?.tesseract_ocr}
                </span>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
