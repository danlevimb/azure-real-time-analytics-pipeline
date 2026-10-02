<p align="center">
  <a href="evidence_checklist.md">← Back</a> |
  <a href="../README.md">Home</a> |
  <a href="README.md">Documentation</a> |
  <a href="evidence_index.md">Evidence</a> |
  <a href="known_limitations.md">Next →</a>
</p>

---

# Evidence Index


**Project:** `azure-real-time-analytics-pipeline`
**Purpose:** Map public technical claims to concrete evidence artifacts
**Status:** Final evidence set committed and validated / repository QA in progress

---

## 1. Purpose

This document is the navigation layer for project evidence.

The [Evidence Checklist](evidence_checklist.md) defines **what must be proven**.

This index records:

```text
Project claim
      ↓
Evidence artifact
      ↓
Repository location
      ↓
Validation status
```

The objective is to make every major portfolio claim independently verifiable.

---

## 2. Evidence Strategy

The evidence set should tell the Data Engineering story in this order:

```text
Azure Event Hubs ingestion
        ↓
Raw analytical data
        ↓
KQL transformation
        ↓
Canonicalization
        ↓
Stream integrity
        ↓
Stream timeliness
        ↓
State reconstruction
        ↓
Gold serving
        ↓
Failure observability
        ↓
Operational dashboard
```

The synthetic producer provides controlled input.

The evidence should emphasize the Azure and analytical processing layers.

---

# 3. Evidence Status Legend

Use the following statuses:

| Status        | Meaning                                         |
| ------------- | ----------------------------------------------- |
| `PENDING`     | Evidence has not yet been captured              |
| `CAPTURED`    | Artifact exists locally                         |
| `REVIEWED`    | Artifact has been checked for technical clarity |
| `PUBLIC-SAFE` | Sensitive information has been reviewed         |
| `COMMITTED`   | Evidence is versioned in Git                    |
| `FINAL`       | Evidence is ready for portfolio use             |

During closeout, evidence should progressively move toward:

```text
FINAL
```

---

# 4. Event Hubs Ingestion

## Claim

Events are published through Azure Event Hubs and received by the analytical platform with Event Hubs transport metadata.

| Evidence                                | Artifact                                                         | Status  |
| --------------------------------------- | ---------------------------------------------------------------- | ------- |
| Successful cloud-enabled simulation run | `evidence/01_event_hubs_ingestion/01_cloud_run_success.png`      | `FINAL` |
| Raw events from current simulator run   | `evidence/01_event_hubs_ingestion/02_raw_events_current_run.png` | `FINAL` |
| Event Hubs metadata visible             | `evidence/01_event_hubs_ingestion/03_event_hubs_metadata.png`    | `FINAL` |

### Primary technical proof

The evidence shows fields such as:

```text
simulator_run_id
event_id
event_type
source_sequence_number

eh_enqueued_time
eh_sequence_number
eh_offset
```

### Related documentation

[Streaming and KQL Architecture](streaming_and_kql_architecture.md)

---

# 5. KQL Processing

## Claim

Raw streaming events are transformed into typed analytical tables and canonical logical events.

| Evidence                 | Artifact                                                   | Status  |
| ------------------------ | ---------------------------------------------------------- | ------- |
| Raw event sample         | `evidence/02_kql_processing/01_raw_event_sample.png`       | `FINAL` |
| Parsed telemetry         | `evidence/02_kql_processing/02_telemetry_parsed.png`       | `FINAL` |
| Parsed state transitions | `evidence/02_kql_processing/03_state_transition_parsed.png`| `FINAL` |
| Canonical telemetry      | `evidence/02_kql_processing/04_telemetry_canonical.png`    | `FINAL` |
| Canonical deduplication  | `evidence/02_kql_processing/05_canonical_deduplication.png`| `FINAL` |

### Primary technical proof

```text
RawDroneEvents
      ↓
Parsed event table
      ↓
Canonical event representation
```

The final evidence also proves that duplicate physical delivery does not produce duplicate logical canonical events.

### Implementation

```text
kql/01_create_tables.kql
kql/02_transform_functions.kql
kql/03_update_policies.kql
kql/04_materialized_views.kql
```

