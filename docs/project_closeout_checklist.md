# Project Closeout Checklist

> **Documentation path:**
> [Documentation Hub](README.md) →
> [Evidence Index](evidence_index.md) →
> [Final Repository QA Checklist](final_repository_qa_checklist.md) →
> **Project Closeout Checklist**

**Project:** `azure-real-time-analytics-pipeline`
**Purpose:** Master checklist for technical, evidence, documentation, Git, Azure, and portfolio closeout
**Status:** Closeout in progress

---

## 1. Closeout Objective

The project should be declared complete only when the implemented Azure Data Engineering MVP is:

* Technically validated
* Evidence-backed
* Public-safe
* Fully documented
* Navigable
* Reproducible
* Versioned
* Cost-reviewed
* Defensible in an interview

The closeout sequence is:

```text
Technical Implementation
        ↓
Documentation
        ↓
Evidence Capture
        ↓
Evidence Review
        ↓
Root README
        ↓
Final Repository QA
        ↓
Git / GitHub Validation
        ↓
Azure Cost / Cleanup Decision
        ↓
Portfolio Roadmap Update
        ↓
Formal Project Closeout
```

Do not reverse this order unnecessarily.

---

# 2. Technical Scope Freeze

Before final closeout, confirm that the MVP scope is frozen.

* [ ] No major new feature remains required.
* [ ] Event Contract v1.2 is the current contract.
* [ ] Mixed RF/FIBER communication support is complete.
* [ ] Event Hubs ingestion path is complete.
* [ ] Raw ingestion layer is complete.
* [ ] Parsed analytical layer is complete.
* [ ] Canonical event layer is complete.
* [ ] Stream-integrity analytics are complete.
* [ ] Timeliness analytics are complete.
* [ ] State reconstruction is complete.
* [ ] Gold serving functions are complete.
* [ ] Dashboard implementation is complete.
* [ ] Representative failure scenarios are complete.
* [ ] Terminal-state behavior is complete.
* [ ] Remaining work is closeout rather than feature development.

If a new idea appears during closeout, classify it as:

```text
Bug / required correction
```

or:

```text
Future improvement
```

Do not expand the MVP simply because another feature would be interesting.

---

# 3. Contract and Schema Closeout

Verify:

* [ ] Event Contract v1.0 remains available where required.
* [ ] Event Contract v1.1 remains available where required.
* [ ] Event Contract v1.2 schema exists.
* [ ] `event_contract_v1_2.md` exists.
* [ ] `contracts/README.md` accurately describes contract evolution.
* [ ] v1.2 communication semantics are documented.
* [ ] RF telemetry semantics are correct.
* [ ] FIBER telemetry semantics are correct.
* [ ] Conditional fiber nullability is correct.
* [ ] No obsolete contract claims remain in current documentation.
* [ ] Producer output validates against the intended schema.

Contract evolution should be understandable as:

```text
v1.0
  ↓
v1.1
  ↓
v1.2
```

without requiring a reader to reconstruct project history from Git commits.

---

# 4. Azure / Event Hubs Validation

Perform a final representative Azure-enabled run.

* [ ] Azure authentication is valid.
* [ ] Event Hubs publisher connects successfully.
* [ ] Event Hub receives events.
* [ ] Raw analytical ingestion receives the run.
* [ ] `simulator_run_id` is visible.
* [ ] Event Hubs metadata is populated.
* [ ] No unexpected ingestion errors occur.
* [ ] Current-run detection works.
* [ ] Final cloud test is documented.

This final run should also be used for evidence capture where possible.

---

# 5. KQL Final Validation

Verify the complete analytical chain:

```text
Raw
 ↓
Parsed
 ↓
Canonical
 ↓
Quality / Timeliness
 ↓
State Reconstruction
 ↓
Gold Serving
```

### KQL files

* [ ] `01_create_tables.kql`
* [ ] `02_transform_functions.kql`
* [ ] `03_update_policies.kql`
* [ ] `04_materialized_views.kql`
* [ ] `05_quality_functions.kql`
* [ ] `06_state_functions.kql`
* [ ] `07_serving_functions.kql`
* [ ] `08_performance_functions.kql`
* [ ] `09_contract_v1_1_migration.kql`
* [ ] `10_contract_v1_2_migration.kql`

### Functional validation

