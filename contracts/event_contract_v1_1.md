# Event Contract v1.1

Status: **current additive contract**

Event Contract v1.1 preserves the complete v1.0 envelope and event-family semantics and adds one telemetry resource measurement.

## Additive telemetry change

For `event_type == "telemetry"`, v1.1 adds:

```json
"consumables": {
  "optic_fiber_remaining_m": 8421.5
}
```

### `payload.consumables.optic_fiber_remaining_m`

- Type: number
- Unit: meters
- Constraint: `>= 0`
- Meaning: onboard optical-fiber spool length remaining at the event's logical `event_time`
- Consumption model in simulator v1.1: one meter is consumed for each meter of simulated drone travel, including vertical travel; deployed fiber is not reeled back during return
- Exhaustion behavior in v1.1: observational only. Reaching `0` does **not** automatically alter mission, asset, health, or connection state. A future explicit scenario may attach behavior to exhaustion.

## Compatibility

- v1.0 event fields are unchanged.
- v1.0 telemetry events remain valid and do not contain `payload.consumables`.
- Silver parsing accepts both versions; `optic_fiber_remaining_m` is null for v1.0 history.
- Existing consumers that ignore unknown fields remain compatible with v1.1.

## Communications boundary

Producer-side connectivity is deliberately outside the schema. A v1.1 event may be generated and logged locally but blocked by the communications gate before entering `TransportEngine`. No transmission-state field is added to the event payload.
