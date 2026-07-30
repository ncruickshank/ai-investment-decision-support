# AI Investment Decision Support

Production-style AI investment decision support platform combining
Retrieval-Augmented Generation (RAG), financial forecasting, LLMs, and machine
learning to synthesize market data, SEC filings, earnings transcripts, and news
into transparent, evidence-based investment insights.

This repository is being built as a portfolio-quality AI engineering project.
The system is intended to support investment research with cited evidence and
interpretable model outputs, not to provide personalized financial advice or
automated trading recommendations.

## Current Branch: 01 Project Scaffold

This branch establishes the lightweight Python 3.12 foundation for the project:

- `uv` project management through `pyproject.toml`
- Ruff linting and formatting
- pytest smoke tests
- Docker scaffold
- GitHub Actions CI
- Initial folder conventions

The branch intentionally avoids implementing ingestion, RAG, forecasting,
FastAPI, Streamlit, provider adapters, or application schemas. Those pieces will
arrive in later branch chapters.

## Repository Layout

```text
data/         Local raw, intermediate, and processed data artifacts
documents/    Planning and design documents
models/       Future model artifacts such as safetensors or serialized models
notebooks/    Exploratory notebooks and component demos
reports/      Generated reports and model-system outputs
reports/figures/
scripts/      Polished command-line workflows built on reusable code
src/          Python source files for the current lightweight scaffold
tests/        Automated tests
```

Generated data, model artifacts, and reports are ignored by default. Placeholder
files keep the intended folder structure visible in git.

## Local Setup

Install `uv`, then create the local environment:

```bash
uv sync --dev
```

Run the scaffold checks:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

## Docker

Build the local image:

```bash
docker build -t ai-investment-decision-support .
```

Run the default container command, which executes the test suite:

```bash
docker run --rm ai-investment-decision-support
```

## Branch Roadmap

The design documents outline the larger implementation sequence:

1. `01-project-scaffold`: project layout, tooling, Docker, tests, CI, docs
2. `02-data-ingestion`: structured data collection and local storage
3. `03-document-pipeline`: SEC or transcript parsing and chunking
4. `04-rag-retrieval`: embeddings, vector search, reranking, citations
5. `05-forecasting-baselines`: classical and XGBoost forecasting baselines
6. `06-signal-extraction`: structured qualitative signal extraction
7. `07-signal-aggregation`: interpretable bullish, neutral, bearish outlooks
8. `08-streamlit-ui`: user-facing dashboard and research workflows
9. `09-evaluation-framework`: retrieval, LLM, citation, and forecasting metrics
10. `10-transformer-forecasting`: advanced time-series forecasting experiments
11. `11-market-outlook-stretch`: weighted top-company market outlook

See [documents/project_plan.md](documents/project_plan.md) and
[documents/design_document.md](documents/design_document.md) for the full product
and architecture direction.
