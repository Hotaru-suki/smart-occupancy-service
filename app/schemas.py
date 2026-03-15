from typing import Optional, List, Literal

from pydantic import BaseModel


class ROIModel(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int


class StatusResponse(BaseModel):
    mock: bool
    supports_video: bool
    occupied: bool
    status: str
    current_people: int
    occupied_duration_sec: float
    today_total_occupied_sec: float
    last_seen_time: Optional[str]
    last_empty_time: Optional[str]
    max_people_today: int
    roi: ROIModel
    camera_ok: bool
    detector_ok: bool
    running: bool
    last_frame_time: Optional[str]
    last_error: Optional[str]
    timestamp: str


class EventItem(BaseModel):
    timestamp: str
    event: str
    people_count: int
    region_id: Optional[int] = None


class EventsResponse(BaseModel):
    mock: bool
    events: List[EventItem]


class HealthResponse(BaseModel):
    mock: bool
    supports_video: bool
    running: bool
    camera_ok: bool
    detector_ok: bool
    last_frame_time: Optional[str]
    last_error: Optional[str]
    timestamp: str


class WebRTCOffer(BaseModel):
    sdp: str
    type: Literal["offer"]


class WebRTCAnswer(BaseModel):
    sdp: str
    type: Literal["answer"]


class HistoryEventItem(BaseModel):
    id: int
    region_name: str
    event_type: str
    people_count: int
    event_time: str


class HistoryEventsResponse(BaseModel):
    items: List[HistoryEventItem]

class EventsResponse(BaseModel):
    mock: bool
    events: List[EventItem]


class HealthResponse(BaseModel):
    mock: bool
    supports_video: bool
    running: bool
    camera_ok: bool
    detector_ok: bool
    last_frame_time: Optional[str]
    last_error: Optional[str]
    timestamp: str


class WebRTCOffer(BaseModel):
    sdp: str
    type: Literal["offer"]


class WebRTCAnswer(BaseModel):
    sdp: str
    type: Literal["answer"]