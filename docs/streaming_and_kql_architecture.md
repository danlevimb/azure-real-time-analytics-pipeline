# Streaming and KQL Architecture

**Project:** `azure-real-time-analytics-pipeline`
**Component:** Real-time ingestion, canonicalization, state reconstruction, quality analytics, and serving
**Status:** Implemented / portfolio documentation closeout

---

## 1. Purpose

This document describes how events move through the analytical side of the project after leaving the simulator.

The pipeline is designed to preserve multiple interpretations of the stream rather than collapsing ingestion, normalization, state reconstruction, and presentation into a single query layer.

The main analytical flow is:

```text
Synthetic Drone Simulator
        ↓
Azure Event Hubs
        ↓
RawDroneEvents
        ↓
Parsed event tables
        ↓
Canonical event views
        ↓
Quality / State / Performance logic
        ↓
Gold serving functions
        ↓
Real-time dashboard
```

Each layer answers a different engineering question.

---

## 2. Architectural Principle

The analytical model intentionally separates:

```text
What arrived?
```

from:

```text
What does the event mean?
```

from:

```text
Is the stream structurally trustworthy?
```

from:

```text
What is the latest operational state?
```

from:

```text
What should the dashboard consume?
```

This separation reduces coupling between ingestion, event interpretation, state reconstruction, and visualization.

---

## 3. Logical Data Layers

The project follows a medallion-inspired logical organization.

```text
Bronze / Raw
    ↓
Silver / Parsed
    ↓
Silver / Canonical
    ↓
Gold / Quality + State + Observation
    ↓
Gold / Serving
    ↓
Dashboard
```

These are analytical responsibilities rather than independent storage systems.

---

# 4. Bronze — Raw Event Layer

The raw layer is represented by:

```text
RawDroneEvents
```

This is the first analytical representation of events arriving from the cloud stream.

Its responsibility is to preserve the producer contract and Event Hubs delivery metadata with minimal interpretation.

---

## 4.1 Raw Event Structure

`RawDroneEvents` contains the common event envelope:

```text
schema_version
event_id
event_type
event_time
drone_id
battalion_id
mission_id
source_sequence_number
source_type
source_gateway_id
simulation
payload
```

and Event Hubs metadata such as:

```text
eh_enqueued_time
eh_sequence_number
eh_offset
```

The source-specific nested structures remain available through:

```text
simulation
payload
```

as dynamic values.

---

## 4.2 Why Raw Is Preserved

The raw layer provides evidence of what the cloud ingestion path actually received.

It supports questions such as:

```text
Did this event reach the analytical platform?

Was it received more than once?

What schema version arrived?

When was it enqueued?

What Event Hubs metadata was attached?

Does the original payload differ from the parsed representation?
```

The raw layer therefore remains useful even after higher analytical layers exist.

---

# 5. Silver — Transform Layer

Raw JSON events are converted into typed analytical structures through reusable transform functions.

The transform layer contains separate logic for each event family.

Examples include:

```text
TransformTelemetry()
TransformStateTransitions()
TransformMaintenanceEvents()
TransformStatusConfirmations()
```

The functions live conceptually under:

```text
Silver/Transforms
```

---

## 5.1 Telemetry Transformation

`TransformTelemetry()` filters:

```text
event_type == "telemetry"
```

and extracts typed attributes from the raw event.

Examples include:

```text
event_time
drone_id
mission_id
source_sequence_number
simulator_run_id

latitude
longitude
altitude_m

ground_speed_mps
vertical_speed_mps
heading_deg

battery_pct
platform_health

connection_state
communication_mode

asset_state
mission_status
mission_phase

optic_fiber_remaining_m
```

The transform also captures:

```text
bronze_ingested_at
```

using ingestion time.

This creates an analytical timestamp independent from producer `event_time`.

---

## 5.2 Multiple Time Perspectives

The architecture intentionally retains different time concepts.

### Event Time

```text
event_time
```

When the simulated event occurred.

### Event Hubs Enqueue Time

```text
eh_enqueued_time
```

When Event Hubs observed the event.

