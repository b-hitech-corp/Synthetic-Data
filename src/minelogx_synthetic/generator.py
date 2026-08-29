from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from typing import Iterator

from .config import GeneratorConfig
from .simulators import create_simulator


def generate_events(
    config: GeneratorConfig,
    *,
    duration_seconds: float | None = None,
    start_time: datetime | None = None,
) -> Iterator[dict]:
    duration = config.duration_seconds if duration_seconds is None else duration_seconds
    if duration < 0:
        raise ValueError("duration_seconds cannot be negative")

    rng = random.Random(config.seed)
    simulators = [
        create_simulator(asset, config.schema_version, config.anomaly_rate, rng)
        for asset in config.assets
    ]
    current = start_time or datetime.now(timezone.utc)
    elapsed = 0.0

    while elapsed < duration:
        for simulator in simulators:
            yield simulator.next_event(current, config.cadence_seconds)
        current += timedelta(seconds=config.cadence_seconds)
        elapsed += config.cadence_seconds
