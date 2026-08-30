from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from app.db.introspect import Schema

_ALLOWED_ROOTS = (exp.Select, exp.Union, exp.Intersect, exp.Except)

DEFAULT_ROW_LIMIT = 1000


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of checking one generated statement."""

    sql: str
    errors: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.errors


def validate_sql(
    sql: str,
    schema: Schema,
    row_limit: int = DEFAULT_ROW_LIMIT,
) -> ValidationResult:
    """Check generated SQL and return it with a row limit applied.

    The returned sql is only safe to run when errors is empty.
    """
    if not sql.strip():
        return ValidationResult(sql=sql, errors=("statement is empty",))

    try:
        statements = sqlglot.parse(sql, dialect="postgres")
    except ParseError as exc:
        return ValidationResult(sql=sql, errors=(f"could not parse: {exc}",))

    parsed = [stmt for stmt in statements if stmt is not None]

    if not parsed:
        return ValidationResult(sql=sql, errors=("statement is empty",))

    if len(parsed) > 1:
        return ValidationResult(sql=sql, errors=("only one statement is allowed",))

    tree = parsed[0]
    errors: list[str] = []

    if not isinstance(tree, _ALLOWED_ROOTS):
        kind = type(tree).__name__.upper()
        return ValidationResult(sql=sql, errors=(f"only read queries are allowed, got {kind}",))

    if tree.args.get("into") is not None:
        errors.append("SELECT INTO writes to a new table and is not allowed")

    errors.extend(_unknown_tables(tree, schema))

    if errors:
        return ValidationResult(sql=sql, errors=tuple(errors))

    limited = _apply_row_limit(tree, row_limit)
    return ValidationResult(sql=limited.sql(dialect="postgres", pretty=True), errors=())


def _unknown_tables(tree: exp.Expression, schema: Schema) -> list[str]:
    """Report table names that the live schema does not contain."""
    known = {table.name.lower() for table in schema.tables}
    cte_names = {cte.alias_or_name.lower() for cte in tree.find_all(exp.CTE)}

    unknown = sorted(
        {
            node.name.lower()
            for node in tree.find_all(exp.Table)
            if node.name and node.name.lower() not in known and node.name.lower() not in cte_names
        }
    )
    return [f"unknown table: {name}" for name in unknown]


def _apply_row_limit(tree: exp.Query, row_limit: int) -> exp.Query:
    """Add a LIMIT when the query has none, or tighten one that is too large."""
    existing = tree.args.get("limit")

    if existing is None:
        return tree.limit(row_limit)

    value = existing.expression
    if isinstance(value, exp.Literal) and value.is_int and int(value.name) > row_limit:
        return tree.limit(row_limit)

    return tree
