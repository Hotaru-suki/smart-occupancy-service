import pytest
import requests
import allure

from tests.utils.api_client import APIClient
from tests.utils.mysql_helper import MySQLHelper
from tests.utils.redis_helper import RedisHelper


BASE_URL = "http://127.0.0.1:8000"


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
    """
    测试会话开始前先确认服务是通的
    """
    with allure.step("预检查：确认被测服务可访问"):
        resp = client.get("/")
        assert resp.status_code == 200, "被测服务未启动或不可访问"


@pytest.fixture(autouse=True)
def clean_test_redis(redis_helper):
    """
    每条用例执行前清理测试 Redis 中的关键 key，提升可控性。
    如果你不想每条都清，可以删掉 autouse=True 改成按需使用。
    """
    redis_helper.delete_key("occupancy:test_status")
    yield
    redis_helper.delete_key("occupancy:test_status")


def pytest_runtest_setup(item):
    """
    根据 mark 和当前环境自动跳过不适用的测试
    """
    env = _safe_get_json("/api/status")
    if env is None:
        return

    is_mock = env.get("mock", False)

    if "mock_only" in item.keywords and not is_mock:
        pytest.skip("当前不是 mock 模式，跳过 mock_only 用例")

    if "real_only" in item.keywords and is_mock:
        pytest.skip("当前是 mock 模式，跳过 real_only 用例")