* [ ] Transform functions execute correctly.
* [ ] Update policies populate expected tables.
* [ ] Canonical materialized views behave correctly.
* [ ] Duplicate logical events are canonicalized.
* [ ] Quality functions execute correctly.
* [ ] Performance/timeliness functions execute correctly.
* [ ] State functions execute correctly.
* [ ] Serving functions execute correctly.
* [ ] Current-run wrappers execute correctly.
* [ ] Contract v1.2 fields propagate through the required layers.

---

# 6. Stream Reliability Closeout

Validate representative conditions.

### Integrity

* [ ] Clean baseline produces expected integrity results.
* [ ] Duplicate delivery is detected.
* [ ] Missing/drop behavior is detected.
* [ ] Sequence gaps are detected.
* [ ] Out-of-order behavior is detected where expected.
* [ ] Raw/Canonical reconciliation is correct.

### Timeliness

* [ ] Relative delay metrics are valid.
* [ ] Physical-gap metrics are valid.
* [ ] Cloud-latency metrics are valid.
* [ ] Buffered delivery produces explainable burst behavior.
* [ ] Timeliness degradation does not automatically appear as integrity loss.

Confirm the project can defend:

```text
Integrity ≠ Timeliness
```

---

# 7. State Reconstruction Closeout

Validate:

* [ ] Multiple event families contribute state evidence.
* [ ] Evidence priority behaves correctly.
* [ ] Event-time ordering behaves correctly.
* [ ] State domains resolve independently.
* [ ] Latest telemetry observation is distinct from latest state evidence.
* [ ] Disconnected-state behavior is correct.
* [ ] Last-known observation remains usable.
* [ ] Terminal-state behavior is correct.
* [ ] State remains meaningful after telemetry stops.

Capture at least one strong example of:

```text
Last known observation
        +
newer operational state
```

for evidence and interview defense.

---

# 8. Gold Serving Closeout

Validate:

```text
CurrentFleetOperationalView()
CurrentFleetOperationalSummary()
CurrentFleetMapView()
```

* [ ] Operational view returns expected assets.
* [ ] Fleet summary reconciles with detailed rows.
* [ ] Map view is dashboard-ready.
* [ ] Communication mode is propagated.
* [ ] RF/FIBER metrics are correct.
* [ ] FIBER-specific values are correctly scoped.
* [ ] Telemetry freshness is available.
* [ ] State timestamp is available.
* [ ] Observation timestamp is available.
* [ ] State/telemetry temporal gap remains interpretable.

---

# 9. Failure Scenario Closeout

Validate representative scenarios only.

### Generic transport behavior

* [ ] Extra delay
* [ ] Duplicate
* [ ] Drop
* [ ] Buffer / reconnect

### Communications

* [ ] RF failure
* [ ] FIBER link loss
* [ ] FIBER terminal cut if retained
* [ ] Fiber exhaustion
* [ ] Mixed RF/FIBER fleet

### Terminal state

* [ ] Terminal asset scenario
* [ ] Final state transitions
* [ ] Telemetry termination
* [ ] Last-known-position behavior

The project does **not** need evidence for every configuration file.

Representative evidence is sufficient if it proves the analytical behavior.

---

# 10. Dashboard Closeout

Validate the current dashboard export:

```text
dashboards/rtd-drone-operations.json
```

### Operations page

* [ ] Fleet operational view works.
* [ ] Map works.
* [ ] Availability KPI works.
* [ ] Connectivity KPI works.
* [ ] Mission-completion KPI works.
* [ ] Platform-health KPI works.
* [ ] RF count works.
* [ ] FIBER count works.
* [ ] Communication-mode coverage works.
* [ ] Disconnected asset view works.

### Stream Quality page

* [ ] Integrity metrics work.
* [ ] Timeliness metrics work.
* [ ] Latest run is correct.
* [ ] Event volume is correct.
* [ ] Reconciliation works.
* [ ] Burst visibility works.

### Asset Detail page

* [ ] `_droneId` parameter works.
* [ ] Asset list populates dynamically.
* [ ] Telemetry history works.
* [ ] State-transition history works.
* [ ] Unified event timeline works.
* [ ] Changing the selected asset updates the page.

---

# 11. Core Documentation Closeout

Verify the primary project documentation.

* [ ] `docs/README.md`
* [ ] `architecture_and_scope.md`
* [ ] `implementation_plan.md`
* [ ] `simulator_and_event_model.md`
* [ ] `streaming_and_kql_architecture.md`
* [ ] `stream_quality_and_timeliness.md`
* [ ] `state_reconstruction_and_serving.md`
* [ ] `communications_and_failure_scenarios.md`
* [ ] `dashboard_and_observability.md`
* [ ] `evidence_checklist.md`
* [ ] `evidence_index.md`
* [ ] `final_repository_qa_checklist.md`
* [ ] `project_closeout_checklist.md`

