# Event Contract

This directory formalizes the logical event contract emitted by the simulator.
The contract is independent of producer-side communications and shared transport behavior.

- `event_contract_v1_0.md` documents the original contract reconstructed from the existing `EventFactory` implementation and tests.
- `event_contract_v1_1.md` is the backward-compatible additive evolution that introduces optical-fiber remaining meters in telemetry.
- `event_contract_v1_1.schema.json` is a machine-readable schema for v1.1 events.

## Versioning rule

Minor versions are additive and preserve existing field names, types, and semantics. A major version is required for removal, rename, type change, structural relocation, or incompatible semantic change.

A valid event can be generated but not transmitted. Communications routing, transport delay, buffering, duplication, and delivery are outside the Event Contract itself.
