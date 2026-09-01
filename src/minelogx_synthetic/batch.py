from __future__ import annotations

import csv
import gzip
import json
import shutil
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


def write_batches_by_domain(
    events: Iterable[dict[str, Any]], output_dir: str | Path
) -> dict[str, dict[str, Path]]:
    rows = list(events)
    if not rows:
        raise ValueError("Cannot split an empty batch")

    groups: dict[str, list[dict[str, Any]]] = {}
    for event in rows:
        message_type = event.get("message_type")
        if not isinstance(message_type, str) or not message_type:
            raise ValueError("Every event must contain a non-empty message_type")
        safe_name = message_type.replace("-", "_")
        if not safe_name.replace("_", "").isalnum():
            raise ValueError(f"Unsafe message_type for output path: {message_type}")
        groups.setdefault(safe_name, []).append(event)

    output_root = Path(output_dir)
    target = output_root / "by-domain"
    result = {
        message_type: write_batch(group, target / message_type)
        for message_type, group in sorted(groups.items())
    }
    bundles = {
        "jsonl": (output_root / "s3-ready-jsonl", ".jsonl"),
        "csv": (output_root / "s3-ready-csv", ".csv"),
        "csv_gz": (output_root / "s3-ready-csv-gz", ".csv.gz"),
    }
    for directory, _ in bundles.values():
        directory.mkdir(parents=True, exist_ok=True)
    for message_type, paths in result.items():
        for kind, (directory, suffix) in bundles.items():
            shutil.copyfile(paths[kind], directory / f"{message_type}{suffix}")
    return result
