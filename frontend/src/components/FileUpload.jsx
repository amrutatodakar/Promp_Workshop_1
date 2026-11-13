import React, { useState, useRef } from 'react';
import { Upload, FileText, Image as ImageIcon, ShieldCheck, Sparkles, AlertCircle } from 'lucide-react';
import { generateSampleReportFile } from '../utils/sampleReport';

export default function FileUpload({ onFileSelect, isAnalyzing }) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const validateAndSelect = (file) => {
    setError(null);
    if (!file) return;

    const validTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg'];
    const validExts = ['.pdf', '.jpg', '.jpeg', '.png'];
    const lowerName = file.name.toLowerCase();

    const isValidType = validTypes.includes(file.type) || validExts.some((ext) => lowerName.endsWith(ext));

    if (!isValidType) {
      setError('Unsupported file type. Please upload a PDF, PNG, JPG, or JPEG file.');
      return;
    }

    if (file.size > 15 * 1024 * 1024) {
      setError('File size exceeds the 15MB limit. Please upload a smaller file.');
      return;
    }

    onFileSelect(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSelect(e.dataTransfer.files[0]);
    }
  };

  const handleQuickSample = async () => {
    setError(null);
    try {
      const sampleFile = await generateSampleReportFile();
      onFileSelect(sampleFile);
    } catch (err) {
      setError('Could not generate sample report.');
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto space-y-4">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isAnalyzing && fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-3xl p-8 sm:p-12 text-center cursor-pointer transition-all duration-200 ${
          isDragging
            ? 'border-teal-500 bg-teal-50/70 scale-[1.01]'
            : 'border-slate-300 hover:border-teal-400 bg-white/70 hover:bg-teal-50/20'
        } shadow-sm backdrop-blur-sm`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg"
          className="hidden"
          onChange={(e) => e.target.files && validateAndSelect(e.target.files[0])}
          disabled={isAnalyzing}
        />

        <div className="flex flex-col items-center justify-center space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-teal-500 to-emerald-400 flex items-center justify-center text-white shadow-md shadow-teal-500/20">
            <Upload className="w-8 h-8 animate-bounce" />
          </div>

          <div className="space-y-1">
            <h3 className="text-lg font-bold text-slate-800">
              Drag & Drop your Lab Report here
            </h3>
            <p className="text-xs sm:text-sm text-slate-500">
              or <span className="text-teal-700 font-semibold underline">browse from your device</span>
            </p>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-2 pt-2 text-xs text-slate-500">
            <span className="flex items-center space-x-1 px-2.5 py-1 rounded-full bg-slate-100 border border-slate-200 font-medium">
              <FileText className="w-3.5 h-3.5 text-red-500" />
              <span>PDF (Digital & Scans)</span>
            </span>
            <span className="flex items-center space-x-1 px-2.5 py-1 rounded-full bg-slate-100 border border-slate-200 font-medium">
              <ImageIcon className="w-3.5 h-3.5 text-blue-500" />
              <span>PNG, JPG, JPEG</span>
            </span>
            <span className="px-2.5 py-1 rounded-full bg-slate-100 border border-slate-200 font-medium">
              Max 15MB
            </span>
          </div>

          <div className="pt-2 flex items-center space-x-2 text-xs text-slate-400">
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span>Automatic patient privacy masking applied before AI processing</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Instant Demo Option */}
      <div className="flex items-center justify-center space-x-2 pt-2">
        <span className="text-xs text-slate-500">Don't have a report on hand?</span>
        <button
          type="button"
          onClick={handleQuickSample}
          disabled={isAnalyzing}
          className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs font-semibold text-teal-800 bg-teal-100/70 hover:bg-teal-200/70 rounded-full transition-colors disabled:opacity-50"
        >
          <Sparkles className="w-3.5 h-3.5 text-teal-700" />
          <span>Try Synthetic Demo Report</span>
        </button>
      </div>
    </div>
  );
}
