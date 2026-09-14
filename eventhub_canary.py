import json
from datetime import datetime, timezone

from azure.eventhub import EventData, EventHubProducerClient
from azure.identity import DefaultAzureCredential


FULLY_QUALIFIED_NAMESPACE = (
    "ehns-drone-rti-dev-eus-01.servicebus.windows.net"
)

EVENT_HUB_NAME = "eh-drone-events-v1"


def main():

    credential = DefaultAzureCredential()

    producer = EventHubProducerClient(
        fully_qualified_namespace=(
            FULLY_QUALIFIED_NAMESPACE
        ),
        eventhub_name=EVENT_HUB_NAME,
        credential=credential,
    )

    canary = {
        "message_kind": "transport_canary",
        "probe_id": "CANARY-001",
        "sent_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "producer": "local-development",
    }

    event = EventData(
        json.dumps(canary)
    )

    print(
        "[CANARY] Connecting to Azure Event Hubs..."
    )

    with producer:

        producer.send_event(
            event,
            partition_key="CANARY-001",
        )

    print(
        "[CANARY] SENT successfully"
    )


if __name__ == "__main__":
    main()