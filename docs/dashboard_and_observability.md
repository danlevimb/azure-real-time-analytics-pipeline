# Dashboard and Observability

> **Documentation path:**
> [Documentation Hub](README.md) →
> [Streaming & KQL Architecture](streaming_and_kql_architecture.md) →
> [Stream Quality & Timeliness](stream_quality_and_timeliness.md) →
> [State Reconstruction & Serving](state_reconstruction_and_serving.md) →
> [Communications & Failure Scenarios](communications_and_failure_scenarios.md) →
> **Dashboard & Observability**

**Project:** `azure-real-time-analytics-pipeline`
**Focus:** Operational visualization of Gold serving data, stream reliability, reconciliation, and communications observability

---

## 1. Purpose

The dashboard is the operational presentation layer of the real-time Data Engineering architecture.

Its purpose is not to calculate the system's analytical truth.

Instead, it exposes results already produced by:

```text
Raw ingestion
      ↓
Canonicalization
      ↓
Quality / Timeliness
      ↓
State reconstruction
      ↓
Gold serving
      ↓
Dashboard
```

The dashboard therefore answers two broad questions:

```text
What is happening operationally?
```

and:

```text
Can the data supporting that view be trusted?
```

Both are required for meaningful real-time observability.

---

## 2. Dashboard Philosophy

A dashboard showing telemetry without pipeline health can be misleading.

For example, a map may display an asset position even when:

* The observation is stale
* Events are missing
* Delivery is delayed
* Duplicates occurred
* State changed after the latest telemetry observation

The project therefore treats observability as multiple related dimensions:

```text
Operational State
        +
Stream Integrity
        +
Stream Timeliness
        +
Raw / Canonical Reconciliation
        +
Communication Context
```

The dashboard makes these dimensions visible without requiring users to inspect individual KQL objects.

---

## 3. Presentation Layer, Not Truth Layer

Core business and reliability logic remains outside the dashboard.

The preferred pattern is:

```text
KQL Function
      ↓
Stable analytical result
      ↓
Dashboard visual
```

rather than:

```text
Dashboard tile
      ↓
Large independent query
      ↓
Different definition of truth
```

Reusable functions such as:

```text
CurrentFleetOperationalView()
CurrentFleetOperationalSummary()
CurrentFleetMapView()

CurrentStreamIntegrityReport()
CurrentStreamTimelinessReport()
```

provide analytical interfaces for presentation.

Diagnostic visuals may still query Raw or Canonical layers directly when the purpose is specifically to compare those layers.

---

# 4. Current Dashboard Structure

The current dashboard contains three primary pages:

```text
Operations
Stream Quality
DRN-001
```

The third page is a parameterized asset-detail view despite retaining the historical `DRN-001` page name.

Conceptually:

```text
                DASHBOARD
                    │
        ┌───────────┼───────────┐
        ↓           ↓           ↓
   Operations   Stream Quality  Asset Detail
```

Each page serves a different analytical purpose.

---

# 5. Operations Page

The Operations page provides the current fleet-level operational view.

Its primary data source is the Gold serving layer.

Examples include:

```text
CurrentFleetOperationalView()
CurrentFleetOperationalSummary()
CurrentFleetMapView()
```

This page focuses on:

* Current fleet state
* Geospatial position
* Availability
* Connectivity
* Mission completion
* Platform health
* Communication modes
* Disconnected assets
* Fiber-specific telemetry

---

## 6. Fleet Operational KPIs

The dashboard derives operational KPIs from:

```text
CurrentFleetOperationalSummary()
```

Current metrics include:

```text
Availability
Connectivity
Mission Completion
Platform Health
```

These values originate from the same Gold serving definition used throughout the dashboard.

Conceptually:

```text
FleetCurrentState
        +
LatestTelemetryObservation
        ↓
FleetOperationalView
        ↓
FleetOperationalSummary
        ↓
KPI Visuals
```

The presentation layer therefore does not independently redefine fleet health.

---

# 7. Geospatial Operational View

The map consumes:

```text
CurrentFleetMapView()
```

