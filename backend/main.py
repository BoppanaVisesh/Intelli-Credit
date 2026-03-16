import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from core.config import get_settings
from core.database import engine, Base
from api.routes import applications, ingestion, research, scoring, cam, due_diligence, fraud_detection, extraction, analysis
from seed_data import seed_demo_applications
from seed_pipeline import start_seed_pipeline_thread
import uvicorn


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created")
    settings = get_settings()
    if settings.ENABLE_DEMO_SEED:
        seed_demo_applications()
        start_seed_pipeline_thread()
    else:
        print("ℹ️ Demo seed disabled (ENABLE_DEMO_SEED=false)")
    yield
    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title="Intelli-Credit API",
    description="AI-Powered Corporate Credit Decisioning Engine",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(applications.router, prefix="/api/v1/applications", tags=["Applications"])
app.include_router(ingestion.router, prefix="/api/v1/ingestion", tags=["Data Ingestion"])
app.include_router(research.router, prefix="/api/v1/research", tags=["Research"])
app.include_router(scoring.router, prefix="/api/v1/scoring", tags=["Scoring"])
app.include_router(cam.router, prefix="/api/v1/cam", tags=["CAM"])
app.include_router(due_diligence.router, prefix="/api/v1/due-diligence", tags=["Due Diligence"])
app.include_router(fraud_detection.router, prefix="/api/v1/fraud", tags=["Fraud Detection"])
app.include_router(extraction.router, prefix="/api/v1/extraction", tags=["Extraction & Schema"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])


@app.get("/")
async def root():
    return {
        "message": "Intelli-Credit API",
        "status": "operational",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
