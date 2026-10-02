# Evidence Checklist

> **Documentation path:**
> [Documentation Hub](README.md) →
> [Dashboard & Observability](dashboard_and_observability.md) →
> **Evidence Checklist** →
> [Evidence Index](evidence_index.md)

**Project:** `azure-real-time-analytics-pipeline`
**Focus:** Public evidence supporting the main Azure Real-Time Data Engineering claims
**Status:** Closeout evidence planning and validation

---

## 1. Purpose

This checklist defines the evidence required to support the main technical claims of the project.

The objective is not to capture every development step.

Evidence should prove that the implemented Azure Data Engineering architecture actually works.

The strongest evidence should demonstrate:

```text
Event generation
      ↓
Azure Event Hubs
      ↓
Raw ingestion
      ↓
KQL processing
      ↓
Canonicalization
      ↓
Stream reliability
      ↓
State reconstruction
      ↓
Gold serving
      ↓
Operational dashboard
```

---

## 2. Evidence Principles

Evidence should be:

* Public-safe
* Numbered consistently
* Easy to understand
* Focused on one technical claim
* Connected to implemented behavior
* Readable without excessive explanation
* Free of secrets and personal information

Evidence should not expose:

* Connection strings
* Shared Access Keys
* SAS tokens
* Passwords
* Access tokens
* Tenant IDs unless intentionally sanitized
* Subscription IDs unless intentionally sanitized
* Personal email addresses
* Private resource identifiers that provide no portfolio value
* Local filesystem information containing personal details

---

## 3. Evidence Folder Structure

Recommended structure:

```text
evidence/
│
├── README.md
│
├── 01_event_hubs_ingestion/
│
├── 02_kql_processing/
│
├── 03_stream_quality/
│
├── 04_state_and_serving/
│
├── 05_failure_scenarios/
│
├── 06_dashboard/
│
└── 07_final_review/
```

Each folder should contain only evidence that supports its specific capability area.

---

# 4. Category 01 — Event Hubs Ingestion

## Claim

The project publishes real-time telemetry into Azure Event Hubs and preserves transport metadata in the analytical platform.

### Required evidence

* Successful Event Hubs-enabled simulator execution
* Azure-side evidence that events were received
* `RawDroneEvents` populated from the current run
* Visible `simulator_run_id`
* Visible `event_type`
* Visible `source_sequence_number`
* Event Hubs metadata such as:

  * `eh_enqueued_time`
  * `eh_sequence_number`
  * `eh_offset`

### Recommended screenshots

```text
01_event_hubs_ingestion/
├── 01_cloud_run_success.png
├── 02_raw_events_current_run.png
└── 03_event_hubs_metadata.png
```

### Evidence should prove

```text
Producer
   ↓
Azure Event Hubs
   ↓
RawDroneEvents
```

not merely that an Event Hubs resource exists.

---

# 5. Category 02 — KQL Processing

## Claim

The incoming event stream is transformed into typed and canonical analytical layers using KQL.

### Required evidence

* Raw event example
* Parsed telemetry result
* Parsed state-transition result
* Canonical telemetry result
* Canonical state-transition result
* Evidence of one logical row per canonical `event_id`

### Recommended screenshots

```text
02_kql_processing/
├── 01_raw_event_sample.png
├── 02_telemetry_parsed.png
├── 03_state_transition_parsed.png
├── 04_telemetry_canonical.png
└── 05_canonical_deduplication.png
```

### Evidence should prove

```text
Raw
  ↓
Parsed
  ↓
Canonical
```

and not simply show KQL source code.

The repository already contains the implementation under:

```text
kql/
```

The evidence should demonstrate execution results.

---

# 6. Category 03 — Stream Quality

## Claim

The analytical platform can detect and explain imperfect stream delivery.

### Required evidence

At least one clean baseline and representative degraded scenarios demonstrating:

* Missing sequences
* Duplicate deliveries
* Sequence gaps
* Out-of-order behavior
* Timeliness degradation
* Raw vs canonical reconciliation

### Recommended screenshots

```text
03_stream_quality/
├── 01_clean_stream_integrity.png
├── 02_missing_sequence_detected.png
├── 03_duplicate_delivery_detected.png
├── 04_timeliness_metrics.png
├── 05_burst_detection.png
└── 06_raw_canonical_reconciliation.png
```

