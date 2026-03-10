import { AlertCircle, ArrowLeft, ArrowRight, Building2, Hash, LayoutGrid, IndianRupee, Shield, CheckCircle2 } from 'lucide-react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../utils/api';

const NewApplication = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [formData, setFormData] = useState({
    company_name: '',
    mca_cin: '',
    sector: '',
    requested_limit_cr: '',
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const result = await api.createApplication({
        company_name: formData.company_name,
        mca_cin: formData.mca_cin,
        sector: formData.sector,
        requested_limit_cr: parseFloat(formData.requested_limit_cr),
      });
      navigate(`/application/${result.application_id}`);
    } catch (err) {
      setError(err.message || 'Failed to create application');
    } finally {
      setLoading(false);
    }
  };

  const pipelineSteps = [
    { n: '01', label: 'Upload Documents' },
    { n: '02', label: 'External Intelligence' },
    { n: '03', label: 'Primary Insights' },
    { n: '04', label: 'Credit Scoring' },
    { n: '05', label: 'Generate CAM' },
  ];

  const fields = [
    { name: 'company_name', label: 'Company Name', type: 'text', placeholder: 'e.g., SpiceJet Limited', icon: Building2, col: 'full' },
    { name: 'mca_cin',      label: 'MCA CIN',      type: 'text', placeholder: 'e.g., L51909DL1984PLC018603', icon: Hash,      col: 'half' },
    { name: 'requested_limit_cr', label: 'Requested Limit (Cr)', type: 'number', placeholder: 'e.g., 500', icon: IndianRupee, col: 'half' },
  ];

  const sectors = ['Aviation','IT Services','Industrial Manufacturing','Textiles','Pharmaceuticals','Real Estate','Banking','FMCG','Auto Components','Food Processing'];

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
            <p className="na-sub">Enter company details to initiate the fraud detection & credit appraisal pipeline.</p>
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
                <h3>Submission Error</h3>
                <p>{error}</p>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit}>
            {/* Company Details Card */}
            <div className="na-card">
              <div className="na-card-head">
                <div className="na-card-head-icon">
                  <Building2 size={15} color="var(--sienna)" strokeWidth={1.5} />
                </div>
                <span className="na-card-head-title">Company Details</span>
              </div>
              <div className="na-card-body">
                <div className="na-grid">

                  {/* Company Name — full width */}
                  <div className="na-field na-field-full">
                    <label className="na-label">Company Name <span style={{ color: 'var(--terracotta)' }}>*</span></label>
                    <div className="na-input-wrap">
                      <input
                        type="text" name="company_name"
                        value={formData.company_name}
                        onChange={handleInputChange}
                        required
                        placeholder="e.g., SpiceJet Limited"
                        className="na-input"
                      />
                      <Building2 size={14} strokeWidth={1.5} className="na-input-icon" />
                    </div>
                  </div>

                  {/* MCA CIN */}
                  <div className="na-field">
                    <label className="na-label">MCA CIN <span style={{ color: 'var(--terracotta)' }}>*</span></label>
                    <div className="na-input-wrap">
                      <input
                        type="text" name="mca_cin"
                        value={formData.mca_cin}
                        onChange={handleInputChange}
                        required
                        placeholder="e.g., L51909DL1984PLC018603"
                        className="na-input"
                        style={{ fontFamily: "'DM Mono', monospace", fontSize: '0.82rem', letterSpacing: '0.04em' }}
                      />
                      <Hash size={14} strokeWidth={1.5} className="na-input-icon" />
                    </div>
                  </div>

                  {/* Requested Limit */}
                  <div className="na-field">
                    <label className="na-label">Requested Limit (Cr) <span style={{ color: 'var(--terracotta)' }}>*</span></label>
                    <div className="na-input-wrap">
                      <input
                        type="number" step="0.01" name="requested_limit_cr"
                        value={formData.requested_limit_cr}
                        onChange={handleInputChange}
                        required
                        placeholder="e.g., 500"
                        className="na-input"
                      />
                      <IndianRupee size={14} strokeWidth={1.5} className="na-input-icon" />
                    </div>
                  </div>

                  {/* Sector — full width */}
                  <div className="na-field na-field-full">
                    <label className="na-label">Sector <span style={{ color: 'var(--terracotta)' }}>*</span></label>
                    <div className="na-input-wrap na-select-wrap">
                      <select
                        name="sector"
                        value={formData.sector}
                        onChange={handleInputChange}
                        required
                        className="na-select"
                      >
                        <option value="">Select industry sector…</option>
                        {['Aviation','IT Services','Industrial Manufacturing','Textiles','Pharmaceuticals','Real Estate','Banking','FMCG','Auto Components','Food Processing'].map(s => (
                          <option key={s} value={s}>{s}</option>
                        ))}
                      </select>
                      <LayoutGrid size={14} strokeWidth={1.5} className="na-input-icon" />
                    </div>
                  </div>

                </div>
              </div>
            </div>

            {/* Pipeline Info */}
            <div className="na-pipeline">
              <div className="na-pipeline-head">
                <div className="na-card-head-icon">
                  <CheckCircle2 size={15} color="var(--sienna)" strokeWidth={1.5} />
                </div>
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
                ].map((step) => (
                  <div className="na-step" key={step.n}>
                    <div className="na-step-num">{step.n}</div>
                    <span className="na-step-label">{step.label}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Actions */}
            <div className="na-actions">
              <button type="button" className="na-cancel-btn" onClick={() => navigate('/')} disabled={loading}>
                <ArrowLeft size={13} /> Cancel
              </button>
              <button type="submit" className="na-submit-btn" disabled={loading}>
                {loading ? (
                  <><div className="na-spinner" /><span>Creating…</span></>
                ) : (
                  <><span>Create Application</span><ArrowRight size={14} /></>
                )}
              </button>
            </div>
          </form>

        </div>
      </div>
    </>
  );
};

export default NewApplication;