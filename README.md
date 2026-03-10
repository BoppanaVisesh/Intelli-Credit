# Intelli-Credit: AI-Powered Corporate Credit Decisioning Engine

## Overview

Intelli-Credit automates end-to-end preparation of Credit Appraisal Memos (CAM) for corporate lending. It processes structured filings (GST, Bank Statements), unstructured documents (Annual Reports), and external intelligence (news, litigation, MCA) to deliver scored credit decisions with explainable reasoning — in seconds instead of weeks.

---

## Architecture & Workflow

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          REACT + TAILWIND FRONTEND                       │
│  Dashboard │ New Application │ Data Ingestion │ Research Agent           │
│  Due Diligence │ Fraud Detection │ Credit Scoring │ CAM Viewer          │
└──────────────────────────┬───────────────────────────────────────────────┘
                           │  REST API (JSON)
                    ┌──────┴──────┐
                    │   FastAPI   │ ← Uvicorn ASGI server
                    │   Gateway   │ ← 7 API route modules
                    └──────┬──────┘
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
  ┌────┴─────┐       ┌────┴─────┐       ┌────┴─────┐
  │ PILLAR 1 │       │ PILLAR 2 │       │ PILLAR 3 │
  │ Data     │       │ External │       │ Credit   │
  │ Ingestor │       │ Research │       │ Decision │
  └────┬─────┘       └────┬─────┘       └────┬─────┘
       │                   │                   │
       ▼                   ▼                   ▼
  ┌──────────┐      ┌──────────┐      ┌───────────────┐
  │PDF Parser│      │Promoter  │      │Five Cs Scorer │
  │GST Parser│      │ Profiler │      │  (Rule-based) │
  │Bank Stmt │      │eCourt    │      │Loan Limit     │
  │ Parser   │      │ Fetcher  │      │  Engine       │
  │Annual Rpt│      │MCA       │      │Interest Rate  │
  │ Parser   │      │ Fetcher  │      │  Calculator   │
  │ITR Parser│      │News      │      │Explainability │
  │Document  │      │ Analyzer │      │  Engine       │
  │Classifier│      │Sector    │      │CAM Generator  │
  │          │      │ Analyzer │      │  (python-docx)│
  └────┬─────┘      └────┬─────┘      └───────┬───────┘
       │                   │                   │
       ▼                   ▼                   ▼
  ┌──────────┐      ┌──────────┐      ┌───────────────┐
  │Data      │      │Tavily    │      │Gemini LLM     │
  │Normalizer│      │Web Search│      │ (narrative     │
  │Cross-    │      │API       │      │  generation)   │
  │Verify    │      │          │      │               │
  │Engine    │      │          │      │RandomForest   │
  │Circular  │      │          │      │ Fraud Model   │
  │Trading   │      │          │      │ (.pkl)        │
  │Detector  │      │          │      │               │
  └──────────┘      └──────────┘      └───────────────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           ▼
                    ┌──────────────┐
                    │   SQLite DB  │
                    │ (auto-created│
                    │  on startup) │
                    └──────────────┘
