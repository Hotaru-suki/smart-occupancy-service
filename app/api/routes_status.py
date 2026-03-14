from fastapi import APIRouter

from app.schemas import StatusResponse, HealthResponse
from app.infrastructure.cache import redis_client
from app.infrastructure.logging.json_logger import logger

import json


def create_status_router(counter):
    router = APIRouter()

    @router.get("/health", response_model=HealthResponse)
    def health():
        return counter.get_health()

    @router.get("/status", response_model=StatusResponse)
    def get_status():
        try:
            cached = redis_client.get("occupancy:status")
            if cached:
                logger.info(
                    "status 接口命中 Redis 缓存",
                    extra={"event": "api_status_cache_hit"}
                )
                return json.loads(cached)
        except Exception as e:
            logger.error(
                f"status 接口读取 Redis 失败: {e}",
                extra={"event": "api_status_cache_read_failed"}
            )

        logger.info(
            "status 接口回退到 counter.get_status()",
            extra={"event": "api_status_fallback_counter"}
        )
        return counter.get_status()

    return router