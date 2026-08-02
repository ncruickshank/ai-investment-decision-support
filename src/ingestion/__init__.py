"""Structured data ingestion helpers."""

from ingestion.pipeline import IngestionResult, run_ingestion
from ingestion.documents.sec import SecEdgarProvider

__all__ = ["IngestionResult", "run_ingestion", "SecEdgarProvider"]
