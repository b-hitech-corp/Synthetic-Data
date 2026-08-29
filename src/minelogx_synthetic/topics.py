from __future__ import annotations

from typing import Any


def build_topic(event: dict[str, Any], template: str, topic_version: str) -> str:
    values = {
        "topic_version": topic_version,
        "tenant_id": event["tenant_id"],
        "site_id": event["site_id"],
        "message_type": event["message_type"],
        "asset_type": event["asset_type"],
        "asset_id": event["asset_id"],
    }
    for name, value in values.items():
        text = str(value)
        if not text or any(character in text for character in ("/", "+", "#")):
            raise ValueError(f"Invalid MQTT topic value for {name}: {value!r}")
    return template.format(**values)