For each document:

* [ ] Markdown renders correctly.
* [ ] Internal links work.
* [ ] Navigation is consistent.
* [ ] File names are correct.
* [ ] Content matches the actual implementation.
* [ ] Azure Data Engineering remains the primary narrative.
* [ ] Simulator details remain supporting context.

---

# 12. Historical Documentation Review

Review existing historical documents such as:

```text
change_summary_v1_1.md
connectivity_fault_v1.md
event_contract_v1_1_rollout.md
local_validation_v1_1.md
```

* [ ] Historical documents remain useful.
* [ ] They are labeled or positioned as historical.
* [ ] They do not conflict with current documentation.
* [ ] Documentation Hub classifies them appropriately.
* [ ] Obsolete documents are removed only when they create confusion.

Preserve useful engineering history without allowing it to dominate the current repo.

---

# 13. Evidence Capture

Follow:

[Evidence Checklist](evidence_checklist.md)

and:

[Evidence Index](evidence_index.md)

Capture evidence in the agreed sequence.

* [ ] Event Hubs ingestion evidence
* [ ] Raw ingestion evidence
* [ ] Parsed-layer evidence
* [ ] Canonical-layer evidence
* [ ] Clean integrity baseline
* [ ] Duplicate evidence
* [ ] Missing/drop evidence
* [ ] Timeliness evidence
* [ ] Burst evidence
* [ ] Raw/Canonical reconciliation
* [ ] State reconstruction
* [ ] Gold serving
* [ ] Terminal-state example
* [ ] Operations dashboard
* [ ] Stream Quality dashboard
* [ ] Asset-detail dashboard

Do not proceed directly to final README closeout until the principal evidence set exists.

---

# 14. Evidence Review

After capture:

* [ ] Every screenshot supports a specific technical claim.
* [ ] No evidence exists only for decoration.
* [ ] Screenshots are readable.
* [ ] Screenshots are cropped appropriately.
* [ ] Filenames follow the naming convention.
* [ ] No credentials are visible.
* [ ] No private connection strings are visible.
* [ ] No personal identifiers are visible.
* [ ] Cloud identifiers have been reviewed.
* [ ] Evidence Index points to real files.
* [ ] Evidence Index status is updated.
* [ ] Strongest Data Engineering evidence appears first.

---

# 15. Root README

The root `README.md` is finalized **after evidence capture**.

The final README should include:

```text
Project title / visual identity
        ↓
Problem
        ↓
Architecture
        ↓
Core Data Engineering capabilities
        ↓
Reliability model
        ↓
State reconstruction
        ↓
Failure engineering
        ↓
Dashboard / observability
        ↓
Evidence
        ↓
Repository structure
        ↓
Design principles
        ↓
Limitations
        ↓
Documentation links
```

Validate:

* [ ] README is recruiter-readable.
* [ ] README is technically accurate.
* [ ] README avoids excessive simulator detail.
* [ ] Azure Event Hubs is visible early.
* [ ] KQL processing is visible early.
* [ ] Stream reliability is clearly explained.
* [ ] Gold serving is explained.
* [ ] Dashboard is positioned as an observability consumer.
* [ ] Evidence is linked.
* [ ] Deep documentation is linked instead of duplicated.
* [ ] README contains no unsupported claims.

---

# 16. Architecture Diagrams

Conceptual diagrams may be added during final documentation polish.

Prioritize only diagrams that strengthen the Data Engineering story.

Recommended candidates:

```text
01 — End-to-End Azure Streaming Architecture
02 — Raw → Parsed → Canonical → Gold Flow
03 — Integrity vs Timeliness
04 — State Reconstruction and Serving
05 — Failure Injection → Azure Observability
06 — Dashboard Analytical Layers
```

* [ ] Final diagram set selected.
* [ ] Diagrams emphasize Data Engineering.
* [ ] Diagram labels match repository terminology.
* [ ] Diagram links work.
* [ ] README uses only the strongest diagrams.
* [ ] Supporting diagrams live under `diagrams/`.

Avoid creating diagrams simply to increase artifact count.

---

# 17. Known Limitations

Create or finalize:

```text
docs/known_limitations.md
```

Document limitations such as applicable MVP boundaries.

