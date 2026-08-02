"""
SEC EDGAR document retrieval utilities.

This module provides a thin client around the SEC EDGAR submissions
and filing archive APIs. It is responsible only for retrieving filing
metadata and raw filing documents.

Downstream responsibilities such as parsing, normalization, chunking,
and persistence should be handled by separate modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import requests


class EdgarError(Exception):
    """Base exception for SEC EDGAR retrieval errors."""


class EdgarRequestError(EdgarError):
    """Raised when an SEC request fails."""


@dataclass(slots=True)
class FilingMetadata:
    """
    Metadata describing an SEC filing.

    Attributes
    ----------
    cik:
        Company's SEC Central Index Key.

    accession_number:
        SEC accession number identifying the filing.

    filing_type:
        SEC form type (for example, 10-K or 10-Q).

    filing_date:
        Date the filing was submitted.

    primary_document:
        Filename of the primary filing document.

    primary_doc_description:
        SEC-provided description of the primary document.

    filing_url:
        URL to the primary filing document.
    """

    cik: str
    accession_number: str
    filing_type: str
    filing_date: date
    primary_document: str
    primary_doc_description: str
    filing_url: str


class SecEdgarProvider:
    """
    Client for retrieving SEC EDGAR filings.

    Parameters
    ----------
    cik:
        Company CIK. Must be the 10-digit zero-padded SEC identifier.

    user_agent:
        Identifying User-Agent string required by SEC fair access policy.

    timeout:
        HTTP request timeout in seconds.
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
        cik: str,
        user_agent: str,
        timeout: int = 30,
    ):
        self.cik = self._normalize_cik(cik)
        self.timeout = timeout

        self.session = requests.Session()

        self.session.headers.update(
            {
                "User-Agent": user_agent,
                "Accept-Encoding": "gzip, deflate",
                "Host": "www.sec.gov",
            }
        )

    # ======================
    # === Public Methods ===
    # ======================

    def get_company_submissions(self) -> dict:
        """
        Retrieve SEC submission history for the company.

        Returns
        -------
        dict
            Raw SEC submissions JSON response.
        """

        url = self._build_submission_url()

        return self._request_json(url)

    def list_filings(
        self,
        filing_types: list[str] | None = None,
        limit: int | None = None,
    ) -> list[FilingMetadata]:
        """
        Retrieve filing metadata from SEC submissions.

        Parameters
        ----------
        filing_types:
            Optional list of SEC form types to include.

            Example:
                ["10-K", "10-Q"]

        limit:
            Maximum number of filings to return.

        Returns
        -------
        list[FilingMetadata]
            Filing metadata objects.
        """

        submissions = self.get_company_submissions()

        recent = submissions["filings"]["recent"]

        forms = recent["form"]
        filing_dates = recent["filingDate"]
        accession_numbers = recent["accessionNumber"]
        primary_documents = recent["primaryDocument"]
        descriptions = recent["primaryDocDescription"]

        filings: list[FilingMetadata] = []

        for (
            form,
            filing_date,
            accession_number,
            primary_document,
            description,
        ) in zip(
            forms,
            filing_dates,
            accession_numbers,
            primary_documents,
            descriptions,
            strict=True,
        ):

            if filing_types and form not in filing_types:
                continue

            filing = FilingMetadata(
                cik=self.cik,
                accession_number=accession_number,
                filing_type=form,
                filing_date=date.fromisoformat(filing_date),
                primary_document=primary_document,
                primary_doc_description=description,
                filing_url=self._build_filing_url(
                    accession_number,
                    primary_document,
                ),
            )

            filings.append(filing)

            if limit and len(filings) >= limit:
                break

        return filings

    def download_filing(
        self,
        filing: FilingMetadata,
    ) -> str:
        """
        Download filing contents.

        Parameters
        ----------
        filing:
            Filing metadata object.

        Returns
        -------
        str
            Raw filing HTML/text.
        """

        return self._request_text(
            filing.filing_url
        )

    def download_primary_document(
        self,
        filing: FilingMetadata,
        output_path: Path,
    ) -> Path:
        """
        Download and save a filing document.

        Parameters
        ----------
        filing:
            Filing metadata object.

        output_path:
            Destination file path.

        Returns
        -------
        Path
            Path to downloaded document.
        """

        content = self.download_filing(filing)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            content,
            encoding="utf-8",
        )

        return output_path

    # =======================
    # === Private Methods ===
    # =======================

    def _build_submission_url(self) -> str:
        """
        Build SEC submissions endpoint URL.
        """

        return self.SUBMISSIONS_URL.format(
            cik=self.cik,
        )

    def _build_filing_url(
        self,
        accession_number: str,
        primary_document: str,
    ) -> str:
        """
        Build SEC archive URL for primary document.
        """

        accession_clean = accession_number.replace(
            "-",
            "",
        )

        cik_clean = str(
            int(self.cik)
        )

        return self.ARCHIVE_URL.format(
            cik=cik_clean,
            accession=accession_clean,
            document=primary_document,
        )

    def _request_json(
        self,
        url: str,
    ) -> dict:
        """
        Execute JSON GET request.
        """

        response = self.session.get(
            url,
            timeout=self.timeout,
        )

        if not response.ok:
            raise EdgarRequestError(
                f"SEC request failed: "
                f"{response.status_code} {url}"
            )

        return response.json()

    def _request_text(
        self,
        url: str,
    ) -> str:
        """
        Execute text GET request.
        """

        response = self.session.get(
            url,
            timeout=self.timeout,
        )

        if not response.ok:
            raise EdgarRequestError(
                f"SEC request failed: "
                f"{response.status_code} {url}"
            )

        return response.text

    @staticmethod
    def _normalize_cik(
        cik: str,
    ) -> str:
        """
        Normalize CIK to SEC 10-digit format.
        """

        return str(cik).zfill(10)