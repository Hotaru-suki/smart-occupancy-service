import allure
import pytest


@allure.epic("Occupancy System")
@allure.feature("Events API")
@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.regression
def test_events_api_status_code(client):
    with allure.step("请求 /api/events?limit=10"):
        resp = client.get("/api/events?limit=10")
    assert resp.status_code == 200


@allure.epic("Occupancy System")
@allure.feature("Events API")
@pytest.mark.api
@pytest.mark.regression
def test_events_api_schema(client):
    with allure.step("校验 /api/events 返回结构"):
        resp = client.get("/api/events?limit=10")
        data = resp.json()

    assert "mock" in data
    assert "events" in data
    assert isinstance(data["mock"], bool)
    assert isinstance(data["events"], list)

    for item in data["events"]:
        assert "timestamp" in item
        assert "event" in item
        assert "people_count" in item
        assert isinstance(item["timestamp"], str)
        assert isinstance(item["event"], str)
        assert isinstance(item["people_count"], int)


@allure.epic("Occupancy System")
@allure.feature("Events API")
@pytest.mark.api
@pytest.mark.regression
def test_events_limit_param(client):
    with allure.step("校验 limit=5 时返回数量不超过 5"):
        resp = client.get("/api/events?limit=5")
        data = resp.json()

    assert resp.status_code == 200
    assert len(data["events"]) <= 5


@allure.epic("Occupancy System")
@allure.feature("Events API")
@pytest.mark.api
@pytest.mark.regression
def test_events_invalid_limit_zero(client):
    with allure.step("校验 limit=0 参数校验"):
        resp = client.get("/api/events?limit=0")
    assert resp.status_code == 422


@allure.epic("Occupancy System")
@allure.feature("Events API")
@pytest.mark.api
@pytest.mark.regression
def test_events_invalid_limit_too_large(client):
    with allure.step("校验 limit=101 参数校验"):
        resp = client.get("/api/events?limit=101")
    assert resp.status_code == 422