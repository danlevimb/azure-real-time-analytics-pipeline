# Final Repository QA Checklist

> **Documentation path:**
> [Documentation Hub](README.md) →
> [Evidence Checklist](evidence_checklist.md) →
> [Evidence Index](evidence_index.md) →
> **Final Repository QA Checklist** →
> [Project Closeout Checklist](project_closeout_checklist.md)

**Project:** `azure-real-time-analytics-pipeline`
**Purpose:** Final technical, documentation, evidence, Git, and public-safety validation
**Status:** Pending final QA execution

---

## 1. QA Rule

This checklist must reflect the **actual repository state**.

Do not mark an item complete because it was planned, implemented previously, or assumed to work.

Use:

```text
[ ] Pending
[x] Verified
```

Only verified items should be checked.

---

# 2. Git and Repository Hygiene

* [ ] `git status` is clean.
* [ ] Local branch is synchronized with the intended remote branch.
* [ ] No uncommitted project changes remain.
* [ ] No unintended generated files are tracked.
* [ ] No Python virtual environment is tracked.
* [ ] No `__pycache__` directories are tracked.
* [ ] No runtime `output/` data is tracked.
* [ ] No temporary debug or traceback files are tracked.
* [ ] No editor-specific temporary files are tracked.
* [ ] `.gitignore` covers expected runtime artifacts.

### Validation commands

```bash
git status
git branch -vv
git ls-files
```

Useful targeted checks:

```bash
git ls-files | findstr /I ".venv __pycache__ output traceback"
```

Expected result:

```text
Only intentional repository artifacts are versioned.
```

---

# 3. Repository Structure

Verify that the public repository presents clear responsibility boundaries.

Expected principal areas include:

```text
contracts/
dashboards/
docs/
evidence/
kql/
scripts/
simulator/
tests/
```

* [ ] `contracts/` contains versioned event contracts.
* [ ] `dashboards/` contains the dashboard export.
* [ ] `docs/` contains current project documentation.
* [ ] `docs/README.md` provides documentation navigation.
* [ ] `evidence/` contains only reviewed public evidence.
* [ ] `kql/` contains the analytical implementation.
* [ ] `scripts/` contains useful execution/support scripts.
* [ ] `simulator/` remains clearly identifiable as supporting infrastructure.
* [ ] Test artifacts are organized and understandable.
* [ ] Repository structure reinforces the Data Engineering story.

---

# 4. Event Contracts

Verify the contract chain:

```text
v1.0
  ↓
v1.1
  ↓
v1.2
```

* [ ] `event_contract_v1_0.schema.json` exists.
* [ ] `event_contract_v1_1.schema.json` exists.
* [ ] `event_contract_v1_2.schema.json` exists.
* [ ] Contract Markdown documentation is present where intended.
* [ ] `event_contract_v1_2.md` accurately describes the current schema.
* [ ] Contract links resolve correctly.
* [ ] v1.2 communication-mode semantics are documented.
* [ ] RF and FIBER conditional behavior is represented accurately.
* [ ] No documentation claims fields unsupported by the actual contract.

### Related documentation

[Event Contract v1.2](../contracts/event_contract_v1_2.md)

---

# 5. KQL Implementation

Verify that the complete analytical sequence exists:

```text
01_create_tables.kql
02_transform_functions.kql
03_update_policies.kql
04_materialized_views.kql
05_quality_functions.kql
06_state_functions.kql
07_serving_functions.kql
08_performance_functions.kql
09_contract_v1_1_migration.kql
10_contract_v1_2_migration.kql
```

* [ ] All expected KQL files are present.
* [ ] Numbering reflects logical dependency order.
* [ ] Raw table definitions are current.
* [ ] Transform functions reflect current event-contract fields.
* [ ] Update policies reference valid tables/functions.
* [ ] Canonical materialized views are valid.
* [ ] Quality functions execute successfully.
* [ ] State reconstruction functions execute successfully.
* [ ] Serving functions execute successfully.
* [ ] Timeliness/performance functions execute successfully.
* [ ] v1.1 migration remains historically coherent.
* [ ] v1.2 migration propagates current contract fields correctly.

---

# 6. Contract-to-KQL Propagation

This is a critical final QA item.

Verify the complete propagation path:

```text
Event Contract
      ↓
Producer Event
      ↓
RawDroneEvents
      ↓
Transform Function
      ↓
Parsed Table
      ↓
Canonical View
      ↓
Gold Function
      ↓
Dashboard
```

