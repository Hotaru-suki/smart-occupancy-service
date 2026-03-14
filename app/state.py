from abc import ABC, abstractmethod


class BaseCounter(ABC):
    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def get_status(self):
        pass

    @abstractmethod
    def get_events(self, limit=20):
        pass

    @abstractmethod
    def get_health(self):
        pass

    @abstractmethod
    def get_latest_frame(self):
        pass

    @abstractmethod
    def supports_video(self) -> bool:
        pass