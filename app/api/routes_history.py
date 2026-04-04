from fastapi import APIRouter, Depends, Query

from app.schemas import HistoryEventsResponse
from app.security.auth import AuthenticatedUser, require_admin_user
from app.services.history_service import history_service


def create_history_router():
    router = APIRouter()

    @router.get("/history/events", response_model=HistoryEventsResponse)
    def get_history_events(
        region_name: str | None = Query(default=None),
        event_type: str | None = Query(default=None),
        limit: int = Query(default=50, ge=1, le=200),
        _: AuthenticatedUser = Depends(require_admin_user),
    ):
        return history_service.get_history_events(
            region_name=region_name,
            event_type=event_type,
            limit=limit,
        )

    return router
