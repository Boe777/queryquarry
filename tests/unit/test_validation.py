import pytest

from app.agent.validation import DEFAULT_ROW_LIMIT, validate_sql
from app.db.introspect import Column, Schema, Table


def _schema() -> Schema:
    return Schema(
        tables=(
            Table(
                name="invoice",
                columns=(
                    Column(name="invoice_id", data_type="integer", nullable=False),
                    Column(name="customer_id", data_type="integer", nullable=False),
                    Column(name="total", data_type="numeric", nullable=False),
                ),
            ),
            Table(
                name="customer",
                columns=(
                    Column(name="customer_id", data_type="integer", nullable=False),
                    Column(name="first_name", data_type="character varying", nullable=False),
                ),
            ),
        )
    )


def _check(sql: str) -> object:
    return validate_sql(sql, _schema())


def test_accepts_a_plain_select() -> None:
    result = _check("select customer_id from invoice")

    assert result.ok
    assert "invoice" in result.sql


def test_accepts_a_join_between_known_tables() -> None:
    sql = """
        select c.first_name, sum(i.total)
        from invoice i
        join customer c on c.customer_id = i.customer_id
        group by c.first_name
    """

    assert _check(sql).ok


def test_accepts_a_cte() -> None:
    sql = """
        with recent as (select * from invoice)
        select count(*) from recent
    """

    assert _check(sql).ok


@pytest.mark.parametrize(
    "sql",
    [
        "delete from invoice",
        "update invoice set total = 0",
        "insert into invoice (total) values (1)",
        "drop table invoice",
        "truncate invoice",
        "alter table invoice add column x int",
        "create table stuff (id int)",
        "grant all on invoice to public",
    ],
)
def test_rejects_writes_and_ddl(sql: str) -> None:
    result = _check(sql)

    assert not result.ok
    assert any("read queries" in message for message in result.errors)


def test_rejects_a_second_statement() -> None:
    result = _check("select 1 from invoice; drop table invoice")

    assert not result.ok
    assert any("one statement" in message for message in result.errors)


def test_rejects_select_into() -> None:
    result = _check("select * into copied from invoice")

    assert not result.ok


def test_rejects_hallucinated_table() -> None:
    result = _check("select * from sales_summary")

    assert not result.ok
    assert any("unknown table: sales_summary" in message for message in result.errors)


def test_reports_every_unknown_table() -> None:
    result = _check("select * from orders join shipments on true")

    assert len(result.errors) == 2


def test_rejects_unparseable_text() -> None:
    result = _check("this is not sql at all !!!")

    assert not result.ok


def test_rejects_empty_input() -> None:
    assert not _check("   ").ok


def test_adds_a_limit_when_missing() -> None:
    result = _check("select customer_id from invoice")

    assert f"LIMIT {DEFAULT_ROW_LIMIT}" in result.sql.upper()


def test_keeps_a_smaller_limit() -> None:
    result = _check("select customer_id from invoice limit 5")

    assert "LIMIT 5" in result.sql.upper()


def test_tightens_an_oversized_limit() -> None:
    result = _check("select customer_id from invoice limit 500000")

    assert f"LIMIT {DEFAULT_ROW_LIMIT}" in result.sql.upper()
    assert "500000" not in result.sql
