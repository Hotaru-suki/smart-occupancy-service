import uuid

import allure
import pytest

from tests.utils.assertions import assert_no_redirect
from tests.utils.auth_payloads import (
    ADMIN_REGISTRATION_CODE,
    AUTH_PASSWORD,
    AUTH_USERNAME,
    login_payload,
    register_payload,
)
from tests.utils.env_loader import get_env


AUTH_RATE_LIMIT_MAX_ATTEMPTS = int(get_env("AUTH_RATE_LIMIT_MAX_ATTEMPTS", "8"))


@allure.epic("Occupancy System")
@allure.feature("Auth API")
@pytest.mark.api
@pytest.mark.regression
def test_admin_login_success_returns_session_cookie(fresh_client, attach_response):
    resp = fresh_client.post("/api/auth/login", json=login_payload())
    attach_response(resp, "auth_admin_login_success")

    assert resp.status_code == 200
    assert resp.json()["authenticated"] is True
    assert resp.json()["role"] == "admin"


@allure.epic("Occupancy System")
@allure.feature("Auth API")
@pytest.mark.api
@pytest.mark.regression
def test_viewer_register_then_login_success(fresh_client, unique_username, attach_kv):
    register_resp = fresh_client.post(
        "/api/auth/register",
        json=register_payload(unique_username, "ValidPass123!", role="viewer"),
    )
    login_resp = fresh_client.post(
        "/api/auth/login",
        json=login_payload(unique_username, "ValidPass123!"),
    )
    attach_kv("viewer_register", register_resp.json())
    attach_kv("viewer_login", login_resp.json())

    assert register_resp.status_code == 201
    assert login_resp.status_code == 200
    assert login_resp.json()["role"] == "viewer"


@allure.epic("Occupancy System")
@allure.feature("Auth API")
@pytest.mark.api
@pytest.mark.regression
def test_admin_register_requires_registration_code(fresh_client, unique_username, attach_response):
    resp = fresh_client.post(
        "/api/auth/register",
        json=register_payload(unique_username, "ValidPass123!", role="admin"),
    )
    attach_response(resp, "auth_admin_register_missing_code")

    assert resp.status_code == 403


@allure.epic("Occupancy System")
@allure.feature("Auth API")
@pytest.mark.api
@pytest.mark.regression
def test_admin_register_success_with_valid_code(fresh_client, unique_username, attach_response):
    resp = fresh_client.post(
        "/api/auth/register",
        json=register_payload(
            unique_username,
            "ValidPass123!",
            role="admin",
            admin_registration_code=ADMIN_REGISTRATION_CODE,
        ),
    )
    attach_response(resp, "auth_admin_register_success")

    assert resp.status_code == 201
    assert resp.json()["role"] == "admin"


@allure.epic("Occupancy System")
@allure.feature("Auth API")
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.parametrize(
    ("payload", "expected_status"),
    [
        ({"username": "ab", "password": "ValidPass123!"}, 422),
        ({"username": "bad user", "password": "ValidPass123!"}, 422),
        ({"username": "user<script>", "password": "ValidPass123!"}, 422),
        ({"username": "admin", "password": "short"}, 422),
        ({"username": AUTH_USERNAME, "password": "WrongPass123!"}, 401),
        ({"username": AUTH_USERNAME, "password": AUTH_PASSWORD, "role": "viewer"}, 403),
        ({"username": "' OR '1'='1", "password": "WrongPass123!"}, 422),
        ({"username": "../../admin", "password": "WrongPass123!"}, 422),
    ],
)
def test_login_rejects_invalid_role_and_injection_inputs(fresh_client, payload, expected_status, attach_response):
    resp = fresh_client.post(
        "/api/auth/login",
        json=payload,
        headers={"x-forwarded-for": f"198.51.100.{uuid.uuid4().int % 200 + 1}"},
    )
    attach_response(resp, f"auth_login_{expected_status}")
    assert resp.status_code == expected_status


@allure.epic("Occupancy System")
@allure.feature("Auth API")
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.parametrize(
    ("payload", "expected_status"),
    [
        ({"username": "ab", "password": "ValidPass123!", "role": "viewer"}, 422),
        ({"username": "viewer alpha", "password": "ValidPass123!", "role": "viewer"}, 422),
        ({"username": "viewer_gamma", "password": "short", "role": "viewer"}, 422),
        ({"username": "viewer_gamma", "password": "x" * 129, "role": "viewer"}, 422),
        ({"username": "ops_team", "password": "ValidPass123!", "role": "admin"}, 403),
        ({"username": "';drop-table--", "password": "ValidPass123!", "role": "viewer"}, 422),
    ],
)
def test_register_validates_role_boundaries_and_special_inputs(fresh_client, payload, expected_status, attach_response):
    resp = fresh_client.post("/api/auth/register", json=payload)
    attach_response(resp, "auth_register_validation")
    assert resp.status_code == expected_status


