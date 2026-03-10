import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../utils/api';

const RISK_COLORS = {
  CRITICAL: { bg: 'bg-red-200', text: 'text-red-900', ring: 'ring-red-500', bar: 'bg-red-600' },
  HIGH:     { bg: 'bg-red-100', text: 'text-red-800', ring: 'ring-red-400', bar: 'bg-red-500' },
  MEDIUM:   { bg: 'bg-yellow-100', text: 'text-yellow-800', ring: 'ring-yellow-400', bar: 'bg-yellow-500' },
  LOW:      { bg: 'bg-green-100', text: 'text-green-800', ring: 'ring-green-400', bar: 'bg-green-500' },
};
const rc = (l) => RISK_COLORS[l] || RISK_COLORS.LOW;

const Badge = ({ level }) => (
  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${rc(level).bg} ${rc(level).text}`}>
    {level}
  </span>
);

const ScoreGauge = ({ score, label, max = 100 }) => {
  const pct = Math.min(100, Math.max(0, (score / max) * 100));
  let color = 'bg-green-500';
  if (pct >= 60) color = 'bg-red-600';
  else if (pct >= 40) color = 'bg-red-500';
  else if (pct >= 20) color = 'bg-yellow-500';
  return (
    <div className="mb-3">
      <div className="flex justify-between text-sm mb-1">
        <span className="font-medium text-ink">{label}</span>
        <span className="font-bold">{score}/{max}</span>
      </div>
      <div className="w-full bg-parchment rounded-full h-3">
        <div className={`${color} h-3 rounded-full transition-all duration-700`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
};

const FraudDetection = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const runVerification = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.runFraudVerification(id);
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const cv = result?.cross_verification;
  const ct = result?.circular_trading;
  const ml = result?.ml_prediction;
  const wb = result?.weight_breakdown;

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="bg-warm-white rounded-xl shadow-warm border border-warm-border p-6">
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h1 className="text-2xl font-bold text-charcoal">Fraud & Cross-Verification</h1>
            <p className="text-muted text-sm mt-1">Application {id}</p>
          </div>
          <div className="flex gap-3">
            <button
              onClick={runVerification}
              disabled={loading}
              className="px-5 py-2.5 bg-red-600 text-white rounded-lg font-medium hover:bg-red-700 disabled:opacity-50 transition"
            >
              {loading ? 'Running Analysis...' : 'Run Fraud Verification'}
            </button>
            <button onClick={() => navigate(`/application/${id}/scoring`)} className="px-4 py-2.5 bg-parchment rounded-lg text-sm font-medium text-ink hover:bg-warm-border transition">
              View Scoring
            </button>
          </div>
        </div>
        {error && <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>}
      </div>

      {loading && (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600" />
          <span className="ml-4 text-muted text-lg">Analyzing documents for fraud patterns...</span>
        </div>
      )}

      {result && !loading && (
        <>
          {/* Combined Score Header */}
          <div className={`rounded-xl shadow-sm border-2 p-6 ${rc(result.overall_risk_level).bg} ${rc(result.overall_risk_level).text} border-opacity-50`}
               style={{ borderColor: 'currentColor' }}>
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div>
                <p className="text-sm font-medium opacity-80">Combined Fraud Risk Score</p>
                <p className="text-5xl font-extrabold mt-1">{result.combined_fraud_score}<span className="text-2xl font-normal opacity-60">/100</span></p>
                <p className="text-sm mt-2 opacity-80">{result.company_name}</p>
              </div>
              <div className="text-right">
                <Badge level={result.overall_risk_level} />
                {result.red_flag_triggered && (
                  <p className="mt-2 text-sm font-bold text-red-700 bg-red-200 px-3 py-1 rounded-full">RED FLAG TRIGGERED</p>
                )}
                <p className="text-sm mt-2 opacity-80">{result.total_flags} flag{result.total_flags !== 1 ? 's' : ''} raised</p>
              </div>
            </div>
          </div>

          {/* Weight Breakdown */}
          {wb && (
            <div className="bg-warm-white rounded-xl shadow-warm border border-warm-border p-6">
              <h2 className="text-lg font-bold text-charcoal mb-4">Score Composition</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-blue-50 rounded-lg p-4 text-center">
                  <p className="text-xs text-blue-600 font-medium">Rules Engine ({wb.rules_weight})</p>
                  <p className="text-3xl font-bold text-blue-800 mt-1">{wb.rules_contribution}</p>
                </div>
                <div className="bg-purple-50 rounded-lg p-4 text-center">
                  <p className="text-xs text-purple-600 font-medium">ML Model ({wb.ml_weight})</p>
                  <p className="text-3xl font-bold text-purple-800 mt-1">{wb.ml_contribution}</p>
                </div>
                <div className="bg-orange-50 rounded-lg p-4 text-center">
                  <p className="text-xs text-orange-600 font-medium">Circular Trading ({wb.circular_trading_weight})</p>
                  <p className="text-3xl font-bold text-orange-800 mt-1">{wb.ct_contribution}</p>
                </div>
              </div>
            </div>
          )}

          {/* Data Sources */}
          {result.normalized_data_summary && (
            <div className="bg-warm-white rounded-xl shadow-warm border border-warm-border p-6">
              <h2 className="text-lg font-bold text-charcoal mb-3">Normalized Data Summary</h2>
              <div className="flex flex-wrap gap-2 mb-4">
                {(result.normalized_data_summary.sources_available || []).map(s => (
                  <span key={s} className="bg-parchment text-sienna text-xs font-medium px-2.5 py-1 rounded-full">{s}</span>
                ))}
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-sm">
                <div className="bg-cream rounded-lg p-3">
                  <p className="text-muted">GST Sales</p>
                  <p className="font-bold text-charcoal">Rs. {result.normalized_data_summary.gst_sales_cr?.toFixed(1)} Cr</p>
                </div>
                <div className="bg-cream rounded-lg p-3">
                  <p className="text-muted">Bank Inflows</p>
                  <p className="font-bold text-charcoal">Rs. {result.normalized_data_summary.bank_inflows_cr?.toFixed(4)} Cr</p>
                </div>
                <div className="bg-cream rounded-lg p-3">
                  <p className="text-muted">Annual Report Revenue</p>
                  <p className="font-bold text-charcoal">Rs. {result.normalized_data_summary.annual_revenue_cr?.toFixed(1)} Cr</p>
                </div>
              </div>
            </div>
          )}

          {/* Cross-Verification Rules */}
          {cv && (
            <div className="bg-warm-white rounded-xl shadow-warm border border-warm-border p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-charcoal">Cross-Verification Rules</h2>
                <div className="flex items-center gap-2">
                  <Badge level={cv.risk_level} />
                  <span className="text-sm font-bold text-muted">{cv.rule_score}/100</span>
                </div>
              </div>
              <ScoreGauge score={cv.rule_score} label="Rule Engine Score" />

              {/* Category Scores */}
              {cv.category_scores && Object.keys(cv.category_scores).length > 0 && (
                <div className="mt-4 flex flex-wrap gap-2">
                  {Object.entries(cv.category_scores).map(([cat, score]) => (
                    <span key={cat} className="bg-gray-100 text-gray-700 text-xs px-2.5 py-1 rounded-full">
                      {cat.replace(/_/g, ' ')}: <b>{score}</b>
                    </span>
                  ))}
                </div>
              )}

              {/* Anomalies List */}
              {cv.anomalies?.length > 0 && (
                <div className="mt-4 space-y-2">
                  <p className="text-sm font-medium text-muted">{cv.anomalies_count} Anomalies Found:</p>
                  {cv.anomalies.map((a, i) => (
                    <div key={i} className={`p-3 rounded-lg border text-sm ${a.severity === 'HIGH' ? 'bg-red-50 border-red-200' : a.severity === 'MEDIUM' ? 'bg-yellow-50 border-yellow-200' : 'bg-gray-50 border-gray-200'}`}>
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <span className="font-semibold">{a.rule}</span>
                          <span className={`ml-2 text-xs px-1.5 py-0.5 rounded ${a.severity === 'HIGH' ? 'bg-red-200 text-red-800' : 'bg-yellow-200 text-yellow-800'}`}>{a.severity}</span>
                        </div>
                        <span className="text-xs font-bold whitespace-nowrap text-gray-500">-{a.score_impact} pts</span>
                      </div>
                      <p className="text-gray-600 mt-1">{a.detail}</p>
                    </div>
                  ))}
                </div>
              )}

              {cv.summary && <p className="mt-4 text-sm text-muted italic">{cv.summary}</p>}
            </div>
          )}

          {/* Circular Trading */}
          {ct && (
            <div className="bg-warm-white rounded-xl shadow-warm border border-warm-border p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-charcoal">Circular Trading Detection</h2>
                <div className="flex items-center gap-2">
                  <Badge level={ct.risk_level} />
                  <span className="text-sm font-bold text-muted">{ct.combined_score}/100</span>
                </div>
              </div>
              <ScoreGauge score={ct.combined_score} label="Circular Trading Score" />

              {ct.flags?.length > 0 && (
                <div className="mt-3 space-y-1">
                  {ct.flags.map((f, i) => (
                    <div key={i} className="flex items-start gap-2 text-sm text-red-700 bg-red-50 p-2 rounded">
                      <span className="mt-0.5 text-red-400">!</span>
                      <span>{f}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Transaction Network Graph */}
              {ct.graph_analysis && ct.graph_analysis.entities > 0 && (
                <div className="mt-5 border-t pt-5">
                  <h3 className="text-md font-semibold text-charcoal mb-3">Transaction Network</h3>
                  
                  {/* Network Stats */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                    <div className="bg-parchment rounded-lg p-3 text-center">
                      <p className="text-xs text-sienna font-medium">Entities</p>
                      <p className="text-2xl font-bold text-charcoal">{ct.graph_analysis.entities}</p>
                    </div>
                    <div className="bg-parchment rounded-lg p-3 text-center">
                      <p className="text-xs text-sienna font-medium">Edges</p>
                      <p className="text-2xl font-bold text-charcoal">{ct.graph_analysis.edges}</p>
                    </div>
                    <div className={`rounded-lg p-3 text-center ${ct.graph_analysis.cycle_count > 0 ? 'bg-red-50' : 'bg-green-50'}`}>
                      <p className={`text-xs font-medium ${ct.graph_analysis.cycle_count > 0 ? 'text-red-500' : 'text-green-500'}`}>Cycles</p>
                      <p className={`text-2xl font-bold ${ct.graph_analysis.cycle_count > 0 ? 'text-red-800' : 'text-green-800'}`}>{ct.graph_analysis.cycle_count}</p>
                    </div>
                    <div className="bg-parchment rounded-lg p-3 text-center">
                      <p className="text-xs text-sienna font-medium">Graph Score</p>
                      <p className="text-2xl font-bold text-charcoal">{ct.graph_analysis.graph_risk_score}</p>
                    </div>
                  </div>

                  {/* Entity List */}
                  {ct.graph_analysis.entity_list?.length > 0 && (
                    <div className="mb-4">
                      <p className="text-sm font-medium text-muted mb-2">Discovered Entities:</p>
                      <div className="flex flex-wrap gap-2">
                        {ct.graph_analysis.entity_list.map((entity, i) => (
                          <span key={i} className={`text-xs font-medium px-2.5 py-1 rounded-full ${
                            entity === result.company_name
                              ? 'bg-parchment text-sienna ring-1 ring-sienna'
                              : 'bg-cream text-ink'
                          }`}>
                            {entity}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Edge List (Transaction Flows) */}
                  {ct.graph_analysis.edge_list?.length > 0 && (
                    <div className="mb-4">
                      <p className="text-sm font-medium text-muted mb-2">Transaction Flows:</p>
                      <div className="space-y-1.5">
                        {ct.graph_analysis.edge_list.map((e, i) => (
                          <div key={i} className="flex items-center gap-2 text-sm bg-cream p-2 rounded-lg">
                            <span className="font-medium text-charcoal truncate max-w-[180px]">{e.from}</span>
                            <span className="text-muted flex-shrink-0">&rarr;</span>
                            <span className="font-medium text-charcoal truncate max-w-[180px]">{e.to}</span>
                            <span className="ml-auto text-xs text-muted flex-shrink-0">
                              {e.amount > 0 ? `Rs. ${e.amount.toFixed(4)} Cr` : ''}
                              {e.count > 0 ? ` (${e.count}x)` : ''}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Cycles Detected */}
                  {ct.graph_analysis.cycles_detected?.length > 0 && (
                    <div className="mb-4 p-4 bg-red-50 rounded-lg border border-red-200">
                      <p className="text-sm font-semibold text-red-800 mb-2">Circular Trading Loops Detected:</p>
                      {ct.graph_analysis.cycles_detected.map((cycle, i) => (
                        <div key={i} className="flex items-center gap-1 text-sm text-red-700 py-1">
                          <span className="font-bold text-red-500">#{i + 1}</span>
                          <span className="ml-1">{cycle.join(' \u2192 ')} \u2192 {cycle[0]}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Reciprocal Pairs */}
                  {ct.graph_analysis.reciprocal_pairs?.length > 0 && (
                    <div className="p-3 bg-orange-50 rounded-lg border border-orange-200">
                      <p className="text-sm font-semibold text-orange-800 mb-1">Reciprocal Trading Pairs:</p>
                      {ct.graph_analysis.reciprocal_pairs.map((pair, i) => (
                        <p key={i} className="text-sm text-orange-700">
                          {pair.entity_a} &harr; {pair.entity_b}
                        </p>
                      ))}
                    </div>
                  )}

                  {/* Strongly Connected Components */}
                  {ct.graph_analysis.strongly_connected_components?.length > 0 && (
                    <div className="mt-3 p-3 bg-amber-50 rounded-lg border border-amber-200">
                      <p className="text-sm font-semibold text-amber-800 mb-1">Tight Trading Clusters (SCCs):</p>
                      {ct.graph_analysis.strongly_connected_components.map((scc, i) => (
                        <p key={i} className="text-sm text-amber-700">Cluster {i + 1}: {scc.join(', ')}</p>
                      ))}
                    </div>
                  )}

                  {/* Concentration Analysis */}
                  {ct.graph_analysis.concentration_analysis && (
                    Object.keys(ct.graph_analysis.concentration_analysis.inflow_sources || {}).length > 0 ||
                    Object.keys(ct.graph_analysis.concentration_analysis.outflow_destinations || {}).length > 0
                  ) && (
                    <div className="mt-4 border-t pt-4">
                      <h4 className="text-sm font-semibold text-ink mb-3">Counterparty Concentration</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Inflow Sources */}
                        {Object.keys(ct.graph_analysis.concentration_analysis.inflow_sources || {}).length > 0 && (
                          <div>
                            <p className="text-xs font-medium text-green-700 mb-2">Inflow Sources (Rs. {ct.graph_analysis.concentration_analysis.total_inflow_cr?.toFixed(2)} Cr total)</p>
                            <div className="space-y-1.5">
                              {Object.entries(ct.graph_analysis.concentration_analysis.inflow_sources).map(([entity, amt], i) => {
                                const pct = ct.graph_analysis.concentration_analysis.total_inflow_cr > 0
                                  ? (amt / ct.graph_analysis.concentration_analysis.total_inflow_cr * 100)
                                  : 0;
                                return (
                                  <div key={i} className="text-xs">
                                    <div className="flex justify-between mb-0.5">
                                      <span className="text-ink truncate max-w-[180px]">{entity}</span>
                                      <span className="text-muted">Rs. {amt.toFixed(2)} Cr ({pct.toFixed(0)}%)</span>
                                    </div>
                                    <div className="w-full bg-parchment rounded-full h-1.5">
                                      <div className={`h-1.5 rounded-full ${pct > 60 ? 'bg-red-500' : 'bg-green-500'}`} style={{ width: `${Math.min(pct, 100)}%` }} />
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}
                        {/* Outflow Destinations */}
                        {Object.keys(ct.graph_analysis.concentration_analysis.outflow_destinations || {}).length > 0 && (
                          <div>
                            <p className="text-xs font-medium text-red-700 mb-2">Outflow Destinations (Rs. {ct.graph_analysis.concentration_analysis.total_outflow_cr?.toFixed(2)} Cr total)</p>
                            <div className="space-y-1.5">
                              {Object.entries(ct.graph_analysis.concentration_analysis.outflow_destinations).map(([entity, amt], i) => {
                                const pct = ct.graph_analysis.concentration_analysis.total_outflow_cr > 0
                                  ? (amt / ct.graph_analysis.concentration_analysis.total_outflow_cr * 100)
                                  : 0;
                                return (
                                  <div key={i} className="text-xs">
                                    <div className="flex justify-between mb-0.5">
                                      <span className="text-ink truncate max-w-[180px]">{entity}</span>
                                      <span className="text-muted">Rs. {amt.toFixed(2)} Cr ({pct.toFixed(0)}%)</span>
                                    </div>
                                    <div className="w-full bg-parchment rounded-full h-1.5">
                                      <div className={`h-1.5 rounded-full ${pct > 60 ? 'bg-red-500' : 'bg-orange-500'}`} style={{ width: `${Math.min(pct, 100)}%` }} />
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                      {/* Reciprocal Counterparties */}
                      {ct.graph_analysis.concentration_analysis.reciprocal_counterparties?.length > 0 && (
                        <div className="mt-3 p-3 bg-red-50 rounded-lg border border-red-200">
                          <p className="text-xs font-semibold text-red-800 mb-1">Reciprocal Counterparties (both customer &amp; vendor):</p>
                          <div className="flex flex-wrap gap-2">
                            {ct.graph_analysis.concentration_analysis.reciprocal_counterparties.map((e, i) => (
                              <span key={i} className="text-xs font-medium bg-red-200 text-red-800 px-2.5 py-1 rounded-full">{e}</span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* ML Prediction */}
          {ml && (
            <div className="bg-warm-white rounded-xl shadow-warm border border-warm-border p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-charcoal">ML Fraud Prediction</h2>
                <div className="flex items-center gap-2">
                  <Badge level={ml.ml_risk_level} />
                  <span className={`text-sm font-bold px-2 py-0.5 rounded ${ml.prediction === 'FRAUDULENT' ? 'bg-red-200 text-red-800' : 'bg-green-200 text-green-800'}`}>
                    {ml.prediction}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-cream rounded-lg p-4 text-center">
                  <p className="text-xs text-muted">Fraud Probability</p>
                  <p className="text-3xl font-bold text-charcoal">{(ml.fraud_probability * 100).toFixed(1)}%</p>
                </div>
                <div className="bg-cream rounded-lg p-4 text-center">
                  <p className="text-xs text-muted">ML Score</p>
                  <p className="text-3xl font-bold text-charcoal">{ml.ml_score}</p>
                </div>
              </div>

              {/* Top Features */}
              {ml.top_features?.length > 0 && (
                <div>
                  <p className="text-sm font-medium text-muted mb-2">Top Contributing Features:</p>
                  <div className="space-y-2">
                    {ml.top_features.map((f, i) => (
                      <div key={i} className="flex items-center gap-3 text-sm">
                        <span className="font-mono text-muted w-48 truncate">{f.feature}</span>
                        <div className="flex-1 bg-parchment rounded-full h-2">
                          <div className="bg-purple-500 h-2 rounded-full" style={{ width: `${f.importance * 100}%` }} />
                        </div>
                        <span className="text-muted w-20 text-right">{(f.importance * 100).toFixed(1)}%</span>
                        <span className="font-mono text-xs text-muted w-24 text-right">{f.value?.toFixed(4)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* All Flags Summary */}
          {result.all_flags?.length > 0 && (
            <div className="bg-warm-white rounded-xl shadow-warm border border-warm-border p-6">
              <h2 className="text-lg font-bold text-charcoal mb-3">All Flags ({result.all_flags.length})</h2>
              <ul className="space-y-1.5">
                {result.all_flags.map((f, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <span className="text-red-500 mt-0.5 font-bold">!</span>
                    <span className="text-ink">{f}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </>
      )}

      {!result && !loading && (
        <div className="bg-warm-white rounded-xl shadow-warm border border-warm-border p-12 text-center">
          <div className="text-6xl mb-4">&#x1F50D;</div>
          <h3 className="text-xl font-bold text-charcoal">Ready to Analyze</h3>
          <p className="text-muted mt-2 max-w-md mx-auto">
            Click "Run Fraud Verification" to cross-verify parsed documents, detect circular trading patterns, and run ML-based fraud prediction.
          </p>
        </div>
      )}
    </div>
  );
};

export default FraudDetection;
