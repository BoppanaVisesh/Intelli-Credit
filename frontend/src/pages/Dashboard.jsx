import { AlertCircle, ArrowUpRight, CheckCircle, FileText, Flame, Plus, Shield } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../utils/api';
import { DECISION_LABELS } from '../utils/constants';
import { formatCurrency, formatDate } from '../utils/formatters';

const Dashboard = () => {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ total: 0, pending: 0, approved: 0, rejected: 0 });

  useEffect(() => { loadApplications(); }, []);

  const loadApplications = async () => {
    try {
      setLoading(true);
      const data = await api.getApplications();
      setApplications(data.applications);
      setStats({
        total: data.total,
        pending: data.applications.filter(a => a.status === 'PENDING' || a.status === 'PROCESSING').length,
        approved: data.applications.filter(a => a.decision === 'APPROVE').length,
        rejected: data.applications.filter(a => a.decision === 'REJECT').length,
      });
    } catch (error) {
      console.error('Failed to load applications:', error);
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
          --sienna-light: #C4693F;
          --terracotta: #CB6E45;
          --gold: #B8860B;
          --gold-light: #D4A017;
          --charcoal: #2C2416;
          --ink: #3D3020;
          --muted: #7A6850;
          --border: #DDD4C0;
          --border-warm: #C9BCA8;
          --shadow-warm: rgba(160, 82, 45, 0.12);
        }

        .dash-wrap {
          min-height: 100vh;
          background: var(--cream);
          font-family: 'DM Sans', sans-serif;
          position: relative;
          overflow: hidden;
        }

        .dash-wrap::after {
          content: '';
          position: fixed;
          top: -200px;
          right: -100px;
          width: 500px;
          height: 900px;
          background: linear-gradient(160deg, rgba(203,110,69,0.07) 0%, rgba(184,134,11,0.04) 50%, transparent 80%);
          transform: rotate(-15deg);
          pointer-events: none;
          z-index: 0;
        }

        .dash-inner {
          position: relative;
          z-index: 1;
          max-width: 1320px;
          margin: 0 auto;
          padding: 0 2.5rem 3rem;
        }

        .dash-topbar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 2rem 0 2.5rem;
          border-bottom: 1.5px solid var(--border);
          margin-bottom: 2.5rem;
        }

        .dash-brand {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .dash-brand-mark {
          position: relative;
          width: 48px;
          height: 48px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .dash-brand-ring {
          position: absolute;
          inset: -4px;
          border-radius: 50%;
          border: 1.5px solid var(--terracotta);
          opacity: 0.4;
          animation: ring-spin 12s linear infinite;
        }

        .dash-brand-ring-2 {
          position: absolute;
          inset: -9px;
          border-radius: 50%;
          border: 1px dashed var(--gold);
          opacity: 0.25;
          animation: ring-spin 20s linear infinite reverse;
        }

        @keyframes ring-spin { to { transform: rotate(360deg); } }

        .dash-brand-icon {
          width: 48px;
          height: 48px;
          background: linear-gradient(135deg, var(--sienna) 0%, var(--terracotta) 100%);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          box-shadow: 0 4px 16px rgba(160,82,45,0.35);
        }

        .dash-brand-eyebrow {
          font-family: 'DM Mono', monospace;
          font-size: 0.6rem;
          letter-spacing: 0.2em;
          text-transform: uppercase;
          color: var(--terracotta);
          line-height: 1;
          margin-bottom: 0.2rem;
        }

        .dash-brand-name {
          font-family: 'Playfair Display', serif;
          font-size: 1.6rem;
          font-weight: 700;
          color: var(--charcoal);
          line-height: 1;
          letter-spacing: -0.01em;
        }

        .dash-topbar-right {
          display: flex;
          align-items: center;
          gap: 1.5rem;
        }

        .dash-date-chip {
          font-family: 'DM Mono', monospace;
          font-size: 0.7rem;
          color: var(--muted);
          background: var(--parchment);
          border: 1px solid var(--border);
          padding: 0.4rem 0.9rem;
          border-radius: 20px;
          letter-spacing: 0.05em;
        }

        .dash-cta {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          font-family: 'DM Sans', sans-serif;
          font-size: 0.85rem;
          font-weight: 500;
          color: var(--warm-white);
          background: linear-gradient(135deg, var(--sienna) 0%, var(--terracotta) 100%);
          padding: 0.65rem 1.35rem;
          border-radius: 8px;
          text-decoration: none;
          box-shadow: 0 4px 14px var(--shadow-warm), inset 0 1px 0 rgba(255,255,255,0.15);
          transition: all 0.2s ease;
        }

        .dash-cta:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 22px rgba(160,82,45,0.3), inset 0 1px 0 rgba(255,255,255,0.15);
        }

        .dash-headline-row {
          display: flex;
          align-items: flex-end;
          justify-content: space-between;
          margin-bottom: 2rem;
        }

        .dash-h1 {
          font-family: 'Playfair Display', serif;
          font-size: 3.2rem;
          font-weight: 700;
          color: var(--charcoal);
          line-height: 1;
          letter-spacing: -0.02em;
        }

        .dash-h1 em {
          font-style: italic;
          color: var(--terracotta);
        }

        .dash-subtitle {
          font-size: 0.85rem;
          color: var(--muted);
          font-weight: 300;
          max-width: 260px;
          text-align: right;
          line-height: 1.6;
        }

        .dash-stats {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 1.25rem;
          margin-bottom: 2.5rem;
        }

        @media (max-width: 1024px) { .dash-stats { grid-template-columns: repeat(2,1fr); } }
        @media (max-width: 640px)  { .dash-stats { grid-template-columns: 1fr; } }

        .scard {
          background: var(--warm-white);
          border: 1.5px solid var(--border);
          border-radius: 16px;
          padding: 1.5rem 1.6rem;
          position: relative;
          overflow: hidden;
          transition: transform 0.2s, box-shadow 0.2s;
        }

        .scard:hover {
          transform: translateY(-3px);
          box-shadow: 0 12px 32px rgba(0,0,0,0.08), 0 4px 8px var(--shadow-warm);
        }

        .scard-accent-bar {
          position: absolute;
          top: 0; left: 0; right: 0;
          height: 3px;
          border-radius: 16px 16px 0 0;
        }

        .scard-corner {
          position: absolute;
          bottom: -18px;
          right: -18px;
          width: 80px;
          height: 80px;
          border-radius: 50%;
          opacity: 0.06;
        }

        .scard-top {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          margin-bottom: 1.2rem;
        }

        .scard-label {
          font-family: 'DM Mono', monospace;
          font-size: 0.62rem;
          font-weight: 500;
          letter-spacing: 0.14em;
          text-transform: uppercase;
          color: var(--muted);
        }

        .scard-icon {
          width: 34px;
          height: 34px;
          border-radius: 9px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .scard-value {
          font-family: 'DM Mono', monospace;
          font-size: 3rem;
          font-weight: 500;
          line-height: 1;
          letter-spacing: -0.04em;
          color: var(--charcoal);
        }

        .scard-footer {
          margin-top: 1rem;
          display: flex;
          align-items: center;
          gap: 0.4rem;
          font-size: 0.72rem;
          color: var(--muted);
          font-weight: 300;
        }

        .scard-divider {
          width: 24px;
          height: 1px;
          background: var(--border-warm);
          flex-shrink: 0;
        }

        .ornament {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          margin-bottom: 2.5rem;
        }

        .ornament-line {
          height: 1px;
          flex: 1;
          background: linear-gradient(to right, transparent, var(--border-warm), transparent);
        }

        .ornament-diamond {
          width: 6px;
          height: 6px;
          background: var(--terracotta);
          transform: rotate(45deg);
          opacity: 0.5;
        }

        .tpanel {
          background: var(--warm-white);
          border: 1.5px solid var(--border);
          border-radius: 20px;
          overflow: hidden;
          box-shadow: 0 2px 16px rgba(0,0,0,0.04);
        }

        .tpanel-head {
          padding: 1.5rem 2rem;
          border-bottom: 1.5px solid var(--border);
          display: flex;
          align-items: center;
          justify-content: space-between;
          background: linear-gradient(to right, var(--parchment), var(--warm-white));
        }

        .tpanel-title-group {
          display: flex;
          align-items: baseline;
          gap: 1rem;
        }

        .tpanel-title {
          font-family: 'Playfair Display', serif;
          font-size: 1.3rem;
          font-weight: 600;
          color: var(--charcoal);
        }

        .tpanel-title-it {
          font-style: italic;
          color: var(--terracotta);
        }

        .tpanel-count {
          font-family: 'DM Mono', monospace;
          font-size: 0.65rem;
          color: var(--muted);
          background: var(--parchment);
          border: 1px solid var(--border);
          padding: 0.25rem 0.75rem;
          border-radius: 20px;
        }

        .tpanel-live {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-family: 'DM Mono', monospace;
          font-size: 0.62rem;
          color: var(--terracotta);
          letter-spacing: 0.1em;
          text-transform: uppercase;
        }

        .tpanel-live-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: var(--terracotta);
          animation: live-pulse 1.8s ease infinite;
        }

        @keyframes live-pulse {
          0%,100% { transform: scale(1); opacity: 1; }
          50% { transform: scale(1.6); opacity: 0.5; }
        }

        .t { width: 100%; border-collapse: collapse; }

        .t thead tr { background: var(--parchment); }

        .t thead th {
          font-family: 'DM Mono', monospace;
          font-size: 0.6rem;
          font-weight: 500;
          letter-spacing: 0.14em;
          text-transform: uppercase;
          color: var(--muted);
          padding: 0.9rem 1.25rem;
          text-align: left;
          border-bottom: 1.5px solid var(--border);
          white-space: nowrap;
        }

        .t tbody tr { border-bottom: 1px solid rgba(221,212,192,0.5); transition: background 0.15s; }
        .t tbody tr:last-child { border-bottom: none; }
        .t tbody tr:hover { background: rgba(203,110,69,0.03); }

        .t tbody td {
          padding: 1rem 1.25rem;
          font-size: 0.875rem;
          color: var(--ink);
        }

        .t-id {
          font-family: 'DM Mono', monospace;
          font-size: 0.72rem;
          color: var(--sienna);
          background: rgba(160,82,45,0.07);
          padding: 0.22rem 0.6rem;
          border-radius: 4px;
          border: 1px solid rgba(160,82,45,0.15);
          white-space: nowrap;
          display: inline-block;
        }

        .t-company { font-weight: 500; color: var(--charcoal); }

        .t-sector {
          font-family: 'DM Mono', monospace;
          font-size: 0.68rem;
          color: var(--muted);
          background: var(--parchment);
          padding: 0.2rem 0.55rem;
          border-radius: 4px;
          border: 1px solid var(--border);
          display: inline-block;
        }

        .t-amount {
          font-family: 'DM Mono', monospace;
          font-size: 0.8rem;
          color: var(--charcoal);
          font-weight: 500;
        }

        .t-score-high { color: #5C7A3E; font-family: 'DM Mono', monospace; font-weight: 500; font-size: 0.82rem; }
        .t-score-mid  { color: #9A6F2A; font-family: 'DM Mono', monospace; font-weight: 500; font-size: 0.82rem; }
        .t-score-low  { color: #A03030; font-family: 'DM Mono', monospace; font-weight: 500; font-size: 0.82rem; }
        .t-score-none { color: var(--border-warm); font-family: 'DM Mono', monospace; font-size: 0.82rem; }

        .tbadge {
          display: inline-flex;
          align-items: center;
          gap: 0.35rem;
          font-family: 'DM Mono', monospace;
          font-size: 0.62rem;
          font-weight: 500;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          padding: 0.28rem 0.65rem;
          border-radius: 4px;
          white-space: nowrap;
        }

        .tbadge::before {
          content: '';
          width: 5px; height: 5px;
          border-radius: 50%;
          background: currentColor;
          flex-shrink: 0;
        }

        .tbadge-approve { color: #4D7C3A; background: rgba(77,124,58,0.1); border: 1px solid rgba(77,124,58,0.2); }
        .tbadge-reject  { color: #A03030; background: rgba(160,48,48,0.1); border: 1px solid rgba(160,48,48,0.2); }
        .tbadge-pending { color: #9A6F2A; background: rgba(154,111,42,0.1); border: 1px solid rgba(154,111,42,0.2); }
        .tbadge-default { color: var(--muted); background: var(--parchment); border: 1px solid var(--border); }

        .t-date {
          font-family: 'DM Mono', monospace;
          font-size: 0.7rem;
          color: var(--muted);
        }

        .t-action {
          display: inline-flex;
          align-items: center;
          gap: 0.3rem;
          font-size: 0.78rem;
          font-weight: 500;
          color: var(--sienna);
          text-decoration: none;
          padding: 0.3rem 0.8rem;
          border-radius: 6px;
          background: rgba(160,82,45,0.07);
          border: 1px solid rgba(160,82,45,0.18);
          transition: all 0.15s;
        }

        .t-action:hover {
          background: rgba(160,82,45,0.14);
          border-color: rgba(160,82,45,0.35);
        }

        .t-loading {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 5rem 2rem;
          gap: 1rem;
        }

        .t-spinner {
          width: 36px; height: 36px;
          border: 2px solid var(--border);
          border-top-color: var(--terracotta);
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

        .t-loading-text {
          font-family: 'DM Mono', monospace;
          font-size: 0.7rem;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          color: var(--muted);
        }

        .t-empty {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 5rem 2rem;
          gap: 1rem;
          text-align: center;
        }

        .t-empty-icon {
          width: 64px; height: 64px;
          background: var(--parchment);
          border: 1.5px solid var(--border);
          border-radius: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .t-empty-title {
          font-family: 'Playfair Display', serif;
          font-size: 1.2rem;
          font-weight: 600;
          color: var(--charcoal);
        }

        .t-empty-sub {
          font-size: 0.85rem;
          color: var(--muted);
          max-width: 300px;
          line-height: 1.6;
          font-weight: 300;
        }
      `}</style>

      <div className="dash-wrap">
        <div className="dash-inner">

          {/* Top Bar */}
          <div className="dash-topbar">
            <div className="dash-brand">
              <div className="dash-brand-mark">
                <div className="dash-brand-ring" />
                <div className="dash-brand-ring-2" />
                <div className="dash-brand-icon">
                  <Shield size={20} color="#FAF7F2" strokeWidth={1.5} />
                </div>
              </div>
              <div>
                <div className="dash-brand-eyebrow">Corporate Intelligence</div>
                <div className="dash-brand-name">FinIntel</div>
              </div>
            </div>
            <div className="dash-topbar-right">
              <span className="dash-date-chip">
                {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
              </span>
              <Link to="/new-application" className="dash-cta">
                <Plus size={14} strokeWidth={2.5} />
                New Application
              </Link>
            </div>
          </div>

          {/* Headline */}
          <div className="dash-headline-row">
            <h1 className="dash-h1">Risk Overview</h1>
            <p className="dash-subtitle">Real-time monitoring of credit applications and fraud detection signals.</p>
          </div>

          {/* Ornamental divider */}
          <div className="ornament">
            <div className="ornament-line" />
            <div className="ornament-diamond" />
            <div className="ornament-line" />
          </div>

          {/* Stat Cards */}
          <div className="dash-stats">
            {[
              { label: 'Total Applications', value: stats.total,    icon: FileText,    color: '#A0522D', bg: 'rgba(160,82,45,0.09)',  bar: 'linear-gradient(90deg,#A0522D,#C4693F)', footer: 'All submissions'   },
              { label: 'Under Review',       value: stats.pending,  icon: AlertCircle, color: '#9A6F2A', bg: 'rgba(154,111,42,0.09)', bar: 'linear-gradient(90deg,#9A6F2A,#D4A017)', footer: 'Awaiting decision' },
              { label: 'Approved',           value: stats.approved, icon: CheckCircle, color: '#4D7C3A', bg: 'rgba(77,124,58,0.09)',  bar: 'linear-gradient(90deg,#4D7C3A,#6BA051)', footer: 'Cleared for credit' },
              { label: 'Rejected',           value: stats.rejected, icon: Flame,       color: '#A03030', bg: 'rgba(160,48,48,0.09)',  bar: 'linear-gradient(90deg,#A03030,#C44444)', footer: 'Risk flagged'      },
            ].map((c, i) => {
              const Icon = c.icon;
              return (
                <div className="scard" key={i}>
                  <div className="scard-accent-bar" style={{ background: c.bar }} />
                  <div className="scard-corner" style={{ background: c.color }} />
                  <div className="scard-top">
                    <span className="scard-label">{c.label}</span>
                    <div className="scard-icon" style={{ background: c.bg }}>
                      <Icon size={16} color={c.color} strokeWidth={1.5} />
                    </div>
                  </div>
                  <div className="scard-value">{c.value}</div>
                  <div className="scard-footer">
                    <div className="scard-divider" />
                    {c.footer}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Table Panel */}
          <div className="tpanel">
            <div className="tpanel-head">
              <div className="tpanel-title-group">
                <span className="tpanel-title">Recent Applications</span>
                <span className="tpanel-count">{applications.length} records</span>
              </div>
              <div className="tpanel-live">
                <span className="tpanel-live-dot" />
                Live feed
              </div>
            </div>

            {loading ? (
              <div className="t-loading">
                <div className="t-spinner" />
                <span className="t-loading-text">Loading records…</span>
              </div>
            ) : applications.length === 0 ? (
              <div className="t-empty">
                <div className="t-empty-icon">
                  <FileText size={26} color="var(--terracotta)" strokeWidth={1.5} />
                </div>
                <div className="t-empty-title">No applications yet</div>
                <p className="t-empty-sub">Submit your first application to begin the fraud detection review process.</p>
                <Link to="/new-application" className="dash-cta" style={{ marginTop: '0.5rem' }}>
                  <Plus size={14} /> Create Application
                </Link>
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table className="t">
                  <thead>
                    <tr>
                      <th>App ID</th>
                      <th>Company</th>
                      <th>Sector</th>
                      <th>Requested</th>
                      <th>Score</th>
                      <th>Decision</th>
                      <th>Date</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {applications.map((app) => {
                      const score = app.final_score;
                      const scoreClass = !score ? 't-score-none' : score >= 75 ? 't-score-high' : score >= 50 ? 't-score-mid' : 't-score-low';
                      let badgeClass = 'tbadge tbadge-default', badgeLabel = 'Pending';
                      if (app.decision === 'APPROVE')      { badgeClass = 'tbadge tbadge-approve'; badgeLabel = DECISION_LABELS[app.decision]; }
                      else if (app.decision === 'REJECT')  { badgeClass = 'tbadge tbadge-reject';  badgeLabel = DECISION_LABELS[app.decision]; }
                      else if (app.decision)               { badgeClass = 'tbadge tbadge-pending'; badgeLabel = DECISION_LABELS[app.decision]; }
                      return (
                        <tr key={app.application_id}>
                          <td><span className="t-id">{app.application_id}</span></td>
                          <td><span className="t-company">{app.company_name}</span></td>
                          <td><span className="t-sector">{app.sector}</span></td>
                          <td><span className="t-amount">{formatCurrency(app.requested_limit_cr)}</span></td>
                          <td><span className={scoreClass}>{score ? `${score}/100` : '—'}</span></td>
                          <td><span className={badgeClass}>{badgeLabel}</span></td>
                          <td><span className="t-date">{formatDate(app.created_at)}</span></td>
                          <td>
                            <Link to={`/application/${app.application_id}`} className="t-action">
                              View <ArrowUpRight size={11} />
                            </Link>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>

        </div>
      </div>
    </>
  );
};

export default Dashboard;