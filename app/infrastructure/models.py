from sqlalchemy import Column, Integer, String, Date, DateTime, Float, func

from app.infrastructure.db import Base


class OccupancyEvent(Base):
    __tablename__ = "occupancy_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False)
    people_count = Column(Integer, nullable=False, default=0)
    event_time = Column(DateTime, nullable=False, server_default=func.now())


class DailyStat(Base):
    __tablename__ = "daily_stats"

    id = Column(Integer, primary_key=True, index=True)
    stat_date = Column(Date, nullable=False, unique=True)
    max_people = Column(Integer, nullable=False, default=0)
    total_occupied_sec = Column(Float, nullable=False, default=0.0)
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())