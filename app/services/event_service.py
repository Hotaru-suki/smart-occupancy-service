from queue import Full

from app.core.event_types import OccupancyEventMessage
from app.infrastructure.logging.json_logger import logger
from app.infrastructure.queue.event_bus import event_queue


class EventService:
    def publish_occupancy_event(self, event_type: str, people_count: int) -> None:
        message = OccupancyEventMessage.build(event_type, people_count).to_dict()
        try:
            event_queue.put_nowait(message)
        except Full:
            logger.error(
                f"事件队列已满，丢弃事件: {event_type}, people_count={people_count}",
                extra={"event": "event_queue_full"}
            )
            return

        logger.info(
            f"事件已投递到队列: {event_type}, people_count={people_count}",
            extra={"event": "event_published"}
        )


event_service = EventService()