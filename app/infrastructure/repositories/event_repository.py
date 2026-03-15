from app.infrastructure.db import SessionLocal
from app.infrastructure.models import OccupancyEvent, MonitorRegion


class EventRepository:
    def save_event(self, region_id: int, event_type: str, people_count: int) -> None:
        db = SessionLocal()
        try:
            db_event = OccupancyEvent(
                region_id=region_id,
                event_type=event_type,
                people_count=people_count
            )
            db.add(db_event)
            db.commit()
        finally:
            db.close()

    def get_history_events(self, region_name=None, event_type=None, limit=50):
        db = SessionLocal()
        try:
            query = db.query(
                OccupancyEvent.id,
                OccupancyEvent.event_type,
                OccupancyEvent.people_count,
                OccupancyEvent.event_time,
                MonitorRegion.region_name
            ).join(
                MonitorRegion, OccupancyEvent.region_id == MonitorRegion.id
            )

            if region_name:
                query = query.filter(MonitorRegion.region_name == region_name)

            if event_type:
                query = query.filter(OccupancyEvent.event_type == event_type)

            rows = query.order_by(OccupancyEvent.event_time.desc()).limit(limit).all()

            return [
                {
                    "id": row.id,
                    "region_name": row.region_name,
                    "event_type": row.event_type,
                    "people_count": row.people_count,
                    "event_time": row.event_time.isoformat(sep=" ", timespec="seconds"),
                }
                for row in rows
            ]
        finally:
            db.close()