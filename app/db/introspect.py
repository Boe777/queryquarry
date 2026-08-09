from dataclasses import dataclass, field
from datetime import date, datetime

from sqlalchemy import text

from app.db.engine import read_connection


@dataclass(frozen=True)
class Column:
    name: str
    data_type: str
    nullable: bool


@dataclass(frozen=True)
class ForeignKey:
    column: str
    references_table: str
    references_column: str


@dataclass(frozen=True)
class Table:
    name: str
    columns: tuple[Column, ...]
    foreign_keys: tuple[ForeignKey, ...] = ()


@dataclass(frozen=True)
class DateRange:
    table: str
    column: str
    earliest: date
    latest: date


@dataclass(frozen=True)
class Schema:
    tables: tuple[Table, ...]
    date_ranges: tuple[DateRange, ...] = field(default=())


_COLUMNS_QUERY = text("""
    select table_name, column_name, data_type, is_nullable
    from information_schema.columns
    where table_schema = 'public'
    order by table_name, ordinal_position
""")

_FOREIGN_KEYS_QUERY = text("""
    select
        src.relname     as table_name,
        src_col.attname as column_name,
        tgt.relname     as foreign_table_name,
        tgt_col.attname as foreign_column_name
    from pg_constraint c
    join pg_namespace ns on ns.oid = c.connamespace
    join pg_class src on src.oid = c.conrelid
    join pg_class tgt on tgt.oid = c.confrelid
    cross join lateral unnest(c.conkey, c.confkey) as u(src_attnum, tgt_attnum)
    join pg_attribute src_col
        on src_col.attrelid = c.conrelid and src_col.attnum = u.src_attnum
    join pg_attribute tgt_col
        on tgt_col.attrelid = c.confrelid and tgt_col.attnum = u.tgt_attnum
    where c.contype = 'f' and ns.nspname = 'public'
    order by src.relname, src_col.attname
""")


def load_schema() -> Schema:
    """Read table, column and foreign key metadata from the live database."""
    with read_connection() as conn:
        column_rows = conn.execute(_COLUMNS_QUERY).all()
        fk_rows = conn.execute(_FOREIGN_KEYS_QUERY).all()

    columns_by_table: dict[str, list[Column]] = {}
    for table_name, column_name, data_type, is_nullable in column_rows:
        columns_by_table.setdefault(table_name, []).append(
            Column(name=column_name, data_type=data_type, nullable=is_nullable == "YES")
        )

    fks_by_table: dict[str, list[ForeignKey]] = {}
    for table_name, column_name, ref_table, ref_column in fk_rows:
        fks_by_table.setdefault(table_name, []).append(
            ForeignKey(
                column=column_name,
                references_table=ref_table,
                references_column=ref_column,
            )
        )

    tables = tuple(
        Table(
            name=name,
            columns=tuple(cols),
            foreign_keys=tuple(fks_by_table.get(name, [])),
        )
        for name, cols in sorted(columns_by_table.items())
    )
    return Schema(tables=tables)


def load_date_ranges(
    table_column_pairs: tuple[tuple[str, str], ...],
) -> tuple[DateRange, ...]:
    """Find the earliest and latest value for each given date column.

    Identifiers cannot be bound as query parameters, so table and column names
    are written straight into the SQL text. Every name is checked against the
    live schema first, which means nothing reaches the query string that the
    database did not already report as existing.
    """
    schema = load_schema()
    known: dict[str, set[str]] = {
        table.name: {column.name for column in table.columns} for table in schema.tables
    }

    ranges: list[DateRange] = []
    with read_connection() as conn:
        for table_name, column_name in table_column_pairs:
            if column_name not in known.get(table_name, set()):
                raise ValueError(f"no such column: {table_name}.{column_name}")

            query = text(f'select min("{column_name}"), max("{column_name}") from "{table_name}"')
            earliest, latest = conn.execute(query).one()

            if earliest is None or latest is None:
                continue

            ranges.append(
                DateRange(
                    table=table_name,
                    column=column_name,
                    earliest=_as_date(earliest),
                    latest=_as_date(latest),
                )
            )

    return tuple(ranges)


def _as_date(value: date | datetime) -> date:
    return value.date() if isinstance(value, datetime) else value


def render_schema(schema: Schema, date_ranges: tuple[DateRange, ...] = ()) -> str:
    """Turn schema objects into the plain text block that goes into the prompt."""
    blocks: list[str] = []

    for table in schema.tables:
        lines = [f"Table: {table.name}"]

        for column in table.columns:
            nullability = "null" if column.nullable else "not null"
            lines.append(f"  {column.name} {column.data_type} {nullability}")

        for fk in table.foreign_keys:
            lines.append(f"  {fk.column} -> {fk.references_table}.{fk.references_column}")

        blocks.append("\n".join(lines))

    if date_ranges:
        lines = ["Data coverage:"]
        for dr in date_ranges:
            lines.append(
                f"  {dr.table}.{dr.column} runs from "
                f"{dr.earliest.isoformat()} to {dr.latest.isoformat()}"
            )
        blocks.append("\n".join(lines))

    return "\n\n".join(blocks)
