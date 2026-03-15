import json
import threading
from queue import Empty

from app.infrastructure.cache import redis_client
from app.infrastructure.queue.event_bus import event_queue
from app.infrastructure.repositories.event_repository import EventRepository
from app.infrastructure.logging.json_logger import logger


class EventWorker:
    def __init__(self):
        self._running = False
        self._thread = None
        self._event_repo = EventRepository()

    def _handle_event(self, message: dict) -> None:
        if message.get("type") != "occupancy_event":
            return

        region_id = message["region_id"]
        event_type = message["event"]
        people_count = message["people_count"]

        redis_client.lpush("occupancy:events", json.dumps(message, ensure_ascii=False))
        redis_client.ltrim("occupancy:events", 0, 99)

        self._event_repo.save_event(region_id, event_type, people_count)

        logger.info(
            f"事件异步处理完成: region_id={region_id}, {event_type}, people_count={people_count}",
            extra={"event": "event_worker_processed"}
        )

    def _run(self):
        self._running = True
        logger.info("事件消费者启动", extra={"event": "event_worker_start"})

        while self._running:
            try:
                message = event_queue.get(timeout=0.5)
            except Empty:
                continue

            try:
                self._handle_event(message)
            except Exception as e:
                logger.exception(
                    f"事件消费者处理失败: {e}",
                    extra={"event": "event_worker_failed"}
                )
            finally:
                event_queue.task_done()

        logger.info("事件消费者退出", extra={"event": "event_worker_stop"})

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)