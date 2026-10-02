<p align="center">
  <a href="README.md#implementation-history">← History Home</a> |
  <a href="../README.md">Home</a> |
  <a href="README.md">Documentation</a> |
  <a href="README.md#implementation-history">History Home</a> |
  <a href="connectivity_fault_v1.md">Next →</a>
</p>

---

# Change summary: Event Contract v1.1 + Connectivity Fault v1

> **Historical implementation record — v1.1.**
> This document preserves an earlier stage of the project and is not the current architecture or contract. Statements such as “next”, “not yet”, or “future” are scoped to that historical stage.
> For the current implementation, start with the [Documentation Hub](README.md) and [Event Contract v1.2](../contracts/event_contract_v1_2.md).

## Scope completed

This change set closes the first producer-connectivity fault model and introduces the additive Event Contract v1.1 optical-fiber consumable.

### Contract and domain

- Formalized Event Contract v1.0 and v1.1 in `contracts/`.
- Added `payload.consumables.optic_fiber_remaining_m` to v1.1 telemetry only.
- Preserved v1.0 telemetry without the new field.
- Added configurable `initial_optic_fiber_m` with a simulator default of `10000.0` meters.
- Added monotonic optical-fiber consumption based on actual simulated travel distance.

### Connectivity semantics

- Added a producer-side `CommsGate` before `TransportEngine`.
- Logical events continue to be generated and logged while a drone is disconnected.
- Events blocked by the producer link do not enter shared transport or cloud delivery.
- The explicit connectivity transition is allowed through as the final control indication.
- Added `comms_log.jsonl` so generated, blocked, transported, and delivered evidence can be reconciled independently.

### Azure / KQL

- Added the v1.1 telemetry column to the Silver parsing path.
- Enabled materialized-view schema propagation for `TelemetryCanonical`.
- Propagated optical-fiber remaining through Gold observation/serving views.
- Added fleet summary optical-fiber metrics.
- Fixed `HealthyPct` so it uses `HealthyDrones` rather than `AvailableDrones`.
- Added `kql/09_contract_v1_1_migration.kql` for the live database migration.

### Runner / configuration

- Integrated Azure/Event Hubs preflight into `run_simulation.ps1` when cloud publishing is enabled.
- Preflight runs before local output directory creation.
- Fixed the wrapper's final exit-code variable to consistently use `$PythonExitCode`.
- Hardened operational-profile and maintenance-scenario configuration keys.
- Repaired two pre-existing malformed/contaminated maintenance YAML sections found during full-repo validation.
- Added `fleet250_connectivity_failure_v11_cloud.yaml` as the next cloud-validation run.

## Validation

- Python test suite: `100 passed`.
- Python compile check: passed.
- All `17` checked simulator YAML configurations parse and pass `load_config` validation.
- Local accelerated end-to-end connectivity validation confirmed:
  - disconnect event delivered;
  - post-disconnect events continue to be generated locally;
  - post-disconnect events are blocked before `TransportEngine`;
  - no post-disconnect events are delivered;
  - Ground Truth continues through mission completion.

## Deliberately not included

- No onboard replay/buffer-on-reconnect implementation yet. That remains Connectivity Fault v2.
- No automatic mission/connection behavior is attached to optical-fiber exhaustion yet.
- No new dashboard visual tile was added before cloud schema migration and v1.1 data-path validation. Gold/serving views already expose the field for the next dashboard step.

---

<p align="center">
  <a href="README.md#implementation-history">← History Home</a> |
  <a href="../README.md">Home</a> |
  <a href="README.md">Documentation</a> |
  <a href="README.md#implementation-history">History Home</a> |
  <a href="connectivity_fault_v1.md">Next →</a>
</p>
