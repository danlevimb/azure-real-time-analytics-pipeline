import json
from threading import Lock


class EventHubPublisher:

    def __init__(
        self,
        *,
        fully_qualified_namespace: str,
        eventhub_name: str,
        partition_key_field: str = "drone_id",
        buffered_mode: bool = True,
        max_wait_time_seconds: float = 0.5,
        producer_client=None,
        event_data_factory=None,
        credential=None,
    ) -> None:

        self.fully_qualified_namespace =  fully_qualified_namespace

        self.eventhub_name = eventhub_name
        self.partition_key_field = partition_key_field
        self.buffered_mode = buffered_mode
        self.max_wait_time_seconds = max_wait_time_seconds
        self._lock = Lock()
        self._enqueued_count = 0
        self._confirmed_count = 0
        self._failed_count = 0
        self._errors = []

        self._owns_credential = (
            credential is None
        )

        if (
            producer_client is None
            or event_data_factory is None
        ):

            from azure.eventhub import (
                EventData,
                EventHubProducerClient,
            )

            from azure.identity import (
                DefaultAzureCredential,
            )

            if credential is None:

                credential = (
                    DefaultAzureCredential()
                )

            if producer_client is None:

                producer_client = (
                    EventHubProducerClient(
                        fully_qualified_namespace=(
                            self.
                            fully_qualified_namespace
                        ),

                        eventhub_name=(
                            self.eventhub_name
                        ),

                        credential=credential,

                        buffered_mode=(
                            self.buffered_mode
                        ),

                        on_success=(
                            self._on_success
                            if self.buffered_mode
                            else None
                        ),

                        on_error=(
                            self._on_error
                            if self.buffered_mode
                            else None
                        ),

                        max_wait_time=(
                            self.
                            max_wait_time_seconds
                            if self.buffered_mode
                            else None
                        ),
                    )
                )

            if event_data_factory is None:

                event_data_factory = EventData

        self._credential = credential
        self._producer = producer_client

        self._event_data_factory = (
            event_data_factory
        )

    @staticmethod
    def _count_events(
        events,
    ) -> int:

        try:

            return len(events)

        except TypeError:

            return 1

    def _on_success(
        self,
        events,
        partition_id,
    ) -> None:

        event_count = self._count_events(
            events
        )

        with self._lock:

            self._confirmed_count += (
                event_count
            )

    def _on_error(
        self,
        events,
        partition_id,
        error,
    ) -> None:

        event_count = self._count_events(
            events
        )

        with self._lock:

            self._failed_count += event_count

            self._errors.append(
                {
                    "partition_id":
                        partition_id,

                    "event_count":
                        event_count,

                    "error":
                        repr(error),
                }
            )

    def _raise_if_failed(
        self,
    ) -> None:

        with self._lock:

            if not self._errors:
                return

            first_error = (
                self._errors[0]
            )

            failed_count = (
                self._failed_count
            )

        raise RuntimeError(
            "Azure Event Hubs buffered "
            "publisher reported "
            f"{failed_count} failed "
            "event(s). First error: "
            f"{first_error}"
        )

    @property
    def enqueued_count(
        self,
    ) -> int:

        with self._lock:

            return self._enqueued_count

    @property
    def confirmed_count(
        self,
    ) -> int:

        with self._lock:

            return self._confirmed_count

    @property
    def failed_count(
        self,
    ) -> int:

        with self._lock:

            return self._failed_count

    def publish(
        self,
        event: dict,
    ) -> None:

        self._raise_if_failed()

        partition_key = event.get(
            self.partition_key_field
        )

        if (
            not isinstance(
                partition_key,
                str,
            )
            or not partition_key
        ):

            raise ValueError(
                "Event Hubs partition key "
                f"field "
                f"'{self.partition_key_field}' "
                "must contain a non-empty "
                "string"
            )

        body = json.dumps(
            event,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        event_data = (
            self._event_data_factory(
                body
            )
        )

        if hasattr(
            event_data,
            "content_type",
        ):

            event_data.content_type = (
                "application/json"
            )

        try:

            self._producer.send_event(
                event_data,
                partition_key=(
                    partition_key
                ),
            )

        except Exception as exc:

            event_id = event.get(
                "event_id",
                "<unknown>",
            )

            raise RuntimeError(
                "Azure Event Hubs publish "
                "failed while enqueueing "
                f"event_id={event_id}"
            ) from exc

        with self._lock:

            self._enqueued_count += 1

        self._raise_if_failed()

    def close(
        self,
    ) -> None:

        close_error = None

        try:

            if self.buffered_mode:

                self._producer.close(
                    flush=True
                )

            else:

                self._producer.close()

        except Exception as exc:

            close_error = exc

        finally:

            if (
                self._owns_credential
                and self._credential
                is not None
                and hasattr(
                    self._credential,
                    "close",
                )
            ):

                self._credential.close()

        self._raise_if_failed()

        if close_error is not None:

            raise RuntimeError(
                "Azure Event Hubs producer "
                "failed while closing/"
                "flushing"
            ) from close_error
