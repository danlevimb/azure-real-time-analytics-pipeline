<p align="center">
  <a href="evidence_index.md">← Back</a> |
  <a href="../README.md">Home</a> |
  <a href="README.md">Documentation</a> |
  <a href="evidence_index.md">Evidence</a> |
  <a href="future_improvements.md">Next →</a>
</p>

---

# Known Limitations


**Project:** `azure-real-time-analytics-pipeline`
**Scope:** Portfolio-ready Azure Real-Time Data Engineering MVP

---

## 1. Purpose

This project demonstrates a complete real-time Data Engineering flow using Azure Event Hubs, KQL analytical processing, stream-quality analysis, state reconstruction, Gold serving, and operational observability.

It is intentionally implemented as a **portfolio MVP**, not as a production-certified enterprise platform.

The limitations below define that boundary explicitly.

---

# 2. Synthetic Data Source

The project uses a custom synthetic telemetry producer.

This provides deterministic:

* Event generation
* Failure injection
* Sequence control
* Reproducible scenarios
* Ground-truth validation

However, the producer does not represent integration with actual field hardware or an external production telemetry platform.

The synthetic domain exists to exercise the streaming architecture.

---

# 3. Domain Simulation Fidelity

The project does not attempt to provide high-fidelity simulation of:

* Aircraft physics
* RF propagation
* Fiber-optic engineering
* Network protocols
* Battlefield communication systems
* Real navigation systems

Communication and operational scenarios exist only to create meaningful event-stream conditions.

For this project:

```text
Domain behavior
      ↓
Controlled data conditions
      ↓
Data Engineering validation
```

The Data Engineering behavior is the primary objective.

---

# 4. Portfolio-Scale Workload

The project has been tested with controlled fleet sizes and repeatable load scenarios, including higher-volume executions.

However, these tests do not represent:

```text
enterprise-scale certification
```

or:

```text
production capacity guarantees
```

The project does not claim validated performance for:

* Millions of concurrent producers
* Sustained enterprise-scale throughput
* Very large geographic deployments
* Multi-day continuous high-volume workloads
* Formal capacity-planning targets

Load testing demonstrates architecture behavior at portfolio scale.

---

# 5. No Formal SLA or SLO

The project measures characteristics such as:

```text
stream integrity
latency
arrival gaps
burst behavior
reconciliation
```

but does not define or guarantee formal production:

```text
SLA
SLO
SLI
```

No contractual availability, latency, freshness, or recovery objective is claimed.

---

# 6. Single Primary Cloud Ingestion Path

The implemented architecture demonstrates Azure Event Hubs as the primary cloud streaming entry point.

The MVP does not implement:

* Multi-region Event Hubs failover
* Active-active ingestion
* Active-passive disaster recovery
* Cross-region replication strategy
* Automated regional failover

The project focuses on stream processing and analytical reliability after ingestion.

---

# 7. Limited Disaster Recovery Scope

Disaster recovery for the complete Azure real-time architecture is outside the MVP scope.

The project does not currently demonstrate:

* Regional recovery runbooks
* Automated resource recreation
* Replicated analytical stores
* Defined RPO/RTO objectives
* Cross-region dashboard recovery

These would be required for a production-critical platform.

---

# 8. Infrastructure Provisioning

The current repository focuses on application, event-contract, KQL, simulation, dashboard, and evidence artifacts.

Azure infrastructure provisioning is not currently represented as a complete Infrastructure as Code deployment.

The project therefore does not claim:

```text
one-command environment provisioning
```

or full environment recreation through Bicep or Terraform.

Resource configuration remains part of the implemented environment rather than a fully automated deployment layer.

---

# 9. Limited CI/CD Automation

The MVP is version-controlled, but the complete Azure analytical deployment lifecycle is not automated through a production CI/CD pipeline.

The project does not currently demonstrate automated deployment of:

* Event Hubs resources
* KQL objects
* Dashboard artifacts
* Environment-specific configuration
* Schema migrations across multiple environments

Versioned implementation artifacts exist, but deployment automation remains future work.

---

# 10. Environment Separation

The project does not implement a complete enterprise:

```text
DEV
TEST
UAT
PROD
```

environment strategy.

There is no formal promotion workflow between isolated environments.

The MVP primarily validates technical behavior within a controlled development / portfolio environment.

---

# 11. Security Hardening

The project follows public-repository safety practices and avoids intentionally exposing credentials.

However, it does not claim a complete enterprise security implementation covering:

* Private endpoints
* VNet isolation
* Enterprise firewall design
* Customer-managed encryption keys
* Full RBAC governance model
* Privileged Identity Management
* Security Center / Defender integration
* Formal secrets rotation automation
* Enterprise identity lifecycle controls

Security architecture is not the central capability demonstrated by this project.

---

# 12. Schema Governance

Event contracts are explicitly versioned:

```text
v1.0
 ↓
v1.1
 ↓
v1.2
```

and schema evolution is propagated through KQL migration scripts.

However, the MVP does not implement a centralized enterprise schema registry or automated compatibility service.

