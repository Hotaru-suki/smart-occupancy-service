import allure
import pytest


@allure.epic("Occupancy System")
@allure.feature("History API")
@pytest.mark.api
@pytest.mark.regression
def test_history_events_status_code(client, attach_response):
    resp = client.get("/api/history/events?limit=10")
    attach_response(resp, "history_events")
    assert resp.status_code == 200


@allure.epic("Occupancy System")
@allure.feature("History API")
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.parametrize(
    ("query", "expected_status"),
    [
        ("region_name=' OR '1'='1", 200),
        ("event_type=<script>alert(1)</script>", 200),
        ("region_name=../../etc/passwd", 200),
        ("limit=0", 422),
        ("limit=999", 422),
        ("limit=' OR 1=1", 422),
    ],
)
def test_history_events_handles_boundary_and_injection_inputs(client, query, expected_status, attach_response):
    resp = client.get(f"/api/history/events?{query}")
    attach_response(resp, "history_events_query")
    assert resp.status_code == expected_status
