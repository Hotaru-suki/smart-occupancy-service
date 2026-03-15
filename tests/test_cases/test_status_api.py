import allure
import pytest

from tests.utils.assertions import (
    assert_bool_field,
    assert_iso_datetime_like,
    assert_keys_exist,
    assert_non_negative_number,
)


@allure.epic("Occupancy System")
@allure.feature("Status API")
@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.regression
def test_status_api_status_code(client, attach_response):
    with allure.step("请求 /api/status"):
        resp = client.get("/api/status")
        attach_response(resp, "status")
    assert resp.status_code == 200


@allure.epic("Occupancy System")
@allure.feature("Status API")
@pytest.mark.api
@pytest.mark.regression
def test_status_api_schema(client, attach_response):
    with allure.step("校验 /api/status 返回结构"):
        resp = client.get("/api/status")
        data = resp.json()
        attach_response(resp, "status")

    required_fields = [
        "mock",
        "supports_video",
        "occupied",
        "status",
        "current_people",
        "occupied_duration_sec",
        "today_total_occupied_sec",
        "last_seen_time",
        "last_empty_time",
        "max_people_today",
        "roi",
        "camera_ok",
        "detector_ok",
        "running",
        "last_frame_time",
        "last_error",
        "timestamp",
    ]
    assert_keys_exist(data, required_fields)

    assert_bool_field(data["mock"], "mock")
    assert_bool_field(data["supports_video"], "supports_video")
    assert_bool_field(data["occupied"], "occupied")
    assert_bool_field(data["camera_ok"], "camera_ok")
    assert_bool_field(data["detector_ok"], "detector_ok")
    assert_bool_field(data["running"], "running")

    assert isinstance(data["status"], str)
    assert isinstance(data["current_people"], int)
    assert_non_negative_number(data["occupied_duration_sec"], "occupied_duration_sec")
    assert_non_negative_number(data["today_total_occupied_sec"], "today_total_occupied_sec")
    assert isinstance(data["max_people_today"], int)
    assert_iso_datetime_like(data["last_seen_time"], "last_seen_time")
    assert_iso_datetime_like(data["last_empty_time"], "last_empty_time")
    assert_iso_datetime_like(data["last_frame_time"], "last_frame_time")
    assert_iso_datetime_like(data["timestamp"], "timestamp")
    assert data["last_error"] is None or isinstance(data["last_error"], str)

    roi = data["roi"]
    assert isinstance(roi, dict)
    for key in ["x1", "y1", "x2", "y2"]:
        assert key in roi
        assert isinstance(roi[key], int)


@allure.epic("Occupancy System")
@allure.feature("Status API")
@pytest.mark.api
@pytest.mark.regression
def test_status_logic_basic(client, attach_kv):
    with allure.step("校验 /api/status 基础业务逻辑"):
        data = client.get("/api/status").json()
        attach_kv("status_data", data)

    assert data["status"] in ["idle", "occupied"]
    assert data["current_people"] >= 0
    assert data["max_people_today"] >= 0
    assert data["occupied_duration_sec"] >= 0
    assert data["today_total_occupied_sec"] >= 0

    if data["occupied"]:
        assert data["status"] == "occupied"
    if data["current_people"] == 0:
        assert data["status"] == "idle"


@allure.epic("Occupancy System")
@allure.feature("Status API")
@pytest.mark.api
@pytest.mark.regression
def test_root_and_status_consistency(client, attach_kv):
    with allure.step("校验根接口与状态接口的 mock / supports_video 一致性"):
        root_data = client.get("/").json()
        status_data = client.get("/api/status").json()
        attach_kv("root_data", root_data)
        attach_kv("status_data", status_data)

    assert root_data["mock"] == status_data["mock"]
    assert root_data["supports_video"] == status_data["supports_video"]


@allure.epic("Occupancy System")
@allure.feature("Status API")
@pytest.mark.api
@pytest.mark.regression
def test_status_cache_consistency(client, redis_helper, attach_kv):
    with allure.step("请求状态接口并读取 Redis 缓存"):
        api_data = client.get("/api/status").json()
        cache_data = redis_helper.get_json("occupancy:status")
        attach_kv("status_api_data", api_data)
        attach_kv("status_cache_data", cache_data)

    assert cache_data is not None
    for key in [
        "mock",
        "supports_video",
        "status",
        "current_people",
        "occupied",
    ]:
        assert cache_data[key] == api_data[key]


@allure.epic("Occupancy System")
@allure.feature("Status API")
@pytest.mark.api
@pytest.mark.regression
def test_status_post_method_not_allowed(client, attach_response):
    with allure.step("校验 /api/status 不接受 POST 请求"):
        resp = client.post("/api/status", json={})
        attach_response(resp, "status_post")

    assert resp.status_code in (405, 422)


@allure.epic("Occupancy System")
@allure.feature("Status API")
@pytest.mark.api
@pytest.mark.mock_only
def test_mock_mode_video_expectation(client, attach_kv):
    with allure.step("mock 模式下 supports_video 应为 false"):
        data = client.get("/api/status").json()
        attach_kv("status_data", data)
    assert data["mock"] is True
    assert data["supports_video"] is False