Potential categories:

```text
Synthetic source domain
Portfolio-scale throughput
No production SLA
No multi-region DR
No enterprise security hardening
No enterprise retention strategy
Limited alerting / automation
No production workload guarantee
```

Only include limitations that accurately describe the final implementation.

* [ ] Known limitations are explicit.
* [ ] Limitations do not undermine implemented capabilities.
* [ ] No production-grade claim exceeds actual scope.

---

# 18. Future Improvements

Create or finalize:

```text
docs/future_improvements.md
```

Future improvements may include areas such as:

* More advanced windowing

* Larger-scale performance testing

* Additional alerting

* Automated deployment

* Infrastructure as Code

* Schema Registry

* Expanded observability

* Additional streaming consumers

* Stronger governance

* Long-term retention

* Automated data-quality thresholds

* [ ] Improvements are clearly future work.

* [ ] Future features are not described as implemented.

* [ ] Improvements connect naturally to the MVP.

---

# 19. Repository Public-Safety Review

Perform the complete safety review defined in:

[Final Repository QA Checklist](final_repository_qa_checklist.md)

Verify:

* [ ] No secrets
* [ ] No connection strings
* [ ] No SAS tokens
* [ ] No access keys
* [ ] No passwords
* [ ] No bearer tokens
* [ ] No client secrets
* [ ] No unintended personal information
* [ ] Dashboard export reviewed
* [ ] Evidence reviewed
* [ ] YAML configuration reviewed
* [ ] Git history reviewed if necessary

If a credential was ever committed:

```text
Remove from repository
+
Rotate credential
+
Review Git history
```

---

# 20. Git Closeout

Execute final Git validation.

```bash
git status
git diff
git branch -vv
git log --oneline -n 10
```

Verify:

* [ ] Working tree is clean.
* [ ] Intended files are tracked.
* [ ] Unwanted files are ignored.
* [ ] Final documentation is committed.
* [ ] Final evidence is committed.
* [ ] Dashboard export is committed.
* [ ] KQL files are committed.
* [ ] Contracts are committed.
* [ ] Root README is committed.
* [ ] Local branch is synchronized.
* [ ] Remote repository contains the final version.

---

# 21. GitHub Public QA

Review the repository directly in GitHub.

Do not rely only on VS Code rendering.

Verify:

* [ ] Root README renders correctly.
* [ ] Hero/banner renders correctly if used.
* [ ] Architecture diagrams render.
* [ ] Documentation links work.
* [ ] Documentation Hub works.
* [ ] Evidence images render.
* [ ] Evidence links work.
* [ ] Contract links work.
* [ ] Dashboard artifact is visible.
* [ ] Repository folders are understandable.
* [ ] No broken Markdown blocks exist.
* [ ] No accidental sensitive information is visible.
* [ ] Mobile/narrow-width rendering remains acceptable where practical.

---

# 22. Azure Cost Review

Before formal closeout:

* [ ] Identify resources still running.
* [ ] Identify resources with continuous cost.
* [ ] Review Event Hubs cost.
* [ ] Review analytical/Fabric/Kusto-related cost if applicable.
* [ ] Review storage cost.
* [ ] Review networking cost if applicable.
* [ ] Decide what remains active for demos.
* [ ] Decide what can be disabled.
* [ ] Decide what can be deleted.
* [ ] Record intentional resource-retention decisions.

The repository does not require permanently running infrastructure to remain portfolio-valid.

---

# 23. Azure Cleanup

After all required cloud evidence has been captured:

* [ ] Export final dashboard artifact.
* [ ] Capture final Event Hubs evidence.
* [ ] Capture final KQL evidence.
* [ ] Capture final dashboard evidence.
* [ ] Confirm no additional cloud screenshots are required.
* [ ] Disable unnecessary components.
* [ ] Delete unnecessary resources where appropriate.
* [ ] Verify no unintended recurring charges remain.
* [ ] Document resources intentionally preserved.

Do **not** delete resources before evidence capture is complete.

---

# 24. Portfolio Positioning

Create or finalize:

```text
docs/portfolio_positioning.md
```

The primary professional narrative should emphasize:

```text
Azure real-time ingestion
+
KQL analytical engineering
+
stream reliability
+
state reconstruction
+
Gold serving
+
operational observability
```

The synthetic drone domain remains secondary.

Potential portfolio statement:

