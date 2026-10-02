<p align="center">
  <a href="../docs/README.md">← Documentation</a> |
  <a href="../README.md">Home</a> |
  <a href="../docs/README.md">Documentation</a> |
  <a href="README.md">Contracts</a> |
  <a href="event_contract_v1_0.md">v1.0 →</a>
</p>

---

# Event Contracts

This directory contains the versioned producer / consumer event contracts for `azure-real-time-analytics-pipeline`.

The contracts define the **logical event structure and semantics emitted by the synthetic producer**.

They are intentionally separate from:

```text
producer-side communication availability
shared transport behavior
physical delivery timing
Azure ingestion behavior
```

A valid logical event may therefore be generated even when it is not ultimately transmitted or delivered.

---

## Contract Evolution

```text
Event Contract v1.0
        ↓
Event Contract v1.1
        ↓
Event Contract v1.2
```

### v1.0 — Baseline

Original event envelope and event-family semantics.

Human-readable documentation:

- [Event Contract v1.0](event_contract_v1_0.md)

Normative machine-readable schema:

```text
event_contract_v1_0.schema.json
```

### v1.1 — Additive Fiber Consumable

Backward-compatible additive evolution that introduced:

```text
payload.consumables.optic_fiber_remaining_m
```

for telemetry.

Human-readable documentation:

- [Event Contract v1.1](event_contract_v1_1.md)

Normative machine-readable schema:

```text
event_contract_v1_1.schema.json
```

### v1.2 — Current Contract

Current contract version.

v1.2 preserves the common event envelope while introducing explicit per-drone communication mode:

```text
RF
FIBER
```

and the semantic relationship:

```text
communication_mode = RF
    → optic_fiber_remaining_m = null

communication_mode = FIBER
    → optic_fiber_remaining_m >= 0
```

This enables heterogeneous mixed fleets while keeping telemetry structurally stable for downstream consumers.

Human-readable documentation:

- [Event Contract v1.2](event_contract_v1_2.md)

Normative machine-readable schema:

```text
event_contract_v1_2.schema.json
```

---

## Versioning Rule

Contract evolution follows the repository's compatibility rule:

- Minor versions are additive and preserve existing field names, types, and semantics.
- A major version is required for removal, rename, incompatible type change, structural relocation, or incompatible semantic change.

The JSON Schema is the normative machine-readable definition.

The Markdown files provide the human-readable architectural and operational interpretation.

---

## Contract Boundary

The contract defines:

```text
What is a valid logical event?
```

It does **not** define:

```text
Was the event transmitted?

Was it blocked by the producer communication layer?

Was it delayed, buffered, duplicated, or dropped?

Was it physically delivered?

Was it ingested by Azure?
```

Those concerns belong to the communication, transport, and analytical layers documented elsewhere in the repository.

Related documentation:

- [Simulator and Event Model](../docs/simulator_and_event_model.md)
- [Communications and Failure Scenarios](../docs/communications_and_failure_scenarios.md)
- [Streaming and KQL Architecture](../docs/streaming_and_kql_architecture.md)

---

## Current Contract

For the current project implementation, use:

> **[Event Contract v1.2](event_contract_v1_2.md)**

---

<p align="center">
  <a href="../docs/README.md">← Documentation</a> |
  <a href="../README.md">Home</a> |
  <a href="../docs/README.md">Documentation</a> |
  <a href="README.md">Contracts</a> |
  <a href="event_contract_v1_0.md">v1.0 →</a>
</p>
