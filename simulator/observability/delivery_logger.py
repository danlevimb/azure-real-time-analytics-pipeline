import json

from datetime import datetime
from pathlib import Path


class DeliveryLogger:

    def __init__(
        self,
        *,
        output_path: Path,
        simulator_run_id: str,
    ) -> None:

        self.output_path = output_path
        self.simulator_run_id = (
            simulator_run_id
        )

        self.output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._file = self.output_path.open("w", encoding="utf-8",)

    @staticmethod
    def _format_datetime(
        value: datetime,
    ) -> str:

        return (
            value
            .isoformat()
            .replace("+00:00", "Z")
        )

    def log_delivery(
        self,
        *,
        event: dict,
        delivered_at: datetime,
        delivered_at_seconds: float,
    ) -> None:

        event_time = datetime.fromisoformat(
            event["event_time"].replace(
                "Z",
                "+00:00",
            )
        )

        delivery_latency_ms = (
            delivered_at
            - event_time
        ).total_seconds() * 1000.0

        record = {
            "record_type": ("transport_delivery"),

            "simulator_run_id": (
                self.simulator_run_id
            ),

            "event_id": (
                event["event_id"]
            ),

            "event_type": (
                event["event_type"]
            ),

            "drone_id": (
                event["drone_id"]
            ),

            "source_sequence_number": (
                event[
                    "source_sequence_number"
                ]
            ),

            "event_time": (
                event["event_time"]
            ),

            "delivered_at": (
                self._format_datetime(
                    delivered_at
                )
            ),

            "delivered_at_seconds": (
                delivered_at_seconds
            ),

            "delivery_latency_ms": (
                delivery_latency_ms
            ),
        }

        json.dump(
            record,
            self._file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        self._file.write("\n")
        self._file.flush()

    def close(self) -> None:

        self._file.close()