```text
Built an Azure real-time analytics pipeline that ingests synthetic
telemetry through Event Hubs and uses KQL to implement Raw, Parsed,
Canonical, stream-quality, state-reconstruction, and Gold serving
layers. The project models imperfect delivery conditions including
duplicates, missing events, delayed arrivals, buffering, mixed
communication modes, and terminal sources, and exposes both
operational state and stream health through a real-time dashboard.
```

This statement should be reviewed again after final evidence and README QA.

---

# 25. Private Portfolio Roadmap Update

After formal technical closeout, update the private:

```text
azure-data-engineering-portfolio-roadmap
```

The project status should change from:

```text
Future / active project
```

to:

```text
Completed / portfolio-ready MVP closed
```

Update relevant roadmap areas:

* [ ] Master snapshot
* [ ] Project sequence
* [ ] Azure training roadmap
* [ ] Capability matrix
* [ ] Portfolio narrative
* [ ] Current next action
* [ ] Next-project recommendation

Real-time analytics should then move from a capability gap to a demonstrated capability.

---

# 26. CV / LinkedIn Boundary

CV and LinkedIn work are **not required to close the technical project**.

* [ ] Technical repository closed first.
* [ ] Roadmap updated.
* [ ] Portfolio statement finalized.
* [ ] CV update deferred to dedicated workstream.
* [ ] LinkedIn update deferred to dedicated workstream.
* [ ] GitHub profile branding deferred unless explicitly included in closeout.

This protects the current rule:

```text
Finish technical projects first.
Branding comes afterward.
```

---

# 27. Interview Defense Readiness

Before considering the project fully portfolio-ready, be able to explain:

* [ ] Why Event Hubs was used.
* [ ] Why Raw data is preserved.
* [ ] Why Parsed and Canonical layers are separate.
* [ ] Why canonicalization is required.
* [ ] Why physical delivery differs from logical event identity.
* [ ] Why integrity differs from timeliness.
* [ ] Why event time differs from ingestion time.
* [ ] How missing events are detected.
* [ ] How duplicates are detected.
* [ ] How Raw and Canonical layers reconcile.
* [ ] Why state reconstruction is required.
* [ ] Why latest observation differs from latest state.
* [ ] Why Gold serving functions exist.
* [ ] How RF/FIBER context propagates analytically.
* [ ] Why failure injection exists.
* [ ] What the dashboard proves.
* [ ] What the project does **not** claim to be.

Interview readiness does not require memorizing every KQL statement.

It requires understanding the architecture and engineering decisions.

---

# 28. Final Acceptance Criteria

The project can be declared:

```text
Completed / portfolio-ready MVP closed
```

only when the following are true:

* [ ] Technical implementation is frozen.
* [ ] Azure ingestion has been revalidated.
* [ ] KQL chain has been validated.
* [ ] Stream reliability has been validated.
* [ ] State reconstruction has been validated.
* [ ] Gold serving has been validated.
* [ ] Dashboard has been validated.
* [ ] Evidence capture is complete.
* [ ] Evidence Index is complete.
* [ ] Root README is final.
* [ ] Documentation navigation is complete.
* [ ] Known limitations are documented.
* [ ] Future improvements are documented.
* [ ] Final Repository QA has passed.
* [ ] GitHub public QA has passed.
* [ ] Public-safety review has passed.
* [ ] Cost/cleanup decision is complete.
* [ ] Private roadmap has been updated.

---

# 29. Formal Closeout Record

When all acceptance criteria are satisfied, record:

```text
Project:
azure-real-time-analytics-pipeline

Final status:
Completed / portfolio-ready MVP closed

Technical closeout date:
Pending

Evidence status:
Pending

Repository QA:
Pending

Azure cleanup / retention decision:
Pending

Private roadmap updated:
Pending
```

---

# 30. Final Project Principle

The project should ultimately demonstrate:

```text
Real-time data is only valuable
if its state and delivery quality
can be trusted.
```

The synthetic domain creates the conditions.

Azure Event Hubs transports the stream.

KQL transforms, reconciles, validates, and reconstructs it.

Gold serving exposes trustworthy analytical outputs.

The dashboard makes both operational state and data-system health observable.

That is the project.

---

### Navigation

**Previous:** [Final Repository QA Checklist](final_repository_qa_checklist.md)
**Documentation Hub:** [README](README.md)

**Related:**
[Evidence Checklist](evidence_checklist.md)
[Evidence Index](evidence_index.md)
[Dashboard and Observability](dashboard_and_observability.md)
[Architecture and Scope](architecture_and_scope.md)
