from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import Connection

from app.config import get_settings

_engine: Engine | None = None


def _to_psycopg3(url: str) -> str:
    """SQLAlchemy still defaults to psycopg2 for bare postgresql:// URLs."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def get_engine() -> Engine:
    """Return the shared engine, creating it on first use."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            _to_psycopg3(settings.database_url),
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=2,
            pool_recycle=300,
            connect_args={"connect_timeout": 10},
        )
    return _engine


@contextmanager
def read_connection() -> Iterator[Connection]:
    """Hand out a connection from the pool and return it afterwards."""
    with get_engine().connect() as conn:
        yield conn
