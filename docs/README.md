<p align="center">
  <a href="../README.md">Home</a> |
  <a href="architecture_and_scope.md">Architecture</a> |
  <a href="evidence_index.md">Evidence</a> |
  <a href="../dashboards/rtd-drone-operations.json">Dashboard</a> |
  <a href="architecture_and_scope.md">Next →</a>
</p>

---

# Documentation

**Project:** `azure-real-time-analytics-pipeline`
**Primary focus:** Azure Real-Time Data Engineering — Event Hubs, KQL, stream reliability, state reconstruction, analytical serving, and observability.

This folder contains the technical documentation for the project.

The synthetic drone domain is used as a controlled event source and failure-injection environment.

The primary engineering focus is the Azure streaming architecture and the analytical processing required to transform imperfect event delivery into trustworthy operational data.

---

## Start Here

For a complete project overview, begin with:

### 1. [Architecture and Scope](architecture_and_scope.md)

Defines:

* Project mission
* Data Engineering problem
* Azure architecture
* MVP scope
* Design principles
* Success criteria

Then continue with:

### 2. [Implementation Plan](implementation_plan.md)

Explains how the project evolved from initial event generation into a complete real-time analytics pipeline.

---

# Core Data Engineering

These documents describe the main Azure analytical architecture.

### [Streaming and KQL Architecture](streaming_and_kql_architecture.md)

The main technical overview.

Covers:

```text
Azure Event Hubs
        ↓
Raw ingestion
        ↓
KQL transformations
        ↓
Canonical events
        ↓
Quality / State / Timeliness
        ↓
Gold serving
        ↓
Real-time dashboard
```

Recommended as the first technical deep dive.

---

### [Stream Quality and Timeliness](stream_quality_and_timeliness.md)

Focuses on stream reliability.

Topics include:

* Missing sequences
* Duplicate deliveries
* Sequence gaps
* Out-of-order events
* Raw-to-canonical reconciliation
* Event time vs arrival time
* Cloud latency
* Buffered delivery
* Arrival bursts

---

### [State Reconstruction and Serving](state_reconstruction_and_serving.md)

Explains how canonical events become operational state.

Topics include:

* State evidence
* Evidence priority
* Latest-state reconstruction
* Latest telemetry observation
* State vs observation
* Gold serving functions
* Fleet operational views
* Dashboard-facing analytical contracts

---

### [Dashboard and Observability](dashboard_and_observability.md)

Documents the presentation and operational visibility layer.

Topics include:

* Fleet KPIs
* Maps
* Drone-level analysis
* Unified event timelines
* Stream integrity
* Timeliness
* Communications
* Reconciliation
* Dashboard design principles

---

# Reliability and Failure Engineering

### [Communications and Failure Scenarios](communications_and_failure_scenarios.md)

Describes the controlled failure scenarios used to exercise the Azure streaming architecture.

Examples include:

```text
RF degradation
Jamming
Communication loss
Buffered reconnect
Dropped events
Duplicate events
Fiber link loss
Fiber exhaustion
Mixed RF / FIBER fleets
Terminal asset behavior
```

These scenarios exist primarily to test downstream Data Engineering behavior under imperfect delivery conditions.

---

# Supporting Event Producer

### [Simulator and Event Model](simulator_and_event_model.md)

Documents the synthetic event producer used by the project.

This document explains:

* Simulation runs
* Fleet and asset identity
* Event families
* Source sequence numbers
* Ground truth
* Generated events
* Transport behavior
* Local evidence
* Event Hubs publishing

The simulator is supporting infrastructure.

The Azure real-time analytical pipeline remains the primary project focus.

---


# Conceptual Visual Guides

Conceptual visuals live under `../diagrams/` and explain the architecture without replacing execution evidence.

| Visual | Purpose |
|---|---|
| [01 — End-to-End Streaming](../diagrams/01_end_to_end_streaming.png) | Complete source → Event Hubs → KQL → serving → dashboard story |
| [02 — Stream Reliability](../diagrams/02_stream_reliability.png) | Physical delivery vs logical identity; integrity vs timeliness |
| [03 — State Reconstruction](../diagrams/03_state_reconstruction.png) | Multi-source evidence, precedence, current state, latest observation, and Gold serving |
| [04 — Failure to Observability](../diagrams/04_failure_to_observability.png) | Controlled failure → stream effect → KQL detection → operational interpretation |
| [05 — Operational Command Center](../diagrams/05_operational_command_center.png) | Conceptual value of trusted real-time operational analytics |

```text
diagrams/ = conceptual communication
evidence/ = implementation proof
```

---

# Event Contracts

Versioned producer / consumer contracts are maintained separately under:

### [Contracts](../contracts/README.md)

Current contract evolution:

```text
v1.0
  ↓
v1.1
  ↓
v1.2
```

Contract documentation:

* [Event Contract v1.0](../contracts/event_contract_v1_0.md)
* [Event Contract v1.1](../contracts/event_contract_v1_1.md)
* [Event Contract v1.2](../contracts/event_contract_v1_2.md)

