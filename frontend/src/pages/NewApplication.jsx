import { AlertCircle, ArrowLeft, ArrowRight, Briefcase, Building2, Calendar, CheckCircle2, Clock, FileText, Hash, IndianRupee, Landmark, LayoutGrid, MapPin, Percent, Shield, Target, Users } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';

const STEPS = [
  { key: 'entity', label: 'Entity Details', icon: Building2 },
  { key: 'loan',   label: 'Loan Details',   icon: IndianRupee },
  { key: 'review', label: 'Review & Submit', icon: CheckCircle2 },
];

const SECTORS = ['Aviation','IT Services','Industrial Manufacturing','Textiles','Pharmaceuticals','Real Estate','Banking','FMCG','Auto Components','Food Processing','Logistics','Chemicals','Infrastructure','Energy','Retail','Healthcare'];

const LOAN_TYPES = ['Working Capital','Term Loan','CC/OD (Cash Credit / Overdraft)','BG/LC (Bank Guarantee / Letter of Credit)','Project Finance','Trade Finance'];

const NewApplication = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [formData, setFormData] = useState({
    // Step 1 — Entity
    company_name: '',
    mca_cin: '',
    pan: '',
    sector: '',
    incorporation_date: '',
    registered_address: '',
    annual_turnover_cr: '',
    employee_count: '',
    promoter_names: '',
    // Step 2 — Loan
    requested_limit_cr: '',
    loan_type: '',
    loan_tenure_months: '',
    interest_type: '',
    collateral_offered: '',
    purpose_of_loan: '',
    existing_banking: '',
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  /* ---- Step validation ---- */
  const isStep1Valid = () => formData.company_name.trim() && formData.mca_cin.trim() && formData.sector;
  const isStep2Valid = () => {
    const limit = parseFloat(formData.requested_limit_cr);
    return !isNaN(limit) && limit > 0 && formData.loan_type;
  };

  const nextStep = () => {
    if (step === 0 && !isStep1Valid()) { setError('Please fill in Company Name, CIN, and Sector'); return; }
    if (step === 1 && !isStep2Valid()) { setError('Please fill in Requested Limit and Loan Type'); return; }
    setError(null);
    setStep(s => Math.min(s + 1, 2));
  };
  const prevStep = () => { setError(null); setStep(s => Math.max(s - 1, 0)); };

  const handleSubmit = async () => {
    setError(null);

    // Validate numeric fields
    const limitVal = parseFloat(formData.requested_limit_cr);
    if (isNaN(limitVal) || limitVal <= 0) {
      setError('Requested limit must be a positive number'); return;
    }
    const turnoverVal = formData.annual_turnover_cr ? parseFloat(formData.annual_turnover_cr) : null;
    if (turnoverVal !== null && (isNaN(turnoverVal) || turnoverVal < 0)) {
      setError('Annual turnover must be a non-negative number'); return;
    }
    const empVal = formData.employee_count ? parseInt(formData.employee_count, 10) : null;
    if (empVal !== null && (isNaN(empVal) || empVal < 0)) {
      setError('Employee count must be a non-negative number'); return;
    }
    const tenureVal = formData.loan_tenure_months ? parseInt(formData.loan_tenure_months, 10) : null;
    if (tenureVal !== null && (isNaN(tenureVal) || tenureVal <= 0)) {
      setError('Loan tenure must be a positive number'); return;
    }

    setLoading(true);
    try {
      const payload = {
        company_name: formData.company_name.trim(),
        mca_cin: formData.mca_cin.trim(),
        sector: formData.sector,
        requested_limit_cr: limitVal,
      };
      if (formData.pan) payload.pan = formData.pan.trim();
      if (formData.incorporation_date) payload.incorporation_date = formData.incorporation_date;
      if (formData.registered_address) payload.registered_address = formData.registered_address.trim();
      if (turnoverVal !== null) payload.annual_turnover_cr = turnoverVal;
      if (empVal !== null) payload.employee_count = empVal;
      if (formData.promoter_names) payload.promoter_names = formData.promoter_names.trim();
      if (formData.loan_type) payload.loan_type = formData.loan_type;
      if (tenureVal !== null) payload.loan_tenure_months = tenureVal;
      if (formData.interest_type) payload.interest_type = formData.interest_type;
      if (formData.collateral_offered) payload.collateral_offered = formData.collateral_offered.trim();
      if (formData.purpose_of_loan) payload.purpose_of_loan = formData.purpose_of_loan.trim();
      if (formData.existing_banking) payload.existing_banking = formData.existing_banking.trim();
      const result = await api.createApplication(payload);
      if (!result?.application_id) {
        setError('Server did not return an application ID'); return;
      }
      navigate(`/application/${result.application_id}`);
    } catch (err) {
      setError(err.message || 'Failed to create application');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400;1,600&family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@400;500&display=swap');

        :root {
          --cream: #F5F0E8;
          --parchment: #EDE5D4;
          --warm-white: #FAF7F2;
          --sienna: #A0522D;
          --terracotta: #CB6E45;
          --gold: #B8860B;
          --gold-light: #D4A017;
          --charcoal: #2C2416;
          --ink: #3D3020;
          --muted: #7A6850;
          --border: #DDD4C0;
          --border-warm: #C9BCA8;
          --shadow-warm: rgba(160,82,45,0.12);
          --forest: #4D7C3A;
        }

        .na-wrap {
          min-height: 100vh;
          background: var(--cream);
          font-family: 'DM Sans', sans-serif;
          position: relative;
          overflow-x: hidden;
        }

        .na-wrap::after {
          content: '';
          position: fixed;
          top: -200px; right: -100px;
          width: 500px; height: 900px;
          background: linear-gradient(160deg, rgba(203,110,69,0.07) 0%, rgba(184,134,11,0.04) 50%, transparent 80%);
          transform: rotate(-15deg);
          pointer-events: none;
          z-index: 0;
        }

        .na-inner {
          position: relative;
          z-index: 1;
          max-width: 820px;
          margin: 0 auto;
          padding: 0 2.5rem 4rem;
        }

        /* ── TOP BAR ── */
        .na-topbar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 2rem 0 2.5rem;
          border-bottom: 1.5px solid var(--border);
          margin-bottom: 2.5rem;
        }

        .na-brand {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .na-brand-mark {
          position: relative;
          width: 48px; height: 48px;
          display: flex; align-items: center; justify-content: center;
        }

        .na-brand-ring {
          position: absolute; inset: -4px;
          border-radius: 50%;
          border: 1.5px solid var(--terracotta);
          opacity: 0.4;
          animation: ring-spin 12s linear infinite;
        }

        .na-brand-ring-2 {
          position: absolute; inset: -9px;
          border-radius: 50%;
          border: 1px dashed var(--gold);
          opacity: 0.25;
          animation: ring-spin 20s linear infinite reverse;
        }

        @keyframes ring-spin { to { transform: rotate(360deg); } }

        .na-brand-icon {
          width: 48px; height: 48px;
          background: linear-gradient(135deg, var(--sienna) 0%, var(--terracotta) 100%);
          border-radius: 50%;
          display: flex; align-items: center; justify-content: center;
          box-shadow: 0 4px 16px rgba(160,82,45,0.35);
        }

        .na-brand-eyebrow {
          font-family: 'DM Mono', monospace;
          font-size: 0.6rem;
          letter-spacing: 0.2em;
          text-transform: uppercase;
          color: var(--terracotta);
          margin-bottom: 0.2rem;
        }

        .na-brand-name {
          font-family: 'Playfair Display', serif;
          font-size: 1.6rem;
          font-weight: 700;
          color: var(--charcoal);
          line-height: 1;
          letter-spacing: -0.01em;
        }

        .na-back-btn {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          font-family: 'DM Mono', monospace;
          font-size: 0.7rem;
          letter-spacing: 0.1em;
          text-transform: uppercase;
          color: var(--muted);
          text-decoration: none;
          padding: 0.5rem 1rem;
          border-radius: 8px;
          border: 1px solid var(--border);
          background: var(--warm-white);
          transition: all 0.15s;
          cursor: pointer;
          background: none;
        }

        .na-back-btn:hover { color: var(--sienna); border-color: rgba(160,82,45,0.3); background: rgba(160,82,45,0.04); }

        /* ── PAGE HEADER ── */
        .na-page-header { margin-bottom: 2.5rem; }

        .na-eyebrow {
          font-family: 'DM Mono', monospace;
          font-size: 0.62rem;
          letter-spacing: 0.18em;
          text-transform: uppercase;
          color: var(--terracotta);
          margin-bottom: 0.5rem;
        }

        .na-h1 {
          font-family: 'Playfair Display', serif;
          font-size: 2.6rem;
          font-weight: 700;
          color: var(--charcoal);
          line-height: 1.05;
          letter-spacing: -0.02em;
          margin-bottom: 0.6rem;
        }

        .na-h1 em { font-style: italic; color: var(--terracotta); }

        .na-sub {
          font-size: 0.9rem;
          color: var(--muted);
          font-weight: 300;
          line-height: 1.6;
        }

        .ornament {
          display: flex; align-items: center; gap: 0.75rem;
          margin-bottom: 2rem;
        }
        .ornament-line { height: 1px; flex: 1; background: linear-gradient(to right, transparent, var(--border-warm), transparent); }
        .ornament-diamond { width: 6px; height: 6px; background: var(--terracotta); transform: rotate(45deg); opacity: 0.5; }

        /* ── ERROR ── */
        .na-error {
          display: flex;
          align-items: flex-start;
          gap: 0.85rem;
          background: rgba(160,48,48,0.06);
          border: 1.5px solid rgba(160,48,48,0.2);
          border-radius: 12px;
          padding: 1rem 1.25rem;
          margin-bottom: 1.75rem;
        }

        .na-error-text h3 {
          font-family: 'Playfair Display', serif;
          font-size: 0.95rem;
          font-weight: 600;
          color: #7A2020;
          margin-bottom: 0.2rem;
        }

        .na-error-text p {
          font-size: 0.82rem;
          color: #9A3030;
        }

        /* ── FORM CARD ── */
        .na-card {
          background: var(--warm-white);
          border: 1.5px solid var(--border);
          border-radius: 20px;
          overflow: hidden;
          box-shadow: 0 2px 16px rgba(0,0,0,0.04);
          margin-bottom: 1.5rem;
        }

        .na-card-head {
          padding: 1.25rem 1.75rem;
          border-bottom: 1.5px solid var(--border);
          background: linear-gradient(to right, var(--parchment), var(--warm-white));
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .na-card-head-icon {
          width: 32px; height: 32px;
          background: rgba(160,82,45,0.09);
          border: 1px solid rgba(160,82,45,0.18);
          border-radius: 8px;
          display: flex; align-items: center; justify-content: center;
        }

        .na-card-head-title {
          font-family: 'Playfair Display', serif;
          font-size: 1.05rem;
          font-weight: 600;
          color: var(--charcoal);
        }

        .na-card-body { padding: 1.75rem; }

        /* ── FORM GRID ── */
        .na-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1.25rem;
        }

        @media (max-width: 640px) { .na-grid { grid-template-columns: 1fr; } }

        .na-field { display: flex; flex-direction: column; gap: 0.5rem; }
        .na-field-full { grid-column: 1 / -1; }

        .na-label {
          font-family: 'DM Mono', monospace;
          font-size: 0.62rem;
          font-weight: 500;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          color: var(--muted);
        }

        .na-input-wrap { position: relative; }

        .na-input-icon {
          position: absolute;
          left: 0.9rem; top: 50%;
          transform: translateY(-50%);
          color: var(--border-warm);
          pointer-events: none;
          transition: color 0.15s;
        }

        .na-input, .na-select {
          width: 100%;
          padding: 0.75rem 0.9rem 0.75rem 2.5rem;
          background: var(--cream);
          border: 1.5px solid var(--border);
          border-radius: 10px;
          font-family: 'DM Sans', sans-serif;
          font-size: 0.9rem;
          color: var(--charcoal);
          outline: none;
          transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
          appearance: none;
          box-sizing: border-box;
        }

        .na-input::placeholder { color: var(--border-warm); font-weight: 300; }

        .na-input:focus, .na-select:focus {
          border-color: var(--terracotta);
          background: var(--warm-white);
          box-shadow: 0 0 0 3px rgba(203,110,69,0.1);
        }

        .na-input:focus + .na-input-focus-line,
        .na-select:focus + .na-input-focus-line { opacity: 1; }

        .na-input:focus ~ .na-input-icon,
        .na-select:focus ~ .na-input-icon { color: var(--terracotta); }

        .na-select { cursor: pointer; }

        .na-select option { background: var(--warm-white); color: var(--charcoal); }

        /* Select arrow */
        .na-select-wrap::after {
          content: '';
          position: absolute;
          right: 0.9rem; top: 50%;
          transform: translateY(-50%);
          width: 0; height: 0;
          border-left: 4px solid transparent;
          border-right: 4px solid transparent;
          border-top: 5px solid var(--border-warm);
          pointer-events: none;
        }

        /* ── PIPELINE INFO ── */
        .na-pipeline {
          background: var(--warm-white);
          border: 1.5px solid var(--border);
          border-radius: 20px;
          overflow: hidden;
          margin-bottom: 2rem;
        }

        .na-pipeline-head {
          padding: 1.25rem 1.75rem;
          border-bottom: 1.5px solid var(--border);
          background: linear-gradient(to right, var(--parchment), var(--warm-white));
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .na-pipeline-title {
          font-family: 'Playfair Display', serif;
          font-size: 1rem;
          font-weight: 600;
          color: var(--charcoal);
        }

        .na-pipeline-sub {
          font-size: 0.75rem;
          color: var(--muted);
          font-weight: 300;
          margin-left: 0.25rem;
        }

        .na-pipeline-body {
          padding: 1.5rem 1.75rem;
          display: grid;
          grid-template-columns: repeat(5, 1fr);
          gap: 0;
          position: relative;
        }

        @media (max-width: 640px) { .na-pipeline-body { grid-template-columns: 1fr; gap: 0.75rem; } }

        /* connecting line */
        .na-pipeline-body::before {
          content: '';
          position: absolute;
          top: 2.25rem;
          left: calc(10% + 16px);
          right: calc(10% + 16px);
          height: 1px;
          background: linear-gradient(to right, var(--border), var(--border-warm), var(--border));
          pointer-events: none;
        }

        @media (max-width: 640px) { .na-pipeline-body::before { display: none; } }

        .na-step {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.6rem;
          text-align: center;
          position: relative;
          z-index: 1;
        }

        .na-step-num {
          width: 36px; height: 36px;
          border-radius: 50%;
          background: var(--parchment);
          border: 1.5px solid var(--border);
          display: flex; align-items: center; justify-content: center;
          font-family: 'DM Mono', monospace;
          font-size: 0.65rem;
          font-weight: 500;
          color: var(--muted);
          letter-spacing: 0.05em;
          transition: all 0.2s;
        }

        .na-step:hover .na-step-num {
          background: rgba(160,82,45,0.09);
          border-color: rgba(160,82,45,0.3);
          color: var(--sienna);
        }

        .na-step-label {
          font-size: 0.72rem;
          color: var(--muted);
          font-weight: 400;
          line-height: 1.3;
          max-width: 80px;
        }

        /* ── ACTIONS ── */
        .na-actions {
          display: flex;
          align-items: center;
          justify-content: flex-end;
          gap: 1rem;
        }

        .na-cancel-btn {
          display: inline-flex;
          align-items: center;
          gap: 0.4rem;
          font-family: 'DM Sans', sans-serif;
          font-size: 0.85rem;
          font-weight: 500;
          color: var(--muted);
          background: var(--warm-white);
          border: 1.5px solid var(--border);
          padding: 0.65rem 1.35rem;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.15s;
          text-decoration: none;
        }

        .na-cancel-btn:hover:not(:disabled) { border-color: var(--border-warm); color: var(--ink); }
        .na-cancel-btn:disabled { opacity: 0.5; cursor: not-allowed; }

        .na-submit-btn {
          display: inline-flex;
          align-items: center;
          gap: 0.55rem;
          font-family: 'DM Sans', sans-serif;
          font-size: 0.85rem;
          font-weight: 500;
          color: var(--warm-white);
          background: linear-gradient(135deg, var(--sienna) 0%, var(--terracotta) 100%);
          border: none;
          padding: 0.65rem 1.6rem;
          border-radius: 8px;
          cursor: pointer;
          box-shadow: 0 4px 14px var(--shadow-warm), inset 0 1px 0 rgba(255,255,255,0.15);
          transition: all 0.2s;
        }

        .na-submit-btn:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 8px 22px rgba(160,82,45,0.3), inset 0 1px 0 rgba(255,255,255,0.15);
        }

        .na-submit-btn:disabled { opacity: 0.65; cursor: not-allowed; transform: none; }

        .na-spinner {
          width: 16px; height: 16px;
          border: 2px solid rgba(255,255,255,0.3);
          border-top-color: #fff;
          border-radius: 50%;
          animation: na-spin 0.7s linear infinite;
        }

        @keyframes na-spin { to { transform: rotate(360deg); } }

        /* ── TEXTAREA ── */
        .na-textarea {
          resize: vertical;
          min-height: 58px;
          padding-top: 0.7rem;
          line-height: 1.5;
        }

        /* ── STEPPER ── */
        .na-stepper {
          display: flex;
          align-items: flex-start;
          justify-content: center;
          gap: 0;
          margin-bottom: 1.4rem;
        }

        .na-stepper-item {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.5rem;
          position: relative;
        }

        .na-stepper-line {
          position: absolute;
          top: 18px;
          right: calc(50% + 22px);
          width: 80px;
          height: 2px;
          background: var(--border);
          transition: background 0.3s;
        }

        .na-stepper-line[data-state="done"],
        .na-stepper-line[data-state="active"] {
          background: var(--sienna);
        }

        .na-stepper-circle {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-family: 'DM Mono', monospace;
          font-size: 0.8rem;
          font-weight: 600;
          border: 2px solid var(--border);
          background: var(--warm-white);
          color: var(--muted);
          cursor: default;
          transition: all 0.3s;
          position: relative;
          z-index: 1;
        }

        .na-stepper-circle[data-state="active"] {
          border-color: var(--sienna);
          background: linear-gradient(135deg, var(--sienna) 0%, var(--terracotta) 100%);
          color: var(--warm-white);
          box-shadow: 0 4px 14px rgba(160,82,45,0.25);
          cursor: default;
        }

        .na-stepper-circle[data-state="done"] {
          border-color: var(--sienna);
          background: var(--warm-white);
          color: var(--sienna);
          cursor: pointer;
        }

        .na-stepper-circle[data-state="done"]:hover {
          background: rgba(160,82,45,0.06);
        }

        .na-stepper-label {
          font-family: 'DM Sans', sans-serif;
          font-size: 0.7rem;
          font-weight: 500;
          color: var(--muted);
          letter-spacing: 0.02em;
          text-align: center;
          width: 110px;
        }

        .na-stepper-item[data-state="active"] .na-stepper-label {
          color: var(--sienna);
          font-weight: 600;
        }

        .na-stepper-item[data-state="done"] .na-stepper-label {
          color: var(--ink);
        }

        /* ── REVIEW GRID ── */
        .na-review-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 0.85rem 1.6rem;
        }

        @media (max-width: 640px) { .na-review-grid { grid-template-columns: 1fr; } }

        .na-review-item {
          display: flex;
          flex-direction: column;
          gap: 0.15rem;
          padding: 0.65rem 0;
          border-bottom: 1px solid var(--border-light);
        }

        .na-review-full {
          grid-column: 1 / -1;
        }

        .na-review-label {
          font-family: 'DM Mono', monospace;
          font-size: 0.62rem;
          font-weight: 500;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: var(--muted);
        }

        .na-review-value {
          font-family: 'DM Sans', sans-serif;
          font-size: 0.88rem;
          font-weight: 500;
          color: var(--ink);
          line-height: 1.4;
          word-break: break-word;
        }

        .na-review-value.na-mono {
          font-family: 'DM Mono', monospace;
          font-size: 0.82rem;
          letter-spacing: 0.04em;
        }

        .na-review-value.na-highlight {
          font-size: 1rem;
          font-weight: 600;
          color: var(--sienna);
        }

        /* ── EDIT LINK ── */
        .na-edit-link {
          margin-left: auto;
          font-family: 'DM Sans', sans-serif;
          font-size: 0.75rem;
          font-weight: 500;
          color: var(--sienna);
          background: none;
          border: 1.5px solid rgba(160,82,45,0.2);
          padding: 0.3rem 0.7rem;
          border-radius: 6px;
          cursor: pointer;
          letter-spacing: 0.02em;
          transition: all 0.15s;
        }

        .na-edit-link:hover {
          background: rgba(160,82,45,0.06);
          border-color: rgba(160,82,45,0.35);
        }
      `}</style>

      <div className="na-wrap">
        <div className="na-inner">

          {/* Top Bar */}
          <div className="na-topbar">
            <div className="na-brand">
              <div className="na-brand-mark">
                <div className="na-brand-ring" />
                <div className="na-brand-ring-2" />
                <div className="na-brand-icon">
                  <Shield size={20} color="#FAF7F2" strokeWidth={1.5} />
                </div>
              </div>
              <div>
                <div className="na-brand-eyebrow">Corporate Intelligence</div>
                <div className="na-brand-name">FraudSentinel</div>
              </div>
            </div>
            <button className="na-back-btn" onClick={() => navigate('/')}>
              <ArrowLeft size={13} /> Back to Dashboard
            </button>
          </div>

          {/* Page Header */}
          <div className="na-page-header">
            <div className="na-eyebrow">New Submission</div>
            <h1 className="na-h1">Credit <em>Application</em></h1>
            <p className="na-sub">Complete the multi-step form to initiate a credit appraisal.</p>
          </div>

          {/* ── STEP INDICATOR ── */}
          <div className="na-stepper">
            {STEPS.map((s, i) => {
              const Icon = s.icon;
              const state = i < step ? 'done' : i === step ? 'active' : 'pending';
              return (
                <div key={s.key} className="na-stepper-item" data-state={state}>
                  {i > 0 && <div className="na-stepper-line" data-state={state} />}
                  <button className="na-stepper-circle" data-state={state} onClick={() => { if (i < step) setStep(i); }}>
                    {state === 'done' ? <CheckCircle2 size={16} /> : <Icon size={16} />}
                  </button>
                  <span className="na-stepper-label">{s.label}</span>
                </div>
              );
            })}
          </div>

          <div className="ornament">
            <div className="ornament-line" />
            <div className="ornament-diamond" />
            <div className="ornament-line" />
          </div>

          {/* Error */}
          {error && (
            <div className="na-error">
              <AlertCircle size={18} color="#A03030" strokeWidth={1.5} style={{ flexShrink: 0, marginTop: 2 }} />
              <div className="na-error-text">
                <h3>Validation Error</h3>
                <p>{error}</p>
              </div>
            </div>
          )}

          {/* ═══════════ STEP 1 — Entity Details ═══════════ */}
          {step === 0 && (
            <div className="na-card">
              <div className="na-card-head">
                <div className="na-card-head-icon"><Building2 size={15} color="var(--sienna)" strokeWidth={1.5} /></div>
                <span className="na-card-head-title">Entity Details</span>
              </div>
              <div className="na-card-body">
                <div className="na-grid">

                  {/* Company Name */}
                  <div className="na-field na-field-full">
                    <label className="na-label">Company Name <span style={{ color: 'var(--terracotta)' }}>*</span></label>
                    <div className="na-input-wrap">
                      <input type="text" name="company_name" value={formData.company_name} onChange={handleInputChange} required placeholder="e.g., SpiceJet Limited" className="na-input" />
                      <Building2 size={14} strokeWidth={1.5} className="na-input-icon" />
                    </div>
                  </div>

                  {/* CIN */}
                  <div className="na-field">
                    <label className="na-label">MCA CIN <span style={{ color: 'var(--terracotta)' }}>*</span></label>
                    <div className="na-input-wrap">
                      <input type="text" name="mca_cin" value={formData.mca_cin} onChange={handleInputChange} required placeholder="L51909DL1984PLC018603" className="na-input" style={{ fontFamily: "'DM Mono', monospace", fontSize: '0.82rem', letterSpacing: '0.04em' }} />
                      <Hash size={14} strokeWidth={1.5} className="na-input-icon" />
                    </div>
                  </div>

                  {/* PAN */}
                  <div className="na-field">
                    <label className="na-label">PAN</label>
                    <div className="na-input-wrap">
                      <input type="text" name="pan" value={formData.pan} onChange={handleInputChange} placeholder="AAACX1234X" className="na-input" style={{ fontFamily: "'DM Mono', monospace", fontSize: '0.82rem', letterSpacing: '0.04em', textTransform: 'uppercase' }} maxLength={10} />
                      <Hash size={14} strokeWidth={1.5} className="na-input-icon" />
                    </div>
                  </div>

                  {/* Sector */}
                  <div className="na-field">
                    <label className="na-label">Sector <span style={{ color: 'var(--terracotta)' }}>*</span></label>
                    <div className="na-input-wrap na-select-wrap">
                      <select name="sector" value={formData.sector} onChange={handleInputChange} required className="na-select">
                        <option value="">Select industry sector…</option>
                        {SECTORS.map(s => <option key={s} value={s}>{s}</option>)}
                      </select>
                      <LayoutGrid size={14} strokeWidth={1.5} className="na-input-icon" />
                    </div>
                  </div>

                  {/* Incorporation Date */}
                  <div className="na-field">
                    <label className="na-label">Incorporation Date</label>
                    <div className="na-input-wrap">
                      <input type="date" name="incorporation_date" value={formData.incorporation_date} onChange={handleInputChange} className="na-input" />
                      <Calendar size={14} strokeWidth={1.5} className="na-input-icon" />
                    </div>
                  </div>

                  {/* Turnover */}
                  <div className="na-field">
                    <label className="na-label">Annual Turnover (Cr)</label>
                    <div className="na-input-wrap">
                      <input type="number" step="0.01" name="annual_turnover_cr" value={formData.annual_turnover_cr} onChange={handleInputChange} placeholder="e.g., 1200" className="na-input" />
                      <IndianRupee size={14} strokeWidth={1.5} className="na-input-icon" />
                    </div>
                  </div>

                  {/* Employees */}
                  <div className="na-field">
                    <label className="na-label">Employee Count</label>
                    <div className="na-input-wrap">
                      <input type="number" name="employee_count" value={formData.employee_count} onChange={handleInputChange} placeholder="e.g., 500" className="na-input" />
                      <Users size={14} strokeWidth={1.5} className="na-input-icon" />
                    </div>
                  </div>

                  {/* Promoter Names */}
                  <div className="na-field">
                    <label className="na-label">Promoter Names</label>
                    <div className="na-input-wrap">
                      <input type="text" name="promoter_names" value={formData.promoter_names} onChange={handleInputChange} placeholder="Ajay Singh, Shilpa Singh" className="na-input" />
                      <Users size={14} strokeWidth={1.5} className="na-input-icon" />
                    </div>
                  </div>

                  {/* Registered Address */}
                  <div className="na-field na-field-full">
                    <label className="na-label">Registered Address</label>
                    <div className="na-input-wrap">
                      <textarea name="registered_address" value={formData.registered_address} onChange={handleInputChange} placeholder="Registered office address" className="na-input na-textarea" rows={2} />
                      <MapPin size={14} strokeWidth={1.5} className="na-input-icon" style={{ top: '1rem' }} />
                    </div>
                  </div>

                </div>
              </div>
            </div>
          )}

          {/* ═══════════ STEP 2 — Loan Details ═══════════ */}
          {step === 1 && (
            <div className="na-card">
              <div className="na-card-head">
                <div className="na-card-head-icon"><IndianRupee size={15} color="var(--sienna)" strokeWidth={1.5} /></div>
                <span className="na-card-head-title">Loan Details</span>
              </div>
              <div className="na-card-body">
                <div className="na-grid">

                  {/* Requested Limit */}
                  <div className="na-field">
                    <label className="na-label">Requested Limit (Cr) <span style={{ color: 'var(--terracotta)' }}>*</span></label>
                    <div className="na-input-wrap">
                      <input type="number" step="0.01" name="requested_limit_cr" value={formData.requested_limit_cr} onChange={handleInputChange} required placeholder="e.g., 500" className="na-input" />
                      <IndianRupee size={14} strokeWidth={1.5} className="na-input-icon" />
                    </div>
                  </div>

                  {/* Loan Type */}
                  <div className="na-field">
                    <label className="na-label">Loan Type <span style={{ color: 'var(--terracotta)' }}>*</span></label>
                    <div className="na-input-wrap na-select-wrap">
                      <select name="loan_type" value={formData.loan_type} onChange={handleInputChange} required className="na-select">
                        <option value="">Select loan type…</option>
                        {LOAN_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                      </select>
                      <Briefcase size={14} strokeWidth={1.5} className="na-input-icon" />
                    </div>
                  </div>

                  {/* Tenure */}
                  <div className="na-field">
                    <label className="na-label">Tenure (Months)</label>
                    <div className="na-input-wrap">
                      <input type="number" name="loan_tenure_months" value={formData.loan_tenure_months} onChange={handleInputChange} placeholder="e.g., 60" className="na-input" />
                      <Clock size={14} strokeWidth={1.5} className="na-input-icon" />
                    </div>
                  </div>

                  {/* Interest Type */}
                  <div className="na-field">
                    <label className="na-label">Interest Type</label>
                    <div className="na-input-wrap na-select-wrap">
                      <select name="interest_type" value={formData.interest_type} onChange={handleInputChange} className="na-select">
                        <option value="">Select…</option>
                        <option value="Fixed">Fixed</option>
                        <option value="Floating">Floating</option>
                      </select>
                      <Percent size={14} strokeWidth={1.5} className="na-input-icon" />
                    </div>
                  </div>

                  {/* Purpose */}
                  <div className="na-field na-field-full">
                    <label className="na-label">Purpose of Loan</label>
                    <div className="na-input-wrap">
                      <textarea name="purpose_of_loan" value={formData.purpose_of_loan} onChange={handleInputChange} placeholder="Working capital for raw material procurement…" className="na-input na-textarea" rows={2} />
                      <Target size={14} strokeWidth={1.5} className="na-input-icon" style={{ top: '1rem' }} />
                    </div>
                  </div>

                  {/* Collateral */}
                  <div className="na-field na-field-full">
                    <label className="na-label">Collateral Offered</label>
                    <div className="na-input-wrap">
                      <textarea name="collateral_offered" value={formData.collateral_offered} onChange={handleInputChange} placeholder="Land & building at sector-12, Noida valued at Rs. 250 Cr…" className="na-input na-textarea" rows={2} />
                      <Landmark size={14} strokeWidth={1.5} className="na-input-icon" style={{ top: '1rem' }} />
                    </div>
                  </div>

                  {/* Existing Banking */}
                  <div className="na-field na-field-full">
                    <label className="na-label">Existing Banking Relationships</label>
                    <div className="na-input-wrap">
                      <input type="text" name="existing_banking" value={formData.existing_banking} onChange={handleInputChange} placeholder="SBI, HDFC Bank, ICICI Bank" className="na-input" />
                      <Landmark size={14} strokeWidth={1.5} className="na-input-icon" />
                    </div>
                  </div>

                </div>
              </div>
            </div>
          )}

          {/* ═══════════ STEP 3 — Review & Submit ═══════════ */}
          {step === 2 && (
            <>
              <div className="na-card">
                <div className="na-card-head">
                  <div className="na-card-head-icon"><FileText size={15} color="var(--sienna)" strokeWidth={1.5} /></div>
                  <span className="na-card-head-title">Review — Entity Details</span>
                  <button className="na-edit-link" onClick={() => setStep(0)}>Edit</button>
                </div>
                <div className="na-card-body">
                  <div className="na-review-grid">
                    <ReviewItem label="Company Name" value={formData.company_name} />
                    <ReviewItem label="MCA CIN" value={formData.mca_cin} mono />
                    <ReviewItem label="PAN" value={formData.pan} mono />
                    <ReviewItem label="Sector" value={formData.sector} />
                    <ReviewItem label="Incorporation Date" value={formData.incorporation_date || '—'} />
                    <ReviewItem label="Annual Turnover" value={formData.annual_turnover_cr ? `₹${formData.annual_turnover_cr} Cr` : '—'} />
                    <ReviewItem label="Employee Count" value={formData.employee_count || '—'} />
                    <ReviewItem label="Promoter Names" value={formData.promoter_names || '—'} />
                    <ReviewItem label="Registered Address" value={formData.registered_address || '—'} full />
                  </div>
                </div>
              </div>

              <div className="na-card">
                <div className="na-card-head">
                  <div className="na-card-head-icon"><IndianRupee size={15} color="var(--sienna)" strokeWidth={1.5} /></div>
                  <span className="na-card-head-title">Review — Loan Details</span>
                  <button className="na-edit-link" onClick={() => setStep(1)}>Edit</button>
                </div>
                <div className="na-card-body">
                  <div className="na-review-grid">
                    <ReviewItem label="Requested Limit" value={`₹${formData.requested_limit_cr} Cr`} highlight />
                    <ReviewItem label="Loan Type" value={formData.loan_type} />
                    <ReviewItem label="Tenure" value={formData.loan_tenure_months ? `${formData.loan_tenure_months} months` : '—'} />
                    <ReviewItem label="Interest Type" value={formData.interest_type || '—'} />
                    <ReviewItem label="Purpose" value={formData.purpose_of_loan || '—'} full />
                    <ReviewItem label="Collateral" value={formData.collateral_offered || '—'} full />
                    <ReviewItem label="Existing Banking" value={formData.existing_banking || '—'} full />
                  </div>
                </div>
              </div>

              {/* Pipeline Info */}
              <div className="na-pipeline">
                <div className="na-pipeline-head">
                  <div className="na-card-head-icon"><CheckCircle2 size={15} color="var(--sienna)" strokeWidth={1.5} /></div>
                  <span className="na-pipeline-title">What happens next?</span>
                  <span className="na-pipeline-sub">— 5 automated stages</span>
                </div>
                <div className="na-pipeline-body">
                  {[
                    { n: '01', label: 'Upload Documents' },
                    { n: '02', label: 'External Intelligence' },
                    { n: '03', label: 'Primary Insights' },
                    { n: '04', label: 'Credit Scoring' },
                    { n: '05', label: 'Generate CAM' },
                  ].map((s) => (
                    <div className="na-step" key={s.n}>
                      <div className="na-step-num">{s.n}</div>
                      <span className="na-step-label">{s.label}</span>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* ── Actions ── */}
          <div className="na-actions">
            {step === 0 ? (
              <button type="button" className="na-cancel-btn" onClick={() => navigate('/')} disabled={loading}>
                <ArrowLeft size={13} /> Cancel
              </button>
            ) : (
              <button type="button" className="na-cancel-btn" onClick={prevStep} disabled={loading}>
                <ArrowLeft size={13} /> Previous
              </button>
            )}

            {step < 2 ? (
              <button type="button" className="na-submit-btn" onClick={nextStep}>
                <span>Next Step</span><ArrowRight size={14} />
              </button>
            ) : (
              <button type="button" className="na-submit-btn" onClick={handleSubmit} disabled={loading}>
                {loading ? (
                  <><div className="na-spinner" /><span>Creating…</span></>
                ) : (
                  <><span>Create Application</span><ArrowRight size={14} /></>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

/* ── Review helper ── */
const ReviewItem = ({ label, value, mono, highlight, full }) => (
  <div className={`na-review-item${full ? ' na-review-full' : ''}`}>
    <span className="na-review-label">{label}</span>
    <span className={`na-review-value${mono ? ' na-mono' : ''}${highlight ? ' na-highlight' : ''}`}>{value || '—'}</span>
  </div>
);

export default NewApplication;