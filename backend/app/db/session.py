from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import os
from backend.app.db.models import Base


# Import settings
from backend.app.config import settings

# Create engine using centralized config
engine = create_engine(
    settings.get_database_url(),
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
    echo=settings.debug
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
