# Stream Quality and Timeliness

> **Documentation path:**
> [Documentation Hub](README.md) →
> [Streaming & KQL Architecture](streaming_and_kql_architecture.md) →
> **Stream Quality & Timeliness** →
> [State Reconstruction & Serving](state_reconstruction_and_serving.md)

**Project:** `azure-real-time-analytics-pipeline`
**Focus:** Real-time stream integrity, reconciliation, arrival behavior, and latency

---

## 1. Purpose

A real-time pipeline is not trustworthy simply because events are arriving.

The platform must also be able to determine whether the stream is:

* Complete
* Unique
* Correctly ordered
* Reconciled across analytical layers
* Timely enough for operational use

This project therefore evaluates two separate dimensions:

```text
STREAM INTEGRITY
Did the expected logical data arrive correctly?

STREAM TIMELINESS
How did that data arrive over time?
```

These dimensions are intentionally independent.

A stream can be:

```text
Complete but late
```

or:

```text
Fast but incomplete
```

Both conditions matter in real-time Data Engineering.

---

## 2. Source Sequence as the Integrity Baseline

Each producer maintains its own:

```text
source_sequence_number
```

across the complete logical event stream.

This provides a deterministic ordering reference for each asset.

Conceptually:

```text
Expected

1  2  3  4  5  6
```

Observed:

```text
1  2  4  5  5  6
```

This reveals two separate conditions:

```text
Missing sequence → 3
Duplicate delivery → 5
```

Sequence analysis therefore provides more information than comparing total row counts.

---

## 3. Integrity Signals

The current analytical model exposes several stream-integrity signals.

The dashboard consumes:

```text
CurrentStreamIntegrityReport()
```

and surfaces metrics including:

```text
DuplicateDeliveries
SequenceGaps
MissingSequences
OutOfOrderTransitions
NullEhMetadata
```

These metrics answer different questions.

### Duplicate Deliveries

Indicates that the same logical event was physically delivered more than once.

### Sequence Gaps

Indicates discontinuities in the observed source sequence.

### Missing Sequences

Represents logical sequence numbers expected from the producer but not observed in the analytical stream.

### Out-of-Order Transitions

Identifies ordering behavior where physical arrival does not follow expected logical sequence.

### Null Event Hubs Metadata

Detects cases where expected transport metadata is unavailable.

---

## 4. Physical Delivery vs Logical Event

The project deliberately separates physical delivery from logical identity.

Example:

```text
Physical arrivals

E41
E42
E42
E43
```

After canonicalization:

```text
Logical events

E41
E42
E43
```

The duplicate remains visible in the raw layer while the canonical layer represents one logical event per `event_id`.

This allows the platform to preserve transport evidence without allowing duplicated physical delivery to corrupt downstream analytical state.

---

## 5. Raw-to-Canonical Reconciliation

Stream quality is also evaluated between:

```text
RawDroneEvents
```

and canonical event representations such as:

```text
TelemetryCanonical
StateTransitionsCanonical
```

The current dashboard performs reconciliation using values such as:

```text
RawRows
RawUniqueEventIds
RawDuplicates

CanonicalRows
UniqueCanonicalEventIds
Difference
ReconciliationStatus
```

Conceptually, healthy canonicalization should satisfy:

```text
Raw unique logical events
        =
Canonical unique logical events
```

while:

```text
Raw physical rows
```

may legitimately be higher because duplicate deliveries remain observable in the raw layer.

---

## 6. Why Reconciliation Matters

Without reconciliation, a canonical layer could appear healthy while silently losing events.

For example:

```text
RAW

100 physical rows
98 unique event IDs
```

and:

```text
CANONICAL

97 unique event IDs
```

would indicate two different phenomena:

```text
2 duplicate physical deliveries
+
1 logical event missing from canonical
```

Those conditions should not be collapsed into a single row-count difference.

The project therefore evaluates physical delivery and logical identity separately.

---

## 7. Event Time and Arrival Time

Real-time analysis requires more than one clock.

The architecture preserves:

```text
event_time
```

when the source event occurred,

```text
eh_enqueued_time
```

when Event Hubs observed the event,

and:

```text
bronze_ingested_at
```

when the analytical processing layer observed it.

Conceptually:

```text
Source Event
    │
    │ event_time
    ↓
Network / Transport
    │
    │ eh_enqueued_time
    ↓
Event Hubs
    │
    ↓
Analytical Processing
    │
    │ bronze_ingested_at
    ↓
KQL Layers
```

These timestamps allow the project to analyze transport and analytical delay rather than treating all times as equivalent.

---

## 8. Timeliness Metrics

The dashboard consumes:

```text
CurrentStreamTimelinessReport()
```

and exposes metrics including:

```text
P95RelativeDelayMs
MaxRelativeDelayMs
MaxPhysicalGapMs
P95CloudLatencyMs
MaxCloudLatencyMs
```

The producer-side validation tooling also evaluates latency distributions including P50, P95, P99, and maximum latency, together with maximum telemetry gaps and burst size.

These measurements provide different views of arrival behavior rather than relying on a single average.

---

## 9. Relative Delay

Relative delay helps identify events that arrived significantly later than neighboring events in the same stream.

Conceptually:

```text
Expected progression

41 → 42 → 43 → 44
```

but:

```text
41 arrives
43 arrives
44 arrives
42 arrives later
```

The logical sequence remains known, but the physical delivery pattern has changed.

This is the type of condition that event-time-aware processing must distinguish from normal ordered delivery.

---

## 10. Physical Arrival Gaps

A physical arrival gap measures periods where expected event activity temporarily disappears from the observed stream.

For example:

