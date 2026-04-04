from __future__ import annotations

import json
from typing import Any

from app.infrastructure.cache import redis_client
from app.infrastructure.logging.json_logger import logger


class MonitoringService:
    def __init__(self, counter):
        self.counter = counter

    def get_health(self) -> dict[str, Any]:
        return self.counter.get_health()

    def get_status(self) -> dict[str, Any]:
        cached = self._read_json_cache(
            key="occupancy:status",
            cache_hit_event="api_status_cache_hit",
            cache_error_event="api_status_cache_read_failed",
            hit_message="status 接口命中 Redis 缓存",
            error_message="status 接口读取 Redis 失败",
        )
        if cached is not None:
            return cached

        logger.info(
            "status 接口回退到 counter.get_status()",
            extra={"event": "api_status_fallback_counter"},
        )
        return self.counter.get_status()

    def get_events(self, limit: int) -> dict[str, Any]:
        cached_items = self._read_json_list_cache(
            key="occupancy:events",
            limit=limit,
            cache_hit_event="api_events_cache_hit",
            cache_error_event="api_events_cache_read_failed",
            hit_message=f"events 接口命中 Redis 缓存: limit={limit}",
            error_message="events 接口读取 Redis 失败",
        )
        if cached_items is not None:
            return {"mock": self.counter.mock, "events": cached_items}

        logger.info(
            f"events 接口回退到 counter.get_events(): limit={limit}",
            extra={"event": "api_events_fallback_counter"},
        )
        return {"mock": self.counter.mock, "events": self.counter.get_events(limit=limit)}

    def _read_json_cache(
        self,
        key: str,
        cache_hit_event: str,
        cache_error_event: str,
        hit_message: str,
        error_message: str,
    ) -> dict[str, Any] | None:
        try:
            cached = redis_client.get(key)
            if cached:
                logger.info(hit_message, extra={"event": cache_hit_event})
                return json.loads(cached)
        except Exception as exc:
            logger.error(
                f"{error_message}: {exc}",
                extra={"event": cache_error_event},
            )
        return None

    def _read_json_list_cache(
        self,
        key: str,
        limit: int,
        cache_hit_event: str,
        cache_error_event: str,
        hit_message: str,
        error_message: str,
    ) -> list[dict[str, Any]] | None:
        try:
            cached_items = redis_client.lrange(key, 0, limit - 1)
            if cached_items:
                logger.info(hit_message, extra={"event": cache_hit_event})
                return [json.loads(item) for item in cached_items]
        except Exception as exc:
            logger.error(
                f"{error_message}: {exc}",
                extra={"event": cache_error_event},
            )
        return None
