from typing import Optional, List, Literal

from pydantic import BaseModel, Field


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


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=128)
    role: Optional[Literal["admin", "viewer"]] = None


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=128)
    role: Literal["admin", "viewer"] = "viewer"
    admin_registration_code: Optional[str] = None


class SessionResponse(BaseModel):
    authenticated: bool
    username: Optional[str] = None
    role: Optional[str] = None
    expires_at: Optional[int] = None
    retry_after_sec: Optional[int] = None
    remaining_attempts: Optional[int] = None


class LoginResponse(SessionResponse):
    pass


class RegisterResponse(BaseModel):
    success: bool
    username: str
    role: str
    created: bool


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class PasswordChangeResponse(BaseModel):
    success: bool
    username: str


class UserDeleteResponse(BaseModel):
    success: bool
    username: str


class BulkUserDeleteResponse(BaseModel):
    success: bool
    deleted_count: int
    usernames: List[str]


class UserInfoResponse(BaseModel):
    username: str
    role: str
    is_active: bool


class UsersResponse(BaseModel):
    items: List[UserInfoResponse]


class UpdateUserRoleRequest(BaseModel):
    role: Literal["admin", "viewer"]


class ROIUpdateRequest(BaseModel):
    x1: int
    y1: int
    x2: int
    y2: int


class RegionConfigResponse(BaseModel):
    region_id: int
    region_name: str
    camera_source: str
    roi: ROIModel
