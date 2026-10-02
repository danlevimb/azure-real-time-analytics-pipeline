# Communications and Failure Scenarios

> **Documentation path:**
> [Documentation Hub](README.md) →
> [Streaming & KQL Architecture](streaming_and_kql_architecture.md) →
> [Stream Quality & Timeliness](stream_quality_and_timeliness.md) →
> [State Reconstruction & Serving](state_reconstruction_and_serving.md) →
> **Communications & Failure Scenarios** →
> [Dashboard & Observability](dashboard_and_observability.md)

**Project:** `azure-real-time-analytics-pipeline`
**Focus:** Controlled stream degradation and failure injection for Azure real-time pipeline validation

---

## 1. Purpose

Failure scenarios exist to test the Data Engineering architecture under imperfect delivery conditions.

The project does not attempt to model telecommunications or physical communication systems in engineering detail.

Instead, communication and transport failures provide controlled ways to answer questions such as:

```text
What happens when an event is delayed?

What happens when a logical event never reaches Azure?

What happens when an event arrives twice?

What happens when telemetry disappears temporarily?

What happens when buffered events arrive together?

What happens when an asset stops producing data permanently?

Can KQL distinguish these conditions?

Can operational state still be reconstructed correctly?
```

The failure model is therefore a **test harness for stream reliability**.

---

## 2. Two Failure Layers

The project intentionally distinguishes between two different types of failure.

```text
COMMUNICATION FAILURE
Asset cannot transmit normally

vs

TRANSPORT FAILURE
Event entered transport but delivery behavior was altered
```

These should not be interpreted as the same problem.

---

## 3. Communication Layer

Communication state determines whether a generated event can leave the source and enter the shared transport pipeline.

Conceptually:

```text
Event Generated
      ↓
Communication Gate
      │
      ├── transmission allowed
      │          ↓
      │     Transport Layer
      │
      └── transmission blocked
                 ↓
          Buffer or remain
          unavailable
```

This models producer-side availability before shared transport behavior is applied.

---

## 4. Transport Layer

Once an event enters transport, additional delivery behavior may be introduced.

Supported controlled conditions include:

```text
Base delay
Extra delay
Drop
Duplicate
Buffer
Reordered physical arrival
```

Conceptually:

```text
Valid Logical Event
        ↓
Transport Engine
   ┌────┼─────┬──────┐
   ↓    ↓     ↓      ↓
Delay  Drop Duplicate Buffer
   └────┴─────┴──────┘
        ↓
Physical Delivery
        ↓
Azure Event Hubs
```

This separation allows the project to identify **where** stream degradation was introduced.

---

# 5. Communication Modes

Event Contract v1.2 introduces explicit asset-level communication mode.

Supported values are:

```text
RF
FIBER
```

Communication mode belongs to the individual source asset rather than the entire fleet.

This allows heterogeneous streams such as:

```text
Asset A → RF
Asset B → FIBER
Asset C → RF
Asset D → FIBER
```

The Data Engineering significance is that:

```text
communication_mode
```

becomes another observable analytical dimension carried through the event pipeline.

---

## 6. Why Mixed Communication Matters

A heterogeneous producer population allows the same Azure pipeline to process assets with different failure characteristics.

The downstream architecture does not require separate ingestion systems.

Instead:

```text
RF events
    │
    ├─────────┐
    │         │
FIBER events │
    │         │
    └────┬────┘
         ↓
   Azure Event Hubs
         ↓
   RawDroneEvents
         ↓
     Same KQL
   analytical model
```

The transport medium becomes part of the event data rather than part of the Azure ingestion topology.

---

# 7. RF Failure Scenarios

Current v1.2 RF-specific fault types include:

```text
RF_LINK_LOSS
RF_JAMMING
```

The objective is not to reproduce radio-frequency physics.

The scenarios simply create deterministic connectivity behavior that can affect downstream event delivery.

From the Data Engineering perspective, expected observable effects may include:

* Connection-state transitions
* Temporary or sustained telemetry gaps
* Increased arrival delays
* Buffered delivery when recovery is configured
* Sequence discontinuities during unavailable periods
* State updates that arrive independently from telemetry

These effects can then be inspected through KQL quality and state functions.

---

# 8. Fiber Failure Scenarios

Current FIBER-specific fault types include:

```text
FIBER_LINK_LOSS
FIBER_CUT
```

The project also models depletion of:

```text
optic_fiber_remaining_m
```

for fiber-connected assets.

Again, the objective is analytical rather than physical simulation.

The important behavior is that the event stream can represent:

