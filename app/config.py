from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
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

    cors_allow_origins: list[str] = ["*"]

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