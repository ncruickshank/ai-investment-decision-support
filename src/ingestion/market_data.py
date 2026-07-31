"""Market-data source adapters and normalizers."""

from datetime import date
from typing import Any

import pandas as pd

from constants import SOURCE_YFINANCE
from ingestion.models import CompanyRecord, PriceBarRecord
from ingestion.universe import company_id_for_ticker


def fetch_yfinance_history(
    tickers: list[str],
    start_date: str,
    end_date: str | None = None,
) -> pd.DataFrame:
    import yfinance as yf

    return yf.download(
        tickers=tickers,
        start=start_date,
        end=end_date,
        auto_adjust=False,
        progress=False,
        group_by="ticker",
    )


def fetch_yfinance_company_metadata(ticker: str) -> dict[str, Any]:
    import yfinance as yf

    info = yf.Ticker(ticker).get_info()
    return {
        "ticker": ticker,
        "name": info.get("longName") or info.get("shortName") or ticker,
        "sector": info.get("sector"),
        "industry": info.get("industry"),
    }


def normalize_yfinance_company_metadata(raw: dict[str, Any]) -> CompanyRecord:
    ticker = str(raw["ticker"]).upper()
    return CompanyRecord(
        company_id=company_id_for_ticker(ticker),
        ticker=ticker,
        name=str(raw.get("name") or ticker),
        sector=raw.get("sector"),
        industry=raw.get("industry"),
        cik=raw.get("cik"),
    )


def normalize_price_rows(raw_rows: list[dict[str, Any]]) -> list[PriceBarRecord]:
    records = []
    for row in raw_rows:
        records.append(
            PriceBarRecord(
                ticker=str(row["ticker"]).upper(),
                date=date.fromisoformat(str(row["date"])),
                open=_optional_float(row.get("open")),
                high=_optional_float(row.get("high")),
                low=_optional_float(row.get("low")),
                close=_optional_float(row.get("close")),
                adj_close=_optional_float(row.get("adj_close")),
                volume=_optional_int(row.get("volume")),
                source=str(row.get("source") or SOURCE_YFINANCE),
            )
        )
    return records


def normalize_yfinance_history_frame(frame: pd.DataFrame) -> list[PriceBarRecord]:
    records: list[PriceBarRecord] = []
    if frame.empty:
        return records

    if isinstance(frame.columns, pd.MultiIndex):
        for ticker in frame.columns.get_level_values(0).unique():
            ticker_frame = frame[ticker].reset_index()
            records.extend(_normalize_single_ticker_frame(str(ticker), ticker_frame))
        return records

    ticker = str(frame.attrs.get("ticker", "UNKNOWN"))
    return _normalize_single_ticker_frame(ticker, frame.reset_index())


def _normalize_single_ticker_frame(
    ticker: str,
    frame: pd.DataFrame,
) -> list[PriceBarRecord]:
    records: list[PriceBarRecord] = []
    for row in frame.to_dict(orient="records"):
        raw_date = row.get("Date") or row.get("date")
        if pd.isna(raw_date):
            continue
        price_date = pd.Timestamp(raw_date).date()
        records.append(
            PriceBarRecord(
                ticker=ticker.upper(),
                date=price_date,
                open=_optional_float(row.get("Open")),
                high=_optional_float(row.get("High")),
                low=_optional_float(row.get("Low")),
                close=_optional_float(row.get("Close")),
                adj_close=_optional_float(row.get("Adj Close")),
                volume=_optional_int(row.get("Volume")),
                source=SOURCE_YFINANCE,
            )
        )
    return records


def _optional_float(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)


def _optional_int(value: Any) -> int | None:
    if value is None or pd.isna(value):
        return None
    return int(value)
