# Open decisions

The implementation must not hard-code these as confirmed production facts.

| Decision | Current position | Status |
|---|---|---|
| MQTT version segment | Include `v1` in the topic | Proposed |
| Tenant identifier grammar | Lowercase kebab-case such as `acme-mining` | TBD |
| Fuel counter | `fuel.total_litres` is cumulative lifetime consumption | Proposed |
| Engine-hours precision | Two decimal places | Proposed |
| Data-quality reasons | Begin with an open string vocabulary | TBD |
| Secondary deduplication key | Tenant + site + asset + timestamp + sequence | TBD |
| Raw/Bronze retention | Defined by platform lifecycle policy | Out of generator scope |
| Live MQTT endpoint and certificates | Supplied securely by Avahi | External dependency |