```

---

## Workflow — Step by Step

A credit officer processes a loan application in **6 stages**:

### Stage 1: Create Application
Create a new application with company name, CIN, sector, and requested loan amount. This generates an Application ID (e.g. `APP-2026-41806`).

**Route:** `POST /api/v1/applications`

### Stage 2: Document Ingestion (Pillar 1)
Upload documents — Annual Report (PDF), Bank Statements (XLSX), GST Returns (XLSX). The system:
1. **Classifies** each document automatically (`document_classifier.py`)
2. **Parses** using the appropriate parser:
   - `annual_report_parser.py` — extracts revenue, debt, equity, auditor remarks via **Gemini Vision LLM**
   - `bank_statement_parser.py` — reads inflows, outflows, bounced cheques, overdraft instances
   - `gst_parser.py` — reads GSTR-1 and GSTR-3B sales figures
3. **Normalizes** all data into a unified format (`data_normalizer.py`)
4. **Cross-verifies** GST vs Bank vs Annual Report figures using a 14-rule engine (`cross_verification_engine.py`)
5. **Detects circular trading** patterns using NetworkX graph analysis (`circular_trading_detector.py`)

**Routes:** `POST /api/v1/ingestion/upload-documents` → `POST /api/v1/ingestion/parse-documents/{id}`

### Stage 3: External Research (Pillar 2)
Triggers 5 parallel research engines powered by **Tavily Web Search API**:
1. **Promoter Profiler** — searches for adverse news about company directors
2. **eCourt Fetcher** — finds pending litigation and NCLT cases
3. **MCA Fetcher** — pulls company registration and compliance data
4. **News Analyzer** — sentiment analysis on recent company news
5. **Sector Analyzer** — industry headwinds, macro and regulatory risks

Each engine returns findings with a sentiment rating and severity penalty.

**Route:** `POST /api/v1/research/trigger-research`

### Stage 4: Due Diligence (Primary Intelligence)
Credit officers add qualitative observations from site visits, management meetings, or external reference checks. The **Gemini LLM** summarizes these notes, assigns severity levels, and calculates score adjustments.

**Route:** `POST /api/v1/due-diligence/add-notes`

### Stage 5: Fraud Detection & Credit Scoring (Cross-Layer + Pillar 3)

**Fraud Detection** runs:
- Data Normalizer → Cross-Verification Engine (14 rules) → Circular Trading Detector (NetworkX)
- **RandomForest ML Model** (pre-trained, saved as `fraud_model.pkl`) — classifies fraud probability from extracted features

**Route:** `POST /api/v1/fraud/run-verification/{id}`

**Credit Scoring** runs the full pipeline:
1. Normalize → Cross-verify → compute fraud score
2. **Five Cs of Credit** scoring (`credit_scorer_fixed.py`):

   | Factor | Weight | What it measures |
   |--------|--------|------------------|
   | Character | 20% | Litigation, promoter reputation, circular trading risk |
   | Capacity | 30% | DSCR, GST-Bank variance, cash flow adequacy |
   | Capital | 20% | Debt-to-Equity ratio, net worth |
   | Collateral | 20% | Fixed assets, LTV ratio, collateral coverage |
   | Conditions | 10% | Sector risk, macro environment, adverse news |

   Sub-scores (0–100 each) are weighted into a **Final Credit Score (0–100)**.

3. **Decision logic:**
   - Score >= 80 → **APPROVE** (100% of requested limit)
   - Score 70–79 → **CONDITIONAL APPROVE** (75%)
   - Score 60–69 → **CONDITIONAL APPROVE** (50%)
   - Score < 60 → **REJECT** (0%)

4. **Loan Limit Engine** (`loan_limit_engine.py`):
   ```
   recommended_loan = min(revenue × 0.25, operating_cash_flow × 4, collateral × 0.7) × risk_multiplier
   ```

5. **Interest Rate Calculator** (`risk_premium_calculator.py`):

   | Score Range | Interest Rate | Category |
   |-------------|--------------|----------|
   | >= 80 | 10.0% | Prime |
   | 70–79 | 11.5% | Standard |
   | 60–69 | 13.0% | Sub-Prime |
   | < 60 | Rejected | — |

   Plus micro-adjustments for DSCR, sector risk, and litigation.

6. **Explainability Engine** (`explainability.py`):
   Generates human-readable decision reasons (positive/negative) with impact weights, plus a narrative paragraph summarizing the verdict.

**Route:** `POST /api/v1/scoring/calculate-score?application_id={id}`

### Stage 6: CAM Generation
Generates a professional **10-section Credit Appraisal Memo** as a Word document (`.docx`) using `python-docx`:

1. Executive Summary (LLM-generated via **Gemini**)
2. Company Profile
3. Industry Analysis
4. Financial Analysis
5. Bank Statement Analysis
6. GST Compliance
7. Litigation Check
8. Five Cs Evaluation
9. Risk Assessment
10. Loan Recommendation

The Gemini LLM writes a formal executive summary narrative. The document is available for download.

**Routes:** `POST /api/v1/cam/generate` → `GET /api/v1/cam/{id}/download`

---

## Tech Stack

### Backend (Python)
| Component | Technology |
|-----------|-----------|
| Framework | FastAPI + Uvicorn |
| Database | SQLAlchemy + SQLite |
| LLM | Google Gemini 2.5 Flash (`google-generativeai`) |
| ML Model | scikit-learn RandomForestClassifier (fraud detection) |
| Graph Analysis | NetworkX (circular trading detection) |
| Document Parsing | PyPDF2, pdfplumber, openpyxl, pandas |
| CAM Generation | python-docx (Word documents) |
| Web Research | Tavily API via `requests` |
| Web Scraping | BeautifulSoup4, Selenium |

### Frontend (JavaScript)
| Component | Technology |
|-----------|-----------|
| Framework | React 18 + Vite |
| Styling | Tailwind CSS |
| State Management | Zustand |
| Charts | Recharts |
| Icons | Lucide React |
| HTTP Client | Fetch API |
| File Upload | react-dropzone |

### Infrastructure
| Component | Technology |
|-----------|-----------|
| Containerization | Docker + Docker Compose |
| Reverse Proxy | NGINX |
| Dev Server (BE) | Uvicorn with hot reload |
| Dev Server (FE) | Vite dev server |

---

## Project Structure

```
Intelli-Credit/
├── backend/
│   ├── main.py                          # FastAPI app entry point
│   ├── requirements.txt                 # Python dependencies
│   ├── Dockerfile
│   ├── api/
│   │   ├── routes/
│   │   │   ├── applications.py          # CRUD for loan applications
│   │   │   ├── ingestion.py             # Document upload & parsing
│   │   │   ├── research.py              # Tavily-powered research
│   │   │   ├── due_diligence.py         # Credit officer notes + LLM
│   │   │   ├── fraud_detection.py       # Cross-verify + ML fraud
│   │   │   ├── scoring.py               # Full scoring pipeline
│   │   │   └── cam.py                   # CAM generation & download
│   │   └── dependencies.py
│   ├── core/
│   │   ├── config.py                    # Environment config
│   │   └── database.py                  # SQLAlchemy engine + session
│   ├── models/                          # SQLAlchemy ORM models
│   │   ├── application.py
│   │   ├── uploaded_document.py
│   │   ├── research_result.py
│   │   └── due_diligence_note.py
│   ├── pillar1_ingestor/                # Document parsing & verification
│   │   ├── pdf_parser.py
│   │   ├── annual_report_parser.py      # Gemini Vision LLM parsing
│   │   ├── bank_statement_parser.py
│   │   ├── gst_parser.py
│   │   ├── itr_parser.py
│   │   ├── document_classifier.py
│   │   ├── data_normalizer.py           # Unified data format
│   │   ├── cross_verification_engine.py # 14-rule fraud detection
│   │   └── circular_trading_detector.py # NetworkX graph analysis
│   ├── pillar2_research/                # External intelligence
│   │   ├── promoter_profiler.py
│   │   ├── ecourt_fetcher.py
│   │   ├── mca_fetcher.py
│   │   ├── news_analyzer.py
│   │   ├── sector_analyzer.py
│   │   └── web_crawler.py
│   ├── pillar3_recommendation/          # Credit decision engine
│   │   ├── credit_scorer_fixed.py       # Five Cs model (weighted)
│   │   ├── loan_limit_engine.py         # 3-method loan calculation
│   │   ├── risk_premium_calculator.py   # Interest rate bands
│   │   ├── explainability.py            # Reason generator + narrative
│   │   └── cam_generator.py             # 10-section Word document
│   ├── ml/
│   │   ├── fraud_model.py               # RandomForest train/predict
│   │   └── models/
│   │       └── fraud_model.pkl          # Pre-trained model (committed)
│   ├── services/
│   │   ├── llm_service.py               # Gemini LLM wrapper
│   │   └── orchestration_service.py     # Full pipeline orchestrator
│   ├── schemas/
│   │   └── application.py               # Pydantic request/response
│   └── test_data/                       # Sample data (3 company profiles)
│       ├── Annual_Report_*.json
│       ├── Bank_Statement_*.xlsx
│       └── GST_Returns_*.xlsx
├── frontend/
│   ├── src/
│   │   ├── App.jsx                      # Router + route definitions
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── NewApplication.jsx
│   │   │   ├── ApplicationDetail.jsx    # 6-step pipeline tracker
│   │   │   ├── DataIngestion.jsx
│   │   │   ├── ResearchAgent.jsx
│   │   │   ├── DueDiligencePortal.jsx
│   │   │   ├── FraudDetection.jsx
│   │   │   ├── ScoringResult.jsx        # Five Cs + loan + interest rate
│   │   │   └── CAMViewer.jsx            # Generate + preview + download
│   │   ├── components/layout/
│   │   │   ├── Header.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   └── Layout.jsx
│   │   ├── store/                       # Zustand state stores
│   │   └── utils/
│   │       ├── api.js                   # All API calls
│   │       ├── constants.js
│   │       └── formatters.js
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── Dockerfile
├── infra/
│   └── nginx.conf                       # Reverse proxy config
├── docker-compose.yml
├── RUN_LOCAL.bat                         # Windows one-click launcher
├── .gitignore
└── README.md
```

---

## Setup & Installation

### Prerequisites
- **Python 3.10+**
- **Node.js 18+**
- **API Keys:** Google Gemini API key (free tier: 1500 req/day), Tavily API key

### 1. Clone & Configure

```bash
git clone <repo-url>
cd Intelli-Credit

# Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Edit `backend/.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

pip install -r requirements.txt
python main.py
```

Server starts at **http://localhost:8000**. API docs at **http://localhost:8000/docs**.

The SQLite database and tables are created automatically on first startup (local dev). When running with Docker, PostgreSQL is used instead — see Docker section below. The fraud detection ML model (`fraud_model.pkl`) is pre-trained and included in the repo — no training needed.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend starts at **http://localhost:5173**.

### 4. One-Click (Windows)

```bash
RUN_LOCAL.bat
```

### 5. Docker (Recommended for Team Testing)

Docker Compose includes a **PostgreSQL database** so all teammates share the same data.

```bash
# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys (GEMINI_API_KEY, TAVILY_API_KEY)

# Start everything (DB + Backend + Frontend + Nginx)
docker-compose up --build

# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# Database: postgresql://intellicredit:intellicredit123@localhost:5432/intellicredit
```

To reset the shared database:
```bash
docker-compose down -v   # removes DB volume
docker-compose up --build
```

> **Local dev without Docker** still uses SQLite by default — no setup needed.
> To point local dev at the shared PostgreSQL, add this to `backend/.env`:
> ```
> DATABASE_URL=postgresql://intellicredit:intellicredit123@localhost:5432/intellicredit
> ```

---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/v1/applications` | Create new loan application |
| `GET` | `/api/v1/applications` | List all applications |
| `GET` | `/api/v1/applications/{id}/summary` | Application summary |
| `POST` | `/api/v1/ingestion/upload-documents` | Upload documents (multipart) |
| `POST` | `/api/v1/ingestion/parse-documents/{id}` | Parse uploaded documents |
| `GET` | `/api/v1/ingestion/documents/{id}` | Get parsed document data |
| `POST` | `/api/v1/research/trigger-research` | Run 5 research engines |
| `GET` | `/api/v1/research/{id}/results` | Get research findings |
| `POST` | `/api/v1/due-diligence/add-notes` | Add credit officer notes |
| `GET` | `/api/v1/due-diligence/{id}/notes` | Get due diligence notes |
| `POST` | `/api/v1/fraud/run-verification/{id}` | Run fraud detection |
| `GET` | `/api/v1/fraud/{id}/results` | Get fraud results |
| `POST` | `/api/v1/scoring/calculate-score` | Run full credit scoring |
| `POST` | `/api/v1/cam/generate` | Generate CAM document |
| `GET` | `/api/v1/cam/{id}/download` | Download CAM (.docx) |
| `GET` | `/api/v1/cam/{id}/preview` | Preview CAM (JSON) |