@allure.epic("Occupancy System")
@allure.feature("Auth API")
@pytest.mark.api
@pytest.mark.regression
def test_register_is_idempotent_for_same_credentials_and_role(fresh_client, unique_username, attach_kv):
    payload = register_payload(unique_username, "ValidPass123!", role="viewer")
    first = fresh_client.post("/api/auth/register", json=payload)
    second = fresh_client.post("/api/auth/register", json=payload)
    attach_kv("register_first", first.json())
    attach_kv("register_second", second.json())

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.json()["created"] is False


@allure.epic("Occupancy System")
@allure.feature("Auth API")
@pytest.mark.api
@pytest.mark.regression
def test_register_conflicts_when_same_username_diff_role_or_password(fresh_client, unique_username, attach_response):
    fresh_client.post(
        "/api/auth/register",
        json=register_payload(unique_username, "ValidPass123!", role="viewer"),
    )
    resp = fresh_client.post(
        "/api/auth/register",
        json=register_payload(
            unique_username,
            "AnotherPass123!",
            role="admin",
            admin_registration_code=ADMIN_REGISTRATION_CODE,
        ),
    )
    attach_response(resp, "auth_register_conflict")
    assert resp.status_code == 409


@allure.epic("Occupancy System")
@allure.feature("Auth API")
@pytest.mark.api
@pytest.mark.regression
def test_login_rate_limit_after_repeated_failures(fresh_client, attach_response):
    headers = {"x-forwarded-for": "203.0.113.66"}
    failure_response = None
    for _ in range(AUTH_RATE_LIMIT_MAX_ATTEMPTS - 1):
        failure_response = fresh_client.post(
            "/api/auth/login",
            json=login_payload(password="WrongPass123!"),
            headers=headers,
        )
        assert failure_response.status_code == 401

    limited = fresh_client.post(
        "/api/auth/login",
        json=login_payload(password="WrongPass123!"),
        headers=headers,
    )
    attach_response(failure_response, "auth_login_failure_before_limit")
    attach_response(limited, "auth_login_rate_limited")

    assert limited.status_code == 429
    assert limited.json()["retry_after_sec"] is not None
    assert limited.json()["remaining_attempts"] == 0


@allure.epic("Occupancy System")
@allure.feature("Auth API")
@pytest.mark.api
@pytest.mark.regression
def test_session_endpoint_after_login(client, attach_kv):
    data = client.get("/api/auth/session").json()
    attach_kv("auth_session", data)
    assert data["authenticated"] is True
    assert data["username"] == AUTH_USERNAME.lower()
    assert data["role"] == "admin"


@allure.epic("Occupancy System")
@allure.feature("Auth API")
@pytest.mark.api
@pytest.mark.regression
def test_logout_clears_session_cookie(registered_user, fresh_client, attach_kv):
    fresh_client.post(
        "/api/auth/login",
        json=login_payload(
            username=registered_user["username"],
            password=registered_user["password"],
        ),
    )
    logout_resp = fresh_client.post("/api/auth/logout")
    session_resp = fresh_client.get("/api/auth/session")
    attach_kv("logout_response", logout_resp.json())
    attach_kv("session_after_logout", session_resp.json())

    assert logout_resp.status_code == 200
    assert session_resp.json()["authenticated"] is False


@allure.epic("Occupancy System")
@allure.feature("Auth API")
@pytest.mark.api
@pytest.mark.regression
def test_viewer_can_change_own_password(fresh_client, unique_username, attach_kv):
    original_password = "ValidPass123!"
    new_password = "ViewerNext123!"
    fresh_client.post(
        "/api/auth/register",
        json=register_payload(unique_username, original_password, role="viewer"),
    )
    login_resp = fresh_client.post(
        "/api/auth/login",
        json=login_payload(unique_username, original_password),
    )
    change_resp = fresh_client.patch(
        "/api/auth/password",
        json={"current_password": original_password, "new_password": new_password},
    )
    attach_kv("viewer_change_password_login", login_resp.json())
    attach_kv("viewer_change_password_response", change_resp.json())

    fresh_login_old = fresh_client.post(
        "/api/auth/login",
        json=login_payload(unique_username, original_password),
    )
    fresh_client.post("/api/auth/logout")
    fresh_login_new = fresh_client.post(
        "/api/auth/login",
        json=login_payload(unique_username, new_password),
    )

    assert change_resp.status_code == 200
    assert fresh_login_old.status_code == 401
    assert fresh_login_new.status_code == 200


