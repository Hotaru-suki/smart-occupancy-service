from __future__ import annotations

from fastapi import HTTPException, status

from app.infrastructure.repositories.region_repository import RegionRepository
from app.infrastructure.repositories.user_repository import UserRepository


class AdminService:
    def __init__(
        self,
        user_repository: UserRepository | None = None,
        region_repository: RegionRepository | None = None,
    ):
        self.user_repository = user_repository or UserRepository()
        self.region_repository = region_repository or RegionRepository()

    def _serialize_user(self, user):
        return {
            "username": user.username,
            "role": user.role,
            "is_active": bool(user.is_active),
        }

    def _serialize_region(self, region):
        return {
            "region_id": region.id,
            "region_name": region.region_name,
            "camera_source": region.camera_source,
            "roi": {
                "x1": region.roi_x1,
                "y1": region.roi_y1,
                "x2": region.roi_x2,
                "y2": region.roi_y2,
            },
        }

    def list_users(self):
        users = self.user_repository.list_users()
        return [self._serialize_user(user) for user in users]

    def update_user_role(self, username: str, role: str):
        user = self.user_repository.update_role(username=username.strip().lower(), role=role)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return self._serialize_user(user)

    def delete_user(self, username: str, actor_username: str, protected_username: str):
        normalized = username.strip().lower()
        actor = actor_username.strip().lower()
        protected = protected_username.strip().lower()

        if normalized == actor:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You cannot delete the current account.",
            )

        if normalized == protected:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The bootstrap admin account cannot be deleted.",
            )

        deleted = self.user_repository.delete_by_username(normalized)
        if deleted == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )
        return {"success": True, "username": normalized}

    def delete_test_users(self, actor_username: str, protected_username: str, prefix: str = "tester_"):
        excluded = [actor_username.strip().lower(), protected_username.strip().lower()]
        deleted_usernames = self.user_repository.delete_by_prefix_excluding(prefix=prefix, excluded_usernames=excluded)
        return {
            "success": True,
            "deleted_count": len(deleted_usernames),
            "usernames": deleted_usernames,
        }

    def get_region(self, region_id: int):
        region = self.region_repository.get_by_id(region_id)
        if region is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Region not found.",
            )
        return self._serialize_region(region)

    def update_region_roi(self, region_id: int, roi: tuple[int, int, int, int]):
        x1, y1, x2, y2 = roi
        if x1 >= x2 or y1 >= y2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="ROI coordinates are invalid.",
            )

        region = self.region_repository.update_roi(region_id=region_id, roi=roi)
        if region is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Region not found.",
            )
        return self._serialize_region(region)


admin_service = AdminService()
