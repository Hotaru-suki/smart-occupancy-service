from fastapi import APIRouter, Depends

from app.schemas import StatusResponse, HealthResponse
from app.security.auth import AuthenticatedUser, require_authenticated_user
from app.services.monitoring_service import MonitoringService


def create_status_router(counter):
    router = APIRouter()
    monitoring_service = MonitoringService(counter)

    @router.get("/health", response_model=HealthResponse)
    def health():
        return monitoring_service.get_health()

    @router.get("/status", response_model=StatusResponse)
    def get_status(_: AuthenticatedUser = Depends(require_authenticated_user)):
        return monitoring_service.get_status()

    return router