@allure.epic("Occupancy System")
@allure.feature("Auth API")
@pytest.mark.api
@pytest.mark.regression
def test_admin_can_change_own_password(fresh_client, unique_username, attach_response):
    original_password = "AdminPass123!"
    new_password = "AdminPass456!"
    register_resp = fresh_client.post(
        "/api/auth/register",
        json=register_payload(
            unique_username,
            original_password,
            role="admin",
            admin_registration_code=ADMIN_REGISTRATION_CODE,
        ),
    )
    assert register_resp.status_code == 201

    login_resp = fresh_client.post(
        "/api/auth/login",
        json=login_payload(unique_username, original_password),
    )
    assert login_resp.status_code == 200

    change_resp = fresh_client.patch(
        "/api/auth/password",
        json={"current_password": original_password, "new_password": new_password},
    )
    attach_response(change_resp, "auth_admin_change_password")
    assert change_resp.status_code == 200


@allure.epic("Occupancy System")
@allure.feature("Auth API")
@pytest.mark.api
@pytest.mark.regression
def test_change_password_rejects_wrong_current_password(fresh_client, unique_username, attach_response):
    password = "ValidPass123!"
    fresh_client.post(
        "/api/auth/register",
        json=register_payload(unique_username, password, role="viewer"),
    )
    fresh_client.post(
        "/api/auth/login",
        json=login_payload(unique_username, password),
    )
    resp = fresh_client.patch(
        "/api/auth/password",
        json={"current_password": "WrongPass123!", "new_password": "ValidPass456!"},
    )
    attach_response(resp, "auth_change_password_wrong_current")
    assert resp.status_code == 401


@allure.epic("Occupancy System")
@allure.feature("Auth API")
@pytest.mark.api
@pytest.mark.regression
def test_status_requires_authentication(fresh_client, attach_response):
    resp = fresh_client.get("/api/status")
    attach_response(resp, "status_requires_auth")
    assert resp.status_code == 401


@allure.epic("Occupancy System")
@allure.feature("Auth API")
@pytest.mark.api
@pytest.mark.regression
def test_viewer_session_after_login_without_role_hint(fresh_client, unique_username, attach_kv):
    fresh_client.post(
        "/api/auth/register",
        json=register_payload(unique_username, "ValidPass123!", role="viewer"),
    )
    login_resp = fresh_client.post(
        "/api/auth/login",
        json=login_payload(unique_username, "ValidPass123!"),
    )
    session_resp = fresh_client.get("/api/auth/session")
    attach_kv("viewer_session_login", login_resp.json())
    attach_kv("viewer_session_state", session_resp.json())

    assert login_resp.status_code == 200
    assert login_resp.json()["role"] == "viewer"
    assert session_resp.json()["authenticated"] is True
    assert session_resp.json()["role"] == "viewer"


@allure.epic("Occupancy System")
@allure.feature("Auth API")
@pytest.mark.api
@pytest.mark.regression
def test_login_with_explicit_wrong_role_is_rejected(fresh_client, unique_username, attach_response):
    fresh_client.post(
        "/api/auth/register",
        json=register_payload(unique_username, "ValidPass123!", role="viewer"),
    )
    resp = fresh_client.post(
        "/api/auth/login",
        json=login_payload(unique_username, "ValidPass123!", role="admin"),
    )
    attach_response(resp, "auth_login_wrong_role")
    assert resp.status_code == 403


@allure.epic("Occupancy System")
@allure.feature("Auth API")
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.parametrize("path", ["/", "/api/health", "/api/auth/session", "/api/auth/login", "/api/auth/register"])
def test_public_endpoints_do_not_redirect(path, fresh_client):
    method = "POST" if path in {"/api/auth/login", "/api/auth/register"} else "GET"
    payload = login_payload("demo_user", "ValidPass123!") if path == "/api/auth/login" else (
        register_payload("demo_user", "ValidPass123!", role="viewer") if path == "/api/auth/register" else None
    )
    headers = {"x-forwarded-for": "203.0.113.10"} if path == "/api/auth/login" else None
    response = fresh_client.request(method, path, json=payload, headers=headers, allow_redirects=False)
    assert_no_redirect(response)


@allure.epic("Occupancy System")
@allure.feature("Auth API")
@pytest.mark.api
@pytest.mark.regression
@pytest.mark.parametrize("path", ["/api/status", "/api/events", "/api/history/events", "/api/webrtc-offer", "/api/auth/password"])
def test_protected_endpoints_do_not_redirect_when_unauthenticated(path, fresh_client):
    method = "POST" if path == "/api/webrtc-offer" else ("PATCH" if path == "/api/auth/password" else "GET")
    payload = (
        {"sdp": "fake", "type": "offer"} if method == "POST" else (
            {"current_password": "ValidPass123!", "new_password": "ValidPass456!"}
            if method == "PATCH"
            else None
        )
    )
    response = fresh_client.request(method, path, json=payload, allow_redirects=False)
    assert response.status_code in (400, 401)
    assert_no_redirect(response)
