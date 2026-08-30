import pytest

from app.agent.sql_extraction import extract_sql


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("select 1", "select 1"),
        ("  select 1  ", "select 1"),
        ("select 1;", "select 1"),
        ("```sql\nselect 1\n```", "select 1"),
        ("```\nselect 1\n```", "select 1"),
        ("```SQL\nselect 1\n```", "select 1"),
        ("SQL: select 1", "select 1"),
        ("Query: select 1", "select 1"),
        ("```sql\nselect 1;\n```", "select 1"),
    ],
)
def test_strips_packaging(raw: str, expected: str) -> None:
    assert extract_sql(raw) == expected


def test_keeps_multiline_queries_intact() -> None:
    raw = "```sql\nselect a\nfrom t\nwhere b = 1\n```"

    assert extract_sql(raw) == "select a\nfrom t\nwhere b = 1"


def test_leaves_plain_text_alone() -> None:
    assert extract_sql("not sql") == "not sql"
