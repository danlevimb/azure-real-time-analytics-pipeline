import json
from datetime import datetime
from pathlib import Path

from simulator.communications.comms_gate import CommsDecision


class CommsLogger:
    """Local evidence for producer-side transmission decisions."""

    def __init__(
        self,
        *,
        output_path: Path,
        simulator_run_id: str,
    ) -> None:

        self.output_path = output_path
        self.simulator_run_id = simulator_run_id

        self.output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._file = self.output_path.open(
            "w",
            encoding="utf-8",
        )

    @staticmethod
    def _format_datetime(
        value: datetime,
    ) -> str:

        return (
            value
            .isoformat()
            .replace("+00:00", "Z")
        )

    def log_decision(
        self,
        *,
        event: dict,
        decision: CommsDecision,
        connection_state: str,
        decided_at: datetime,
        decided_at_seconds: float,
    ) -> None:

        record = {
            "record_type": "comms_decision",
            "simulator_run_id": self.simulator_run_id,
            "event_id": event["event_id"],
            "event_type": event["event_type"],
            "drone_id": event["drone_id"],
            "source_sequence_number": (
                event["source_sequence_number"]
            ),
            "connection_state": connection_state,
            "transmit": decision.transmit,
            "reason": decision.reason,
            "decided_at": self._format_datetime(
                decided_at
            ),
            "decided_at_seconds": decided_at_seconds,
        }

        json.dump(
            record,
            self._file,
            ensure_ascii=False,
            separators=(",", ":"),
        )

        self._file.write("\n")
        self._file.flush()

    def log_buffer_action(
        self,
        *,
        event: dict,
        action: str,
        connection_state: str,
        acted_at: datetime,
        acted_at_seconds: float,
    ) -> None:

        if action not in {
            "BUFFERED",
            "FLUSHED",
        }:

            raise ValueError(
                "Unsupported buffer action: "
                f"{action}"
            )

        record = {
            "record_type": (
                "comms_buffer_action"
            ),
            "simulator_run_id": (
                self.simulator_run_id
            ),
            "event_id": event["event_id"],
            "event_type": event["event_type"],
            "event_time": event["event_time"],
            "drone_id": event["drone_id"],
            "source_sequence_number": (
                event[
                    "source_sequence_number"
                ]
            ),
            "connection_state": (
                connection_state
            ),
            "action": action,
            "acted_at": (
                self._format_datetime(
                    acted_at
                )
            ),
            "acted_at_seconds": (
                acted_at_seconds
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
