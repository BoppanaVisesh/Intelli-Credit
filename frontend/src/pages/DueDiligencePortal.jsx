import {
    AlertTriangle,
    ArrowLeft,
    ChevronDown, ChevronUp,
    ClipboardList,
    Eye,
    Factory,
    FileText,
    MessageSquare,
    Minus,
    Shield,
    Sparkles,
    Trash2,
    TrendingDown,
    TrendingUp
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../utils/api';

const SEVERITY_STYLES = {
  HIGH:   { color: '#A03030', bg: 'rgba(160,48,48,0.09)',   border: 'rgba(160,48,48,0.2)'   },
  MEDIUM: { color: '#9A6F2A', bg: 'rgba(154,111,42,0.09)', border: 'rgba(154,111,42,0.2)' },
  LOW:    { color: '#4D7C3A', bg: 'rgba(77,124,58,0.09)',  border: 'rgba(77,124,58,0.2)'  },
};

const SENTIMENT_STYLES = {
  POSITIVE: { color: '#4D7C3A', bg: 'rgba(77,124,58,0.09)',  border: 'rgba(77,124,58,0.2)',  Icon: TrendingUp   },
  NEGATIVE: { color: '#A03030', bg: 'rgba(160,48,48,0.09)',  border: 'rgba(160,48,48,0.2)',  Icon: TrendingDown },
  NEUTRAL:  { color: '#9A6F2A', bg: 'rgba(154,111,42,0.09)', border: 'rgba(154,111,42,0.2)', Icon: Minus        },
};

const TYPE_META = {
  site_visit:           { Icon: Factory,       label: 'Factory / Site Visit',        placeholder: 'Describe factory conditions, capacity utilization, inventory levels, workforce observations, safety compliance, machinery condition...' },
  management_interview: { Icon: MessageSquare, label: 'Management Interview',         placeholder: 'Summarize management discussion: expansion plans, market outlook, key challenges, revenue projections, competitive position...' },
  observation:          { Icon: Eye,           label: 'Due Diligence Observation',    placeholder: 'Document governance concerns, related party issues, supply chain risks, regulatory compliance gaps...' },
  general:              { Icon: FileText,      label: 'General Note',                 placeholder: 'Enter any relevant observations or notes...' },
};

const SeverityBadge = ({ val }) => {
  const s = SEVERITY_STYLES[val] || SEVERITY_STYLES.LOW;
  return (
    <span style={{ color: s.color, background: s.bg, border: `1px solid ${s.border}`, fontFamily: "'DM Mono', monospace", fontSize: '0.6rem', fontWeight: 500, letterSpacing: '0.1em', textTransform: 'uppercase', padding: '0.22rem 0.6rem', borderRadius: 4, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
      <span style={{ width: 5, height: 5, borderRadius: '50%', background: s.color, display: 'inline-block', flexShrink: 0 }} />
      {val}
    </span>
  );
};

const SentimentBadge = ({ val }) => {
  const s = SENTIMENT_STYLES[val] || SENTIMENT_STYLES.NEUTRAL;
  const { Icon } = s;
  return (
    <span style={{ color: s.color, background: s.bg, border: `1px solid ${s.border}`, fontFamily: "'DM Mono', monospace", fontSize: '0.6rem', fontWeight: 500, letterSpacing: '0.1em', textTransform: 'uppercase', padding: '0.22rem 0.6rem', borderRadius: 4, display: 'inline-flex', alignItems: 'center', gap: 4 }}>
      <Icon size={10} strokeWidth={2} />
      {val}
    </span>
  );
};

const DueDiligencePortal = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [insightType, setInsightType] = useState('site_visit');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [lastResult, setLastResult] = useState(null);
  const [allInsights, setAllInsights] = useState(null);
  const [fetchingInsights, setFetchingInsights] = useState(false);
  const [expandedNotes, setExpandedNotes] = useState({});

  useEffect(() => { if (id) fetchInsights(); }, [id]);

  const fetchInsights = async () => {
    setFetchingInsights(true);
    try { setAllInsights(await api.getDueDiligenceNotes(id)); }
    catch { /* no insights yet */ }
    finally { setFetchingInsights(false); }
  };

  const handleSubmit = async () => {
    if (!notes.trim()) { setError('Please enter your observations'); return; }
    setLoading(true); setError(''); setLastResult(null);
    try {
      const result = await api.addDueDiligenceNotes({ application_id: id, insight_type: insightType, credit_officer_notes: notes });
      setLastResult(result); setNotes('');
      await fetchInsights();
    } catch (e) { setError(e.message || 'Failed to process insight'); }
    finally { setLoading(false); }
  };

  const handleDelete = async (noteId) => {
    try { await api.deleteDueDiligenceNote(id, noteId); await fetchInsights(); }
    catch (e) { setError(e.message || 'Failed to delete'); }
  };

  const toggleExpand = (noteId) => setExpandedNotes(prev => ({ ...prev, [noteId]: !prev[noteId] }));

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
          --charcoal: #2C2416;
          --ink: #3D3020;
          --muted: #7A6850;
          --border: #DDD4C0;
          --border-warm: #C9BCA8;
          --shadow-warm: rgba(160,82,45,0.12);
        }

        .ddp-wrap {
          min-height: 100vh;
          background: var(--cream);
          font-family: 'DM Sans', sans-serif;
          position: relative;
          overflow-x: hidden;
        }

        .ddp-wrap::after {
          content: '';
          position: fixed;
          top: -200px; right: -100px;
          width: 500px; height: 900px;
          background: linear-gradient(160deg, rgba(203,110,69,0.07) 0%, rgba(184,134,11,0.04) 50%, transparent 80%);
          transform: rotate(-15deg);
          pointer-events: none;
          z-index: 0;
        }

        .ddp-inner {
          position: relative;
          z-index: 1;
          max-width: 1120px;
          margin: 0 auto;
          padding: 0 2.5rem 4rem;
        }

        /* TOP BAR */
        .ddp-topbar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 2rem 0 2.5rem;
          border-bottom: 1.5px solid var(--border);
          margin-bottom: 2.5rem;
        }

        .ddp-brand { display: flex; align-items: center; gap: 1rem; }

        .ddp-brand-mark {
          position: relative; width: 48px; height: 48px;
          display: flex; align-items: center; justify-content: center;
        }

        .ddp-ring {
          position: absolute; border-radius: 50%;
          animation: ring-spin 12s linear infinite;
        }
        .ddp-ring-1 { inset: -4px; border: 1.5px solid var(--terracotta); opacity: 0.4; }
        .ddp-ring-2 { inset: -9px; border: 1px dashed var(--gold); opacity: 0.25; animation-duration: 20s; animation-direction: reverse; }

        @keyframes ring-spin { to { transform: rotate(360deg); } }

        .ddp-brand-icon {
          width: 48px; height: 48px;
          background: linear-gradient(135deg, var(--sienna), var(--terracotta));
          border-radius: 50%;
          display: flex; align-items: center; justify-content: center;
          box-shadow: 0 4px 16px rgba(160,82,45,0.35);
        }

        .ddp-brand-eyebrow {
          font-family: 'DM Mono', monospace;
          font-size: 0.6rem; letter-spacing: 0.2em; text-transform: uppercase;
          color: var(--terracotta); margin-bottom: 0.2rem;
        }

        .ddp-brand-name {
          font-family: 'Playfair Display', serif;
          font-size: 1.6rem; font-weight: 700; color: var(--charcoal);
          line-height: 1; letter-spacing: -0.01em;
        }

        .ddp-back {
          display: inline-flex; align-items: center; gap: 0.5rem;
          font-family: 'DM Mono', monospace; font-size: 0.7rem;
          letter-spacing: 0.1em; text-transform: uppercase;
          color: var(--muted); cursor: pointer;
          padding: 0.5rem 1rem; border-radius: 8px;
          border: 1px solid var(--border); background: none;
          transition: all 0.15s;
        }
        .ddp-back:hover { color: var(--sienna); border-color: rgba(160,82,45,0.3); background: rgba(160,82,45,0.04); }

        /* PAGE HEADER */
        .ddp-page-header { margin-bottom: 2rem; }

        .ddp-eyebrow {
          font-family: 'DM Mono', monospace;
          font-size: 0.62rem; letter-spacing: 0.18em; text-transform: uppercase;
          color: var(--terracotta); margin-bottom: 0.5rem;
        }

        .ddp-h1 {
          font-family: 'Playfair Display', serif;
          font-size: 2.4rem; font-weight: 700; color: var(--charcoal);
          line-height: 1.05; letter-spacing: -0.02em; margin-bottom: 0.5rem;
        }

        .ddp-h1 em { font-style: italic; color: var(--terracotta); }

        .ddp-app-id {
          display: inline-flex; align-items: center; gap: 0.4rem;
          font-family: 'DM Mono', monospace; font-size: 0.72rem;
          color: var(--sienna); background: rgba(160,82,45,0.07);
          padding: 0.25rem 0.7rem; border-radius: 4px;
          border: 1px solid rgba(160,82,45,0.15);
        }

        .ornament {
          display: flex; align-items: center; gap: 0.75rem;
          margin-bottom: 2rem;
        }
        .ornament-line { height: 1px; flex: 1; background: linear-gradient(to right, transparent, var(--border-warm), transparent); }
        .ornament-diamond { width: 6px; height: 6px; background: var(--terracotta); transform: rotate(45deg); opacity: 0.5; }

        /* CARD BASE */
        .ddp-card {
          background: var(--warm-white);
          border: 1.5px solid var(--border);
          border-radius: 20px;
          overflow: hidden;
          box-shadow: 0 2px 16px rgba(0,0,0,0.04);
          margin-bottom: 1.5rem;
        }

        .ddp-card-head {
          padding: 1.25rem 1.75rem;
          border-bottom: 1.5px solid var(--border);
          background: linear-gradient(to right, var(--parchment), var(--warm-white));
          display: flex; align-items: center; gap: 0.75rem;
        }

        .ddp-card-head-icon {
          width: 32px; height: 32px;
          background: rgba(160,82,45,0.09);
          border: 1px solid rgba(160,82,45,0.18);
          border-radius: 8px;
          display: flex; align-items: center; justify-content: center;
          flex-shrink: 0;
        }

        .ddp-card-title {
          font-family: 'Playfair Display', serif;
          font-size: 1.05rem; font-weight: 600; color: var(--charcoal);
        }

        .ddp-card-title em { font-style: italic; color: var(--terracotta); }

        .ddp-card-body { padding: 1.75rem; }

        /* TYPE SELECTOR */
        .ddp-type-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 0.75rem;
          margin-bottom: 1.5rem;
        }

        @media (max-width: 768px) { .ddp-type-grid { grid-template-columns: repeat(2,1fr); } }

        .ddp-type-btn {
          padding: 1rem;
          border-radius: 12px;
          border: 1.5px solid var(--border);
          background: var(--cream);
          text-align: left;
          cursor: pointer;
          transition: all 0.18s ease;
          display: flex; flex-direction: column; gap: 0.5rem;
        }

        .ddp-type-btn:hover {
          border-color: rgba(160,82,45,0.3);
          background: rgba(160,82,45,0.04);
        }

        .ddp-type-btn.active {
          border-color: var(--terracotta);
          background: rgba(203,110,69,0.07);
          box-shadow: 0 2px 12px rgba(160,82,45,0.12);
        }

        .ddp-type-icon {
          width: 32px; height: 32px;
          border-radius: 8px;
          display: flex; align-items: center; justify-content: center;
          background: var(--parchment);
          transition: background 0.18s;
        }

        .ddp-type-btn.active .ddp-type-icon {
          background: rgba(160,82,45,0.12);
        }

        .ddp-type-label {
          font-size: 0.75rem;
          font-weight: 500;
          color: var(--ink);
          line-height: 1.3;
        }

        .ddp-type-btn.active .ddp-type-label { color: var(--sienna); }

        /* TEXTAREA */
        .ddp-label {
          font-family: 'DM Mono', monospace;
          font-size: 0.62rem; font-weight: 500;
          letter-spacing: 0.12em; text-transform: uppercase;
          color: var(--muted); margin-bottom: 0.5rem;
          display: block;
        }

        .ddp-textarea {
          width: 100%;
          padding: 0.9rem 1rem;
          background: var(--cream);
          border: 1.5px solid var(--border);
          border-radius: 12px;
          font-family: 'DM Sans', sans-serif;
          font-size: 0.875rem;
          color: var(--charcoal);
          resize: vertical;
          outline: none;
          transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
          box-sizing: border-box;
          line-height: 1.6;
        }

        .ddp-textarea::placeholder { color: var(--border-warm); font-weight: 300; font-size: 0.83rem; }

        .ddp-textarea:focus {
          border-color: var(--terracotta);
          background: var(--warm-white);
          box-shadow: 0 0 0 3px rgba(203,110,69,0.1);
        }

        .ddp-char-count {
          font-family: 'DM Mono', monospace;
          font-size: 0.62rem; color: var(--border-warm);
          text-align: right; margin-top: 0.4rem;
        }

        /* ERROR */
        .ddp-error {
          display: flex; align-items: flex-start; gap: 0.75rem;
          background: rgba(160,48,48,0.06);
          border: 1.5px solid rgba(160,48,48,0.2);
          border-radius: 10px;
          padding: 0.85rem 1rem;
          margin-bottom: 1rem;
        }

        .ddp-error span {
          font-size: 0.82rem; color: #9A3030;
        }

        /* SUBMIT BTN */
        .ddp-submit {
          width: 100%;
          display: flex; align-items: center; justify-content: center; gap: 0.6rem;
          font-family: 'DM Sans', sans-serif;
          font-size: 0.9rem; font-weight: 500;
          color: var(--warm-white);
          background: linear-gradient(135deg, var(--sienna), var(--terracotta));
          border: none; border-radius: 10px;
          padding: 0.85rem;
          cursor: pointer;
          box-shadow: 0 4px 14px var(--shadow-warm), inset 0 1px 0 rgba(255,255,255,0.15);
          transition: all 0.2s;
          margin-top: 1.25rem;
        }

        .ddp-submit:hover:not(:disabled) {
          transform: translateY(-2px);
          box-shadow: 0 8px 22px rgba(160,82,45,0.3), inset 0 1px 0 rgba(255,255,255,0.15);
        }

        .ddp-submit:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

        .ddp-spinner {
          width: 16px; height: 16px;
          border: 2px solid rgba(255,255,255,0.3);
          border-top-color: #fff;
          border-radius: 50%;
          animation: ddp-spin 0.7s linear infinite;
        }

        @keyframes ddp-spin { to { transform: rotate(360deg); } }

        /* AI RESULT CARD */
        .ddp-result {
          background: var(--warm-white);
          border: 1.5px solid rgba(160,82,45,0.25);
          border-left: 4px solid var(--terracotta);
          border-radius: 16px;
          overflow: hidden;
          margin-bottom: 1.5rem;
          box-shadow: 0 4px 20px rgba(160,82,45,0.08);
        }

        .ddp-result-head {
          padding: 1.1rem 1.5rem;
          background: linear-gradient(to right, rgba(203,110,69,0.07), transparent);
          border-bottom: 1px solid rgba(160,82,45,0.12);
          display: flex; align-items: center; gap: 0.6rem;
        }

        .ddp-result-title {
          font-family: 'Playfair Display', serif;
          font-size: 1rem; font-weight: 600; color: var(--charcoal);
        }

        .ddp-result-title em { font-style: italic; color: var(--terracotta); }

        .ddp-result-body { padding: 1.25rem 1.5rem; }

        .ddp-result-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 1rem;
          margin-bottom: 1rem;
        }

        @media (max-width: 768px) { .ddp-result-grid { grid-template-columns: repeat(2,1fr); } }

        .ddp-result-meta-label {
          font-family: 'DM Mono', monospace;
          font-size: 0.58rem; letter-spacing: 0.12em; text-transform: uppercase;
          color: var(--muted); margin-bottom: 0.35rem;
        }

        .ddp-score-adj {
          font-family: 'Playfair Display', serif;
          font-size: 1.4rem; font-weight: 700; line-height: 1;
        }

        .ddp-summary {
          font-size: 0.875rem;
          color: var(--ink);
          line-height: 1.65;
          background: var(--cream);
          border-radius: 10px;
          padding: 0.85rem 1rem;
          border: 1px solid var(--border);
          margin-bottom: 0.85rem;
        }

        .ddp-tag-group { margin-top: 0.75rem; }

        .ddp-tag-label {
          font-family: 'DM Mono', monospace;
          font-size: 0.58rem; letter-spacing: 0.12em; text-transform: uppercase;
          color: var(--muted); margin-bottom: 0.4rem;
        }

        .ddp-tag-row { display: flex; flex-wrap: wrap; gap: 0.4rem; }

        .ddp-tag-risk {
          font-family: 'DM Mono', monospace; font-size: 0.65rem;
          color: #A03030; background: rgba(160,48,48,0.08);
          border: 1px solid rgba(160,48,48,0.18);
          padding: 0.2rem 0.55rem; border-radius: 4px;
        }

        .ddp-tag-entity {
          font-family: 'DM Mono', monospace; font-size: 0.65rem;
          color: var(--sienna); background: rgba(160,82,45,0.08);
          border: 1px solid rgba(160,82,45,0.18);
          padding: 0.2rem 0.55rem; border-radius: 4px;
        }

        /* SUMMARY BAR */
        .ddp-summary-bar {
          background: var(--warm-white);
          border: 1.5px solid var(--border);
          border-radius: 16px;
          padding: 1.25rem 1.75rem;
          margin-bottom: 1.5rem;
          display: flex;
          flex-wrap: wrap;
          align-items: center;
          justify-content: space-between;
          gap: 1rem;
        }

        .ddp-summary-count {
          font-family: 'Playfair Display', serif;
          font-size: 2rem; font-weight: 700; color: var(--charcoal);
          line-height: 1; letter-spacing: -0.02em;
        }

        .ddp-summary-count-label {
          font-size: 0.8rem; color: var(--muted); font-weight: 300;
        }

        .ddp-total-adj {
          font-family: 'DM Mono', monospace;
          font-size: 0.72rem; color: var(--muted);
          display: flex; align-items: center; gap: 0.5rem;
        }

        .ddp-adj-val {
          font-family: 'Playfair Display', serif;
          font-size: 1.2rem; font-weight: 700;
        }

        .ddp-sev-badges { display: flex; gap: 0.5rem; flex-wrap: wrap; }

        /* NOTE CARDS */
        .ddp-note-card {
          background: var(--warm-white);
          border: 1.5px solid var(--border);
          border-radius: 16px;
          overflow: hidden;
          margin-bottom: 1rem;
          transition: box-shadow 0.15s;
        }

        .ddp-note-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.06); }

        .ddp-note-head {
          padding: 1rem 1.5rem;
          background: linear-gradient(to right, var(--parchment), var(--warm-white));
          border-bottom: 1px solid var(--border);
          display: flex; align-items: center;
          justify-content: space-between;
          flex-wrap: wrap; gap: 0.75rem;
        }

        .ddp-note-head-left {
          display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap;
        }

        .ddp-note-type-icon {
          width: 30px; height: 30px;
          background: rgba(160,82,45,0.09);
          border: 1px solid rgba(160,82,45,0.18);
          border-radius: 7px;
          display: flex; align-items: center; justify-content: center;
        }

        .ddp-note-type-label {
          font-family: 'Playfair Display', serif;
          font-size: 0.88rem; font-weight: 600; color: var(--charcoal);
        }

        .ddp-note-head-right { display: flex; align-items: center; gap: 0.75rem; }

        .ddp-delete-btn {
          display: inline-flex; align-items: center; gap: 0.3rem;
          font-family: 'DM Mono', monospace; font-size: 0.62rem;
          letter-spacing: 0.08em; text-transform: uppercase;
          color: var(--border-warm); background: none;
          border: 1px solid var(--border);
          padding: 0.25rem 0.65rem; border-radius: 5px;
          cursor: pointer; transition: all 0.15s;
        }

        .ddp-delete-btn:hover { color: #A03030; border-color: rgba(160,48,48,0.3); background: rgba(160,48,48,0.05); }

        .ddp-note-body { padding: 1.25rem 1.5rem; }

        .ddp-ai-summary {
          font-size: 0.875rem; color: var(--ink); line-height: 1.65;
          background: var(--cream); border-radius: 10px;
          padding: 0.85rem 1rem; border: 1px solid var(--border);
          margin-bottom: 1rem;
        }

        .ddp-expand-toggle {
          display: inline-flex; align-items: center; gap: 0.35rem;
          font-family: 'DM Mono', monospace; font-size: 0.62rem;
          letter-spacing: 0.08em; text-transform: uppercase;
          color: var(--muted); background: none; border: none;
          cursor: pointer; padding: 0; transition: color 0.15s;
          margin-bottom: 0.75rem;
        }

        .ddp-expand-toggle:hover { color: var(--sienna); }

        .ddp-raw-notes {
          font-family: 'DM Sans', sans-serif;
          font-size: 0.82rem; color: var(--muted); line-height: 1.7;
          background: var(--parchment); border-radius: 8px;
          padding: 0.85rem 1rem; border: 1px solid var(--border);
          white-space: pre-wrap; margin-bottom: 0.85rem;
        }

        .ddp-note-date {
          font-family: 'DM Mono', monospace;
          font-size: 0.62rem; color: var(--border-warm);
          letter-spacing: 0.06em;
        }

        /* EMPTY / LOADING */
        .ddp-empty {
          text-align: center; padding: 4rem 2rem;
          display: flex; flex-direction: column; align-items: center; gap: 1rem;
        }

        .ddp-empty-icon {
          width: 60px; height: 60px;
          background: var(--parchment);
          border: 1.5px solid var(--border); border-radius: 16px;
          display: flex; align-items: center; justify-content: center;
        }

        .ddp-empty-title {
          font-family: 'Playfair Display', serif;
          font-size: 1.1rem; font-weight: 600; color: var(--charcoal);
        }

        .ddp-empty-sub { font-size: 0.83rem; color: var(--muted); font-weight: 300; max-width: 320px; line-height: 1.6; }

        .ddp-loading {
          display: flex; flex-direction: column; align-items: center;
          padding: 3rem; gap: 0.75rem;
        }

        .ddp-load-spinner {
          width: 32px; height: 32px;
          border: 2px solid var(--border);
          border-top-color: var(--terracotta);
          border-radius: 50%;
          animation: ddp-spin 0.8s linear infinite;
        }

        .ddp-load-text {
          font-family: 'DM Mono', monospace;
          font-size: 0.65rem; letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted);
        }
      `}</style>

      <div className="ddp-wrap">
        <div className="ddp-inner">

          {/* Top Bar */}
          <div className="ddp-topbar">
            <div className="ddp-brand">
              <div className="ddp-brand-mark">
                <div className="ddp-ring ddp-ring-1" />
                <div className="ddp-ring ddp-ring-2" />
                <div className="ddp-brand-icon">
                  <Shield size={20} color="#FAF7F2" strokeWidth={1.5} />
                </div>
              </div>
              <div>
                <div className="ddp-brand-eyebrow">Corporate Intelligence</div>
                <div className="ddp-brand-name">FraudSentinel</div>
              </div>
            </div>
              <button className="ddp-back" onClick={() => navigate(`/application/${id}`)}>
                <ArrowLeft size={13} /> Back to Application
            </button>
          </div>

          {/* Page Header */}
          <div className="ddp-page-header">
            <div className="ddp-eyebrow">Due Diligence</div>
            <h1 className="ddp-h1">Primary <em>Insights</em> Portal</h1>
            <span className="ddp-app-id">
              <ClipboardList size={11} strokeWidth={1.5} />
              Application: {id}
            </span>
          </div>

          <div className="ornament">
            <div className="ornament-line" />
            <div className="ornament-diamond" />
            <div className="ornament-line" />
          </div>

          {/* Input Form Card */}
          <div className="ddp-card">
            <div className="ddp-card-head">
              <div className="ddp-card-head-icon">
                <Sparkles size={14} color="var(--sienna)" strokeWidth={1.5} />
              </div>
              <span className="ddp-card-title">Add New <em>Insight</em></span>
            </div>
            <div className="ddp-card-body">

              {/* Type Selector */}
              <label className="ddp-label">Insight Type</label>
              <div className="ddp-type-grid">
                {Object.entries(TYPE_META).map(([key, { Icon, label }]) => (
                  <button
                    key={key}
                    onClick={() => setInsightType(key)}
                    className={`ddp-type-btn${insightType === key ? ' active' : ''}`}
                  >
                    <div className="ddp-type-icon">
                      <Icon size={15} color={insightType === key ? 'var(--sienna)' : 'var(--muted)'} strokeWidth={1.5} />
                    </div>
                    <span className="ddp-type-label">{label}</span>
                  </button>
                ))}
              </div>

              {/* Textarea */}
              <label className="ddp-label">Officer's Observations <span style={{ color: 'var(--terracotta)' }}>*</span></label>
              <textarea
                value={notes}
                onChange={e => setNotes(e.target.value)}
                rows={6}
                placeholder={TYPE_META[insightType]?.placeholder}
                className="ddp-textarea"
              />
              <div className="ddp-char-count">{notes.length} characters</div>

              {error && (
                <div className="ddp-error">
                  <AlertTriangle size={15} color="#A03030" strokeWidth={1.5} style={{ flexShrink: 0, marginTop: 1 }} />
                  <span>{error}</span>
                </div>
              )}

              <button className="ddp-submit" onClick={handleSubmit} disabled={loading}>
                {loading ? (
                  <><div className="ddp-spinner" /> Analysing with AI…</>
                ) : (
                  <><Sparkles size={15} strokeWidth={1.5} /> Submit &amp; Analyse with AI</>
                )}
              </button>

            </div>
          </div>

          {/* AI Result */}
          {lastResult?.ai_analysis && (() => {
            const ai = lastResult.ai_analysis;
            const adj = ai.score_adjustment;
            return (
              <div className="ddp-result">
                <div className="ddp-result-head">
                  <Sparkles size={14} color="var(--terracotta)" strokeWidth={1.5} />
                  <span className="ddp-result-title">AI <em>Analysis</em> Result</span>
                </div>
                <div className="ddp-result-body">
                  <div className="ddp-result-grid">
                    <div>
                      <div className="ddp-result-meta-label">Risk Category</div>
                      <span style={{ fontFamily: "'DM Sans', sans-serif", fontWeight: 500, color: 'var(--charcoal)', fontSize: '0.9rem' }}>{ai.risk_category}</span>
                    </div>
                    <div>
                      <div className="ddp-result-meta-label">Severity</div>
                      <SeverityBadge val={ai.severity} />
                    </div>
                    <div>
                      <div className="ddp-result-meta-label">Sentiment</div>
                      <SentimentBadge val={ai.sentiment} />
                    </div>
                    <div>
                      <div className="ddp-result-meta-label">Score Adjustment</div>
                      <span className="ddp-score-adj" style={{ color: adj >= 0 ? '#4D7C3A' : '#A03030' }}>
                        {adj > 0 ? '+' : ''}{adj} pts
                      </span>
                    </div>
                  </div>

                  <div className="ddp-summary">{ai.summary}</div>

                  {(ai.risk_flags || []).length > 0 && (
                    <div className="ddp-tag-group">
                      <div className="ddp-tag-label">Risk Flags</div>
                      <div className="ddp-tag-row">
                        {ai.risk_flags.map((f, i) => <span key={i} className="ddp-tag-risk">{f}</span>)}
                      </div>
                    </div>
                  )}

                  {(ai.entities || []).length > 0 && (
                    <div className="ddp-tag-group" style={{ marginTop: '0.75rem' }}>
                      <div className="ddp-tag-label">Entities Identified</div>
                      <div className="ddp-tag-row">
                        {ai.entities.map((e, i) => <span key={i} className="ddp-tag-entity">{e}</span>)}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            );
          })()}

          {/* Loading */}
          {fetchingInsights && (
            <div className="ddp-card">
              <div className="ddp-loading">
                <div className="ddp-load-spinner" />
                <span className="ddp-load-text">Loading insights…</span>
              </div>
            </div>
          )}

          {/* Summary Bar */}
          {allInsights && allInsights.total_insights > 0 && (() => {
            const adj = allInsights.total_score_adjustment;
            return (
              <>
                <div className="ddp-summary-bar">
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
                    <span className="ddp-summary-count">{allInsights.total_insights}</span>
                    <span className="ddp-summary-count-label">insights recorded</span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
                    <div className="ddp-total-adj">
                      Total Adjustment:
                      <span className="ddp-adj-val" style={{ color: adj >= 0 ? '#4D7C3A' : '#A03030' }}>
                        {adj > 0 ? '+' : ''}{adj} pts
                      </span>
                    </div>
                    <div className="ddp-sev-badges">
                      {Object.entries(allInsights.severity_breakdown || {}).map(([sev, count]) =>
                        count > 0 ? <SeverityBadge key={sev} val={sev} /> : null
                      )}
                    </div>
                  </div>
                  {(allInsights.all_risk_flags || []).length > 0 && (
                    <div style={{ width: '100%', paddingTop: '0.85rem', borderTop: '1px solid var(--border)' }}>
                      <div className="ddp-tag-label" style={{ marginBottom: '0.4rem' }}>All Risk Flags</div>
                      <div className="ddp-tag-row">
                        {allInsights.all_risk_flags.map((f, i) => <span key={i} className="ddp-tag-risk">{f}</span>)}
                      </div>
                    </div>
                  )}
                </div>

                {/* Individual Notes */}
                {(allInsights.notes || []).map(note => {
                  const { Icon, label } = TYPE_META[note.insight_type] || TYPE_META.general;
                  const isExpanded = expandedNotes[note.id];
                  const scoreAdj = note.score_adjustment || 0;
                  return (
                    <div className="ddp-note-card" key={note.id}>
                      <div className="ddp-note-head">
                        <div className="ddp-note-head-left">
                          <div className="ddp-note-type-icon">
                            <Icon size={13} color="var(--sienna)" strokeWidth={1.5} />
                          </div>
                          <span className="ddp-note-type-label">{label}</span>
                          <SeverityBadge val={note.severity} />
                          <SentimentBadge val={note.sentiment} />
                        </div>
                        <div className="ddp-note-head-right">
                          <span style={{ fontFamily: "'Playfair Display', serif", fontSize: '1.1rem', fontWeight: 700, color: scoreAdj >= 0 ? '#4D7C3A' : '#A03030' }}>
                            {scoreAdj > 0 ? '+' : ''}{scoreAdj} pts
                          </span>
                          <button className="ddp-delete-btn" onClick={() => handleDelete(note.id)}>
                            <Trash2 size={10} strokeWidth={1.5} /> Delete
                          </button>
                        </div>
                      </div>

                      <div className="ddp-note-body">
                        {note.ai_summary && (
                          <div className="ddp-ai-summary">{note.ai_summary}</div>
                        )}

                        <button className="ddp-expand-toggle" onClick={() => toggleExpand(note.id)}>
                          {isExpanded ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
                          Original notes ({note.notes?.length || 0} chars)
                        </button>

                        {isExpanded && (
                          <div className="ddp-raw-notes">{note.notes}</div>
                        )}

                        {(note.risk_flags || []).length > 0 && (
                          <div className="ddp-tag-row" style={{ marginBottom: '0.75rem' }}>
                            {note.risk_flags.map((f, i) => <span key={i} className="ddp-tag-risk">{f}</span>)}
                          </div>
                        )}

                        {note.created_at && (
                          <div className="ddp-note-date">
                            {new Date(note.created_at).toLocaleString('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' })}
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </>
            );
          })()}

          {/* Empty State */}
          {allInsights && allInsights.total_insights === 0 && (
            <div className="ddp-card">
              <div className="ddp-empty">
                <div className="ddp-empty-icon">
                  <ClipboardList size={26} color="var(--terracotta)" strokeWidth={1.5} />
                </div>
                <div className="ddp-empty-title">No insights recorded yet</div>
                <p className="ddp-empty-sub">Add your first site visit report, management interview, or observation above.</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default DueDiligencePortal;