from collections.abc import Iterator

from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

from app.config import get_settings


def make_engine(url: str | None = None) -> Engine:
    url = url or get_settings().database_url
    # check_same_thread only applies to SQLite; PostgreSQL needs no extra args
    args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=args)


engine = make_engine()


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
