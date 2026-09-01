# Avahi synthetic telemetry MVP validation report

Validation date: 2026-09-01

Configuration: `configs/avahi-load-500.json`

Duration: 60 simulated seconds
Cadence: 5 seconds per asset

## Dataset summary

| Check | Result |
|---|---:|
| Total events | 6,000 |
| Unique assets | 500 |
| Tenants | 2 |
| Sites | 3 |
| Fleet events | 2,880 |
| Equipment-health events | 840 |
| Air-quality events | 600 |
| Production events | 840 |
| Maintenance events | 480 |
| Safety events | 360 |
| Detected abnormal events | 285 |
| Observed anomaly rate | 4.75% |

## Structural checks

| Check | Result |
|---|---|
| Common-envelope fields present | PASS — 0 invalid rows |
| Unique `message_id` values | PASS — 0 duplicates |
| Per-asset sequences continuous | PASS — 0 affected assets |
| Globally unique configured asset identities | PASS — 500/500 |
| JSONL event count | PASS — 6,000 |
| CSV output created | PASS |
| CSV.GZ output created and readable | PASS |
| Six domain groups represented | PASS |

## Automated implementation tests

Eleven tests pass locally, covering:

- all six representative domains;
- equivalent batch output creation;
- expansion to 500 unique configured assets;
- MQTT topic construction;
- buffer deduplication;
- aggregate burst-rate behavior;
- buffering on failure and replay after recovery.
- safe S3 upload planning, checksums, and incomplete-batch rejection.
- generation and S3 discovery of six separated domain batches.

## Not yet validated

- Live publication to Avahi AWS IoT Core
- Certificate policy and per-tenant MQTT authorization
- IoT Rule identity-match/quarantine behavior
- Kinesis/Firehose/S3 Bronze end-to-end delivery
- Direct S3 upload destination and authorization
- Final signed-off topic, units, optionality, and field-name contract
- Sustained production performance at 1,000 devices and burst load

Live validation requires an Avahi endpoint, CA certificate, client certificate,
private key, and permitted topic policy supplied through an approved secure
channel. No credentials or certificate material are stored in this project.
