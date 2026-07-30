"""Ticker universe sources."""

import re
from datetime import date

import httpx

from constants import INDEX_SYMBOL_SP500, SOURCE_PINNED_UNIVERSE, SOURCE_SLICKCHARTS
from ingestion.models import CompanyRecord, IndexConstituentRecord

PINNED_SP500_TOP_10_AS_OF_DATE = date(2026, 7, 30)

PINNED_SP500_TOP_10 = (
    {
        "ticker": "NVDA",
        "name": "NVIDIA Corp",
        "sector": "Information Technology",
        "industry": "Semiconductors",
        "cik": "0001045810",
        "weight": 7.44,
        "rank": 1,
    },
    {
        "ticker": "AAPL",
        "name": "Apple Inc",
        "sector": "Information Technology",
        "industry": "Technology Hardware, Storage & Peripherals",
        "cik": "0000320193",
        "weight": 7.27,
        "rank": 2,
    },
    {
        "ticker": "MSFT",
        "name": "Microsoft Corp",
        "sector": "Information Technology",
        "industry": "Systems Software",
        "cik": "0000789019",
        "weight": 4.21,
        "rank": 3,
    },
    {
        "ticker": "AMZN",
        "name": "Amazon.com Inc",
        "sector": "Consumer Discretionary",
        "industry": "Broadline Retail",
        "cik": "0001018724",
        "weight": 3.71,
        "rank": 4,
    },
    {
        "ticker": "GOOGL",
        "name": "Alphabet Inc",
        "sector": "Communication Services",
        "industry": "Interactive Media & Services",
        "cik": "0001652044",
        "weight": 2.99,
        "rank": 5,
    },
    {
        "ticker": "GOOG",
        "name": "Alphabet Inc",
        "sector": "Communication Services",
        "industry": "Interactive Media & Services",
        "cik": "0001652044",
        "weight": 2.81,
        "rank": 6,
    },
    {
        "ticker": "AVGO",
        "name": "Broadcom Inc",
        "sector": "Information Technology",
        "industry": "Semiconductors",
        "cik": "0001730168",
        "weight": 2.70,
        "rank": 7,
    },
    {
        "ticker": "META",
        "name": "Meta Platforms Inc",
        "sector": "Communication Services",
        "industry": "Interactive Media & Services",
        "cik": "0001326801",
        "weight": 2.24,
        "rank": 8,
    },
    {
        "ticker": "TSLA",
        "name": "Tesla Inc",
        "sector": "Consumer Discretionary",
        "industry": "Automobile Manufacturers",
        "cik": "0001318605",
        "weight": 1.84,
        "rank": 9,
    },
    {
        "ticker": "BRK.B",
        "name": "Berkshire Hathaway Inc",
        "sector": "Financials",
        "industry": "Multi-Sector Holdings",
        "cik": "0001067983",
        "weight": 1.59,
        "rank": 10,
    },
)


def company_id_for_ticker(ticker: str) -> str:
    return ticker.upper().replace(".", "-")


def load_pinned_top_10_universe() -> tuple[
    list[CompanyRecord], list[IndexConstituentRecord]
]:
    companies = [
        CompanyRecord(
            company_id=company_id_for_ticker(row["ticker"]),
            ticker=row["ticker"],
            name=row["name"],
            sector=row["sector"],
            industry=row["industry"],
            cik=row["cik"],
        )
        for row in PINNED_SP500_TOP_10
    ]
    constituents = [
        IndexConstituentRecord(
            index_symbol=INDEX_SYMBOL_SP500,
            company_id=company_id_for_ticker(row["ticker"]),
            ticker=row["ticker"],
            weight=row["weight"],
            rank=row["rank"],
            as_of_date=PINNED_SP500_TOP_10_AS_OF_DATE,
            source=SOURCE_PINNED_UNIVERSE,
        )
        for row in PINNED_SP500_TOP_10
    ]
    return companies, constituents


def refresh_sp500_top_10_universe(
    as_of_date: date | None = None,
    url: str = "https://www.slickcharts.com/sp500/analysis",
) -> list[IndexConstituentRecord]:
    """Fetch a current top-10 weight snapshot from Slickcharts.

    This deliberately updates membership/weights only. Stable company metadata remains
    sourced from pinned records or market-data providers.
    """
    response = httpx.get(
        url,
        headers={"User-Agent": "ai-investment-decision-support/0.1"},
        timeout=30,
    )
    response.raise_for_status()

    rows = re.findall(
        r"<tr>.*?<td>(\d+)</td>.*?<td><a[^>]*>([^<]+)</a></td>.*?"
        r"<td><a[^>]*>([^<]+)</a></td>.*?<td>.*?</td>.*?<td>([\d.]+)%</td>",
        response.text,
        flags=re.DOTALL,
    )
    snapshot_date = as_of_date or date.today()
    return [
        IndexConstituentRecord(
            index_symbol=INDEX_SYMBOL_SP500,
            company_id=company_id_for_ticker(ticker),
            ticker=ticker,
            weight=float(weight),
            rank=int(rank),
            as_of_date=snapshot_date,
            source=SOURCE_SLICKCHARTS,
        )
        for rank, ticker, _name, weight in rows[:10]
    ]