This provides current location together with operational context such as:

```text
latitude
longitude
altitude

asset_state
connection_state

mission_phase
mission_status

platform_health

battery_pct

telemetry_as_of
state_as_of
telemetry_age_sec
```

The important Data Engineering detail is that the map is not simply showing:

```text
latest telemetry row
```

It is showing a serving model combining:

```text
latest known observation
        +
reconstructed state
```

---

## 8. Telemetry Freshness

Operational visuals expose telemetry freshness through values such as:

```text
telemetry_age_sec
```

This prevents the dashboard from presenting old observations as if they were current without context.

Conceptually:

```text
Position exists
      ↓
How old is that observation?
      ↓
Can the user interpret it correctly?
```

Freshness becomes part of observability rather than an invisible implementation detail.

---

# 9. Communications Observability

Communication mode is propagated through the Gold serving layer and displayed operationally.

Current metrics include:

```text
RfDrones
FiberDrones
CommunicationModeCoveragePct
```

The dashboard can also group assets by:

```text
communication_mode
```

and expose asset-level values such as:

```text
communication_mode
connection_state
optic_fiber_remaining_m
```

This makes heterogeneous source behavior observable without requiring access to simulator configuration.

---

## 10. Communication Mode Coverage

The metric:

```text
CommunicationModeCoveragePct
```

helps validate that the current operational dataset contains explicit communication metadata for the expected population.

This is useful during contract evolution because missing communication-mode values can reveal:

* Legacy events
* Incomplete migrations
* Unexpected schema behavior
* Incomplete analytical propagation

The metric therefore functions as both an operational and data-quality signal.

---

## 11. Disconnected Asset View

The dashboard includes a focused operational view based on:

```text
connection_state != "CONNECTED"
```

and exposes context such as:

```text
asset_state
mission_status
mission_phase

latitude
longitude

battery_pct
optic_fiber_remaining_m

telemetry_as_of
state_as_of
telemetry_age_sec
```

This allows a user to distinguish:

```text
Disconnected but recently observed
```

from:

```text
Disconnected with stale telemetry
```

or:

```text
Terminal asset with last known position
```

without changing the underlying analytical model.

---

# 12. Stream Quality Page

The Stream Quality page shifts focus from operational assets to the **health of the data pipeline itself**.

Its main concerns are:

```text
Integrity
Timeliness
Reconciliation
Volume
Latest observed run
```

This makes pipeline reliability a first-class dashboard subject.

---

# 13. Stream Integrity Visuals

The dashboard consumes:

```text
CurrentStreamIntegrityReport()
```

and exposes values including:

```text
DuplicateDeliveries
SequenceGaps
MissingSequences
OutOfOrderTransitions
NullEhMetadata
```

These metrics answer:

```text
Did the logical stream arrive correctly?
```

They are deliberately separate from fleet operational KPIs.

---

# 14. Stream Timeliness Visuals

The dashboard also consumes:

```text
CurrentStreamTimelinessReport()
```

and exposes metrics such as:

```text
P95RelativeDelayMs
MaxRelativeDelayMs

MaxPhysicalGapMs

P95CloudLatencyMs
MaxCloudLatencyMs
```

This answers a different question:

```text
How did the stream arrive over time?
```

Integrity and timeliness remain visually and conceptually distinct.

---

# 15. Burst Visibility

Reconnect and buffering scenarios may cause several events to arrive together.

The dashboard exposes burst context such as:

```text
BurstDrone
MaxBurstEvents
BurstFirstSeq
BurstLastSeq
```

This allows a user to identify:

```text
which producer
+
how many events
+
which sequence range
```

participated in the observed burst.

A temporary arrival spike can therefore be explained rather than treated as unexplained volume.

---

# 16. Latest Observed Run

The dashboard exposes the current analytical execution using:

```text
LatestObservedRun()
```

with information such as:

```text
RunId
Events
LastSeenAt
```

This is important because the analytical database may contain multiple historical simulator runs.

Dashboard visuals generally operate against the most recently observed run rather than hard-coded Run IDs.

