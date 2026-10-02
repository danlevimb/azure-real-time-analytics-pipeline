<p align="center">
  <a href="change_summary_v1_1.md">← Previous</a> |
  <a href="../README.md">Home</a> |
  <a href="README.md">Documentation</a> |
  <a href="README.md#implementation-history">History Home</a> |
  <a href="event_contract_v1_1_rollout.md">Next →</a>
</p>

---

# Connectivity Fault v1

> **Historical implementation record — v1.1.**
> This document preserves an earlier stage of the project and is not the current architecture or contract. Statements such as “next”, “not yet”, or “future” are scoped to that historical stage.
> For the current implementation, start with the [Documentation Hub](README.md) and [Event Contract v1.2](../contracts/event_contract_v1_2.md).

## Goal

Model an operational communications loss without turning it into a shared-transport fault.

## Runtime semantics

1. Mission physics and Ground Truth continue while the drone is disconnected.
2. Logical events can continue to be generated and receive their normal per-drone `source_sequence_number`.
3. Every generated event is recorded in `generated_events.jsonl`.
4. `CommsGate` decides whether the event can leave the producer.
5. Every communications decision is recorded in `comms_log.jsonl`.
6. An event accepted by `CommsGate` is then submitted to the existing `TransportEngine`.
7. Events blocked by communications never enter `TransportEngine`, `delivery_log.jsonl`, the file delivery sink, or Event Hubs.

## Disconnect transition

For v1, the `CONNECTED -> DISCONNECTED` state transition is treated as a final control indication that is allowed through the communications gate even though the in-memory drone state has already changed to `DISCONNECTED`.

This lets the cloud reconstruct the communications state while physical telemetry remains frozen at the last successfully observed sample.

## What v1 deliberately does not do

There is no producer-side backlog/replay yet. Events generated during a disconnection are retained only as local simulator evidence and are not retransmitted after reconnect.

Onboard buffering, reconnect backlog flush, burst delivery, and late-event analysis belong to **Connectivity Fault v2**.

## Boundary with TransportEngine

`TransportEngine` keeps its existing responsibility for faults that happen after producer submission:

- base delay
- buffering windows
- drop injection
- duplicate injection
- extra delay

A communications outage is therefore distinct from a transport fault.

---

<p align="center">
  <a href="change_summary_v1_1.md">← Previous</a> |
  <a href="../README.md">Home</a> |
  <a href="README.md">Documentation</a> |
  <a href="README.md#implementation-history">History Home</a> |
  <a href="event_contract_v1_1_rollout.md">Next →</a>
</p>
