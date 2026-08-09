import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from app.db.engine import read_connection


@pytest.mark.integration
def test_reads_expected_invoice_count() -> None:
    with read_connection() as conn:
        count = conn.execute(text("select count(*) from invoice")).scalar_one()
    assert count == 412


@pytest.mark.integration
def test_role_app_ro_validator() -> None:
    with read_connection() as conn, pytest.raises(ProgrammingError, match="permission denied"):
        conn.execute(text("delete from invoice where invoice_id = 1"))
