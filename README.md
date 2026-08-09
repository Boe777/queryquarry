# queryquarry

You write a question in plain English. The agent reads the database schema,
writes SQL, checks that SQL before it ever runs, executes it, and explains
what came back.

Status: early development. Nothing is runnable yet beyond the project skeleton.

## Why another text-to-SQL project

Most demos prompt a model and run whatever comes back. This one treats generated
SQL as untrusted input. Every query is parsed into an abstract syntax tree,
checked against the live schema, dry-run through EXPLAIN, and only then executed.
The application connects with a role that holds SELECT and nothing else, so the
validator is the first line of defence rather than the only one.

## Stack

| Layer | Choice |
| --- | --- |
| Agent | LangGraph |
| Model | Llama 3.3 70B via Groq |
| Database | Neon Postgres |
| API | FastAPI |
| Interface | Streamlit |
| Charts | Plotly |
| Tooling | uv, ruff, mypy, pytest |

## Data

Chinook sample database, MIT licence.
Source: https://github.com/lerocha/chinook-database

Sales data runs from 2021-01-01 to 2025-12-22. Since that end date sits in the
past, relative phrases such as "last month" are resolved against the last month
present in the data, not against today. The agent states which period it used.

## Known limits

- English input only. The schema is in English and mixing languages measurably
  hurts column matching. Scoped out on purpose rather than half-supported.
- Read queries only. No INSERT, UPDATE, DELETE or DDL, enforced both in the
  validator and by database privileges.
- Single schema. Multi-database routing is not implemented.

## Local setup

Requires uv and Docker.

    uv sync
    cp .env.example .env

Fill in the two connection strings and a Groq key, then:

    uv run pytest
    uv run ruff check .
    uv run mypy app

## Licence

MIT