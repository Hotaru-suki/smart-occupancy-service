import allure
import pytest

from tests.utils.assertions import assert_no_redirect


@allure.epic("Occupancy System")
@allure.feature("HTTP Method API")
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.parametrize(
    ("client_fixture", "method", "path", "payload"),
    [
        ("fresh_client", "PUT", "/api/health", None),
        ("client", "POST", "/api/status", {}),
        ("client", "POST", "/api/events", {}),
        ("client", "POST", "/api/history/events", {}),
        ("client", "GET", "/api/auth/logout", None),
        ("client", "GET", "/api/auth/password", None),
        ("client", "GET", "/api/auth/register", None),
        ("client", "GET", "/api/auth/login", None),
        ("client", "POST", "/api/admin/users", {}),
        ("client", "POST", "/api/admin/users/tester_x/role", {"role": "admin"}),
        ("client", "PATCH", "/api/admin/regions/default", {}),
        ("client", "PATCH", "/api/admin/regions/default/roi", {"x1": 1, "y1": 1, "x2": 2, "y2": 2}),
    ],
)
def test_api_rejects_wrong_http_methods(request, client_fixture, method, path, payload):
    api_client = request.getfixturevalue(client_fixture)
    response = api_client.request(method, path, json=payload, allow_redirects=False)

    assert response.status_code == 405
    assert "allow" in {key.lower() for key in response.headers.keys()}
    assert_no_redirect(response)