For important v1.2 fields such as:

```text
communication_mode
optic_fiber_remaining_m
```

verify:

* [ ] Field exists in the source event.
* [ ] Field reaches Raw ingestion.
* [ ] Field is extracted by the KQL transform.
* [ ] Field exists in the parsed analytical layer.
* [ ] Field survives canonicalization.
* [ ] Field reaches serving functions where applicable.
* [ ] Field is usable by dashboard queries.
* [ ] RF nullability / FIBER applicability remain semantically correct.

No field should appear in the dashboard only because of undocumented ad-hoc logic.

---

# 7. Event Hubs / Raw Ingestion QA

Using a known cloud-enabled run:

* [ ] Simulator successfully publishes to Azure Event Hubs.
* [ ] `RawDroneEvents` receives the expected run.
* [ ] `simulator_run_id` is populated.
* [ ] `event_id` is populated.
* [ ] `event_type` is populated.
* [ ] `source_sequence_number` is populated.
* [ ] `eh_enqueued_time` is populated.
* [ ] `eh_sequence_number` is populated.
* [ ] `eh_offset` is populated.
* [ ] No unexpected null Event Hubs metadata appears in the clean baseline.

Evidence should be captured during this validation.

See:

[Evidence Checklist](evidence_checklist.md)

---

# 8. Canonicalization QA

Validate the distinction between physical and logical events.

* [ ] Clean runs preserve all expected logical events.
* [ ] Duplicate physical deliveries remain visible in Raw.
* [ ] Duplicate physical deliveries collapse to one canonical `event_id`.
* [ ] Canonical tables do not introduce unexpected duplicates.
* [ ] Raw unique-event counts reconcile with Canonical unique-event counts.
* [ ] Per-asset reconciliation identifies no unexplained differences.

Expected principle:

```text
Physical delivery count
        may differ from
Logical event count
```

without corrupting downstream state.

---

# 9. Stream Integrity QA

Execute:

```kusto
CurrentStreamIntegrityReport()
```

Validate representative scenarios.

### Clean baseline

* [ ] Duplicate count is expected.
* [ ] Missing sequence count is expected.
* [ ] Sequence gaps are expected.
* [ ] Out-of-order count is expected.
* [ ] Null Event Hubs metadata is expected.

### Controlled degradation

* [ ] Duplicate scenario is detected.
* [ ] Missing/drop scenario is detected.
* [ ] Out-of-order behavior is detectable where injected.
* [ ] Results correspond to the intentionally configured failure.

The goal is not for every metric to be zero.

The goal is for the metric to **correctly describe the executed scenario**.

---

# 10. Stream Timeliness QA

Execute:

```kusto
CurrentStreamTimelinessReport()
```

Verify:

* [ ] Relative-delay metrics are returned.
* [ ] Physical-gap metric is returned.
* [ ] Cloud-latency metrics are returned.
* [ ] Burst information is returned where applicable.
* [ ] Buffered/reconnect scenarios produce explainable timeliness degradation.
* [ ] Clean baseline differs meaningfully from intentional degradation.

Confirm the central distinction:

```text
Integrity ≠ Timeliness
```

A complete stream may still be late.

---

# 11. State Reconstruction QA

Validate:

```text
StateEvidence()
LatestStateEvidence()
FleetCurrentState()
LatestTelemetryObservation()
```

* [ ] Multiple canonical event families contribute evidence.
* [ ] Evidence ranking behaves as designed.
* [ ] State is ordered primarily by event semantics/time rather than ingestion order.
* [ ] State domains resolve independently.
* [ ] Controlled inference does not override stronger explicit evidence.
* [ ] Latest telemetry observation is independently available.
* [ ] Disconnection can remain visible after telemetry becomes stale.
* [ ] Terminal-state behavior remains visible after telemetry stops.

Capture at least one case where:

```text
latest observation
        ≠
latest state
```

---

# 12. Gold Serving QA

Validate:

```kusto
CurrentFleetOperationalView()
CurrentFleetOperationalSummary()
CurrentFleetMapView()
```

* [ ] Operational view returns expected asset population.
* [ ] State fields are populated appropriately.
* [ ] Observation fields are populated appropriately.
* [ ] `communication_mode` is present.
* [ ] FIBER-specific fields behave correctly.
* [ ] RF records do not falsely imply fiber state.
* [ ] State timestamps are available.
* [ ] Telemetry timestamps are available.
* [ ] Freshness/age values are meaningful.
* [ ] Fleet summary KPIs reconcile with detailed rows.
* [ ] Map-serving output is dashboard-ready.

