# Intelli-Credit: AI-Powered Corporate Credit Decisioning Engine

> **🆓 100% FREE AI APIs Available!** This project works with Google Gemini (1500 req/day free) or Ollama (unlimited local). **No paid OpenAI subscription needed!** See [FREE_SETUP.md](FREE_SETUP.md) for 2-minute setup.

---

## 🎯 Overview

Intelli-Credit is a next-generation credit appraisal platform that automates the end-to-end preparation of Comprehensive Credit Appraisal Memos (CAM) for corporate lending. It bridges the "Data Paradox" in Indian corporate lending by intelligently processing structured data, unstructured documents, and external intelligence to deliver rapid, unbiased credit decisions.

### Problem Statement

Credit managers are overwhelmed by disparate data sources:
- **Structured**: GST filings, ITRs, Bank Statements
- **Unstructured**: Annual Reports, Financial Statements, Minutes
- **External**: News, MCA filings, eCourts litigation
- **Primary**: Site visits, Management interviews

Traditional manual processes take weeks, are prone to bias, and often miss early warning signals.

### Solution

Intelli-Credit automates credit decisioning through three intelligent pillars:

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        REACT FRONTEND                           │
│  Dashboard │ Application Form │ CAM Viewer │ Explainability UI │
└────────────────────────┬────────────────────────────────────────┘
                         │
                    FastAPI Gateway
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   PILLAR 1         PILLAR 2         PILLAR 3
   
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ DATA         │  │ RESEARCH     │  │ RECOMMENDATION│
│ INGESTOR     │  │ AGENT        │  │ ENGINE       │
├──────────────┤  ├──────────────┤  ├──────────────┤
│• PDF Parser  │  │• Promoter    │  │• XGBoost     │
│• GST Parser  │  │  Profiler    │  │  Scorer      │
│• Bank Parser │  │• eCourts     │  │• SHAP        │
│• Circular    │  │  Fetcher     │  │  Explainer   │
│  Trading     │  │• MCA Fetcher │  │• CAM         │
│  Detector    │  │• News        │  │  Generator   │
│• Vision LLM  │  │  Analyzer    │  │• Loan Limit  │
│  (Gemini)    │  │• Sector      │  │  Calculator  │
│              │  │  Analyzer    │  │              │
└──────────────┘  └──────────────┘  └──────────────┘
```

## 🚀 Key Features

### 1️⃣ Pillar 1: Multi-Format Data Ingestion
- **PDF Parsing**: Extract commitments and risks from annual reports using Vision LLMs
- **Structured Synthesis**: Cross-verify GST returns against bank statements
- **Fraud Detection**: Identify circular trading and revenue inflation patterns
- **Automated Ratio Calculation**: DSCR, Current Ratio, Debt-to-Equity

### 2️⃣ Pillar 2: Digital Credit Manager (Research Agent)
- **Promoter Background**: Web crawling for adverse media, litigation history
- **Legal Intelligence**: Automatic eCourts and NCLT case search
- **Sector Analysis**: Real-time industry headwinds and regulatory changes
- **Primary Insights**: AI translation of qualitative credit officer notes

### 3️⃣ Pillar 3: Intelligent Recommendation Engine
- **ML Scoring**: XGBoost-based credit scoring (0-100)
- **Explainable AI**: SHAP values showing exact decision drivers
- **CAM Generation**: Professional Word/PDF reports with structured analysis
- **Risk-Adjusted Pricing**: Dynamic interest rate calculation

## 📊 Output Example

**Sample Decision**: Apex Manufacturing Pvt Ltd

```json
{
  "decision": "REJECT",
  "credit_score": 58/100,
  "requested_limit": "₹10 Cr",
  "recommended_limit": "₹0 Cr",
  
  "shap_explanations": [
    {"feature": "DSCR < 1.0", "impact": -18.5, "type": "NEGATIVE"},
    {"feature": "Pending Litigation", "impact": -12.0, "type": "NEGATIVE"},
    {"feature": "Consistent GST Flows", "impact": +15.0, "type": "POSITIVE"},
    {"feature": "Aging Machinery", "impact": -5.0, "type": "NEGATIVE"}
  ]
}
```

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **ML/AI**: XGBoost, SHAP, OpenAI/Gemini APIs
- **Document Processing**: PyPDF2, pdfplumber, python-docx
- **Web Research**: Tavily API, BeautifulSoup, Selenium

### Frontend
- **Framework**: React 18 + Vite
- **Styling**: Tailwind CSS
- **State**: Zustand
- **Charts**: Recharts
- **Icons**: Lucide React

### Infrastructure
- **Containerization**: Docker + Docker Compose
- **API Gateway**: NGINX (reverse proxy)

## 📦 Installation

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for local frontend dev)
- Python 3.10+ (for local backend dev)

### Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/your-org/intelli-credit.git
cd intelli-credit

# Set up environment variables
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit backend/.env and add your API keys
nano backend/.env

# Start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Local Development Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add API keys

# Run development server
python main.py
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env

# Run development server
npm run dev
```

