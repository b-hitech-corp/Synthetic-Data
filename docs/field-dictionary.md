# Proposed field dictionary

Status values in this document are **Proposed** unless explicitly stated.
Ranges are simulator defaults for validation, not production/OEM guarantees.

## Common envelope

| Field | Type | Unit/format | Required | Applicability | Example |
|---|---|---|---:|---|---|
| `message_id` | string | UUID | Yes | All | `9f1c2e6a-...` |
| `schema_version` | string | semantic version | Yes | All | `1.0` |
| `tenant_id` | string | identifier | Yes | All | `acme-mining` |
| `site_id` | string | identifier | Yes | All | `site-01` |
| `message_type` | string | open registry | Yes | All | `fleet_telemetry` |
| `asset_id` | string | identifier | Yes | All | `TRUCK-014` |
| `asset_type` | string | open registry | Yes | All | `haul_truck` |
| `timestamp` | string | ISO-8601 UTC, milliseconds | Yes | All | `2026-08-28T12:00:00.000Z` |
| `sequence_no` | integer | per-asset monotonic count | Yes | All | `48213` |

## Fleet and location

| Field | Type | Unit | Precision | Default range | Required |
|---|---|---|---:|---|---:|
| `location.lat` | number | decimal degrees | 6 | -90 to 90 | Asset-specific |
| `location.lon` | number | decimal degrees | 6 | -180 to 180 | Asset-specific |
| `location.heading` | number | degrees | 1 | 0 to <360 | No |
| `location.speed_kmh` | number | km/h | 1 | 0 to 62 simulated | No |
| `location.zone` | string | site zone ID | — | site registry | No |
| `haul_cycle.cycle_id` | string | identifier | — | — | Cyclic assets |
| `haul_cycle.cycle_state` | string | state | — | loading/hauling/dumping/returning | Cyclic assets |
| `haul_cycle.payload_tonnes` | number | metric tonnes | 1 | 0 to 228 simulated | No |
| `haul_cycle.target_payload_tonnes` | number | metric tonnes | 1 | 240 simulated | No |

## Fuel, operating, and diagnostics

| Field | Type | Unit | Precision | Semantics | Required |
|---|---|---|---:|---|---:|
| `fuel.total_litres` | number | L | 2 | cumulative lifetime counter | No |
| `fuel.level_pct` | number | % | 1 | instantaneous | No |
| `fuel.engine_on` | boolean | — | — | current state | No |
| `fuel.idle_flag` | boolean | — | — | current/precomputed state | No |
| `operating.engine_hours` | number | h | 2 | cumulative lifetime counter | No |
| `operating.odometer_km` | number | km | 2 | cumulative lifetime counter | Mobile assets |
| `operating.geofence_violation` | boolean | — | — | current/precomputed flag | No |
| `operating.harsh_braking_flag` | boolean | — | — | current/precomputed flag | No |
| `operating.speeding_flag` | boolean | — | — | current/precomputed flag | No |
| `diagnostics.engine_temp_c` | number | °C | 1 | instantaneous | No |
| `diagnostics.battery_voltage` | number | V | 1 | instantaneous | No |
| `diagnostics.fault_codes` | array[string] | code registry | — | empty when healthy | No |
| `diagnostics.health_index` | number | ratio | 3 | 0 to 1 | No |

## Equipment health / plant

| Field | Type | Unit | Precision | Default range | Required |
|---|---|---|---:|---|---:|
| `equipment_health.operating_state` | string | state | — | running/faulted | Domain-specific |
| `equipment_health.bearing_temp_c` | number | °C | 1 | 68 to 108 simulated | No |
| `equipment_health.vibration_m_s2` | number | m/s² | 2 | 3.5 to 10 simulated | No |
| `equipment_health.hydraulic_pressure_psi` | number | psi | 1 | 2900 to 3150 simulated | No |
| `equipment_health.health_index` | number | ratio | 3 | 0 to 1 | No |

## Environmental / air quality

| Field | Type | Unit | Precision | Default range | Required |
|---|---|---|---:|---|---:|
| `air_quality.pm2_5_ug_m3` | number | µg/m³ | 1 | 8 to 90 simulated | Domain-specific |
| `air_quality.pm10_ug_m3` | number | µg/m³ | 1 | 18 to 180 simulated | Domain-specific |
| `air_quality.dust_mg_m3` | number | mg/m³ | 2 | 0.05 to 0.8 simulated | No |
| `air_quality.ambient_temp_c` | number | °C | 1 | 18 to 34 simulated | No |
| `air_quality.relative_humidity_pct` | number | % | 1 | 25 to 75 simulated | No |
| `air_quality.alert_flag` | boolean | — | — | simulated threshold/anomaly flag | No |

## Nullability and data quality

A non-applicable group is omitted. An applicable but unavailable field is
`null` and should be accompanied by a `data_quality` entry. The controlled
reason vocabulary remains TBD with Avahi.
