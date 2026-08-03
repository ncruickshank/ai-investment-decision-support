"""
SEC EDGAR document retrieval.

This module provides a lightweight client for retrieving SEC filing
metadata and filing documents from the public EDGAR APIs.

Responsibilities
----------------
* Retrieve company submission history
* List available filings
* Download filing HTML

Non-responsibilities
--------------------
* Persisting documents
* Parsing HTML
* Chunking
* Embeddings
* SQLite interaction
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import httpx


@dataclass(slots=True)
class FilingMetadata:
    """Metadata describing a single SEC filing."""

    cik: str
    accession_number: str
    filing_type: str
    filing_date: date
    primary_document: str
    filing_url: str


class EdgarRequestError(RuntimeError):
    """Raised when an EDGAR request fails."""


class SecEdgarProvider:
    """
    Lightweight client for the SEC EDGAR public APIs.

    Parameters
    ----------
    user_agent
        User-Agent string identifying your application.
        Required by the SEC Fair Access Policy.

    timeout
        HTTP timeout in seconds.
    """

    SUBMISSIONS_URL = (
        "https://data.sec.gov/submissions/CIK{cik}.json"
    )

    ARCHIVE_URL = (
        "https://www.sec.gov/Archives/edgar/data/"
        "{cik}/{accession}/{document}"
    )

    def __init__(
        self,
        user_agent: str,
        timeout: int = 30,
    ):

        self.client = httpx.Client(
            headers={
                "User-Agent": user_agent,
                "Accept-Encoding": "gzip, deflate",
            },
            timeout=timeout,
            follow_redirects=True,
        )

    def list_filings(
        self,
        cik: str,
        filing_types: list[str] | None = None,
        limit: int | None = None,
    ) -> list[FilingMetadata]:
        """
        Retrieve filing metadata for a company.

        Parameters
        ----------
        cik
            SEC company CIK.

        filing_types
            Optional list of SEC form types to include.

        limit
            Maximum number of filings returned.
        """

        cik = self._normalize_cik(cik)

        url = self.SUBMISSIONS_URL.format(cik=cik)

        response = self.client.get(url)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise EdgarRequestError(
                f"Unable to retrieve submissions for CIK {cik}."
            ) from exc

        recent = response.json()["filings"]["recent"]

        filings: list[FilingMetadata] = []

        for (
            form,
            filing_date,
            accession,
            primary_document,
        ) in zip(
            recent["form"],
            recent["filingDate"],
            recent["accessionNumber"],
            recent["primaryDocument"],
            strict=True,
        ):

            if filing_types and form not in filing_types:
                continue

            archive_url = self.ARCHIVE_URL.format(
                cik=int(cik),
                accession=accession.replace("-", ""),
                document=primary_document,
            )

            filings.append(
                FilingMetadata(
                    cik=cik,
                    accession_number=accession,
                    filing_type=form,
                    filing_date=date.fromisoformat(filing_date),
                    primary_document=primary_document,
                    filing_url=archive_url,
                )
            )

            if limit and len(filings) >= limit:
                break

        return filings

    def download_filing(
        self,
        filing: FilingMetadata,
    ) -> str:
        """
        Download the raw filing document.

        Returns
        -------
        str
            Raw HTML returned by EDGAR.
        """

        response = self.client.get(filing.filing_url)

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise EdgarRequestError(
                f"Unable to download {filing.filing_url}"
            ) from exc

        return response.text

    @staticmethod
    def _normalize_cik(cik: str | int) -> str:
        """Convert a CIK to the SEC's required 10-digit format."""

        return f"{int(cik):010d}"