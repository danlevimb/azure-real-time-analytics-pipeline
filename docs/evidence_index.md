# Evidence Index

> **Documentation path:**
> [Documentation Hub](README.md) →
> [Evidence Checklist](evidence_checklist.md) →
> **Evidence Index** →
> [Final Repository QA Checklist](final_repository_qa_checklist.md)

**Project:** `azure-real-time-analytics-pipeline`
**Purpose:** Map public technical claims to concrete evidence artifacts
**Status:** Evidence capture pending / index prepared for closeout

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

| Evidence                                | Planned Artifact                                                 | Status    |
| --------------------------------------- | ---------------------------------------------------------------- | --------- |
| Successful cloud-enabled simulation run | `evidence/01_event_hubs_ingestion/01_cloud_run_success.png`      | `PENDING` |
| Raw events from current simulator run   | `evidence/01_event_hubs_ingestion/02_raw_events_current_run.png` | `PENDING` |
| Event Hubs metadata visible             | `evidence/01_event_hubs_ingestion/03_event_hubs_metadata.png`    | `PENDING` |

### Primary technical proof

The evidence should clearly show fields such as:

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

| Evidence                 | Planned Artifact                                            | Status    |
| ------------------------ | ----------------------------------------------------------- | --------- |
| Raw event sample         | `evidence/02_kql_processing/01_raw_event_sample.png`        | `PENDING` |
| Parsed telemetry         | `evidence/02_kql_processing/02_telemetry_parsed.png`        | `PENDING` |
| Parsed state transitions | `evidence/02_kql_processing/03_state_transition_parsed.png` | `PENDING` |
| Canonical telemetry      | `evidence/02_kql_processing/04_telemetry_canonical.png`     | `PENDING` |
| Canonical deduplication  | `evidence/02_kql_processing/05_canonical_deduplication.png` | `PENDING` |

### Primary technical proof

The evidence should demonstrate:

```text
RawDroneEvents
      ↓
Parsed event table
      ↓
Canonical event representation
```

and specifically show that duplicate physical delivery does not produce duplicate logical canonical events.

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

The platform detects logical stream-quality problems such as missing sequences, duplicate deliveries, sequence gaps, and ordering anomalies.

| Evidence                    | Planned Artifact                                                | Status    |
| --------------------------- | --------------------------------------------------------------- | --------- |
| Clean integrity baseline    | `evidence/03_stream_quality/01_clean_stream_integrity.png`      | `PENDING` |
| Missing sequence detected   | `evidence/03_stream_quality/02_missing_sequence_detected.png`   | `PENDING` |
| Duplicate delivery detected | `evidence/03_stream_quality/03_duplicate_delivery_detected.png` | `PENDING` |

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

| Evidence                 | Planned Artifact                                       | Status    |
| ------------------------ | ------------------------------------------------------ | --------- |
| Timeliness metrics       | `evidence/03_stream_quality/04_timeliness_metrics.png` | `PENDING` |
| Buffered/reconnect burst | `evidence/03_stream_quality/05_burst_detection.png`    | `PENDING` |

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

Burst evidence may include:

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

The evidence should make this distinction understandable without requiring inspection of simulator code.

### Related documentation

[Stream Quality and Timeliness](stream_quality_and_timeliness.md)

---

# 8. Raw-to-Canonical Reconciliation

## Claim

Physical ingestion and logical analytical events can be reconciled without losing duplicate-delivery evidence.

| Evidence                              | Planned Artifact                                                 | Status    |
| ------------------------------------- | ---------------------------------------------------------------- | --------- |
| Raw vs Canonical summary              | `evidence/03_stream_quality/06_raw_canonical_reconciliation.png` | `PENDING` |
| Per-asset discrepancy view, if useful | `evidence/03_stream_quality/07_per_asset_reconciliation.png`     | `PENDING` |

### Expected values

Evidence should make relationships such as the following visible:

```text
RawRows
RawUniqueEventIds
RawDuplicates

CanonicalRows
UniqueCanonicalEventIds

MissingFromCanonical
ReconciliationStatus
```

Healthy canonicalization should preserve:

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

Current operational state is reconstructed from canonical evidence rather than being inferred only from the latest physically ingested telemetry row.

| Evidence                     | Planned Artifact                                                    | Status    |
| ---------------------------- | ------------------------------------------------------------------- | --------- |
| Latest state evidence        | `evidence/04_state_and_serving/01_latest_state_evidence.png`        | `PENDING` |
| Current reconstructed state  | `evidence/04_state_and_serving/02_fleet_current_state.png`          | `PENDING` |
| Latest telemetry observation | `evidence/04_state_and_serving/03_latest_telemetry_observation.png` | `PENDING` |

### Strongest recommended proof

Capture one case where:

```text
Latest telemetry observation
        ≠
Latest operational state
```

For example:

```text
Last known observation
+
newer DISCONNECTED state
```

or:

```text
Last known observation
+
terminal state
```

This demonstrates why state reconstruction exists.

### Related documentation

[State Reconstruction and Serving](state_reconstruction_and_serving.md)

---

# 10. Gold Serving

## Claim

Reusable KQL functions expose standardized analytical interfaces for downstream consumers.

| Evidence                  | Planned Artifact                                              | Status    |
| ------------------------- | ------------------------------------------------------------- | --------- |
| Fleet operational view    | `evidence/04_state_and_serving/04_fleet_operational_view.png` | `PENDING` |
| Fleet operational summary | `evidence/04_state_and_serving/05_operational_summary.png`    | `PENDING` |
| Current map-serving view  | `evidence/04_state_and_serving/06_current_map_view.png`       | `PENDING` |

