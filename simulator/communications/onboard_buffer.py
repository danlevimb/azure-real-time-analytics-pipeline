from collections import defaultdict, deque
from copy import deepcopy


class OnboardBuffer:
    """
    Producer-side buffer for events generated while a drone
    cannot transmit.

    Events stored here have already been created under the
    Event Contract. The buffer does not modify event_id,
    event_time, source_sequence_number, or payload.
    """

    def __init__(self) -> None:

        self._buffers: dict[
            str,
            deque[dict],
        ] = defaultdict(deque)

    def add(
        self,
        *,
        event: dict,
    ) -> None:

        drone_id = event.get(
            "drone_id"
        )

        if not drone_id:

            raise ValueError(
                "Buffered event must contain drone_id"
            )

        self._buffers[
            drone_id
        ].append(
            deepcopy(event)
        )

    def drain(
        self,
        *,
        drone_id: str,
    ) -> list[dict]:

        queue = self._buffers.get(
            drone_id
        )

        if not queue:

            return []

        events = list(
            queue
        )

        queue.clear()

        self._buffers.pop(
            drone_id,
            None,
        )

        return events

    def count_for(
        self,
        *,
        drone_id: str,
    ) -> int:

        return len(
            self._buffers.get(
                drone_id,
                (),
            )
        )

    @property
    def total_count(
        self,
    ) -> int:

        return sum(
            len(queue)
            for queue
            in self._buffers.values()
        )