from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import os
from backend.app.db.models import Base


# Handle Railway DATABASE_URL which uses postgresql:// instead of postgresql+psycopg://
def get_database_url():
    db_url = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:password@localhost:5435/mvp_db")
    # Convert postgresql:// to postgresql+psycopg:// for Railway compatibility
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return db_url


# Create engine
engine = create_engine(
    get_database_url(),
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False
)

# Create session factory
SessionLocal = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)


def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