### Analytical Ingestion Time

```text
bronze_ingested_at
```

When the parsed event entered the analytical processing layer.

These timestamps allow the platform to distinguish:

```text
Event semantics
vs
Transport arrival
vs
Analytical ingestion
```

This distinction becomes important for late-event and timeliness analysis.

---

# 6. Parsed Event Tables

Each event family has a structured table.

The implemented model includes:

```text
TelemetryParsed
StateTransitionsParsed
MaintenanceEventsParsed
StatusConfirmationsParsed
```

The purpose of these tables is not simply performance.

They establish typed event-family boundaries.

Instead of every downstream query repeatedly parsing arbitrary nested JSON, analytical logic can operate against stable typed columns.

---

# 7. Update Policies

Transform functions are connected to the ingestion path through update policies.

Conceptually:

```text
RawDroneEvents
        │
        ├── telemetry
        │      ↓
        │  TelemetryParsed
        │
        ├── state_transition
        │      ↓
        │  StateTransitionsParsed
        │
        ├── maintenance_event
        │      ↓
        │  MaintenanceEventsParsed
        │
        └── status_confirmation
               ↓
           StatusConfirmationsParsed
```

This creates event-family-specific structured streams without requiring dashboard queries to perform raw parsing.

---

# 8. Silver — Canonical Layer

Parsed rows do not automatically represent unique logical events.

Transport scenarios may intentionally create duplicate physical deliveries.

The canonical layer therefore operates on logical event identity.

For telemetry:

```text
TelemetryCanonical
```

is implemented as a materialized view over:

```text
TelemetryParsed
```

using:

```kusto
summarize take_any(*) by event_id
```

The design goal is:

```text
One canonical row per logical event_id
```

---

## 8.1 Physical Delivery vs Logical Event

This distinction is central to the project.

Suppose one logical event is delivered twice:

```text
event_id = E42

Raw:
E42
E42

Canonical:
E42
```

The raw layer preserves both physical deliveries.

The canonical layer represents one logical event.

Therefore:

```text
Raw count
```

and:

```text
Canonical count
```

have intentionally different meanings.

---

## 8.2 Canonical Event Families

The architecture applies the same canonical concept to the relevant event families.

Examples include:

```text
TelemetryCanonical
StateTransitionsCanonical
MaintenanceEventsCanonical
StatusConfirmationsCanonical
```

Canonical data becomes the preferred input for state reconstruction and operational serving.

Raw remains authoritative for delivery-level investigation.

---

# 9. Why Canonicalization Matters

Without canonicalization, a duplicated physical delivery could affect:

* Event counts
* Latest-state queries
* Timelines
* KPI calculations
* State reconstruction
* Dashboard results

By preserving both raw and canonical layers, the system can simultaneously answer:

```text
How many physical events arrived?
```

and:

```text
How many unique logical events exist?
```

That distinction is necessary for real stream-quality analysis.

---

# 10. Gold — Stream Quality Layer

Quality functions evaluate whether the stream behaves as expected.

The quality layer includes concepts such as:

```text
Expected sequences
Observed sequences
Missing sequences
Duplicate deliveries
Sequence gaps
Out-of-order behavior
Raw-to-canonical reconciliation
Event Hubs metadata completeness
```

The sequence model is especially useful because `source_sequence_number` is generated by the producer independently for each drone.

---

## 10.1 Sequence-Based Integrity

Conceptually:

```text
Expected producer sequence

1 2 3 4 5 6 7
```

Observed cloud stream:

```text
1 2 3 5 5 6 7
```

This reveals two different conditions:

```text
Missing:
4

Duplicate:
5
```

The event stream itself therefore contains enough information to perform integrity analysis without relying solely on row counts.

---

# 11. Raw-to-Canonical Reconciliation

The architecture also compares raw and canonical representations.

For each event family, analytical queries can evaluate:

```text
Raw rows
Raw unique event IDs
Raw duplicates

Canonical rows
Canonical unique event IDs

Difference
Reconciliation status
```

Expected healthy behavior is approximately:

```text
Raw unique event IDs
        =
Canonical unique event IDs
```

