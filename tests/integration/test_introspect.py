from datetime import date

import pytest

from app.db.introspect import load_date_ranges, load_schema


@pytest.mark.integration
def test_finds_all_chinook_tables() -> None:
    schema = load_schema()
    names = {table.name for table in schema.tables}
    assert len(names) == 11
    assert "invoice" in names
    assert "invoice_line" in names


@pytest.mark.integration
def test_invoice_has_customer_foreign_key() -> None:
    schema = load_schema()
    invoice = next(t for t in schema.tables if t.name == "invoice")
    targets = {fk.references_table for fk in invoice.foreign_keys}
    assert "customer" in targets


@pytest.mark.integration
def test_invoice_date_range_matches_loaded_data() -> None:
    ranges = load_date_ranges((("invoice", "invoice_date"),))
    assert len(ranges) == 1
    assert ranges[0].earliest == date(2021, 1, 1)
    assert ranges[0].latest == date(2025, 12, 22)


@pytest.mark.integration
def test_unknown_column_is_rejected() -> None:
    with pytest.raises(ValueError, match="no such column"):
        load_date_ranges((("invoice", "invoice_date; drop table invoice"),))
