from aiortc import VideoStreamTrack
from av import VideoFrame
import numpy as np
import cv2

from app.infrastructure.logging.json_logger import logger


class CounterVideoTrack(VideoStreamTrack):
    def __init__(self, counter):
        super().__init__()
        self.counter = counter
        self._no_frame_logged = False

    async def recv(self):
        pts, time_base = await self.next_timestamp()

        frame = self.counter.get_latest_frame()
        if frame is None:
            if not self._no_frame_logged:
                logger.info(
                    "WebRTC 视频流当前无可用帧，返回占位图",
                    extra={"event": "video_track_no_frame"}
                )
                self._no_frame_logged = True

            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(
                frame,
                "No Frame",
                (220, 240),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                (0, 255, 255),
                2
            )
        else:
            if self._no_frame_logged:
                logger.info(
                    "WebRTC 视频流恢复正常帧输出",
                    extra={"event": "video_track_frame_recovered"}
                )
                self._no_frame_logged = False

        video_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        video_frame.pts = pts
        video_frame.time_base = time_base
        return video_frame