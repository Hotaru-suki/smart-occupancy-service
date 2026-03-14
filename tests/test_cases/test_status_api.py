import allure
import pytest

from tests.utils.assertions import (
    assert_keys_exist,
    assert_bool_field,
    assert_non_negative_number,
)


@allure.epic("Occupancy System")
@allure.feature("Status API")
@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.regression
def test_status_api_status_code(client):
    with allure.step("请求 /api/status"):
        resp = client.get("/api/status")
    assert resp.status_code == 200


@allure.epic("Occupancy System")
@allure.feature("Status API")
@pytest.mark.api
@pytest.mark.regression
def test_status_api_schema(client):
    with allure.step("校验 /api/status 返回结构"):
        resp = client.get("/api/status")
        data = resp.json()

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
    assert isinstance(data["timestamp"], str)

    roi = data["roi"]
    assert isinstance(roi, dict)
    for key in ["x1", "y1", "x2", "y2"]:
        assert key in roi
        assert isinstance(roi[key], int)


@allure.epic("Occupancy System")
@allure.feature("Status API")
@pytest.mark.api
@pytest.mark.regression
def test_status_logic_basic(client):
    with allure.step("校验 /api/status 基础业务逻辑"):
        resp = client.get("/api/status")
        data = resp.json()

    assert data["status"] in ["idle", "occupied"]
    assert data["current_people"] >= 0
    assert data["max_people_today"] >= 0
    assert data["occupied_duration_sec"] >= 0
    assert data["today_total_occupied_sec"] >= 0


@allure.epic("Occupancy System")
@allure.feature("Status API")
@pytest.mark.api
@pytest.mark.regression
def test_root_and_status_consistency(client):
    with allure.step("校验根接口与状态接口的 mock / supports_video 一致性"):
        root_resp = client.get("/")
        status_resp = client.get("/api/status")

        root_data = root_resp.json()
        status_data = status_resp.json()

    assert root_data["mock"] == status_data["mock"]
    assert root_data["supports_video"] == status_data["supports_video"]


@allure.epic("Occupancy System")
@allure.feature("Status API")
@pytest.mark.api
@pytest.mark.mock_only
def test_mock_mode_video_expectation(client):
    with allure.step("mock 模式下 supports_video 应为 false"):
        data = client.get("/api/status").json()
    assert data["mock"] is True
    assert data["supports_video"] is False