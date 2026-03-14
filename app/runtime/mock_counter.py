import threading
import json
import time
from datetime import datetime, date

from app.state import BaseCounter
from app.infrastructure.cache import redis_client
from app.infrastructure.logging.json_logger import logger
from app.infrastructure.repositories.stat_repository import StatRepository
from app.services.event_service import event_service


class MockPeopleCounter(BaseCounter):
    def __init__(self, roi=None, interval=1.0, mock=True):
        self.roi = roi if roi is not None else (100, 100, 500, 400)
        self.interval = interval
        self.mock = mock

        self.lock = threading.RLock()
        self.running = False
        self.worker_thread = None

        self.current_people = 0
        self.occupied = False
        self.status = "idle"

        self.last_seen_time = None
        self.last_empty_time = None
        self.occupied_since = None

        self.today_total_occupied_sec = 0.0
        self.max_people_today = 0

        self.camera_ok = True
        self.detector_ok = True
        self.last_frame_time = None
        self.last_error = None

        self.events = []
        self.current_day = str(date.today())
        self._status_snapshot = {}

        self.timeline = [
            (5, 0),
            (10, 1),
            (8, 2),
            (6, 0),
            (12, 3),
            (5, 0),
        ]

        self.stat_repository = StatRepository()

        self._refresh_status_snapshot()

        logger.info(
            f"MockPeopleCounter 初始化完成: roi={self.roi}, interval={self.interval}",
            extra={"event": "mock_counter_init"}
        )

    def _now(self):
        return datetime.now()

    def _now_str(self):
        return self._now().isoformat(timespec="seconds")

    def supports_video(self) -> bool:
        return False

    def _append_event(self, event_type, people_count):
        event = {
            "timestamp": self._now_str(),
            "event": event_type,
            "people_count": people_count
        }

        self.events.append(event)
        self.events = self.events[-100:]

        event_service.publish_occupancy_event(event_type, people_count)

    def _sync_daily_stat_to_mysql(self):
        try:
            self.stat_repository.upsert_today(
                max_people=self.max_people_today,
                total_occupied_sec=self.today_total_occupied_sec
            )
        except Exception as e:
            self.last_error = f"MySQL每日统计同步失败: {e}"
            logger.exception(
                self.last_error,
                extra={"event": "mock_mysql_daily_stat_sync_failed"}
            )

    def _refresh_status_snapshot(self):
        occupied_duration_sec = 0.0
        if self.occupied and self.occupied_since is not None:
            occupied_duration_sec = time.time() - self.occupied_since

        self._status_snapshot = {
            "mock": self.mock,
            "supports_video": self.supports_video(),
            "occupied": self.occupied,
            "status": self.status,
            "current_people": self.current_people,
            "occupied_duration_sec": round(occupied_duration_sec, 2),
            "today_total_occupied_sec": round(self.today_total_occupied_sec, 2),
            "last_seen_time": self.last_seen_time,
            "last_empty_time": self.last_empty_time,
            "max_people_today": self.max_people_today,
            "roi": {
                "x1": self.roi[0],
                "y1": self.roi[1],
                "x2": self.roi[2],
                "y2": self.roi[3]
            },
            "camera_ok": self.camera_ok,
            "detector_ok": self.detector_ok,
            "running": self.running,
            "last_frame_time": self.last_frame_time,
            "last_error": self.last_error,
            "timestamp": self._now_str()
        }

        try:
            redis_client.set("occupancy:status", json.dumps(self._status_snapshot, ensure_ascii=False))
        except Exception as e:
            self.last_error = f"Redis状态缓存失败: {e}"
            logger.error(
                self.last_error,
                extra={"event": "mock_redis_status_cache_failed"}
            )

    def _reset_daily_if_needed(self):
        today = str(date.today())
        if self.current_day != today:
            self.current_day = today
            self.today_total_occupied_sec = 0.0
            self.max_people_today = 0
            self.events = []

            logger.info(
                f"Mock检测到日期切换，重置当日统计: current_day={self.current_day}",
                extra={"event": "mock_daily_stat_reset"}
            )

    def _set_people(self, people):
        now_ts = time.time()
        now_str = self._now_str()

        old_occupied = self.occupied

        self.current_people = people
        self.occupied = people > 0
        self.status = "occupied" if people > 0 else "idle"
        self.last_frame_time = now_str
        self.max_people_today = max(self.max_people_today, people)

        if self.occupied:
            self.last_seen_time = now_str
            if not old_occupied:
                self.occupied_since = now_ts
                self._append_event("enter_region", people)

                logger.info(
                    f"Mock区域进入事件触发: people_count={people}",
                    extra={"event": "mock_enter_region"}
                )
        else:
            if old_occupied:
                if self.occupied_since is not None:
                    self.today_total_occupied_sec += max(0.0, now_ts - self.occupied_since)
                self.occupied_since = None
                self.last_empty_time = now_str
                self._append_event("leave_region", 0)

                logger.info(
                    "Mock区域离开事件触发",
                    extra={"event": "mock_leave_region"}
                )

    def _run_mock(self):
        self.running = True

        logger.info(
            "Mock线程启动",
            extra={"event": "mock_thread_start"}
        )

        while self.running:
            for duration, people in self.timeline:
                if not self.running:
                    break

                start = time.time()
                while self.running and (time.time() - start < duration):
                    with self.lock:
                        self._reset_daily_if_needed()
                        self._set_people(people)
                        self._sync_daily_stat_to_mysql()
                        self._refresh_status_snapshot()
                    time.sleep(self.interval)

        logger.info(
            "Mock线程退出",
            extra={"event": "mock_thread_stop"}
        )

    def start(self):
        with self.lock:
            if self.running:
                return
            if self.worker_thread is not None and self.worker_thread.is_alive():
                return

            self.worker_thread = threading.Thread(target=self._run_mock, daemon=True)
            self.worker_thread.start()

        logger.info(
            "MockPeopleCounter 启动",
            extra={"event": "mock_counter_start"}
        )

    def stop(self):
        with self.lock:
            self.running = False

        if self.worker_thread is not None:
            self.worker_thread.join(timeout=2.0)

        with self.lock:
            self._refresh_status_snapshot()

        logger.info(
            "MockPeopleCounter 停止",
            extra={"event": "mock_counter_stop"}
        )

    def get_status(self):
        with self.lock:
            snapshot = dict(self._status_snapshot)

            if self.occupied and self.occupied_since is not None:
                snapshot["occupied_duration_sec"] = round(time.time() - self.occupied_since, 2)
            else:
                snapshot["occupied_duration_sec"] = 0.0

            snapshot["timestamp"] = self._now_str()
            return snapshot

    def get_events(self, limit=20):
        with self.lock:
            return list(self.events[-limit:])

    def get_health(self):
        with self.lock:
            return {
                "mock": self.mock,
                "supports_video": self.supports_video(),
                "running": self.running,
                "camera_ok": self.camera_ok,
                "detector_ok": self.detector_ok,
                "last_frame_time": self.last_frame_time,
                "last_error": self.last_error,
                "timestamp": self._now_str()
            }

    def get_latest_frame(self):
        return None