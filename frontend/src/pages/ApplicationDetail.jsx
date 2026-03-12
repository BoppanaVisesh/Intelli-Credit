import { ArrowLeft } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../utils/api';

const STEPS = [
  {
    key: 'ingestion',
    icon: '📄',
    label: 'Data Ingestion',
    desc: 'Upload & parse financial documents (Annual Report, Bank Statements, GST Returns)',
    route: 'ingestion',
  },
  {
    key: 'research',
    icon: '🔍',
    label: 'External Intelligence',
    desc: 'News analysis, litigation search, promoter profiling, sector & regulatory checks',
    route: 'research',
  },
  {
    key: 'due_diligence',
    icon: '📝',
    label: 'Primary Insights',
    desc: 'Site visits, management interviews, officer observations with AI analysis',
    route: 'due-diligence',
  },
  {
    key: 'fraud',
    icon: '🛡️',
    label: 'Fraud Detection',
    desc: 'Cross-verification, circular trading detection & ML fraud prediction',
    route: 'fraud',
  },
  {
    key: 'scoring',
    icon: '📊',
    label: 'Credit Scoring',
    desc: 'Five Cs scoring with explainable decision reasons',
    route: 'scoring',
  },
  {
    key: 'cam',
    icon: '📋',
    label: 'CAM Generation',
    desc: 'Credit Appraisal Memo with full analysis report',
    route: 'cam',
  },
  {
    key: 'analysis',
    icon: '🧠',
    label: 'Pre-Cognitive Analysis',
    desc: 'Secondary research, triangulation, reasoning engine & SWOT report',
    route: 'analysis',
  },
];

const STATUS_STYLES = {
  completed: { bg: 'bg-green-100', text: 'text-green-800', label: 'Completed', dot: 'bg-green-500' },
  in_progress: { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'In Progress', dot: 'bg-yellow-500' },
  not_started: { bg: 'bg-gray-100', text: 'text-gray-600', label: 'Not Started', dot: 'bg-gray-400' },
};

const RISK_COLORS = {
  HIGH: 'bg-red-100 text-red-800',
  MEDIUM: 'bg-yellow-100 text-yellow-800',
  LOW: 'bg-green-100 text-green-800',
};

const ApplicationDetail = () => {
  const { id } = useParams();
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadSummary();
  }, [id]);

  const loadSummary = async () => {
    try {
      setLoading(true);
      const data = await api.getApplicationSummary(id);
      setSummary(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-terracotta"></div>
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="text-center py-12">
        <p className="text-muted mb-4">{error || 'Application not found'}</p>
        <Link to="/" className="btn-primary inline-block">Back to Dashboard</Link>
      </div>
    );
  }

  const { pipeline } = summary;
  const completedSteps = STEPS.filter(s => pipeline[s.key]?.status === 'completed').length;

  const getStepDetail = (key) => {
    const p = pipeline[key];
    if (!p) return null;
    switch (key) {
      case 'ingestion':
        return p.docs_uploaded > 0
          ? `${p.docs_parsed}/${p.docs_uploaded} documents parsed`
          : null;
      case 'research':
        return p.count > 0
          ? `${p.count} checks completed${p.overall_risk ? ` | Risk: ${p.overall_risk}` : ''}`
          : null;
      case 'due_diligence':
        return p.count > 0
          ? `${p.count} insights | Score adjustment: ${p.total_adjustment > 0 ? '+' : ''}${p.total_adjustment} pts`
          : null;
      case 'fraud':
        return p.risk_level && p.risk_level !== 'NOT_RUN'
          ? `Risk: ${p.risk_level}${p.red_flag ? ' | RED FLAG' : ''}`
          : null;
      case 'scoring':
        return p.score
          ? `Score: ${p.score}/100 | Decision: ${p.decision}`
          : null;
      case 'cam':
        return p.url ? 'Report generated' : null;
      case 'analysis':
        return p.status === 'completed' ? 'Analysis complete' : null;
      default:
        return null;
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <Link to="/" className="text-sienna hover:text-terracotta flex items-center space-x-2 mb-3">
          <ArrowLeft size={20} />
          <span>Back to Dashboard</span>
        </Link>
        <div className="card">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-charcoal">{summary.company_name}</h1>
              <p className="text-muted text-sm mt-1">
                {summary.application_id} &bull; {summary.sector} &bull; Requested: &#8377;{summary.requested_limit_cr} Cr
              </p>
              <p className="text-xs text-muted mt-1">CIN: {summary.mca_cin}</p>
            </div>
            <div className="text-right">
              <span className={`inline-flex px-3 py-1 rounded-full text-sm font-medium ${
                summary.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                summary.status === 'PROCESSING' ? 'bg-parchment text-sienna' :
                'bg-cream text-ink'
              }`}>
                {summary.status}
              </span>
              <p className="text-xs text-muted mt-1">{completedSteps}/{STEPS.length} steps done</p>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mt-4">
            <div className="w-full bg-parchment rounded-full h-2">
              <div
                className="bg-sienna h-2 rounded-full transition-all duration-300"
                style={{ width: `${(completedSteps / STEPS.length) * 100}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Pipeline Steps */}
      <div className="space-y-3">
        <h2 className="text-lg font-bold text-charcoal">Credit Appraisal Pipeline</h2>

        {STEPS.map((step, idx) => {
          const stepData = pipeline[step.key] || {};
          const status = stepData.status || 'not_started';
          const style = STATUS_STYLES[status];
          const detail = getStepDetail(step.key);

          return (
            <Link
              key={step.key}
              to={`/application/${id}/${step.route}`}
              className="card block hover:shadow-md transition-shadow border-l-4"
              style={{
                borderLeftColor: status === 'completed' ? '#22c55e' : status === 'in_progress' ? '#eab308' : '#d1d5db',
              }}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="text-2xl w-10 text-center">{step.icon}</div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-muted font-mono">Step {idx + 1}</span>
                      <h3 className="font-semibold text-charcoal">{step.label}</h3>
                    </div>
                    <p className="text-sm text-muted">{step.desc}</p>
                    {detail && (
                      <p className="text-sm font-medium text-ink mt-1">
                        {detail}
                        {step.key === 'research' && stepData.overall_risk && (
                          <span className={`ml-2 px-2 py-0.5 rounded-full text-xs font-medium ${RISK_COLORS[stepData.overall_risk] || ''}`}>
                            {stepData.overall_risk}
                          </span>
                        )}
                      </p>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${style.bg} ${style.text}`}>
                    <span className={`w-1.5 h-1.5 rounded-full mr-1.5 ${style.dot}`} />
                    {style.label}
                  </span>
                  <span className="text-muted text-lg">&rsaquo;</span>
                </div>
              </div>
            </Link>
          );
        })}
      </div>
    </div>
  );
};

export default ApplicationDetail;
