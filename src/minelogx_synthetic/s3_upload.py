from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ALLOWED_FILES = ("telemetry.jsonl", "telemetry.csv", "telemetry.csv.gz")


def build_manifest(
    source: str | Path,
    bucket: str,
    prefix: str,
    layout: str = "combined",
    file_format: str = "csv",
) -> dict[str, Any]:
    root = Path(source)
    if not root.is_dir():
        raise ValueError(f"Source directory does not exist: {root}")
    clean_prefix = prefix.strip("/")
    if not bucket.strip() or not clean_prefix:
        raise ValueError("Both bucket and a non-empty prefix are required")

    if layout not in {"combined", "by-domain", "all"}:
        raise ValueError("layout must be combined, by-domain, or all")
    format_files = {
        "jsonl": ("telemetry.jsonl",),
        "csv": ("telemetry.csv",),
        "csv-gz": ("telemetry.csv.gz",),
        "all": ALLOWED_FILES,
    }
    if file_format not in format_files:
        raise ValueError("file_format must be jsonl, csv, csv-gz, or all")
    selected_files = format_files[file_format]

    files = []
    if layout in {"combined", "all"}:
        for name in selected_files:
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
    domain_root = root / "by-domain"
    if layout in {"by-domain", "all"}:
        if not domain_root.is_dir():
            raise ValueError(f"Domain batch directory does not exist: {domain_root}")
        for domain_dir in sorted(path for path in domain_root.iterdir() if path.is_dir()):
            if not domain_dir.name.replace("_", "").isalnum():
                raise ValueError(f"Unsafe domain directory: {domain_dir}")
            for name in selected_files:
                path = domain_dir / name
                if not path.is_file():
                    raise ValueError(f"Incomplete domain batch; missing: {path}")
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                relative = path.relative_to(root).as_posix()
                key = f"{clean_prefix}/{relative}"
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
        if not files:
            raise ValueError(f"No domain batches found under: {domain_root}")
    return {
        "bucket": bucket,
        "prefix": clean_prefix,
        "layout": layout,
        "file_format": file_format,
        "files": files,
    }


def upload_directory(
    source: str | Path,
    bucket: str,
    prefix: str,
    profile: str | None = None,
    region: str | None = None,
    dry_run: bool = False,
    overwrite: bool = False,
    layout: str = "combined",
    file_format: str = "csv",
) -> dict[str, Any]:
    manifest = build_manifest(
        source, bucket, prefix, layout=layout, file_format=file_format
    )
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