Contract governance currently relies on:

```text
versioned JSON Schema
+
repository documentation
+
tests
+
controlled KQL migrations
```

---

# 13. Long-Term Retention

The project focuses on near-real-time analytics.

It does not define a complete long-term data-retention architecture for:

* Historical telemetry archives
* Regulatory retention
* Cold storage
* Multi-year analytics
* Data lifecycle policies
* Tiered storage optimization

Long-term historical persistence would require a separate retention and serving strategy.

---

# 14. Replay and Recovery

The system preserves useful local execution evidence and raw analytical data.

However, the MVP does not implement a complete production-grade replay platform capable of automatically:

```text
re-reading historical source streams
        ↓
reprocessing selected windows
        ↓
rebuilding downstream state
```

at enterprise scale.

Replay and backfill orchestration remain outside the current scope.

---

# 15. Alerting and Automated Response

The project exposes:

```text
stream integrity
stream timeliness
state
freshness
reconciliation
```

through analytical functions and dashboard observability.

However, it does not implement a complete automated alerting and incident-response platform.

Examples not included as full production capabilities:

* Automatic alerts on missing-event thresholds
* Latency SLO breach alerts
* Automated incident creation
* Pager / on-call integration
* Automated remediation
* Runbook automation

The current focus is **detection and observability**.

---

# 16. Data Quality Threshold Management

Quality metrics are implemented, but thresholds are not managed through a centralized policy framework.

For example, the system can measure:

```text
P95 latency
missing sequences
duplicates
physical gaps
```

but the MVP does not implement centrally configured rules such as:

```text
P95 latency > threshold
        ↓
warning

MissingSequences > 0
        ↓
critical alert
```

Threshold-driven operational policy remains future work.

---

# 17. Dashboard Scope

The dashboard is designed as an operational and analytical demonstration surface.

It is not intended to replace an enterprise monitoring platform.

Current dashboard capabilities focus on:

* Operational state
* Stream integrity
* Timeliness
* Reconciliation
* Communication context
* Asset-level investigation

The MVP does not claim:

* Enterprise BI governance
* Large-scale role-based dashboard distribution
* Formal reporting certification
* Multi-tenant dashboard security
* Executive reporting workflows

---

# 18. Current-Run Abstraction

Operational convenience functions use the most recently observed simulator run.

This works well for controlled portfolio executions.

A production system with multiple concurrent workloads would require more explicit workload context, partitioning, tenancy, or selection logic rather than assuming one operationally relevant latest run.

---

# 19. Failure Model Scope

Failure scenarios are deterministic and intentionally controlled.

They are designed to exercise the analytical platform.

They do not represent an exhaustive model of all possible distributed-system failures.

The MVP focuses on representative conditions such as:

```text
delay
drop
duplicate
buffer
reconnect
communication loss
terminal source
```

These scenarios are sufficient to demonstrate stream-reliability reasoning without attempting to model every production failure mode.

---

# 20. Observability Scope

The project provides strong **data observability**.

It does not implement complete infrastructure observability for every Azure component.

The distinction is:

```text
Implemented strongly:
Data stream health
Event integrity
Timeliness
State consistency
Reconciliation

Not implemented comprehensively:
CPU / memory monitoring
Platform infrastructure telemetry
Network diagnostics
Azure resource health automation
Enterprise logging aggregation
```

The focus remains the reliability of the data product.

---

# 21. Cost Optimization

The project is intentionally cost-aware and uses controlled execution windows.

However, it does not represent a formal FinOps implementation.

The MVP does not include:

* Automated budget enforcement
* Chargeback / showback
* Cost allocation by producer
* Automated resource shutdown policies
* Cost anomaly detection
* Long-term cost forecasting

Cost control is operationally considered but not itself a major project feature.

---

# 22. Production Readiness Boundary

The project demonstrates:

```text
real-time ingestion
+
analytical processing
+
stream reliability
+
state reconstruction
+
serving
+
observability
```

It does **not** claim:

```text
enterprise production certification
```

A production deployment would require additional work across:

```text
security
deployment automation
DR
capacity planning
SLOs
alerting
governance
retention
operational ownership
```

---

# 23. What the MVP Does Prove

These limitations do not reduce the implemented technical objective.

The project demonstrates the ability to design and implement an Azure real-time Data Engineering system that:

```text
Receives streaming data through Event Hubs

Preserves Raw transport evidence

Transforms events into typed analytical structures

Canonicalizes logical event identity

Detects missing, duplicate, delayed, and reordered data

Separates stream integrity from stream timeliness

Reconstructs operational state from event evidence

Exposes reusable Gold serving interfaces

Makes data-system health observable through a dashboard
```

That is the intended scope of the project.

---

<p align="center">
  <a href="evidence_index.md">← Back</a> |
  <a href="../README.md">Home</a> |
  <a href="README.md">Documentation</a> |
  <a href="evidence_index.md">Evidence</a> |
  <a href="future_improvements.md">Next →</a>
</p>
