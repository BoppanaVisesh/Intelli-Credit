import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../utils/api';

const GRADE_COLORS = {
  AAA: 'text-green-700 bg-green-100',
  AA:  'text-green-600 bg-green-50',
  A:   'text-blue-700 bg-blue-100',
  BBB: 'text-yellow-700 bg-yellow-100',
  BB:  'text-orange-700 bg-orange-100',
  B:   'text-red-700 bg-red-100',
};

const DECISION_COLORS = {
  APPROVE: 'bg-green-600',
  CONDITIONAL_APPROVE: 'bg-yellow-500',
  REJECT: 'bg-red-600',
};

const ScoringResult = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const calculate = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.calculateScore(id);
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const sub = result?.sub_scores;
  const expl = result?.explanations;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-sm border p-6">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Credit Scoring</h1>
            <p className="text-gray-500 text-sm mt-1">5-Cs Framework &mdash; Application {id}</p>
          </div>
          <div className="flex gap-3">
            <button onClick={calculate} disabled={loading}
              className="px-5 py-2.5 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 transition">
              {loading ? 'Calculating...' : 'Calculate Score'}
            </button>
            <button onClick={() => navigate(`/application/${id}/fraud`)}
              className="px-4 py-2.5 bg-gray-100 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-200 transition">
              Fraud Detection
            </button>
            <button onClick={() => navigate(`/application/${id}/cam`)}
              className="px-4 py-2.5 bg-gray-100 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-200 transition">
              View CAM
            </button>
          </div>
        </div>
        {error && <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" />
          <span className="ml-4 text-gray-500 text-lg">Running 5-Cs credit assessment...</span>
        </div>
      )}

      {result && !loading && (
        <>
          {/* Score Hero */}
          <div className={`rounded-xl shadow-sm border p-6 text-white ${DECISION_COLORS[result.decision] || 'bg-gray-700'}`}>
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div>
                <p className="text-sm opacity-80">{result.company_name}</p>
                <p className="text-5xl font-extrabold mt-1">{result.final_credit_score}<span className="text-2xl font-normal opacity-60">/{result.max_score}</span></p>
                <p className="text-sm mt-2 opacity-90">{result.model_version}</p>
              </div>
              <div className="text-right">
                <span className={`inline-block px-3 py-1 rounded-full text-sm font-bold ${GRADE_COLORS[result.risk_grade] || 'bg-gray-200 text-gray-800'}`}>
                  {result.risk_grade}
                </span>
                <p className="text-2xl font-bold mt-2">{result.decision?.replace('_', ' ')}</p>
                {result.approval_percentage > 0 && (
                  <p className="text-sm opacity-80 mt-1">
                    Approved {result.approval_percentage}% &mdash; Rs. {result.recommended_limit_cr} Cr of Rs. {result.requested_limit_cr} Cr
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Sub-Scores */}
          {sub && (
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4">5-Cs Sub-Scores</h2>
              <div className="space-y-4">
                {Object.entries(sub).map(([key, val]) => {
                  const pct = val.score;
                  let color = 'bg-green-500';
                  if (pct < 30) color = 'bg-red-500';
                  else if (pct < 60) color = 'bg-yellow-500';
                  return (
                    <div key={key}>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="font-medium text-gray-700 capitalize">{key} ({(val.weight * 100).toFixed(0)}%)</span>
                        <span className="font-bold">{val.score}/100</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-3">
                        <div className={`${color} h-3 rounded-full transition-all duration-700`} style={{ width: `${pct}%` }} />
                      </div>
                      {expl?.[key] && (
                        <p className="text-xs text-gray-500 mt-1">{expl[key]}</p>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Key Factors */}
          {result.key_factors?.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-3">Key Decision Factors</h2>
              <ol className="list-decimal list-inside space-y-1 text-sm text-gray-700">
                {result.key_factors.map((f, i) => <li key={i}>{f}</li>)}
              </ol>
            </div>
          )}
        </>
      )}

      {!result && !loading && (
        <div className="bg-white rounded-xl shadow-sm border p-12 text-center">
          <div className="text-6xl mb-4">&#x1F4CA;</div>
          <h3 className="text-xl font-bold text-gray-800">Ready to Score</h3>
          <p className="text-gray-500 mt-2 max-w-md mx-auto">
            Click "Calculate Score" to run the 5-Cs credit assessment using parsed documents, research findings, and due diligence data.
          </p>
        </div>
      )}
    </div>
  );
};

export default ScoringResult;
