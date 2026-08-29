from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .config import AssetConfig


MESSAGE_TYPES = {
    "fleet": "fleet_telemetry",
    "equipment_health": "equipment_health",
    "environmental": "air_quality",
}


def utc_timestamp(value: datetime) -> str:
    aware = value.astimezone(timezone.utc)
    return aware.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def build_event(
    *,
    asset: AssetConfig,
    schema_version: str,
    timestamp: datetime,
    sequence_no: int,
    measurements: dict[str, Any],
) -> dict[str, Any]:
    try:
        message_type = MESSAGE_TYPES[asset.domain]
    except KeyError as exc:
        raise ValueError(f"Unsupported domain: {asset.domain}") from exc

    return {
        "message_id": str(uuid4()),
        "schema_version": schema_version,
        "tenant_id": asset.tenant_id,
        "site_id": asset.site_id,
        "message_type": message_type,
        "asset_id": asset.asset_id,
        "asset_type": asset.asset_type,
        "timestamp": utc_timestamp(timestamp),
        "sequence_no": sequence_no,
        **measurements,
    }
