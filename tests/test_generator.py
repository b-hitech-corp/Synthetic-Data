from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from minelogx_synthetic.batch import write_batch
from minelogx_synthetic.config import load_config
from minelogx_synthetic.generator import generate_events


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs" / "avahi-validation.json"


def test_generates_all_three_domains() -> None:
    config = load_config(CONFIG)
    events = list(
        generate_events(
            config,
            duration_seconds=5,
            start_time=datetime(2026, 8, 28, tzinfo=timezone.utc),
        )
    )

    assert len(events) == 3
    assert {event["message_type"] for event in events} == {
        "fleet_telemetry",
        "equipment_health",
        "air_quality",
    }
    for event in events:
        assert event["sequence_no"] == 1
        assert event["timestamp"] == "2026-08-28T00:00:00.000Z"
        assert event["tenant_id"] == "acme-mining"


def test_batch_outputs_are_equivalent(tmp_path: Path) -> None:
    config = load_config(CONFIG)
    events = list(generate_events(config, duration_seconds=5))
    paths = write_batch(events, tmp_path)

    json_lines = paths["jsonl"].read_text(encoding="utf-8").splitlines()
    assert len(json_lines) == len(events)
    assert json.loads(json_lines[0])["message_id"] == events[0]["message_id"]
    assert paths["csv"].exists()
    assert paths["csv_gz"].exists()


def test_load_configuration_expands_to_500_unique_assets() -> None:
    config = load_config(ROOT / "configs" / "avahi-load-500.json")
    identities = {
        (asset.tenant_id, asset.site_id, asset.asset_id) for asset in config.assets
    }
    assert len(config.assets) == 500
    assert len(identities) == 500

    events = list(generate_events(config, duration_seconds=5))
    assert len(events) == 500
    assert len({event["message_id"] for event in events}) == 500
