import {
    AlertCircle,
    ArrowLeft,
    BarChart3, Briefcase,
    CheckCircle2,
    ChevronDown, ChevronUp,
    FileText,
    Landmark,
    Layers,
    Loader2,
    PieChart,
    Shield,
    Upload,
    X
} from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../utils/api';

/* ── Document categories ── */
const DOC_CATEGORIES = [
  {
    key: 'ALM',
    label: 'ALM',
    full: 'Asset-Liability Management',
    desc: 'Maturity buckets, gap analysis, interest rate sensitivity statements.',
    icon: Layers,
    accept: '.pdf,.xlsx,.xls,.csv',
    color: '#A0522D',
  },
  {
    key: 'SHAREHOLDING_PATTERN',
    label: 'Shareholding',
    full: 'Shareholding Pattern',
    desc: 'Promoter / institutional / public shareholding as per SEBI disclosures.',
    icon: PieChart,
    accept: '.pdf,.xlsx,.xls,.csv',
    color: '#B8860B',
  },
  {
    key: 'BORROWING_PROFILE',
    label: 'Borrowing Profile',
    full: 'Borrowing Profile',
    desc: 'Existing debt facilities, consortium details, repayment schedules.',
    icon: Landmark,
    accept: '.pdf,.xlsx,.xls,.csv',
    color: '#CB6E45',
  },
  {
    key: 'ANNUAL_REPORT',
    label: 'Annual Reports',
    full: 'Annual Reports (P&L, Cashflow, Balance Sheet)',
    desc: 'Audited financials — Profit & Loss, Cash Flow Statement, Balance Sheet.',
    icon: BarChart3,
    accept: '.pdf,.xlsx,.xls,.csv,.json',
    color: '#4D7C3A',
  },
  {
    key: 'PORTFOLIO_DATA',
    label: 'Portfolio Data',
    full: 'Portfolio Cuts / Performance Data',
    desc: 'Segment-wise portfolio quality, NPA trends, provision coverage ratios.',
    icon: Briefcase,
    accept: '.pdf,.xlsx,.xls,.csv',
    color: '#6B5B3E',
  },
];

