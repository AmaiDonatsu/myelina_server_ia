import pytest
from core.config import settings


def test_debug_settings_endpoint_when_debug_true(client):
    settings.DEBUG = True
    response = client.get("/debug_settings")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Myelina Server IA" in response.text
    assert "DEBUG Role Selection" in response.text


def test_debug_settings_endpoint_when_debug_false(client):
    settings.DEBUG = False
    response = client.get("/debug_settings")
    assert response.status_code == 404
    # Reset debug mode
    settings.DEBUG = True


def test_register_role_in_debug_mode(client):
    # When DEBUG is True, user can register as admin
    settings.DEBUG = True
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "superadmin",
            "email": "superadmin@example.com",
            "password": "password123",
            "role": "admin",
        },
    )
    assert response.status_code == 201
    assert response.json()["role"] == "admin"


def test_register_role_in_non_debug_mode(client):
    # When DEBUG is False, requesting admin role defaults back to user
    settings.DEBUG = False
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "wannabe_admin",
            "email": "wannabe@example.com",
            "password": "password123",
            "role": "admin",
        },
    )
    assert response.status_code == 201
    assert response.json()["role"] == "user"
    # Reset debug mode
    settings.DEBUG = True
