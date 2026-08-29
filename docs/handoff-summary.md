# Avahi handoff summary

This MVP provides a field-accurate implementation of the **proposed** Phase 2
ingestion contract for rapid architecture validation.

## Included

- Small representative JSONL/CSV/CSV.GZ samples in `samples/`
- A 500-device load configuration generating 6,000 events/minute
- Fleet, equipment-health/plant, and air-quality domains
- Configurable five-second cadence, anomaly rate, and aggregate burst rate
- Proposed versioned MQTT topic construction
- MQTT/TLS QoS 1 client, dry-run mode, retry/backoff, disk-backed buffering,
  and ordered replay
- Proposed JSON Schema and field dictionary
- Automated tests and a reproducible validation report

## Requested Avahi confirmation

1. Final `v1` topic structure and `message_type` vocabulary
2. Final tenant identifier grammar
3. Cumulative `fuel.total_litres` and `operating.odometer_km` semantics
4. Two-decimal `operating.engine_hours`
5. Controlled or open vocabulary for `data_quality` reasons
6. Secondary compound deduplication key
7. AWS IoT endpoint, certificate/policy process, and test topic
8. Exact batch API endpoint and submission contract

## Recommended validation sequence

1. Review the representative samples and field dictionary.
2. Confirm or revise the open contract decisions.
3. Run MQTT dry-run and inspect topic/payload identity parity.
4. Supply test-only AWS IoT connectivity material securely.
5. Execute live MQTT and batch ingestion into Bronze.
6. Run the 500-device test, then increase toward 1,000 devices and bursts.
