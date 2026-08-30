from datetime import date

from app.agent.prompts import build_sql_messages
from app.agent.sql_extraction import extract_sql
from app.llm.client import GroqClient


def generate_sql(
    question: str,
    schema_text: str,
    client: GroqClient,
    today: date | None = None,
    previous_sql: str | None = None,
    errors: tuple[str, ...] = (),
) -> str:
    """Ask the model for one SQL statement and return it stripped of packaging."""
    messages = build_sql_messages(
        question=question,
        schema_text=schema_text,
        today=today or date.today(),
        previous_sql=previous_sql,
        errors=errors,
    )
    reply = client.complete(messages, temperature=0.0, max_tokens=800)
    return extract_sql(reply)
