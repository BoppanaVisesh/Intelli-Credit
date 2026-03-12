import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../utils/api';

/* ── colour helpers ── */
const SIGNAL_COLORS = {
  POSITIVE:   { bg: 'bg-green-100', text: 'text-green-800', dot: '#4D7C3A' },
  NEGATIVE:   { bg: 'bg-red-100',   text: 'text-red-800',   dot: '#B91C1C' },
  HIGH:       { bg: 'bg-red-100',   text: 'text-red-800',   dot: '#B91C1C' },
  RISK_ALERT: { bg: 'bg-orange-100',text: 'text-orange-800', dot: '#C2410C' },
  MEDIUM:     { bg: 'bg-yellow-100',text: 'text-yellow-800', dot: '#B8860B' },
  LOW:        { bg: 'bg-green-100', text: 'text-green-800',  dot: '#4D7C3A' },
  NEUTRAL:    { bg: 'bg-gray-100',  text: 'text-gray-700',   dot: '#7A6850' },
};
const sc = (s) => SIGNAL_COLORS[s] || SIGNAL_COLORS.NEUTRAL;

const STATUS_COLORS = {
  CONFIRMED:     { bg: 'bg-green-100', text: 'text-green-800', icon: '✓' },
  CONTRADICTION: { bg: 'bg-red-100',   text: 'text-red-800',   icon: '✗' },
  WARNING:       { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: '⚠' },
  GAP:           { bg: 'bg-gray-100',   text: 'text-gray-600',  icon: '?' },
};
const tc = (s) => STATUS_COLORS[s] || STATUS_COLORS.GAP;

const DECISION_STYLES = {
  APPROVE:              { bg: 'bg-green-600',  label: 'APPROVED' },
  CONDITIONAL_APPROVE:  { bg: 'bg-yellow-500', label: 'CONDITIONAL' },
  REJECT:               { bg: 'bg-red-600',    label: 'REJECTED' },
};
const ds = (d) => DECISION_STYLES[d] || { bg: 'bg-gray-500', label: d };

const SWOT_META = {
  strengths:     { label: 'Strengths',     color: 'border-green-500',  bg: 'bg-green-50',   icon: '💪' },
  weaknesses:    { label: 'Weaknesses',    color: 'border-red-400',    bg: 'bg-red-50',     icon: '⚡' },
  opportunities: { label: 'Opportunities', color: 'border-blue-400',   bg: 'bg-blue-50',    icon: '🎯' },
  threats:       { label: 'Threats',        color: 'border-orange-400', bg: 'bg-orange-50',  icon: '🔥' },
};

