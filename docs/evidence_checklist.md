<p align="center">
  <a href="dashboard_and_observability.md">← Back</a> |
  <a href="../README.md">Home</a> |
  <a href="README.md">Documentation</a> |
  <a href="evidence_index.md">Evidence</a> |
  <a href="evidence_index.md">Next →</a>
</p>

---

# Evidence Checklist


**Project:** `azure-real-time-analytics-pipeline`
**Focus:** Public evidence supporting the main Azure Real-Time Data Engineering claims
**Status:** Completed / validated / public-safe

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

Final public evidence structure:

```text
evidence/
│
├── 01_event_hubs_ingestion/
├── 02_kql_processing/
├── 03_stream_quality/
├── 04_state_and_serving/
├── 05_failure_scenarios/
└── 06_dashboard/
```

The final evidence set contains **33 public-safe screenshots**. Each folder contains only evidence that supports its specific capability area.

Repository closeout is validated through repository artifacts and the final QA checklist; it does not require a separate `07_final_review/` screenshot folder.

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

### Final screenshots

```text
03_stream_quality/
├── 01_clean_stream_integrity.png
├── 02_missing_sequence_detected.png
├── 03_missing_sequence_gap_detail.png
├── 04_duplicate_delivery_detected.png
├── 05_duplicate_canonical_protection.png
├── 06_reconnect_integrity.png
├── 07_timeliness_metrics.png
├── 08_burst_detection.png
└── 09_raw_canonical_reconciliation.png
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

### Final screenshots

```text
04_state_and_serving/
├── 01_state_evidence_precedence.png
├── 02_current_state_reconstruction.png
├── 03_asset_state_precedence_resolution.png
├── 04_operational_serving_view.png
├── 05_fleet_operational_summary.png
└── 06_geospatial_serving_dataset.png
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

### Final screenshots

The final failure evidence focuses on representative communication and terminal-state behavior; duplicate, drop, and reconnect reliability effects are already proven in Category 03.

```text
05_failure_scenarios/
├── 01_fiber_link_loss_state_transitions.png
├── 02_fiber_link_loss_telemetry_window.png
├── 03_terminal_destruction_state_transitions.png
├── 04_terminal_destruction_reconstructed_state.png
├── 05_terminal_destruction_fleet_impact.png
└── 06_failure_isolation_mixed_fleet.png
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

The final dashboard implementation includes four principal pages:

```text
Operations
Communications
Stream Quality
Drone Detail
```

### Required evidence

#### Operations

Capture:

* Fleet map
* Operational KPIs
* Connectivity
* Mission completion
* Platform health
* Communications mix
* Operational detail

#### Communications

Capture:

* Communication quality summary
* Healthy / affected link condition
* RF / FIBER mode distribution
* Affected links
* Link-state events

#### Stream Quality

Capture:

* Integrity metrics
* Timeliness metrics
* Current run context
* Raw-to-Canonical reconciliation
* Event volume / throughput
* Window throughput and timeliness

#### Drone Detail

Capture:

* Parameterized drone selector
* Current fleet position
* Per-drone trajectory
* Flight profile
* State transitions
* Unified event timeline

### Final screenshots

```text
06_dashboard/
├── 01_operations_dashboard.png
├── 02_stream_quality_dashboard.png
├── 03_asset_detail_dashboard.png
└── 04_communications_dashboard.png
```

The `RunId` control is intentionally visible as analyst context across pages. Dashboard queries continue to resolve the active dataset through `LatestObservedRun()` and the `Current*` serving functions rather than using the displayed RunId as a query filter.

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

### Validation approach

No additional screenshot folder is required for this phase.

Final review is performed against repository artifacts and the dedicated QA checklist:

```text
final_repository_qa_checklist.md
project_closeout_checklist.md
```

The review should verify repository structure, public safety, committed evidence, documentation consistency, dashboard export sanitization, Git cleanliness, and remote synchronization.

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
| Repository is portfolio-safe and reproducible                | Final Repository QA |

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

### Final evidence result

```text
Category 01 — Event Hubs Ingestion:       3 screenshots
Category 02 — KQL Processing:             5 screenshots
Category 03 — Stream Quality:             9 screenshots
Category 04 — State and Serving:          6 screenshots
Category 05 — Failure Scenarios:          6 screenshots
Category 06 — Dashboard / Observability:  4 screenshots
                                          --------------
Total:                                   33 screenshots
```

**Evidence phase status:** `COMPLETE / PUBLIC-SAFE / COMMITTED`

---

<p align="center">
  <a href="dashboard_and_observability.md">← Back</a> |
  <a href="../README.md">Home</a> |
  <a href="README.md">Documentation</a> |
  <a href="evidence_index.md">Evidence</a> |
  <a href="evidence_index.md">Next →</a>
</p>
