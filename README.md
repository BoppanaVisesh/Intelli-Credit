# Intelli-Credit

Corporate credit underwriting is still painfully manual. A credit officer has to collect borrower documents, reconcile numbers across filings, look for fraud signals, scan public intelligence, write a credit note, and then justify the final recommendation. That process is slow, inconsistent, and hard to scale.

Intelli-Credit compresses that workflow into a single system. It ingests borrower documents, extracts structured financial data, runs verification and fraud checks, pulls external intelligence, scores the borrower using an explainable credit model, and generates a CAM-style output that a lending team can actually review.

---

## Why This Matters

For SME and corporate lending teams, the bottleneck is rarely a lack of applicants. It is the time and judgment needed to separate a clean file from a risky one.

The pain points are familiar:

- financial data sits across PDFs, spreadsheets, and tax filings
- the same company story must be validated across bank statements, GST, ITR, and annual reports
- fraud patterns are often visible only when documents are compared against each other
- external red flags such as litigation, compliance issues, and adverse news are checked too late
- final decisions are difficult to standardize and even harder to explain

Intelli-Credit addresses that with a practical pipeline built around three pillars: ingestion and verification, external intelligence, and recommendation.

---

## What The Product Does

At a high level, Intelli-Credit helps a lender move from raw borrower data to a defendable lending recommendation.

### Core flow

1. Create a borrower application.
2. Upload key financial documents.
3. Parse and normalize the extracted data.
4. Compare filings to detect inconsistencies and fraud signals.
5. Pull external intelligence on the company, promoters, sector, and litigation.
6. Add primary due diligence notes from a credit officer.
7. Compute a credit score, decision, recommended limit, and pricing band.
8. Generate an explainable CAM-style output.

---

### What is already seeded

On backend startup, the system seeds three demo applications and runs them through the pipeline in the background to visualize easily how it wors and what it extracts:

- `DEMO-APEX-001`: healthier manufacturing borrower
- `DEMO-GREENFIELD-002`: logistics borrower with stronger fraud concerns
- `DEMO-ORION-003`: retail borrower with circular-trading style risk patterns

Each demo application is populated with five working document types:

- Annual Report
- Bank Statement
- GST Return
- ITR
- Balance Sheet

That means the app is usable immediately after startup without asking a reviewer to prepare data first.

---


If you need to demo this fast.

### 2-minute version

1. Start the app with `RUN_LOCAL.bat` or `docker-compose up --build`.
2. Open the dashboard and point out the three seeded demo borrowers.
3. Open `DEMO-APEX-001` to show a cleaner borrower journey.
4. Open the ingestion page and show the five working document categories.
5. Open extraction, fraud, research, and scoring to show this is a real pipeline, not a static UI.
6. End on the CAM page and download the output.

---

## Feature Set

### 1. Application Intake

- create a new borrowing application with company details, sector, CIN, requested limit, and lending context
- track applications through a multi-step workflow
- keep a clear application-level summary for downstream analysis

### 2. Document Ingestion

- upload files by document category from the UI
- support the current working categories used by the backend pipeline:
  - Bank Statement
  - GST Return
  - ITR
  - Annual Report
  - Balance Sheet
- auto-store uploaded files per application
- track parse status for each document

### 3. Parsing and Structured Extraction

- parse spreadsheets, PDFs, and JSON-based demo data
- route each uploaded file to the right parser/classifier flow
- extract key financial and compliance fields such as revenue, cash flow indicators, GST sales, tax return details, asset values, and borrower-level financial attributes
- review and approve document classifications in the extraction workflow
- manage extraction schemas and trigger structured extraction for reviewed documents

### 4. Fraud and Verification Layer

- cross-verify values across documents instead of trusting a single source
- compare bank behaviour with GST and reported business performance
- detect mismatch patterns that matter to a lender
- run circular trading analysis
- run an ML-backed fraud model on the extracted feature set

### 5. External Intelligence Layer

- promoter profiling
- eCourt / litigation checks
- MCA / company profile checks
- news analysis
- sector analysis

This turns the system from a document reader into a fuller underwriting assistant.

### 6. Due Diligence Layer

- capture credit officer notes from site visits, management interactions, and reference checks
- bring qualitative field observations into the same decision workflow as the financial data

### 7. Credit Decision Engine

- compute an explainable final credit score
- use a Five Cs style scoring structure
- output a lending recommendation such as approve, conditional approve, or reject
- estimate a recommended limit
- calculate a pricing / risk premium band
- generate reasoning that explains why the recommendation was reached

### 8. CAM and Analysis Output

- generate a CAM-style document for download
- surface pre-cognitive analysis outputs such as SWOT, triangulation, and recommendation summaries
- expose the rationale in a format that a banker, reviewer, or judge can follow

### 9. End-to-End Demo and Test Utilities

- one-click Windows runner with `RUN_LOCAL.bat`
- seeded applications and seeded pipeline processing
- end-to-end API pipeline test script
- test-data generation utilities for the included demo borrowers

