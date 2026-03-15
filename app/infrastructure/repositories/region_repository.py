from app.infrastructure.db import SessionLocal
from app.infrastructure.models import MonitorRegion


class RegionRepository:
    def get_by_name(self, region_name: str):
        db = SessionLocal()
        try:
            return db.query(MonitorRegion).filter(MonitorRegion.region_name == region_name).first()
        finally:
            db.close()

    def create_region(self, region_name: str, camera_source: str, roi: tuple[int, int, int, int]):
        db = SessionLocal()
        try:
            region = MonitorRegion(
                region_name=region_name,
                camera_source=camera_source,
                roi_x1=roi[0],
                roi_y1=roi[1],
                roi_x2=roi[2],
                roi_y2=roi[3],
            )
            db.add(region)
            db.commit()
            db.refresh(region)
            return region
        finally:
            db.close()