while:

```text
Raw rows
```

may be greater if transport duplicates occurred.

This provides evidence that canonicalization removed duplicate physical deliveries without losing logical events.

---

# 12. Gold — State Evidence Layer

Current operational state cannot always be derived safely from the latest telemetry row alone.

The project therefore creates a normalized state-evidence model.

The central function is conceptually:

```text
StateEvidence(RunId)
```

It combines state assertions from multiple canonical sources.

---

## 12.1 State Evidence Sources

State may be derived from:

```text
StatusConfirmationsCanonical
StateTransitionsCanonical
TelemetryCanonical
```

and limited controlled inference where required.

These are normalized into a common structure containing concepts such as:

```text
drone_id
state_domain
state_value
event_time
source_sequence_number
evidence_type
evidence_rank
evidence_event_id
reason_code
```

---

## 12.2 Evidence Ranking

Different evidence types have different semantic authority.

The implemented state model uses an evidence ranking concept.

Conceptually:

```text
Status confirmation
        ↓ highest authority

State transition

Telemetry snapshot

Controlled inference
        ↓ lowest authority
```

This allows state reconstruction to prefer explicit domain events over weaker evidence when timestamps compete.

---

# 13. Latest State Evidence

The function:

```text
LatestStateEvidence(RunId)
```

selects the latest evidence independently by:

```text
drone_id
+
state_domain
```

Conceptually:

```text
DRN-001
│
├── asset_state
├── connection_state
├── mission_phase
├── mission_status
└── platform_health
```

Each state domain is resolved independently.

---

## 13.1 Selection Logic

Evidence selection considers:

```text
event_time
evidence_rank
source_sequence_number
```

rather than simply assuming:

```text
last row ingested = current truth
```

This distinction protects state reconstruction from transport timing effects.

---

# 14. Current Fleet State

`FleetCurrentState(RunId)` pivots the resolved evidence into one operational row per drone.

The resulting state includes concepts such as:

```text
asset_state
connection_state
mission_phase
mission_status
platform_health
state_as_of
```

The result represents reconstructed operational state.

It is not merely the latest telemetry packet.

---

# 15. Observation vs State

The architecture intentionally distinguishes:

```text
Latest observation
```

from:

```text
Current state
```

These concepts are related but not identical.

---

## 15.1 Latest Telemetry Observation

The function:

```text
LatestTelemetryObservation(RunId)
```

selects the latest canonical telemetry event per drone using:

```text
event_time
source_sequence_number
```

The observation provides physical telemetry attributes such as:

```text
latitude
longitude
altitude_m

ground_speed_mps
vertical_speed_mps
heading_deg

battery_pct
communication_mode
optic_fiber_remaining_m
```

and associated observation timestamps.

---

## 15.2 Why the Separation Matters

Imagine that the most recent explicit state event says:

```text
connection_state = DISCONNECTED
```

while the latest telemetry observation available was generated just before the disconnect.

The system should preserve both facts:

```text
Last observed telemetry position
```

and:

```text
Current reconstructed connection state
```

Combining them blindly would lose analytical meaning.

---

# 16. Gold — Operational Serving Layer

The primary fleet serving model is:

```text
FleetOperationalView(RunId)
```

This combines:

```text
FleetCurrentState
        +
LatestTelemetryObservation
```

through an operational join.

Conceptually:

```text
Reconstructed State
        │
        ├──────────────┐
        │              │
        ↓              ↓
 State attributes   Latest telemetry
        │              │
        └──────┬───────┘
               ↓
     FleetOperationalView
```

---

## 16.1 Serving Output

The operational view can expose:

```text
drone_id
battalion_id
mission_id

asset_state
connection_state
mission_phase
mission_status
platform_health

latitude
longitude
altitude_m
heading_deg
ground_speed_mps
vertical_speed_mps

battery_pct
communication_mode
optic_fiber_remaining_m

telemetry_as_of
state_as_of
telemetry_ingested_at
telemetry_state_gap_ms
```

This is significantly more useful to dashboard consumers than joining state and telemetry independently.

