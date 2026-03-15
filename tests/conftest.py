from __future__ import annotations

import pytest
import requests
import allure

from tests.utils.api_client import APIClient
from tests.utils.env_loader import get_env
from tests.utils.mysql_helper import MySQLHelper
from tests.utils.redis_helper import RedisHelper
from tests.utils.reporting import attach_json, attach_text


BASE_URL = get_env("BASE_URL", "http://127.0.0.1:8000")


def _safe_get_json(path: str):
    try:
        resp = requests.get(f"{BASE_URL}{path}", timeout=5)
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


@pytest.fixture(scope="session")
def client():
    return APIClient(base_url=BASE_URL, timeout=5)


@pytest.fixture(scope="session")
def mysql_helper():
    return MySQLHelper()


@pytest.fixture(scope="session")
def redis_helper():
    return RedisHelper()


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
def precheck_service(client):
    with allure.step("预检查：确认被测服务可访问"):
        resp = client.get("/")
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
    env = _safe_get_json("/api/status")
    if env is None:
        return

    is_mock = env.get("mock", False)

    if "mock_only" in item.keywords and not is_mock:
        pytest.skip("当前不是 mock 模式，跳过 mock_only 用例")

    if "real_only" in item.keywords and is_mock:
        pytest.skip("当前是 mock 模式，跳过 real_only 用例")
