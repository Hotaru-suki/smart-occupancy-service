from __future__ import annotations

from typing import Any, Callable

import allure
import pytest
from requests import Response

from tests.utils.api_client import APIClient
from tests.utils.assertions import assert_event_item_schema


@allure.epic("Occupancy System")
@allure.feature("Events API")
@pytest.mark.smoke
@pytest.mark.api
@pytest.mark.regression
def test_events_api_status_code(
    client: APIClient,
    attach_response: Callable[[Response, str], None],
) -> None:
    resp = client.get("/api/events?limit=10")
    attach_response(resp, "events")
    assert resp.status_code == 200


@allure.epic("Occupancy System")
@allure.feature("Events API")
@pytest.mark.api
@pytest.mark.regression
def test_events_api_schema(
    client: APIClient,
    attach_response: Callable[[Response, str], None],
) -> None:
    resp = client.get("/api/events?limit=10")
    data: dict[str, Any] = resp.json()
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
def test_events_limit_boundary_values(
    client: APIClient,
    limit: int,
    attach_kv: Callable[[str, Any], None],
) -> None:
    data: dict[str, Any] = client.get(f"/api/events?limit={limit}").json()
    attach_kv(f"events_limit_{limit}", data)

    assert len(data["events"]) <= limit


@allure.epic("Occupancy System")
@allure.feature("Events API")
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.parametrize("invalid_limit", ["0", "101", "-1", "abc", "1.5", "' or 1=1"])
def test_events_invalid_limit_inputs(
    client: APIClient,
    invalid_limit: str,
    attach_response: Callable[[Response, str], None],
) -> None:
    resp = client.get(f"/api/events?limit={invalid_limit}")
    attach_response(resp, f"events_limit_{invalid_limit}")
    assert resp.status_code == 422


@allure.epic("Occupancy System")
@allure.feature("Events API")
@pytest.mark.api
@pytest.mark.regression
def test_events_without_limit_uses_default_shape(
    client: APIClient,
    attach_kv: Callable[[str, Any], None],
) -> None:
    data: dict[str, Any] = client.get("/api/events").json()
    attach_kv("events_default", data)

    assert "events" in data
    assert isinstance(data["events"], list)
    for item in data["events"]:
        assert_event_item_schema(item)