The JSON Schemas in the same directory remain the normative structural definitions.

---

# Validation and Evidence

### [Evidence Checklist](evidence_checklist.md)

Defines the evidence required to support the main public project claims.

### [Evidence Index](evidence_index.md)

Provides the final navigation index between technical claims and captured project evidence.

Evidence should demonstrate:

```text
Architecture
Ingestion
Canonicalization
Stream integrity
Timeliness
State reconstruction
Failure scenarios
Serving
Dashboard behavior
```

---

# Project Boundaries

### [Known Limitations](known_limitations.md)

Documents MVP limitations explicitly.

The project should demonstrate real engineering capability without claiming production characteristics that were not implemented.

### [Future Improvements](future_improvements.md)

Documents logical extensions beyond the current portfolio-ready MVP.

---

# Repository and Closeout

### [Public Repository Structure](public_repo_structure.md)

Explains the role of the main repository folders and public-facing artifacts.

### [Final Repository QA Checklist](final_repository_qa_checklist.md)

Validates the repository before public closeout.

### [Project Closeout Checklist](project_closeout_checklist.md)

Tracks technical, documentation, evidence, Git, and cost-related closeout activities.

### [Portfolio Positioning](portfolio_positioning.md)

Summarizes how the project should be explained and defended as an Azure Data Engineering portfolio project.

### [Roadmap Update Notes](roadmap_update_notes.md)

Contains the updates required for the private Azure portfolio roadmap after formal project closeout.

---

# Implementation History

The following documents are retained because they capture important stages in the project's technical evolution.

### [v1.1 Change Summary](change_summary_v1_1.md)

Documents the principal changes introduced during the v1.1 evolution.

### [Connectivity Fault Model](connectivity_fault_v1.md)

Documents the earlier connectivity-failure implementation.

### [Event Contract v1.1 Rollout](event_contract_v1_1_rollout.md)

Records the rollout strategy for Event Contract v1.1.

### [Local Validation v1.1](local_validation_v1_1.md)

Preserves validation evidence and implementation notes from the v1.1 stage.

These documents are historical implementation records rather than the primary architectural entry points.

---

# Recommended Reading Paths

## Recruiter / Portfolio Review

```text
Root README
    ↓
Architecture and Scope
    ↓
Streaming and KQL Architecture
    ↓
Evidence
```

Focus:

```text
What was built?
Why does it matter?
What Azure capabilities does it demonstrate?
Can the claims be proven?
```

---

## Data Engineering Review

```text
Architecture and Scope
        ↓
Streaming and KQL Architecture
        ↓
Stream Quality and Timeliness
        ↓
State Reconstruction and Serving
        ↓
Dashboard and Observability
```

Focus:

```text
How does data move?
How is it normalized?
How is reliability measured?
How is operational state reconstructed?
How is analytical logic exposed?
```

---

## Reliability / Failure Review

```text
Streaming and KQL Architecture
        ↓
Communications and Failure Scenarios
        ↓
Stream Quality and Timeliness
        ↓
State Reconstruction and Serving
```

Focus:

```text
What happens when delivery is imperfect?
How are missing, duplicate, delayed, or reordered events detected?
Can useful state still be reconstructed?
```

---

## Interview Defense

```text
Architecture and Scope
        ↓
Streaming and KQL Architecture
        ↓
Stream Quality and Timeliness
        ↓
State Reconstruction and Serving
        ↓
Known Limitations
```

Focus on explaining the engineering decisions rather than memorizing implementation syntax.

---

# Conceptual Documentation Map

```text
                         README.md
                             │
                             ↓
                  docs/architecture_and_scope.md
                             │
                 ┌───────────┴───────────┐
                 ↓                       ↓
        Implementation Plan      Streaming & KQL
                                         │
                         ┌───────────────┼───────────────┐
                         ↓               ↓               ↓
                  Stream Quality      State &        Communications
                  & Timeliness        Serving         & Failures
                         │               │               │
                         └───────────────┼───────────────┘
                                         ↓
                              Dashboard & Observability
                                         │
                                         ↓
                                Evidence / Validation
                                         │
                                         ↓
                                      Closeout
```

Conceptual architecture visuals complement this navigation under the project's `diagrams/` directory, while execution screenshots remain separated under `evidence/`.

---

# Documentation Principle

The repository documentation follows one central rule:

```text
Each document should answer one major engineering question.
```

The root README tells the project story.

This documentation hub controls navigation.

Specialized technical documents provide depth.

The implementation itself remains in the project's code, KQL, configuration, contract, dashboard, and test artifacts.

---

<p align="center">
  <a href="../README.md">Home</a> |
  <a href="architecture_and_scope.md">Architecture</a> |
  <a href="evidence_index.md">Evidence</a> |
  <a href="../dashboards/rtd-drone-operations.json">Dashboard</a> |
  <a href="architecture_and_scope.md">Next →</a>
</p>
