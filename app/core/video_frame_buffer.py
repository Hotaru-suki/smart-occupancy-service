import threading


class VideoFrameBuffer:
    def __init__(self):
        self._lock = threading.RLock()
        self._frame = None

    def set_frame(self, frame):
        with self._lock:
            self._frame = frame.copy()

    def get_frame(self):
        with self._lock:
            if self._frame is None:
                return None
            return self._frame.copy()