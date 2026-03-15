from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.infrastructure.db import Base, engine
from app.infrastructure.logging.json_logger import logger
from app.infrastructure.queue.event_worker import EventWorker
from app.infrastructure.repositories.region_repository import RegionRepository
from app.runtime.people_counter import PeopleCounter
from app.runtime.mock_counter import MockPeopleCounter
from app.api.routes_status import create_status_router
from app.api.routes_events import create_events_router
from app.api.routes_webrtc import create_webrtc_router
from app.api.routes_history import create_history_router

import app.infrastructure.models


def ensure_default_region():
    repo = RegionRepository()
    roi = (
        settings.roi_x1,
        settings.roi_y1,
        settings.roi_x2,
        settings.roi_y2
    )
    region = repo.get_by_name("default_region")
    if region is None:
        region = repo.create_region(
            region_name="default_region",
            camera_source=str(settings.video_source),
            roi=roi
        )
    return region


def build_counter(region_id: int):
    roi = (
        settings.roi_x1,
        settings.roi_y1,
        settings.roi_x2,
        settings.roi_y2
    )

    if settings.use_mock:
        return MockPeopleCounter(
            roi=roi,
            region_id=region_id,
            interval=settings.mock_interval,
            mock=True
        )

    return PeopleCounter(
        video_source=settings.video_source,
        model_path=settings.model_path,
        roi=roi,
        region_id=region_id,
        enter_frames=settings.enter_frames,
        leave_seconds=settings.leave_seconds,
        confidence=settings.confidence,
        reconnect_interval=settings.reconnect_interval,
        loop_interval=settings.loop_interval,
        mock=False
    )


Base.metadata.create_all(bind=engine)
default_region = ensure_default_region()

counter = build_counter(default_region.id)
pcs = set()
event_worker = EventWorker()


@asynccontextmanager
async def lifespan(app: FastAPI):
    event_worker.start()
    counter.start()

    logger.info(
        f"服务启动成功，mock={counter.mock}, region_id={default_region.id}",
        extra={"event": "app_start"}
    )
    yield

    counter.stop()
    event_worker.stop()

    coros = [pc.close() for pc in pcs]
    for coro in coros:
        await coro
    pcs.clear()

    logger.info(
        "服务已停止。",
        extra={"event": "app_stop"}
    )


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(create_status_router(counter), prefix="/api", tags=["status"])
app.include_router(create_events_router(counter), prefix="/api", tags=["events"])
app.include_router(create_webrtc_router(counter, pcs), prefix="/api", tags=["webrtc"])
app.include_router(create_history_router(), prefix="/api", tags=["history"])


@app.get("/")
def root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "mock": counter.mock,
        "supports_video": counter.supports_video()
    }