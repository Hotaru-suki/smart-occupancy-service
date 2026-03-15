import requests


class APIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: int = 5):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

    def get(self, path: str, **kwargs):
        return self.session.get(
            f"{self.base_url}{path}",
            timeout=self.timeout,
            **kwargs
        )

    def post(self, path: str, **kwargs):
        return self.session.post(
            f"{self.base_url}{path}",
            timeout=self.timeout,
            **kwargs
        )

    def options(self, path: str, **kwargs):
        return self.session.options(
            f"{self.base_url}{path}",
            timeout=self.timeout,
            **kwargs
        )
