from __future__ import annotations

from pathlib import Path

import pytest

from minelogx_synthetic.s3_upload import ALLOWED_FILES, build_manifest, upload_directory


def test_s3_dry_run_builds_checksummed_plan(tmp_path: Path) -> None:
    for name in ALLOWED_FILES:
        (tmp_path / name).write_bytes(name.encode())
    result = upload_directory(tmp_path, "approved-bucket", "phase2/test", dry_run=True)
    assert result["status"] == "dry-run"
    assert len(result["files"]) == 3
    assert result["files"][0]["s3_uri"].startswith("s3://approved-bucket/phase2/test/")
    assert all(len(item["sha256"]) == 64 for item in result["files"])


def test_manifest_rejects_incomplete_batch(tmp_path: Path) -> None:
    (tmp_path / "telemetry.jsonl").write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing"):
        build_manifest(tmp_path, "bucket", "prefix")
