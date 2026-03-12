import {
    AlertCircle,
    ArrowLeft,
    BarChart3, Briefcase,
    Check,
    CheckCircle2,
    ChevronDown, ChevronUp,
    Database,
    Edit3,
    FileText,
    Landmark,
    Layers,
    Loader2,
    PieChart,
    Play,
    Plus,
    Save,
    Settings2,
    Shield,
    Trash2,
    X
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { api } from '../utils/api';

/* ── Doc-type metadata ── */
const DOC_META = {
  ALM:                   { label: 'ALM', color: '#A0522D', icon: Layers },
  SHAREHOLDING_PATTERN:  { label: 'Shareholding', color: '#B8860B', icon: PieChart },
  BORROWING_PROFILE:     { label: 'Borrowing', color: '#CB6E45', icon: Landmark },
  ANNUAL_REPORT:         { label: 'Annual Report', color: '#4D7C3A', icon: BarChart3 },
  PORTFOLIO_DATA:        { label: 'Portfolio', color: '#6B5B3E', icon: Briefcase },
  BANK_STATEMENT:        { label: 'Bank Stmt', color: '#5A7DA0', icon: Landmark },
  GST_RETURN:            { label: 'GST Return', color: '#7A6850', icon: FileText },
  ITR:                   { label: 'ITR', color: '#856840', icon: FileText },
  BALANCE_SHEET:         { label: 'Balance Sheet', color: '#4F7942', icon: BarChart3 },
  OTHER:                 { label: 'Other', color: '#7A6850', icon: FileText },
};

const ALL_TYPES = Object.keys(DOC_META);
const FIELD_TYPES = ['text', 'number', 'date'];

const ExtractionMapping = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [docs, setDocs] = useState([]);
  const [schemas, setSchemas] = useState([]);
  const [defaults, setDefaults] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // UI state
  const [activeTab, setActiveTab] = useState('classify'); // classify | schema | extract
  const [selectedDoc, setSelectedDoc] = useState(null);
  const [editingType, setEditingType] = useState(null); // doc id being type-edited
  const [editTypeValue, setEditTypeValue] = useState('');
  const [extracting, setExtracting] = useState(null); // doc id
  const [editingFields, setEditingFields] = useState(null); // doc id currently editing extracted fields
  const [editFieldValues, setEditFieldValues] = useState({});

  // Schema editor
  const [schemaEditorOpen, setSchemaEditorOpen] = useState(false);
  const [schemaEditorDocType, setSchemaEditorDocType] = useState('ANNUAL_REPORT');
  const [schemaEditorName, setSchemaEditorName] = useState('');
  const [schemaEditorFields, setSchemaEditorFields] = useState([]);
  const [savingSchema, setSavingSchema] = useState(false);

  useEffect(() => { loadAll(); }, [id]);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [docRes, schemaRes, defaultRes] = await Promise.all([
        api.getExtractionDocuments(id),
        api.getExtractionSchemas(id),
        api.getDefaultSchemas(),
      ]);
      setDocs(docRes.documents || []);
      setSchemas(schemaRes.schemas || []);
      setDefaults(defaultRes || {});
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  /* ── Classification review ── */
  const approveClassification = async (docId) => {
    try {
      await api.reviewClassification(docId, { action: 'approve' });
      flash('Classification approved');
      await loadAll();
    } catch (err) { setError(err.message); }
  };

  const saveEditedType = async (docId) => {
    try {
      await api.reviewClassification(docId, { action: 'edit', corrected_type: editTypeValue });
      setEditingType(null);
      flash('Classification updated');
      await loadAll();
    } catch (err) { setError(err.message); }
  };

  /* ── Extraction ── */
  const runExtraction = async (docId, schemaId = null) => {
    setExtracting(docId);
    setError(null);
    try {
      await api.extractDocument(docId, { schema_id: schemaId || null });
      flash('Extraction complete');
      await loadAll();
    } catch (err) { setError(err.message); }
    finally { setExtracting(null); }
  };

  const saveEditedFields = async (docId) => {
    try {
      await api.updateExtractedFields(docId, { extracted_fields: editFieldValues });
      setEditingFields(null);
      flash('Fields updated');
      await loadAll();
    } catch (err) { setError(err.message); }
  };

  /* ── Schema CRUD ── */
  const openSchemaEditor = (docType) => {
    const def = defaults[docType] || defaults['OTHER'];
    setSchemaEditorDocType(docType);
    setSchemaEditorName(def?.name || docType);
    setSchemaEditorFields(def?.fields?.map(f => ({ ...f })) || []);
    setSchemaEditorOpen(true);
  };

  const addSchemaField = () => {
    setSchemaEditorFields(prev => [...prev, { key: '', label: '', type: 'text', required: false }]);
  };

  const removeSchemaField = (idx) => {
    setSchemaEditorFields(prev => prev.filter((_, i) => i !== idx));
  };

  const updateSchemaField = (idx, field, value) => {
    setSchemaEditorFields(prev => prev.map((f, i) => i === idx ? { ...f, [field]: value } : f));
  };

  const saveSchema = async () => {
    setSavingSchema(true);
    try {
      await api.createExtractionSchema(id, {
        document_type: schemaEditorDocType,
        schema_name: schemaEditorName,
        fields: schemaEditorFields.filter(f => f.key && f.label),
      });
      setSchemaEditorOpen(false);
      flash('Schema saved');
      await loadAll();
    } catch (err) { setError(err.message); }
    finally { setSavingSchema(false); }
  };

  const deleteSchema = async (schemaId) => {
    try {
      await api.deleteExtractionSchema(schemaId);
      flash('Schema deleted');
      await loadAll();
    } catch (err) { setError(err.message); }
  };

  /* ── Helpers ── */
  const flash = (msg) => { setSuccess(msg); setTimeout(() => setSuccess(null), 3500); };
  const confPct = (c) => c != null ? `${(c * 100).toFixed(0)}%` : '—';

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '60vh' }}>
        <Loader2 size={32} className="ex-spin" style={{ color: '#A0522D' }} />
      </div>
    );
  }

  return (
    <>
      <style>{`
        :root {
          --sienna: #A0522D; --terracotta: #CB6E45; --gold: #B8860B;
          --warm-white: #FAF7F2; --cream: #F5F0E8; --parchment: #EDE5D4;
          --charcoal: #2C2416; --ink: #3D3020; --muted: #7A6850;
          --border: #DDD4C0; --border-light: #EDE8DD;
          --shadow-warm: rgba(160,82,45,0.08); --forest: #4D7C3A;
        }
        .ex-wrap { min-height:100vh; padding:2rem 1.5rem 4rem; background:var(--cream); font-family:'DM Sans',sans-serif; }
        .ex-inner { max-width:1040px; margin:0 auto; display:flex; flex-direction:column; gap:1.4rem; }

        /* top bar */
        .ex-topbar { display:flex; justify-content:space-between; align-items:center; }
        .ex-brand { display:flex; align-items:center; gap:0.65rem; }
        .ex-brand-mark { position:relative; width:36px; height:36px; display:flex; align-items:center; justify-content:center; }
        .ex-brand-ring { position:absolute; inset:0; border-radius:50%; border:1.8px solid var(--sienna); opacity:0.25; }
        .ex-brand-ring-2 { position:absolute; inset:3px; border-radius:50%; border:1.8px solid var(--sienna); opacity:0.5; }
        .ex-brand-icon { position:relative; width:24px; height:24px; background:var(--sienna); border-radius:50%; display:flex; align-items:center; justify-content:center; }
        .ex-brand-eyebrow { font-family:'DM Mono',monospace; font-size:0.55rem; letter-spacing:0.14em; text-transform:uppercase; color:var(--muted); line-height:1; }
        .ex-brand-name { font-family:'Playfair Display',serif; font-size:1rem; font-weight:600; color:var(--charcoal); line-height:1.15; }
        .ex-back-btn { display:inline-flex; align-items:center; gap:0.35rem; font-family:'DM Sans',sans-serif; font-size:0.78rem; font-weight:500; color:var(--muted); background:var(--warm-white); border:1.5px solid var(--border); padding:0.45rem 1rem; border-radius:8px; cursor:pointer; transition:all 0.15s; text-decoration:none; }
        .ex-back-btn:hover { border-color:var(--sienna); color:var(--sienna); }

        /* header */
        .ex-header { text-align:center; }
        .ex-eyebrow { font-family:'DM Mono',monospace; font-size:0.62rem; letter-spacing:0.14em; text-transform:uppercase; color:var(--sienna); margin-bottom:0.45rem; }
        .ex-h1 { font-family:'Playfair Display',serif; font-size:1.75rem; font-weight:700; color:var(--charcoal); margin:0 0 0.3rem; }
        .ex-h1 em { font-style:italic; color:var(--sienna); }
        .ex-sub { font-size:0.85rem; color:var(--muted); max-width:600px; margin:0 auto; line-height:1.5; }

        /* ornament */
        .ornament{display:flex;align-items:center;gap:0.8rem;justify-content:center;}
        .ornament-line{width:60px;height:1px;background:linear-gradient(90deg,transparent,var(--border),transparent);}
        .ornament-diamond{width:6px;height:6px;background:var(--sienna);transform:rotate(45deg);opacity:0.5;}

        /* alerts */
        .ex-alert { display:flex; align-items:flex-start; gap:0.75rem; padding:0.85rem 1.1rem; border-radius:10px; font-size:0.82rem; line-height:1.45; }
        .ex-alert-error { background:#FDF2F0; border:1px solid #E8C8C0; color:#6B2B2B; }
        .ex-alert-success { background:#F1F7EE; border:1px solid #C4D8BC; color:#2D4A21; }
        .ex-alert p { margin:0; }

        /* tabs */
        .ex-tabs { display:flex; gap:0; background:var(--warm-white); border:1.5px solid var(--border); border-radius:10px; overflow:hidden; }
        .ex-tab { flex:1; padding:0.7rem 0.5rem; text-align:center; font-family:'DM Sans',sans-serif; font-size:0.78rem; font-weight:600; color:var(--muted); background:none; border:none; cursor:pointer; transition:all 0.15s; border-right:1px solid var(--border); display:flex; align-items:center; justify-content:center; gap:0.4rem; }
        .ex-tab:last-child { border-right:none; }
        .ex-tab[data-active="true"] { background:linear-gradient(135deg,rgba(160,82,45,0.07) 0%,transparent 60%); color:var(--sienna); }
        .ex-tab:hover:not([data-active="true"]) { background:rgba(160,82,45,0.03); }
        .ex-tab-badge { font-family:'DM Mono',monospace; font-size:0.58rem; padding:0.1rem 0.4rem; border-radius:8px; background:var(--parchment); }
        .ex-tab[data-active="true"] .ex-tab-badge { background:rgba(160,82,45,0.12); color:var(--sienna); }

        /* card */
        .ex-card { background:var(--warm-white); border:1.5px solid var(--border); border-radius:12px; overflow:hidden; }
        .ex-card-head { display:flex; align-items:center; gap:0.55rem; padding:0.75rem 1rem; border-bottom:1px solid var(--border-light); background:linear-gradient(135deg,rgba(160,82,45,0.03) 0%,transparent 60%); }
        .ex-card-head-icon { width:28px; height:28px; border-radius:7px; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
        .ex-card-head-title { font-family:'DM Sans',sans-serif; font-size:0.85rem; font-weight:600; color:var(--charcoal); }
        .ex-card-head-sub { font-size:0.7rem; color:var(--muted); margin-left:0.3rem; }
        .ex-card-body { padding:0; }

        /* doc row */
        .ex-row { display:flex; align-items:center; gap:0.6rem; padding:0.7rem 1rem; border-bottom:1px solid var(--border-light); transition:background 0.1s; cursor:pointer; }
        .ex-row:last-child { border-bottom:none; }
        .ex-row:hover { background:rgba(160,82,45,0.02); }
        .ex-row[data-selected="true"] { background:rgba(160,82,45,0.05); }
        .ex-row-icon { width:30px; height:30px; border-radius:7px; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
        .ex-row-info { flex:1; min-width:0; }
        .ex-row-name { font-size:0.8rem; font-weight:600; color:var(--charcoal); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
        .ex-row-meta { display:flex; align-items:center; gap:0.5rem; font-family:'DM Mono',monospace; font-size:0.6rem; color:var(--muted); margin-top:0.1rem; letter-spacing:0.02em; }
        .ex-badge { font-family:'DM Mono',monospace; font-size:0.58rem; font-weight:600; letter-spacing:0.05em; padding:0.15rem 0.5rem; border-radius:10px; flex-shrink:0; white-space:nowrap; }

        /* action buttons */
        .ex-btn { display:inline-flex; align-items:center; gap:0.35rem; font-family:'DM Sans',sans-serif; font-size:0.72rem; font-weight:600; padding:0.35rem 0.7rem; border-radius:6px; cursor:pointer; transition:all 0.15s; border:none; }
        .ex-btn-primary { color:var(--warm-white); background:var(--sienna); }
        .ex-btn-primary:hover:not(:disabled) { background:var(--terracotta); }
        .ex-btn-primary:disabled { opacity:0.5; cursor:not-allowed; }
        .ex-btn-outline { color:var(--sienna); background:none; border:1.5px solid rgba(160,82,45,0.25); }
        .ex-btn-outline:hover { border-color:var(--sienna); background:rgba(160,82,45,0.04); }
        .ex-btn-ghost { color:var(--muted); background:none; border:1px solid var(--border); }
        .ex-btn-ghost:hover { border-color:var(--sienna); color:var(--sienna); }
        .ex-btn-danger { color:#A03030; background:none; border:1px solid rgba(160,48,48,0.2); }
        .ex-btn-danger:hover { background:rgba(160,48,48,0.05); border-color:rgba(160,48,48,0.4); }
        .ex-btn-success { color:var(--forest); background:none; border:1.5px solid rgba(77,124,58,0.25); }
        .ex-btn-success:hover { background:rgba(77,124,58,0.06); border-color:var(--forest); }

        .ex-actions { display:flex; gap:0.4rem; flex-shrink:0; align-items:center; }

        /* select */
        .ex-select { font-family:'DM Sans',sans-serif; font-size:0.75rem; padding:0.35rem 0.6rem; border:1.5px solid var(--border); border-radius:6px; background:var(--warm-white); color:var(--ink); cursor:pointer; }
        .ex-select:focus { border-color:var(--sienna); outline:none; }

        /* detail panel */
        .ex-detail { padding:1rem; }
        .ex-detail-title { font-family:'Playfair Display',serif; font-size:1rem; font-weight:600; color:var(--charcoal); margin:0 0 0.75rem; }

        /* fields table */
        .ex-fields { display:grid; grid-template-columns:1fr 1fr; gap:0.6rem 1.2rem; }
        @media (max-width:640px) { .ex-fields { grid-template-columns:1fr; } }
        .ex-field-item { display:flex; flex-direction:column; gap:0.1rem; padding:0.55rem 0; border-bottom:1px solid var(--border-light); }
        .ex-field-label { font-family:'DM Mono',monospace; font-size:0.6rem; font-weight:500; letter-spacing:0.07em; text-transform:uppercase; color:var(--muted); }
        .ex-field-value { font-size:0.85rem; font-weight:500; color:var(--ink); }
        .ex-field-value.empty { color:var(--muted); font-style:italic; font-weight:400; }
        .ex-field-input { font-family:'DM Sans',sans-serif; font-size:0.82rem; padding:0.35rem 0.5rem; border:1.5px solid var(--border); border-radius:6px; background:var(--warm-white); color:var(--ink); width:100%; }
        .ex-field-input:focus { border-color:var(--sienna); outline:none; }

        /* schema editor */
        .ex-schema-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.35); z-index:100; display:flex; align-items:center; justify-content:center; }
        .ex-schema-modal { background:var(--warm-white); border-radius:14px; width:min(680px,95vw); max-height:85vh; display:flex; flex-direction:column; box-shadow:0 20px 60px rgba(0,0,0,0.18); }
        .ex-schema-modal-head { display:flex; align-items:center; gap:0.5rem; padding:1rem 1.2rem; border-bottom:1px solid var(--border); }
        .ex-schema-modal-head h2 { font-family:'Playfair Display',serif; font-size:1.1rem; font-weight:600; color:var(--charcoal); margin:0; flex:1; }
        .ex-schema-modal-body { flex:1; overflow-y:auto; padding:1rem 1.2rem; display:flex; flex-direction:column; gap:0.8rem; }
        .ex-schema-modal-foot { display:flex; justify-content:flex-end; gap:0.5rem; padding:0.85rem 1.2rem; border-top:1px solid var(--border); }

        .ex-schema-row { display:grid; grid-template-columns:1fr 1.4fr 80px 60px 36px; gap:0.4rem; align-items:center; padding:0.4rem 0; border-bottom:1px solid var(--border-light); }
        .ex-schema-row:last-child { border-bottom:none; }
        .ex-schema-input { font-family:'DM Mono',monospace; font-size:0.72rem; padding:0.3rem 0.5rem; border:1.5px solid var(--border); border-radius:5px; background:var(--cream); color:var(--ink); }
        .ex-schema-input:focus { border-color:var(--sienna); outline:none; background:var(--warm-white); }
        .ex-schema-select { font-family:'DM Mono',monospace; font-size:0.7rem; padding:0.25rem 0.3rem; border:1.5px solid var(--border); border-radius:5px; background:var(--cream); }
        .ex-schema-cb { width:14px; height:14px; accent-color:var(--sienna); }
        .ex-schema-rm { background:none; border:none; cursor:pointer; color:var(--muted); display:flex; padding:3px; transition:color 0.15s; }
        .ex-schema-rm:hover { color:#A03030; }

        .ex-input-row { display:flex; gap:0.5rem; align-items:center; }
        .ex-input-row label { font-family:'DM Mono',monospace; font-size:0.6rem; letter-spacing:0.06em; text-transform:uppercase; color:var(--muted); white-space:nowrap; }
        .ex-input-row input, .ex-input-row select { flex:1; font-family:'DM Sans',sans-serif; font-size:0.82rem; padding:0.4rem 0.6rem; border:1.5px solid var(--border); border-radius:6px; background:var(--warm-white); color:var(--ink); }

        /* empty */
        .ex-empty { text-align:center; padding:2.5rem 1.5rem; color:var(--muted); }
        .ex-empty-icon { width:48px; height:48px; border-radius:50%; background:var(--parchment); display:flex; align-items:center; justify-content:center; margin:0 auto 0.8rem; }
        .ex-empty h3 { font-family:'Playfair Display',serif; font-size:1rem; font-weight:600; color:var(--charcoal); margin:0 0 0.3rem; }
        .ex-empty p { font-size:0.82rem; margin:0; }

        /* spinner */
        .ex-spin { animation:ex-spin 0.7s linear infinite; }
        @keyframes ex-spin { to { transform:rotate(360deg); } }
      `}</style>

      <div className="ex-wrap">
        <div className="ex-inner">

          {/* ── TOP BAR ── */}
          <div className="ex-topbar">
            <div className="ex-brand">
              <div className="ex-brand-mark">
                <div className="ex-brand-ring" /><div className="ex-brand-ring-2" />
                <div className="ex-brand-icon"><Shield size={20} color="#FAF7F2" strokeWidth={1.5} /></div>
              </div>
              <div>
                <div className="ex-brand-eyebrow">Corporate Intelligence</div>
                <div className="ex-brand-name">FraudSentinel</div>
              </div>
            </div>
            <button className="ex-back-btn" onClick={() => navigate(`/application/${id}`)}>
              <ArrowLeft size={13} /> Back to Application
            </button>
          </div>

          {/* ── HEADER ── */}
          <div className="ex-header">
            <div className="ex-eyebrow">Pillar 1 — Automated Extraction</div>
            <h1 className="ex-h1">Extraction &amp; <em>Schema Mapping</em></h1>
            <p className="ex-sub">Review classifications, define extraction schemas, and map structured data from uploaded documents.</p>
          </div>

          <div className="ornament"><div className="ornament-line"/><div className="ornament-diamond"/><div className="ornament-line"/></div>

          {/* ── ALERTS ── */}
          {error && <div className="ex-alert ex-alert-error"><AlertCircle size={16} style={{ flexShrink:0, marginTop:2 }} /><p>{error}</p></div>}
          {success && <div className="ex-alert ex-alert-success"><CheckCircle2 size={16} style={{ flexShrink:0, marginTop:2 }} /><p>{success}</p></div>}

          {/* ── TABS ── */}
          <div className="ex-tabs">
            <button className="ex-tab" data-active={activeTab === 'classify' ? 'true' : undefined} onClick={() => setActiveTab('classify')}>
              <FileText size={14} /> Classify
              <span className="ex-tab-badge">{docs.filter(d => (d.reviewed || 'pending') === 'pending').length} pending</span>
            </button>
            <button className="ex-tab" data-active={activeTab === 'schema' ? 'true' : undefined} onClick={() => setActiveTab('schema')}>
              <Settings2 size={14} /> Schemas
              <span className="ex-tab-badge">{schemas.length + Object.keys(defaults).length}</span>
            </button>
            <button className="ex-tab" data-active={activeTab === 'extract' ? 'true' : undefined} onClick={() => setActiveTab('extract')}>
              <Database size={14} /> Extract
              <span className="ex-tab-badge">{docs.filter(d => d.extracted_fields).length}/{docs.length}</span>
            </button>
          </div>

          {/* ═══════════════════ TAB 1 — CLASSIFY ═══════════════════ */}
          {activeTab === 'classify' && (
            <div className="ex-card">
              <div className="ex-card-head">
                <div className="ex-card-head-icon" style={{ background: 'rgba(160,82,45,0.08)' }}>
                  <FileText size={15} color="var(--sienna)" strokeWidth={1.5} />
                </div>
                <span className="ex-card-head-title">Classification Review</span>
                <span className="ex-card-head-sub">— approve or correct auto-detected types</span>
              </div>

              <div className="ex-card-body">
                {docs.length === 0 ? (
                  <div className="ex-empty">
                    <div className="ex-empty-icon"><FileText size={22} /></div>
                    <h3>No Documents</h3>
                    <p>Upload documents first from the Data Ingestion page.</p>
                  </div>
                ) : docs.map(doc => {
                  const meta = DOC_META[doc.effective_type] || DOC_META.OTHER;
                  const Icon = meta.icon;
                  const reviewed = doc.reviewed || 'pending';
                  const isEditing = editingType === doc.file_id;
                  return (
                    <div key={doc.file_id} className="ex-row">
                      <div className="ex-row-icon" style={{ background: `${meta.color}12` }}>
                        <Icon size={15} color={meta.color} strokeWidth={1.5} />
                      </div>
                      <div className="ex-row-info">
                        <div className="ex-row-name">{doc.filename}</div>
                        <div className="ex-row-meta">
                          <span>{meta.label}</span>
                          <span>•</span>
                          <span>Confidence {confPct(doc.classification_confidence)}</span>
                        </div>
                      </div>

                      {/* Review status */}
                      {reviewed === 'approved' && (
                        <span className="ex-badge" style={{ background: 'rgba(77,124,58,0.12)', color: '#4D7C3A' }}>
                          <CheckCircle2 size={10} style={{ marginRight: 3 }} /> Approved
                        </span>
                      )}
                      {reviewed === 'edited' && (
                        <span className="ex-badge" style={{ background: 'rgba(184,134,11,0.12)', color: '#B8860B' }}>
                          <Edit3 size={10} style={{ marginRight: 3 }} /> Edited → {doc.reviewed_type}
                        </span>
                      )}
                      {reviewed === 'pending' && (
                        <span className="ex-badge" style={{ background: 'var(--parchment)', color: 'var(--muted)' }}>
                          Pending
                        </span>
                      )}

                      {/* Actions */}
                      <div className="ex-actions">
                        {isEditing ? (
                          <>
                            <select className="ex-select" value={editTypeValue} onChange={e => setEditTypeValue(e.target.value)}>
                              {ALL_TYPES.map(t => <option key={t} value={t}>{DOC_META[t]?.label || t}</option>)}
                            </select>
                            <button className="ex-btn ex-btn-primary" onClick={() => saveEditedType(doc.file_id)}><Check size={12} /></button>
                            <button className="ex-btn ex-btn-ghost" onClick={() => setEditingType(null)}><X size={12} /></button>
                          </>
                        ) : (
                          <>
                            {reviewed === 'pending' && (
                              <button className="ex-btn ex-btn-success" onClick={() => approveClassification(doc.file_id)}>
                                <Check size={12} /> Approve
                              </button>
                            )}
                            <button className="ex-btn ex-btn-outline" onClick={() => { setEditingType(doc.file_id); setEditTypeValue(doc.effective_type); }}>
                              <Edit3 size={12} /> Edit
                            </button>
                          </>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ═══════════════════ TAB 2 — SCHEMAS ═══════════════════ */}
          {activeTab === 'schema' && (
            <>
              {/* Default schemas */}
              <div className="ex-card">
                <div className="ex-card-head">
                  <div className="ex-card-head-icon" style={{ background: 'rgba(160,82,45,0.08)' }}>
                    <Settings2 size={15} color="var(--sienna)" strokeWidth={1.5} />
                  </div>
                  <span className="ex-card-head-title">Default Schemas</span>
                  <span className="ex-card-head-sub">— built-in templates per document type</span>
                </div>
                <div className="ex-card-body">
                  {Object.entries(defaults).map(([type, schema]) => {
                    const meta = DOC_META[type] || DOC_META.OTHER;
                    const Icon = meta.icon;
                    return (
                      <div key={type} className="ex-row" onClick={() => setSelectedDoc(selectedDoc === `def-${type}` ? null : `def-${type}`)}>
                        <div className="ex-row-icon" style={{ background: `${meta.color}12` }}>
                          <Icon size={15} color={meta.color} strokeWidth={1.5} />
                        </div>
                        <div className="ex-row-info">
                          <div className="ex-row-name">{schema.name}</div>
                          <div className="ex-row-meta"><span>{schema.fields?.length || 0} fields</span></div>
                        </div>
                        <span className="ex-badge" style={{ background: 'var(--parchment)', color: 'var(--muted)' }}>Default</span>
                        <button className="ex-btn ex-btn-outline" onClick={(e) => { e.stopPropagation(); openSchemaEditor(type); }}>
                          <Plus size={12} /> Customize
                        </button>
                        {selectedDoc === `def-${type}` ? <ChevronUp size={15} color="var(--muted)" /> : <ChevronDown size={15} color="var(--muted)" />}
                      </div>
                    );
                  })}
                  {Object.entries(defaults).map(([type, schema]) => (
                    selectedDoc === `def-${type}` && (
                      <div key={`detail-${type}`} className="ex-detail" style={{ borderTop: '1px solid var(--border-light)' }}>
                        <div className="ex-fields">
                          {schema.fields?.map(f => (
                            <div key={f.key} className="ex-field-item">
                              <span className="ex-field-label">{f.label} {f.required && <span style={{ color: 'var(--terracotta)' }}>*</span>}</span>
                              <span className="ex-field-value empty">{f.type}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )
                  ))}
                </div>
              </div>

              {/* Custom schemas */}
              <div className="ex-card">
                <div className="ex-card-head">
                  <div className="ex-card-head-icon" style={{ background: 'rgba(77,124,58,0.08)' }}>
                    <Database size={15} color="var(--forest)" strokeWidth={1.5} />
                  </div>
                  <span className="ex-card-head-title">Custom Schemas</span>
                  <span className="ex-card-head-sub">— your configured extraction templates</span>
                  <div style={{ marginLeft: 'auto' }}>
                    <button className="ex-btn ex-btn-primary" onClick={() => openSchemaEditor('ANNUAL_REPORT')}>
                      <Plus size={12} /> New Schema
                    </button>
                  </div>
                </div>
                <div className="ex-card-body">
                  {schemas.length === 0 ? (
                    <div className="ex-empty">
                      <div className="ex-empty-icon"><Settings2 size={22} /></div>
                      <h3>No Custom Schemas</h3>
                      <p>Customize a default schema or create one from scratch.</p>
                    </div>
                  ) : schemas.map(s => {
                    const meta = DOC_META[s.document_type] || DOC_META.OTHER;
                    const Icon = meta.icon;
                    const flds = s.fields || [];
                    return (
                      <div key={s.id}>
                        <div className="ex-row" onClick={() => setSelectedDoc(selectedDoc === s.id ? null : s.id)}>
                          <div className="ex-row-icon" style={{ background: `${meta.color}12` }}>
                            <Icon size={15} color={meta.color} strokeWidth={1.5} />
                          </div>
                          <div className="ex-row-info">
                            <div className="ex-row-name">{s.schema_name}</div>
                            <div className="ex-row-meta"><span>{flds.length} fields</span><span>•</span><span>{meta.label}</span></div>
                          </div>
                          <span className="ex-badge" style={{ background: 'rgba(160,82,45,0.1)', color: 'var(--sienna)' }}>Custom</span>
                          <div className="ex-actions" onClick={e => e.stopPropagation()}>
                            <button className="ex-btn ex-btn-danger" onClick={() => deleteSchema(s.id)}><Trash2 size={12} /></button>
                          </div>
                          {selectedDoc === s.id ? <ChevronUp size={15} color="var(--muted)" /> : <ChevronDown size={15} color="var(--muted)" />}
                        </div>
                        {selectedDoc === s.id && (
                          <div className="ex-detail" style={{ borderTop: '1px solid var(--border-light)' }}>
                            <div className="ex-fields">
                              {flds.map(f => (
                                <div key={f.key} className="ex-field-item">
                                  <span className="ex-field-label">{f.label} {f.required && <span style={{ color: 'var(--terracotta)' }}>*</span>}</span>
                                  <span className="ex-field-value empty">{f.type}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}

          {/* ═══════════════════ TAB 3 — EXTRACT ═══════════════════ */}
          {activeTab === 'extract' && (
            <div className="ex-card">
              <div className="ex-card-head">
                <div className="ex-card-head-icon" style={{ background: 'rgba(160,82,45,0.08)' }}>
                  <Database size={15} color="var(--sienna)" strokeWidth={1.5} />
                </div>
                <span className="ex-card-head-title">Data Extraction</span>
                <span className="ex-card-head-sub">— run extraction and review / edit mapped fields</span>
              </div>
              <div className="ex-card-body">
                {docs.length === 0 ? (
                  <div className="ex-empty">
                    <div className="ex-empty-icon"><Database size={22} /></div>
                    <h3>No Documents</h3>
                    <p>Upload and classify documents first.</p>
                  </div>
                ) : docs.map(doc => {
                  const meta = DOC_META[doc.effective_type] || DOC_META.OTHER;
                  const Icon = meta.icon;
                  const hasData = !!doc.extracted_fields;
                  const isExpanded = selectedDoc === `ext-${doc.file_id}`;
                  const isExtracting = extracting === doc.file_id;
                  const isEditingF = editingFields === doc.file_id;

                  // Matching custom schemas for this doc type
                  const matchingSchemas = schemas.filter(s => s.document_type === doc.effective_type);

                  return (
                    <div key={doc.file_id}>
                      <div className="ex-row" onClick={() => setSelectedDoc(isExpanded ? null : `ext-${doc.file_id}`)}>
                        <div className="ex-row-icon" style={{ background: `${meta.color}12` }}>
                          <Icon size={15} color={meta.color} strokeWidth={1.5} />
                        </div>
                        <div className="ex-row-info">
                          <div className="ex-row-name">{doc.filename}</div>
                          <div className="ex-row-meta">
                            <span>{meta.label}</span>
                            <span>•</span>
                            <span>{doc.parse_status}</span>
                          </div>
                        </div>
                        {hasData ? (
                          <span className="ex-badge" style={{ background: 'rgba(77,124,58,0.12)', color: '#4D7C3A' }}>Extracted</span>
                        ) : (
                          <span className="ex-badge" style={{ background: 'var(--parchment)', color: 'var(--muted)' }}>Not Extracted</span>
                        )}
                        <div className="ex-actions" onClick={e => e.stopPropagation()}>
                          {/* Run default extraction */}
                          <button className="ex-btn ex-btn-primary" disabled={isExtracting || doc.parse_status === 'PENDING'} onClick={() => runExtraction(doc.file_id)}>
                            {isExtracting ? <Loader2 size={12} className="ex-spin" /> : <Play size={12} />}
                            {hasData ? 'Re-extract' : 'Extract'}
                          </button>
                          {/* If there are custom schemas, show a dropdown-style button */}
                          {matchingSchemas.length > 0 && (
                            <select className="ex-select" defaultValue="" onChange={e => { if (e.target.value) runExtraction(doc.file_id, e.target.value); e.target.value = ''; }}>
                              <option value="" disabled>Custom Schema…</option>
                              {matchingSchemas.map(s => <option key={s.id} value={s.id}>{s.schema_name}</option>)}
                            </select>
                          )}
                        </div>
                        {isExpanded ? <ChevronUp size={15} color="var(--muted)" /> : <ChevronDown size={15} color="var(--muted)" />}
                      </div>

                      {/* Expanded detail */}
                      {isExpanded && hasData && (
                        <div className="ex-detail" style={{ borderTop: '1px solid var(--border-light)' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.7rem' }}>
                            <span className="ex-detail-title" style={{ margin: 0 }}>Extracted Fields</span>
                            <div className="ex-actions">
                              {isEditingF ? (
                                <>
                                  <button className="ex-btn ex-btn-primary" onClick={() => saveEditedFields(doc.file_id)}><Save size={12} /> Save</button>
                                  <button className="ex-btn ex-btn-ghost" onClick={() => setEditingFields(null)}><X size={12} /> Cancel</button>
                                </>
                              ) : (
                                <button className="ex-btn ex-btn-outline" onClick={() => { setEditingFields(doc.file_id); setEditFieldValues({ ...doc.extracted_fields }); }}>
                                  <Edit3 size={12} /> Edit Fields
                                </button>
                              )}
                            </div>
                          </div>
                          <div className="ex-fields">
                            {Object.entries(isEditingF ? editFieldValues : doc.extracted_fields).map(([key, val]) => (
                              <div key={key} className="ex-field-item">
                                <span className="ex-field-label">{key.replace(/_/g, ' ')}</span>
                                {isEditingF ? (
                                  <input className="ex-field-input" value={editFieldValues[key] ?? ''} onChange={e => setEditFieldValues(prev => ({ ...prev, [key]: e.target.value }))} />
                                ) : (
                                  <span className={`ex-field-value${val == null || val === '' ? ' empty' : ''}`}>
                                    {val != null && val !== '' ? String(val) : '—'}
                                  </span>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {isExpanded && !hasData && (
                        <div className="ex-detail" style={{ borderTop: '1px solid var(--border-light)', textAlign: 'center', padding: '1.5rem' }}>
                          <p style={{ color: 'var(--muted)', fontSize: '0.82rem' }}>
                            {doc.parse_status === 'PENDING' ? 'Document not yet parsed. Parse it first from the Ingestion page.' : 'Click "Extract" to map document data to the schema fields.'}
                          </p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

        </div>
      </div>

      {/* ═══════════ Next Step Navigation ═══════════ */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem', marginTop: '0.5rem' }}>
        <button className="ex-btn ex-btn-outline" onClick={() => navigate(`/application/${id}/research`)}>
          Next: External Intelligence →
        </button>
        <button className="ex-btn ex-btn-outline" onClick={() => navigate(`/application/${id}/analysis`)}>
          Skip to Analysis →
        </button>
      </div>

      {/* ═══════════════════ SCHEMA EDITOR MODAL ═══════════════════ */}
      {schemaEditorOpen && (
        <div className="ex-schema-overlay" onClick={() => setSchemaEditorOpen(false)}>
          <div className="ex-schema-modal" onClick={e => e.stopPropagation()}>
            <div className="ex-schema-modal-head">
              <Settings2 size={18} color="var(--sienna)" />
              <h2>Configure Extraction Schema</h2>
              <button className="ex-btn ex-btn-ghost" onClick={() => setSchemaEditorOpen(false)}><X size={14} /></button>
            </div>

            <div className="ex-schema-modal-body">
              <div className="ex-input-row">
                <label>Type</label>
                <select value={schemaEditorDocType} onChange={e => setSchemaEditorDocType(e.target.value)}>
                  {ALL_TYPES.map(t => <option key={t} value={t}>{DOC_META[t]?.label || t}</option>)}
                </select>
              </div>
              <div className="ex-input-row">
                <label>Name</label>
                <input value={schemaEditorName} onChange={e => setSchemaEditorName(e.target.value)} placeholder="Schema name" />
              </div>

              <div style={{ fontSize: '0.7rem', fontFamily: "'DM Mono', monospace", textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--muted)', marginTop: '0.4rem' }}>
                Fields ({schemaEditorFields.length})
              </div>

              {/* Column headers */}
              <div className="ex-schema-row" style={{ fontFamily: "'DM Mono', monospace", fontSize: '0.58rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--muted)', borderBottom: '2px solid var(--border)' }}>
                <span>Key</span><span>Label</span><span>Type</span><span>Req</span><span></span>
              </div>

              {schemaEditorFields.map((f, idx) => (
                <div key={idx} className="ex-schema-row">
                  <input className="ex-schema-input" value={f.key} onChange={e => updateSchemaField(idx, 'key', e.target.value)} placeholder="field_key" />
                  <input className="ex-schema-input" value={f.label} onChange={e => updateSchemaField(idx, 'label', e.target.value)} placeholder="Field Label" />
                  <select className="ex-schema-select" value={f.type} onChange={e => updateSchemaField(idx, 'type', e.target.value)}>
                    {FIELD_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                  <input type="checkbox" className="ex-schema-cb" checked={f.required} onChange={e => updateSchemaField(idx, 'required', e.target.checked)} />
                  <button className="ex-schema-rm" onClick={() => removeSchemaField(idx)}><Trash2 size={13} /></button>
                </div>
              ))}

              <button className="ex-btn ex-btn-outline" onClick={addSchemaField} style={{ alignSelf: 'flex-start' }}>
                <Plus size={12} /> Add Field
              </button>
            </div>

            <div className="ex-schema-modal-foot">
              <button className="ex-btn ex-btn-ghost" onClick={() => setSchemaEditorOpen(false)}>Cancel</button>
              <button className="ex-btn ex-btn-primary" onClick={saveSchema} disabled={savingSchema || !schemaEditorName.trim()}>
                {savingSchema ? <Loader2 size={12} className="ex-spin" /> : <Save size={12} />}
                Save Schema
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ExtractionMapping;