/* ── tiny components ── */
const Badge = ({ signal }) => (
  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold ${sc(signal).bg} ${sc(signal).text}`}>
    <span className="w-1.5 h-1.5 rounded-full" style={{ background: sc(signal).dot }} />
    {signal}
  </span>
);

const GateBar = ({ gate }) => {
  const pct = Math.min(100, Math.max(0, gate.score));
  const color = gate.passed ? 'bg-green-500' : 'bg-red-500';
  return (
    <div className="sa-gate-card">
      <div className="flex items-center justify-between mb-1">
        <span className="font-semibold text-ink text-sm">Gate {gate.gate} — {gate.name}</span>
        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${gate.passed ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
          {gate.verdict}
        </span>
      </div>
      <div className="w-full bg-parchment rounded-full h-2.5 mb-1">
        <div className={`${color} h-2.5 rounded-full transition-all duration-700`} style={{ width: `${pct}%` }} />
      </div>
      <div className="flex justify-between text-xs text-muted">
        <span>Score: {gate.score}</span>
        <span>Threshold: {gate.threshold}</span>
      </div>
    </div>
  );
};

/* ── main page ── */
const SecondaryAnalysis = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Auto-load previous results on mount
  useEffect(() => {
    if (id) {
      (async () => {
        try {
          const data = await api.getAnalysis(id);
          if (data && (data.recommendation || data.triangulation || data.swot)) {
            setResult(data);
          }
        } catch {
          // No previous analysis — that's fine
        }
      })();
    }
  }, [id]);

  const runAnalysis = async () => {
    setLoading(true);
    setError('');
    setSuccess('');
    try {
      const data = await api.runAnalysis(id);
      setResult(data);
      setSuccess('Full analysis pipeline completed successfully');
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const loadExisting = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getAnalysis(id);
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const generateReport = async () => {
    setGenerating(true);
    setError('');
    try {
      await api.generateInvestmentReport(id);
      setSuccess('Investment report generated — ready to download');
    } catch (e) {
      setError(e.message);
    } finally {
      setGenerating(false);
    }
  };

  const downloadReport = async () => {
    setDownloading(true);
    try {
      const blob = await api.downloadInvestmentReport(id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${id}_investment_report.docx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (e) {
      setError(e.message);
    } finally {
      setDownloading(false);
    }
  };

  const rec = result?.recommendation;
  const tri = result?.triangulation;
  const swot = result?.swot;
  const rb = result?.research_bundle;
  const signals = rb?.overall_signals?.signals || [];

  return (
    <>
      <style>{`
        .sa-card { background: #FAF7F2; border-radius: 0.75rem; border: 1px solid #E8E0D0; padding: 1.5rem; }
        .sa-section-title { font-family: 'Playfair Display', serif; font-size: 1.1rem; font-weight: 700; color: #2C2416; margin-bottom: 0.75rem; }
        .sa-gate-card { background: #fff; border: 1px solid #E8E0D0; border-radius: 0.5rem; padding: 1rem; }
        .sa-swot-card { border-left-width: 4px; border-radius: 0.5rem; padding: 1rem; }
        .sa-signal-row { display: flex; align-items: center; gap: 0.75rem; padding: 0.5rem 0; border-bottom: 1px solid #f0ebe0; }
        .sa-signal-row:last-child { border-bottom: none; }
        .sa-finding-row { background: #fff; border: 1px solid #E8E0D0; border-radius: 0.5rem; padding: 0.75rem 1rem; margin-bottom: 0.5rem; }
        .sa-confidence-ring { width: 100px; height: 100px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; font-weight: 800; }
      `}</style>

      <div className="space-y-6 max-w-6xl mx-auto">
        {/* Header */}
        <div className="sa-card">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h1 className="text-2xl font-bold text-charcoal font-heading">Pre-Cognitive Analysis</h1>
              <p className="text-muted text-sm mt-1">Secondary Research · Triangulation · Reasoning Engine · SWOT — Application {id}</p>
            </div>
            <div className="flex gap-3 flex-wrap">
              <button onClick={runAnalysis} disabled={loading}
                className="px-5 py-2.5 bg-sienna text-white rounded-lg font-medium hover:bg-terracotta disabled:opacity-50 transition">
                {loading ? 'Running Analysis...' : 'Run Full Analysis'}
              </button>
              <button onClick={loadExisting} disabled={loading}
                className="px-4 py-2.5 bg-parchment rounded-lg text-sm font-medium text-ink hover:bg-warm-border transition">
                Load Previous
              </button>
              <button onClick={() => navigate(`/application/${id}/scoring`)}
                className="px-4 py-2.5 bg-parchment rounded-lg text-sm font-medium text-ink hover:bg-warm-border transition">
                Scoring
              </button>
              <button onClick={() => navigate(`/application/${id}/cam`)}
                className="px-4 py-2.5 bg-parchment rounded-lg text-sm font-medium text-ink hover:bg-warm-border transition">
                CAM
              </button>
            </div>
          </div>
          {error && <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}
          {success && <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">{success}</div>}
        </div>

        {/* Loading spinner */}
        {loading && (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-terracotta" />
            <span className="ml-4 text-muted text-lg">Running 360° pre-cognitive analysis pipeline...</span>
          </div>
        )}

        {result && !loading && (
          <>
            {/* ═══ Recommendation Hero ═══ */}
            {rec && (
              <div className={`rounded-xl shadow-sm p-6 text-white ${ds(rec.decision).bg}`}>
                <div className="flex items-center justify-between flex-wrap gap-6">
                  <div>
                    <p className="text-sm opacity-80">{result.company_name} — {result.sector}</p>
                    <p className="text-4xl font-extrabold mt-1">{rec.credit_score}<span className="text-xl font-normal opacity-60">/100</span></p>
                    <p className="text-lg font-bold mt-1">{ds(rec.decision).label}</p>
                  </div>
                  <div className="text-right">
                    <div className="sa-confidence-ring bg-white/20 mx-auto">
                      {rec.confidence_pct}%
                    </div>
                    <p className="text-xs opacity-80 mt-1">Confidence</p>
                  </div>
                  <div className="text-right text-sm space-y-1 opacity-90">
                    <p>Loan: ₹{rec.loan_recommendation?.recommended_limit_cr || '—'} Cr</p>
                    <p>Rate: {rec.interest_rate?.final_interest_rate || '—'}%</p>
                    <p>Gates Passed: {rec.gates?.filter(g => g.passed).length}/{rec.gates?.length}</p>
                  </div>
                </div>
              </div>
            )}

            {/* ═══ 3-Gate Visualization ═══ */}
            {rec?.gates && (
              <div className="sa-card">
                <h2 className="sa-section-title">Decision Gates</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {rec.gates.map(g => <GateBar key={g.gate} gate={g} />)}
                </div>
              </div>
            )}

            {/* ═══ Two-column: Research Signals + Triangulation ═══ */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Research Signals */}
              <div className="sa-card">
                <h2 className="sa-section-title">Secondary Research Signals</h2>
                <div className="flex gap-4 mb-4 text-sm">
                  <span className="px-2 py-1 bg-red-100 text-red-700 rounded-lg font-semibold">
                    {rb?.overall_signals?.risk_signal_count || 0} Risks
                  </span>
                  <span className="px-2 py-1 bg-green-100 text-green-700 rounded-lg font-semibold">
                    {rb?.overall_signals?.positive_signal_count || 0} Positive
                  </span>
                  <span className={`px-2 py-1 rounded-lg font-semibold ${sc(rb?.overall_signals?.overall_risk).bg} ${sc(rb?.overall_signals?.overall_risk).text}`}>
                    Overall: {rb?.overall_signals?.overall_risk || 'N/A'}
                  </span>
                </div>
                <div>
                  {signals.map((s, i) => (
                    <div key={i} className="sa-signal-row">
                      <span className="text-sm font-semibold text-ink w-24 shrink-0">{s.source}</span>
                      <Badge signal={s.signal} />
                      <span className="text-sm text-muted flex-1">{s.detail}</span>
                    </div>
                  ))}
                  {signals.length === 0 && <p className="text-sm text-muted py-4 text-center">No signals collected yet</p>}
                </div>

                {/* Research category breakdown */}
                {rb && (
                  <div className="mt-4 pt-4 border-t border-warm-border">
                    <p className="text-xs font-semibold text-muted uppercase mb-2">Category Sentiment</p>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      {[
                        { key: 'news', label: 'News' },
                        { key: 'legal', label: 'Legal' },
                        { key: 'market_sentiment', label: 'Market' },
                        { key: 'macro_trends', label: 'Macro' },
                        { key: 'regulatory', label: 'Regulatory' },
                        { key: 'management', label: 'Management' },
                      ].map(({ key, label }) => {
                        const cat = rb[key] || {};
                        const sentiment = cat.overall_sentiment || cat.risk_level || (cat.has_issues ? 'NEGATIVE' : 'NEUTRAL');
                        return (
                          <div key={key} className="flex items-center gap-2 py-1">
                            <span className="w-2 h-2 rounded-full" style={{ background: sc(sentiment).dot }} />
                            <span className="text-ink">{label}</span>
                            <span className={`ml-auto text-xs font-semibold ${sc(sentiment).text}`}>{sentiment}</span>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>

              {/* Triangulation Matrix */}
              <div className="sa-card">
                <h2 className="sa-section-title">Triangulation Matrix</h2>
                {tri && (
                  <>
                    <div className="flex gap-3 mb-4 text-sm flex-wrap">
                      <span className="px-2 py-1 bg-green-100 text-green-800 rounded-lg font-semibold">
                        {tri.summary?.confirmed || 0} Confirmed
                      </span>
                      <span className="px-2 py-1 bg-red-100 text-red-800 rounded-lg font-semibold">
                        {tri.summary?.contradictions || 0} Contradictions
                      </span>
                      <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-lg font-semibold">
                        {tri.summary?.warnings || 0} Warnings
                      </span>
                      <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded-lg font-semibold">
                        {tri.summary?.gaps || 0} Gaps
                      </span>
                    </div>
                    <p className="text-sm mb-3">
                      Confidence Grade:{' '}
                      <span className={`font-bold ${tri.summary?.confidence_grade === 'HIGH' ? 'text-green-700' : tri.summary?.confidence_grade === 'LOW' ? 'text-red-700' : 'text-yellow-700'}`}>
                        {tri.summary?.confidence_grade}
                      </span>
                    </p>
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {(tri.findings || []).map((f, i) => (
                        <div key={i} className="sa-finding-row">
                          <div className="flex items-center gap-2 mb-1">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${tc(f.status).bg} ${tc(f.status).text}`}>
                              {tc(f.status).icon} {f.status}
                            </span>
                            <span className="font-semibold text-sm text-ink">{f.metric}</span>
                            <span className="ml-auto text-xs text-muted">{Math.round((f.confidence || 0) * 100)}% conf.</span>
                          </div>
                          <p className="text-sm text-muted">{f.detail}</p>
                          {f.sources?.length > 0 && (
                            <p className="text-xs text-muted mt-1">Sources: {f.sources.join(', ')}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* ═══ SWOT Analysis ═══ */}
            {swot && (
              <div className="sa-card">
                <h2 className="sa-section-title">SWOT Analysis</h2>
                {swot.executive_summary && (
                  <p className="text-sm text-muted mb-4 italic">{swot.executive_summary}</p>
                )}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {Object.entries(SWOT_META).map(([key, meta]) => (
                    <div key={key} className={`sa-swot-card border-l ${meta.color} ${meta.bg}`}>
                      <h3 className="font-bold text-sm text-ink mb-2">{meta.icon} {meta.label}</h3>
                      <ul className="space-y-1">
                        {(swot[key] || []).map((item, i) => (
                          <li key={i} className="text-sm text-ink flex gap-2">
                            <span className="shrink-0 mt-1">•</span>
                            <span>{item}</span>
                          </li>
                        ))}
                        {(!swot[key] || swot[key].length === 0) && (
                          <li className="text-sm text-muted italic">No data</li>
                        )}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* ═══ Reasoning Chain ═══ */}
            {rec?.reason_chain && (
              <div className="sa-card">
                <h2 className="sa-section-title">Reasoning Chain (Audit Trail)</h2>
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Key Risks */}
                  <div>
                    <h3 className="text-sm font-bold text-red-700 mb-2">Key Risks</h3>
                    {(rec.key_risks || []).map((r, i) => (
                      <div key={i} className="flex items-start gap-2 mb-2 text-sm">
                        <span className="text-red-500 mt-0.5">✗</span>
                        <div>
                          <span className="font-semibold text-ink">{r.factor}</span>
                          <p className="text-muted">{r.detail}</p>
                        </div>
                      </div>
                    ))}
                    {(!rec.key_risks || rec.key_risks.length === 0) && <p className="text-sm text-muted">No key risks identified</p>}
                  </div>
                  {/* Key Strengths */}
                  <div>
                    <h3 className="text-sm font-bold text-green-700 mb-2">Key Strengths</h3>
                    {(rec.key_strengths || []).map((r, i) => (
                      <div key={i} className="flex items-start gap-2 mb-2 text-sm">
                        <span className="text-green-500 mt-0.5">✓</span>
                        <div>
                          <span className="font-semibold text-ink">{r.factor}</span>
                          <p className="text-muted">{r.detail}</p>
                        </div>
                      </div>
                    ))}
                    {(!rec.key_strengths || rec.key_strengths.length === 0) && <p className="text-sm text-muted">No key strengths identified</p>}
                  </div>
                </div>

                {/* Narrative */}
                {rec.narrative && (
                  <div className="mt-4 pt-4 border-t border-warm-border">
                    <h3 className="text-sm font-bold text-ink mb-2">Narrative Summary</h3>
                    <p className="text-sm text-muted whitespace-pre-line">{rec.narrative}</p>
                  </div>
                )}
              </div>
            )}

            {/* ═══ Investment Report Actions ═══ */}
            <div className="sa-card">
              <div className="flex items-center justify-between flex-wrap gap-4">
                <div>
                  <h2 className="sa-section-title mb-0">Investment Report</h2>
                  <p className="text-sm text-muted">Generate and download a comprehensive .docx investment analysis report</p>
                </div>
                <div className="flex gap-3">
                  <button onClick={generateReport} disabled={generating}
                    className="px-5 py-2.5 bg-sienna text-white rounded-lg font-medium hover:bg-terracotta disabled:opacity-50 transition">
                    {generating ? 'Generating...' : 'Generate Report'}
                  </button>
                  <button onClick={downloadReport} disabled={downloading}
                    className="px-5 py-2.5 bg-gold text-white rounded-lg font-medium hover:opacity-90 disabled:opacity-50 transition">
                    {downloading ? 'Downloading...' : 'Download .docx'}
                  </button>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    </>
  );
};

export default SecondaryAnalysis;
