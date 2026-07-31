"""End-to-end structured ingestion orchestration."""

import json
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from config import ROOT_DIR
from constants import (
    DEFAULT_FIXTURE_END_DATE,
    DEFAULT_FIXTURE_START_DATE,
    DEFAULT_RAW_DATA_DIR,
    DEFAULT_SQLITE_PATH,
    INGESTION_MODE_FIXTURE,
    INGESTION_MODES,
    SOURCE_PINNED_UNIVERSE,
    SOURCE_SEC_EDGAR,
    SOURCE_YFINANCE,
    TABLE_COMPANIES,
    TABLE_FUNDAMENTAL_FACTS,
    TABLE_INDEX_CONSTITUENTS,
    TABLE_PRICE_BARS,
    TABLE_RAW_ARTIFACTS,
)
from ingestion.artifacts import write_raw_artifact
from ingestion.market_data import (
    fetch_yfinance_company_metadata,
    fetch_yfinance_history,
    normalize_price_rows,
    normalize_yfinance_company_metadata,
    normalize_yfinance_history_frame,
)
from ingestion.models import CompanyRecord, IndexConstituentRecord
from ingestion.sec import fetch_sec_company_facts, normalize_sec_company_facts
from ingestion.storage import (
    connect_database,
    create_schema,
    finish_ingestion_run,
    insert_raw_artifacts,
    start_ingestion_run,
    table_count,
    upsert_companies,
    upsert_fundamental_facts,
    upsert_index_constituents,
    upsert_price_bars,
)
from ingestion.universe import (
    load_pinned_top_10_universe,
    refresh_sp500_top_10_universe,
)

DEFAULT_FIXTURE_PATH = (
    ROOT_DIR / "tests" / "fixtures" / "ingestion" / "sample_ingestion.json"
)


@dataclass(frozen=True)
class IngestionResult:
    run_id: str
    db_path: Path
    source_summary: dict[str, int]