### Related documentation

[Streaming and KQL Architecture](streaming_and_kql_architecture.md)

---

# 6. Stream Integrity

## Claim

The platform detects logical stream-quality problems such as missing sequences, duplicate deliveries, sequence gaps, and ordering anomalies while preserving canonical uniqueness.

| Evidence                         | Artifact                                                              | Status  |
| -------------------------------- | --------------------------------------------------------------------- | ------- |
| Clean integrity baseline         | `evidence/03_stream_quality/01_clean_stream_integrity.png`            | `FINAL` |
| Missing sequence detected        | `evidence/03_stream_quality/02_missing_sequence_detected.png`         | `FINAL` |
| Missing-sequence gap detail      | `evidence/03_stream_quality/03_missing_sequence_gap_detail.png`       | `FINAL` |
| Duplicate delivery detected      | `evidence/03_stream_quality/04_duplicate_delivery_detected.png`       | `FINAL` |
| Canonical duplicate protection   | `evidence/03_stream_quality/05_duplicate_canonical_protection.png`    | `FINAL` |
| Reconnect / out-of-order result  | `evidence/03_stream_quality/06_reconnect_integrity.png`               | `FINAL` |

### Primary analytical surface

```text
CurrentStreamIntegrityReport()
```

Expected metrics include:

```text
DuplicateDeliveries
SequenceGaps
MissingSequences
OutOfOrderTransitions
NullEhMetadata
```

### Related documentation

[Stream Quality and Timeliness](stream_quality_and_timeliness.md)

---

# 7. Stream Timeliness

## Claim

The project measures how events arrive over time independently from whether the logical stream is complete.

| Evidence           | Artifact                                                   | Status  |
| ------------------ | ---------------------------------------------------------- | ------- |
| Timeliness metrics | `evidence/03_stream_quality/07_timeliness_metrics.png`     | `FINAL` |
| Burst diagnostics  | `evidence/03_stream_quality/08_burst_detection.png`        | `FINAL` |

### Primary analytical surface

```text
CurrentStreamTimelinessReport()
```

Expected metrics include:

```text
P95RelativeDelayMs
MaxRelativeDelayMs
MaxPhysicalGapMs
P95CloudLatencyMs
MaxCloudLatencyMs
```

Burst evidence includes:

```text
BurstDrone
MaxBurstEvents
BurstFirstSeq
BurstLastSeq
```

### Key claim

```text
Integrity ≠ Timeliness
```

### Related documentation

[Stream Quality and Timeliness](stream_quality_and_timeliness.md)

---

# 8. Raw-to-Canonical Reconciliation

## Claim

Physical ingestion and logical analytical events can be reconciled without losing duplicate-delivery evidence.

| Evidence                    | Artifact                                                               | Status  |
| --------------------------- | ---------------------------------------------------------------------- | ------- |
| Raw vs Canonical summary    | `evidence/03_stream_quality/09_raw_canonical_reconciliation.png`       | `FINAL` |

### Expected values

The evidence makes these relationships visible:

```text
RawRows
RawUniqueEventIds
RawDuplicates

CanonicalRows
UniqueCanonicalEventIds

MissingFromCanonical
ReconciliationStatus
```

Healthy canonicalization preserves:

```text
Raw unique logical events
        =
Canonical unique logical events
```

while still allowing:

```text
RawRows > CanonicalRows
```

when duplicate physical deliveries exist.

---

# 9. State Reconstruction

## Claim

Current operational state is reconstructed from canonical evidence and explicit precedence rules rather than being inferred only from the latest physically ingested telemetry row.

| Evidence                          | Artifact                                                                  | Status  |
| --------------------------------- | ------------------------------------------------------------------------- | ------- |
| State-evidence precedence         | `evidence/04_state_and_serving/01_state_evidence_precedence.png`          | `FINAL` |
| Current state reconstruction      | `evidence/04_state_and_serving/02_current_state_reconstruction.png`       | `FINAL` |
| Asset-state precedence resolution | `evidence/04_state_and_serving/03_asset_state_precedence_resolution.png`  | `FINAL` |

### Strongest proof

