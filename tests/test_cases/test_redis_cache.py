import allure
import pytest


@allure.epic("Occupancy System")
@allure.feature("Redis Cache")
@pytest.mark.redis
@pytest.mark.regression
def test_status_cache_exists_after_status_api_call(client, redis_helper):
    with allure.step("先请求状态接口，触发缓存写入"):
        resp = client.get("/api/status")
        assert resp.status_code == 200

    with allure.step("检查 Redis 中 occupancy:status 是否存在"):
        exists = redis_helper.exists("occupancy:status")

    assert exists is True


@allure.epic("Occupancy System")
@allure.feature("Redis Cache")
@pytest.mark.redis
@pytest.mark.regression
def test_status_cache_content_structure(redis_helper, client):
    with allure.step("请求状态接口，确保缓存被刷新"):
        client.get("/api/status")

    with allure.step("获取 Redis 中 occupancy:status 内容"):
        cache_data = redis_helper.get_json("occupancy:status")

    assert cache_data is not None
    assert "mock" in cache_data
    assert "supports_video" in cache_data
    assert "status" in cache_data
    assert "current_people" in cache_data


@allure.epic("Occupancy System")
@allure.feature("Redis Cache")
@pytest.mark.redis
@pytest.mark.regression
def test_events_cache_readable(redis_helper, client):
    with allure.step("请求事件接口"):
        resp = client.get("/api/events?limit=10")
        assert resp.status_code == 200

    with allure.step("读取 Redis 最近事件缓存"):
        events = redis_helper.lrange_json("occupancy:events", 0, 9)

    # 这里做宽松校验，因为测试开始时可能暂时还没有事件
    assert isinstance(events, list)

    for item in events:
        assert "event" in item
        assert "people_count" in item
        assert "timestamp" in item


@allure.epic("Occupancy System")
@allure.feature("Redis Cache")
@pytest.mark.redis
@pytest.mark.regression
def test_manual_test_cache_control(redis_helper):
    with allure.step("写入测试专用缓存 key"):
        redis_helper.set_json("occupancy:test_status", {"ok": True, "source": "pytest"})

    with allure.step("读取测试专用缓存 key"):
        data = redis_helper.get_json("occupancy:test_status")

    assert data == {"ok": True, "source": "pytest"}