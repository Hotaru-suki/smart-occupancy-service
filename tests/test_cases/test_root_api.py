import allure
import pytest

from tests.utils.assertions import assert_keys_exist, assert_bool_field


@allure.epic("Occupancy System")
@allure.feature("Root API")
@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.regression
def test_root_api_status_code(client, attach_response):
    with allure.step("请求根接口 /"):
        resp = client.get("/")
        attach_response(resp, "root")

    assert resp.status_code == 200


@allure.epic("Occupancy System")
@allure.feature("Root API")
@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.regression
def test_root_api_schema(client, attach_response):
    with allure.step("请求根接口并校验返回结构"):
        resp = client.get("/")
        data = resp.json()
        attach_response(resp, "root")

    required_fields = ["service", "version", "mock", "supports_video"]
    assert_keys_exist(data, required_fields)

    assert isinstance(data["service"], str)
    assert isinstance(data["version"], str)
    assert_bool_field(data["mock"], "mock")
    assert_bool_field(data["supports_video"], "supports_video")
