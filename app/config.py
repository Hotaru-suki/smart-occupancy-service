from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    insecure_placeholder: str = "__CHANGE_ME__"
    app_name: str = "Occupancy Detection Service"
    app_version: str = "1.2.0"

    host: str = "127.0.0.1"
    port: int = 8000

    use_mock: bool = False

    video_source: int = 0
    model_path: str = "yolov8n.pt"

    roi_x1: int = 100
    roi_y1: int = 100
    roi_x2: int = 500
    roi_y2: int = 400

    enter_frames: int = 5
    leave_seconds: float = 2.0
    confidence: float = 0.4

    reconnect_interval: float = 2.0
    loop_interval: float = 0.05

    mock_interval: float = 1.0

    cors_allow_origins: list[str] = [
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ]

    auth_username: str = "admin"
    auth_password: str = "__CHANGE_ME__"
    auth_password_hash: str | None = None
    admin_registration_code: str = "__CHANGE_ME__"
    auth_cookie_name: str = "occupancy_session"
    auth_cookie_secure: bool = False
    auth_cookie_samesite: str = "lax"
    auth_session_ttl_sec: int = 8 * 60 * 60
    auth_rate_limit_window_sec: int = 10 * 60
    auth_rate_limit_max_attempts: int = 8
    auth_rate_limit_lock_sec: int = 2 * 60

    realtime_push_interval: float = 1.0
    stat_sync_interval_sec: float = 5.0

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_db: str = "occupancy_system"

    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
