from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .buffer import PersistentBuffer
from .config import GeneratorConfig
from .publishers import Publisher
from .simulators import create_simulator
from .topics import build_topic


log = logging.getLogger(__name__)


@dataclass
class StreamStats:
    generated: int = 0
    published: int = 0
    buffered: int = 0
    replayed: int = 0
    failed_attempts: int = 0


def _publish_with_retry(
    publisher: Publisher,
    topic: str,
    event: dict[str, Any],
    qos: int,
    backoff_seconds: list[float],
    stats: StreamStats,
) -> bool:
    attempts = max(1, len(backoff_seconds) + 1)
    for attempt in range(attempts):
        try:
            publisher.publish(topic, event, qos)
            return True
        except (ConnectionError, TimeoutError, OSError) as exc:
            stats.failed_attempts += 1
            if attempt == attempts - 1:
                log.warning("Publish failed after %s attempts: %s", attempts, exc)
                return False
            time.sleep(backoff_seconds[attempt])
    return False


def replay_buffer(
    buffer: PersistentBuffer,
    publisher: Publisher,
    *,
    qos: int,
    rate_per_second: int,
    backoff_seconds: list[float],
    stats: StreamStats,
) -> None:
    delay = 1 / rate_per_second if rate_per_second > 0 else 0
    for buffered in list(buffer.pending(limit=max(rate_per_second, 1))):
        if not _publish_with_retry(
            publisher,
            buffered.topic,
            buffered.payload,
            qos,
            backoff_seconds,
            stats,
        ):
            break
        buffer.acknowledge(buffered.message_id)
        stats.replayed += 1
        if delay:
            time.sleep(delay)


def stream_events(
    config: GeneratorConfig,
    publisher: Publisher,
    *,
    duration_seconds: float | None = None,
    realtime: bool = True,
) -> StreamStats:
    raw_schema = config.raw["schema"]
    connectivity = config.raw["connectivity"]
    duration = config.duration_seconds if duration_seconds is None else duration_seconds
    qos = int(connectivity["mqtt_qos"])
    backoff = [float(value) for value in connectivity["retry_backoff_seconds"]]
    retry_attempts = int(connectivity["retry_max_attempts"])
    backoff = backoff[: max(retry_attempts - 1, 0)]
    stats = StreamStats()

    import random

    rng = random.Random(config.seed)
    simulators = [
        create_simulator(asset, config.schema_version, config.anomaly_rate, rng)
        for asset in config.assets
    ]
    buffer_path = connectivity["buffer_path"]
    max_events = int(connectivity["max_buffer_events"])

    with PersistentBuffer(buffer_path, max_events=max_events) as buffer:
        replay_buffer(
            buffer,
            publisher,
            qos=qos,
            rate_per_second=int(connectivity["replay_rate_per_second"]),
            backoff_seconds=backoff,
            stats=stats,
        )

        elapsed = 0.0
        burst = config.raw["generation"].get("burst", {})
        burst_enabled = bool(burst.get("enabled", False))
        burst_rate = int(burst.get("events_per_second", 0))
        burst_duration = min(float(burst.get("duration_seconds", 0)), duration)
        if burst_enabled and burst_rate <= 0:
            raise ValueError("burst.events_per_second must be positive when burst is enabled")

        # Burst rate is aggregate across all assets, not per asset. Assets are
        # sampled round-robin so a 250 events/s setting means 250 total events/s.
        burst_index = 0
        burst_interval = 1 / burst_rate if burst_enabled else 0
        while burst_enabled and elapsed < burst_duration:
            iteration_started = time.monotonic()
            simulator = simulators[burst_index % len(simulators)]
            timestamp = datetime.now(timezone.utc)
            event = simulator.next_event(timestamp, burst_interval)
            topic = build_topic(
                event,
                raw_schema["topic_template"],
                raw_schema["topic_version"],
            )
            stats.generated += 1
            if _publish_with_retry(publisher, topic, event, qos, backoff, stats):
                stats.published += 1
            else:
                buffer.enqueue(topic, event)
                stats.buffered += 1
            burst_index += 1
            elapsed += burst_interval
            if realtime:
                remaining = burst_interval - (time.monotonic() - iteration_started)
                if remaining > 0:
                    time.sleep(remaining)

        while elapsed < duration:
            iteration_started = time.monotonic()
            timestamp = datetime.now(timezone.utc)
            for simulator in simulators:
                event = simulator.next_event(timestamp, config.cadence_seconds)
                topic = build_topic(
                    event,
                    raw_schema["topic_template"],
                    raw_schema["topic_version"],
                )
                stats.generated += 1
                if _publish_with_retry(publisher, topic, event, qos, backoff, stats):
                    stats.published += 1
                else:
                    buffer.enqueue(topic, event)
                    stats.buffered += 1

            elapsed += config.cadence_seconds
            if realtime:
                remaining = config.cadence_seconds - (time.monotonic() - iteration_started)
                if remaining > 0:
                    time.sleep(remaining)
    return stats