### Primary serving surfaces

```text
CurrentFleetOperationalView()
CurrentFleetOperationalSummary()
CurrentFleetMapView()
```

Evidence should show that dashboard-facing results are already analytically prepared before visualization.

---

# 11. Controlled Failure Scenarios

## Claim

Known upstream failure conditions produce observable and explainable downstream effects.

| Evidence                  | Planned Artifact                                            | Status    |
| ------------------------- | ----------------------------------------------------------- | --------- |
| Duplicate-delivery effect | `evidence/05_failure_scenarios/01_duplicate_scenario.png`   | `PENDING` |
| Missing/drop effect       | `evidence/05_failure_scenarios/02_drop_scenario.png`        | `PENDING` |
| Buffered reconnect burst  | `evidence/05_failure_scenarios/03_reconnect_burst.png`      | `PENDING` |
| RF degradation effect     | `evidence/05_failure_scenarios/04_rf_failure_effect.png`    | `PENDING` |
| FIBER degradation effect  | `evidence/05_failure_scenarios/05_fiber_failure_effect.png` | `PENDING` |
| Terminal-state behavior   | `evidence/05_failure_scenarios/06_terminal_state.png`       | `PENDING` |

### Evidence principle

Do not focus primarily on:

```text
the YAML configuration
```

Focus on:

```text
Injected condition
      ↓
Observable Azure/KQL effect
```

### Related documentation

[Communications and Failure Scenarios](communications_and_failure_scenarios.md)

---

# 12. Operations Dashboard

## Claim

The dashboard exposes current operational information using Gold serving functions.

| Evidence                      | Planned Artifact                                         | Status    |
| ----------------------------- | -------------------------------------------------------- | --------- |
| Operations overview           | `evidence/06_dashboard/01_operations_overview.png`       | `PENDING` |
| Communications / connectivity | `evidence/06_dashboard/02_operations_communications.png` | `PENDING` |

Evidence should include useful context such as:

```text
Availability
Connectivity
Mission Completion
Platform Health

Map
Communication mode
Telemetry freshness
```

### Related documentation

[Dashboard and Observability](dashboard_and_observability.md)

---

# 13. Stream Quality Dashboard

## Claim

Pipeline-health information is exposed operationally alongside domain information.

| Evidence                | Planned Artifact                                       | Status    |
| ----------------------- | ------------------------------------------------------ | --------- |
| Stream Quality overview | `evidence/06_dashboard/03_stream_quality_overview.png` | `PENDING` |
| Reconciliation view     | `evidence/06_dashboard/04_stream_reconciliation.png`   | `PENDING` |

The strongest screenshot should show several reliability dimensions together.

Examples:

```text
Integrity
Timeliness
Latest Run
Reconciliation
```

This is one of the most important portfolio evidence artifacts.

---

# 14. Asset Detail

## Claim

The dashboard supports parameterized investigation of an individual producer while preserving logical event sequencing.

| Evidence                   | Planned Artifact                                      | Status    |
| -------------------------- | ----------------------------------------------------- | --------- |
| Parameterized asset detail | `evidence/06_dashboard/05_asset_detail.png`           | `PENDING` |
| Unified event timeline     | `evidence/06_dashboard/06_unified_event_timeline.png` | `PENDING` |

Evidence should show:

```text
_droneId selection
        ↓
Telemetry history
        +
State transitions
        ↓
Unified sequence-oriented timeline
```

---

# 15. Repository Closeout Evidence

## Claim

The public repository accurately represents the completed MVP and contains no unnecessary runtime artifacts or sensitive information.

| Evidence                    | Artifact                               | Status    |
| --------------------------- | -------------------------------------- | --------- |
| Final repository tree       | Repository itself                      | `PENDING` |
| KQL scripts 01–10           | `kql/`                                 | `PENDING` |
| Event contracts             | `contracts/`                           | `PENDING` |
| Documentation hub           | `docs/README.md`                       | `PENDING` |
| Dashboard export            | `dashboards/rtd-drone-operations.json` | `PENDING` |
| Evidence structure          | `evidence/`                            | `PENDING` |
| Git clean state             | Local Git validation                   | `PENDING` |
| Secret/public-safety review | Final repository QA                    | `PENDING` |

The final repository should prove most of these items directly without screenshots.

---

# 16. Minimum Final Evidence Story

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
```

Together these prove the main professional capability:

```text
Designing a real-time Azure Data Engineering pipeline
that can ingest, normalize, reconcile, validate,
reconstruct, serve, and observe imperfect event streams.
```

---

# 17. Evidence Capture Workflow

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

# 18. Capture Order

Recommended evidence-capture order:

```text
01 Event Hubs ingestion
02 KQL processing
03 Clean quality baseline
04 Duplicate scenario
05 Missing-event scenario
06 Timeliness / reconnect burst
07 Raw-to-Canonical reconciliation
08 State reconstruction
09 Gold serving
10 Terminal-state example
11 Operations dashboard
12 Stream Quality dashboard
13 Asset-detail page
14 Final repository QA
```

This sequence minimizes unnecessary scenario reruns and keeps related screenshots together.

---

# 19. Final Evidence Review

Before closeout verify that:

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

### Continue

**Previous:** [Evidence Checklist](evidence_checklist.md)
**Documentation Hub:** [README](README.md)
**Next:** [Final Repository QA Checklist](final_repository_qa_checklist.md)

**Related:**
[Dashboard and Observability](dashboard_and_observability.md)
[Stream Quality and Timeliness](stream_quality_and_timeliness.md)
[State Reconstruction and Serving](state_reconstruction_and_serving.md)
