class TimelinessScenarioValidator:

    def __init__(
        self,
        *,
        timeliness_result: dict,
        transport_config: dict,
        telemetry_interval_ms: int,
        tick_ms: int,
    ) -> None:

        self.timeliness_result = (
            timeliness_result
        )

        self.transport_config = (
            transport_config
        )

        self.telemetry_interval_ms = (
            telemetry_interval_ms
        )

        self.tick_ms = (
            tick_ms
        )

    def validate(
        self,
    ) -> dict:

        buffer_config = (
            self.transport_config.get(
                "buffering",
                {},
            )
        )

        buffering_enabled = (
            buffer_config.get(
                "enabled",
                False,
            )
        )

        producers = (
            self.timeliness_result[
                "producers"
            ]
        )

        base_delay_ms = float(
            self.transport_config.get(
                "base_delay_ms",
                0,
            )
        )

        # =================================================
        # No buffering scenario
        # =================================================

        if not buffering_enabled:

            return {
                "applicable": False,
                "scenario_passed": True,
                "target_producers": [],
                "degraded_producers": [],
                "healthy_producers": (
                    sorted(
                        producers
                    )
                ),
                "latency_spike_passed": True,
                "freshness_gap_passed": True,
                "recovery_burst_passed": True,
                "isolation_passed": True,
            }

        # =================================================
        # Scenario configuration
        # =================================================

        target_producers = set(
            buffer_config.get(
                "target_drone_ids",
                producers.keys(),
            )
        )

        start_seconds = float(
            buffer_config[
                "start_at_seconds"
            ]
        )

        end_seconds = float(
            buffer_config[
                "end_at_seconds"
            ]
        )

        window_seconds = (
            end_seconds
            - start_seconds
        )

        if window_seconds <= 0:

            raise ValueError(
                "Buffer window must have "
                "positive duration."
            )

        # =================================================
        # Thresholds
        #
        # We do NOT require an exact 10,000 ms spike.
        # A telemetry cadence may not align exactly with
        # the beginning of a future buffer window.
        # =================================================

        expected_min_latency_spike_ms = max(
            base_delay_ms,
            (
                window_seconds
                * 1000.0
                -
                self.telemetry_interval_ms
            ),
        )

        expected_min_freshness_gap_s = max(
            0.0,
            (
                window_seconds
                -
                self.telemetry_interval_ms
                / 1000.0
            ),
        )

        # Healthy producers receive normal traffic.
        #
        # One simulation tick of tolerance prevents
        # harmless scheduler granularity from becoming
        # an anomaly.
        healthy_latency_limit_ms = (
            base_delay_ms
            + self.tick_ms
        )

        healthy_gap_limit_s = (
            self.telemetry_interval_ms
            / 1000.0
            +
            self.tick_ms
            / 1000.0
        )

        # =================================================
        # Target producer validation
        # =================================================

        latency_spike_by_target = {}

        freshness_gap_by_target = {}

        recovery_burst_by_target = {}

        for drone_id in sorted(
            target_producers
        ):

            producer = producers.get(
                drone_id
            )

            if producer is None:

                latency_spike_by_target[
                    drone_id
                ] = False

                freshness_gap_by_target[
                    drone_id
                ] = False

                recovery_burst_by_target[
                    drone_id
                ] = False

                continue

            latency_spike_by_target[
                drone_id
            ] = (
                producer[
                    "latency_max_ms"
                ]
                >=
                expected_min_latency_spike_ms
            )

            freshness_gap_by_target[
                drone_id
            ] = (
                producer[
                    "max_telemetry_gap_seconds"
                ]
                >=
                expected_min_freshness_gap_s
            )

            # Normal behavior can create a burst of 2
            # when transition + telemetry share a tick.
            #
            # A recovery burst must be meaningfully
            # larger than that normal condition.
            recovery_burst_by_target[
                drone_id
            ] = (
                producer[
                    "max_burst_size"
                ]
                > 2
            )

        latency_spike_passed = all(
            latency_spike_by_target.values()
        )

        freshness_gap_passed = all(
            freshness_gap_by_target.values()
        )

        recovery_burst_passed = all(
            recovery_burst_by_target.values()
        )

        # =================================================
        # Isolation validation
        #
        # Producers outside the target set must remain
        # near nominal latency and telemetry cadence.
        # =================================================

        healthy_producers = sorted(
            set(producers)
            -
            target_producers
        )

        unexpected_degradation = []

        for drone_id in healthy_producers:

            producer = producers[
                drone_id
            ]

            if (
                producer[
                    "latency_max_ms"
                ]
                >
                healthy_latency_limit_ms
                or
                producer[
                    "max_telemetry_gap_seconds"
                ]
                >
                healthy_gap_limit_s
            ):

                unexpected_degradation.append(
                    drone_id
                )

        isolation_passed = (
            len(
                unexpected_degradation
            )
            == 0
        )

        # =================================================
        # Observed degraded producers
        # =================================================

        degraded_producers = []

        for (
            drone_id,
            producer,
        ) in producers.items():

            if (
                producer[
                    "latency_max_ms"
                ]
                >
                healthy_latency_limit_ms
                or
                producer[
                    "max_telemetry_gap_seconds"
                ]
                >
                healthy_gap_limit_s
            ):

                degraded_producers.append(
                    drone_id
                )

        degraded_producers.sort()

        target_match_passed = (
            set(
                degraded_producers
            )
            ==
            target_producers
        )

        # =================================================
        # Final scenario validation
        # =================================================

        scenario_passed = all(
            [
                latency_spike_passed,
                freshness_gap_passed,
                recovery_burst_passed,
                isolation_passed,
                target_match_passed,
            ]
        )

        return {
            "applicable": True,

            "buffer_window_seconds":
                window_seconds,

            "target_producers":
                sorted(
                    target_producers
                ),

            "healthy_producers":
                healthy_producers,

            "degraded_producers":
                degraded_producers,

            "unexpected_degradation":
                unexpected_degradation,

            "expected_min_latency_spike_ms":
                expected_min_latency_spike_ms,

            "expected_min_freshness_gap_s":
                expected_min_freshness_gap_s,

            "latency_spike_by_target":
                latency_spike_by_target,

            "freshness_gap_by_target":
                freshness_gap_by_target,

            "recovery_burst_by_target":
                recovery_burst_by_target,

            "latency_spike_passed":
                latency_spike_passed,

            "freshness_gap_passed":
                freshness_gap_passed,

            "recovery_burst_passed":
                recovery_burst_passed,

            "isolation_passed":
                isolation_passed,

            "target_match_passed":
                target_match_passed,

            "scenario_passed":
                scenario_passed,
        }