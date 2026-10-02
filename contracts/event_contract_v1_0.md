<p align="center">
  <a href="README.md">← Contracts</a> |
  <a href="../README.md">Home</a> |
  <a href="../docs/README.md">Documentation</a> |
  <a href="README.md">Contracts</a> |
  <a href="event_contract_v1_1.md">v1.1 →</a>
</p>

---

# Event Contract v1.0

Status: **historical baseline / backward-compatible legacy**

> **Historical contract note:** v1.0 is preserved to document the original event envelope and compatibility baseline. The current project contract is [v1.2](event_contract_v1_2.md).

This document formalizes the contract that already existed in `EventFactory` before the v1.1 extension.

## Common envelope

Every logical event contains:

- `schema_version`: string, `"1.0"`
- `event_id`: string; deterministic format `<simulator_run_id>-<drone_id>-<source_sequence_number:08d>`
- `event_type`: string
- `event_time`: ISO-8601 UTC string
- `drone_id`: string
- `battalion_id`: string
- `mission_id`: string
- `source_sequence_number`: integer; monotonically increments per drone across event families
- `source_type`: `"virtual_drone"`
- `source_gateway_id`: string, `GW-<battalion_id>`
- `simulation.simulator_run_id`: string
- `simulation.scenario`: string
- `simulation.seed`: integer
- `payload`: event-family-specific object

## Event families

### `telemetry`

`payload.position`
- `latitude`
- `longitude`
- `altitude_m`

`payload.movement`
- `ground_speed_mps`
- `vertical_speed_mps`
- `heading_deg`

`payload.power`
- `battery_pct`

`payload.health`
- `platform_health`

`payload.communications`
- `connection_state`

`payload.operations`
- `asset_state`
- `mission_status`
- `mission_phase`

### `state_transition`

- `payload.state_domain`
- `payload.previous_state`
- `payload.new_state`
- `payload.reason_code`

### `maintenance_event`

- `payload.maintenance_action`
- `payload.maintenance_category`
- `payload.reason_code`
- `payload.severity`

### `status_confirmation`

- `payload.state_domain`
- `payload.confirmed_state`
- `payload.confirmation_type`
- `payload.reason_code`

## Boundary

The contract describes the logical event after generation. It does not guarantee that the event is transmitted, submitted to `TransportEngine`, physically delivered, or ingested by Azure.

---

<p align="center">
  <a href="README.md">← Contracts</a> |
  <a href="../README.md">Home</a> |
  <a href="../docs/README.md">Documentation</a> |
  <a href="README.md">Contracts</a> |
  <a href="event_contract_v1_1.md">v1.1 →</a>
</p>
