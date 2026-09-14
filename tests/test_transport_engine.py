import unittest

from simulator.transport.transport_engine import (TransportEngine,)

class TestTransportEngine(unittest.TestCase):

    def test_fixed_delay(
        self,
    ):

        engine = TransportEngine(base_delay_ms=1000,)

        event = {
            "event_id": "EVT-001",
            "source_sequence_number": 1,
        }

        engine.submit(event=event, current_seconds=0.0,)

        released, _ = engine.release_ready(current_seconds=0.75)

        self.assertEqual(released, [],)

        released, _ = engine.release_ready(current_seconds=1.0)

        self.assertEqual(len(released), 1,)

        self.assertEqual(released[0]["event_id"], "EVT-001",)

    def test_buffer_releases_as_burst(
        self,
    ):

        engine = TransportEngine(
            base_delay_ms=0,
            buffering_enabled=True,
            buffer_start_seconds=2.0,
            buffer_end_seconds=4.0,
        )

        event_1 = {
            "event_id": "EVT-001",
            "source_sequence_number": 1,
        }

        event_2 = {
            "event_id": "EVT-002",
            "source_sequence_number": 2,
        }

        engine.submit(
            event=event_1,
            current_seconds=2.5,
        )

        engine.submit(
            event=event_2,
            current_seconds=3.0,
        )

        released, _ = (
            engine.release_ready(
                current_seconds=3.5
            )
        )

        self.assertEqual(
            released,
            [],
        )

        self.assertEqual(
            engine.buffered_count,
            2,
        )

        released, burst_count = (
            engine.release_ready(
                current_seconds=4.0
            )
        )

        self.assertEqual(
            burst_count,
            2,
        )

        self.assertEqual(
            [
                event[
                    "source_sequence_number"
                ]
                for event in released
            ],
            [1, 2],
        )
    
    def test_duplicate_event_is_delivered_twice(
        self,
    ):

        engine = TransportEngine(
            duplicate_sequences={
                10
            },
        )

        event = {
            "event_id": "EVT-010",
            "source_sequence_number": 10,
        }

        engine.submit(
            event=event,
            current_seconds=1.0,
        )

        released, _ = (
            engine.release_ready(
                current_seconds=1.0
            )
        )

        self.assertEqual(
            len(released),
            2,
        )

        self.assertEqual(
            released[0]["event_id"],
            released[1]["event_id"],
        )


    def test_dropped_event_is_never_delivered(
        self,
    ):

        engine = TransportEngine(
            drop_sequences={
                10
            },
        )

        event = {
            "event_id": "EVT-010",
            "source_sequence_number": 10,
        }

        submission = engine.submit(
            event=event,
            current_seconds=1.0,
        )

        self.assertTrue(
            submission.dropped
        )

        released, _ = (
            engine.release_ready(
                current_seconds=100.0
            )
        )

        self.assertEqual(
            released,
            [],
        )


    def test_extra_delay_can_create_out_of_order_delivery(
        self,
    ):

        engine = TransportEngine(
            base_delay_ms=0,
            extra_delay_ms_by_sequence={
                1: 3000
            },
        )

        event_1 = {
            "event_id": "EVT-001",
            "source_sequence_number": 1,
        }

        event_2 = {
            "event_id": "EVT-002",
            "source_sequence_number": 2,
        }

        engine.submit(
            event=event_1,
            current_seconds=0.0,
        )

        engine.submit(
            event=event_2,
            current_seconds=1.0,
        )

        released, _ = (
            engine.release_ready(
                current_seconds=1.0
            )
        )

        self.assertEqual(
            [
                event[
                    "source_sequence_number"
                ]
                for event in released
            ],
            [2],
        )

        released, _ = (
            engine.release_ready(
                current_seconds=3.0
            )
        )

        self.assertEqual(
            [
                event[
                    "source_sequence_number"
                ]
                for event in released
            ],
            [1],
        )
    
    def test_duplicate_target_affects_only_one_drone(
        self,
    ):

        engine = TransportEngine(
            duplicate_targets={
                (
                    "DRN-003",
                    10,
                )
            }
        )

        drone_1_event = {
            "event_id": "D1-E10",
            "drone_id": "DRN-001",
            "source_sequence_number": 10,
        }

        drone_3_event = {
            "event_id": "D3-E10",
            "drone_id": "DRN-003",
            "source_sequence_number": 10,
        }

        engine.submit(
            event=drone_1_event,
            current_seconds=1.0,
        )

        engine.submit(
            event=drone_3_event,
            current_seconds=1.0,
        )

        released, _ = (
            engine.release_ready(
                current_seconds=1.0
            )
        )

        drone_1_count = sum(
            1
            for event in released
            if event["drone_id"]
            == "DRN-001"
        )

        drone_3_count = sum(
            1
            for event in released
            if event["drone_id"]
            == "DRN-003"
        )

        self.assertEqual(
            drone_1_count,
            1,
        )

        self.assertEqual(
            drone_3_count,
            2,
        )


    def test_drop_target_affects_only_one_drone(
        self,
    ):

        engine = TransportEngine(
            drop_targets={
                (
                    "DRN-003",
                    10,
                )
            }
        )

        drone_1_event = {
            "event_id": "D1-E10",
            "drone_id": "DRN-001",
            "source_sequence_number": 10,
        }

        drone_3_event = {
            "event_id": "D3-E10",
            "drone_id": "DRN-003",
            "source_sequence_number": 10,
        }

        engine.submit(
            event=drone_1_event,
            current_seconds=1.0,
        )

        engine.submit(
            event=drone_3_event,
            current_seconds=1.0,
        )

        released, _ = (
            engine.release_ready(
                current_seconds=1.0
            )
        )

        delivered_ids = {
            event["event_id"]
            for event
            in released
        }

        self.assertIn(
            "D1-E10",
            delivered_ids,
        )

        self.assertNotIn(
            "D3-E10",
            delivered_ids,
        )

    def test_extra_delay_target_affects_only_one_drone(
        self,
    ):

        engine = TransportEngine(
            extra_delay_ms_by_target={
                (
                    "DRN-003",
                    10,
                ):
                3000
            }
        )

        drone_1_event = {
            "event_id": "D1-E10",
            "drone_id": "DRN-001",
            "source_sequence_number": 10,
        }

        drone_3_event = {
            "event_id": "D3-E10",
            "drone_id": "DRN-003",
            "source_sequence_number": 10,
        }

        engine.submit(
            event=drone_1_event,
            current_seconds=1.0,
        )

        engine.submit(
            event=drone_3_event,
            current_seconds=1.0,
        )

        released, _ = (
            engine.release_ready(
                current_seconds=1.0
            )
        )

        self.assertEqual(
            [
                event["event_id"]
                for event in released
            ],
            [
                "D1-E10"
            ],
        )

        released, _ = (
            engine.release_ready(
                current_seconds=4.0
            )
        )

        self.assertEqual(
            [
                event["event_id"]
                for event in released
            ],
            [
                "D3-E10"
            ],
        )

    def test_targeted_buffer_affects_only_selected_drone(
        self,
    ):

        engine = TransportEngine(
            buffering_enabled=True,
            buffer_start_seconds=1.0,
            buffer_end_seconds=3.0,

            buffer_target_drone_ids={
                "DRN-003"
            },
        )

        healthy_event = {
            "event_id": "D1-E10",
            "drone_id": "DRN-001",
            "source_sequence_number": 10,
        }

        buffered_event = {
            "event_id": "D3-E10",
            "drone_id": "DRN-003",
            "source_sequence_number": 10,
        }

        engine.submit(
            event=healthy_event,
            current_seconds=1.5,
        )

        engine.submit(
            event=buffered_event,
            current_seconds=1.5,
        )

        released, buffer_count = (
            engine.release_ready(
                current_seconds=1.5
            )
        )

        self.assertEqual(
            [
                event["event_id"]
                for event in released
            ],
            [
                "D1-E10"
            ],
        )

        self.assertEqual(
            buffer_count,
            0,
        )

        self.assertEqual(
            engine.buffered_count,
            1,
        )

        released, buffer_count = (
            engine.release_ready(
                current_seconds=3.0
            )
        )

        self.assertEqual(
            buffer_count,
            1,
        )

        self.assertEqual(
            [
                event["event_id"]
                for event in released
            ],
            [
                "D3-E10"
            ],
        )
    
    def test_legacy_buffer_without_targets_affects_all_events(
        self,
    ):

        engine = TransportEngine(
            buffering_enabled=True,
            buffer_start_seconds=1.0,
            buffer_end_seconds=3.0,
        )

        event = {
            "event_id": "LEGACY-E10",
            "source_sequence_number": 10,
        }

        submission = engine.submit(
            event=event,
            current_seconds=1.5,
        )

        self.assertTrue(
            submission.buffered
        )

        self.assertEqual(
            engine.buffered_count,
            1,
        )
    
    
if __name__ == "__main__":
    unittest.main()