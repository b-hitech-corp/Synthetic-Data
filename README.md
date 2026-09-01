# MineLogX synthetic telemetry generator

Independent Phase 2 validation toolkit for producing Avahi-compatible synthetic
telemetry. This project reuses the equipment degradation/state-machine concepts
from Souleymane's original generator while replacing its hard-coded historical
CSV loop with a configurable canonical event model.

## Delivery scope

- Proposed Avahi `v1` common event envelope
- Fleet/haul, equipment-health, and environmental sample domains
- Near-real-time cadence and burst generation
- Batch JSON Lines, CSV, and CSV.GZ output
- MQTT/TLS QoS 1 publishing with persistent buffering and replay

MQTT publishing will be implemented after the canonical samples are validated.
OPC UA, Modbus, and HTTP adapters are outside this immediate Avahi handoff.

## Requirements

- Python 3.11 or newer
- No third-party dependency for batch generation and MQTT dry-run
- `paho-mqtt` only for live MQTT publishing

## Run locally

From this directory in PowerShell:

```powershell
$env:PYTHONPATH = "src"

# Generate equivalent JSON Lines, CSV, and CSV.GZ samples
python -m minelogx_synthetic generate `
  --config configs/avahi-validation.json `
  --duration 15 `
  --output output

# Generate a one-minute, 500-device load sample (6,000 events)
python -m minelogx_synthetic generate `
  --config configs/avahi-load-500.json `
  --duration 60 `
  --output output/load-500 `
  --preview 0

# Exercise topics and payloads without connecting to AWS
python -m minelogx_synthetic stream `
  --config configs/avahi-validation.json `
  --duration 5 `
  --dry-run
```

The `--no-wait` option skips real-time sleeps for fast local validation.

## Live AWS IoT Core publishing

Install the optional MQTT dependency:

```powershell
python -m pip install -e ".[mqtt]"
```

Keep all certificate files outside Git, then run:

```powershell
mlx-synth stream `
  --config configs/avahi-validation.json `
  --endpoint "<account-specific-iot-endpoint>" `
  --ca "<path-to-root-ca>" `
  --cert "<path-to-device-certificate>" `
  --key "<path-to-private-key>"
```

The client publishes with MQTT QoS 1. Failed events are written to the
disk-backed SQLite buffer configured by `connectivity.buffer_path`. On the next
run, buffered events are replayed in tenant/asset event order at the configured
rate while retaining their original IDs, timestamps, and sequence numbers.

## Configuration

Edit a copy of `configs/avahi-validation.json` to select tenants, sites, assets,
cadence, duration, anomaly rate, and connectivity behavior. Burst rate is an
aggregate event rate across all configured assets.

For scale tests, an asset entry can use `asset_id_pattern` plus `count` instead
of listing every device. `configs/avahi-load-500.json` demonstrates 500 globally
unique assets across two tenants and three sites. At a five-second cadence it
produces 100 events/second, or 6,000 events/minute, before burst mode.

Do not put AWS endpoints, certificates, private keys, or credentials in a
configuration committed to Git.

## Contract status

The schema is **proposed**, not a signed production contract. Open decisions are
kept configurable and documented in `docs/open-decisions.md`.

The machine-readable baseline is
`schemas/avahi-event-v1-proposed.schema.json`; it intentionally permits new
domain groups while enforcing the common envelope and core value constraints.

No credentials, certificates, endpoints, or tenant secrets belong in this
repository.

## Current validation status

- Batch and dry-run paths are covered by automated tests.
- Live AWS IoT publishing is implemented but cannot be declared end-to-end
  validated until Avahi supplies a permitted endpoint, certificate, and policy.
- Units and schema decisions remain proposed until discovery sign-off.

## Included data samples

- `samples/telemetry.*`: small nine-event example for quickly reviewing the
  payload shape across the three domains.
- `samples/load-500-one-minute/telemetry.*`: one-minute load sample containing
  6,000 events from 500 unique assets across two tenants and three sites,
  provided as JSONL, CSV, and CSV.GZ.
