import React, { useState } from 'react';
import {
  FileText,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  TrendingDown,
  HelpCircle,
  Stethoscope,
  Printer,
  Copy,
  RotateCcw,
  BookOpen,
  Info,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

export default function ReportView({ analysis, onReset }) {
  const [copied, setCopied] = useState(false);
  const [showRawText, setShowRawText] = useState(false);
  const [checkedQuestions, setCheckedQuestions] = useState({});

  const {
    extraction,
    summary,
    key_findings = [],
    parameters_explained = [],
    terminology_breakdown = [],
    questions_for_doctor = [],
    educational_notes = [],
    disclaimer,
    is_mock = false
  } = analysis;

  const handlePrint = () => {
    window.print();
  };

  const handleCopySummary = () => {
    const textToCopy = `REPORT SUMMARY:\n${summary}\n\nKEY FINDINGS:\n${key_findings.map(k => `• ${k}`).join('\n')}\n\nQUESTIONS FOR DOCTOR:\n${questions_for_doctor.map(q => `• ${q}`).join('\n')}`;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const toggleQuestion = (idx) => {
    setCheckedQuestions(prev => ({
      ...prev,
      [idx]: !prev[idx]
    }));
  };

  const getStatusBadge = (status) => {
    const s = (status || '').toLowerCase();
    if (s.includes('high')) {
      return (
        <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800 border border-amber-300">
          <TrendingUp className="w-3.5 h-3.5 text-amber-700" />
          <span>Higher than typical</span>
        </span>
      );
    }
    if (s.includes('low')) {
      return (
        <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-100 text-sky-800 border border-sky-300">
          <TrendingDown className="w-3.5 h-3.5 text-sky-700" />
          <span>Lower than typical</span>
        </span>
      );
    }
    if (s.includes('normal')) {
      return (
        <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700" />
          <span>Within range</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-800 border border-slate-300">
        <HelpCircle className="w-3.5 h-3.5 text-slate-600" />
        <span>{status || 'Needs Verification'}</span>
      </span>
    );
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto pb-16">
      {/* Top Action Bar (hidden in print) */}
      <div className="print:hidden flex flex-wrap items-center justify-between gap-3 bg-white p-4 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 bg-teal-50 rounded-xl text-teal-700">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900 truncate max-w-xs sm:max-w-md">
              {extraction.filename}
            </h2>
            <div className="flex items-center space-x-2 text-xs text-slate-500 pt-0.5">
              <span className="capitalize">{extraction.extraction_method.replace('_', ' ')}</span>
              <span>&bull;</span>
              <span>{extraction.total_pages} page(s)</span>
              <span>&bull;</span>
              <span className="text-emerald-700 font-medium flex items-center space-x-1">
                <ShieldCheck className="w-3.5 h-3.5 inline" />
                <span>PII Sanitized</span>
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleCopySummary}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-medium transition-colors"
          >
            <Copy className="w-3.5 h-3.5" />
            <span>{copied ? 'Copied!' : 'Copy Summary'}</span>
          </button>
          <button
            onClick={handlePrint}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-medium transition-colors"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print Report</span>
          </button>
          <button
            onClick={onReset}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-medium shadow-sm transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>New Report</span>
          </button>
        </div>
      </div>

      {/* Mandatory Medical Disclaimer Banner */}
      <div className="p-4 rounded-2xl bg-amber-50/90 border border-amber-200/90 text-amber-900 shadow-sm">
        <div className="flex items-start space-x-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="text-xs leading-relaxed space-y-1">
            <p className="font-bold text-amber-950">Medical Literacy Advisory</p>
            <p className="text-amber-900/90">{disclaimer}</p>
          </div>
        </div>
      </div>

      {/* Executive Overview Card */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-6">
        <div className="flex items-center space-x-2.5 pb-4 border-b border-slate-100">
          <div className="p-2 rounded-xl bg-teal-50 text-teal-700">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900">Summary Overview</h3>
            <p className="text-xs text-slate-500">Plain English interpretation of your lab findings</p>
          </div>
        </div>

        <p className="text-sm sm:text-base text-slate-700 leading-relaxed">
          {summary}
        </p>

        {key_findings && key_findings.length > 0 && (
          <div className="space-y-3 pt-2">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              Key Observations
            </h4>
            <div className="grid grid-cols-1 gap-2.5">
              {key_findings.map((finding, idx) => (
                <div
                  key={idx}
                  className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 flex items-start space-x-3 text-xs sm:text-sm text-slate-800"
                >
                  <Info className="w-4 h-4 text-teal-600 flex-shrink-0 mt-0.5" />
                  <span>{finding}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Lab Parameters Explained */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-slate-900 flex items-center space-x-2">
            <span>Test Results Breakdown</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-200 text-slate-700 font-semibold">
              {parameters_explained.length}
            </span>
          </h3>
          <span className="text-xs text-slate-500">Original values & plain explanations</span>
        </div>

        <div className="grid grid-cols-1 gap-4">
          {parameters_explained.map((param, idx) => (
            <div
              key={idx}
              className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4 transition-all hover:border-slate-300"
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div>
                  <h4 className="text-base font-bold text-slate-900">{param.name}</h4>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {param.plain_english_explanation}
                  </p>
                </div>
                <div>{getStatusBadge(param.status)}</div>
              </div>

              {/* Lab Values Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100">
                <div>
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                    Observed Result
                  </span>
                  <p className="text-base font-extrabold text-slate-900">
                    {param.observed_value || 'N/A'}{' '}
                    <span className="text-xs font-normal text-slate-500">{param.unit || ''}</span>
                  </p>
                </div>

                <div>
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                    Reference Interval
                  </span>
                  <p className="text-xs font-semibold text-slate-700 mt-1">
                    {param.normal_range || 'Not specified'} {param.unit || ''}
                  </p>
                </div>

                <div className="col-span-2 sm:col-span-1">
                  <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                    Category
                  </span>
                  <p className="text-xs font-semibold text-slate-700 mt-1">
                    {param.status || 'Normal'}
                  </p>
                </div>
              </div>

              {/* What this means */}
              <div className="text-xs text-slate-700 bg-teal-50/50 p-3 rounded-xl border border-teal-100 flex items-start space-x-2.5">
                <Stethoscope className="w-4 h-4 text-teal-700 flex-shrink-0 mt-0.5" />
                <p className="leading-relaxed">
                  <strong className="font-semibold text-teal-900">Educational Context: </strong>
                  {param.interpretation}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Questions for Doctor */}
      {questions_for_doctor && questions_for_doctor.length > 0 && (
        <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-4">
          <div className="flex items-center space-x-2.5 pb-3 border-b border-slate-100">
            <div className="p-2 rounded-xl bg-blue-50 text-blue-700">
              <Stethoscope className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">Questions to Ask Your Doctor</h3>
              <p className="text-xs text-slate-500">Take these proactive questions to your appointment</p>
            </div>
          </div>

          <div className="space-y-2.5 pt-2">
            {questions_for_doctor.map((question, idx) => (
              <label
                key={idx}
                onClick={() => toggleQuestion(idx)}
                className={`flex items-start space-x-3 p-3.5 rounded-xl border cursor-pointer transition-all ${
                  checkedQuestions[idx]
                    ? 'bg-slate-50 border-slate-200 line-through text-slate-400'
                    : 'bg-white hover:bg-slate-50/80 border-slate-200 text-slate-800'
                }`}
              >
                <input
                  type="checkbox"
                  checked={!!checkedQuestions[idx]}
                  onChange={() => {}}
                  className="mt-1 h-4 w-4 rounded border-slate-300 text-teal-600 focus:ring-teal-500"
                />
                <span className="text-xs sm:text-sm font-medium leading-relaxed select-none">
                  {question}
                </span>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Terminology Jargon Buster */}
      {terminology_breakdown && terminology_breakdown.length > 0 && (
        <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-4">
          <div className="flex items-center space-x-2.5 pb-3 border-b border-slate-100">
            <div className="p-2 rounded-xl bg-emerald-50 text-emerald-700">
              <BookOpen className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">Medical Terminology Explained</h3>
              <p className="text-xs text-slate-500">Complex laboratory terms translated into everyday words</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            {terminology_breakdown.map((item, idx) => (
              <div key={idx} className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                <h5 className="text-xs font-bold text-slate-900">{item.term}</h5>
                <p className="text-xs text-slate-600 leading-relaxed">{item.simple_definition}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Educational Footnotes & Raw Text Toggle */}
      <div className="pt-2 text-center space-y-3">
        {educational_notes.map((note, i) => (
          <p key={i} className="text-xs text-slate-500 italic max-w-2xl mx-auto">
            {note}
          </p>
        ))}

        <div className="pt-2">
          <button
            onClick={() => setShowRawText(!showRawText)}
            className="inline-flex items-center space-x-1 text-xs text-slate-500 hover:text-slate-800 underline"
          >
            <span>{showRawText ? 'Hide' : 'View'} Sanitized Extracted Text</span>
            {showRawText ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>

        {showRawText && (
          <div className="mt-4 p-4 rounded-2xl bg-slate-900 text-slate-200 text-left font-mono text-xs overflow-x-auto max-h-72 border border-slate-800">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-800 text-slate-400">
              <span>Sanitized OCR & Text Output</span>
              <span>All PII Masked</span>
            </div>
            <pre className="whitespace-pre-wrap">{extraction.extracted_text}</pre>
          </div>
        )}
      </div>
    </div>
  );
}
