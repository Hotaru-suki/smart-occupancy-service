import allure
import pytest

from tests.utils.assertions import assert_keys_exist, assert_bool_field


@allure.epic("Occupancy System")
@allure.feature("Health API")
@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.regression
def test_health_api_status_code(client):
    with allure.step("请求 /api/health"):
        resp = client.get("/api/health")
    assert resp.status_code == 200


@allure.epic("Occupancy System")
@allure.feature("Health API")
@pytest.mark.api
@pytest.mark.regression
def test_health_api_schema(client):
    with allure.step("校验 /api/health 返回结构"):
        resp = client.get("/api/health")
        data = resp.json()

    required_fields = [
        "mock",
        "supports_video",
        "running",
        "camera_ok",
        "detector_ok",
        "last_frame_time",
        "last_error",
        "timestamp",
    ]
    assert_keys_exist(data, required_fields)

    assert_bool_field(data["mock"], "mock")
    assert_bool_field(data["supports_video"], "supports_video")
    assert_bool_field(data["running"], "running")
    assert_bool_field(data["camera_ok"], "camera_ok")
    assert_bool_field(data["detector_ok"], "detector_ok")
    assert isinstance(data["timestamp"], str)