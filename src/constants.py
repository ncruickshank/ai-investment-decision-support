"""Shared constants for ingestion workflows."""

from config import PROCESSED_DATA_DIR, RAW_DATA_DIR

# =============================================================================
# ========== (Non-Text) Data Acquisition ======================================
# =============================================================================

INGESTION_MODE_FIXTURE = "fixture"
INGESTION_MODE_LIVE = "live"
INGESTION_MODES = (INGESTION_MODE_FIXTURE, INGESTION_MODE_LIVE)

SOURCE_PINNED_UNIVERSE = "pinned_universe"
SOURCE_SLICKCHARTS = "slickcharts"
SOURCE_YFINANCE = "yfinance"
SOURCE_SEC_EDGAR = "sec_edgar"

INDEX_SYMBOL_SP500 = "SP500"

DEFAULT_SQLITE_PATH = PROCESSED_DATA_DIR / "investment_data.sqlite"
DEFAULT_RAW_DATA_DIR = RAW_DATA_DIR
DEFAULT_FIXTURE_START_DATE = "2024-01-02"
DEFAULT_FIXTURE_END_DATE = "2026-07-30"
DEFAULT_LIVE_START_DATE = "2023-01-01"

TABLE_INGESTION_RUNS = "ingestion_runs"
TABLE_COMPANIES = "companies"
TABLE_INDEX_CONSTITUENTS = "index_constituents"
TABLE_PRICE_BARS = "price_bars"
TABLE_FUNDAMENTAL_FACTS = "fundamental_facts"
TABLE_RAW_ARTIFACTS = "raw_artifacts"

SEC_TAXONOMY_US_GAAP = "us-gaap"
SEC_CONCEPT_REVENUE = "Revenues"
SEC_CONCEPT_NET_INCOME = "NetIncomeLoss"
SEC_CONCEPT_EPS_DILUTED = "EarningsPerShareDiluted"
SEC_CONCEPT_ASSETS = "Assets"
SEC_CONCEPT_LIABILITIES = "Liabilities"
SEC_CONCEPT_OPERATING_CASH_FLOW = "NetCashProvidedByUsedInOperatingActivities"

SEC_CONCEPTS = (
    SEC_CONCEPT_REVENUE,
    SEC_CONCEPT_NET_INCOME,
    SEC_CONCEPT_EPS_DILUTED,
    SEC_CONCEPT_ASSETS,
    SEC_CONCEPT_LIABILITIES,
    SEC_CONCEPT_OPERATING_CASH_FLOW,
)

# =============================================================================
# ========== Document Ingestion ===============================================
# =============================================================================

USER_AGENT = "ai-investment-decision-support (nccruickshank94@gmail.com)"
FILING_TYPES = ['10-K', '10-Q']
# LIMIT = 500 # arbitrary high limit
START_DATE = "2020-01-01"
END_DATE = "2026-06-31"