---

# 17. Event Volume

Raw Event Hubs ingestion is also visible through diagnostic metrics.

The dashboard evaluates values such as:

```text
TotalEvents
FirstSeen
LastSeen
DurationSeconds
EventsPerSecond
```

and event counts grouped by:

```text
event_type
```

These metrics help distinguish:

```text
pipeline volume
```

from:

```text
business / operational state
```

They are diagnostic rather than state-defining measures.

---

# 18. Raw-to-Canonical Reconciliation

One of the most important Stream Quality views compares:

```text
RawDroneEvents
```

against canonical representations.

The dashboard evaluates values such as:

```text
RawRows
RawUniqueEventIds
RawDuplicates

CanonicalRows
UniqueCanonicalEventIds

MissingFromCanonical
ReconciliationStatus
```

This provides direct evidence that:

```text
physical deliveries
```

and:

```text
logical analytical events
```

are being treated correctly.

---

## 19. Per-Asset Reconciliation

Reconciliation can also be evaluated by:

```text
asset
+
event family
```

For example:

```text
DRN-001
TELEMETRY

Raw unique events
vs
Canonical unique events
```

Differences can be classified as:

```text
MISSING IN CANONICAL

EXTRA IN CANONICAL

OK
```

This makes canonicalization problems traceable to a smaller analytical scope instead of only exposing a fleet-wide total.

---

# 20. Asset Detail Page

The current detail page uses a dashboard parameter:

```text
_droneId
```

The selectable asset values are populated from canonical telemetry for the current run.

This converts what originally began as a `DRN-001` dashboard page into a reusable per-asset analytical view.

Conceptually:

```text
Select asset
      ↓
_droneId
      ↓
Canonical event history
      ↓
Asset-specific visuals
```

---

# 21. Asset Telemetry History

The detail page can visualize telemetry ordered by:

```text
source_sequence_number
```

rather than relying on physical ingestion order.

Examples include:

```text
latitude
longitude

altitude_m
ground_speed_mps
battery_pct

mission_phase
```

This supports investigation of the logical event progression for one producer.

---

# 22. State Transition History

The detail view also exposes canonical state transitions.

A transition can be represented as:

```text
previous_state → new_state
```

together with:

```text
source_sequence_number
reason_code
event_time
```

This provides direct visibility into explicit domain state changes.

---

# 23. Unified Event Timeline

Telemetry and state transitions can be combined into one sequence-oriented timeline.

Conceptually:

```text
Sequence 41
TELEMETRY

Sequence 42
STATE_TRANSITION

Sequence 43
TELEMETRY

Sequence 44
STATE_TRANSITION
```

This is possible because event families share the producer's logical:

```text
source_sequence_number
```

The timeline therefore helps answer:

```text
What did the producer logically emit, and in what order?
```

rather than:

```text
In what order happened to arrive in Azure?
```

---

# 24. Observability Layers

The complete dashboard can be viewed as several observability layers.

```text
┌───────────────────────────────┐
│ OPERATIONAL OBSERVABILITY     │
│ state / location / health     │
└──────────────┬────────────────┘
               │
┌──────────────▼────────────────┐
│ COMMUNICATION OBSERVABILITY   │
│ RF / FIBER / connectivity     │
└──────────────┬────────────────┘
               │
┌──────────────▼────────────────┐
│ STREAM INTEGRITY              │
│ missing / duplicate / order   │
└──────────────┬────────────────┘
               │
┌──────────────▼────────────────┐
│ STREAM TIMELINESS             │
│ delay / latency / bursts      │
└──────────────┬────────────────┘
               │
┌──────────────▼────────────────┐
│ RECONCILIATION                │
│ Raw vs Canonical              │
└───────────────────────────────┘
```

Together, these answer not only:

```text
What does the operational data say?
```

but also:

```text
Why should I trust it?
```

---

# 25. Dashboard as a Data Engineering Consumer

The dashboard intentionally consumes different layers for different questions.

