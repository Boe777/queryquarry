import pytest

from app.agent.nodes.generator import generate_sql
from app.agent.validation import validate_sql
from app.db.introspect import load_date_ranges, load_schema, render_schema
from app.llm.client import GroqClient


@pytest.mark.integration
def test_model_writes_a_query_that_passes_validation() -> None:
    schema = load_schema()
    ranges = load_date_ranges((("invoice", "invoice_date"),))
    schema_text = render_schema(schema, ranges)

    sql = generate_sql(
        question="How many invoices are there in total?",
        schema_text=schema_text,
        client=GroqClient(),
    )

    result = validate_sql(sql, schema)
    assert result.ok, f"validation failed: {result.errors}\nsql: {sql}"


@pytest.mark.integration
def test_model_respects_the_data_coverage_window() -> None:
    schema = load_schema()
    ranges = load_date_ranges((("invoice", "invoice_date"),))
    schema_text = render_schema(schema, ranges)

    sql = generate_sql(
        question="Which customers spent the most last month?",
        schema_text=schema_text,
        client=GroqClient(),
    )

    result = validate_sql(sql, schema)
    assert result.ok, f"validation failed: {result.errors}\nsql: {sql}"
    assert "2025" in sql, f"expected the query to target the data window, got: {sql}"