def load_fixture_payload(path: Path = DEFAULT_FIXTURE_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run_ingestion(
    *,
    mode: str = INGESTION_MODE_FIXTURE,
    db_path: Path = DEFAULT_SQLITE_PATH,
    raw_data_dir: Path = DEFAULT_RAW_DATA_DIR,
    fixture_path: Path = DEFAULT_FIXTURE_PATH,
    start_date: str = DEFAULT_FIXTURE_START_DATE,
    end_date: str | None = DEFAULT_FIXTURE_END_DATE,
    tickers: list[str] | None = None,
    refresh_universe: bool = False,
) -> IngestionResult:
    if mode not in INGESTION_MODES:
        raise ValueError(f"Unsupported ingestion mode: {mode}")

    run_id = str(uuid4())
    connection = connect_database(db_path)
    create_schema(connection)
    start_ingestion_run(connection, run_id=run_id, mode=mode)

    try:
        if mode == INGESTION_MODE_FIXTURE:
            summary = _run_fixture_ingestion(
                connection=connection,
                run_id=run_id,
                raw_data_dir=raw_data_dir,
                fixture_path=fixture_path,
                tickers=tickers,
            )
        else:
            summary = _run_live_ingestion(
                connection=connection,
                run_id=run_id,
                raw_data_dir=raw_data_dir,
                start_date=start_date,
                end_date=end_date,
                tickers=tickers,
                refresh_universe=refresh_universe,
            )
        finish_ingestion_run(
            connection,
            run_id=run_id,
            status="completed",
            source_summary=summary,
        )
        return IngestionResult(run_id=run_id, db_path=db_path, source_summary=summary)
    except Exception as exc:
        finish_ingestion_run(
            connection,
            run_id=run_id,
            status="failed",
            source_summary={},
            error_message=str(exc),
        )
        raise
    finally:
        connection.close()


def _run_fixture_ingestion(
    *,
    connection,
    run_id: str,
    raw_data_dir: Path,
    fixture_path: Path,
    tickers: list[str] | None,
) -> dict[str, int]:
    payload = load_fixture_payload(fixture_path)
    selected_tickers = {ticker.upper() for ticker in tickers} if tickers else None

    companies = [
        CompanyRecord(**row)
        for row in payload["companies"]
        if _include_ticker(row["ticker"], selected_tickers)
    ]
    constituents = [
        IndexConstituentRecord(**row)
        for row in payload["index_constituents"]
        if _include_ticker(row["ticker"], selected_tickers)
    ]
    price_rows = [
        row
        for row in payload["prices"]
        if _include_ticker(row["ticker"], selected_tickers)
    ]

    raw_artifacts = [
        write_raw_artifact(
            run_id=run_id,
            source=SOURCE_PINNED_UNIVERSE,
            artifact_type="fixture_universe",
            payload={"companies": [row.model_dump(mode="json") for row in companies]},
            raw_data_dir=raw_data_dir,
        ),
        write_raw_artifact(
            run_id=run_id,
            source=SOURCE_YFINANCE,
            artifact_type="fixture_prices",
            payload=price_rows,
            raw_data_dir=raw_data_dir,
        ),
    ]

    facts = []
    for company in companies:
        sec_payload = payload["sec_company_facts"].get(company.ticker)
        if not sec_payload or not company.cik:
            continue
        raw_artifacts.append(
            write_raw_artifact(
                run_id=run_id,
                source=SOURCE_SEC_EDGAR,
                artifact_type="fixture_company_facts",
                payload=sec_payload,
                ticker=company.ticker,
                raw_data_dir=raw_data_dir,
            )
        )
        facts.extend(
            normalize_sec_company_facts(company.ticker, company.cik, sec_payload)
        )

    upsert_companies(connection, companies)
    upsert_index_constituents(connection, constituents)
    upsert_price_bars(connection, normalize_price_rows(price_rows))
    upsert_fundamental_facts(connection, facts)
    insert_raw_artifacts(connection, raw_artifacts)

    return _summary(connection)


def _run_live_ingestion(
    *,
    connection,
    run_id: str,
    raw_data_dir: Path,
    start_date: str,
    end_date: str | None,
    tickers: list[str] | None,
    refresh_universe: bool,
) -> dict[str, int]:
    pinned_companies, constituents = load_pinned_top_10_universe()
    selected_tickers = {ticker.upper() for ticker in tickers} if tickers else None
    companies = [
        company
        for company in pinned_companies
        if _include_ticker(company.ticker, selected_tickers)
    ]
    if refresh_universe:
        refreshed = refresh_sp500_top_10_universe()
        constituents = [
            row for row in refreshed if _include_ticker(row.ticker, selected_tickers)
        ]
    else:
        constituents = [
            row for row in constituents if _include_ticker(row.ticker, selected_tickers)
        ]

    enriched_companies = []
    raw_artifacts = [
        write_raw_artifact(
            run_id=run_id,
            source=SOURCE_PINNED_UNIVERSE,
            artifact_type="pinned_universe",
            payload=[company.model_dump(mode="json") for company in companies],
            raw_data_dir=raw_data_dir,
        )
    ]

    for company in companies:
        metadata = fetch_yfinance_company_metadata(company.ticker)
        raw_artifacts.append(
            write_raw_artifact(
                run_id=run_id,
                source=SOURCE_YFINANCE,
                artifact_type="company_metadata",
                payload=metadata,
                ticker=company.ticker,
                raw_data_dir=raw_data_dir,
            )
        )
        enriched = normalize_yfinance_company_metadata({**metadata, "cik": company.cik})
        enriched_companies.append(enriched)

    price_frame = fetch_yfinance_history(
        [company.ticker for company in companies],
        start_date=start_date,
        end_date=end_date,
    )
    prices = normalize_yfinance_history_frame(price_frame)
    raw_artifacts.append(
        write_raw_artifact(
            run_id=run_id,
            source=SOURCE_YFINANCE,
            artifact_type="price_history",
            payload=[price.model_dump(mode="json") for price in prices],
            raw_data_dir=raw_data_dir,
        )
    )

    facts = []
    for company in enriched_companies:
        if not company.cik:
            continue
        payload = fetch_sec_company_facts(company.cik)
        raw_artifacts.append(
            write_raw_artifact(
                run_id=run_id,
                source=SOURCE_SEC_EDGAR,
                artifact_type="company_facts",
                payload=payload,
                ticker=company.ticker,
                raw_data_dir=raw_data_dir,
            )
        )
        facts.extend(normalize_sec_company_facts(company.ticker, company.cik, payload))

    upsert_companies(connection, enriched_companies)
    upsert_index_constituents(connection, constituents)
    upsert_price_bars(connection, prices)
    upsert_fundamental_facts(connection, facts)
    insert_raw_artifacts(connection, raw_artifacts)

    return _summary(connection)


def _include_ticker(ticker: str, selected_tickers: set[str] | None) -> bool:
    return selected_tickers is None or ticker.upper() in selected_tickers


def _summary(connection) -> dict[str, int]:
    return {
        TABLE_COMPANIES: table_count(connection, TABLE_COMPANIES),
        TABLE_INDEX_CONSTITUENTS: table_count(connection, TABLE_INDEX_CONSTITUENTS),
        TABLE_PRICE_BARS: table_count(connection, TABLE_PRICE_BARS),
        TABLE_FUNDAMENTAL_FACTS: table_count(connection, TABLE_FUNDAMENTAL_FACTS),
        TABLE_RAW_ARTIFACTS: table_count(connection, TABLE_RAW_ARTIFACTS),
    }
