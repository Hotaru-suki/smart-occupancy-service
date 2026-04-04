from fastapi import APIRouter, Depends, Query

from app.schemas import EventsResponse
from app.security.auth import AuthenticatedUser, require_admin_user
from app.services.monitoring_service import MonitoringService


def create_events_router(counter):
    router = APIRouter()
    monitoring_service = MonitoringService(counter)

    @router.get("/events", response_model=EventsResponse)
    def get_events(
        limit: int = Query(default=20, ge=1, le=100),
        _: AuthenticatedUser = Depends(require_admin_user),
    ):
        return monitoring_service.get_events(limit=limit)

    return router
