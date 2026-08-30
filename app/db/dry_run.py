from sqlalchemy import text
from sqlalchemy.exc import DatabaseError

from app.db.engine import read_connection


def explain(sql: str) -> str | None:
    """Ask Postgres to plan the query without running it.

    Returns None when the query plans cleanly, or the database error message.
    """
    with read_connection() as conn:
        transaction = conn.begin()
        try:
            conn.execute(text(f"explain {sql}"))
        except DatabaseError as exc:
            return str(exc.orig).strip()
        finally:
            transaction.rollback()

    return None