```text
communication technology
+
remaining resource
+
connection state
+
failure condition
```

and propagate those attributes through the Azure analytical layers.

---

## 9. Fiber Link Loss vs Fiber Cut

These scenarios represent different stream behaviors.

### Fiber Link Loss

May be temporary.

Conceptually:

```text
CONNECTED
    ↓
FIBER_LINK_LOSS
    ↓
DISCONNECTED
    ↓
optional recovery
    ↓
CONNECTED
```

A reconnect can therefore create a delayed or buffered-delivery pattern.

### Fiber Cut

Represents a terminal communication failure for the current mission.

Conceptually:

```text
CONNECTED
    ↓
FIBER_CUT
    ↓
DISCONNECTED
```

No reconnect time is defined for this condition.

For the analytics platform, the important distinction is whether the data outage is expected to recover or represents a terminal communication condition.

---

# 10. Fiber Exhaustion

Fiber-connected sources also expose a finite:

```text
optic_fiber_remaining_m
```

resource.

When the simulated resource reaches zero, communication can transition:

```text
CONNECTED
    ↓
DISCONNECTED
```

Subsequent telemetry may continue to exist logically at the producer but be blocked from normal transmission.

This creates an especially useful Data Engineering test:

```text
Producer continues changing state
        ↓
Cloud telemetry stops
        ↓
Latest observation becomes stale
        ↓
State reconstruction must remain meaningful
```

The analytical challenge is not the fiber model itself.

It is handling the resulting **absence of fresh events** correctly.

---

# 11. Disconnect and Reconnect

Temporary connectivity loss provides a different failure pattern.

Conceptually:

```text
Normal stream

1 2 3 4 5
        ↓
   disconnect

6 7 8 9
  generated but
  unavailable

        ↓
    reconnect
        ↓

buffered events released
        ↓

6 7 8 9
arrive as a burst
```

This creates several downstream signals:

```text
arrival gap
+
relative delay
+
burst delivery
+
possible out-of-order behavior
```

while the logical event sequence may remain complete.

This scenario directly supports the distinction between:

```text
Integrity
```

and:

```text
Timeliness
```

described in [Stream Quality and Timeliness](stream_quality_and_timeliness.md).

---

# 12. Drop Scenario

A transport drop represents a logical event that was generated but never physically delivered.

Conceptually:

```text
Generated

41 42 43 44 45
```

Transport:

```text
43 → DROP
```

Observed downstream:

```text
41 42 44 45
```

Expected Azure signals include:

```text
Missing source sequence
Sequence gap
Reduced unique logical event count
```

Unlike buffering, the missing event does not later reappear.

---

# 13. Duplicate Scenario

A transport duplicate creates more than one physical delivery for the same logical event.

Conceptually:

```text
Generated

41 42 43
```

Delivered:

```text
41 42 42 43
```

Expected downstream behavior is:

```text
Raw rows > unique event IDs
```

while canonicalization should preserve:

```text
one logical event_id
```

This validates the distinction between:

```text
physical delivery count
```

and:

```text
logical event count
```

---

# 14. Extra Delay and Reordering

Individual events may receive additional transport delay.

Example:

```text
Logical order

30 → 31 → 32
```

with different delays:

```text
30 → +7000 ms
31 → +5000 ms
32 → +3000 ms
```

Physical arrival can therefore differ from logical source order.

The Azure analytical architecture must preserve:

```text
event_time
source_sequence_number
```

rather than deriving business state only from arrival order.

This scenario directly exercises:

* Out-of-order detection
* Relative delay metrics
* Event-time reasoning
* State reconstruction

---

# 15. Terminal Asset Scenario

The project also supports a terminal source condition.

A controlled destruction scenario produces explicit state transitions such as:

```text
asset_state
ACTIVE → DESTROYED

mission_status
ACTIVE → ABORTED

connection_state
CONNECTED → DISCONNECTED
```

After the terminal condition, normal telemetry production for that asset stops.

From the Data Engineering perspective, this tests a difficult condition:

```text
No more fresh telemetry
        +
Last known observation still matters
        +
Explicit terminal state must remain visible
```

A latest-telemetry-only architecture could incorrectly lose operational context.

The state-reconstruction layer instead preserves the relationship between:

```text
last known observation
```

and:

```text
latest explicit state
```

---

# 16. Failure Scenario Matrix

