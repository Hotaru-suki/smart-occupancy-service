import allure
import pytest

from tests.utils.assertions import assert_event_item_schema


@allure.epic("Occupancy System")
@allure.feature("Events API")
@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.regression
def test_events_api_status_code(client, attach_response):
    resp = client.get("/api/events?limit=10")
    attach_response(resp, "events")
    assert resp.status_code == 200


@allure.epic("Occupancy System")
@allure.feature("Events API")
@pytest.mark.api
@pytest.mark.regression
def test_events_api_schema(client, attach_response):
    resp = client.get("/api/events?limit=10")
    data = resp.json()
    attach_response(resp, "events_schema")

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
@pytest.mark.parametrize("limit", [1, 5, 20, 100])
def test_events_limit_boundary_values(client, limit, attach_kv):
    data = client.get(f"/api/events?limit={limit}").json()
    attach_kv(f"events_limit_{limit}", data)

    assert len(data["events"]) <= limit


@allure.epic("Occupancy System")
@allure.feature("Events API")
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.parametrize("invalid_limit", ["0", "101", "-1", "abc", "1.5", "' or 1=1"])
def test_events_invalid_limit_inputs(client, invalid_limit, attach_response):
    resp = client.get(f"/api/events?limit={invalid_limit}")
    attach_response(resp, f"events_limit_{invalid_limit}")
    assert resp.status_code == 422


@allure.epic("Occupancy System")
@allure.feature("Events API")
@pytest.mark.api
@pytest.mark.regression
def test_events_without_limit_uses_default_shape(client, attach_kv):
    data = client.get("/api/events").json()
    attach_kv("events_default", data)

    assert "events" in data
    assert isinstance(data["events"], list)
    for item in data["events"]:
        assert_event_item_schema(item)
