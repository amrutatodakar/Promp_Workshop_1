import React, { useState } from 'react';
import Navbar from './components/Navbar';
import FileUpload from './components/FileUpload';
import ReportView from './components/ReportView';
import HealthStatus from './components/HealthStatus';
import { analyzeReport } from './services/api';
import {
  ShieldAlert,
  Sparkles,
  FileCheck,
  ShieldCheck,
  Stethoscope,
  RefreshCw,
  AlertCircle,
  FileSearch,
  BrainCircuit
} from 'lucide-react';

export default function App() {
  const [status, setStatus] = useState('idle'); // idle | analyzing | complete | error
  const [analysis, setAnalysis] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [progressStage, setProgressStage] = useState('Processing document...');

  const handleFileSelect = async (file) => {
    setStatus('analyzing');
    setErrorMessage(null);
    setProgressStage('Uploading and reading document...');

    try {
      setTimeout(() => setProgressStage('Extracting tables and running OCR...'), 800);
      setTimeout(() => setProgressStage('Scrubbing patient names & personal identifiers...'), 1800);
      setTimeout(() => setProgressStage('Translating medical findings with Gemini AI...'), 2800);

      const result = await analyzeReport(file);
      setAnalysis(result);
      setStatus('complete');
    } catch (err) {
      console.error('Analysis failed:', err);
      setStatus('error');
      const detail = err.response?.data?.detail || err.message || 'Failed to analyze report';
      setErrorMessage(detail);
    }
  };

  const handleReset = () => {
    setStatus('idle');
    setAnalysis(null);
    setErrorMessage(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-teal-50/20 to-slate-50 flex flex-col font-sans text-slate-800">
      <Navbar />

      <main className="flex-1 max-w-5xl mx-auto px-4 py-8 w-full space-y-8">
        {status === 'idle' && (
          <div className="space-y-8 animate-fade-in">
            {/* Hero Section */}
            <div className="text-center space-y-3 max-w-2xl mx-auto pt-4">
              <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-teal-100/70 text-teal-800 text-xs font-semibold">
                <Sparkles className="w-3.5 h-3.5" />
                <span>AI-Powered Medical Report Companion</span>
              </div>
              <h1 className="text-3xl sm:text-5xl font-extrabold text-slate-900 tracking-tight leading-tight">
                Understand Your Lab Reports in <span className="text-teal-700">Simple English</span>
              </h1>
              <p className="text-sm sm:text-base text-slate-600 leading-relaxed">
                ReportSaathi translates confusing laboratory jargon, highlights values that need doctor review, and prepares meaningful questions for your next appointment.
              </p>
            </div>

            {/* Medical Advisory Banner */}
            <div className="p-4 rounded-2xl bg-amber-50/90 border border-amber-200/90 text-amber-900 max-w-3xl mx-auto shadow-sm">
              <div className="flex items-start space-x-3">
                <ShieldAlert className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                <div className="text-xs leading-relaxed">
                  <strong className="font-semibold text-amber-950">Educational Disclaimer: </strong>
                  ReportSaathi is built for patient health literacy only. It does not offer medical diagnoses or treatment plans. Always review your laboratory report with a qualified physician.
                </div>
              </div>
            </div>

            {/* File Upload Zone */}
            <section>
              <FileUpload onFileSelect={handleFileSelect} isAnalyzing={false} />
            </section>

            {/* Features Highlight */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mx-auto pt-6">
              <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-2">
                <div className="w-9 h-9 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center">
                  <FileCheck className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-bold text-slate-900">PDFs & Scanned Images</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Extracts structured tables from digital PDFs, and uses Tesseract OCR for scanned copies, PNG, JPG, and JPEG.
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-2">
                <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-700 flex items-center justify-center">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-bold text-slate-900">Patient Privacy First</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Automatically sanitizes patient names, contact numbers, and identifiers before AI processing.
                </p>
              </div>

              <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-2">
                <div className="w-9 h-9 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center">
                  <Stethoscope className="w-5 h-5" />
                </div>
                <h3 className="text-sm font-bold text-slate-900">Doctor-Aligned Questions</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Generates practical, targeted questions for your doctor instead of giving diagnostic claims.
                </p>
              </div>
            </div>

            {/* System Status Drawer */}
            <div className="pt-6">
              <HealthStatus />
            </div>
          </div>
        )}

        {status === 'analyzing' && (
          <div className="py-20 flex flex-col items-center justify-center space-y-6 text-center max-w-md mx-auto">
            <div className="relative">
              <div className="w-20 h-20 rounded-3xl bg-teal-100 flex items-center justify-center text-teal-700 animate-pulse">
                <BrainCircuit className="w-10 h-10 animate-spin" />
              </div>
            </div>

            <div className="space-y-2">
              <h3 className="text-xl font-bold text-slate-900">Analyzing Your Lab Report</h3>
              <p className="text-sm text-teal-700 font-medium">{progressStage}</p>
              <p className="text-xs text-slate-400">
                This takes a few seconds while OCR and privacy sanitization run.
              </p>
            </div>
          </div>
        )}

        {status === 'error' && (
          <div className="py-12 max-w-xl mx-auto space-y-6 text-center">
            <div className="p-6 rounded-3xl bg-red-50 border border-red-200 text-red-900 space-y-3 shadow-sm">
              <div className="w-12 h-12 rounded-2xl bg-red-100 text-red-600 flex items-center justify-center mx-auto">
                <AlertCircle className="w-6 h-6" />
              </div>
              <h3 className="text-base font-bold">Could Not Process Report</h3>
              <p className="text-xs text-red-700">{errorMessage}</p>
              <div className="pt-2">
                <button
                  onClick={handleReset}
                  className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white text-xs font-semibold shadow-sm transition-colors"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Try Again</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {status === 'complete' && analysis && (
          <ReportView analysis={analysis} onReset={handleReset} />
        )}
      </main>

      <footer className="py-6 border-t border-slate-200 text-center text-xs text-slate-500 bg-white/50">
        <p>ReportSaathi &copy; {new Date().getFullYear()} &bull; AI-Powered Patient Health Literacy Companion</p>
      </footer>
    </div>
  );
}
