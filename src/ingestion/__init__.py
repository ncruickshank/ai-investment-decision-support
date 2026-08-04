"""Structured data ingestion helpers."""

from ingestion.pipeline import IngestionResult, run_ingestion
from ingestion.documents.sec import SecEdgarProvider
from ingestion.documents.parser import DocumentParser

__all__ = ["IngestionResult", "run_ingestion", "SecEdgarProvider", "DocumentParser"]
