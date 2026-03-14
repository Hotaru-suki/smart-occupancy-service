from dataclasses import dataclass
from datetime import datetime
from typing import Literal


EventKind = Literal["enter_region", "leave_region"]


@dataclass
class OccupancyEventMessage:
    event: EventKind
    people_count: int
    timestamp: str

    @classmethod
    def build(cls, event: EventKind, people_count: int) -> "OccupancyEventMessage":
        return cls(
            event=event,
            people_count=people_count,
            timestamp=datetime.now().isoformat(timespec="seconds")
        )

    def to_dict(self) -> dict:
        return {
            "type": "occupancy_event",
            "event": self.event,
            "people_count": self.people_count,
            "timestamp": self.timestamp
        }