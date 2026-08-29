# Proposed Avahi ingestion contract

Status: **Proposed for discovery-session validation**

## Authoritative topic

```text
minelogx/v1/{tenant_id}/{site_id}/{message_type}/{asset_type}/{asset_id}
```

The topic is authoritative for routing identity. The payload repeats the same
identifiers so batch and non-MQTT transports remain self-describing. A mismatch
must be quarantined rather than silently corrected.

## Required common envelope

| Field | Type | Required | Meaning |
|---|---|---:|---|
| `message_id` | UUID string | Yes | Stable event identifier used for deduplication |
| `schema_version` | string | Yes | Payload contract version |
| `tenant_id` | string | Yes | Customer/mining-company identifier |
| `site_id` | string | Yes | Mine or operating-site identifier |
| `message_type` | string | Yes | Domain/routing category |
| `asset_id` | string | Yes | Producer or tracked-asset identifier |
| `asset_type` | string | Yes | Open, registry-validated asset classification |
| `timestamp` | ISO-8601 UTC | Yes | Original device/event time |
| `sequence_no` | integer | Yes | Monotonic sequence scoped to the asset |

## Optionality convention

- A group that does not apply to an asset is omitted.
- An applicable but unavailable value is `null` and may have a corresponding
  `data_quality` entry mapping its JSON field path to a reason.
- `data_quality` is omitted for a clean event.

## Meter convention

- `operating.engine_hours`: cumulative lifetime hours, 2 decimals.
- `operating.odometer_km`: cumulative lifetime distance, up to 2 decimals.
- `fuel.total_litres`: cumulative lifetime fuel consumed, up to 2 decimals.
- `fuel.level_pct`: instantaneous tank level, 1 decimal.
- An interval measurement must use a distinct field name and declare its
  interval; one field must never carry cumulative and interval semantics.

## Delivery behavior

- MQTT QoS 1 / at-least-once delivery.
- Persistent disk-backed buffering during connectivity loss.
- Replayed events retain their original `message_id`, `timestamp`, and
  `sequence_no`.
- Downstream primary deduplication key: `message_id`.
