import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { api } from '../utils/api';

const SEVERITY_COLORS = {
  HIGH: 'bg-red-100 text-red-800',
  MEDIUM: 'bg-yellow-100 text-yellow-800',
  LOW: 'bg-green-100 text-green-800',
};

const SENTIMENT_BADGE = {
  POSITIVE: { cls: 'bg-green-100 text-green-800', icon: '\u{1F60A}' },
  NEGATIVE: { cls: 'bg-red-100 text-red-800', icon: '\u{1F61F}' },
  NEUTRAL: { cls: 'bg-gray-100 text-gray-800', icon: '\u{1F610}' },
};

const TYPE_LABELS = {
  site_visit: { icon: '\u{1F3ED}', label: 'Factory / Site Visit' },
  management_interview: { icon: '\u{1F4AC}', label: 'Management Interview' },
  observation: { icon: '\u{1F440}', label: 'Due Diligence Observation' },
  general: { icon: '\u{1F4DD}', label: 'General Note' },
};

const DueDiligencePortal = () => {
  const { id } = useParams();

  const [insightType, setInsightType] = useState('site_visit');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [lastResult, setLastResult] = useState(null);
  const [allInsights, setAllInsights] = useState(null);
  const [fetchingInsights, setFetchingInsights] = useState(false);

  useEffect(() => {
    if (id) fetchInsights();
  }, [id]);

  const fetchInsights = async () => {
    setFetchingInsights(true);
    try {
      const data = await api.getDueDiligenceNotes(id);
      setAllInsights(data);
    } catch {
      // no insights yet
    } finally {
      setFetchingInsights(false);
    }
  };

  const handleSubmit = async () => {
    if (!notes.trim()) { setError('Please enter your observations'); return; }
    setLoading(true);
    setError('');
    setLastResult(null);

    try {
      const result = await api.addDueDiligenceNotes({
        application_id: id,
        insight_type: insightType,
        credit_officer_notes: notes,
      });
      setLastResult(result);
      setNotes('');
      await fetchInsights();
    } catch (e) {
      setError(e.message || 'Failed to process insight');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (noteId) => {
    try {
      await api.deleteDueDiligenceNote(id, noteId);
      await fetchInsights();
    } catch (e) {
      setError(e.message || 'Failed to delete');
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="card">
        <h1 className="text-2xl font-bold mb-1">Primary Insights Portal</h1>
        <p className="text-gray-500 text-sm">Human intelligence inputs for application: {id}</p>
        <p className="text-xs text-gray-400 mt-1">Site visits, management interviews, due diligence observations</p>
      </div>

      {/* Input Form */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Add New Insight</h2>

        <div className="space-y-4">
          {/* Insight Type Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Insight Type</label>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {Object.entries(TYPE_LABELS).map(([key, { icon, label }]) => (
                <button
                  key={key}
                  onClick={() => setInsightType(key)}
                  className={`p-3 rounded-lg border-2 text-left transition-all ${
                    insightType === key
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <span className="text-xl">{icon}</span>
                  <p className="text-xs font-medium mt-1">{label}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Notes Textarea */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Officer's Observations *
            </label>
            <textarea
              value={notes}
              onChange={e => setNotes(e.target.value)}
              rows={6}
              placeholder={
                insightType === 'site_visit'
                  ? "Describe factory conditions, capacity utilization, inventory levels, workforce observations, safety compliance, machinery condition..."
                  : insightType === 'management_interview'
                  ? "Summarize management discussion: expansion plans, market outlook, key challenges, revenue projections, competitive position..."
                  : insightType === 'observation'
                  ? "Document any governance concerns, related party issues, supply chain risks, regulatory compliance gaps..."
                  : "Enter any relevant observations or notes..."
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
            />
            <p className="text-xs text-gray-400 mt-1">{notes.length} characters</p>
          </div>

          {error && <div className="bg-red-50 text-red-700 px-4 py-2 rounded text-sm">{error}</div>}

          <button
            onClick={handleSubmit}
            disabled={loading}
            className="w-full px-4 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
                Analyzing with AI...
              </span>
            ) : 'Submit & Analyze with AI'}
          </button>
        </div>
      </div>

      {/* Last Submission Result */}
      {lastResult && lastResult.ai_analysis && (
        <div className="card border-l-4 border-l-indigo-500 bg-indigo-50">
          <h3 className="text-lg font-bold mb-3">AI Analysis Result</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-3">
            <div>
              <p className="text-xs text-gray-500">Risk Category</p>
              <p className="font-semibold">{lastResult.ai_analysis.risk_category}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Severity</p>
              <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${SEVERITY_COLORS[lastResult.ai_analysis.severity] || SEVERITY_COLORS.LOW}`}>
                {lastResult.ai_analysis.severity}
              </span>
            </div>
            <div>
              <p className="text-xs text-gray-500">Sentiment</p>
              <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${(SENTIMENT_BADGE[lastResult.ai_analysis.sentiment] || SENTIMENT_BADGE.NEUTRAL).cls}`}>
                {(SENTIMENT_BADGE[lastResult.ai_analysis.sentiment] || SENTIMENT_BADGE.NEUTRAL).icon} {lastResult.ai_analysis.sentiment}
              </span>
            </div>
            <div>
              <p className="text-xs text-gray-500">Score Adjustment</p>
              <span className={`font-bold ${lastResult.ai_analysis.score_adjustment >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {lastResult.ai_analysis.score_adjustment > 0 ? '+' : ''}{lastResult.ai_analysis.score_adjustment} pts
              </span>
            </div>
          </div>
          <p className="text-sm text-gray-700">{lastResult.ai_analysis.summary}</p>
          {(lastResult.ai_analysis.risk_flags || []).length > 0 && (
            <div className="mt-3">
              <p className="text-xs text-gray-500 mb-1">Risk Flags:</p>
              <div className="flex flex-wrap gap-1">
                {lastResult.ai_analysis.risk_flags.map((f, i) => (
                  <span key={i} className="px-2 py-0.5 bg-red-50 text-red-700 rounded text-xs">{f}</span>
                ))}
              </div>
            </div>
          )}
          {(lastResult.ai_analysis.entities || []).length > 0 && (
            <div className="mt-2">
              <p className="text-xs text-gray-500 mb-1">Entities Identified:</p>
              <div className="flex flex-wrap gap-1">
                {lastResult.ai_analysis.entities.map((e, i) => (
                  <span key={i} className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs">{e}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* All Insights */}
      {fetchingInsights && <div className="card text-center text-gray-500">Loading insights...</div>}

      {allInsights && allInsights.total_insights > 0 && (
        <div className="space-y-4">
          {/* Summary Bar */}
          <div className="card bg-gray-50">
            <div className="flex flex-wrap items-center justify-between gap-4">
              <div>
                <span className="text-lg font-bold">{allInsights.total_insights}</span>
                <span className="text-gray-500 text-sm ml-1">insights recorded</span>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-sm">
                  Total Adjustment: <span className={`font-bold ${allInsights.total_score_adjustment >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {allInsights.total_score_adjustment > 0 ? '+' : ''}{allInsights.total_score_adjustment} pts
                  </span>
                </div>
                <div className="flex gap-2">
                  {Object.entries(allInsights.severity_breakdown || {}).map(([sev, count]) => count > 0 && (
                    <span key={sev} className={`px-2 py-0.5 rounded-full text-xs font-medium ${SEVERITY_COLORS[sev]}`}>
                      {sev}: {count}
                    </span>
                  ))}
                </div>
              </div>
            </div>
            {(allInsights.all_risk_flags || []).length > 0 && (
              <div className="mt-3 pt-3 border-t">
                <p className="text-xs text-gray-500 mb-1">All Risk Flags Across Insights:</p>
                <div className="flex flex-wrap gap-1">
                  {allInsights.all_risk_flags.map((f, i) => (
                    <span key={i} className="px-2 py-0.5 bg-red-50 text-red-700 rounded text-xs">{f}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Individual Notes */}
          {(allInsights.notes || []).map(note => {
            const typeMeta = TYPE_LABELS[note.insight_type] || TYPE_LABELS.general;
            const sentBadge = SENTIMENT_BADGE[note.sentiment] || SENTIMENT_BADGE.NEUTRAL;
            return (
              <div key={note.id} className="card">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{typeMeta.icon}</span>
                    <span className="font-medium text-sm">{typeMeta.label}</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${SEVERITY_COLORS[note.severity] || SEVERITY_COLORS.LOW}`}>
                      {note.severity}
                    </span>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${sentBadge.cls}`}>
                      {sentBadge.icon} {note.sentiment}
                    </span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`font-bold text-sm ${(note.score_adjustment || 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {note.score_adjustment > 0 ? '+' : ''}{note.score_adjustment} pts
                    </span>
                    <button onClick={() => handleDelete(note.id)} className="text-gray-400 hover:text-red-500 text-xs">Delete</button>
                  </div>
                </div>

                {note.ai_summary && (
                  <p className="text-sm text-gray-800 bg-gray-50 rounded p-2 mb-2">{note.ai_summary}</p>
                )}

                <details className="text-xs">
                  <summary className="text-gray-500 cursor-pointer hover:text-gray-700">Original notes ({note.notes?.length || 0} chars)</summary>
                  <p className="text-gray-600 mt-1 whitespace-pre-wrap bg-gray-50 rounded p-2">{note.notes}</p>
                </details>

                {(note.risk_flags || []).length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {note.risk_flags.map((f, i) => (
                      <span key={i} className="px-1.5 py-0.5 bg-red-50 text-red-700 rounded text-xs">{f}</span>
                    ))}
                  </div>
                )}

                {note.created_at && (
                  <p className="text-xs text-gray-400 mt-2">{new Date(note.created_at).toLocaleString()}</p>
                )}
              </div>
            );
          })}
        </div>
      )}

      {allInsights && allInsights.total_insights === 0 && (
        <div className="card text-center text-gray-500 py-8">
          <p className="text-lg mb-1">No insights recorded yet</p>
          <p className="text-sm">Add your first site visit report, management interview, or observation above.</p>
        </div>
      )}
    </div>
  );
};

export default DueDiligencePortal;
