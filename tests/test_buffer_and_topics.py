from __future__ import annotations

from minelogx_synthetic.buffer import PersistentBuffer
from minelogx_synthetic.topics import build_topic
from minelogx_synthetic.config import load_config
from minelogx_synthetic.publishers import Publisher
from minelogx_synthetic.streaming import stream_events
from pathlib import Path
import json


def sample_event() -> dict:
    return {
        "message_id": "msg-1",
        "tenant_id": "acme-mining",
        "site_id": "site-01",
        "message_type": "fleet_telemetry",
        "asset_type": "haul_truck",
        "asset_id": "TRUCK-014",
        "timestamp": "2026-08-28T12:00:00.000Z",
        "sequence_no": 1,
    }


def test_topic_uses_avahi_proposed_segments() -> None:
    topic = build_topic(
        sample_event(),
        "minelogx/{topic_version}/{tenant_id}/{site_id}/{message_type}/{asset_type}/{asset_id}",
        "v1",
    )
    assert topic == "minelogx/v1/acme-mining/site-01/fleet_telemetry/haul_truck/TRUCK-014"


def test_persistent_buffer_deduplicates_and_replays(tmp_path) -> None:
    path = tmp_path / "events.sqlite3"
    with PersistentBuffer(path) as buffer:
        assert buffer.enqueue("topic", sample_event()) is True
        assert buffer.enqueue("topic", sample_event()) is False
        assert len(buffer) == 1
        pending = list(buffer.pending())
        assert pending[0].message_id == "msg-1"
        buffer.acknowledge("msg-1")
        assert len(buffer) == 0


class CountingPublisher(Publisher):
    def __init__(self) -> None:
        self.count = 0

    def publish(self, topic: str, event: dict, qos: int) -> None:
        del topic, event, qos
        self.count += 1

    def close(self) -> None:
        return None


class FailingPublisher(CountingPublisher):
    def publish(self, topic: str, event: dict, qos: int) -> None:
        del topic, event, qos
        raise ConnectionError("simulated outage")


def test_burst_rate_is_aggregate(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    raw = json.loads((root / "configs" / "avahi-validation.json").read_text())
    raw["generation"]["burst"] = {
        "enabled": True,
        "events_per_second": 4,
        "duration_seconds": 1,
    }
    raw["connectivity"]["buffer_path"] = str(tmp_path / "buffer.sqlite3")
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(raw), encoding="utf-8")

    publisher = CountingPublisher()
    stats = stream_events(
        load_config(config_path),
        publisher,
        duration_seconds=1,
        realtime=False,
    )
    assert stats.generated == 4
    assert stats.published == 4


def test_failed_events_are_buffered_then_replayed(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    raw = json.loads((root / "configs" / "avahi-validation.json").read_text())
    raw["tenants"][0]["sites"][0]["assets"] = [
        raw["tenants"][0]["sites"][0]["assets"][0]
    ]
    raw["connectivity"]["buffer_path"] = str(tmp_path / "buffer.sqlite3")
    raw["connectivity"]["retry_max_attempts"] = 1
    raw["connectivity"]["retry_backoff_seconds"] = []
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(raw), encoding="utf-8")
    config = load_config(config_path)

    first = stream_events(config, FailingPublisher(), duration_seconds=5, realtime=False)
    assert first.buffered == 1

    succeeding = CountingPublisher()
    second = stream_events(config, succeeding, duration_seconds=0, realtime=False)
    assert second.replayed == 1
    assert succeeding.count == 1
