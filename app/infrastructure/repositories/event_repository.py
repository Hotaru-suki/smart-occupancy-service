from app.infrastructure.db import SessionLocal
from app.infrastructure.models import OccupancyEvent


class EventRepository:
    def save_event(self, event_type: str, people_count: int) -> None:
        db = SessionLocal()
        try:
            db_event = OccupancyEvent(
                event_type=event_type,
                people_count=people_count
            )
            db.add(db_event)
            db.commit()
        finally:
            db.close()