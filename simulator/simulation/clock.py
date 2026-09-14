from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class SimulationClock:
    start_time: datetime
    tick_seconds: float
    elapsed_seconds: float = 0.0

    @property
    def now(self) -> datetime:
        return self.start_time + timedelta(
            seconds=self.elapsed_seconds
        )

    def advance(self) -> None:
        self.elapsed_seconds += self.tick_seconds