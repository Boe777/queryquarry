from datetime import date

from app.db.introspect import Column, DateRange, ForeignKey, Schema, Table


def _album_table() -> Table:
    return Table(
        name="album",
        columns=(
            Column(name="album_id", data_type="integer", nullable=False),
            Column(name="title", data_type="character varying", nullable=False),
            Column(name="artist_id", data_type="integer", nullable=True),
        ),
        foreign_keys=(
            ForeignKey(
                column="artist_id",
                references_table="artist",
                references_column="artist_id",
            ),
        ),
    )


def test_lists_table_and_columns() -> None:
    from app.db.introspect import render_schema

    rendered = render_schema(Schema(tables=(_album_table(),)))

    assert "Table: album" in rendered
    assert "  album_id integer not null" in rendered
    assert "  artist_id integer null" in rendered


def test_shows_foreign_key_arrow() -> None:
    from app.db.introspect import render_schema

    rendered = render_schema(Schema(tables=(_album_table(),)))

    assert "  artist_id -> artist.artist_id" in rendered


def test_appends_data_coverage_when_given() -> None:
    from app.db.introspect import render_schema

    ranges = (
        DateRange(
            table="invoice",
            column="invoice_date",
            earliest=date(2021, 1, 1),
            latest=date(2025, 12, 22),
        ),
    )
    rendered = render_schema(Schema(tables=(_album_table(),)), ranges)

    assert "Data coverage:" in rendered
    assert "  invoice.invoice_date runs from 2021-01-01 to 2025-12-22" in rendered


def test_omits_data_coverage_when_empty() -> None:
    from app.db.introspect import render_schema

    rendered = render_schema(Schema(tables=(_album_table(),)))

    assert "Data coverage:" not in rendered
