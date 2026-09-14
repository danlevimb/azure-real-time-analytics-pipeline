import json
import unittest

from simulator.publishers.eventhub_publisher import (
    EventHubPublisher,
)


class FakeEventData:

    def __init__(
        self,
        body,
    ) -> None:

        self.body = body
        self.content_type = None


class FakeProducer:

    def __init__(
        self,
    ) -> None:

        self.sent = []
        self.closed = False
        self.flush_value = None

    def send_event(
        self,
        event_data,
        *,
        partition_key=None,
    ) -> None:

        self.sent.append(
            (
                event_data,
                partition_key,
            )
        )

    def close(
        self,
        *,
        flush=True,
    ) -> None:

        self.closed = True
        self.flush_value = flush


class EventHubPublisherTests(
    unittest.TestCase
):

    def _build_publisher(
        self,
    ):

        producer = FakeProducer()

        publisher = EventHubPublisher(
            fully_qualified_namespace=(
                "example.servicebus.windows.net"
            ),

            eventhub_name=(
                "eh-drone-events-v1"
            ),

            partition_key_field=(
                "drone_id"
            ),

            buffered_mode=True,

            producer_client=producer,

            event_data_factory=(
                FakeEventData
            ),

            credential=object(),
        )

        return publisher, producer

    def test_publish_uses_drone_id_partition_key(
        self,
    ):

        publisher, producer = (
            self._build_publisher()
        )

        event = {
            "event_id": "EVT-001",
            "drone_id": "DRN-003",
            "event_type": "telemetry",
        }

        publisher.publish(
            event
        )

        self.assertEqual(
            len(
                producer.sent
            ),
            1,
        )

        event_data, partition_key = (
            producer.sent[0]
        )

        self.assertEqual(
            partition_key,
            "DRN-003",
        )

        self.assertEqual(
            json.loads(
                event_data.body
            ),
            event,
        )

        self.assertEqual(
            event_data.content_type,
            "application/json",
        )

        self.assertEqual(
            publisher.enqueued_count,
            1,
        )

    def test_publish_requires_partition_key_field(
        self,
    ):

        publisher, _ = (
            self._build_publisher()
        )

        with self.assertRaises(
            ValueError
        ):

            publisher.publish(
                {
                    "event_id":
                        "EVT-002",
                }
            )

    def test_close_flushes_buffered_client(
        self,
    ):

        publisher, producer = (
            self._build_publisher()
        )

        publisher.close()

        self.assertTrue(
            producer.closed
        )

        self.assertTrue(
            producer.flush_value
        )


if __name__ == "__main__":
    unittest.main()
