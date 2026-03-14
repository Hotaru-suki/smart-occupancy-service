from datetime import datetime

from app.infrastructure.db import SessionLocal
from app.infrastructure.models import DailyStat


class StatRepository:
    def upsert_today(self, max_people: int, total_occupied_sec: float) -> None:
        db = SessionLocal()
        try:
            today = datetime.now().date()
            stat = db.query(DailyStat).filter(DailyStat.stat_date == today).first()

            if stat is None:
                stat = DailyStat(
                    stat_date=today,
                    max_people=max_people,
                    total_occupied_sec=total_occupied_sec
                )
                db.add(stat)
            else:
                stat.max_people = max_people
                stat.total_occupied_sec = total_occupied_sec

            db.commit()
        finally:
            db.close()