---

# 17. Telemetry-State Gap

The serving layer calculates the time relationship between the latest telemetry observation and reconstructed state.

Conceptually:

```text
telemetry_state_gap_ms
```

This provides visibility into cases where:

```text
Latest physical observation
```

and:

```text
Latest known operational state
```

were established at different moments.

It helps prevent users from assuming all attributes in an operational row originate from one single event.

---

# 18. Fleet Operational Summary

`FleetOperationalSummary(RunId)` derives fleet-level KPIs from the serving view.

Examples include:

```text
Total drones

RF drones
FIBER drones
Unknown communication-mode drones

Available drones
Connected drones
Completed missions
Healthy drones

Average battery
Minimum battery

Average fiber remaining
Minimum fiber remaining
```

and percentages such as:

```text
AvailabilityPct
ConnectivityPct
MissionCompletionPct
HealthyPct
CommunicationModeCoveragePct
```

Fiber statistics are evaluated specifically for FIBER assets.

---

# 19. Current-Run Abstraction

Dashboard queries generally need the most recently observed simulation run.

The function:

```text
LatestObservedRun()
```

identifies that run using Event Hubs enqueue activity.

Conceptually:

```text
RawDroneEvents
    ↓
group by simulator_run_id
    ↓
max(eh_enqueued_time)
    ↓
most recently observed run
```

This avoids hard-coding a run identifier throughout dashboard queries.

---

# 20. Current Serving Functions

Convenience functions expose the latest observed run directly.

Examples include:

```text
CurrentFleetOperationalView()
CurrentFleetOperationalSummary()
CurrentFleetMapView()
```

These wrap the run-aware functions.

Conceptually:

```text
LatestObservedRun()
        ↓
RunId
        ↓
FleetOperationalView(RunId)
        ↓
CurrentFleetOperationalView()
```

This provides a clean dashboard-facing interface while retaining parameterized functions for historical analysis.

---

# 21. Current Fleet Map View

`CurrentFleetMapView()` exposes geospatial operational information for the current run.

It combines location with current state and telemetry freshness.

Examples include:

```text
latitude
longitude
altitude_m
heading_deg

battery_pct
communication_mode
optic_fiber_remaining_m

asset_state
connection_state
mission_phase
mission_status
platform_health

telemetry_age_sec
```

This allows map visuals to consume a focused dataset rather than reproduce state reconstruction logic.

---

# 22. Performance and Timeliness Layer

Stream correctness and stream timeliness are treated as separate concerns.

A stream may be structurally complete but operationally late.

The analytical model therefore evaluates metrics such as:

```text
Relative delay
Physical arrival gaps
Cloud latency
Burst delivery
```

The dashboard consumes a timeliness report through:

```text
CurrentStreamTimelinessReport()
```

with metrics including:

```text
P95RelativeDelayMs
MaxRelativeDelayMs
MaxPhysicalGapMs
P95CloudLatencyMs
MaxCloudLatencyMs
```

and burst-related information.

---

# 23. Burst Behavior

Buffered reconnect scenarios may produce bursts.

Conceptually:

```text
Normal telemetry

1   2   3   4

Connection interruption

5   6   7   8
        buffered

Reconnect
        ↓

5 6 7 8 arrive together
```

The producer sequence is still meaningful, but physical arrival behavior changes significantly.

Timeliness analytics expose this behavior instead of treating the post-reconnect burst as ordinary delivery.

---

# 24. Stream Integrity Report

The dashboard also consumes:

```text
CurrentStreamIntegrityReport()
```

to expose metrics such as:

```text
DuplicateDeliveries
SequenceGaps
MissingSequences
OutOfOrderTransitions
NullEhMetadata
```

This provides a compact operational summary of stream health.

---

# 25. Integrity vs Timeliness

These two analytical dimensions are intentionally separated.

### Integrity

```text
Did the expected logical stream arrive correctly?
```

Examples:

* Missing sequence
* Duplicate delivery
* Sequence gap
* Invalid ordering

### Timeliness

```text
How did the stream arrive over time?
```

Examples:

