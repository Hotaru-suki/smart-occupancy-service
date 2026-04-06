from __future__ import annotations

from typing import Any

import requests
from requests import Response, Session


class APIClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000", timeout: int = 5) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session: Session = requests.Session()

    def reset(self) -> APIClient:
        self.session.cookies.clear()
        return self

    def request(self, method: str, path: str, **kwargs: Any) -> Response:
        return self.session.request(
            method,
            f"{self.base_url}{path}",
            timeout=self.timeout,
            **kwargs,
        )

    def get(self, path: str, **kwargs: Any) -> Response:
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs: Any) -> Response:
        return self.request("POST", path, **kwargs)

    def put(self, path: str, **kwargs: Any) -> Response:
        return self.request("PUT", path, **kwargs)

    def patch(self, path: str, **kwargs: Any) -> Response:
        return self.request("PATCH", path, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> Response:
        return self.request("DELETE", path, **kwargs)

    def options(self, path: str, **kwargs: Any) -> Response:
        return self.request("OPTIONS", path, **kwargs)
