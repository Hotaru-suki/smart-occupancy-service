from __future__ import annotations

from tests.utils.env_loader import get_env


AUTH_USERNAME = get_env("AUTH_USERNAME", "admin")
AUTH_PASSWORD = get_env("AUTH_PASSWORD", "ChangeMe123!")
ADMIN_REGISTRATION_CODE = get_env("ADMIN_REGISTRATION_CODE", "OccupancyAdmin2026!")


def login_payload(
    username: str | None = None,
    password: str | None = None,
    role: str | None = None,
) -> dict:
    payload = {
        "username": username or AUTH_USERNAME,
        "password": password or AUTH_PASSWORD,
    }
    if role is not None:
        payload["role"] = role
    return payload


def register_payload(
    username: str,
    password: str,
    role: str = "viewer",
    admin_registration_code: str | None = None,
) -> dict:
    payload = {
        "username": username,
        "password": password,
        "role": role,
    }
    if admin_registration_code is not None:
        payload["admin_registration_code"] = admin_registration_code
    return payload