---

## Product Approach

The design philosophy was simple: do not build a vague “AI for finance” shell. Build the exact steps a credit team actually performs and wire those steps into a single product.

### Approach principles

- start from the real underwriting workflow, not a model-first demo
- combine rule-based verification with ML signals instead of overclaiming pure AI judgment
- keep the output explainable so the recommendation can be defended
- support both structured data and messy real-world document inputs
- reduce demo friction with seeded borrowers and pre-run pipelines

### Why the hybrid approach matters

Credit decisioning is not just text generation. The useful part is the combination of:

- deterministic checks for document consistency
- structured financial extraction
- external intelligence gathering
- qualitative due diligence
- final recommendation logic with explainability

That is why the system mixes parsers, heuristics, graph checks, ML scoring, and LLM-generated narrative in specific places instead of using an LLM as the whole product.

---

## System Architecture

The application is split into a React frontend and a FastAPI backend, with the backend organized around three credit-analysis pillars.

```text
┌──────────────────────────────────────────────────────────────┐
│                         Frontend                             │
│  React + Vite + Tailwind + Zustand                          │
│  Dashboard | Intake | Ingestion | Extraction | Analysis     │
│  Research | Due Diligence | Fraud | Scoring | CAM Viewer    │
└──────────────────────────────┬───────────────────────────────┘
                               │
                               │ REST API
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                          │
│     Applications | Ingestion | Extraction | Analysis        │
│     Research | Due Diligence | Fraud | Scoring | CAM        │
└───────────────┬───────────────────────┬──────────────────────┘
                │                       │
                ▼                       ▼
      ┌──────────────────┐    ┌────────────────────────────┐
      │ Pillar 1         │    │ Pillar 2                  │
      │ Ingestion        │    │ External Research         │
      │ Parsing          │    │ Promoter / News / MCA     │
      │ Normalization    │    │ Litigation / Sector       │
      │ Cross-verify     │    └────────────────────────────┘
      │ Circular trading │
      └─────────┬────────┘
                │
                ▼
      ┌──────────────────────────────────────────────────────┐
      │ Pillar 3                                             │
      │ Credit Scoring | Loan Limit | Risk Premium | CAM     │
      │ Explainability | Recommendation                      │
      └──────────────────────────────────────────────────────┘
                │
                ▼
      ┌──────────────────────────────────────────────────────┐
      │ Data + Model Layer                                   │
      │ SQLite / PostgreSQL | uploaded docs | parsed data    │
      │ fraud model | generated reports                      │
      └──────────────────────────────────────────────────────┘
```

---

## Pillar Breakdown

### Pillar 1: Data Ingestion and Verification

Purpose: turn borrower documents into lender-usable structured evidence.

Major components:

- document classification
- annual report parser
- bank statement parser
- GST parser
- ITR parser
- data normalizer
- cross-verification engine
- circular trading detector

Outputs:

- parsed document data
- normalized financial facts
- verification mismatches
- fraud indicators

### Pillar 2: Secondary Research and Risk Signals

Purpose: pull intelligence that will never appear in the borrower’s uploaded documents.

Major components:

- promoter profiler
- eCourt fetcher
- MCA fetcher
- news analyzer
- sector analyzer
- web crawler

Outputs:

- promoter red flags
- litigation findings
- public-profile intelligence
- sector headwinds and contextual risk

### Pillar 3: Credit Recommendation

Purpose: convert all the evidence into a recommendation a credit committee can act on.

Major components:

- Five Cs scoring engine
- loan limit engine
- risk premium calculator
- explainability engine
- CAM generator
- recommendation engine

Outputs:

- final credit score
- decision band
- recommended exposure
- pricing guidance
- explainable CAM-style output

---

## Technical Approach By Layer

### Document processing

- PDFs handled through Python PDF tooling
- spreadsheet-based financial documents handled with `openpyxl` and `pandas`
- JSON fixtures used for repeatable demo inputs and tests

### AI usage

- Gemini is used where narrative generation or richer unstructured understanding makes sense
- LLM usage is wrapped behind a service layer instead of being mixed directly into route code
- the platform avoids making the LLM the source of truth for financial verification

### Fraud logic

- rule-based cross-verification catches mismatches that are easy to justify
- graph-based detection helps identify circular transaction patterns
- an ML model adds a second signal instead of replacing deterministic checks

### Recommendation logic

- final scoring uses a business-readable structure rather than a black-box score only
- recommendation is tied to score, risk, and exposure logic
- explainability is built into the pipeline rather than added as an afterthought

---

## Tech Stack

### Frontend

- React 18
- Vite
- Tailwind CSS
- React Router
- Zustand
- Recharts
- Lucide React
- Axios
- react-dropzone

### Backend

- FastAPI
- Uvicorn
- SQLAlchemy
- Pydantic
- Python multipart handling for uploads

### Parsing and data handling