| Analytical question                    | Preferred source               |
| -------------------------------------- | ------------------------------ |
| What physically arrived?               | `RawDroneEvents`               |
| What unique logical events exist?      | Canonical views                |
| Is the stream complete?                | Quality functions              |
| Is the stream timely?                  | Performance functions          |
| What is the current state?             | State reconstruction           |
| What should operators consume?         | Gold serving functions         |
| Did canonicalization behave correctly? | Raw + Canonical reconciliation |

This prevents one dataset from being forced to answer every analytical question.

---

# 26. Source-Controlled Dashboard Artifact

The dashboard export is versioned in the repository as:

```text
dashboards/
└── rtd-drone-operations.json
```

The export preserves:

* Dashboard pages
* Visual definitions
* KQL queries
* Parameters
* Data-source configuration
* Layout metadata

This makes the analytical presentation layer part of the reproducible project artifact rather than an undocumented cloud-only object.

Sensitive identifiers should remain sanitized before public publication.

---

# 27. Dashboard and Contract Evolution

As the event contract evolved, the dashboard also evolved.

For example, Event Contract v1.2 introduced explicit:

```text
communication_mode
```

which later became visible through:

```text
RF asset counts
FIBER asset counts
communication-mode distribution
communication-mode coverage
fiber-specific telemetry
```

This demonstrates the complete impact path of schema evolution:

```text
Event Contract
      ↓
Producer
      ↓
Event Hubs
      ↓
KQL Transform
      ↓
Canonical
      ↓
Gold Serving
      ↓
Dashboard
```

Schema evolution therefore affects the full Data Engineering lifecycle, not only the producer.

---

# 28. Conceptual Observability Diagram

A final polished diagram should show how observability is derived from multiple analytical layers.

```text
              Azure Event Hubs
                     │
                     ↓
               Raw Ingestion
                     │
            ┌────────┼─────────┐
            ↓        ↓         ↓
        Canonical  Quality  Timeliness
            │        │         │
            ↓        │         │
          State      │         │
            │        │         │
            ↓        │         │
          Serving    │         │
            └────────┼─────────┘
                     ↓
                DASHBOARD
                     │
        ┌────────────┼────────────┐
        ↓            ↓            ↓
   Operations   Stream Quality  Detail
```

The emphasis should remain on **analytical dependencies**, not dashboard aesthetics.

---

# 29. Design Principles

### Dashboard visuals should consume reusable analytical interfaces

Core state and reliability logic belongs in KQL functions.

### Data health belongs beside operational metrics

A real-time view without stream-health context may create false confidence.

### Raw and canonical views have different purposes

The dashboard uses each where appropriate.

### Freshness should remain visible

A position without observation age can be misleading.

### Event history should preserve logical ordering

Asset detail analysis uses source sequence rather than assuming ingestion order.

### Schema evolution must reach the presentation layer deliberately

New contract attributes should propagate through the full architecture.

### Dashboard configuration should be versioned

The presentation layer is part of the project implementation.

---

# 30. Engineering Value

The dashboard demonstrates more than visualization.

It closes the Data Engineering loop:

```text
Event production
      ↓
Azure Event Hubs
      ↓
Raw ingestion
      ↓
Canonical processing
      ↓
Reliability analytics
      ↓
State reconstruction
      ↓
Gold serving
      ↓
Operational observability
```

The key outcome is not:

```text
Telemetry appears on a dashboard.
```

It is:

```text
Operational data is presented together with evidence
about its freshness, integrity, timing, and analytical reconciliation.
```

That makes the dashboard an observability surface for the **data system itself**, not only for the synthetic domain generating the events.

---

### Navigation

**Previous:** [Communications and Failure Scenarios](communications_and_failure_scenarios.md)
**Documentation Hub:** [README](README.md)

**Related:**
[Streaming and KQL Architecture](streaming_and_kql_architecture.md)
[Stream Quality and Timeliness](stream_quality_and_timeliness.md)
[State Reconstruction and Serving](state_reconstruction_and_serving.md)

**Implementation artifact:** [`../dashboards/rtd-drone-operations.json`](../dashboards/rtd-drone-operations.json)
