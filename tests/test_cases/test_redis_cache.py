import allure
import pytest

from tests.utils.assertions import assert_event_item_schema


@allure.epic("Occupancy System")
@allure.feature("Redis Cache")
@pytest.mark.redis
@pytest.mark.regression
def test_status_cache_exists_after_status_api_call(client, redis_helper, attach_kv):
    with allure.step("先请求状态接口，触发缓存写入"):
        api_data = client.get("/api/status").json()
        attach_kv("status_api_data", api_data)

    with allure.step("检查 Redis 中 occupancy:status 是否存在"):
        exists = redis_helper.exists("occupancy:status")
        attach_kv("status_cache_exists", {"exists": exists})

    assert exists is True


@allure.epic("Occupancy System")
@allure.feature("Redis Cache")
@pytest.mark.redis
@pytest.mark.regression
def test_status_cache_content_structure(redis_helper, client, attach_kv):
    with allure.step("请求状态接口，确保缓存被刷新"):
        client.get("/api/status")

    with allure.step("获取 Redis 中 occupancy:status 内容"):
        cache_data = redis_helper.get_json("occupancy:status")
        attach_kv("status_cache_data", cache_data)

    assert cache_data is not None
    assert "mock" in cache_data
    assert "supports_video" in cache_data
    assert "status" in cache_data
    assert "current_people" in cache_data


@allure.epic("Occupancy System")
@allure.feature("Redis Cache")
@pytest.mark.redis
@pytest.mark.regression
def test_status_cache_and_api_basic_consistency(redis_helper, client, attach_kv):
    with allure.step("请求状态接口"):
        api_data = client.get("/api/status").json()
        attach_kv("status_api_data", api_data)

    with allure.step("读取 Redis 状态缓存"):
        cache_data = redis_helper.get_json("occupancy:status")
        attach_kv("status_cache_data", cache_data)

    assert cache_data is not None
    for key in ["mock", "supports_video", "status", "current_people", "occupied"]:
        assert cache_data[key] == api_data[key]


@allure.epic("Occupancy System")
@allure.feature("Redis Cache")
@pytest.mark.redis
@pytest.mark.regression
def test_events_cache_readable(redis_helper, client, attach_kv):
    with allure.step("请求事件接口"):
        api_data = client.get("/api/events?limit=10").json()
        attach_kv("events_api_data", api_data)

    with allure.step("读取 Redis 最近事件缓存"):
        events = redis_helper.lrange_json("occupancy:events", 0, 9)
        attach_kv("events_cache_data", events)

    assert isinstance(events, list)
    for item in events:
        assert_event_item_schema(item)


@allure.epic("Occupancy System")
@allure.feature("Redis Cache")
@pytest.mark.redis
@pytest.mark.regression
def test_events_cache_and_api_basic_consistency(redis_helper, client, attach_kv):
    with allure.step("请求事件接口并读取 Redis 事件缓存"):
        api_events = client.get("/api/events?limit=5").json()["events"]
        cache_events = redis_helper.lrange_json("occupancy:events", 0, 4)
        attach_kv("events_api_data", api_events)
        attach_kv("events_cache_data", cache_events)

    assert isinstance(cache_events, list)
    compare_count = min(len(api_events), len(cache_events))
    for index in range(compare_count):
        assert cache_events[index]["event"] == api_events[index]["event"]
        assert cache_events[index]["people_count"] == api_events[index]["people_count"]


@allure.epic("Occupancy System")
@allure.feature("Redis Cache")
@pytest.mark.redis
@pytest.mark.regression
def test_manual_test_cache_control(redis_helper, attach_kv):
    with allure.step("写入测试专用缓存 key"):
        redis_helper.set_json("occupancy:test_status", {"ok": True, "source": "pytest"})

    with allure.step("读取测试专用缓存 key"):
        data = redis_helper.get_json("occupancy:test_status")
        attach_kv("manual_test_status", data)

    assert data == {"ok": True, "source": "pytest"}
