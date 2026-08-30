import pytest

from app.db.dry_run import explain


@pytest.mark.integration
def test_valid_query_plans_cleanly() -> None:
    assert explain("select invoice_id from invoice") is None


@pytest.mark.integration
def test_unknown_column_is_reported() -> None:
    error = explain("select no_such_column from invoice")

    assert error is not None
    assert "no_such_column" in error


@pytest.mark.integration
def test_ambiguous_column_is_reported() -> None:
    sql = "select customer_id from invoice join customer on true"
    error = explain(sql)

    assert error is not None
    assert "ambiguous" in error.lower()
