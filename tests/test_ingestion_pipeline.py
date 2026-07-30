import sqlite3
import subprocess
import sys

from constants import (
    INGESTION_MODE_FIXTURE,
    TABLE_COMPANIES,
    TABLE_FUNDAMENTAL_FACTS,
    TABLE_INDEX_CONSTITUENTS,
    TABLE_INGESTION_RUNS,
    TABLE_PRICE_BARS,
    TABLE_RAW_ARTIFACTS,
)
from ingestion.pipeline import run_ingestion


def test_fixture_ingestion_normalizes_records_and_is_idempotent(tmp_path) -> None:
    db_path = tmp_path / "investment_data.sqlite"
    raw_data_dir = tmp_path / "raw"

    first = run_ingestion(
        mode=INGESTION_MODE_FIXTURE,
        db_path=db_path,
        raw_data_dir=raw_data_dir,
    )
    second = run_ingestion(
        mode=INGESTION_MODE_FIXTURE,
        db_path=db_path,
        raw_data_dir=raw_data_dir,
    )

    assert first.source_summary[TABLE_COMPANIES] == 2
    assert second.source_summary[TABLE_COMPANIES] == 2
    assert second.source_summary[TABLE_INDEX_CONSTITUENTS] == 2
    assert second.source_summary[TABLE_PRICE_BARS] == 4
    assert second.source_summary[TABLE_FUNDAMENTAL_FACTS] == 4

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    assert _count(connection, TABLE_INGESTION_RUNS) == 2
    assert _count(connection, TABLE_RAW_ARTIFACTS) == 8
    assert _company_weight(connection, "MSFT") == 4.21
    connection.close()


def test_ingest_script_runs_fixture_mode(tmp_path) -> None:
    db_path = tmp_path / "script.sqlite"
    raw_data_dir = tmp_path / "script_raw"

    result = subprocess.run(
        [
            sys.executable,
            "scripts/ingest_data.py",
            "--mode",
            INGESTION_MODE_FIXTURE,
            "--db-path",
            str(db_path),
            "--raw-data-dir",
            str(raw_data_dir),
            "--tickers",
            "MSFT",
        ],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Ingestion run completed" in result.stdout

    connection = sqlite3.connect(db_path)
    assert (
        connection.execute(f"SELECT COUNT(*) FROM {TABLE_COMPANIES}").fetchone()[0] == 1
    )
    assert (
        connection.execute(f"SELECT COUNT(*) FROM {TABLE_PRICE_BARS}").fetchone()[0]
        == 2
    )
    connection.close()


def _count(connection: sqlite3.Connection, table_name: str) -> int:
    return connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]


def _company_weight(connection: sqlite3.Connection, ticker: str) -> float:
    row = connection.execute(
        f"SELECT weight FROM {TABLE_INDEX_CONSTITUENTS} WHERE ticker = ?",
        (ticker,),
    ).fetchone()
    return row["weight"]
