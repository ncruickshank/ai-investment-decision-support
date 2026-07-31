# Branch 02: Structured Data Ingestion

## Summary

This PR implements the second major milestone of the AI Investment Decision Support Platform by introducing a complete structured data ingestion pipeline. The repository now supports collecting, normalizing, and persisting financial data for the top 10 S&P 500 companies into a local SQLite database while preserving raw source artifacts for auditability and future reprocessing.

Following the project's notebook-first philosophy, the ingestion workflow is first demonstrated interactively in `notebooks/01_data_acquisition.ipynb` before being exposed through reusable production modules and a command-line ingestion script.

## Key Changes

### Structured Data Ingestion

* Added reusable ingestion modules under `src/`
* Implemented historical price ingestion using `yfinance`
* Implemented SEC Company Facts ingestion through the EDGAR XBRL API
* Added support for a pinned top-10 S&P 500 universe with optional live refresh
* Centralized project constants in `src/constants.py`

### Local Analytics Database

Introduced a normalized SQLite schema supporting:

* ingestion run tracking
* company metadata
* S&P 500 index constituents
* historical daily price bars
* normalized SEC fundamental facts
* raw artifact registry

All tables support idempotent ingestion through primary keys and UPSERT operations.

### Raw Artifact Tracking

Every downloaded API response is registered with metadata including:

* source
* ticker
* artifact type
* source URL
* local filesystem path
* content hash
* ingestion run

This establishes an auditable ingestion pipeline and allows future parser improvements without re-fetching upstream data.

### Notebook-First Workflow

Added `notebooks/01_data_acquisition.ipynb` to demonstrate:

* company universe loading
* market data collection
* SEC Company Facts retrieval
* SQLite persistence
* ingestion inspection and validation

The notebook shares the same reusable package code as the production ingestion script.

### Command-Line Workflow

Added `scripts/ingest_data.py` to execute the complete ingestion workflow from the command line using configurable options such as:

* fixture vs. live mode
* database path
* ticker selection
* date range
* universe refresh

### Testing

Expanded automated test coverage to include:

* SQLite schema creation
* fixture normalization
* idempotent upserts
* constants validation
* ingestion smoke tests
* script execution using temporary databases

## Database Snapshot

A successful ingestion currently produces:

| Table              |  Rows |
| ------------------ | ----: |
| companies          |    10 |
| index_constituents |    10 |
| price_bars         | 6,450 |
| fundamental_facts  | 7,306 |
| raw_artifacts      |    30 |

## Why This Matters

This branch establishes the structured data foundation that every subsequent project stage depends on.

Future branches will build on this database to support:

* document ingestion
* RAG retrieval
* forecasting models
* LLM signal extraction
* investment outlook generation

By separating raw artifacts from normalized analytics tables and implementing idempotent persistence, the project now has a reproducible, production-style data engineering layer suitable for downstream AI workflows.
