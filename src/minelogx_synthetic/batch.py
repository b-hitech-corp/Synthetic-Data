from __future__ import annotations

import csv
import gzip
import json
from pathlib import Path
from typing import Any, Iterable


def flatten(value: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in value.items():
        field = f"{prefix}.{key}" if prefix else key
        if isinstance(item, dict):
            result.update(flatten(item, field))
        elif isinstance(item, list):
            result[field] = json.dumps(item, separators=(",", ":"))
        else:
            result[field] = item
    return result


def write_batch(events: Iterable[dict[str, Any]], output_dir: str | Path) -> dict[str, Path]:
    rows = list(events)
    if not rows:
        raise ValueError("Cannot write an empty batch")

    target = Path(output_dir)
    target.mkdir(parents=True, exist_ok=True)
    jsonl_path = target / "telemetry.jsonl"
    csv_path = target / "telemetry.csv"
    gzip_path = target / "telemetry.csv.gz"

    with jsonl_path.open("w", encoding="utf-8", newline="\n") as handle:
        for event in rows:
            handle.write(json.dumps(event, separators=(",", ":"), sort_keys=False) + "\n")

    flat_rows = [flatten(event) for event in rows]
    fieldnames = list(dict.fromkeys(key for row in flat_rows for key in row))
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(flat_rows)

    with csv_path.open("rb") as source, gzip.open(gzip_path, "wb", compresslevel=6) as target_gzip:
        while chunk := source.read(1024 * 1024):
            target_gzip.write(chunk)

    return {"jsonl": jsonl_path, "csv": csv_path, "csv_gz": gzip_path}
