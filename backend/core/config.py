from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Intelli-Credit"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./intellicredit.db"
    
    # LLM Provider (gemini/ollama/groq)
    LLM_PROVIDER: str = "gemini"  # Default to free Gemini
    
    # API Keys (set via environment variables)
    OPENAI_API_KEY: str = ""  # Optional - Gemini is free alternative
    GEMINI_API_KEY: str = ""  # FREE: 1500 requests/day
    TAVILY_API_KEY: str = ""  # FREE: 1000 searches/month
    GROQ_API_KEY: str = ""    # Optional: for fast inference
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB
    UPLOAD_DIR: str = "./uploads"
    
    # ML Model
    MODEL_PATH: str = "./ml/models/xgboost_credit_model.pkl"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings():
    return Settings()