---

# 13. Failure Scenario QA

Representative scenarios should be verified, not every configuration file.

### Transport

* [ ] Extra-delay scenario behaves as intended.
* [ ] Drop scenario behaves as intended.
* [ ] Duplicate scenario behaves as intended.
* [ ] Buffered/reconnect scenario behaves as intended.

### Communications

* [ ] RF failure produces the intended downstream effect.
* [ ] FIBER link-loss behavior is observable.
* [ ] FIBER terminal-cut behavior is observable if retained in final scope.
* [ ] Fiber exhaustion produces the intended disconnected state.
* [ ] Mixed RF/FIBER runs remain analytically coherent.

### Terminal source

* [ ] Terminal asset produces explicit terminal-state evidence.
* [ ] Telemetry stops as intended.
* [ ] Last known observation remains usable downstream.
* [ ] Gold state remains operationally meaningful.

Related:

[Communications and Failure Scenarios](communications_and_failure_scenarios.md)

---

# 14. Dashboard QA

Validate the versioned dashboard artifact:

```text
dashboards/rtd-drone-operations.json
```

## Operations

* [ ] Fleet map renders correctly.
* [ ] Operational KPIs render correctly.
* [ ] Connectivity values are correct.
* [ ] Mission completion values are correct.
* [ ] Platform health values are correct.
* [ ] RF/FIBER metrics render correctly.
* [ ] Disconnected assets can be identified.
* [ ] Telemetry freshness is visible where intended.

## Stream Quality

* [ ] Integrity metrics render correctly.
* [ ] Timeliness metrics render correctly.
* [ ] Latest observed run is correct.
* [ ] Raw/Canonical reconciliation renders correctly.
* [ ] Event-volume metrics render correctly.
* [ ] Burst information renders where appropriate.

## Asset Detail

* [ ] `_droneId` selector works.
* [ ] Selector values are populated dynamically.
* [ ] Telemetry history responds to the selected asset.
* [ ] State-transition history responds to the selected asset.
* [ ] Unified event timeline responds to the selected asset.
* [ ] Logical sequence ordering is understandable.

---

# 15. Dashboard Export Safety QA

Because the dashboard export contains implementation metadata:

* [ ] Review cluster URI.
* [ ] Review database identifiers.
* [ ] Review workspace identifiers.
* [ ] Review embedded query text.
* [ ] Verify no credential or access token exists.
* [ ] Sanitize identifiers only where required.
* [ ] Confirm sanitization does not break the value of the public artifact.
* [ ] Re-export if a cleaner artifact is preferable to manual modification.

Never assume that a JSON dashboard export is automatically public-safe.

---

# 16. Documentation QA

Verify current principal documentation:

```text
docs/README.md
architecture_and_scope.md
implementation_plan.md
simulator_and_event_model.md
streaming_and_kql_architecture.md
stream_quality_and_timeliness.md
state_reconstruction_and_serving.md
communications_and_failure_scenarios.md
dashboard_and_observability.md
evidence_checklist.md
evidence_index.md
final_repository_qa_checklist.md
```

* [ ] Every current document renders correctly in GitHub.
* [ ] Navigation links work.
* [ ] Documentation Hub links work.
* [ ] Previous/Next navigation works where used.
* [ ] Contract links work.
* [ ] Dashboard artifact links work.
* [ ] No obsolete path is referenced.
* [ ] Documentation consistently emphasizes Azure Data Engineering.
* [ ] Simulator details remain secondary.
* [ ] No document contradicts the current implementation.
* [ ] No document claims functionality outside the implemented MVP.

---

# 17. Historical Documentation QA

Historical implementation documents may remain in the repository.

Examples include:

```text
change_summary_v1_1.md
connectivity_fault_v1.md
event_contract_v1_1_rollout.md
local_validation_v1_1.md
```

* [ ] Historical documents are still useful.
* [ ] They are clearly distinguishable from current architecture documentation.
* [ ] They do not appear to represent the current contract accidentally.
* [ ] Documentation Hub classifies them appropriately.
* [ ] Obsolete material that creates confusion is removed only if no longer useful.

Historical documentation should preserve evolution without competing with the current project story.

---

# 18. Evidence QA

Before closeout:

