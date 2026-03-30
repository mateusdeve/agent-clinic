"""Auth endpoint tests — stubs filled by Plan 02 executor."""
import pytest


@pytest.mark.auth
@pytest.mark.xfail(reason="Plan 02 not yet executed")
def test_login_valid_credentials(test_client):
    """POST /auth/login with valid email+password returns 200 + tokens (AUTH-01, API-02)."""
    response = test_client.post("/auth/login", json={
        "email": "admin@clinica.com",
        "password": "admin123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["role"] == "admin"


@pytest.mark.auth
@pytest.mark.xfail(reason="Plan 02 not yet executed")
def test_login_invalid_credentials(test_client):
    """POST /auth/login with wrong password returns 401 (AUTH-01)."""
    response = test_client.post("/auth/login", json={
        "email": "admin@clinica.com",
        "password": "wrongpassword",
    })
    assert response.status_code == 401


@pytest.mark.auth
@pytest.mark.xfail(reason="Plan 02 not yet executed")
def test_refresh_token(test_client):
    """POST /auth/refresh with valid refresh token returns new access_token (AUTH-04)."""
    # First login to get refresh token
    login_resp = test_client.post("/auth/login", json={
        "email": "admin@clinica.com",
        "password": "admin123",
    })
    refresh_token = login_resp.json().get("refresh_token", "")
    response = test_client.post("/auth/refresh", json={
        "refresh_token": refresh_token,
    })
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.auth
@pytest.mark.xfail(reason="Plan 02 not yet executed")
def test_me_endpoint(test_client):
    """GET /auth/me with valid Bearer token returns user info."""
    login_resp = test_client.post("/auth/login", json={
        "email": "admin@clinica.com",
        "password": "admin123",
    })
    token = login_resp.json().get("access_token", "")
    response = test_client.get("/auth/me", headers={
        "Authorization": f"Bearer {token}",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "admin@clinica.com"
    assert data["role"] == "admin"
