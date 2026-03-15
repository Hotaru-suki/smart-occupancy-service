from fastapi import APIRouter, Query

from app.schemas import HistoryEventsResponse
from app.infrastructure.repositories.event_repository import EventRepository
from app.infrastructure.logging.json_logger import logger


def create_history_router():
    router = APIRouter()
    event_repo = EventRepository()

    @router.get("/history/events", response_model=HistoryEventsResponse)
    def get_history_events(
        region_name: str | None = Query(default=None),
        event_type: str | None = Query(default=None),
        limit: int = Query(default=50, ge=1, le=200),
    ):
        logger.info(
            f"历史事件查询: region_name={region_name}, event_type={event_type}, limit={limit}",
            extra={"event": "api_history_events_query"}
        )

        items = event_repo.get_history_events(
            region_name=region_name,
            event_type=event_type,
            limit=limit
        )
        return {"items": items}

    return router