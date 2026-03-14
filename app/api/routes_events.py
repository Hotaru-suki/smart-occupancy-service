from fastapi import APIRouter, Query

from app.schemas import EventsResponse
from app.infrastructure.cache import redis_client
from app.infrastructure.logging.json_logger import logger

import json


def create_events_router(counter):
    router = APIRouter()

    @router.get("/events", response_model=EventsResponse)
    def get_events(limit: int = Query(default=20, ge=1, le=100)):
        try:
            cached_events = redis_client.lrange("occupancy:events", 0, limit - 1)
            if cached_events:
                logger.info(
                    f"events 接口命中 Redis 缓存: limit={limit}",
                    extra={"event": "api_events_cache_hit"}
                )
                return {
                    "mock": counter.mock,
                    "events": [json.loads(item) for item in cached_events]
                }
        except Exception as e:
            logger.error(
                f"events 接口读取 Redis 失败: {e}",
                extra={"event": "api_events_cache_read_failed"}
            )

        logger.info(
            f"events 接口回退到 counter.get_events(): limit={limit}",
            extra={"event": "api_events_fallback_counter"}
        )
        return {
            "mock": counter.mock,
            "events": counter.get_events(limit=limit)
        }

    return router