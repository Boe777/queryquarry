from datetime import date

from app.agent.prompts import build_sql_messages


def _messages(**kwargs: object) -> list[dict[str, str]]:
    base: dict[str, object] = {
        "question": "top customers",
        "schema_text": "Table: invoice",
        "today": date(2026, 8, 30),
    }
    base.update(kwargs)
    return build_sql_messages(**base)  # type: ignore[arg-type]


def test_puts_rules_in_a_system_message() -> None:
    messages = _messages()

    assert messages[0]["role"] == "system"
    assert "SELECT only" in messages[0]["content"]


def test_includes_question_and_schema() -> None:
    user = _messages()[1]["content"]

    assert "top customers" in user
    assert "Table: invoice" in user
    assert "2026-08-30" in user


def test_omits_retry_block_on_first_attempt() -> None:
    user = _messages()[1]["content"]

    assert "rejected" not in user


def test_includes_previous_attempt_and_errors_on_retry() -> None:
    user = _messages(
        previous_sql="select * from nowhere",
        errors=("unknown table: nowhere",),
    )[1]["content"]

    assert "select * from nowhere" in user
    assert "unknown table: nowhere" in user


def test_ignores_previous_sql_without_errors() -> None:
    user = _messages(previous_sql="select 1")[1]["content"]

    assert "rejected" not in user