* High latency
* Buffered bursts
* Long arrival gaps
* Delayed events

A stream may therefore be:

```text
Complete but late
```

or:

```text
Fast but incomplete
```

These are different operational conditions.

---

# 26. Dashboard Consumption Pattern

The dashboard consumes multiple analytical layers depending on the question.

For raw volume questions:

```text
RawDroneEvents
```

For unique event history:

```text
TelemetryCanonical
StateTransitionsCanonical
```

For current operational state:

```text
CurrentFleetOperationalView()
```

For fleet KPIs:

```text
CurrentFleetOperationalSummary()
```

For maps:

```text
CurrentFleetMapView()
```

For stream quality:

```text
CurrentStreamIntegrityReport()
```

For stream timing:

```text
CurrentStreamTimelinessReport()
```

This layered approach avoids forcing one dataset to answer every analytical question.

---

# 27. Unified Event Timeline

Drone-level timeline analysis combines multiple canonical event families.

Conceptually:

```text
TelemetryCanonical
        +
StateTransitionsCanonical
        ↓
Unified sequence-ordered timeline
```

A timeline can therefore show:

```text
Sequence 41 — TELEMETRY
Sequence 42 — STATE_TRANSITION
Sequence 43 — TELEMETRY
Sequence 44 — TELEMETRY
```

This is possible because source sequence numbering is shared across event families.

The result makes domain transitions visible alongside continuous telemetry.

---

# 28. Event Time vs Arrival Time

One of the most important architectural lessons of the project is:

```text
Event order
≠
Arrival order
```

For example:

```text
Producer order:

41
42
43

Physical arrival:

41
43
42
```

A dashboard using ingestion order as operational truth could reconstruct the wrong sequence.

The canonical and state layers therefore preserve event semantics and sequence information independently from physical delivery timing.

---

# 29. Contract Evolution Through the KQL Layers

Event contract changes are introduced through explicit migration scripts.

The repository includes migrations such as:

```text
09_contract_v1_1_migration.kql
10_contract_v1_2_migration.kql
```

Contract evolution may require changes to:

```text
Parsed table schemas
Transform functions
Canonical views
State functions
Serving functions
Dashboard queries
```

The migration scripts make those changes visible and reproducible rather than modifying production objects without documentation.

---

# 30. Communication Mode Evolution

Contract v1.2 added:

```text
communication_mode
```

to telemetry analytics.

The serving layer now carries communication mode alongside:

```text
connection_state
optic_fiber_remaining_m
```

This enables operational analysis such as:

```text
How many assets use RF?

How many use FIBER?

Are communication modes present for all assets?

Which disconnected drones use which technology?

How much fiber remains on fiber-connected assets?
```

This information is propagated into dashboard-facing serving functions rather than being interpreted from simulator configuration.

---

# 31. Why Communication Mode Is Kept in the Event Stream

The analytical platform should not need access to the original YAML configuration to understand an asset.

Instead:

```text
Event
    ↓
Parsed telemetry
    ↓
Canonical telemetry
    ↓
Operational serving
```

carries the communication identity downstream.

This keeps event analytics self-describing.

---

# 32. Terminal Assets

The state architecture is also important when telemetry permanently stops.

A destroyed or otherwise terminal asset may no longer generate new observations.

A naive system could cause the asset to disappear from a latest-telemetry-only view.

The project instead combines:

```text
Latest known observation
        +
Explicit state evidence
```

so the analytical model can preserve meaningful operational context.

Conceptually:

```text
Last known position
        +
DESTROYED state
        ↓
Terminal asset remains visible analytically
```

This is one reason state reconstruction is separated from telemetry selection.

---

# 33. KQL Repository Organization

The implementation is divided by responsibility.

```text
kql/
├── 01_create_tables.kql
├── 02_transform_functions.kql
├── 03_update_policies.kql
├── 04_materialized_views.kql
├── 05_quality_functions.kql
├── 06_state_functions.kql
├── 07_serving_functions.kql
├── 08_performance_functions.kql
├── 09_contract_v1_1_migration.kql
└── 10_contract_v1_2_migration.kql
```

