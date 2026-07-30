"""Raw artifact persistence helpers."""

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from constants import DEFAULT_RAW_DATA_DIR
from ingestion.models import RawArtifactRecord


def write_raw_artifact(
    *,
    run_id: str,
    source: str,
    artifact_type: str,
    payload: Any,
    ticker: str | None = None,
    source_url: str | None = None,
    raw_data_dir: Path = DEFAULT_RAW_DATA_DIR,
) -> RawArtifactRecord:
    fetched_at = datetime.now(UTC)
    ticker_part = ticker.upper().replace(".", "-") if ticker else "market"
    directory = raw_data_dir / source / ticker_part
    directory.mkdir(parents=True, exist_ok=True)

    body = json.dumps(payload, indent=2, sort_keys=True, default=str)
    content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
    artifact_id = str(uuid4())
    path = directory / f"{artifact_type}_{fetched_at:%Y%m%dT%H%M%SZ}_{artifact_id}.json"
    path.write_text(body + "\n", encoding="utf-8")

    return RawArtifactRecord(
        artifact_id=artifact_id,
        run_id=run_id,
        source=source,
        ticker=ticker,
        artifact_type=artifact_type,
        source_url=source_url,
        local_path=str(path),
        content_hash=content_hash,
        fetched_at=fetched_at,
    )