The evidence demonstrates that state reconstruction can resolve multiple evidence families using precedence rather than trusting only the latest telemetry observation.

### Related documentation

[State Reconstruction and Serving](state_reconstruction_and_serving.md)

---

# 10. Gold Serving

## Claim

Reusable KQL functions expose standardized analytical interfaces for downstream consumers.

| Evidence                    | Artifact                                                             | Status  |
| --------------------------- | -------------------------------------------------------------------- | ------- |
| Operational serving view    | `evidence/04_state_and_serving/04_operational_serving_view.png`      | `FINAL` |
| Fleet operational summary   | `evidence/04_state_and_serving/05_fleet_operational_summary.png`     | `FINAL` |
| Geospatial serving dataset  | `evidence/04_state_and_serving/06_geospatial_serving_dataset.png`    | `FINAL` |

### Primary serving surfaces

```text
CurrentFleetOperationalView()
CurrentFleetOperationalSummary()
CurrentFleetMapView()
```

The evidence shows that dashboard-facing results are analytically prepared before visualization.

---

# 11. Controlled Failure Scenarios

## Claim

Known upstream failure conditions produce observable and explainable downstream effects.

The final failure evidence focuses on communication-path failure and terminal asset behavior. Duplicate, missing, reconnect, and out-of-order effects are already proven in Stream Quality evidence.

| Evidence                                  | Artifact                                                                         | Status  |
| ----------------------------------------- | -------------------------------------------------------------------------------- | ------- |
| FIBER link-loss state transitions         | `evidence/05_failure_scenarios/01_fiber_link_loss_state_transitions.png`         | `FINAL` |
| FIBER link-loss telemetry window          | `evidence/05_failure_scenarios/02_fiber_link_loss_telemetry_window.png`          | `FINAL` |
| Terminal destruction transitions          | `evidence/05_failure_scenarios/03_terminal_destruction_state_transitions.png`    | `FINAL` |
| Terminal state reconstruction             | `evidence/05_failure_scenarios/04_terminal_destruction_reconstructed_state.png`  | `FINAL` |
| Terminal fleet impact                     | `evidence/05_failure_scenarios/05_terminal_destruction_fleet_impact.png`         | `FINAL` |
| Failure isolation in mixed fleet          | `evidence/05_failure_scenarios/06_failure_isolation_mixed_fleet.png`             | `FINAL` |

### Evidence principle

```text
Injected condition
      ↓
Observable Azure/KQL effect
      ↓
Operational interpretation
```

### Related documentation

[Communications and Failure Scenarios](communications_and_failure_scenarios.md)

---

# 12. Operations Dashboard

## Claim

The Operations page exposes current fleet state through Gold serving functions.

| Evidence            | Artifact                                                   | Status  |
| ------------------- | ---------------------------------------------------------- | ------- |
| Operations dashboard| `evidence/06_dashboard/01_operations_dashboard.png`        | `FINAL` |

The evidence shows:

```text
Availability
Connectivity
Mission Completion
Platform Health
Fleet map
Communication mode mix
Asset losses
Operational detail
```

### Related documentation

[Dashboard and Observability](dashboard_and_observability.md)

---

# 13. Stream Quality Dashboard

## Claim

Pipeline-health information is exposed operationally alongside domain information.

| Evidence                 | Artifact                                                      | Status  |
| ------------------------ | ------------------------------------------------------------- | ------- |
| Stream Quality dashboard | `evidence/06_dashboard/02_stream_quality_dashboard.png`       | `FINAL` |

The final page combines:

```text
Integrity
Timeliness
Event volume
Burst diagnostics
Window throughput
Raw → Canonical reconciliation
Window timeliness
```

This is one of the strongest portfolio evidence artifacts.

---

# 14. Drone Detail

## Claim

The dashboard supports parameterized investigation of an individual producer while preserving logical event sequencing.

| Evidence              | Artifact                                                | Status  |
| --------------------- | ------------------------------------------------------- | ------- |
| Drone Detail dashboard| `evidence/06_dashboard/03_asset_detail_dashboard.png`   | `FINAL` |

The evidence shows:

```text
_droneId selection
        ↓
Current fleet position
+
Trajectory
+
Flight profile
+
State transitions
        ↓
Unified sequence-oriented timeline
```

