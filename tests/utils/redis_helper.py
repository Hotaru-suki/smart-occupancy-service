from __future__ import annotations

import json
from typing import Any, cast

import redis

from tests.utils.env_loader import get_env


class RedisHelper:
    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        db: int | None = None,
        password: str | None = None,
    ) -> None:
        redis_host = host if host is not None else get_env("REDIS_HOST", "127.0.0.1")
        redis_port = port if port is not None else int(get_env("REDIS_PORT", "6379"))
        redis_db = db if db is not None else int(get_env("REDIS_DB", "1"))
        redis_password = (
            password if password is not None else get_env("REDIS_PASSWORD", "")
        )
        self.client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password,
            decode_responses=True,
        )

    def get_json(self, key: str) -> dict[str, Any] | list[Any] | None:
        raw = cast(str | bytes | bytearray | None, self.client.get(key))
        if not raw:
            return None
        return json.loads(raw)

    def set_json(self, key: str, value: dict[str, Any]) -> None:
        self.client.set(key, json.dumps(value, ensure_ascii=False))

    def lrange_json(self, key: str, start: int = 0, end: int = -1) -> list[Any]:
        items = cast(list[str | bytes | bytearray], self.client.lrange(key, start, end))
        return [json.loads(item) for item in items]

    def lpush_json(self, key: str, value: dict[str, Any]) -> None:
        self.client.lpush(key, json.dumps(value, ensure_ascii=False))

    def delete_key(self, key: str) -> None:
        self.client.delete(key)

    def exists(self, key: str) -> bool:
        return bool(self.client.exists(key))