### Preferred KQL surfaces

Evidence may include results from:

```text
CurrentStreamIntegrityReport()
CurrentStreamTimelinessReport()
```

plus targeted reconciliation queries.

### Evidence should demonstrate

```text
Integrity
≠
Timeliness
```

and prove that both dimensions are observable.

---

# 7. Category 04 — State Reconstruction and Serving

## Claim

The project reconstructs current operational state from canonical event evidence rather than relying only on the latest physically ingested telemetry row.

### Required evidence

* Latest state evidence
* Current reconstructed fleet state
* Latest telemetry observation
* Gold operational view
* Operational summary
* Map-serving result

### Recommended screenshots

```text
04_state_and_serving/
├── 01_latest_state_evidence.png
├── 02_fleet_current_state.png
├── 03_latest_telemetry_observation.png
├── 04_fleet_operational_view.png
├── 05_operational_summary.png
└── 06_current_map_view.png
```

### Important evidence case

Capture at least one example where:

```text
Latest observation
        ≠
Latest state evidence
```

For example:

```text
last known telemetry position
+
newer DISCONNECTED or terminal state
```

This is one of the strongest demonstrations of the project architecture.

---

# 8. Category 05 — Failure Scenarios

## Claim

Controlled failure scenarios produce measurable downstream effects in the Azure streaming architecture.

The evidence should focus on **observable data behavior**, not on simulator mechanics.

### Representative scenarios

Recommended minimum coverage:

```text
Duplicate delivery
Drop / missing event
Reconnect / buffered burst
RF communication failure
FIBER communication failure
Terminal asset
```

It is not necessary to publish evidence for every YAML configuration.

### Recommended screenshots

```text
05_failure_scenarios/
├── 01_duplicate_scenario.png
├── 02_drop_scenario.png
├── 03_reconnect_burst.png
├── 04_rf_failure_effect.png
├── 05_fiber_failure_effect.png
└── 06_terminal_state.png
```

### Evidence should demonstrate

```text
Controlled failure
       ↓
Observable stream effect
       ↓
KQL detection
       ↓
Operational interpretation
```

---

# 9. Category 06 — Dashboard

## Claim

The real-time dashboard consumes reusable KQL analytical layers and exposes both operational state and data-pipeline health.

The current dashboard implementation includes the principal areas:

```text
Operations
Stream Quality
Asset Detail
```

### Required evidence

#### Operations

Capture:

* Fleet map
* Operational KPIs
* Connectivity
* Mission completion
* Platform health
* Communications information

#### Stream Quality

Capture:

* Integrity metrics
* Timeliness metrics
* Latest observed run
* Reconciliation
* Event volume or throughput

#### Asset Detail

Capture:

* Parameterized asset selector
* Telemetry history
* State transitions
* Unified event timeline

### Recommended screenshots

```text
06_dashboard/
├── 01_operations_overview.png
├── 02_operations_communications.png
├── 03_stream_quality_overview.png
├── 04_stream_reconciliation.png
├── 05_asset_detail.png
└── 06_unified_event_timeline.png
```

---

# 10. Category 07 — Final Review

## Claim

The public repository accurately represents the completed portfolio MVP.

### Required evidence

* Final repository structure
* KQL scripts 01–10 present
* Event contracts present
* Dashboard export present
* Documentation hub present
* Evidence structure complete
* No runtime output tracked
* No virtual environments tracked
* No secrets committed
* Git working tree clean
* Local repository synchronized with remote

### Recommended artifacts

```text
07_final_review/
├── README.md
└── optional_public_repo_overview.png
```

This section may rely partly on repository files rather than screenshots where screenshots add little value.

---

# 11. Evidence Priority

Not every implementation detail deserves a screenshot.

Prioritize evidence in this order:

```text
1. Azure ingestion
2. KQL analytical processing
3. Stream reliability
4. State reconstruction
5. Gold serving
6. Dashboard observability
7. Representative failure scenarios
8. Repository closeout
```

The public evidence should reinforce the Data Engineering story.

Simulator implementation details should remain secondary.