---

## Sample Output

**Scoring Response** for a high-risk application:

```json
{
  "final_credit_score": 37,
  "decision": "REJECT",
  "risk_grade": "B",
  "sub_scores": {
    "character":  { "score": 10, "weight": 0.20 },
    "capacity":   { "score": 25, "weight": 0.30 },
    "capital":    { "score": 95, "weight": 0.20 },
    "collateral": { "score": 50, "weight": 0.20 },
    "conditions": { "score": 85, "weight": 0.10 }
  },
  "loan_recommendation": {
    "recommended_limit_cr": 0.0,
    "methodology": "min(Revenue×0.25, CashFlow×4, Collateral×0.7) × risk_adj"
  },
  "interest_rate": {
    "base_rate": 9.5,
    "final_interest_rate": null,
    "rate_category": "Rejected"
  },
  "decision_reasons": [
    { "text": "Circular trading patterns detected", "impact": "NEGATIVE", "weight": 3 },
    { "text": "GST-Bank mismatch 100%", "impact": "NEGATIVE", "weight": 2 },
    { "text": "Conservative leverage (D/E 1.00)", "impact": "POSITIVE", "weight": 2 }
  ],
  "narrative": "With a credit score of 37/100 the application is REJECTED due to significant risk factors..."
}
```

---

## Key Design Decisions

- **Rule-based Five Cs** over ML scoring — more transparent, auditable, and aligns with how credit committees actually evaluate loans.
- **Pre-trained fraud model committed to repo** — teammates clone and run immediately, no training step needed. Model auto-retrains only if `.pkl` is deleted.
- **Gemini LLM for narratives** — writes formal executive summaries for CAM documents in banking language. Falls back gracefully if API is unavailable.
- **python-docx for CAM** — generates proper Word documents that credit officers can edit, vs PDF which is read-only.
- **SQLite for dev** — zero-config database, auto-created on startup. Switch to PostgreSQL for production via `DATABASE_URL` env var.

---
