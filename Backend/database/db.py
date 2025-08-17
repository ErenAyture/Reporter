# app/db.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase,sessionmaker, Session

from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator
from .models import metadata
# from fastapi import Depends
# from .models import metadata   # ← put the snippet you showed in app/tables.py
DATABASE_URL = "postgresql+asyncpg://postgres:ankara_123@localhost:5432/reporter"
SYNC_URL  = "postgresql+psycopg2://postgres:ankara_123@localhost:5432/reporter"

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

sync_engine = create_engine(SYNC_URL, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(bind=sync_engine)

class Base(DeclarativeBase):
    metadata = metadata  
# re-use the MetaData object that holds your Table definitions
class NotFoundError(Exception):
    pass

async def get_db() -> AsyncSession:          # FastAPI dependency
    async with async_session() as session:
        yield session

def get_sync_db() -> Session:
    """
    Usage:

        with get_sync_session() as db:
            ...  # normal ORM ops
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ────────────────────────────────
# sync – for Celery workers, cron jobs, etc.
# ────────────────────────────────
@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Preferred pattern for *sync* code.

    Example:
        with session_scope() as db:
            db.query(...)

    The block is automatically committed, or rolled back on error.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ────────────────────────────────
# async – for FastAPI HTTP handlers, websockets, etc.
# ────────────────────────────────
@asynccontextmanager
async def async_session_scope() -> AsyncGenerator[AsyncSession, None]:
    """
    Preferred pattern for *async* code (e.g. FastAPI dependencies).

    Example:

        async with async_session_scope() as db:
            await db.execute(...)
    """
    async with async_session() as db:
        try:
            yield db
            await db.commit()
        except Exception:
            await db.rollback()
            raise