from sqlalchemy import (
    Column, Integer, String, Date, DateTime, Float, ForeignKey, Boolean,
    func, Index
)
from sqlalchemy.orm import relationship

from app.infrastructure.db import Base


class MonitorRegion(Base):
    __tablename__ = "monitor_regions"

    id = Column(Integer, primary_key=True, index=True)
    region_name = Column(String(100), nullable=False, unique=True)
    camera_source = Column(String(100), nullable=False, default="0")

    roi_x1 = Column(Integer, nullable=False)
    roi_y1 = Column(Integer, nullable=False)
    roi_x2 = Column(Integer, nullable=False)
    roi_y2 = Column(Integer, nullable=False)

    created_at = Column(DateTime, nullable=False, server_default=func.now())

    events = relationship("OccupancyEvent", back_populates="region")


class OccupancyEvent(Base):
    __tablename__ = "occupancy_events"

    id = Column(Integer, primary_key=True, index=True)
    region_id = Column(Integer, ForeignKey("monitor_regions.id"), nullable=False, index=True)

    event_type = Column(String(50), nullable=False, index=True)
    people_count = Column(Integer, nullable=False, default=0)
    event_time = Column(DateTime, nullable=False, server_default=func.now(), index=True)

    region = relationship("MonitorRegion", back_populates="events")

    __table_args__ = (
        Index("idx_event_region_time", "region_id", "event_time"),
        Index("idx_event_type_time", "event_type", "event_time"),
    )


class DailyStat(Base):
    __tablename__ = "daily_stats"

    id = Column(Integer, primary_key=True, index=True)
    stat_date = Column(Date, nullable=False, unique=True, index=True)
    max_people = Column(Integer, nullable=False, default=0)
    total_occupied_sec = Column(Float, nullable=False, default=0.0)
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class AppUser(Base):
    __tablename__ = "app_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(64), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False, default="viewer")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
