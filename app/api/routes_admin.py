from fastapi import APIRouter, Depends

from app.config import settings
from app.schemas import (
    BulkUserDeleteResponse,
    RegionConfigResponse,
    ROIUpdateRequest,
    UserDeleteResponse,
    UpdateUserRoleRequest,
    UserInfoResponse,
    UsersResponse,
)
from app.security.auth import AuthenticatedUser, require_admin_user
from app.services.admin_service import admin_service


def create_admin_router(counter, region_id: int):
    router = APIRouter()

    @router.get("/admin/users", response_model=UsersResponse)
    def list_users(_: AuthenticatedUser = Depends(require_admin_user)):
        return {"items": admin_service.list_users()}

    @router.patch("/admin/users/{username}/role", response_model=UserInfoResponse)
    def update_user_role(
        username: str,
        payload: UpdateUserRoleRequest,
        _: AuthenticatedUser = Depends(require_admin_user),
    ):
        return admin_service.update_user_role(username=username, role=payload.role)

    @router.get("/admin/regions/default", response_model=RegionConfigResponse)
    def get_default_region(_: AuthenticatedUser = Depends(require_admin_user)):
        return admin_service.get_region(region_id=region_id)

    @router.delete("/admin/users/{username}", response_model=UserDeleteResponse)
    def delete_user(
        username: str,
        user: AuthenticatedUser = Depends(require_admin_user),
    ):
        return admin_service.delete_user(
            username=username,
            actor_username=user.username,
            protected_username=settings.auth_username,
        )

    @router.delete("/admin/users", response_model=BulkUserDeleteResponse)
    def delete_test_users(user: AuthenticatedUser = Depends(require_admin_user)):
        return admin_service.delete_test_users(
            actor_username=user.username,
            protected_username=settings.auth_username,
        )

    @router.put("/admin/regions/default/roi", response_model=RegionConfigResponse)
    def update_default_region_roi(
        payload: ROIUpdateRequest,
        _: AuthenticatedUser = Depends(require_admin_user),
    ):
        roi = (payload.x1, payload.y1, payload.x2, payload.y2)
        region = admin_service.update_region_roi(region_id=region_id, roi=roi)
        counter.update_roi(roi)
        return region

    return router
