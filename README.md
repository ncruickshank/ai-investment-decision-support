# AI Investment Decision Support

Production-style AI investment decision support platform combining Retrieval-Augmented Generation (RAG), financial forecasting, LLMs, and machine learning to synthesize market data, SEC filings, earnings transcripts, and news into transparent, evidence-based investment insights.

This repository is being built as a portfolio-quality AI engineering project. The system is intended to support investment research with cited evidence and interpretable model outputs—not to provide personalized financial advice or automated trading recommendations.

## Current Status

The project currently includes two completed implementation milestones:

* **Project scaffold**

  * Python 3.12 project managed with `uv`
  * Ruff linting and formatting
  * pytest test suite
  * Docker development environment
  * GitHub Actions CI
  * Repository conventions and documentation

* **Structured data ingestion**

  * Historical market data ingestion via `yfinance`
  * SEC EDGAR Company Facts ingestion
  * Notebook-first ingestion workflow
  * Reusable ingestion modules
  * Command-line ingestion script
  * Local SQLite analytics database
  * Raw artifact tracking for reproducible ingestion
  * Idempotent UPSERT-based persistence

The current ingestion pipeline populates a local SQLite database containing:

| Table                | Purpose                                 |
| -------------------- | --------------------------------------- |
| `companies`          | Company reference data                  |
| `index_constituents` | S&P 500 constituent snapshots           |
| `price_bars`         | Daily historical OHLCV market data      |
| `fundamental_facts`  | Normalized SEC XBRL Company Facts       |
| `raw_artifacts`      | Registry of downloaded source artifacts |
| `ingestion_runs`     | Ingestion execution metadata            |

A typical ingestion currently produces:

| Table              |  Rows |
| ------------------ | ----: |
| companies          |    10 |
| index_constituents |    10 |
| price_bars         | 6,450 |
| fundamental_facts  | 7,306 |
| raw_artifacts      |    30 |

## Repository Layout

```text
data/         Local raw, intermediate, and processed data artifacts
documents/    Planning and design documents
models/       Future trained model artifacts
notebooks/    Exploratory notebooks and experimentation
reports/      Generated reports and evaluation outputs
scripts/      Command-line workflows
src/          Reusable application code
tests/        Automated test suite
```

Generated datasets, models, reports, and databases are ignored by default. Placeholder `.gitkeep` files preserve the intended project structure.

## Local Setup

Install project dependencies:

```bash
uv sync --dev
```

Run the quality checks:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

## Running Data Ingestion

Execute the structured ingestion pipeline:

```bash
uv run python scripts/ingest_data.py
```

This will download market and SEC data, register raw artifacts, and populate the local SQLite database.

The exploratory version of this workflow is available in:

```text
notebooks/01_data_acquisition.ipynb
```

## Docker

Build the local development image:

```bash
docker build -t ai-investment-decision-support .
```

Run the default container command:

```bash
docker run --rm ai-investment-decision-support
```

## Project Roadmap

The project is being developed incrementally through a series of focused implementation branches:

| Branch | Milestone                               |
| ------ | --------------------------------------- |
| 01     | Project scaffold                        |
| **02** | **Structured data ingestion** ✓         |
| 03     | Document parsing and chunking           |
| 04     | RAG retrieval system                    |
| 05     | Forecasting baselines                   |
| 06     | LLM signal extraction                   |
| 07     | Signal aggregation                      |
| 08     | Streamlit application                   |
| 09     | Evaluation framework                    |
| 10     | Transformer forecasting                 |
| 11     | Market outlook and comparison workflows |

## Long-Term Architecture

The completed system will combine:

* Structured financial data ingestion
* Document ingestion and parsing
* Retrieval-Augmented Generation (RAG)
* Hybrid search and reranking
* Financial forecasting
* LLM-based qualitative signal extraction
* Explainable investment outlook generation
* FastAPI services
* Streamlit user interface
* Evaluation of retrieval, forecasting, and LLM performance

See `documents/project_plan.md` and `documents/design_document.md` for the complete product vision and system architecture.
