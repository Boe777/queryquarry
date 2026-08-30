from datetime import date

_SYSTEM = """You write PostgreSQL queries. You are given a database schema and a
question. Reply with one SQL statement and nothing else.

Rules:
- SELECT only. Never write INSERT, UPDATE, DELETE, or any DDL.
- One statement. No semicolon-separated extras.
- Use only tables and columns that appear in the schema below.
- Qualify columns with table aliases when more than one table is involved.
- Prefer explicit JOIN syntax over comma-separated FROM lists.
- Do not wrap the query in markdown fences or add commentary.
- When the question implies a ranking or a top-N, add ORDER BY and LIMIT.

Date handling:
- The data has a fixed coverage window shown under "Data coverage".
- Resolve relative phrases such as "last month" or "this year" against the
  latest date in that window, not against today.
- Use half-open ranges: col >= start AND col < next_start. Never use BETWEEN
  on a timestamp column.
"""


def build_sql_messages(
    question: str,
    schema_text: str,
    today: date,
    previous_sql: str | None = None,
    errors: tuple[str, ...] = (),
) -> list[dict[str, str]]:
    """Assemble the chat messages that ask the model for one SQL statement."""
    parts = [
        f"Today's date is {today.isoformat()}.",
        "",
        "Schema:",
        schema_text,
        "",
        f"Question: {question}",
    ]

    if previous_sql and errors:
        parts.extend(
            [
                "",
                "Your previous attempt was rejected:",
                previous_sql,
                "",
                "Problems found:",
                *(f"- {message}" for message in errors),
                "",
                "Write a corrected query.",
            ]
        )

    return [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": "\n".join(parts)},
    ]