- pandas
- openpyxl
- PyPDF2
- pdfplumber
- pypdf
- python-docx
- Pillow
- pdf2image
- pytesseract

### AI and ML

- Google Gemini
- OpenAI client support in dependencies
- scikit-learn
- XGBoost
- SHAP
- NumPy
- joblib

### Research and web intelligence

- requests
- BeautifulSoup4
- Selenium
- Tavily API integration

### Graph and analytics

- NetworkX
- matplotlib

### Infrastructure

- Docker
- Docker Compose
- NGINX
- SQLite for local simplicity
- PostgreSQL for containerized team/shared setup

---

## Backend API Surface

The FastAPI app exposes route groups for the full pipeline:

- `/api/v1/applications`
- `/api/v1/ingestion`
- `/api/v1/extraction`
- `/api/v1/analysis`
- `/api/v1/research`
- `/api/v1/due-diligence`
- `/api/v1/fraud`
- `/api/v1/scoring`
- `/api/v1/cam`

Useful local endpoints:

- `GET /` for API status
- `GET /health` for health check
- `GET /docs` for Swagger UI

### High-value endpoint map

| Method | Endpoint | Why it matters in demo |
|---|---|---|
| `POST` | `/api/v1/applications` | creates a new borrower application |
| `POST` | `/api/v1/ingestion/upload-documents` | uploads borrower documents into the pipeline |
| `POST` | `/api/v1/ingestion/parse-documents/{id}` | parses uploaded files into structured data |
| `GET` | `/api/v1/extraction/documents/{id}` | lists extracted documents for review |
| `POST` | `/api/v1/extraction/extract/{file_id}` | runs extraction against a reviewed document |
| `POST` | `/api/v1/research/trigger-research` | launches external intelligence collection |
| `POST` | `/api/v1/due-diligence/add-notes` | feeds qualitative field observations into the case |
| `POST` | `/api/v1/fraud/run-verification/{id}` | runs verification and fraud detection |
| `POST` | `/api/v1/scoring/calculate-score` | computes score, decision, and recommendation |
| `POST` | `/api/v1/analysis/run/{id}` | runs deeper secondary analysis and triangulation |
| `POST` | `/api/v1/cam/generate` | generates CAM output for review/download |

---

## Running The Project

### Option 1: Windows one-click run

If you just want the project running quickly on Windows:

```bat
RUN_LOCAL.bat
```

That script:

- installs backend dependencies
- starts the FastAPI server
- installs frontend dependencies
- starts the Vite dev server
- opens the app in the browser

### Option 2: Local development

#### Prerequisites

- Python 3.10+
- Node.js 18+
- npm
- Gemini API key
- Tavily API key

#### Backend setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python main.py
```

Backend runs on:

- `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`

Default backend environment notes:

- local development uses SQLite by default
- demo applications are seeded automatically if the database is empty
- the seed pipeline attempts to process the demo applications on startup

#### Frontend setup

```bash
cd frontend
npm install
copy .env.example .env
npm run dev
```

Frontend runs on:

- `http://localhost:3000`

The frontend dev server proxies `/api` requests to `http://localhost:8000`.

### Option 3: Docker Compose

```bash
copy .env.example .env
docker-compose up --build
```

Containerized services:

- frontend on `http://localhost:3000`
- backend on `http://localhost:8000`
- nginx on `http://localhost:80`
- PostgreSQL on `localhost:5432`

The compose setup uses PostgreSQL and passes API keys through environment variables.

---

## Environment Variables

### Root `.env` for Docker Compose

```env
OPENAI_API_KEY=
GEMINI_API_KEY=
TAVILY_API_KEY=
POSTGRES_PASSWORD=intellicredit123
```

### Backend `.env`

Important keys used by local development:

```env
GEMINI_API_KEY=your_gemini_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
DATABASE_URL=sqlite:///./intellicredit.db
DEBUG=True
LLM_PROVIDER=gemini
```

### Frontend `.env`

```env
VITE_API_URL=http://localhost:8000/api/v1
```

---

## Demo Data and Seeded Flow

One of the stronger parts of this repo is that it is demo-friendly out of the box.

### Seed behaviour

- if the database is empty, three demo applications are inserted automatically
- a background seed pipeline uploads five documents per demo application
- the same pipeline runs parsing, extraction review, fraud checks, research, due diligence, scoring, analysis, and CAM generation.

### Full pipeline test

```bash
cd backend
python run_full_test.py
```

This script exercises the product across 11 steps, including:

1. application creation
2. document upload
3. document parsing
4. extraction review
5. schema CRUD and extraction
6. research
7. due diligence
8. fraud detection
9. credit scoring
10. pre-cognitive analysis
11. CAM generation and download

### E2E API test

```bash
cd backend
python run_e2e_test.py
```

---

Intelli-Credit is a practical underwriting co-pilot for corporate lending teams. The real value is not that it “uses AI”; it is that it reduces the time required to move from raw borrower evidence to a defendable lending view.

That is the problem this project is trying to solve.
