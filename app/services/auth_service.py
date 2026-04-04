from __future__ import annotations

import re
from dataclasses import dataclass

from fastapi import HTTPException, status

from app.config import settings
from app.infrastructure.repositories.user_repository import UserRepository
from app.security.passwords import hash_password, verify_password


USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{2,31}$")


@dataclass
class UserIdentity:
    username: str
    role: str
    is_active: bool


@dataclass
class RegistrationResult:
    username: str
    role: str
    created: bool


class AuthService:
    def __init__(self, user_repository: UserRepository | None = None):
        self.user_repository = user_repository or UserRepository()

    def normalize_username(self, username: str) -> str:
        return username.strip().lower()

    def validate_username(self, username: str) -> str:
        normalized = self.normalize_username(username)
        if not USERNAME_PATTERN.fullmatch(normalized):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Username must be 3-32 chars and use letters, numbers, ., _, - only.",
            )
        return normalized

    def validate_password(self, password: str) -> str:
        if len(password) < 8 or len(password) > 128:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Password length must be between 8 and 128 characters.",
            )
        return password

    def bootstrap_admin(self) -> None:
        self.ensure_runtime_security()
        username = self.validate_username(settings.auth_username)
        password_hash = self._resolve_password_hash(settings.auth_password, settings.auth_password_hash)
        self.user_repository.ensure_user(username=username, password_hash=password_hash, role="admin")

    def register_user(
        self,
        username: str,
        password: str,
        role: str = "viewer",
        admin_registration_code: str | None = None,
    ) -> RegistrationResult:
        normalized = self.validate_username(username)
        secret = self.validate_password(password)
        target_role = self._validate_role(role)

        if target_role == "admin" and admin_registration_code != settings.admin_registration_code:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin registration code is invalid.",
            )

        existing = self.user_repository.get_by_username(normalized)

        if existing is None:
            created = self.user_repository.create_user(
                username=normalized,
                password_hash=hash_password(secret),
                role=target_role,
            )
            return RegistrationResult(username=created.username, role=created.role, created=True)

        if verify_password(secret, existing.password_hash) and existing.role == target_role:
            return RegistrationResult(username=existing.username, role=existing.role, created=False)

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists with different credentials.",
        )

    def change_password(
        self,
        username: str,
        current_password: str,
        new_password: str,
    ) -> UserIdentity:
        normalized = self.validate_username(username)
        existing = self.user_repository.get_by_username(normalized)
        if existing is None or not existing.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if not verify_password(current_password, existing.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect.",
            )

        secret = self.validate_password(new_password)
        if verify_password(secret, existing.password_hash):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="New password must be different from the current password.",
            )

        updated = self.user_repository.update_password(
            username=normalized,
            password_hash=hash_password(secret),
        )
        return UserIdentity(
            username=updated.username,
            role=updated.role,
            is_active=bool(updated.is_active),
        )

    def authenticate_user(
        self,
        username: str,
        password: str,
        expected_role: str | None = None,
    ) -> UserIdentity | None:
        normalized = self.validate_username(username)
        existing = self.user_repository.get_by_username(normalized)
        if existing is None or not existing.is_active:
            return None

        if not verify_password(password, existing.password_hash):
            return None

        if expected_role is not None and existing.role != self._validate_role(expected_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Selected role does not match the account role.",
            )

        return UserIdentity(
            username=existing.username,
            role=existing.role,
            is_active=bool(existing.is_active),
        )

    def get_user_identity(self, username: str) -> UserIdentity | None:
        normalized = self.normalize_username(username)
        existing = self.user_repository.get_by_username(normalized)
        if existing is None or not existing.is_active:
            return None
        return UserIdentity(
            username=existing.username,
            role=existing.role,
            is_active=bool(existing.is_active),
        )

    def _resolve_password_hash(self, raw_password: str, configured_hash: str | None) -> str:
        if configured_hash:
            return configured_hash
        self.validate_password(raw_password)
        return hash_password(raw_password)

    def ensure_runtime_security(self) -> None:
        if not settings.auth_password_hash and settings.auth_password == settings.insecure_placeholder:
            raise RuntimeError("AUTH_PASSWORD or AUTH_PASSWORD_HASH must be explicitly configured.")
        if settings.admin_registration_code == settings.insecure_placeholder:
            raise RuntimeError("ADMIN_REGISTRATION_CODE must be explicitly configured.")

    def _validate_role(self, role: str) -> str:
        if role not in {"admin", "viewer"}:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Role must be admin or viewer.",
            )
        return role


auth_service = AuthService()
