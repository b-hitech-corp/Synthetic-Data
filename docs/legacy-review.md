# Review of Souleymane's original generator

The original `iot_data_generator.py` was reviewed before this refactor.

## Reused concepts

- Persistent state per asset
- Progressive equipment-health degradation
- Normal, drift/degraded, failure, and maintenance concepts
- Equipment-specific measurement adjustments
- Configurable anomaly-rate intent
- Small random sensor variation

## Limitations addressed

- Historical four-hour cadence replaced by configurable near-real-time cadence
- Hard-coded Windows output path removed
- Monthly-only CSV output replaced by canonical event plus transport writers
- Tenant/site/message identity added
- Per-asset sequence numbers and UUID message IDs added
- Fleet, plant/equipment-health, and environmental domains added
- Cumulative engine, odometer, and fuel meter semantics introduced
- Batch JSONL/CSV/CSV.GZ and MQTT paths separated from simulation logic
- Credentials are never embedded

The result is a modular extension of the original simulation approach rather
than an unrelated replacement.
