from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ALLOWED_FILES = ("telemetry.jsonl", "telemetry.csv", "telemetry.csv.gz")


def build_manifest(source: str | Path, bucket: str, prefix: str) -> dict[str, Any]:
    root = Path(source)
    if not root.is_dir():
        raise ValueError(f"Source directory does not exist: {root}")
    clean_prefix = prefix.strip("/")
    if not bucket.strip() or not clean_prefix:
        raise ValueError("Both bucket and a non-empty prefix are required")

    files = []
    for name in ALLOWED_FILES:
        path = root / name
        if not path.is_file():
            raise ValueError(f"Required generated file is missing: {path}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        key = f"{clean_prefix}/{name}"
        files.append(
            {
                "name": name,
                "path": str(path.resolve()),
                "s3_uri": f"s3://{bucket}/{key}",
                "key": key,
                "bytes": path.stat().st_size,
                "sha256": digest,
            }
        )
    return {"bucket": bucket, "prefix": clean_prefix, "files": files}


def upload_directory(
    source: str | Path,
    bucket: str,
    prefix: str,
    profile: str | None = None,
    region: str | None = None,
    dry_run: bool = False,
    overwrite: bool = False,
) -> dict[str, Any]:
    manifest = build_manifest(source, bucket, prefix)
    if dry_run:
        return {"status": "dry-run", **manifest}

    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError as exc:
        raise RuntimeError('Live upload requires: python -m pip install -e ".[aws]"') from exc

    session = boto3.Session(profile_name=profile, region_name=region)
    s3 = session.client("s3")
    s3.head_bucket(Bucket=bucket)
    content_types = {
        "telemetry.jsonl": "application/x-ndjson",
        "telemetry.csv": "text/csv",
        "telemetry.csv.gz": "application/gzip",
    }
    uploaded = []
    for item in manifest["files"]:
        if not overwrite:
            try:
                s3.head_object(Bucket=bucket, Key=item["key"])
            except ClientError as exc:
                status = exc.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
                if status != 404:
                    raise
            else:
                raise FileExistsError(
                    f"Refusing to overwrite {item['s3_uri']}; pass --overwrite if approved"
                )
        extra_args = {"ContentType": content_types[item["name"]]}
        if item["name"].endswith(".gz"):
            extra_args["ContentEncoding"] = "gzip"
        s3.upload_file(item["path"], bucket, item["key"], ExtraArgs=extra_args)
        uploaded.append(item["s3_uri"])

    manifest_path = Path(source) / "upload-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return {"status": "uploaded", "uploaded": uploaded, "manifest": str(manifest_path.resolve())}
