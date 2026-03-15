import allure
import pytest

from tests.utils.assertions import assert_bool_field, assert_iso_datetime_like, assert_keys_exist


@allure.epic("Occupancy System")
@allure.feature("Health API")
@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.regression
def test_health_api_status_code(client, attach_response):
    with allure.step("请求 /api/health"):
        resp = client.get("/api/health")
        attach_response(resp, "health")
    assert resp.status_code == 200


@allure.epic("Occupancy System")
@allure.feature("Health API")
@pytest.mark.api
@pytest.mark.regression
def test_health_api_schema(client, attach_response):
    with allure.step("校验 /api/health 返回结构"):
        resp = client.get("/api/health")
        data = resp.json()
        attach_response(resp, "health")

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
    assert_iso_datetime_like(data["last_frame_time"], "last_frame_time")
    assert_iso_datetime_like(data["timestamp"], "timestamp")
    assert data["last_error"] is None or isinstance(data["last_error"], str)


@allure.epic("Occupancy System")
@allure.feature("Health API")
@pytest.mark.api
@pytest.mark.regression
def test_health_and_status_environment_consistency(client, attach_kv):
    with allure.step("分别获取 /api/health 与 /api/status"):
        health_data = client.get("/api/health").json()
        status_data = client.get("/api/status").json()
        attach_kv("health_data", health_data)
        attach_kv("status_data", status_data)

    assert health_data["mock"] == status_data["mock"]
    assert health_data["supports_video"] == status_data["supports_video"]
    assert health_data["running"] == status_data["running"]
    assert health_data["camera_ok"] == status_data["camera_ok"]
    assert health_data["detector_ok"] == status_data["detector_ok"]