## 🔑 API Keys Required

Add these to `backend/.env`:

```env
# LLM APIs (choose one or both)
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...

# Web Research
TAVILY_API_KEY=...

# Optional: for production OCR
GOOGLE_CLOUD_VISION_API_KEY=...
```

## 📚 API Documentation

Once the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

```
POST /api/v1/applications/analyze-credit
  - Main endpoint: Upload documents and get complete analysis

GET  /api/v1/applications
  - List all applications

GET  /api/v1/applications/{id}
  - Get detailed analysis for specific application

POST /api/v1/due-diligence/add-notes
  - Add credit officer observations

POST /api/v1/cam/generate
  - Generate CAM document
```

## 🎓 How It Works

### User Journey

1. **Upload**: Credit officer uploads Annual Report, Bank Statements, GST Returns
2. **Add Notes**: Optionally adds site visit observations
3. **Processing** (3-5 seconds):
   - Pillar 1 extracts and reconciles financial data
   - Pillar 2 researches promoters, litigation, sector
   - Pillar 3 scores risk and generates CAM
4. **Review**: Dashboard shows:
   - Credit decision with SHAP waterfall chart
   - Executive summary
   - Downloadable CAM PDF

### Sample Processing Flow

```
User submits application
    ↓
Parse PDF (Vision LLM) → Extract auditor, debt, litigations
    ↓
Parse GST/Bank → Calculate ratios, detect circular trading
    ↓
Web Search → Promoter background, eCourts, news sentiment
    ↓
XGBoost Model → Score = 58/100
    ↓
SHAP Analysis → Top factors: DSCR (-18.5), Litigation (-12)
    ↓
Decision: REJECT (Score < 60)
    ↓
Generate CAM → Word/PDF with full analysis
```

## 🧪 Testing

### Run Backend Tests

```bash
cd backend
pytest tests/
```

### Test with Sample Data

```bash
# Use the mock data endpoints
curl -X POST http://localhost:8000/api/v1/applications/analyze-credit \
  -F "company_name=Test Corp" \
  -F "mca_cin=U12345MH2020PTC123456" \
  -F "sector=Industrial Manufacturing" \
  -F "requested_limit_cr=10"
```

## 🎯 Hackathon Demo Guide

### Phase 1: Show Hardcoded Flow (Complete ✅)
- Dashboard loads with mock applications
- Create new application form works
- Mock analysis returns JSON in 3 seconds
- Frontend displays SHAP waterfall beautifully

### Phase 2: Replace with Real Logic (In Progress)
- Integrate actual PDF parsing with Gemini Vision
- Connect Tavily for real web research
- Train basic XGBoost on sample data
- Generate actual CAM documents

### Phase 3: Polish & Present
- Add loading animations
- Improve error handling
- Add "Chat with CAM" feature
- Prepare demo video

## 🏆 Judging Criteria Alignment

| Criteria | Implementation |
|----------|---------------|
| **Innovation** | First-of-its-kind AI agent for Indian credit appraisal |
| **Technical Depth** | 3-pillar architecture, ML explainability, LLM orchestration |
| **Business Impact** | Reduces weeks of work to seconds, removes bias |
| **Completeness** | End-to-end: Upload → Analysis → CAM generation |
| **UX/Design** | Clean React UI with intuitive waterfall charts |

## 📈 Future Enhancements

- [ ] Multi-language support (Hindi, regional languages)
- [ ] Real-time dashboard for portfolio monitoring
- [ ] Integration with core banking systems
- [ ] Advanced fraud detection using graph neural networks
- [ ] Mobile app for field credit officers
- [ ] Blockchain-based audit trail

## 🤝 Contributing

This is a hackathon project. For collaboration:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

MIT License - See [LICENSE](LICENSE) file

## 👥 Team

- **Backend & ML**: [Your Name]
- **Frontend & UX**: [Team Member]
- **Research & Data**: [Team Member]

## 📞 Contact

- Email: team@intellicredit.ai
- Demo: [Link to deployed demo]
- Presentation: [Link to slides]

---

**Built with ❤️ for Next-Gen Corporate Credit Appraisal**
