# Local validation: Contract v1.1 + Connectivity Fault v1

Validation was executed locally with a two-drone derivative of the v1.1 connectivity configuration, Event Hubs disabled, and accelerated wall-clock pacing.

## Automated suite

- `100 passed`

Coverage added for:

- Event Contract v1.0 and v1.1 JSON schemas
- v1.1 optical-fiber telemetry
- optical-fiber consumption model
- operational-profile validation
- connectivity disconnect/reconnect behavior
- communications gate behavior
- local state projection of optical-fiber remaining

## End-to-end local behavior for DRN-001

- Disconnect transition: sequence `124`
- Events generated after disconnect: `48`
- Events blocked by producer communications after disconnect: `48`
- Events delivered after disconnect: `0`
- Last delivered sequence: `124`
- Last generated sequence: `172`
- Initial optical fiber: `10000.0 m`
- Final optical fiber: approximately `8277.10 m`
- Ground Truth final mission phase: `LANDED`
- Ground Truth final connection state: `DISCONNECTED`

This demonstrates the intended separation:

- the drone continues its physical mission and keeps generating logical events;
- the cloud stream stops at the final disconnect indication;
- local evidence preserves what happened after loss of communications.
