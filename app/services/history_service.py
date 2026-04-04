from __future__ import annotations

from app.infrastructure.logging.json_logger import logger
from app.infrastructure.repositories.event_repository import EventRepository


class HistoryService:
    def __init__(self, event_repository: EventRepository | None = None):
        self.event_repository = event_repository or EventRepository()

    def get_history_events(
        self,
        region_name: str | None = None,
        event_type: str | None = None,
        limit: int = 50,
    ) -> dict:
        logger.info(
            f"历史事件查询: region_name={region_name}, event_type={event_type}, limit={limit}",
            extra={"event": "api_history_events_query"},
        )
        items = self.event_repository.get_history_events(
            region_name=region_name,
            event_type=event_type,
            limit=limit,
        )
        return {"items": items}


history_service = HistoryService()
