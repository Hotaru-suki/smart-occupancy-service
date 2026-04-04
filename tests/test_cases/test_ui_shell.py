import allure
import pytest

from tests.utils.assertions import assert_no_redirect


@allure.epic("Occupancy System")
@allure.feature("UI Shell")
@pytest.mark.api
@pytest.mark.regression
def test_ui_shell_renders_login_first(fresh_client):
    response = fresh_client.get("/ui/", allow_redirects=False)
    assert response.status_code == 200
    assert_no_redirect(response)

    html = response.text
    assert 'id="loginForm"' in html
    assert 'id="registerForm" hidden' in html
    assert 'id="dashboard" hidden' in html
    assert ">登录<" in html
    assert ">注册<" in html


@allure.epic("Occupancy System")
@allure.feature("UI Shell")
@pytest.mark.api
@pytest.mark.regression
def test_ui_shell_contains_split_registration_modes(fresh_client):
    response = fresh_client.get("/ui/")
    assert response.status_code == 200

    html = response.text
    assert "注册普通用户" in html
    assert "注册管理员" in html
    assert "管理员注册码" in html