* [ ] Required evidence has been captured.
* [ ] Evidence filenames follow the planned convention.
* [ ] Every image is readable.
* [ ] Every image supports a specific claim.
* [ ] No screenshot exists only for decoration.
* [ ] Evidence Index points to actual files.
* [ ] Evidence Index statuses are current.
* [ ] No personal information is visible.
* [ ] No credentials or secrets are visible.
* [ ] Azure identifiers have been reviewed.
* [ ] Strong Data Engineering evidence appears first.

Related:

[Evidence Checklist](evidence_checklist.md)
[Evidence Index](evidence_index.md)

---

# 19. Secret and Sensitive-Data QA

Perform repository-wide checks for common secret patterns.

Review for:

```text
connection strings
SharedAccessKey
SharedAccessKeyName
SAS tokens
AccountKey
Authorization headers
Bearer tokens
client secrets
passwords
private keys
personal email addresses
```

Possible local searches:

```bash
git grep -n -i "SharedAccessKey"
git grep -n -i "AccountKey"
git grep -n -i "password"
git grep -n -i "client_secret"
git grep -n -i "Bearer "
```

Also manually inspect:

```text
*.yaml
*.json
*.ps1
*.py
*.md
dashboard exports
screenshots
```

* [ ] No secrets are committed.
* [ ] No credentials exist in Git history intended for publication.
* [ ] No private connection string remains.
* [ ] No public evidence exposes sensitive information.

If a real secret was ever committed, simply deleting the current line is not sufficient; the credential must also be rotated.

---

# 20. README Preflight

The root `README.md` should be finalized **after** technical and evidence QA.

Before writing the final README:

* [ ] Technical scope is frozen.
* [ ] Current architecture is verified.
* [ ] Evidence set is substantially complete.
* [ ] Documentation paths are final.
* [ ] Known limitations are understood.
* [ ] Repository structure is stable.
* [ ] Principal screenshots are selected.
* [ ] Final public claims are evidence-backed.

The root README should summarize the implemented system rather than introducing new claims during closeout.

---

# 21. Public Narrative QA

A reviewer should quickly understand that the project demonstrates:

```text
Azure Event Hubs ingestion
        ↓
KQL analytical engineering
        ↓
Raw / Parsed / Canonical layering
        ↓
Stream integrity and timeliness
        ↓
State reconstruction
        ↓
Gold serving
        ↓
Operational observability
```

Verify:

* [ ] The project is clearly positioned as Data Engineering.
* [ ] Drone simulation is clearly a synthetic test domain.
* [ ] Failure injection supports reliability testing.
* [ ] Azure/KQL architecture remains the main story.
* [ ] The project does not read like a drone-simulation project.
* [ ] The project does not read like only a dashboard project.
* [ ] Claims are understandable to a Data Engineer or technical interviewer.

---

# 22. Final Git QA

After all final edits:

```bash
git status
git diff
git log --oneline -n 10
```

Then verify:

* [ ] Intended changes are committed.
* [ ] Commit messages are understandable.
* [ ] No accidental file deletion occurred.
* [ ] No generated evidence was omitted unintentionally.
* [ ] No temporary files were added.
* [ ] Local branch is synchronized with remote.
* [ ] GitHub renders README correctly.
* [ ] GitHub renders Markdown links correctly.
* [ ] GitHub displays evidence correctly.

---

# 23. Final Technical Acceptance

The repository is technically ready for closeout only when all of the following statements are true:

```text
Azure receives the stream.

KQL transforms the stream.

Canonicalization protects logical identity.

Integrity problems are detectable.

Timeliness problems are measurable.

Raw and Canonical layers reconcile.

Operational state can be reconstructed.

Gold functions expose reusable analytical outputs.

Controlled failures create explainable downstream signals.

The dashboard makes both operational state and stream health observable.

The repository contains sufficient public evidence to prove those claims.
```

* [ ] Final technical acceptance completed.

---

# 24. QA Outcome

After execution, record:

```text
Repository QA status:
[ ] NOT STARTED
[ ] IN PROGRESS
[ ] PASSED WITH OPEN ITEMS
[ ] PASSED
```

Open items:

```text
None recorded yet.
```

Final QA date:

```text
Pending.
```

---

### Continue

**Previous:** [Evidence Index](evidence_index.md)
**Documentation Hub:** [README](README.md)
**Next:** [Project Closeout Checklist](project_closeout_checklist.md)

**Related:**
[Evidence Checklist](evidence_checklist.md)
[Dashboard and Observability](dashboard_and_observability.md)
[Streaming and KQL Architecture](streaming_and_kql_architecture.md)
