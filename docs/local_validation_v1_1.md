<p align="center">
  <a href="event_contract_v1_1_rollout.md">← Previous</a> |
  <a href="../README.md">Home</a> |
  <a href="README.md">Documentation</a> |
  <a href="README.md#implementation-history">History Home</a> |
  <a href="README.md#implementation-history">History Home →</a>
</p>

---

# Local validation: Contract v1.1 + Connectivity Fault v1

> **Historical implementation record — v1.1.**
> This document preserves an earlier stage of the project and is not the current architecture or contract. Statements such as “next”, “not yet”, or “future” are scoped to that historical stage.
> For the current implementation, start with the [Documentation Hub](README.md) and [Event Contract v1.2](../contracts/event_contract_v1_2.md).

Validation was executed locally with a two-drone derivative of the v1.1 connectivity configuration, Event Hubs disabled, and accelerated wall-clock pacing.

## Automated suite

- `100 passed`

Coverage added for:

- Event Contract v1.0 and v1.1 JSON schemas
- v1.1 optical-fiber telemetry
- optical-fiber consumption model
- operational-profile validation
- connectivity disconnect/reconnect behavior
- communications gate behavior
- local state projection of optical-fiber remaining

## End-to-end local behavior for DRN-001

- Disconnect transition: sequence `124`
- Events generated after disconnect: `48`
- Events blocked by producer communications after disconnect: `48`
- Events delivered after disconnect: `0`
- Last delivered sequence: `124`
- Last generated sequence: `172`
- Initial optical fiber: `10000.0 m`
- Final optical fiber: approximately `8277.10 m`
- Ground Truth final mission phase: `LANDED`
- Ground Truth final connection state: `DISCONNECTED`

This demonstrates the intended separation:

- the drone continues its physical mission and keeps generating logical events;
- the cloud stream stops at the final disconnect indication;
- local evidence preserves what happened after loss of communications.

---

<p align="center">
  <a href="event_contract_v1_1_rollout.md">← Previous</a> |
  <a href="../README.md">Home</a> |
  <a href="README.md">Documentation</a> |
  <a href="README.md#implementation-history">History Home</a> |
  <a href="README.md#implementation-history">History Home →</a>
</p>
