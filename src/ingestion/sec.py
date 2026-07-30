"""SEC EDGAR source adapters and normalizers."""

from datetime import date
from typing import Any

import httpx

from constants import SEC_CONCEPTS, SEC_TAXONOMY_US_GAAP, SOURCE_SEC_EDGAR
from ingestion.models import FundamentalFactRecord


def fetch_sec_company_facts(cik: str) -> dict[str, Any]:
    padded_cik = cik.zfill(10)
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{padded_cik}.json"
    response = httpx.get(
        url,
        headers={
            "User-Agent": "ai-investment-decision-support/0.1 contact@example.com"
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def normalize_sec_company_facts(
    ticker: str,
    cik: str,
    payload: dict[str, Any],
    concepts: tuple[str, ...] = SEC_CONCEPTS,
) -> list[FundamentalFactRecord]:
    records: list[FundamentalFactRecord] = []
    us_gaap_facts = payload.get("facts", {}).get(SEC_TAXONOMY_US_GAAP, {})

    for concept in concepts:
        concept_payload = us_gaap_facts.get(concept)
        if not concept_payload:
            continue

        label = concept_payload.get("label")
        for unit, facts in concept_payload.get("units", {}).items():
            for fact in facts:
                value = fact.get("val")
                period_end = fact.get("end")
                form = fact.get("form")
                if value is None or not period_end or not form:
                    continue
                records.append(
                    FundamentalFactRecord(
                        ticker=ticker.upper(),
                        cik=cik.zfill(10),
                        taxonomy=SEC_TAXONOMY_US_GAAP,
                        concept=concept,
                        label=label,
                        unit=unit,
                        value=float(value),
                        period_start=_parse_optional_date(fact.get("start")),
                        period_end=date.fromisoformat(period_end),
                        fiscal_year=fact.get("fy"),
                        fiscal_period=fact.get("fp"),
                        form=form,
                        filed_at=_parse_optional_date(fact.get("filed")),
                        source=SOURCE_SEC_EDGAR,
                    )
                )
    return records


def _parse_optional_date(value: str | None) -> date | None:
    if not value:
        return None
    return date.fromisoformat(value)
