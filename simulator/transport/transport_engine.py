import heapq

from copy import deepcopy
from dataclasses import (dataclass, field,)
from itertools import count

@dataclass(order=True)
class ScheduledEvent:

    release_at_seconds: float
    insertion_order: int

    event: dict = field(
        compare=False
    )


@dataclass
class TransportSubmission:

    dropped: bool = False
    buffered: bool = False

    duplicate_copies: int = 0

    scheduled_release_at_seconds: (
        float | None
    ) = None

    extra_delay_ms: int = 0


class TransportEngine:

    def __init__(
        self,
        *,
        base_delay_ms: int = 0,        
        duplicate_targets: set[tuple[str, int]] | None = None,
        drop_targets: set[tuple[str, int]] | None = None,
        extra_delay_ms_by_target: dict[tuple[str, int], int,] | None = None,
        buffering_enabled: bool = False,
        buffer_start_seconds: float = 0.0,
        buffer_end_seconds: float = 0.0,
        buffer_target_drone_ids: (set[str] | None) = None,
        duplicate_sequences: set[int] | None = None,
        drop_sequences: set[int] | None = None,
        extra_delay_ms_by_sequence: dict[int, int,] | None = None,                        
    ) -> None:

        if base_delay_ms < 0:
            raise ValueError(
                "base_delay_ms cannot "
                "be negative"
            )

        if buffering_enabled:

            if buffer_start_seconds < 0:
                raise ValueError(
                    "buffer_start_seconds "
                    "cannot be negative"
                )

            if (
                buffer_end_seconds
                <= buffer_start_seconds
            ):
                raise ValueError(
                    "buffer_end_seconds must "
                    "be greater than "
                    "buffer_start_seconds"
                )

        self.base_delay_seconds = base_delay_ms / 1000.0
        self.buffering_enabled = buffering_enabled
        self.buffer_start_seconds = buffer_start_seconds
        self.buffer_end_seconds = buffer_end_seconds        
        
        self.buffer_target_drone_ids = (
            None

            if buffer_target_drone_ids
            is None

            else set(
                buffer_target_drone_ids
            )
        )
        
        self.duplicate_sequences = set(duplicate_sequences or set())

        self.drop_sequences = set(drop_sequences or set())

        overlap = (
            self.duplicate_sequences
            & self.drop_sequences
        )

        if overlap:
            raise ValueError(
                "A sequence cannot be both "
                "duplicated and dropped: "
                f"{sorted(overlap)}"
            )

        self.extra_delay_ms_by_sequence = (
            dict(
                extra_delay_ms_by_sequence
                or {}
            )
        )
        
        self.duplicate_targets = set(duplicate_targets or set())
        self.drop_targets = set(drop_targets or set())
        self.extra_delay_ms_by_target = dict(extra_delay_ms_by_target or {})
        
        target_overlap = (
            self.duplicate_targets
            & self.drop_targets
        )

        if target_overlap:

            raise ValueError(
                "A producer target cannot be "
                "both duplicated and dropped: "
                f"{sorted(target_overlap)}"
            )

        for (
            target,
            delay_ms,
        ) in (
            self
            .extra_delay_ms_by_target
            .items()
        ):

            if delay_ms < 0:

                raise ValueError(
                    "Extra delay cannot be "
                    "negative for target "
                    f"{target}"
                )

        for (
            target,
            delay_ms,
        ) in (
            self
            .extra_delay_ms_by_target
            .items()
        ):

            if delay_ms < 0:
                raise ValueError(
                    "Extra delay cannot "
                    "be negative for target "
                    f"{target}"
                )

        self._queue: list[
            ScheduledEvent
        ] = []

        self._buffer: list[
            dict
        ] = []

        self._order_counter = count()

        self._buffer_released = False

    # =====================================================
    # Properties
    # =====================================================

    @property
    def buffered_count(self) -> int:

        return len(
            self._buffer
        )

    @property
    def queued_count(self) -> int:

        return len(
            self._queue
        )

    @property
    def pending_count(self) -> int:

        return (
            self.buffered_count
            + self.queued_count
        )

    # =====================================================
    # Internal helpers
    # =====================================================

    def _is_buffer_window(
        self,
        current_seconds: float,
    ) -> bool:

        return (
            self.buffering_enabled
            and
            self.buffer_start_seconds
            <= current_seconds
            < self.buffer_end_seconds
        )

    def _schedule(
        self,
        *,
        event: dict,
        release_at_seconds: float,
    ) -> None:

        scheduled = ScheduledEvent(
            release_at_seconds=(
                release_at_seconds
            ),
            insertion_order=next(
                self._order_counter
            ),
            event=event,
        )

        heapq.heappush(
            self._queue,
            scheduled,
        )
    
    def _event_target(
        self,
        event: dict,
    ) -> tuple[str, int] | None:

        drone_id = event.get(
            "drone_id"
        )

        if drone_id is None:

            return None

        return (
            drone_id,
            int(
                event[
                    "source_sequence_number"
                ]
            ),
        )

    def _should_duplicate(
        self,
        event: dict,
    ) -> bool:

        sequence_number = int(
            event[
                "source_sequence_number"
            ]
        )

        target = self._event_target(
            event
        )

        return (
            sequence_number
            in self.duplicate_sequences
            or
            target
            in self.duplicate_targets
        )


    def _should_drop(
        self,
        event: dict,
    ) -> bool:

        sequence_number = int(
            event[
                "source_sequence_number"
            ]
        )

        target = self._event_target(
            event
        )

        return (
            sequence_number
            in self.drop_sequences
            or
            target
            in self.drop_targets
        )

    def _extra_delay_ms(
        self,
        event: dict,
    ) -> int:

        sequence_number = int(
            event[
                "source_sequence_number"
            ]
        )

        target = self._event_target(
            event
        )

        # Producer-specific rule wins.
        if (
            target
            in self.extra_delay_ms_by_target
        ):

            return (
                self
                .extra_delay_ms_by_target[
                    target
                ]
            )

        return (
            self
            .extra_delay_ms_by_sequence
            .get(
                sequence_number,
                0,
            )
        )        

    # =====================================================
    # Submit logical event into transport
    # =====================================================

    def submit(
        self,
        *,
        event: dict,
        current_seconds: float,
    ) -> TransportSubmission:

        sequence_number = int(
            event[
                "source_sequence_number"
            ]
        )

        # -------------------------------------------------
        # DROP
        # -------------------------------------------------

        if self._should_drop(event):

            return TransportSubmission(
                dropped=True,
            )

        # -------------------------------------------------
        # DUPLICATE
        # -------------------------------------------------

        copies = [event]

        duplicate_copies = 0

        if self._should_duplicate(event):

            # Same logical event:
            # same event_id,
            # same sequence,
            # same event_time,
            # same payload.
            copies.append(
                deepcopy(event)
            )

            duplicate_copies = 1

        # -------------------------------------------------
        # EXTRA DELAY
        # -------------------------------------------------

        extra_delay_ms = self._extra_delay_ms(event)
        extra_delay_seconds = extra_delay_ms / 1000.0

        # -------------------------------------------------
        # BUFFER
        # -------------------------------------------------

        if self._should_buffer(
            event=event,
            current_seconds=current_seconds,
        ):

            self._buffer.extend(
                copies
            )

            return TransportSubmission(
                buffered=True,
                duplicate_copies=(
                    duplicate_copies
                ),
                extra_delay_ms=(
                    extra_delay_ms
                ),
            )

        # -------------------------------------------------
        # NORMAL SCHEDULING
        # -------------------------------------------------

        release_at_seconds = (
            current_seconds
            + self.base_delay_seconds
            + extra_delay_seconds
        )

        for event_copy in copies:

            self._schedule(
                event=event_copy,
                release_at_seconds=(
                    release_at_seconds
                ),
            )

        return TransportSubmission(
            dropped=False,
            buffered=False,
            duplicate_copies=(
                duplicate_copies
            ),
            scheduled_release_at_seconds=(
                release_at_seconds
            ),
            extra_delay_ms=(
                extra_delay_ms
            ),
        )

    # =====================================================
    # Buffer recovery
    # =====================================================

    def _release_buffer_if_due(
        self,
        current_seconds: float,
    ) -> int:

        if (
            not self.buffering_enabled
            or self._buffer_released
            or current_seconds
            < self.buffer_end_seconds
        ):

            return 0

        release_count = len(
            self._buffer
        )

        for event in self._buffer:

            self._schedule(
                event=event,
                release_at_seconds=(
                    current_seconds
                ),
            )

        self._buffer.clear()

        self._buffer_released = True

        return release_count

    # =====================================================
    # Deliver ready events
    # =====================================================

    def release_ready(
        self,
        *,
        current_seconds: float,
    ) -> tuple[
        list[dict],
        int,
    ]:

        buffer_release_count = (
            self._release_buffer_if_due(
                current_seconds
            )
        )

        released: list[
            dict
        ] = []

        epsilon = 1e-9

        while self._queue:

            next_event = (
                self._queue[0]
            )

            if (
                next_event.release_at_seconds
                >
                current_seconds
                + epsilon
            ):
                break

            scheduled = heapq.heappop(
                self._queue
            )

            released.append(
                scheduled.event
            )

        return (
            released,
            buffer_release_count,
        )

    # =====================================================
    # End-of-run drain
    # =====================================================

    def flush_all(
        self,
        *,
        current_seconds: float,
    ) -> list[dict]:

        for event in self._buffer:

            self._schedule(
                event=event,
                release_at_seconds=(
                    current_seconds
                ),
            )

        self._buffer.clear()

        remaining = []

        while self._queue:

            scheduled = heapq.heappop(
                self._queue
            )

            remaining.append(
                scheduled.event
            )

        return remaining
    
    def _should_buffer(
        self,
        *,
        event: dict,
        current_seconds: float,
    ) -> bool:

        if not self._is_buffer_window(
            current_seconds
        ):

            return False

        # Legacy behavior:
        # no producer targeting means
        # buffer every producer.
        if (
            self.buffer_target_drone_ids
            is None
        ):

            return True

        drone_id = event.get(
            "drone_id"
        )

        return (
            drone_id
            in self.buffer_target_drone_ids
        )