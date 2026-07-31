"""SQLite schema and persistence utilities for structured ingestion."""

import json
import sqlite3
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from constants import (
    TABLE_COMPANIES,
    TABLE_FUNDAMENTAL_FACTS,
    TABLE_INDEX_CONSTITUENTS,
    TABLE_INGESTION_RUNS,
    TABLE_PRICE_BARS,
    TABLE_RAW_ARTIFACTS,
)
from ingestion.models import (
    CompanyRecord,
    FundamentalFactRecord,
    IndexConstituentRecord,
    PriceBarRecord,
    RawArtifactRecord,
)


def connect_database(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE_INGESTION_RUNS} (
            run_id TEXT PRIMARY KEY,
            mode TEXT NOT NULL,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            status TEXT NOT NULL,
            source_summary_json TEXT NOT NULL DEFAULT '{{}}',
            error_message TEXT
        );

        CREATE TABLE IF NOT EXISTS {TABLE_COMPANIES} (
            company_id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            sector TEXT,
            industry TEXT,
            cik TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS {TABLE_INDEX_CONSTITUENTS} (
            index_symbol TEXT NOT NULL,
            company_id TEXT NOT NULL,
            ticker TEXT NOT NULL,
            weight REAL,
            rank INTEGER,
            as_of_date TEXT NOT NULL,
            source TEXT NOT NULL,
            PRIMARY KEY (index_symbol, ticker, as_of_date),
            FOREIGN KEY (company_id) REFERENCES {TABLE_COMPANIES}(company_id)
        );

        CREATE TABLE IF NOT EXISTS {TABLE_PRICE_BARS} (
            ticker TEXT NOT NULL,
            date TEXT NOT NULL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            adj_close REAL,
            volume INTEGER,
            source TEXT NOT NULL,
            PRIMARY KEY (ticker, date, source)
        );

        CREATE TABLE IF NOT EXISTS {TABLE_FUNDAMENTAL_FACTS} (
            ticker TEXT NOT NULL,
            cik TEXT NOT NULL,
            taxonomy TEXT NOT NULL,
            concept TEXT NOT NULL,
            label TEXT,
            unit TEXT NOT NULL,
            value REAL NOT NULL,
            period_start TEXT,
            period_end TEXT NOT NULL,
            fiscal_year INTEGER,
            fiscal_period TEXT,
            form TEXT NOT NULL,
            filed_at TEXT,
            source TEXT NOT NULL,
            PRIMARY KEY (ticker, concept, unit, period_end, form, filed_at)
        );

        CREATE TABLE IF NOT EXISTS {TABLE_RAW_ARTIFACTS} (
            artifact_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            source TEXT NOT NULL,
            ticker TEXT,
            artifact_type TEXT NOT NULL,
            source_url TEXT,
            local_path TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            fetched_at TEXT NOT NULL,
            FOREIGN KEY (run_id) REFERENCES {TABLE_INGESTION_RUNS}(run_id)
        );
        """
    )
    connection.commit()


def start_ingestion_run(
    connection: sqlite3.Connection,
    *,
    run_id: str,
    mode: str,
) -> None:
    connection.execute(
        f"""
        INSERT INTO {TABLE_INGESTION_RUNS}
            (run_id, mode, started_at, status, source_summary_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (run_id, mode, datetime.now(UTC).isoformat(), "running", "{}"),
    )
    connection.commit()


def finish_ingestion_run(
    connection: sqlite3.Connection,
    *,
    run_id: str,
    status: str,
    source_summary: dict[str, int],
    error_message: str | None = None,
) -> None:
    connection.execute(
        f"""
        UPDATE {TABLE_INGESTION_RUNS}
        SET completed_at = ?, status = ?, source_summary_json = ?, error_message = ?
        WHERE run_id = ?
        """,
        (
            datetime.now(UTC).isoformat(),
            status,
            json.dumps(source_summary, sort_keys=True),
            error_message,
            run_id,
        ),
    )
    connection.commit()


def upsert_companies(
    connection: sqlite3.Connection,
    records: Sequence[CompanyRecord],
) -> None:
    now = datetime.now(UTC).isoformat()
    connection.executemany(
        f"""
        INSERT INTO {TABLE_COMPANIES}
            (
                company_id, ticker, name, sector, industry, cik, is_active,
                created_at, updated_at
            )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(company_id) DO UPDATE SET
            ticker = excluded.ticker,
            name = excluded.name,
            sector = excluded.sector,
            industry = excluded.industry,
            cik = excluded.cik,
            is_active = excluded.is_active,
            updated_at = excluded.updated_at
        """,
        [
            (
                record.company_id,
                record.ticker,
                record.name,
                record.sector,
                record.industry,
                record.cik,
                int(record.is_active),
                now,
                now,
            )
            for record in records
        ],
    )
    connection.commit()


def upsert_index_constituents(
    connection: sqlite3.Connection,
    records: Sequence[IndexConstituentRecord],
) -> None:
    connection.executemany(
        f"""
        INSERT INTO {TABLE_INDEX_CONSTITUENTS}
            (index_symbol, company_id, ticker, weight, rank, as_of_date, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(index_symbol, ticker, as_of_date) DO UPDATE SET
            company_id = excluded.company_id,
            weight = excluded.weight,
            rank = excluded.rank,
            source = excluded.source
        """,
        [
            (
                record.index_symbol,
                record.company_id,
                record.ticker,
                record.weight,
                record.rank,
                record.as_of_date.isoformat(),
                record.source,
            )
            for record in records
        ],
    )
    connection.commit()


def upsert_price_bars(
    connection: sqlite3.Connection,
    records: Sequence[PriceBarRecord],
) -> None:
    connection.executemany(
        f"""
        INSERT INTO {TABLE_PRICE_BARS}
            (ticker, date, open, high, low, close, adj_close, volume, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(ticker, date, source) DO UPDATE SET
            open = excluded.open,
            high = excluded.high,
            low = excluded.low,
            close = excluded.close,
            adj_close = excluded.adj_close,
            volume = excluded.volume
        """,
        [
            (
                record.ticker,
                record.date.isoformat(),
                record.open,
                record.high,
                record.low,
                record.close,
                record.adj_close,
                record.volume,
                record.source,
            )
            for record in records
        ],
    )
    connection.commit()


def upsert_fundamental_facts(
    connection: sqlite3.Connection,
    records: Sequence[FundamentalFactRecord],
) -> None:
    connection.executemany(
        f"""
        INSERT INTO {TABLE_FUNDAMENTAL_FACTS}
            (
                ticker, cik, taxonomy, concept, label, unit, value, period_start,
                period_end, fiscal_year, fiscal_period, form, filed_at, source
            )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(ticker, concept, unit, period_end, form, filed_at) DO UPDATE SET
            cik = excluded.cik,
            taxonomy = excluded.taxonomy,
            label = excluded.label,
            value = excluded.value,
            period_start = excluded.period_start,
            fiscal_year = excluded.fiscal_year,
            fiscal_period = excluded.fiscal_period,
            source = excluded.source
        """,
        [
            (
                record.ticker,
                record.cik,
                record.taxonomy,
                record.concept,
                record.label,
                record.unit,
                record.value,
                _date_or_none(record.period_start),
                record.period_end.isoformat(),
                record.fiscal_year,
                record.fiscal_period,
                record.form,
                _date_or_none(record.filed_at),
                record.source,
            )
            for record in records
        ],
    )
    connection.commit()


def insert_raw_artifacts(
    connection: sqlite3.Connection,
    records: Sequence[RawArtifactRecord],
) -> None:
    connection.executemany(
        f"""
        INSERT OR IGNORE INTO {TABLE_RAW_ARTIFACTS}
            (
                artifact_id, run_id, source, ticker, artifact_type, source_url,
                local_path, content_hash, fetched_at
            )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                record.artifact_id,
                record.run_id,
                record.source,
                record.ticker,
                record.artifact_type,
                record.source_url,
                record.local_path,
                record.content_hash,
                record.fetched_at.isoformat(),
            )
            for record in records
        ],
    )
    connection.commit()


def table_count(connection: sqlite3.Connection, table_name: str) -> int:
    row = connection.execute(f"SELECT COUNT(*) AS count FROM {table_name}").fetchone()
    return int(row["count"])


def _date_or_none(value: object) -> str | None:
    if value is None:
        return None
    return value.isoformat()
