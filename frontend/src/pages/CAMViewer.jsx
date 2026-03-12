import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../utils/api';

const SECTIONS = [
  'Executive Summary', 'Company Profile', 'Industry Analysis',
  'Financial Analysis', 'Bank Statement Analysis', 'GST Compliance',
  'Litigation Check', 'Five Cs Evaluation', 'Risk Assessment',
  'Loan Recommendation',
];

const CAMViewer = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [hasExistingReport, setHasExistingReport] = useState(false);

  // On mount, check if a CAM report already exists for download
  useEffect(() => {
    if (id) {
      api.getApplicationSummary(id).then(data => {
        if (data?.pipeline?.cam?.url) setHasExistingReport(true);
      }).catch(() => {});
    }
  }, [id]);

  const generate = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.generateCAM(id);
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const download = async () => {
    setDownloading(true);
    try {
      const blob = await api.downloadCAM(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `CAM_${id}.docx`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      setError('Download failed: ' + e.message);
    } finally {
      setDownloading(false);
    }
  };

  const scoring = result?.scoring;
  const loan = result?.loan_recommendation;
  const rate = result?.interest_rate;
  const reasons = result?.decision_reasons;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="bg-warm-white rounded-xl shadow-warm border border-warm-border p-6">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold text-charcoal">Credit Appraisal Memo</h1>
            <p className="text-muted text-sm mt-1">Professional CAM Report &mdash; Application {id}</p>
          </div>
          <div className="flex gap-3">
            <button onClick={() => navigate(`/application/${id}`)}
              className="px-4 py-2.5 bg-parchment rounded-lg text-sm font-medium text-ink hover:bg-warm-border transition">
              Back to Application
            </button>
            <button onClick={generate} disabled={loading}
              className="px-5 py-2.5 bg-sienna text-white rounded-lg font-medium hover:bg-terracotta disabled:opacity-50 transition">
              {loading ? 'Generating...' : 'Generate CAM'}
            </button>
            {(result || hasExistingReport) && (
              <button onClick={download} disabled={downloading}
                className="px-5 py-2.5 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 disabled:opacity-50 transition">
                {downloading ? 'Downloading...' : 'Download .docx'}
              </button>
            )}
            <button onClick={() => navigate(`/application/${id}/scoring`)}
              className="px-4 py-2.5 bg-parchment rounded-lg text-sm font-medium text-ink hover:bg-warm-border transition">
              Back to Scoring
            </button>
          </div>
        </div>
        {error && <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-terracotta" />
          <span className="ml-4 text-muted text-lg">Generating CAM with LLM narrative...</span>
        </div>
      )}

      {result && !loading && (
        <>
          {/* Executive Summary */}
          {result.executive_summary && (
            <div className="bg-gradient-to-br from-parchment to-warm-white rounded-xl shadow-warm border border-warm-border p-6">
              <h2 className="text-lg font-bold text-charcoal mb-3">Executive Summary (LLM-Generated)</h2>
              <p className="text-sm text-ink leading-relaxed whitespace-pre-wrap">{result.executive_summary}</p>
            </div>
          )}

          {/* Score + Decision Summary */}
          {scoring && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-warm-white rounded-xl shadow-warm border border-warm-border p-5 text-center">
                <p className="text-sm text-muted">Credit Score</p>
                <p className="text-4xl font-extrabold text-charcoal">{scoring.final_credit_score}<span className="text-lg text-muted">/100</span></p>
                <p className="text-sm font-medium mt-1 text-sienna">{scoring.risk_grade}</p>
              </div>
              <div className={`rounded-xl shadow-sm border p-5 text-center text-white ${scoring.decision === 'APPROVE' ? 'bg-green-600' : scoring.decision === 'CONDITIONAL_APPROVE' ? 'bg-yellow-500' : 'bg-red-600'}`}>
                <p className="text-sm opacity-80">Decision</p>
                <p className="text-2xl font-bold mt-1">{scoring.decision?.replace('_', ' ')}</p>
                {scoring.approval_percentage > 0 && <p className="text-sm opacity-80 mt-1">{scoring.approval_percentage}% Approved</p>}
              </div>
              <div className="bg-warm-white rounded-xl shadow-warm border border-warm-border p-5 text-center">
                <p className="text-sm text-muted">Recommended Loan</p>
                <p className="text-3xl font-bold text-green-700">₹{loan?.recommended_limit_cr || '—'} Cr</p>
                {rate && <p className="text-sm text-muted mt-1">@ {rate.final_interest_rate}% ({rate.risk_category})</p>}
              </div>
            </div>
          )}

          {/* Document Sections */}
          <div className="bg-warm-white rounded-xl shadow-warm border border-warm-border p-6">
            <h2 className="text-lg font-bold text-charcoal mb-4">CAM Document Sections</h2>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {SECTIONS.map((s, i) => (
                <div key={i} className="flex items-center gap-2 p-3 bg-green-50 rounded-lg">
                  <span className="text-green-600 text-sm">&#10003;</span>
                  <span className="text-xs font-medium text-ink">{s}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Decision Reasons */}
          {reasons?.length > 0 && (
          <div className="bg-warm-white rounded-xl shadow-warm border border-warm-border p-6">
            <h2 className="text-lg font-bold text-charcoal mb-3">Decision Reasons</h2>
              <div className="space-y-2">
                {reasons.map((r, i) => (
                  <div key={i} className={`flex items-start gap-3 p-3 rounded-lg ${r.impact === 'POSITIVE' ? 'bg-green-50' : 'bg-red-50'}`}>
                    <span className={`mt-0.5 text-lg ${r.impact === 'POSITIVE' ? 'text-green-600' : 'text-red-600'}`}>
                      {r.impact === 'POSITIVE' ? '✓' : '✗'}
                    </span>
                    <p className={`text-sm font-medium ${r.impact === 'POSITIVE' ? 'text-green-800' : 'text-red-800'}`}>{r.text}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Five Cs Summary */}
          {scoring?.sub_scores && (
          <div className="bg-warm-white rounded-xl shadow-warm border border-warm-border p-6">
            <h2 className="text-lg font-bold text-charcoal mb-4">Five Cs Assessment</h2>
              <div className="space-y-3">
                {Object.entries(scoring.sub_scores).map(([key, val]) => (
                  <div key={key}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="font-medium text-ink capitalize">{key} ({(val.weight * 100).toFixed(0)}%)</span>
                      <span className="font-bold">{val.score}/100</span>
                    </div>
                    <div className="w-full bg-parchment rounded-full h-2.5">
                      <div className={`${val.score >= 60 ? 'bg-green-500' : val.score >= 30 ? 'bg-yellow-500' : 'bg-red-500'} h-2.5 rounded-full`} style={{ width: `${val.score}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {!result && !loading && (
        <div className="bg-warm-white rounded-xl shadow-warm border border-warm-border p-12 text-center">
          <div className="text-6xl mb-4">&#x1F4DD;</div>
          <h3 className="text-xl font-bold text-charcoal">Generate Credit Appraisal Memo</h3>
          <p className="text-muted mt-2 max-w-md mx-auto">
            Click "Generate CAM" to create a professional 10-section Credit Appraisal Memo with LLM-powered executive summary. The document will be available for download as a Word file.
          </p>
        </div>
      )}
    </div>
  );
};

export default CAMViewer;
