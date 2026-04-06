from __future__ import annotations

from typing import Any, Callable

import allure
import pytest
from requests import Response

from tests.utils.api_client import APIClient
from tests.utils.assertions import assert_bool_field, assert_keys_exist


@allure.epic("Occupancy System")
@allure.feature("Root API")
@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.regression
def test_root_api_status_code(
    client: APIClient,
    attach_response: Callable[[Response, str], None],
) -> None:
    with allure.step("请求根接口 /"):
        resp = client.get("/")
        attach_response(resp, "root")

    assert resp.status_code == 200


@allure.epic("Occupancy System")
@allure.feature("Root API")
@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.regression
def test_root_api_schema(
    client: APIClient,
    attach_response: Callable[[Response, str], None],
) -> None:
    with allure.step("请求根接口并校验返回结构"):
        resp = client.get("/")
        data: dict[str, Any] = resp.json()
        attach_response(resp, "root")

    required_fields = ["service", "version", "mock", "supports_video"]
    assert_keys_exist(data, required_fields)

    assert isinstance(data["service"], str)
    assert isinstance(data["version"], str)
    assert_bool_field(data["mock"], "mock")
    assert_bool_field(data["supports_video"], "supports_video")
