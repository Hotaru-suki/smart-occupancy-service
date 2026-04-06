from __future__ import annotations

import uuid
from typing import Any

import allure
import pytest
import requests
from requests import Response

from tests.utils.api_client import APIClient
from tests.utils.auth_payloads import (
    AUTH_PASSWORD,
    AUTH_USERNAME,
    login_payload,
    register_payload,
)
from tests.utils.env_loader import get_env
from tests.utils.mysql_helper import MySQLHelper
from tests.utils.redis_helper import RedisHelper
from tests.utils.reporting import attach_json, attach_text

BASE_URL = get_env("BASE_URL", "http://127.0.0.1:8000")
_HEALTH_ENV_CACHE: dict[str, Any] | None = None


def _queue_attachment(request: pytest.FixtureRequest, kind: str, name: str, data: Any) -> None:
    attachments = getattr(request.node, "_pending_attachments", None)
    if attachments is None:
        attachments = []
        setattr(request.node, "_pending_attachments", attachments)
    attachments.append((kind, name, data))


def _flush_attachments(request: pytest.FixtureRequest) -> None:
    attachments = getattr(request.node, "_pending_attachments", [])
    for kind, name, data in attachments:
        if kind == "json":
            attach_json(name, data)
        else:
            attach_text(name, str(data))


def _safe_get_json(path: str) -> dict[str, Any] | None:
    try:
        resp = requests.get(f"{BASE_URL}{path}", timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except (requests.RequestException, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _login(api_client: APIClient, username: str, password: str, **kwargs: Any) -> Response:
    return api_client.post(
        "/api/auth/login",
        json=login_payload(username=username, password=password),
        **kwargs,
    )


@pytest.fixture(scope="session")
def anonymous_client():
    return APIClient(base_url=BASE_URL, timeout=5)


@pytest.fixture(scope="session")
def shared_fresh_client():
    return APIClient(base_url=BASE_URL, timeout=5)


@pytest.fixture(scope="session")
def client(anonymous_client):
    login_resp = _login(anonymous_client, AUTH_USERNAME, AUTH_PASSWORD)
    assert login_resp.status_code == 200, "测试登录失败，请检查认证配置"
    return anonymous_client


@pytest.fixture
def fresh_client(shared_fresh_client):
    return shared_fresh_client.reset()


@pytest.fixture(scope="session")
def mysql_helper():
    return MySQLHelper()


@pytest.fixture(scope="session")
def redis_helper():
    return RedisHelper()


@pytest.fixture
def unique_username():
    return f"tester_{uuid.uuid4().hex[:12]}"


@pytest.fixture
def registered_user(client, fresh_client, unique_username):
    password = "ValidPass123!"
    response = fresh_client.post(
        "/api/auth/register",
        json=register_payload(unique_username, password, role="viewer"),
    )
    assert response.status_code in (200, 201)
    user = {"username": unique_username, "password": password, "role": "viewer"}
    yield user
    client.delete(f"/api/admin/users/{unique_username}")


@pytest.fixture
def viewer_client(registered_user, fresh_client):
    response = fresh_client.post(
        "/api/auth/login",
        json=login_payload(
            username=registered_user["username"],
            password=registered_user["password"],
        ),
    )
    assert response.status_code == 200
    return fresh_client


@pytest.fixture(scope="session")
def env_info(client):
    root_data = client.get("/").json()
    status_data = client.get("/api/status").json()
    return {
        "root": root_data,
        "status": status_data,
        "is_mock": status_data["mock"],
        "supports_video": status_data["supports_video"],
    }


@pytest.fixture(scope="session", autouse=True)
def precheck_service():
    with allure.step("预检查：确认被测服务可访问"):
        resp = requests.get(f"{BASE_URL}/", timeout=5)
        attach_text("precheck_url", f"{BASE_URL}/")
        attach_text("precheck_status_code", str(resp.status_code))
        try:
            attach_json("precheck_response", resp.json())
        except ValueError:
            attach_text("precheck_response_text", resp.text)
        assert resp.status_code == 200, "被测服务未启动或不可访问"


@pytest.fixture(autouse=True)
def clean_test_redis(redis_helper):
    test_keys = [
        "occupancy:test_status",
        "occupancy:test_events",
    ]
    for key in test_keys:
        redis_helper.delete_key(key)
    yield
    for key in test_keys:
        redis_helper.delete_key(key)


@pytest.fixture
def deferred_attachments(request: pytest.FixtureRequest):
    request.node._pending_attachments = []
    yield

    rep_setup = getattr(request.node, "rep_setup", None)
    rep_call = getattr(request.node, "rep_call", None)
    should_attach = bool(
        (rep_setup is not None and rep_setup.failed)
        or (rep_call is not None and rep_call.failed)
    )
    if should_attach:
        _flush_attachments(request)


@pytest.fixture
def attach_response(request: pytest.FixtureRequest, deferred_attachments):
    def _attach_response(resp, name: str = "response"):
        _queue_attachment(request, "text", f"{name}_status_code", str(resp.status_code))
        try:
            _queue_attachment(request, "json", f"{name}_json", resp.json())
        except ValueError:
            _queue_attachment(request, "text", f"{name}_text", resp.text)
    return _attach_response


@pytest.fixture
def attach_kv(request: pytest.FixtureRequest, deferred_attachments):
    def _attach_kv(name: str, data):
        if isinstance(data, (dict, list)):
            _queue_attachment(request, "json", name, data)
        else:
            _queue_attachment(request, "text", name, data)
    return _attach_kv


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


def pytest_runtest_setup(item):
    global _HEALTH_ENV_CACHE

    if _HEALTH_ENV_CACHE is None:
        _HEALTH_ENV_CACHE = _safe_get_json("/api/health")

    env = _HEALTH_ENV_CACHE
    if env is None:
        return

    is_mock = env.get("mock", False)

    if "mock_only" in item.keywords and not is_mock:
        pytest.skip("当前不是 mock 模式，跳过 mock_only 用例")

    if "real_only" in item.keywords and is_mock:
        pytest.skip("当前是 mock 模式，跳过 real_only 用例")
