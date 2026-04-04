from concurrent.futures import ThreadPoolExecutor

import allure
import pytest

from tests.utils.assertions import assert_no_redirect
from tests.utils.api_client import APIClient
from tests.utils.auth_payloads import login_payload
from tests.utils.env_loader import get_env


BASE_URL = get_env("BASE_URL", "http://127.0.0.1:8000")
AUTH_USERNAME = get_env("AUTH_USERNAME", "admin")
AUTH_PASSWORD = get_env("AUTH_PASSWORD", "ChangeMe123!")


@allure.epic("Occupancy System")
@allure.feature("Admin API")
@pytest.mark.api
@pytest.mark.regression
def test_viewer_cannot_access_admin_resources(viewer_client, attach_response):
    resp = viewer_client.get("/api/admin/users")
    attach_response(resp, "admin_users_forbidden")
    assert resp.status_code == 403


@allure.epic("Occupancy System")
@allure.feature("Admin API")
@pytest.mark.api
@pytest.mark.regression
def test_admin_can_list_users(client, attach_kv):
    data = client.get("/api/admin/users").json()
    attach_kv("admin_users", data)
    assert "items" in data
    assert isinstance(data["items"], list)


@allure.epic("Occupancy System")
@allure.feature("Admin API")
@pytest.mark.api
@pytest.mark.regression
def test_admin_can_update_viewer_role_and_viewer_gains_access(client, viewer_client, registered_user, attach_kv):
    username = registered_user["username"]

    update_resp = client.patch(
        f"/api/admin/users/{username}/role",
        json={"role": "admin"},
    )
    attach_kv("promote_user", update_resp.json())
    assert update_resp.status_code == 200

    users_resp = viewer_client.get("/api/events?limit=5")
    assert users_resp.status_code == 200


@allure.epic("Occupancy System")
@allure.feature("Admin API")
@pytest.mark.api
@pytest.mark.regression
def test_admin_can_delete_test_user(client, registered_user, attach_response):
    username = registered_user["username"]
    delete_resp = client.delete(f"/api/admin/users/{username}")
    attach_response(delete_resp, "admin_delete_user")
    assert delete_resp.status_code == 200

    list_resp = client.get("/api/admin/users")
    usernames = [item["username"] for item in list_resp.json()["items"]]
    assert username not in usernames


@allure.epic("Occupancy System")
@allure.feature("Admin API")
@pytest.mark.api
@pytest.mark.regression
def test_admin_can_bulk_delete_test_users(client, fresh_client, unique_username, attach_response):
    usernames = [unique_username, f"tester_{unique_username.split('_')[-1]}x"]
    for username in usernames:
        response = fresh_client.post(
            "/api/auth/register",
            json={"username": username, "password": "ValidPass123!", "role": "viewer"},
        )
        assert response.status_code in (200, 201)

    delete_resp = client.delete("/api/admin/users")
    attach_response(delete_resp, "admin_bulk_delete_test_users")
    assert delete_resp.status_code == 200
    assert delete_resp.json()["deleted_count"] >= 2
    assert AUTH_USERNAME.lower() not in delete_resp.json()["usernames"]


@allure.epic("Occupancy System")
@allure.feature("Admin API")
@pytest.mark.api
@pytest.mark.regression
def test_admin_cannot_delete_self(client, attach_response):
    resp = client.delete(f"/api/admin/users/{AUTH_USERNAME.lower()}")
    attach_response(resp, "admin_delete_self")
    assert resp.status_code == 409


@allure.epic("Occupancy System")
@allure.feature("Admin API")
@pytest.mark.api
@pytest.mark.regression
def test_viewer_cannot_delete_users(viewer_client, registered_user, attach_response):
    resp = viewer_client.delete(f"/api/admin/users/{registered_user['username']}")
    attach_response(resp, "viewer_delete_user_forbidden")
    assert resp.status_code == 403


@allure.epic("Occupancy System")
@allure.feature("Admin API")
@pytest.mark.api
@pytest.mark.regression
def test_viewer_can_read_status_but_not_events(viewer_client, attach_response):
    status_resp = viewer_client.get("/api/status")
    events_resp = viewer_client.get("/api/events?limit=5")
    attach_response(status_resp, "viewer_status")
    attach_response(events_resp, "viewer_events")

    assert status_resp.status_code == 200
    assert events_resp.status_code == 403


@allure.epic("Occupancy System")
@allure.feature("Admin API")
@pytest.mark.api
@pytest.mark.regression
def test_admin_roi_update_is_serializable_under_concurrent_writes(client, attach_kv):
    payloads = [
      {"x1": 120, "y1": 120, "x2": 420, "y2": 320},
      {"x1": 140, "y1": 140, "x2": 460, "y2": 360},
    ]

    def update_roi(payload):
        api_client = APIClient(base_url=BASE_URL, timeout=5)
        login = api_client.post(
            "/api/auth/login",
            json=login_payload(AUTH_USERNAME, AUTH_PASSWORD),
        )
        assert login.status_code == 200
        response = api_client.put("/api/admin/regions/default/roi", json=payload)
        return response.status_code, response.json()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(update_roi, payloads))

    attach_kv("concurrent_roi_updates", results)
    assert all(status == 200 for status, _ in results)

    final_region = client.get("/api/admin/regions/default").json()
    attach_kv("final_region", final_region)
    assert final_region["roi"] in payloads


@allure.epic("Occupancy System")
@allure.feature("Admin API")
@pytest.mark.api
@pytest.mark.regression
def test_admin_write_and_viewer_read_can_run_concurrently(client, viewer_client, attach_kv):
    roi_payload = {"x1": 130, "y1": 130, "x2": 430, "y2": 330}

    def admin_write():
        return client.put("/api/admin/regions/default/roi", json=roi_payload).status_code

    def viewer_read():
        return viewer_client.get("/api/status").status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        write_status, read_status = list(executor.map(lambda fn: fn(), [admin_write, viewer_read]))

    attach_kv("admin_write_viewer_read", {"write_status": write_status, "read_status": read_status})
    assert write_status == 200
    assert read_status == 200


@allure.epic("Occupancy System")
@allure.feature("Admin API")
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/admin/users"),
        ("GET", "/api/admin/regions/default"),
        ("DELETE", "/api/admin/users/someone"),
    ],
)
def test_admin_endpoints_do_not_redirect_when_forbidden(method, path, viewer_client):
    response = viewer_client.request(method, path, allow_redirects=False)
    assert response.status_code == 403
    assert_no_redirect(response)
