import cv2
import threading
import json
import time
from datetime import datetime, date

from ultralytics import YOLO

from app.state import BaseCounter
from app.infrastructure.cache import redis_client
from app.infrastructure.logging.json_logger import logger
from app.infrastructure.repositories.stat_repository import StatRepository
from app.core.roi_detector import point_in_roi
from app.core.video_frame_buffer import VideoFrameBuffer
from app.services.event_service import event_service


class PeopleCounter(BaseCounter):
    def __init__(
        self,
        video_source=0,
        model_path="yolov8n.pt",
        roi=None,
        enter_frames=5,
        leave_seconds=2.0,
        confidence=0.4,
        reconnect_interval=2.0,
        loop_interval=0.05,
        mock=False
    ):
        self.video_source = video_source
        self.model_path = model_path
        self.model = YOLO(model_path)

        self.cap = None
        self.roi = roi if roi is not None else (100, 100, 500, 400)

        self.enter_frames = enter_frames
        self.leave_seconds = leave_seconds
        self.confidence = confidence

        self.reconnect_interval = reconnect_interval
        self.loop_interval = loop_interval
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

        self._inside_frame_count = 0
        self._last_person_seen_ts = None

        self.camera_ok = False
        self.detector_ok = True
        self.last_frame_time = None
        self.last_error = None

        self.events = []
        self.current_day = str(date.today())
        self._status_snapshot = {}

        self.frame_buffer = VideoFrameBuffer()
        self.stat_repository = StatRepository()

        self._refresh_status_snapshot()

        logger.info(
            f"PeopleCounter 初始化完成: source={self.video_source}, roi={self.roi}",
            extra={"event": "people_counter_init"}
        )

    def _now(self):
        return datetime.now()

    def _now_str(self):
        return self._now().isoformat(timespec="seconds")

    def supports_video(self) -> bool:
        return True

    def _open_capture(self):
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass

        self.cap = cv2.VideoCapture(self.video_source, cv2.CAP_DSHOW)
        self.camera_ok = bool(self.cap and self.cap.isOpened())

        if self.camera_ok:
            logger.info(
                f"摄像头打开成功: source={self.video_source}",
                extra={"event": "camera_open_success"}
            )
        else:
            logger.error(
                f"摄像头打开失败: source={self.video_source}",
                extra={"event": "camera_open_failed"}
            )

        return self.camera_ok

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
                extra={"event": "mysql_daily_stat_sync_failed"}
            )

    def _reset_daily_if_needed(self):
        today = str(date.today())
        if self.current_day != today:
            self.current_day = today
            self.today_total_occupied_sec = 0.0
            self.max_people_today = 0
            self.events = []

            logger.info(
                f"检测到日期切换，重置当日统计: current_day={self.current_day}",
                extra={"event": "daily_stat_reset"}
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
                extra={"event": "redis_status_cache_failed"}
            )

    def _draw_overlay(self, frame, results, people_in_roi):
        display = frame.copy()

        x1, y1, x2, y2 = self.roi
        cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 255), 2)
        cv2.putText(
            display,
            "ROI",
            (x1, max(20, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )

        if results.boxes is not None:
            for box in results.boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])

                if cls_id != 0 or conf < self.confidence:
                    continue

                bx1, by1, bx2, by2 = box.xyxy[0].tolist()
                bx1, by1, bx2, by2 = map(int, [bx1, by1, bx2, by2])

                cv2.rectangle(display, (bx1, by1), (bx2, by2), (0, 255, 0), 2)
                cv2.putText(
                    display,
                    f"person {conf:.2f}",
                    (bx1, max(20, by1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 255, 0),
                    2
                )

        cv2.putText(
            display,
            f"People in ROI: {people_in_roi}",
            (20, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )
        cv2.putText(
            display,
            f"Status: {self.status}",
            (20, 65),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2
        )

        return display

    def _set_latest_frame(self, frame):
        self.frame_buffer.set_frame(frame)

    def get_latest_frame(self):
        return self.frame_buffer.get_frame()

    def _update_state(self, people_in_roi):
        now_ts = time.time()
        now_str = self._now_str()

        self.current_people = people_in_roi
        self.max_people_today = max(self.max_people_today, people_in_roi)

        if people_in_roi > 0:
            self.last_seen_time = now_str
            self._last_person_seen_ts = now_ts
            self._inside_frame_count += 1

            if not self.occupied and self._inside_frame_count >= self.enter_frames:
                self.occupied = True
                self.status = "occupied"
                self.occupied_since = now_ts
                self._append_event("enter_region", people_in_roi)

                logger.info(
                    f"区域进入事件触发: people_count={people_in_roi}",
                    extra={"event": "enter_region"}
                )
        else:
            self._inside_frame_count = 0

            if self.occupied and self._last_person_seen_ts is not None:
                elapsed = now_ts - self._last_person_seen_ts
                if elapsed >= self.leave_seconds:
                    if self.occupied_since is not None:
                        self.today_total_occupied_sec += max(0.0, now_ts - self.occupied_since)

                    self.occupied = False
                    self.status = "idle"
                    self.occupied_since = None
                    self.last_empty_time = now_str
                    self._append_event("leave_region", 0)

                    logger.info(
                        "区域离开事件触发",
                        extra={"event": "leave_region"}
                    )

    def process_frame(self):
        logger.info(
            "视频处理线程启动",
            extra={"event": "video_thread_start"}
        )
        self.running = True

        if not self._open_capture():
            self.last_error = "摄像头打开失败，进入重连模式。"
            logger.error(
                self.last_error,
                extra={"event": "camera_open_failed"}
            )

        while self.running:
            try:
                self._reset_daily_if_needed()

                if self.cap is None or not self.cap.isOpened():
                    self.camera_ok = False
                    time.sleep(self.reconnect_interval)
                    self._open_capture()
                    self._refresh_status_snapshot()
                    continue

                ret, frame = self.cap.read()
                if not ret or frame is None:
                    self.camera_ok = False
                    self.last_error = "读取摄像头帧失败，准备重连。"
                    logger.error(
                        self.last_error,
                        extra={"event": "camera_read_failed"}
                    )
                    try:
                        self.cap.release()
                    except Exception:
                        pass
                    time.sleep(self.reconnect_interval)
                    self._open_capture()
                    self._refresh_status_snapshot()
                    continue

                self.camera_ok = True
                self.detector_ok = True
                self.last_frame_time = self._now_str()
                self.last_error = None

                results = self.model.track(frame, persist=True, verbose=False)[0]
                people_in_roi = 0

                if results.boxes is not None:
                    for box in results.boxes:
                        cls_id = int(box.cls[0])
                        conf = float(box.conf[0])

                        if cls_id != 0 or conf < self.confidence:
                            continue

                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        center_x = (x1 + x2) / 2
                        bottom_y = y2

                        if point_in_roi(center_x, bottom_y, self.roi):
                            people_in_roi += 1

                display_frame = self._draw_overlay(frame, results, people_in_roi)
                self._set_latest_frame(display_frame)

                with self.lock:
                    self._update_state(people_in_roi)
                    self._sync_daily_stat_to_mysql()
                    self._refresh_status_snapshot()

            except Exception as e:
                with self.lock:
                    self.detector_ok = False
                    self.last_error = f"检测线程异常: {e}"
                    self._refresh_status_snapshot()

                logger.exception(
                    self.last_error,
                    extra={"event": "detect_thread_exception"}
                )
                time.sleep(0.3)

            time.sleep(self.loop_interval)

        logger.info(
            "视频处理线程退出",
            extra={"event": "video_thread_stop"}
        )

    def start(self):
        with self.lock:
            if self.running:
                return
            if self.worker_thread is not None and self.worker_thread.is_alive():
                return

            self.worker_thread = threading.Thread(target=self.process_frame, daemon=True)
            self.worker_thread.start()

        logger.info(
            "PeopleCounter 启动",
            extra={"event": "people_counter_start"}
        )

    def stop(self):
        with self.lock:
            self.running = False

        if self.worker_thread is not None:
            self.worker_thread.join(timeout=2.0)

        if self.cap is not None and self.cap.isOpened():
            self.cap.release()

        with self.lock:
            self.camera_ok = False
            self._refresh_status_snapshot()

        logger.info(
            "PeopleCounter 停止",
            extra={"event": "people_counter_stop"}
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