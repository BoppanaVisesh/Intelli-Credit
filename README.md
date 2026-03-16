# Intelli-Credit : FinIntel

Corporate credit underwriting is still painfully manual. A credit officer has to collect borrower documents, reconcile numbers across filings, look for fraud signals, scan public intelligence, write a credit note, and then justify the final recommendation. That process is slow, inconsistent, and hard to scale.

FinIntel compresses that workflow into a single system. It ingests borrower documents, extracts structured financial data, runs verification and fraud checks, pulls external intelligence, scores the borrower using an explainable credit model, and generates a CAM-style output that a lending team can actually review.

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

On backend startup, the system seeds seven applications and runs them through the pipeline in the background so the app is usable immediately without any manual data preparation:

- `DEMO-APEX-001`: healthier manufacturing borrower
- `DEMO-GREENFIELD-002`: logistics borrower with stronger fraud concerns
- `DEMO-ORION-003`: retail borrower with circular-trading style risk patterns
- `DEMO-KINARA-004`: Kinara annual-report walkthrough from `backend/downloads/kinara_capital/`
- `DEMO-TATA-005`: Tata annual-report walkthrough from `backend/downloads/tata_capital/`
- `DEMO-MONEYBOXX-006`: Moneyboxx public-disclosure walkthrough from `backend/downloads/moneyboxx/`
- `DEMO-VIVRITI-007`: Vivriti annual-report walkthrough from `backend/downloads/vivriti/`

---


If you need to demo this fast.

### 2-minute version

1. Start the app with `RUN_LOCAL.bat` or `docker-compose up --build`.
2. Open the dashboard and point out the seven seeded borrowers.
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
- Loan Limit = min(
    Revenue × 0.25,
    Operating Cash Flow × 4,
    Collateral Value × 0.7
) × Risk Multiplier
  
### 7. Credit Decision Engine

- compute an explainable final credit score
- use a Five Cs style scoring structure
- output a lending recommendation such as approve, conditional approve, or reject
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

<table>
<tr>
<td><img src="https://github.com/user-attachments/assets/b525ec16-6404-415c-ace5-2e9a1ad16ceb" width="450"/></td>
<td><img src="https://github.com/user-attachments/assets/b6f7d83b-e65d-4cec-a6b5-19c7e05d7a85" width="450"/></td>
</tr>
<tr>
<td><img src="https://github.com/user-attachments/assets/da2a0429-67cc-48a6-8d36-eee5bb477d96" width="450"/></td>
<td><img src="https://github.com/user-attachments/assets/89bd99cb-4caf-40a8-b5e8-fb0bf7145e23" width="450"/></td>
</tr>
</table>

---

## System Architecture

The application is split into a React frontend and a FastAPI backend, with the backend organized around three credit-analysis pillars.


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

- 14-rule verification engine covering:
    - GST sales vs. bank inflows variance
    - GSTR-1 vs. GSTR-3B consistency
    - ITR revenue vs. annual report revenue
    - Bank inflows vs. annual report revenue
    - Cash flow stability (monthly variability)
    - Bounced cheque rate and overdraft patterns
    - Debt-to-equity sanity check
    - Related party transaction exposure
    - Contingent liabilities assessment
    - Auditor opinion check (qualified/adverse)
    - Purchase-to-sales ratio (round-tripping signal)
    - Net cash retention percentage
    - graph-based detection helps identify circular transaction patterns
    - an ML model adds a second signal instead of replacing deterministic checks
---

## Tech Stack
| Category                        | Technologies                                                                                       |
| ------------------------------- | -------------------------------------------------------------------------------------------------- |
| **Frontend**                    | React 18, Vite, Tailwind CSS, React Router, Zustand, Recharts, Lucide React, Axios, react-dropzone |
| **Backend**                     | FastAPI, Uvicorn, SQLAlchemy, Pydantic, Python multipart uploads                                   |
| **Parsing & Data Handling**     | pandas, openpyxl, PyPDF2, pdfplumber, pypdf, python-docx, Pillow, pdf2image, pytesseract           |
| **AI / ML**                     | Google Gemini, OpenAI Client, scikit-learn, XGBoost, SHAP, NumPy, joblib                           |
| **Research & Web Intelligence** | requests, BeautifulSoup4, Selenium, Tavily API                                                     |
| **Graph & Analytics**           | NetworkX, matplotlib                                                                               |
| **Infrastructure**              | Docker, Docker Compose, NGINX, SQLite, PostgreSQL                                                  |

---

## Backend API Surface

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

### Option 4: Cloud Deployment (Render + Vercel)

Recommended cloud path:

- Deploy backend (`backend/`) as a Python Web Service on Render.
- Deploy frontend (`frontend/`) as a Vite app on Vercel.
- Use Render PostgreSQL and set `DATABASE_URL` in backend environment variables.
- Set frontend env `VITE_API_URL` to your Render backend URL + `/api/v1`.

Important for Render backend compatibility:

- `backend/runtime.txt` pins Python to `3.10.14`
- `backend/.python-version` pins Python to `3.10.14`

---

## Environment Variables

### Root `.env` for Docker Compose

```env
OPENAI_API_KEY=
GEMINI_API_KEY=
TAVILY_API_KEY=
POSTGRES_PASSWORD=intellicredit123
```

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
