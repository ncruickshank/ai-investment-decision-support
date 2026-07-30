"""Typed records used by the structured ingestion layer."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class CompanyRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    company_id: str
    ticker: str
    name: str
    sector: str | None = None
    industry: str | None = None
    cik: str | None = None
    is_active: bool = True


class IndexConstituentRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    index_symbol: str
    company_id: str
    ticker: str
    weight: float | None = None
    rank: int | None = None
    as_of_date: date
    source: str


class PriceBarRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    ticker: str
    date: date
    open: float | None = None
    high: float | None = None
    low: float | None = None
    close: float | None = None
    adj_close: float | None = None
    volume: int | None = None
    source: str


class FundamentalFactRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    ticker: str
    cik: str
    taxonomy: str
    concept: str
    label: str | None = None
    unit: str
    value: float
    period_start: date | None = None
    period_end: date
    fiscal_year: int | None = None
    fiscal_period: str | None = None
    form: str
    filed_at: date | None = None
    source: str


class RawArtifactRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    artifact_id: str
    run_id: str
    source: str
    ticker: str | None = None
    artifact_type: str
    source_url: str | None = None
    local_path: str
    content_hash: str
    fetched_at: datetime
