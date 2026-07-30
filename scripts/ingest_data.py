"""Run structured financial data ingestion."""

import sys
from argparse import ArgumentParser
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from constants import (  # noqa: E402
    DEFAULT_FIXTURE_END_DATE,
    DEFAULT_FIXTURE_START_DATE,
    DEFAULT_RAW_DATA_DIR,
    DEFAULT_SQLITE_PATH,
    INGESTION_MODE_FIXTURE,
    INGESTION_MODES,
)
from ingestion.pipeline import DEFAULT_FIXTURE_PATH, run_ingestion  # noqa: E402


def parse_args() -> ArgumentParser:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode", choices=INGESTION_MODES, default=INGESTION_MODE_FIXTURE
    )
    parser.add_argument("--db-path", type=Path, default=DEFAULT_SQLITE_PATH)
    parser.add_argument("--raw-data-dir", type=Path, default=DEFAULT_RAW_DATA_DIR)
    parser.add_argument("--fixture-path", type=Path, default=DEFAULT_FIXTURE_PATH)
    parser.add_argument("--start-date", default=DEFAULT_FIXTURE_START_DATE)
    parser.add_argument("--end-date", default=DEFAULT_FIXTURE_END_DATE)
    parser.add_argument("--tickers", nargs="*", default=None)
    parser.add_argument("--refresh-universe", action="store_true")
    return parser


def main() -> None:
    args = parse_args().parse_args()
    end_date = None if args.end_date == "" else args.end_date
    result = run_ingestion(
        mode=args.mode,
        db_path=args.db_path,
        raw_data_dir=args.raw_data_dir,
        fixture_path=args.fixture_path,
        start_date=args.start_date,
        end_date=end_date,
        tickers=args.tickers,
        refresh_universe=args.refresh_universe,
    )
    print(f"Ingestion run completed: {result.run_id}")
    print(f"SQLite database: {result.db_path}")
    for table_name, count in sorted(result.source_summary.items()):
        print(f"{table_name}: {count}")


if __name__ == "__main__":
    main()
