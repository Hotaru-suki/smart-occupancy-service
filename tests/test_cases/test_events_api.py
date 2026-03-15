import allure
import pytest

from tests.utils.assertions import assert_event_item_schema


@allure.epic("Occupancy System")
@allure.feature("Events API")
@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.regression
def test_events_api_status_code(client, attach_response):
    with allure.step("请求 /api/events?limit=10"):
        resp = client.get("/api/events?limit=10")
        attach_response(resp, "events")
    assert resp.status_code == 200


@allure.epic("Occupancy System")
@allure.feature("Events API")
@pytest.mark.api
@pytest.mark.regression
def test_events_api_schema(client, attach_response):
    with allure.step("校验 /api/events 返回结构"):
        resp = client.get("/api/events?limit=10")
        data = resp.json()
        attach_response(resp, "events")

    assert "mock" in data
    assert "events" in data
    assert isinstance(data["mock"], bool)
    assert isinstance(data["events"], list)

    for item in data["events"]:
        assert_event_item_schema(item)


@allure.epic("Occupancy System")
@allure.feature("Events API")
@pytest.mark.api
@pytest.mark.regression
def test_events_limit_param(client, attach_kv):
    with allure.step("校验 limit=5 时返回数量不超过 5"):
        data = client.get("/api/events?limit=5").json()
        attach_kv("events_limit_5", data)

    assert len(data["events"]) <= 5


@allure.epic("Occupancy System")
@allure.feature("Events API")
@pytest.mark.api
@pytest.mark.regression
def test_events_invalid_limit_zero(client, attach_response):
    with allure.step("校验 limit=0 参数校验"):
        resp = client.get("/api/events?limit=0")
        attach_response(resp, "events_limit_zero")
    assert resp.status_code == 422


@allure.epic("Occupancy System")
@allure.feature("Events API")
@pytest.mark.api
@pytest.mark.regression
def test_events_invalid_limit_too_large(client, attach_response):
    with allure.step("校验 limit=101 参数校验"):
        resp = client.get("/api/events?limit=101")
        attach_response(resp, "events_limit_too_large")
    assert resp.status_code == 422


@allure.epic("Occupancy System")
@allure.feature("Events API")
@pytest.mark.api
@pytest.mark.regression
def test_events_invalid_limit_negative(client, attach_response):
    with allure.step("校验 limit=-1 参数校验"):
        resp = client.get("/api/events?limit=-1")
        attach_response(resp, "events_limit_negative")
    assert resp.status_code == 422


@allure.epic("Occupancy System")
@allure.feature("Events API")
@pytest.mark.api
@pytest.mark.regression
def test_events_invalid_limit_non_integer(client, attach_response):
    with allure.step("校验 limit=abc 参数校验"):
        resp = client.get("/api/events?limit=abc")
        attach_response(resp, "events_limit_non_integer")
    assert resp.status_code == 422


@allure.epic("Occupancy System")
@allure.feature("Events API")
@pytest.mark.api
@pytest.mark.regression
def test_events_without_limit_uses_default_shape(client, attach_kv):
    with allure.step("不传 limit 时也应返回标准结构"):
        data = client.get("/api/events").json()
        attach_kv("events_default", data)

    assert "events" in data
    assert isinstance(data["events"], list)
    for item in data["events"]:
        assert_event_item_schema(item)
