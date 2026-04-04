from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, WebSocket, status

from app.config import settings
from app.infrastructure.logging.json_logger import logger
from app.services.auth_service import auth_service
from app.security.session_manager import session_manager


@dataclass
class AuthenticatedUser:
    username: str
    role: str
    issued_at: int
    expires_at: int


def get_client_id(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def get_cookie_settings() -> dict:
    return {
        "key": settings.auth_cookie_name,
        "httponly": True,
        "secure": settings.auth_cookie_secure,
        "samesite": settings.auth_cookie_samesite,
        "max_age": settings.auth_session_ttl_sec,
        "path": "/",
    }


def read_user_from_token(token: str | None) -> AuthenticatedUser | None:
    session = session_manager.get_session(token)
    if session is None:
        return None

    identity = auth_service.get_user_identity(session["username"])
    if identity is None:
        session_manager.destroy_session(token)
        return None

    return AuthenticatedUser(
        username=identity.username,
        role=identity.role,
        issued_at=session["issued_at"],
        expires_at=session["expires_at"],
    )


def get_optional_user(request: Request) -> AuthenticatedUser | None:
    token = request.cookies.get(settings.auth_cookie_name)
    return read_user_from_token(token)


def require_authenticated_user(
    user: AuthenticatedUser | None = Depends(get_optional_user),
) -> AuthenticatedUser:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
        )
    return user


def require_admin_user(
    user: AuthenticatedUser = Depends(require_authenticated_user),
) -> AuthenticatedUser:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required.",
        )
    return user


async def require_websocket_user(websocket: WebSocket) -> AuthenticatedUser | None:
    token = websocket.cookies.get(settings.auth_cookie_name)
    user = read_user_from_token(token)
    if user is None:
        await websocket.close(code=4401, reason="Authentication required.")
        return None
    return user


def ensure_allowed_origin(origin: str | None) -> None:
    if not origin:
        return

    if origin not in settings.cors_allow_origins:
        logger.warning(
            f"拒绝来自未授权 Origin 的认证/实时请求: {origin}",
            extra={"event": "auth_origin_rejected"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Origin is not allowed.",
        )
