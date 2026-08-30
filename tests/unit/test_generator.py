from datetime import date
from typing import Any

from app.agent.nodes.generator import generate_sql


class _FakeClient:
    """Stands in for GroqClient and records what it was asked."""

    def __init__(self, reply: str) -> None:
        self.reply = reply
        self.messages: list[dict[str, str]] = []

    def complete(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        self.messages = messages
        return self.reply


def test_returns_cleaned_sql() -> None:
    client = _FakeClient("```sql\nselect 1 from invoice;\n```")

    result = generate_sql(
        question="anything",
        schema_text="Table: invoice",
        client=client,  # type: ignore[arg-type]
        today=date(2026, 8, 30),
    )

    assert result == "select 1 from invoice"


def test_passes_errors_through_to_the_prompt() -> None:
    client = _FakeClient("select 1")

    generate_sql(
        question="anything",
        schema_text="Table: invoice",
        client=client,  # type: ignore[arg-type]
        today=date(2026, 8, 30),
        previous_sql="select * from missing",
        errors=("unknown table: missing",),
    )

    user_message = client.messages[1]["content"]
    assert "unknown table: missing" in user_message