const DataIngestion = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  // Per-category staged files: { ALM: [File, ...], ... }
  const [staged, setStaged] = useState(() =>
    Object.fromEntries(DOC_CATEGORIES.map(c => [c.key, []]))
  );
  const [uploading, setUploading] = useState(null); // currently uploading category key, or 'ALL'
  const [parsing, setParsing] = useState(false);
  const [uploadedDocs, setUploadedDocs] = useState([]);
  const [dragOver, setDragOver] = useState(null); // category key being dragged over
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [expandedDoc, setExpandedDoc] = useState(null);
  const fileInputRefs = useRef({});

  useEffect(() => { if (id) fetchDocuments(); }, [id]);

  const fetchDocuments = async () => {
    try {
      const res = await api.getDocuments(id);
      setUploadedDocs(res.documents || []);
    } catch (err) {
      console.error('Error fetching documents:', err);
    }
  };

  /* ── Drag / drop handlers ── */
  const onDrag = useCallback((e, catKey) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragOver(catKey);
    else if (e.type === 'dragleave') setDragOver(null);
  }, []);

  const onDrop = useCallback((e, catKey) => {
    e.preventDefault();
    e.stopPropagation();
    setDragOver(null);
    if (e.dataTransfer.files?.length) addFiles(catKey, e.dataTransfer.files);
  }, []);

  const onFileInput = (catKey, e) => {
    if (e.target.files?.length) addFiles(catKey, e.target.files);
    e.target.value = '';
  };

  const addFiles = (catKey, fileList) => {
    const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50 MB
    const oversized = [];
    const valid = [];
    for (const f of Array.from(fileList)) {
      if (f.size > MAX_FILE_SIZE) {
        oversized.push(f.name);
      } else {
        valid.push({ file: f, uid: crypto.randomUUID(), name: f.name, size: f.size });
      }
    }
    if (oversized.length > 0) {
      setError(`Files too large (>50 MB): ${oversized.join(', ')}`);
    }
    if (valid.length > 0) {
      setStaged(prev => ({ ...prev, [catKey]: [...prev[catKey], ...valid] }));
      if (!oversized.length) setError(null);
    }
  };

  const removeStaged = (catKey, uid) => {
    setStaged(prev => ({ ...prev, [catKey]: prev[catKey].filter(f => f.uid !== uid) }));
  };

  /* ── Upload per category ── */
  const uploadCategory = async (catKey) => {
    const catFiles = staged[catKey];
    if (!catFiles.length) return;

    setUploading(catKey);
    setError(null);
    setSuccess(null);

    try {
      const formData = new FormData();
      formData.append('application_id', id);
      formData.append('document_type', catKey);
      catFiles.forEach(({ file }) => formData.append('files', file));

      const res = await api.uploadDocuments(formData);
      setStaged(prev => ({ ...prev, [catKey]: [] }));
      setSuccess(`Uploaded ${res.total_files} file(s) under ${DOC_CATEGORIES.find(c => c.key === catKey)?.label}`);
      await fetchDocuments();
    } catch (err) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(null);
    }
  };

  /* ── Upload all staged ── */
  const uploadAll = async () => {
    const cats = DOC_CATEGORIES.filter(c => staged[c.key].length > 0);
    if (!cats.length) { setError('No files staged for upload'); return; }

    setUploading('ALL');
    setError(null);
    setSuccess(null);

    try {
      let totalUploaded = 0;
      for (const cat of cats) {
        const formData = new FormData();
        formData.append('application_id', id);
        formData.append('document_type', cat.key);
        staged[cat.key].forEach(({ file }) => formData.append('files', file));
        const res = await api.uploadDocuments(formData);
        totalUploaded += res.total_files;
      }
      setStaged(Object.fromEntries(DOC_CATEGORIES.map(c => [c.key, []])));
      setSuccess(`Successfully uploaded ${totalUploaded} file(s) across ${cats.length} categories`);
      await fetchDocuments();
    } catch (err) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(null);
    }
  };

  /* ── Parse ── */
  const handleParse = async () => {
    setParsing(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await api.parseDocuments(id);
      setSuccess(res.parsed_count > 0
        ? `Parsed ${res.parsed_count} document(s) successfully`
        : res.message || 'No pending documents to parse');
      await fetchDocuments();
    } catch (err) {
      setError(err.message || 'Parsing failed');
    } finally {
      setParsing(false);
    }
  };

  /* ── Helpers ── */
  const fmtSize = (b) => b < 1024 ? b + ' B' : b < 1048576 ? (b / 1024).toFixed(1) + ' KB' : (b / 1048576).toFixed(1) + ' MB';

  const totalStaged = DOC_CATEGORIES.reduce((n, c) => n + staged[c.key].length, 0);
  const pendingCount = uploadedDocs.filter(d => d.parse_status === 'PENDING').length;

  const docsByCategory = DOC_CATEGORIES.map(cat => ({
    ...cat,
    docs: uploadedDocs.filter(d => d.document_type === cat.key),
  }));

  const statusColor = { PENDING: '#B8860B', IN_PROGRESS: '#3B82F6', COMPLETED: '#4D7C3A', FAILED: '#A03030' };

  return (
    <>
      <style>{`
        /* ── CSS VARS ── */
        :root {
          --sienna: #A0522D;
          --terracotta: #CB6E45;
          --gold: #B8860B;
          --warm-white: #FAF7F2;
          --cream: #F5F0E8;
          --parchment: #EDE5D4;
          --charcoal: #2C2416;
          --ink: #3D3020;
          --muted: #7A6850;
          --border: #DDD4C0;
          --border-light: #EDE8DD;
          --shadow-warm: rgba(160,82,45,0.08);
          --forest: #4D7C3A;
        }

        .di-wrap {
          min-height: 100vh;
          padding: 2rem 1.5rem 4rem;
          background: var(--cream);
          font-family: 'DM Sans', sans-serif;
        }
        .di-inner {
          max-width: 980px;
          margin: 0 auto;
          display: flex;
          flex-direction: column;
          gap: 1.6rem;
        }

        /* ── TOP BAR ── */
        .di-topbar {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .di-brand {
          display: flex;
          align-items: center;
          gap: 0.65rem;
        }
        .di-brand-mark {
          position: relative;
          width: 36px;
          height: 36px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .di-brand-ring {
          position: absolute;
          inset: 0;
          border-radius: 50%;
          border: 1.8px solid var(--sienna);
          opacity: 0.25;
        }
        .di-brand-ring-2 {
          position: absolute;
          inset: 3px;
          border-radius: 50%;
          border: 1.8px solid var(--sienna);
          opacity: 0.5;
        }
        .di-brand-icon {
          position: relative;
          width: 24px;
          height: 24px;
          background: var(--sienna);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .di-brand-eyebrow {
          font-family: 'DM Mono', monospace;
          font-size: 0.55rem;
          letter-spacing: 0.14em;
          text-transform: uppercase;
          color: var(--muted);
          line-height: 1;
        }
        .di-brand-name {
          font-family: 'Playfair Display', serif;
          font-size: 1rem;
          font-weight: 600;
          color: var(--charcoal);
          line-height: 1.15;
        }
        .di-back-btn {
          display: inline-flex;
          align-items: center;
          gap: 0.35rem;
          font-family: 'DM Sans', sans-serif;
          font-size: 0.78rem;
          font-weight: 500;
          color: var(--muted);
          background: var(--warm-white);
          border: 1.5px solid var(--border);
          padding: 0.45rem 1rem;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.15s;
          text-decoration: none;
        }
        .di-back-btn:hover { border-color: var(--sienna); color: var(--sienna); }

        /* ── PAGE HEADER ── */
        .di-page-header { text-align: center; }
        .di-eyebrow {
          font-family: 'DM Mono', monospace;
          font-size: 0.62rem;
          letter-spacing: 0.14em;
          text-transform: uppercase;
          color: var(--sienna);
          margin-bottom: 0.45rem;
        }
        .di-h1 {
          font-family: 'Playfair Display', serif;
          font-size: 1.75rem;
          font-weight: 700;
          color: var(--charcoal);
          margin: 0 0 0.3rem;
        }
        .di-h1 em { font-style: italic; color: var(--sienna); }
        .di-sub {
          font-size: 0.85rem;
          color: var(--muted);
          max-width: 540px;
          margin: 0 auto;
          line-height: 1.5;
        }

        /* ── ORNAMENT ── */
        .ornament { display: flex; align-items: center; gap: 0.8rem; justify-content: center; }
        .ornament-line { width: 60px; height: 1px; background: linear-gradient(90deg, transparent, var(--border), transparent); }
        .ornament-diamond { width: 6px; height: 6px; background: var(--sienna); transform: rotate(45deg); opacity: 0.5; }

        /* ── ALERT ── */
        .di-alert {
          display: flex;
          align-items: flex-start;
          gap: 0.75rem;
          padding: 0.85rem 1.1rem;
          border-radius: 10px;
          font-size: 0.82rem;
          line-height: 1.45;
        }
        .di-alert-error { background: #FDF2F0; border: 1px solid #E8C8C0; color: #6B2B2B; }
        .di-alert-success { background: #F1F7EE; border: 1px solid #C4D8BC; color: #2D4A21; }
        .di-alert p { margin: 0; }
        .di-alert strong { font-weight: 600; }

        /* ── APP CHIP ── */
        .di-app-chip {
          display: inline-flex;
          align-items: center;
          gap: 0.4rem;
          padding: 0.35rem 0.75rem;
          border-radius: 6px;
          background: var(--parchment);
          border: 1px solid var(--border);
          font-family: 'DM Mono', monospace;
          font-size: 0.68rem;
          letter-spacing: 0.03em;
          color: var(--muted);
          align-self: center;
        }

        /* ── CATEGORY GRID ── */
        .di-cat-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 1.1rem;
        }
        @media (max-width: 700px) { .di-cat-grid { grid-template-columns: 1fr; } }

        .di-cat-card {
          background: var(--warm-white);
          border: 1.5px solid var(--border);
          border-radius: 12px;
          overflow: hidden;
          transition: border-color 0.2s, box-shadow 0.2s;
        }
        .di-cat-card:hover { border-color: rgba(160,82,45,0.25); box-shadow: 0 4px 16px var(--shadow-warm); }
        .di-cat-card[data-drag="true"] { border-color: var(--sienna); box-shadow: 0 0 0 3px rgba(160,82,45,0.12); }

        /* span full width for the last card if odd count */
        .di-cat-card:last-child:nth-child(odd) { grid-column: 1 / -1; }

        .di-cat-head {
          display: flex;
          align-items: center;
          gap: 0.55rem;
          padding: 0.75rem 1rem;
          border-bottom: 1px solid var(--border-light);
          background: linear-gradient(135deg, rgba(160,82,45,0.03) 0%, transparent 60%);
        }
        .di-cat-icon {
          width: 30px;
          height: 30px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        .di-cat-title {
          font-family: 'DM Sans', sans-serif;
          font-size: 0.82rem;
          font-weight: 600;
          color: var(--charcoal);
          line-height: 1.2;
        }
        .di-cat-subtitle {
          font-family: 'DM Sans', sans-serif;
          font-size: 0.68rem;
          color: var(--muted);
          font-weight: 400;
        }
        .di-cat-badge {
          margin-left: auto;
          font-family: 'DM Mono', monospace;
          font-size: 0.6rem;
          font-weight: 600;
          padding: 0.15rem 0.5rem;
          border-radius: 10px;
          letter-spacing: 0.04em;
        }

        /* ── DROP ZONE ── */
        .di-drop {
          padding: 1.1rem 1rem;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.5rem;
          cursor: pointer;
          transition: background 0.15s;
        }
        .di-drop:hover { background: rgba(160,82,45,0.02); }
        .di-drop[data-drag="true"] { background: rgba(160,82,45,0.05); }

        .di-drop-icon {
          width: 40px;
          height: 40px;
          border-radius: 50%;
          border: 2px dashed var(--border);
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--muted);
          transition: all 0.2s;
        }
        .di-drop:hover .di-drop-icon,
        .di-drop[data-drag="true"] .di-drop-icon { border-color: var(--sienna); color: var(--sienna); }

        .di-drop-text {
          font-size: 0.78rem;
          color: var(--muted);
          text-align: center;
          line-height: 1.4;
        }
        .di-drop-text strong { color: var(--sienna); font-weight: 600; cursor: pointer; }
        .di-drop-formats {
          font-family: 'DM Mono', monospace;
          font-size: 0.58rem;
          color: var(--muted);
          letter-spacing: 0.05em;
          opacity: 0.8;
        }

        /* ── STAGED FILES ── */
        .di-staged { padding: 0 0.85rem 0.85rem; }
        .di-staged-file {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.45rem 0.65rem;
          border-radius: 6px;
          background: var(--cream);
          margin-bottom: 0.35rem;
          font-size: 0.78rem;
        }
        .di-staged-name {
          flex: 1;
          font-weight: 500;
          color: var(--ink);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .di-staged-size {
          font-family: 'DM Mono', monospace;
          font-size: 0.6rem;
          color: var(--muted);
          flex-shrink: 0;
        }
        .di-staged-rm {
          background: none;
          border: none;
          cursor: pointer;
          color: var(--muted);
          padding: 2px;
          display: flex;
          transition: color 0.15s;
        }
        .di-staged-rm:hover { color: #A03030; }

        .di-cat-upload-btn {
          display: inline-flex;
          align-items: center;
          gap: 0.35rem;
          font-family: 'DM Sans', sans-serif;
          font-size: 0.72rem;
          font-weight: 600;
          color: var(--warm-white);
          background: var(--sienna);
          border: none;
          padding: 0.4rem 0.9rem;
          border-radius: 6px;
          cursor: pointer;
          margin: 0.3rem 0.85rem 0.85rem;
          transition: all 0.15s;
        }
        .di-cat-upload-btn:hover:not(:disabled) { background: var(--terracotta); }
        .di-cat-upload-btn:disabled { opacity: 0.5; cursor: not-allowed; }

        /* ── BULK ACTIONS ── */
        .di-actions {
          display: flex;
          align-items: center;
          justify-content: flex-end;
          gap: 0.8rem;
          flex-wrap: wrap;
        }
        .di-btn-primary {
          display: inline-flex;
          align-items: center;
          gap: 0.45rem;
          font-family: 'DM Sans', sans-serif;
          font-size: 0.82rem;
          font-weight: 600;
          color: var(--warm-white);
          background: linear-gradient(135deg, var(--sienna) 0%, var(--terracotta) 100%);
          border: none;
          padding: 0.6rem 1.4rem;
          border-radius: 8px;
          cursor: pointer;
          box-shadow: 0 4px 14px var(--shadow-warm);
          transition: all 0.2s;
        }
        .di-btn-primary:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 8px 22px rgba(160,82,45,0.3); }
        .di-btn-primary:disabled { opacity: 0.55; cursor: not-allowed; transform: none; }

        .di-btn-secondary {
          display: inline-flex;
          align-items: center;
          gap: 0.45rem;
          font-family: 'DM Sans', sans-serif;
          font-size: 0.82rem;
          font-weight: 500;
          color: var(--forest);
          background: var(--warm-white);
          border: 1.5px solid rgba(77,124,58,0.3);
          padding: 0.55rem 1.2rem;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.15s;
        }
        .di-btn-secondary:hover:not(:disabled) { border-color: var(--forest); background: #F4F9F1; }
        .di-btn-secondary:disabled { opacity: 0.5; cursor: not-allowed; }

        /* ── SPINNER ── */
        .di-spin {
          animation: di-spin 0.7s linear infinite;
        }
        @keyframes di-spin { to { transform: rotate(360deg); } }

        /* ── UPLOADED DOCS SECTION ── */
        .di-uploaded-section {
          background: var(--warm-white);
          border: 1.5px solid var(--border);
          border-radius: 12px;
          overflow: hidden;
        }
        .di-uploaded-head {
          display: flex;
          align-items: center;
          gap: 0.6rem;
          padding: 0.85rem 1.1rem;
          border-bottom: 1px solid var(--border-light);
          background: linear-gradient(135deg, rgba(160,82,45,0.03) 0%, transparent 60%);
        }
        .di-uploaded-title {
          font-family: 'Playfair Display', serif;
          font-size: 1rem;
          font-weight: 600;
          color: var(--charcoal);
        }
        .di-uploaded-count {
          margin-left: auto;
          font-family: 'DM Mono', monospace;
          font-size: 0.65rem;
          color: var(--muted);
          padding: 0.2rem 0.55rem;
          background: var(--parchment);
          border-radius: 10px;
        }

        /* ── DOC ROW ── */
        .di-doc-row {
          display: flex;
          align-items: center;
          gap: 0.65rem;
          padding: 0.75rem 1.1rem;
          border-bottom: 1px solid var(--border-light);
          transition: background 0.15s;
        }
        .di-doc-row:last-child { border-bottom: none; }
        .di-doc-row:hover { background: rgba(160,82,45,0.02); }

        .di-doc-icon {
          width: 32px;
          height: 32px;
          border-radius: 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
        }
        .di-doc-info { flex: 1; min-width: 0; }
        .di-doc-name {
          font-size: 0.8rem;
          font-weight: 600;
          color: var(--charcoal);
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        .di-doc-meta {
          display: flex;
          align-items: center;
          gap: 0.6rem;
          font-family: 'DM Mono', monospace;
          font-size: 0.6rem;
          color: var(--muted);
          margin-top: 0.15rem;
          letter-spacing: 0.02em;
        }
        .di-doc-status {
          display: inline-flex;
          align-items: center;
          gap: 0.2rem;
          font-family: 'DM Mono', monospace;
          font-size: 0.58rem;
          font-weight: 600;
          letter-spacing: 0.06em;
          padding: 0.15rem 0.5rem;
          border-radius: 10px;
          flex-shrink: 0;
        }
        .di-doc-expand {
          background: none;
          border: none;
          cursor: pointer;
          color: var(--muted);
          padding: 4px;
          display: flex;
          transition: color 0.15s;
        }
        .di-doc-expand:hover { color: var(--sienna); }
        .di-doc-parsed {
          padding: 0 1.1rem 0.75rem 1.1rem;
          margin-top: -0.25rem;
        }
        .di-doc-parsed pre {
          font-family: 'DM Mono', monospace;
          font-size: 0.65rem;
          background: var(--cream);
          padding: 0.65rem;
          border-radius: 6px;
          overflow: auto;
          max-height: 260px;
          line-height: 1.5;
          color: var(--ink);
          border: 1px solid var(--border-light);
        }
        .di-doc-error {
          font-size: 0.75rem;
          color: #6B2B2B;
          background: #FDF2F0;
          padding: 0.5rem 0.7rem;
          border-radius: 6px;
          border: 1px solid #E8C8C0;
        }

        /* ── EMPTY STATE ── */
        .di-empty {
          text-align: center;
          padding: 3rem 1.5rem;
        }
        .di-empty-icon {
          width: 56px;
          height: 56px;
          border-radius: 50%;
          background: var(--parchment);
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 0 auto 1rem;
          color: var(--muted);
        }
        .di-empty h3 {
          font-family: 'Playfair Display', serif;
          font-size: 1.1rem;
          font-weight: 600;
          color: var(--charcoal);
          margin: 0 0 0.35rem;
        }
        .di-empty p { font-size: 0.82rem; color: var(--muted); margin: 0; }
      `}</style>

      <div className="di-wrap">
        <div className="di-inner">

          {/* ── TOP BAR ── */}
          <div className="di-topbar">
            <div className="di-brand">
              <div className="di-brand-mark">
                <div className="di-brand-ring" />
                <div className="di-brand-ring-2" />
                <div className="di-brand-icon">
                  <Shield size={20} color="#FAF7F2" strokeWidth={1.5} />
                </div>
              </div>
              <div>
                <div className="di-brand-eyebrow">Corporate Intelligence</div>
                <div className="di-brand-name">FraudSentinel</div>
              </div>
            </div>
            <button className="di-back-btn" onClick={() => navigate(`/applications/${id}`)}>
              <ArrowLeft size={13} /> Back to Application
            </button>
          </div>

          {/* ── HEADER ── */}
          <div className="di-page-header">
            <div className="di-eyebrow">Pillar 1 — Data Ingestion</div>
            <h1 className="di-h1">Intelligent <em>Document Upload</em></h1>
            <p className="di-sub">Upload critical financial documents across 5 categories. Files are auto-classified, securely stored, and parsed by our ML pipeline.</p>
          </div>

          <div className="di-app-chip">
            <FileText size={11} strokeWidth={1.5} /> Application {id?.slice(0, 8)}…
          </div>

          <div className="ornament">
            <div className="ornament-line" />
            <div className="ornament-diamond" />
            <div className="ornament-line" />
          </div>

          {/* ── ALERTS ── */}
          {error && (
            <div className="di-alert di-alert-error">
              <AlertCircle size={16} strokeWidth={1.5} style={{ flexShrink: 0, marginTop: 2 }} />
              <p><strong>Error:</strong> {error}</p>
            </div>
          )}
          {success && (
            <div className="di-alert di-alert-success">
              <CheckCircle2 size={16} strokeWidth={1.5} style={{ flexShrink: 0, marginTop: 2 }} />
              <p>{success}</p>
            </div>
          )}

          {/* ── CATEGORY CARDS ── */}
          <div className="di-cat-grid">
            {DOC_CATEGORIES.map(cat => {
              const Icon = cat.icon;
              const files = staged[cat.key];
              const existingCount = uploadedDocs.filter(d => d.document_type === cat.key).length;
              const isUploading = uploading === cat.key || uploading === 'ALL';

              return (
                <div
                  key={cat.key}
                  className="di-cat-card"
                  data-drag={dragOver === cat.key ? 'true' : undefined}
                >
                  {/* Card header */}
                  <div className="di-cat-head">
                    <div className="di-cat-icon" style={{ background: `${cat.color}12` }}>
                      <Icon size={16} color={cat.color} strokeWidth={1.5} />
                    </div>
                    <div>
                      <div className="di-cat-title">{cat.full}</div>
                      <div className="di-cat-subtitle">{cat.desc}</div>
                    </div>
                    {existingCount > 0 && (
                      <span className="di-cat-badge" style={{ background: `${cat.color}14`, color: cat.color }}>
                        {existingCount} uploaded
                      </span>
                    )}
                  </div>

                  {/* Drop zone */}
                  <div
                    className="di-drop"
                    data-drag={dragOver === cat.key ? 'true' : undefined}
                    onDragEnter={(e) => onDrag(e, cat.key)}
                    onDragOver={(e) => onDrag(e, cat.key)}
                    onDragLeave={(e) => onDrag(e, cat.key)}
                    onDrop={(e) => onDrop(e, cat.key)}
                    onClick={() => fileInputRefs.current[cat.key]?.click()}
                  >
                    <input
                      ref={el => fileInputRefs.current[cat.key] = el}
                      type="file"
                      multiple
                      accept={cat.accept}
                      onChange={(e) => onFileInput(cat.key, e)}
                      style={{ display: 'none' }}
                    />
                    <div className="di-drop-icon">
                      <Upload size={16} strokeWidth={1.5} />
                    </div>
                    <div className="di-drop-text">
                      Drag & drop or <strong>browse</strong>
                    </div>
                    <div className="di-drop-formats">{cat.accept.replace(/\./g, '').toUpperCase()}</div>
                  </div>

                  {/* Staged files */}
                  {files.length > 0 && (
                    <div className="di-staged">
                      {files.map(f => (
                        <div key={f.uid} className="di-staged-file">
                          <FileText size={13} color={cat.color} strokeWidth={1.5} />
                          <span className="di-staged-name">{f.name}</span>
                          <span className="di-staged-size">{fmtSize(f.size)}</span>
                          <button className="di-staged-rm" onClick={() => removeStaged(cat.key, f.uid)} title="Remove">
                            <X size={13} />
                          </button>
                        </div>
                      ))}
                      <button
                        className="di-cat-upload-btn"
                        onClick={() => uploadCategory(cat.key)}
                        disabled={isUploading}
                      >
                        {isUploading
                          ? <><Loader2 size={13} className="di-spin" /> Uploading…</>
                          : <><Upload size={13} /> Upload {files.length} file{files.length > 1 ? 's' : ''}</>
                        }
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* ── BULK ACTIONS ── */}
          <div className="di-actions">
            {totalStaged > 0 && (
              <button className="di-btn-primary" onClick={uploadAll} disabled={!!uploading}>
                {uploading === 'ALL'
                  ? <><Loader2 size={15} className="di-spin" /> Uploading…</>
                  : <><Upload size={15} /> Upload All ({totalStaged} files)</>
                }
              </button>
            )}
            {pendingCount > 0 && (
              <button className="di-btn-secondary" onClick={handleParse} disabled={parsing}>
                {parsing
                  ? <><Loader2 size={15} className="di-spin" /> Parsing…</>
                  : <><BarChart3 size={15} /> Parse {pendingCount} Pending</>
                }
              </button>
            )}
          </div>

          {/* ── UPLOADED DOCUMENTS ── */}
          {uploadedDocs.length > 0 && (
            <div className="di-uploaded-section">
              <div className="di-uploaded-head">
                <FileText size={16} color="var(--sienna)" strokeWidth={1.5} />
                <span className="di-uploaded-title">Uploaded Documents</span>
                <span className="di-uploaded-count">{uploadedDocs.length} total</span>
              </div>

              {docsByCategory.filter(c => c.docs.length > 0).map(cat => (
                <div key={cat.key}>
                  {cat.docs.map(doc => {
                    const Icon = cat.icon;
                    const sc = statusColor[doc.parse_status] || '#7A6850';
                    return (
                      <div key={doc.file_id}>
                        <div className="di-doc-row">
                          <div className="di-doc-icon" style={{ background: `${cat.color}12` }}>
                            <Icon size={15} color={cat.color} strokeWidth={1.5} />
                          </div>
                          <div className="di-doc-info">
                            <div className="di-doc-name">{doc.filename}</div>
                            <div className="di-doc-meta">
                              <span>{cat.label}</span>
                              <span>•</span>
                              <span>{doc.classification_confidence != null ? `${(doc.classification_confidence * 100).toFixed(0)}% conf` : ''}</span>
                              {doc.uploaded_at && <><span>•</span><span>{new Date(doc.uploaded_at).toLocaleDateString()}</span></>}
                            </div>
                          </div>
                          <span className="di-doc-status" style={{ background: `${sc}14`, color: sc }}>
                            {doc.parse_status}
                          </span>
                          {(doc.parse_status === 'COMPLETED' || doc.parse_status === 'FAILED') && (
                            <button className="di-doc-expand" onClick={() => setExpandedDoc(expandedDoc === doc.file_id ? null : doc.file_id)}>
                              {expandedDoc === doc.file_id ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
                            </button>
                          )}
                        </div>
                        {expandedDoc === doc.file_id && doc.parse_status === 'COMPLETED' && doc.parsed_data && (
                          <div className="di-doc-parsed">
                            <pre>{JSON.stringify(doc.parsed_data, null, 2)}</pre>
                          </div>
                        )}
                        {expandedDoc === doc.file_id && doc.parse_status === 'FAILED' && doc.parse_error && (
                          <div className="di-doc-parsed">
                            <div className="di-doc-error"><strong>Error:</strong> {doc.parse_error}</div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ))}
            </div>
          )}

          {/* ── EMPTY STATE ── */}
          {uploadedDocs.length === 0 && totalStaged === 0 && (
            <div className="di-empty">
              <div className="di-empty-icon"><Upload size={24} strokeWidth={1.5} /></div>
              <h3>No Documents Yet</h3>
              <p>Drag files into any category above, or click to browse.</p>
            </div>
          )}

          {/* ── NEXT STEP NAV ── */}
          {uploadedDocs.length > 0 && (
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.75rem' }}>
              <button className="di-btn-secondary" onClick={() => navigate(`/application/${id}/extraction`)}>
                Next: Extraction & Mapping →
              </button>
            </div>
          )}

        </div>
      </div>
    </>
  );
};

export default DataIngestion;
