from __future__ import annotations

import uuid

import allure
import pytest
import requests

from tests.utils.api_client import APIClient
from tests.utils.env_loader import get_env
from tests.utils.mysql_helper import MySQLHelper
from tests.utils.redis_helper import RedisHelper
from tests.utils.reporting import attach_json, attach_text
from tests.utils.auth_payloads import AUTH_PASSWORD, AUTH_USERNAME, login_payload, register_payload
BASE_URL = get_env("BASE_URL", "http://127.0.0.1:8000")


def _safe_get_json(path: str):
    try:
        resp = requests.get(f"{BASE_URL}{path}", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def _login(api_client: APIClient, username: str, password: str, **kwargs):
    return api_client.post(
        "/api/auth/login",
        json=login_payload(username=username, password=password),
        **kwargs,
    )


@pytest.fixture(scope="session")
def anonymous_client():
    return APIClient(base_url=BASE_URL, timeout=5)


@pytest.fixture(scope="session")
def client(anonymous_client):
    login_resp = _login(anonymous_client, AUTH_USERNAME, AUTH_PASSWORD)
    assert login_resp.status_code == 200, "测试登录失败，请检查认证配置"
    return anonymous_client


@pytest.fixture
def fresh_client():
    return APIClient(base_url=BASE_URL, timeout=5)


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
def registered_user(fresh_client, unique_username):
    password = "ValidPass123!"
    response = fresh_client.post(
        "/api/auth/register",
        json=register_payload(unique_username, password, role="viewer"),
    )
    assert response.status_code in (200, 201)
    return {"username": unique_username, "password": password, "role": "viewer"}


@pytest.fixture
def viewer_client(registered_user):
    api_client = APIClient(base_url=BASE_URL, timeout=5)
    response = api_client.post(
        "/api/auth/login",
        json=login_payload(
            username=registered_user["username"],
            password=registered_user["password"],
        ),
    )
    assert response.status_code == 200
    return api_client


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
        except Exception:
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
def attach_response():
    def _attach_response(resp, name: str = "response"):
        attach_text(f"{name}_status_code", str(resp.status_code))
        try:
            attach_json(f"{name}_json", resp.json())
        except Exception:
            attach_text(f"{name}_text", resp.text)
    return _attach_response


@pytest.fixture
def attach_kv():
    def _attach_kv(name: str, data):
        if isinstance(data, (dict, list)):
            attach_json(name, data)
        else:
            attach_text(name, str(data))
    return _attach_kv


def pytest_runtest_setup(item):
    env = _safe_get_json("/api/health")
    if env is None:
        return

    is_mock = env.get("mock", False)

    if "mock_only" in item.keywords and not is_mock:
        pytest.skip("当前不是 mock 模式，跳过 mock_only 用例")

    if "real_only" in item.keywords and is_mock:
        pytest.skip("当前是 mock 模式，跳过 real_only 用例")
