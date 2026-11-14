from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings


class Base(DeclarativeBase):
    pass


def build_engine(database_url: str | None = None):
    url = database_url or settings.database_url
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)

    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
    elif url.startswith("postgresql"):
        # Supabase's transaction pooler (port 6543) breaks psycopg prepared statements
        connect_args = {"prepare_threshold": None}
    else:
        connect_args = {}
    poolclass = NullPool if url.startswith("postgresql") else None

    kwargs = {"connect_args": connect_args, "future": True}
    if poolclass:
        kwargs["poolclass"] = poolclass

    return create_engine(url, **kwargs)


engine = build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()
