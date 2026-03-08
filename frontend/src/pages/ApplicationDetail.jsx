import {
    AlertTriangle,
    ArrowLeft,
    Download
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { api } from '../utils/api';
import { DECISION_LABELS } from '../utils/constants';
import { formatCurrency, getDecisionBadgeClass, getRiskLevelClass } from '../utils/formatters';

const ApplicationDetail = () => {
  const { id } = useParams();
  const [application, setApplication] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadApplication();
  }, [id]);

  const loadApplication = async () => {
    try {
      setLoading(true);
      const data = await api.getApplication(id);
      setApplication(data);
    } catch (error) {
      console.error('Failed to load application:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!application) {
    return (
      <div className="text-center py-12">
        <AlertTriangle size={48} className="mx-auto mb-4 text-gray-400" />
        <p className="text-gray-600">Application not found</p>
        <Link to="/" className="btn-primary mt-4 inline-block">
          Back to Dashboard
        </Link>
      </div>
    );
  }

  const { 
    company_details, 
    financial_analysis, 
    ai_research_agent, 
    primary_due_diligence,
    risk_scoring_engine, 
    cam_generation 
  } = application;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <Link to="/" className="text-blue-600 hover:text-blue-800 flex items-center space-x-2 mb-2">
            <ArrowLeft size={20} />
            <span>Back to Dashboard</span>
          </Link>
          <h1 className="text-3xl font-bold text-gray-900">{company_details.company_name}</h1>
          <p className="text-gray-600 mt-1">
            {application.application_id} • {company_details.sector}
          </p>
        </div>
        <button className="btn-primary flex items-center space-x-2">
          <Download size={20} />
          <span>Download CAM</span>
        </button>
      </div>

      {/* Decision Banner */}
      <div className={`card ${
        risk_scoring_engine.decision === 'APPROVE' ? 'bg-green-50 border-2 border-green-200' :
        risk_scoring_engine.decision === 'CONDITIONAL_APPROVE' ? 'bg-yellow-50 border-2 border-yellow-200' :
        'bg-red-50 border-2 border-red-200'
      }`}>
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">
              <span className={`badge ${getDecisionBadgeClass(risk_scoring_engine.decision)} text-lg`}>
                {DECISION_LABELS[risk_scoring_engine.decision]}
              </span>
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
              <div>
                <p className="text-sm text-gray-600">Credit Score</p>
                <p className="text-2xl font-bold">
                  {risk_scoring_engine.final_credit_score}/{risk_scoring_engine.max_score}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Requested Limit</p>
                <p className="text-2xl font-bold">{formatCurrency(company_details.requested_limit_cr)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600">Recommended Limit</p>
                <p className="text-2xl font-bold text-red-600">
                  {formatCurrency(risk_scoring_engine.recommended_limit_cr)}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Executive Summary */}
      <div className="card">
        <h2 className="text-xl font-bold mb-4">Executive Summary</h2>
        <p className="text-gray-700 leading-relaxed">{cam_generation.executive_summary}</p>
      </div>

      {/* SHAP Explainability */}
      <div className="card">
        <h2 className="text-xl font-bold mb-4">Decision Factors (SHAP Analysis)</h2>
        <p className="text-sm text-gray-600 mb-6">
          Key features that influenced the credit decision
        </p>
        
        <div className="space-y-3">
          {risk_scoring_engine.shap_explanations.map((shap, idx) => (
            <div key={idx} className="flex items-center">
              <div className="w-1/3">
                <p className="text-sm font-medium text-gray-700">{shap.feature}</p>
              </div>
              <div className="w-2/3 flex items-center space-x-3">
                <div className="flex-1 bg-gray-200 rounded-full h-8 relative overflow-hidden">
                  <div
                    className={`h-full flex items-center justify-end px-3 text-sm font-bold text-white ${
                      shap.type === 'POSITIVE' ? 'bg-green-500' : 'bg-red-500'
                    }`}
                    style={{
                      width: `${Math.abs(shap.impact_value) * 3}%`,
                      float: shap.type === 'POSITIVE' ? 'left' : 'right'
                    }}
                  >
                    {shap.impact_value > 0 ? '+' : ''}{shap.impact_value.toFixed(1)}
                  </div>
                </div>
                <span className={`text-sm font-bold w-16 text-right ${
                  shap.type === 'POSITIVE' ? 'text-green-600' : 'text-red-600'
                }`}>
                  {shap.impact_value > 0 ? '+' : ''}{shap.impact_value.toFixed(1)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Financial Analysis */}
      <div className="card">
        <h2 className="text-xl font-bold mb-4">Financial Analysis</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div>
            <h3 className="font-semibold text-gray-700 mb-3">Key Ratios</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">DSCR:</span>
                <span className="font-bold">{financial_analysis.calculated_ratios.dscr}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Current Ratio:</span>
                <span className="font-bold">{financial_analysis.calculated_ratios.current_ratio}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">D/E Ratio:</span>
                <span className="font-bold">{financial_analysis.calculated_ratios.debt_to_equity}</span>
              </div>
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-gray-700 mb-3">Revenue Metrics</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">GSTR-1 Sales:</span>
                <span className="font-bold">{formatCurrency(financial_analysis.raw_data_extracted.gstr_1_sales_cr)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Bank Inflows:</span>
                <span className="font-bold">{formatCurrency(financial_analysis.raw_data_extracted.bank_statement_inflows_cr)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Variance:</span>
                <span className={getRiskLevelClass(financial_analysis.reconciliation_flags.circular_trading_risk)}>
                  {financial_analysis.reconciliation_flags.gst_vs_bank_variance_percent.toFixed(2)}%
                </span>
              </div>
            </div>
          </div>

          <div>
            <h3 className="font-semibold text-gray-700 mb-3">Risk Flags</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Circular Trading:</span>
                <span className={`badge ${
                  financial_analysis.reconciliation_flags.circular_trading_risk === 'LOW' ? 'bg-green-100 text-green-800' :
                  financial_analysis.reconciliation_flags.circular_trading_risk === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {financial_analysis.reconciliation_flags.circular_trading_risk}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Red Flag:</span>
                <span className={`font-bold ${financial_analysis.reconciliation_flags.red_flag_triggered ? 'text-red-600' : 'text-green-600'}`}>
                  {financial_analysis.reconciliation_flags.red_flag_triggered ? 'Yes' : 'No'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* AI Research Findings */}
      <div className="card">
        <h2 className="text-xl font-bold mb-4">AI Research Findings</h2>
        
        <div className="space-y-6">
          {/* Promoter Checks */}
          <div>
            <h3 className="font-semibold text-gray-700 mb-3">Promoter Background</h3>
            {ai_research_agent.promoter_checks.map((check, idx) => (
              <div key={idx} className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="font-medium">{check.name}</p>
                    <p className="text-sm text-gray-600 mt-1">{check.finding}</p>
                  </div>
                  <span className={`badge ${
                    check.sentiment === 'POSITIVE' ? 'bg-green-100 text-green-800' :
                    check.sentiment === 'NEGATIVE' ? 'bg-red-100 text-red-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {check.sentiment}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Litigation */}
          <div>
            <h3 className="font-semibold text-gray-700 mb-3">Litigation & Legal Issues</h3>
            {ai_research_agent.litigation_and_nclt.map((lit, idx) => (
              <div key={idx} className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="font-medium text-red-900">{lit.source}</p>
                    <p className="text-sm text-red-700 mt-1">{lit.summary}</p>
                  </div>
                  <span className="text-red-600 font-bold ml-4">
                    {lit.severity_penalty} pts
                  </span>
                </div>
              </div>
            ))}
          </div>

          {/* Sector Analysis */}
          <div>
            <h3 className="font-semibold text-gray-700 mb-3">Sector Headwinds</h3>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-900">{ai_research_agent.sector_headwinds}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Due Diligence Notes */}
      {primary_due_diligence && (
        <div className="card">
          <h2 className="text-xl font-bold mb-4">Due Diligence Notes</h2>
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-gray-700 mb-3">{primary_due_diligence.credit_officer_notes}</p>
            <div className="flex items-center justify-between pt-3 border-t border-yellow-200">
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-600">AI Analysis:</span>
                <span className="badge bg-yellow-100 text-yellow-800">
                  {primary_due_diligence.ai_translated_impact.risk_category}
                </span>
                <span className={`badge ${
                  primary_due_diligence.ai_translated_impact.severity === 'LOW' ? 'bg-green-100 text-green-800' :
                  primary_due_diligence.ai_translated_impact.severity === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                  'bg-red-100 text-red-800'
                }`}>
                  {primary_due_diligence.ai_translated_impact.severity}
                </span>
              </div>
              <span className="text-red-600 font-bold">
                {primary_due_diligence.ai_translated_impact.score_adjustment} pts
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ApplicationDetail;