---

# 15. Communications Dashboard

## Claim

The dashboard exposes communication-path health as an analytical surface rather than only as simulator behavior.

| Evidence                 | Artifact                                                     | Status  |
| ------------------------ | ------------------------------------------------------------ | ------- |
| Communications dashboard | `evidence/06_dashboard/04_communications_dashboard.png`      | `FINAL` |

The evidence shows:

```text
Unaffected / affected links
Disconnected links
Out-of-order communication events
Communication condition
RF / FIBER mode distribution
Affected links
Link-state events
```

### Related documentation

[Dashboard and Observability](dashboard_and_observability.md)

---

# 16. Repository Closeout Evidence

## Claim

The public repository accurately represents the completed MVP and contains no unnecessary runtime artifacts or sensitive information.

Repository closeout is validated directly from repository artifacts; no `07_final_review/` screenshot folder is required.

| Evidence                    | Artifact                               | Status      |
| --------------------------- | -------------------------------------- | ----------- |
| KQL scripts 01–10           | `kql/`                                 | `COMMITTED` |
| Event contracts             | `contracts/`                           | `COMMITTED` |
| Documentation hub           | `docs/README.md`                       | `COMMITTED` |
| Sanitized dashboard export  | `dashboards/rtd-drone-operations.json` | `COMMITTED` |
| Final evidence structure    | `evidence/`                            | `FINAL`     |
| Git clean state             | Local Git validation                   | `PENDING`   |
| Full secret/public-safety QA| Final repository QA                    | `PENDING`   |

The remaining `PENDING` items belong to the final repository QA phase, not to evidence capture.

---

# 17. Minimum Final Evidence Story

If a reviewer examines only a small subset of evidence, prioritize:

```text
01 Event Hubs ingestion
        ↓
02 Raw / Parsed / Canonical
        ↓
03 Stream Integrity
        ↓
04 Stream Timeliness
        ↓
05 Raw / Canonical Reconciliation
        ↓
06 State Reconstruction
        ↓
07 Gold Serving
        ↓
08 Controlled Failure
        ↓
09 Operations Dashboard
        ↓
10 Stream Quality Dashboard
        ↓
11 Drone Detail
        ↓
12 Communications Dashboard
```

Together these prove the main professional capability:

```text
Designing a real-time Azure Data Engineering pipeline
that can ingest, normalize, reconcile, validate,
reconstruct, serve, and observe imperfect event streams.
```

---

# 18. Evidence Capture Workflow

Evidence should be captured deliberately rather than opportunistically.

For each artifact:

```text
1. Select the scenario or run
2. Execute or identify the required KQL
3. Validate the expected result
4. Capture only the relevant UI area
5. Inspect for sensitive information
6. Save using the planned filename
7. Review readability
8. Add to evidence/
9. Update this index
10. Commit only after review
```

Do not mark an artifact `FINAL` merely because a screenshot exists.

It should first demonstrate the intended claim clearly.

---

# 19. Capture Order

Final evidence capture was completed in this order:

```text
01 Event Hubs ingestion
02 KQL processing
03 Stream Quality
04 State reconstruction and Gold serving
05 Representative failure scenarios
06 Operations dashboard
07 Stream Quality dashboard
08 Drone Detail dashboard
09 Communications dashboard
10 Final repository QA
```

This sequence kept related evidence together and minimized unnecessary scenario reruns.

---

# 20. Final Evidence Review

The committed evidence set contains **33 public-safe screenshots**. Before repository closeout, verify that:

* Every screenshot supports a specific claim
* No screenshot exists only for decoration
* Values are legible
* Azure identifiers are reviewed
* No secret or credential is visible
* Filenames match this index
* Links resolve correctly
* Evidence folders contain README files where useful
* The index matches the actual committed evidence
* The strongest Data Engineering capabilities are immediately visible

---

<p align="center">
  <a href="evidence_checklist.md">← Back</a> |
  <a href="../README.md">Home</a> |
  <a href="README.md">Documentation</a> |
  <a href="evidence_index.md">Evidence</a> |
  <a href="known_limitations.md">Next →</a>
</p>
