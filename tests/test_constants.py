from constants import (
    DEFAULT_SQLITE_PATH,
    INGESTION_MODE_FIXTURE,
    INGESTION_MODE_LIVE,
    INGESTION_MODES,
    SEC_CONCEPT_REVENUE,
    TABLE_COMPANIES,
    TABLE_PRICE_BARS,
)


def test_ingestion_modes_are_centralized() -> None:
    assert INGESTION_MODE_FIXTURE in INGESTION_MODES
    assert INGESTION_MODE_LIVE in INGESTION_MODES


def test_table_and_concept_constants_are_available() -> None:
    assert TABLE_COMPANIES == "companies"
    assert TABLE_PRICE_BARS == "price_bars"
    assert SEC_CONCEPT_REVENUE == "Revenues"


def test_default_sqlite_path_lives_under_processed_data() -> None:
    assert DEFAULT_SQLITE_PATH.parts[-2:] == ("processed", "investment_data.sqlite")