```text
regular arrivals

● ● ● ● ●

           <──── gap ────>

                       ● ● ● ●
```

A large gap does not automatically mean events were permanently lost.

Possible causes may include:

* Network interruption
* Producer connectivity loss
* Intentional buffering
* Additional transport delay

The integrity layer determines whether events are actually missing.

The timeliness layer determines how they arrived.

---

## 11. Buffered Delivery and Bursts

Reconnect scenarios can intentionally buffer events before transmission resumes.

Conceptually:

```text
Generated

41 42 43 44 45 46
```

during a connectivity interruption:

```text
41 42 delivered

43 44 45 buffered
```

after reconnect:

```text
43 44 45 → released as a burst

46 → normal delivery resumes
```

This may result in:

* A visible physical arrival gap
* High relative delay
* A burst of several events
* No permanently missing logical events

This is a useful example of why:

```text
timeliness degradation
```

does not necessarily imply:

```text
integrity failure
```

---

## 12. Burst Detection

The current analytical model also exposes burst-related information through:

```text
CurrentStreamTimelinessReport()
```

including values such as:

```text
BurstDrone
MaxBurstEvents
BurstFirstSeq
BurstLastSeq
```

This makes reconnect behavior visible at the analytical layer.

A burst can therefore be traced back to the affected producer and sequence range rather than appearing only as a temporary spike in dashboard volume.

---

## 13. Producer-Side Validation

The simulator also maintains an independent validation perspective.

Producer-side reconciliation tracks values such as:

```text
Generated logical events
Published physical events
Unique published events

Missing events
Duplicate deliveries
Out-of-order arrivals
Mutated deliveries
Unexpected events
```

It also compares configured fault targets with observed behavior.

For controlled scenarios, the producer can therefore answer:

```text
What failure was intentionally injected?
```

while the Azure analytical layer answers:

```text
What failure was observed downstream?
```

This separation provides stronger validation than testing only from one side of the pipeline.

---

## 14. Reliability Model

The complete quality model can be understood as three comparisons:

```text
Producer Intent
      ↓
Generated Logical Events
      ↓
Physical Delivery
      ↓
Azure Raw Ingestion
      ↓
Canonical Logical Events
```

Each boundary answers a different question.

### Generated → Delivered

Did transport alter delivery?

### Delivered → Raw

Did the cloud ingestion path receive what was released?

### Raw → Canonical

Did analytical processing preserve every unique logical event?

This gives the project multiple observable checkpoints rather than one final dashboard result.

---

## 15. Why Row Counts Alone Are Insufficient

Suppose:

```text
Generated events = 100
Raw rows        = 100
```

At first glance, this appears healthy.

But the raw stream could actually contain:

```text
99 unique events
+
1 duplicate
+
1 missing logical event
```

The physical row count would still equal 100.

For this reason the project combines:

```text
row counts
+
distinct event IDs
+
source sequence analysis
+
arrival ordering
+
timeliness metrics
```

to assess reliability.

---

## 16. Dashboard Role

Stream-quality metrics are exposed as operational signals rather than hidden troubleshooting queries.

The dashboard includes dedicated views for:

```text
Stream integrity
Timeliness
Raw vs canonical reconciliation
Latest observed run
Burst behavior
```

This makes data-pipeline health visible alongside business or operational telemetry.

The dashboard is therefore observing not only the simulated assets, but also the **health of the data stream itself**.

---

## 17. Conceptual Quality Model

A final diagram should visualize the distinction between logical integrity and physical arrival behavior.

```text
              PRODUCER
                 │
                 ↓
        Logical Event Stream
        1 2 3 4 5 6 7 8
                 │
                 ↓
           TRANSPORT
        ┌────────┼─────────┐
        │        │         │
      DROP    DELAY    DUPLICATE
        │        │         │
        └────────┼─────────┘
                 ↓
           EVENT HUBS
                 │
                 ↓
        Raw Physical Stream
                 │
       ┌─────────┴─────────┐
       ↓                   ↓
   INTEGRITY            TIMELINESS
       │                   │
 Missing seq           Relative delay
 Duplicates            Arrival gaps
 Reordering            Cloud latency
 Metadata              Bursts
       │                   │
       └─────────┬─────────┘
                 ↓
          STREAM HEALTH
```

This diagram will later be added under `diagrams/`.

---

## 18. Design Principles

### Integrity and timeliness are independent

Completeness does not guarantee freshness.

### Logical identity matters more than physical row count

`event_id` and producer sequencing provide the basis for meaningful reconciliation.

### Raw duplicates should remain observable

Canonicalization should correct analytical interpretation without destroying transport evidence.

### Event time must remain distinct from arrival time

Late or reordered delivery cannot be understood otherwise.

### Controlled failures improve validation

Known fault scenarios provide measurable expected outcomes.

### Stream health belongs in operational analytics

Reliability should be visible, not buried in troubleshooting queries.

---

## 19. Engineering Value

The primary lesson demonstrated by this layer is:

```text
A real-time pipeline should not merely process events.

It should be able to explain whether those events arrived
completely, uniquely, in the expected logical order,
and within an operationally meaningful time window.
```

This moves the project beyond simple streaming ingestion into real-time **data reliability engineering**.

---

### Continue

**Previous:** [Streaming and KQL Architecture](streaming_and_kql_architecture.md)
**Documentation Hub:** [README](README.md)
**Next:** [State Reconstruction and Serving](state_reconstruction_and_serving.md)

**Related:** [Communications and Failure Scenarios](communications_and_failure_scenarios.md)
**Supporting producer model:** [Simulator and Event Model](simulator_and_event_model.md)
