# 01 Project Scaffold

## Summary

This branch establishes the lightweight Python 3.12 scaffold for the AI
Investment Decision Support project. It sets up the repository structure,
developer tooling, Docker foundation, CI checks, and starter documentation while
intentionally avoiding implementation of ingestion, RAG, forecasting, API, or UI
features.

## Changes

- Added `uv` project management with Python 3.12 in `pyproject.toml` and
  `uv.lock`.
- Added Ruff linting and formatting configuration.
- Added pytest smoke tests for the initial project configuration.
- Created the preferred top-level folders:
  - `data/`
  - `models/`
  - `notebooks/`
  - `reports/`
  - `reports/figures/`
  - `scripts/`
  - `src/`
  - `tests/`
- Added a minimal flat `src/` layout with `src/config.py` and `src/__init__.py`.
- Added Docker scaffold using Python 3.12.
- Added GitHub Actions CI for dependency install, linting, format checks, and
  tests.
- Updated the README with setup instructions, Docker usage, folder conventions,
  and the planned branch roadmap.
- Expanded `.gitignore` and `.dockerignore` for local environments, generated
  data, model artifacts, reports, caches, and secrets.

## Design Notes

- The scaffold deliberately keeps `src/` flat for now instead of introducing a
  nested package such as `src/ai_investment_decision_support/`.
- `src/config.py` is the only project-level Python module introduced in this
  branch.
- Generated artifacts are ignored by default, with `.gitkeep` placeholders used
  to preserve the intended folder structure.
- Docker is included as a reproducibility and learning tool, not as a required
  replacement for day-to-day local development with `uv`.

## Validation

- `uv run pytest`
- `uv run ruff check .`
- `uv run ruff format --check .`

Docker build was not verified in the Codex environment because Docker was not
installed or available on `PATH` there.

## Out of Scope

- Data ingestion
- SEC filing or transcript processing
- RAG, embeddings, vector databases, or reranking
- Forecasting models
- LLM provider adapters
- FastAPI or Streamlit application code
- Production schemas or domain models