The ordering communicates the dependency flow of the analytical architecture.

---

## 33.1 Responsibility Map

```text
01
Tables
   ↓
02
Transforms
   ↓
03
Update Policies
   ↓
04
Canonical Materialized Views
   ↓
05
Quality
   ↓
06
State + Observation
   ↓
07
Serving
   ↓
08
Performance / Timeliness
   ↓
09 / 10
Contract Evolution
```

This keeps object creation and analytical responsibilities understandable from the repository itself.

---

# 34. Architectural Dependency Direction

Higher analytical layers may depend on lower layers.

The reverse should not occur.

Conceptually:

```text
Dashboard
    ↓
Serving
    ↓
State / Quality / Performance
    ↓
Canonical
    ↓
Parsed
    ↓
Raw
```

For example:

```text
FleetOperationalView()
```

may depend on:

```text
FleetCurrentState()
LatestTelemetryObservation()
```

which in turn depend on canonical tables.

But canonicalization should not depend on dashboard requirements.

This preserves separation of concerns.

---

# 35. Conceptual Diagram Candidate

The final architecture diagram should emphasize analytical responsibilities rather than individual KQL statements.

```text
┌───────────────────────────────┐
│       Azure Event Hubs        │
└───────────────┬───────────────┘
                ↓
┌───────────────────────────────┐
│ BRONZE / RAW                  │
│ RawDroneEvents                │
│ + EH metadata                 │
└───────────────┬───────────────┘
                ↓
┌───────────────────────────────┐
│ SILVER / TRANSFORMS           │
│ TelemetryParsed               │
│ StateTransitionsParsed        │
│ MaintenanceEventsParsed       │
│ StatusConfirmationsParsed     │
└───────────────┬───────────────┘
                ↓
┌───────────────────────────────┐
│ SILVER / CANONICAL            │
│ one row per logical event_id  │
└───────────────┬───────────────┘
                ↓
        ┌───────┴────────┐
        ↓                ↓
┌───────────────┐ ┌───────────────┐
│ QUALITY /     │ │ STATE /       │
│ PERFORMANCE   │ │ OBSERVATION   │
└───────┬───────┘ └───────┬───────┘
        │                  │
        └─────────┬────────┘
                  ↓
┌───────────────────────────────┐
│ GOLD / SERVING                │
│ FleetOperationalView          │
│ FleetOperationalSummary       │
│ CurrentFleetMapView           │
│ Stream Reports                │
└───────────────┬───────────────┘
                ↓
┌───────────────────────────────┐
│ REAL-TIME DASHBOARD           │
└───────────────────────────────┘
```

---

# 36. Key Design Principles

### Raw data is preserved

Higher-level transformations do not replace delivery evidence.

### Logical events are different from physical deliveries

Canonicalization operates on `event_id`.

### Event time and arrival time remain distinct

Timeliness analysis depends on preserving both.

### State is reconstructed from evidence

The latest telemetry row is not automatically authoritative for every state domain.

### Serving functions form an analytical contract

Dashboard visuals consume reusable interfaces instead of rebuilding core logic.

### Integrity and timeliness are separate concerns

Completeness does not imply freshness, and freshness does not imply completeness.

### Contract changes propagate explicitly

Schema evolution is versioned and migration-aware.

### Dashboard logic remains thin

The presentation layer should visualize analytical results rather than become the place where operational truth is calculated.

---

# 37. Professional Value

The KQL architecture demonstrates that a real-time pipeline requires more than fast ingestion.

The project addresses several layers of reasoning:

```text
Ingestion
    ↓
Structural parsing
    ↓
Logical deduplication
    ↓
Stream-quality validation
    ↓
Temporal analysis
    ↓
State reconstruction
    ↓
Serving abstraction
    ↓
Operational visualization
```

The professional objective is therefore not:

```text
Events appear on a dashboard.
```

It is:

```text
Events can be traced from physical arrival to canonical identity,
evaluated for stream integrity and timeliness, reconstructed into
operational state, and exposed through reusable analytical interfaces.
```
