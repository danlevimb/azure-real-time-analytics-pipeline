# Event Contract v1.1 rollout

## Change

Event Contract v1.1 is backward-compatible with v1.0 and adds:

`payload.consumables.optic_fiber_remaining_m`

The simulator models the value as a monotonic consumable measured in meters. One meter is consumed for each meter of simulated travel. Reaching zero is observational only in v1.1 and does not automatically terminate a mission or communications link.

## Azure Data Explorer rollout order

Perform the schema migration while no simulator run is actively ingesting.

1. Run `kql/09_contract_v1_1_migration.kql`.
2. Re-run `kql/02_transform_functions.kql`.
3. Re-run `kql/04_materialized_views.kql`.
4. Re-run `kql/06_state_functions.kql`.
5. Re-run `kql/07_serving_functions.kql`.

The update-policy target schema and transform output must stay aligned. The new parsed column is appended to `TelemetryParsed`, so the transform also projects it last.

Historical v1.0 rows remain valid and expose `optic_fiber_remaining_m = null` in Silver/Canonical/Gold.

## Validation queries

```kusto
TelemetryCanonical
| where schema_version == "1.1"
| top 20 by bronze_ingested_at desc
| project
    simulator_run_id,
    drone_id,
    source_sequence_number,
    battery_pct,
    optic_fiber_remaining_m,
    bronze_ingested_at
```

```kusto
CurrentFleetOperationalSummary()
| project
    TotalDrones,
    ConnectivityPct,
    HealthyPct,
    AvgBatteryPct,
    MinBatteryPct,
    AvgOpticFiberRemainingM,
    MinOpticFiberRemainingM
```

```kusto
CurrentFleetMapView()
| project
    drone_id,
    connection_state,
    mission_phase,
    battery_pct,
    optic_fiber_remaining_m,
    telemetry_as_of,
    state_as_of
| order by drone_id asc
```

## Validation run configuration

Use:

```powershell
./scripts/run_simulation.ps1 -Config fleet250_connectivity_failure_v11_cloud.yaml
```

The configuration uses a new `RunId` so it does not overwrite the previous connectivity run.