| Scenario           | Layer                    | Typical downstream signal                            |
| ------------------ | ------------------------ | ---------------------------------------------------- |
| Extra delay        | Transport                | Higher latency / reordered arrival                   |
| Drop               | Transport                | Missing sequence / gap                               |
| Duplicate          | Transport                | Raw duplicate / canonical deduplication              |
| Buffer + reconnect | Communication / delivery | Arrival gap followed by burst                        |
| RF link loss       | Communication            | Telemetry interruption / connection transition       |
| RF jamming         | Communication            | Connectivity degradation / delayed or blocked stream |
| Fiber link loss    | Communication            | Temporary disconnect, optional recovery              |
| Fiber cut          | Communication            | Terminal communication loss                          |
| Fiber exhaustion   | Communication            | Resource reaches zero, delivery becomes unavailable  |
| Terminal asset     | Source state             | Telemetry stops; terminal state remains              |

The purpose of the matrix is to map failure mechanisms to **observable data behavior**.

---

# 17. Expected Azure Observability

Failure scenarios should leave evidence across several analytical layers.

```text
Raw
│
├── Physical event count
├── Event Hubs metadata
└── Arrival timestamps

Canonical
│
├── Unique logical events
└── Deduplicated history

Quality
│
├── Missing sequences
├── Duplicates
├── Sequence gaps
└── Out-of-order behavior

Timeliness
│
├── Relative delay
├── Cloud latency
├── Arrival gaps
└── Bursts

State
│
├── Connection state
├── Asset state
└── Terminal conditions

Serving
│
└── Operational representation
```

A failure is therefore useful only if the pipeline can make its effects observable.

---

# 18. Failure Injection Is Not the Result

The project is not valuable because it can simulate a failure.

The important engineering sequence is:

```text
Controlled Failure
        ↓
Observable Stream Effect
        ↓
Azure Ingestion
        ↓
KQL Detection
        ↓
Canonical Interpretation
        ↓
State Reconstruction
        ↓
Operational Visualization
```

The simulated fault is simply the input.

The Data Engineering behavior is the actual project result.

---

# 19. Conceptual Failure Diagram

A final documentation diagram should visualize the relationship between failure injection and Azure detection.

```text
               EVENT PRODUCER
                     │
                     ↓
              Logical Events
                     │
             ┌───────┴────────┐
             ↓                ↓
      Communication       Transport
         Layer              Layer
             │                │
      ┌──────┼──────┐   ┌────┼─────┐
      ↓      ↓      ↓   ↓    ↓     ↓
   Link    Fiber  Terminal Delay Drop Duplicate
   Loss   Exhaust  State
      └──────┬──────┘   └────┬─────┘
             │                │
             └───────┬────────┘
                     ↓
              Azure Event Hubs
                     ↓
              RawDroneEvents
                     ↓
         ┌───────────┼───────────┐
         ↓           ↓           ↓
      Quality     Timeliness    State
         │           │           │
         └───────────┼───────────┘
                     ↓
                Gold Serving
                     ↓
                  Dashboard
```

This diagram should emphasize the **data path**, not the physical failure mechanism.

---

# 20. Design Principles

### Failure scenarios must be deterministic

Known input conditions make downstream validation meaningful.

### Communication and transport are separate layers

A source unable to transmit is different from an event being altered after entering transport.

### Failure behavior must remain observable

Injected problems should produce measurable downstream signals.

### Event semantics survive imperfect delivery

`event_time`, `event_id`, and `source_sequence_number` remain critical under delay, duplication, and reordering.

### Missing telemetry does not mean missing state

Explicit state events and last-known observations may still provide meaningful operational context.

### The simulator remains supporting infrastructure

Failure simulation exists to exercise Azure Event Hubs, KQL processing, reliability analytics, state reconstruction, and serving.

---

# 21. Engineering Value

The main capability demonstrated by these scenarios is not failure simulation itself.

It is the ability to build a real-time analytical platform that can distinguish:

```text
Missing data
Delayed data
Duplicated data
Buffered data
Out-of-order data
Temporarily unavailable sources
Permanently unavailable sources
```

and still expose understandable stream-health and operational state information.

That capability is central to building trustworthy real-time Data Engineering systems.

---

### Continue

**Previous:** [State Reconstruction and Serving](state_reconstruction_and_serving.md)
**Documentation Hub:** [README](README.md)
**Next:** [Dashboard and Observability](dashboard_and_observability.md)

**Related:** [Stream Quality and Timeliness](stream_quality_and_timeliness.md)
**Architecture overview:** [Streaming and KQL Architecture](streaming_and_kql_architecture.md)
**Supporting producer:** [Simulator and Event Model](simulator_and_event_model.md)
