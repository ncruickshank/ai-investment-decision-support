from constants import (
    TABLE_COMPANIES,
    TABLE_FUNDAMENTAL_FACTS,
    TABLE_INDEX_CONSTITUENTS,
    TABLE_INGESTION_RUNS,
    TABLE_PRICE_BARS,
    TABLE_RAW_ARTIFACTS,
)
from ingestion.storage import connect_database, create_schema, table_count


def test_create_schema_adds_expected_tables(tmp_path) -> None:
    db_path = tmp_path / "investment_data.sqlite"
    connection = connect_database(db_path)

    create_schema(connection)

    table_names = {
        row["name"]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    }
    assert {
        TABLE_INGESTION_RUNS,
        TABLE_COMPANIES,
        TABLE_INDEX_CONSTITUENTS,
        TABLE_PRICE_BARS,
        TABLE_FUNDAMENTAL_FACTS,
        TABLE_RAW_ARTIFACTS,
    }.issubset(table_names)
    assert table_count(connection, TABLE_COMPANIES) == 0
    connection.close()
