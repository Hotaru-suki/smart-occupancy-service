from __future__ import annotations

import json
import secrets
import time

from app.config import settings
from app.infrastructure.cache import redis_client


class SessionManager:
    def __init__(self):
        self.cookie_name = settings.auth_cookie_name
        self.session_ttl_sec = settings.auth_session_ttl_sec
        self.fail_window_sec = settings.auth_rate_limit_window_sec
        self.fail_max_attempts = settings.auth_rate_limit_max_attempts
        self.fail_lock_sec = settings.auth_rate_limit_lock_sec

    def _session_key(self, token: str) -> str:
        return f"auth:session:{token}"

    def _normalize_login_subject(self, username: str | None) -> str:
        candidate = (username or "anonymous").strip().lower()
        return candidate or "anonymous"

    def _fail_key(self, client_id: str, username: str | None) -> str:
        subject = self._normalize_login_subject(username)
        return f"auth:login_fail:{client_id}:{subject}"

    def _fail_lock_key(self, client_id: str, username: str | None) -> str:
        subject = self._normalize_login_subject(username)
        return f"auth:login_lock:{client_id}:{subject}"

    def create_session(self, username: str, role: str = "viewer") -> dict:
        token = secrets.token_urlsafe(32)
        now = int(time.time())
        session = {
            "token": token,
            "username": username,
            "role": role,
            "issued_at": now,
            "expires_at": now + self.session_ttl_sec,
        }
        redis_client.setex(
            self._session_key(token),
            self.session_ttl_sec,
            json.dumps(session, ensure_ascii=False),
        )
        return session

    def get_session(self, token: str | None) -> dict | None:
        if not token:
            return None

        raw = redis_client.get(self._session_key(token))
        if not raw:
            return None
        return json.loads(raw)

    def destroy_session(self, token: str | None) -> None:
        if token:
            redis_client.delete(self._session_key(token))

    def get_fail_state(self, client_id: str, username: str | None = None) -> tuple[int, int]:
        lock_key = self._fail_lock_key(client_id, username)
        lock_ttl = redis_client.ttl(lock_key)
        if lock_ttl and lock_ttl > 0:
            attempts = int(redis_client.get(self._fail_key(client_id, username)) or self.fail_max_attempts)
            return attempts, lock_ttl

        key = self._fail_key(client_id, username)
        attempts = int(redis_client.get(key) or 0)
        ttl = redis_client.ttl(key)
        return attempts, max(ttl, 0)

    def register_login_failure(self, client_id: str, username: str | None = None) -> tuple[int, int]:
        key = self._fail_key(client_id, username)
        attempts = int(redis_client.incr(key))
        if attempts == 1:
            redis_client.expire(key, self.fail_window_sec)
        if attempts >= self.fail_max_attempts:
            lock_key = self._fail_lock_key(client_id, username)
            redis_client.setex(lock_key, self.fail_lock_sec, "1")
            return attempts, self.fail_lock_sec
        ttl = redis_client.ttl(key)
        return attempts, max(ttl, 0)

    def clear_login_failures(self, client_id: str, username: str | None = None) -> None:
        redis_client.delete(self._fail_key(client_id, username))
        redis_client.delete(self._fail_lock_key(client_id, username))


session_manager = SessionManager()