---

# 12. What Does Not Need Separate Evidence

Separate screenshots are generally unnecessary for:

* Every YAML configuration
* Every unit test
* Every simulator class
* Every KQL function
* Every state transition
* Every communication mode combination
* Every historical contract version
* Every intermediate debugging step

Those artifacts remain available in source control.

Evidence should prove the architecture without duplicating the entire repository visually.

---

# 13. Code vs Evidence

The project uses three different forms of proof.

### Implementation

```text
kql/
simulator/
scripts/
tests/
contracts/
dashboards/
```

answers:

```text
How was it implemented?
```

### Documentation

```text
docs/
```

answers:

```text
Why was it designed this way?
```

### Evidence

```text
evidence/
```

answers:

```text
Did it actually work?
```

All three are useful, but they serve different purposes.

---

# 14. Evidence Naming Convention

Use ordered filenames:

```text
01_description.png
02_description.png
03_description.png
```

Names should describe the claim rather than the UI action.

Prefer:

```text
03_stream_integrity_report.png
```

over:

```text
03_query_screen.png
```

Prefer:

```text
05_raw_canonical_reconciliation.png
```

over:

```text
05_kql_result.png
```

This keeps evidence understandable from GitHub navigation alone.

---

# 15. Screenshot Guidelines

Before committing a screenshot:

* Crop unnecessary browser or desktop content
* Verify text is readable
* Remove unrelated tabs or windows
* Avoid showing local usernames or personal paths
* Verify cloud identifiers are safe
* Verify credentials are not visible
* Use meaningful zoom
* Capture enough context to understand the result
* Avoid giant full-screen captures when a focused view is clearer

Do not modify technical values merely to improve appearance.

Evidence should remain truthful to the executed scenario.

---

# 16. Claim-to-Evidence Map

The final evidence set should support at least the following project claims:

| Project Claim                                                | Primary Evidence    |
| ------------------------------------------------------------ | ------------------- |
| Events are ingested through Azure Event Hubs                 | Category 01         |
| Raw events retain Event Hubs metadata                        | Category 01         |
| Raw events are transformed into typed structures             | Category 02         |
| Logical duplicate delivery is canonicalized                  | Categories 02–03    |
| Missing and duplicate sequences are detectable               | Category 03         |
| Stream timeliness is measurable                              | Category 03         |
| Raw and Canonical layers can be reconciled                   | Category 03         |
| Current state is reconstructed from multiple event families  | Category 04         |
| Gold serving functions expose reusable analytical interfaces | Category 04         |
| Controlled failures create observable downstream effects     | Category 05         |
| RF/FIBER context reaches analytical consumers                | Categories 04–06    |
| Operational state and stream health are visible together     | Category 06         |
| Dashboard configuration is versioned                         | Repository artifact |
| Repository is portfolio-safe and reproducible                | Category 07         |

---

# 17. Minimum Portfolio Evidence Set

If the public evidence needs to remain compact, the minimum strong set is:

```text
01 Event Hubs → Raw ingestion
02 Raw → Parsed / Canonical
03 Stream integrity
04 Stream timeliness
05 Raw → Canonical reconciliation
06 Current state / Gold serving
07 Failure scenario effect
08 Operations dashboard
09 Stream Quality dashboard
10 Asset-detail timeline
```

These ten evidence points tell the complete Data Engineering story without overwhelming the reader.

---

# 18. Completion Criteria

The evidence phase is complete when:

* Every major public claim has supporting evidence
* Evidence is linked from the final Evidence Index
* Screenshots are public-safe
* Filenames are consistent
* Evidence does not duplicate implementation unnecessarily
* The strongest claims are easy to verify
* Azure Data Engineering remains the visible project focus
* The evidence supports the final README narrative

---

### Continue

**Previous:** [Dashboard and Observability](dashboard_and_observability.md)
**Documentation Hub:** [README](README.md)
**Next:** [Evidence Index](evidence_index.md)

**Related:**
[Streaming and KQL Architecture](streaming_and_kql_architecture.md)
[Stream Quality and Timeliness](stream_quality_and_timeliness.md)
[State Reconstruction and Serving](state_reconstruction_and_serving.md)
