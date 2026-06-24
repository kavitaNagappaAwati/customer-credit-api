"""
database.py
───────────
SQLAlchemy async-compatible engine, session factory, and the declarative base
that all ORM models inherit from.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# ── Engine ────────────────────────────────────────────────────────────────────
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,       # Detect stale connections before using them
    pool_recycle=3600,        # Recycle connections every hour
    pool_size=10,             # Keep up to 10 connections in the pool
    max_overflow=20,          # Allow 20 extra connections under load
    echo=settings.DEBUG,      # Log SQL statements in debug mode only
)

# ── Session factory ───────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# ── Declarative base ──────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# ── FastAPI dependency ─────────────────────────────────────────────────────────
def get_db():
    """
    Yield a database session and ensure it is closed after the request
    regardless of whether it succeeded or raised an exception.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
