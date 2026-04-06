from __future__ import annotations

from queue import Queue
from typing import Any

event_queue: Queue[dict[str, Any]] = Queue(maxsize=1000)
