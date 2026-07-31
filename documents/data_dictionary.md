# SQLite Data Dictionary

## Overview

The project uses SQLite as its local analytical data store during the MVP phase. The schema is designed to support reproducible ingestion while keeping raw source artifacts separate from normalized analytical tables.

### Entity Relationships

```text
ingestion_runs
        │
        │
        └────────────── raw_artifacts

companies
     │
     └────────────── index_constituents

price_bars
fundamental_facts
```

---

# ingestion_runs

Tracks each ingestion execution.

| Column              | Type      | Description                                   |
| ------------------- | --------- | --------------------------------------------- |
| run_id              | TEXT (PK) | Unique ingestion run identifier               |
| mode                | TEXT      | Fixture or live ingestion mode                |
| started_at          | TEXT      | UTC timestamp when ingestion began            |
| completed_at        | TEXT      | UTC timestamp when ingestion completed        |
| status              | TEXT      | Run status (running, completed, failed, etc.) |
| source_summary_json | TEXT      | JSON summary of records ingested by source    |
| error_message       | TEXT      | Error message if ingestion failed             |

---

# companies

Master reference table containing company metadata.

**Primary Key**

* company_id

**Unique Constraints**

* ticker

| Column     | Type    | Description                        |
| ---------- | ------- | ---------------------------------- |
| company_id | TEXT    | Stable internal company identifier |
| ticker     | TEXT    | Stock ticker symbol                |
| name       | TEXT    | Company name                       |
| sector     | TEXT    | GICS sector                        |
| industry   | TEXT    | Industry classification            |
| cik        | TEXT    | SEC Central Index Key              |
| is_active  | INTEGER | Active company flag (0/1)          |
| created_at | TEXT    | Record creation timestamp          |
| updated_at | TEXT    | Last update timestamp              |

---

# index_constituents

Snapshot of index membership and weighting.

**Primary Key**

(index_symbol, ticker, as_of_date)

**Foreign Keys**

* company_id → companies.company_id

| Column       | Type    | Description                     |
| ------------ | ------- | ------------------------------- |
| index_symbol | TEXT    | Index identifier (e.g. S&P 500) |
| company_id   | TEXT    | Company reference               |
| ticker       | TEXT    | Stock ticker                    |
| weight       | REAL    | Index weight                    |
| rank         | INTEGER | Weight ranking within the index |
| as_of_date   | TEXT    | Snapshot date                   |
| source       | TEXT    | Data source                     |

Historical snapshots can coexist by storing different `as_of_date` values.

---

# price_bars

Normalized daily OHLCV market data.

**Primary Key**

(ticker, date, source)

| Column    | Type    | Description            |
| --------- | ------- | ---------------------- |
| ticker    | TEXT    | Stock ticker           |
| date      | TEXT    | Trading date           |
| open      | REAL    | Opening price          |
| high      | REAL    | Daily high             |
| low       | REAL    | Daily low              |
| close     | REAL    | Closing price          |
| adj_close | REAL    | Adjusted closing price |
| volume    | INTEGER | Trading volume         |
| source    | TEXT    | Market data provider   |

UPSERT operations ensure repeated ingestion refreshes existing observations instead of creating duplicates.

---

# fundamental_facts

Normalized SEC XBRL Company Facts.

**Primary Key**

(ticker, concept, unit, period_end, form, filed_at)

| Column        | Type    | Description                          |
| ------------- | ------- | ------------------------------------ |
| ticker        | TEXT    | Stock ticker                         |
| cik           | TEXT    | SEC Central Index Key                |
| taxonomy      | TEXT    | XBRL taxonomy namespace              |
| concept       | TEXT    | SEC concept identifier               |
| label         | TEXT    | Human-readable concept label         |
| unit          | TEXT    | Measurement unit (USD, shares, etc.) |
| value         | REAL    | Reported value                       |
| period_start  | TEXT    | Reporting period start               |
| period_end    | TEXT    | Reporting period end                 |
| fiscal_year   | INTEGER | Fiscal year                          |
| fiscal_period | TEXT    | Fiscal quarter or annual designation |
| form          | TEXT    | Filing form (10-K, 10-Q, etc.)       |
| filed_at      | TEXT    | SEC filing date                      |
| source        | TEXT    | Data source                          |

Each record represents one reported SEC financial fact.

---

# raw_artifacts

Registry of downloaded source artifacts.

**Primary Key**

artifact_id

**Foreign Keys**

* run_id → ingestion_runs.run_id

| Column        | Type | Description                              |
| ------------- | ---- | ---------------------------------------- |
| artifact_id   | TEXT | Unique artifact identifier               |
| run_id        | TEXT | Ingestion run that produced the artifact |
| source        | TEXT | Source system                            |
| ticker        | TEXT | Associated company ticker                |
| artifact_type | TEXT | Type of downloaded artifact              |
| source_url    | TEXT | Original source URL                      |
| local_path    | TEXT | Local filesystem location                |
| content_hash  | TEXT | Content hash used for integrity tracking |
| fetched_at    | TEXT | Download timestamp                       |

The raw artifact registry provides traceability between upstream data sources and normalized analytical records while enabling future parser improvements without re-downloading source data.
