# Avahi synthetic telemetry MVP validation report

Validation date: 2026-08-29

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
| Fleet events | 3,600 |
| Equipment-health events | 1,200 |
| Air-quality events | 1,200 |
| Detected abnormal events | 313 |
| Observed anomaly rate | 5.22% |

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
| Three domain groups represented | PASS |

## Automated implementation tests

Seven tests pass locally, covering:

- all three representative domains;
- equivalent batch output creation;
- expansion to 500 unique configured assets;
- MQTT topic construction;
- buffer deduplication;
- aggregate burst-rate behavior;
- buffering on failure and replay after recovery.

## Not yet validated

- Live publication to Avahi AWS IoT Core
- Certificate policy and per-tenant MQTT authorization
- IoT Rule identity-match/quarantine behavior
- Kinesis/Firehose/S3 Bronze end-to-end delivery
- Final signed-off topic, units, optionality, and field-name contract
- Sustained production performance at 1,000 devices and burst load

Live validation requires an Avahi endpoint, CA certificate, client certificate,
private key, and permitted topic policy supplied through an approved secure
channel. No credentials or certificate material are stored in this project.
