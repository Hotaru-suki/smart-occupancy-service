import asyncio
import json

from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect

from app.config import settings
from app.infrastructure.logging.json_logger import logger
from app.security.auth import ensure_allowed_origin, require_websocket_user


def create_realtime_router(counter):
    router = APIRouter()

    @router.websocket("/realtime")
    async def realtime_stream(websocket: WebSocket):
        ensure_allowed_origin(websocket.headers.get("origin"))
        user = await require_websocket_user(websocket)
        if user is None:
            return
        await websocket.accept()

        logger.info(
            f"实时连接已建立: username={user.username}",
            extra={"event": "realtime_connected"},
        )

        last_status = None
        last_events = None

        try:
            while True:
                status_payload = counter.get_status()
                status_json = json.dumps(status_payload, ensure_ascii=False, sort_keys=True)

                if status_json != last_status:
                    await websocket.send_json({"type": "status", "data": status_payload})
                    last_status = status_json

                if user.role == "admin":
                    events_payload = {
                        "mock": counter.mock,
                        "events": counter.get_events(limit=10),
                    }
                    events_json = json.dumps(events_payload, ensure_ascii=False, sort_keys=True)
                    if events_json != last_events:
                        await websocket.send_json({"type": "events", "data": events_payload})
                        last_events = events_json

                await asyncio.sleep(settings.realtime_push_interval)
        except WebSocketDisconnect:
            logger.info(
                f"实时连接已断开: username={user.username}",
                extra={"event": "realtime_disconnected"},
            )
        except Exception as exc:
            logger.exception(
                f"实时连接异常: username={user.username}, error={exc}",
                extra={"event": "realtime_error"},
            )
            try:
                await websocket.close(code=1011, reason="Realtime stream error.")
            except RuntimeError:
                pass

    return router
