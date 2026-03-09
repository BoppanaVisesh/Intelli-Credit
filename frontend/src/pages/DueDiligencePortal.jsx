import { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { api } from '../utils/api';

const RISK_COLORS = {
  HIGH: { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-300', dot: 'bg-red-500' },
  MEDIUM: { bg: 'bg-yellow-100', text: 'text-yellow-800', border: 'border-yellow-300', dot: 'bg-yellow-500' },
  LOW: { bg: 'bg-green-100', text: 'text-green-800', border: 'border-green-300', dot: 'bg-green-500' },
};

const SENTIMENT_ICONS = { POSITIVE: '😊', NEGATIVE: '😟', NEUTRAL: '😐' };

const TYPE_META = {
  news: { icon: '📰', label: 'News Analysis', desc: 'Media sentiment & risk alerts' },
  litigation: { icon: '⚖️', label: 'Litigation Search', desc: 'Court cases, NCLT & legal disputes' },
  promoter: { icon: '👤', label: 'Promoter Profiling', desc: 'Background checks & web intelligence' },
  sector: { icon: '📊', label: 'Sector Analysis', desc: 'Industry outlook & headwinds' },
  regulatory: { icon: '🏛️', label: 'Regulatory Check', desc: 'Credit rating & compliance actions' },
};

const RiskBadge = ({ level }) => {
  const c = RISK_COLORS[level] || RISK_COLORS.LOW;
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${c.bg} ${c.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${c.dot}`} />
      {level}
    </span>
  );
};

const DueDiligencePortal = () => {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const companyFromUrl = searchParams.get('company') || '';

  const [companyName, setCompanyName] = useState(companyFromUrl);
  const [sector, setSector] = useState('');
  const [promoterInput, setPromoterInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [fetchingResults, setFetchingResults] = useState(false);
  const [researchData, setResearchData] = useState(null);
  const [triggerResponse, setTriggerResponse] = useState(null);
  const [error, setError] = useState('');
  const [expandedCards, setExpandedCards] = useState({});

  useEffect(() => {
    if (id) fetchResults();
  }, [id]);

  const fetchResults = async () => {
    setFetchingResults(true);
    try {
      const data = await api.getResearchResults(id);
      if (data.research_completed) setResearchData(data);
    } catch {
      // no results yet
    } finally {
      setFetchingResults(false);
    }
  };

  const handleTrigger = async () => {
    if (!companyName.trim()) { setError('Company name is required'); return; }
    setLoading(true);
    setError('');
    setTriggerResponse(null);
    setResearchData(null);

    try {
      const promoterNames = promoterInput
        .split(',')
        .map(s => s.trim())
        .filter(Boolean);

      const result = await api.triggerResearch({
        application_id: id,
        company_name: companyName,
        sector: sector || undefined,
        promoter_names: promoterNames.length ? promoterNames : undefined,
      });
      setTriggerResponse(result);
      await fetchResults();
    } catch (e) {
      setError(e.message || 'Research failed');
    } finally {
      setLoading(false);
    }
  };

  const toggle = key => setExpandedCards(prev => ({ ...prev, [key]: !prev[key] }));

  const renderArticles = articles => (
    <div className="space-y-2 mt-2">
      {articles.map((a, i) => (
        <div key={i} className="bg-white border rounded p-2 text-sm">
          <div className="flex justify-between items-start">
            <a href={a.url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline font-medium">{a.title}</a>
            <span className={`ml-2 text-xs px-1.5 py-0.5 rounded ${a.sentiment === 'NEGATIVE' ? 'bg-red-100 text-red-700' : a.sentiment === 'POSITIVE' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-700'}`}>{a.sentiment}</span>
          </div>
          <p className="text-gray-500 text-xs mt-1">{a.source}</p>
          {a.snippet && <p className="text-gray-600 text-xs mt-1">{a.snippet.slice(0, 150)}...</p>}
        </div>
      ))}
    </div>
  );

  const renderLitigation = data => (
    <div className="space-y-2 mt-2">
      <div className="grid grid-cols-3 gap-3 text-sm">
        <div className="bg-white border rounded p-2 text-center">
          <div className="text-2xl font-bold">{data.case_count}</div>
          <div className="text-gray-500 text-xs">Cases Found</div>
        </div>
        <div className="bg-white border rounded p-2 text-center">
          <div className="text-2xl font-bold">{(data.nclt_cases || []).length}</div>
          <div className="text-gray-500 text-xs">NCLT Cases</div>
        </div>
        <div className="bg-white border rounded p-2 text-center">
          <div className="text-2xl font-bold text-red-600">{data.total_penalty}</div>
          <div className="text-gray-500 text-xs">Score Penalty</div>
        </div>
      </div>
      {data.recommendation && <p className="text-sm text-gray-700 bg-white border rounded p-2">💡 {data.recommendation}</p>}
      {(data.records || []).map((r, i) => (
        <div key={i} className="bg-white border rounded p-2 text-sm">
          <p className="text-gray-700">{r.summary}</p>
          {r.url && <a href={r.url} target="_blank" rel="noopener noreferrer" className="text-blue-500 text-xs hover:underline">Source →</a>}
        </div>
      ))}
    </div>
  );

  const renderSector = data => (
    <div className="space-y-3 mt-2">
      <div className="grid grid-cols-3 gap-3 text-sm">
        <div className="bg-white border rounded p-3 text-center">
          <div className="text-lg font-bold">{data.outlook}</div>
          <div className="text-gray-500 text-xs">Outlook</div>
        </div>
        <div className="bg-white border rounded p-3 text-center">
          <div className="text-lg font-bold">{data.growth_rate}%</div>
          <div className="text-gray-500 text-xs">Growth Rate</div>
        </div>
        <div className="bg-white border rounded p-3 text-center">
          <div className="text-lg font-bold">{data.risk_score}</div>
          <div className="text-gray-500 text-xs">Risk Score</div>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div className="bg-red-50 border border-red-200 rounded p-2">
          <div className="font-medium text-red-800 mb-1">⚠️ Headwinds</div>
          <ul className="list-disc list-inside text-red-700 text-xs space-y-1">
            {(data.headwinds || []).map((h, i) => <li key={i}>{h}</li>)}
          </ul>
        </div>
        <div className="bg-green-50 border border-green-200 rounded p-2">
          <div className="font-medium text-green-800 mb-1">🌿 Tailwinds</div>
          <ul className="list-disc list-inside text-green-700 text-xs space-y-1">
            {(data.tailwinds || []).map((t, i) => <li key={i}>{t}</li>)}
          </ul>
        </div>
      </div>
      {data.recommendation && <p className="text-sm bg-white border rounded p-2">💡 {data.recommendation}</p>}
    </div>
  );

  const renderPromoter = data => (
    <div className="mt-2 space-y-2 text-sm">
      <div className="flex items-center gap-2">
        <span>Sentiment: {SENTIMENT_ICONS[data.sentiment] || '❓'} {data.sentiment}</span>
        <span className="text-gray-400">|</span>
        <span>Risk Score: <span className={data.risk_score < 0 ? 'text-red-600 font-bold' : 'text-green-600 font-bold'}>{data.risk_score}</span></span>
      </div>
      {data.finding && <p className="text-gray-700 bg-white border rounded p-2 text-xs max-h-40 overflow-y-auto">{data.finding}</p>}
      {(data.sources || []).length > 0 && (
        <div className="text-xs text-gray-500">
          Sources: {data.sources.map((s, i) => <a key={i} href={s} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline mr-2">{new URL(s).hostname}</a>)}
        </div>
      )}
    </div>
  );

  const renderRegulatory = data => (
    <div className="mt-2 space-y-2">
      <div className="text-sm text-gray-600">
        Checked {data.total_results_checked} sources. Found {data.concerns_found} concern(s).
      </div>
      {(data.findings || []).map((f, i) => (
        <div key={i} className="bg-white border border-red-200 rounded p-2 text-sm">
          <div className="font-medium text-red-800">{f.title}</div>
          <p className="text-gray-600 text-xs mt-1">{f.content}</p>
          {f.url && <a href={f.url} target="_blank" rel="noopener noreferrer" className="text-blue-500 text-xs hover:underline">Read more →</a>}
        </div>
      ))}
      {data.concerns_found === 0 && <p className="text-green-700 text-sm">✅ No regulatory concerns found</p>}
    </div>
  );

  const renderCardContent = (type, data) => {
    switch (type) {
      case 'news': return renderArticles(data.articles || []);
      case 'litigation': return renderLitigation(data);
      case 'sector': return renderSector(data);
      case 'promoter': return renderPromoter(data);
      case 'regulatory': return renderRegulatory(data);
      default: return <pre className="text-xs bg-white p-2 rounded overflow-auto max-h-40">{JSON.stringify(data, null, 2)}</pre>;
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="card">
        <h1 className="text-2xl font-bold mb-1">🔍 External Intelligence Portal</h1>
        <p className="text-gray-500 text-sm">Application: {id}</p>
      </div>

      {/* Research Trigger Form */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4">Configure Research</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Company Name *</label>
            <input
              type="text" value={companyName}
              onChange={e => setCompanyName(e.target.value)}
              placeholder="e.g. SpiceJet Limited"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Industry / Sector</label>
            <select value={sector} onChange={e => setSector(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
              <option value="">Auto-detect</option>
              <option value="Aviation">Aviation</option>
              <option value="IT Services">IT Services</option>
              <option value="Industrial Manufacturing">Industrial Manufacturing</option>
              <option value="Textiles">Textiles</option>
              <option value="Pharmaceuticals">Pharmaceuticals</option>
              <option value="Real Estate">Real Estate</option>
              <option value="Banking">Banking</option>
              <option value="FMCG">FMCG</option>
            </select>
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">Promoter Names (comma-separated)</label>
            <input
              type="text" value={promoterInput}
              onChange={e => setPromoterInput(e.target.value)}
              placeholder="e.g. Ajay Singh, Shilpa Singh"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {error && <div className="mt-3 bg-red-50 text-red-700 px-4 py-2 rounded">{error}</div>}

        <button
          onClick={handleTrigger}
          disabled={loading}
          className="mt-4 w-full px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" /></svg>
              Running Intelligence Scan... (This takes 15-30 seconds)
            </span>
          ) : '🚀 Run External Intelligence Scan'}
        </button>
      </div>

      {/* Trigger Response Summary */}
      {triggerResponse && (
        <div className={`card border-l-4 ${triggerResponse.overall_risk === 'HIGH' ? 'border-l-red-500 bg-red-50' : triggerResponse.overall_risk === 'MEDIUM' ? 'border-l-yellow-500 bg-yellow-50' : 'border-l-green-500 bg-green-50'}`}>
          <div className="flex justify-between items-center">
            <div>
              <h3 className="text-lg font-bold">Research Complete for {triggerResponse.company_name}</h3>
              <p className="text-sm text-gray-600">{triggerResponse.completed_tasks} tasks completed, {triggerResponse.failed_tasks} failed</p>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-500">Overall Risk</div>
              <RiskBadge level={triggerResponse.overall_risk} />
            </div>
          </div>
          <div className="flex gap-4 mt-3">
            {Object.entries(triggerResponse.risk_summary || {}).map(([level, count]) => (
              <div key={level} className="text-sm"><RiskBadge level={level} /> × {count}</div>
            ))}
          </div>
        </div>
      )}

      {/* Detailed Results */}
      {fetchingResults && <div className="card text-center text-gray-500">Loading research results...</div>}

      {researchData && researchData.research_completed && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-bold">Research Findings</h2>
            <div className="text-sm text-gray-500">
              Total Score Penalty: <span className="font-bold text-red-600">{researchData.total_penalty}</span>
            </div>
          </div>

          {Object.entries(researchData.results_by_type || {}).map(([type, items]) => {
            const meta = TYPE_META[type] || { icon: '📋', label: type, desc: '' };
            return (
              <div key={type} className="card">
                <div
                  className="flex justify-between items-center cursor-pointer"
                  onClick={() => toggle(type)}
                >
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{meta.icon}</span>
                    <div>
                      <h3 className="font-semibold text-lg">{meta.label}</h3>
                      <p className="text-gray-500 text-xs">{meta.desc}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {items.map((item, idx) => (
                      <RiskBadge key={idx} level={item.risk_level} />
                    ))}
                    <span className="text-gray-400">{expandedCards[type] ? '▲' : '▼'}</span>
                  </div>
                </div>

                {expandedCards[type] && items.map((item, idx) => (
                  <div key={idx} className={`mt-3 pt-3 border-t ${idx > 0 ? 'mt-4' : ''}`}>
                    {item.entity_name && type !== 'news' && (
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-medium">{item.entity_name}</span>
                        <RiskBadge level={item.risk_level} />
                        {item.sentiment && <span className="text-sm">{SENTIMENT_ICONS[item.sentiment]} {item.sentiment}</span>}
                      </div>
                    )}
                    <p className="text-sm text-gray-700 mb-2">{item.findings_summary}</p>
                    {item.findings_data && renderCardContent(type, item.findings_data)}
                  </div>
                ))}

                {!expandedCards[type] && (
                  <p className="text-sm text-gray-500 mt-2">{items[0]?.findings_summary?.slice(0, 100)}...</p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default DueDiligencePortal;
