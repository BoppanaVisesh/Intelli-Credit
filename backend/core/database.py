from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from core.config import get_settings

settings = get_settings()


def _build_engine():
    """Create the database engine, with automatic fallback to SQLite when the
    primary DATABASE_URL (e.g. a Render PostgreSQL instance) is unreachable."""
    url = settings.DATABASE_URL

    # Render uses postgres:// but SQLAlchemy 2.x requires postgresql://
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    is_sqlite = "sqlite" in url
    connect_args = {"check_same_thread": False} if is_sqlite else {}

    try:
        eng = create_engine(url, connect_args=connect_args, pool_pre_ping=True)
        # Quick connectivity check for non-SQLite databases
        if not is_sqlite:
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
        return eng
    except Exception as e:
        if is_sqlite:
            raise  # SQLite failures are real, re-raise
        print(f"⚠️  Primary DB connection failed ({e}), falling back to SQLite")
        fallback = "sqlite:///./intellicredit.db"
        return create_engine(fallback, connect_args={"check_same_thread": False})


engine = _build_engine()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
