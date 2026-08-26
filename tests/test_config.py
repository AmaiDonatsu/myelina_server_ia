import pytest
from services.inference import inference_service


@pytest.fixture
def admin_token(client):
    # Register an admin user (DEBUG=True permits role selection)
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "superadmin",
            "email": "admin@myelina.ai",
            "password": "adminpassword123",
            "role": "admin",
        },
    )
    res = client.post(
        "/api/v1/auth/login",
        data={"username": "superadmin", "password": "adminpassword123"},
    )
    return res.json()["access_token"]


@pytest.fixture
def user_token(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "regular_user",
            "email": "user@myelina.ai",
            "password": "userpassword123",
            "role": "user",
        },
    )
    res = client.post(
        "/api/v1/auth/login",
        data={"username": "regular_user", "password": "userpassword123"},
    )
    return res.json()["access_token"]


def test_config_requires_admin_authentication(client, user_token):
    # Unauthenticated -> 401
    res_unauth = client.get("/config")
    assert res_unauth.status_code == 401

    # Regular user -> 403
    res_user = client.get(
        "/config",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert res_user.status_code == 403
    assert "Permisos insuficientes" in res_user.json()["detail"]


def test_admin_get_and_update_config(client, admin_token):
    # 1. Admin GET /config
    res_get = client.get(
        "/config",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_get.status_code == 200
    assert "runpod_port" in res_get.json()
    assert "ai_inference_url" in res_get.json()

    # 2. Admin POST /config to change runpod_port
    new_url = "https://04tenxdnwyyxfp-11434.proxy.runpod.net"
    res_post = client.post(
        "/config",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"runpod_port": new_url},
    )
    assert res_post.status_code == 200
    data = res_post.json()
    assert data["status"] == "success"
    assert data["current_config"]["runpod_port"] == new_url

    # Verify that the inference service in memory updated its base URL
    assert inference_service.get_base_url() == new_url

    # 3. GET /config returns the newly set runpod_port
    res_get_updated = client.get(
        "/config",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_get_updated.status_code == 200
    assert res_get_updated.json()["runpod_port"] == new_url


def test_config_via_api_v1_path(client, admin_token):
    # Verify /api/v1/config also works seamlessly
    new_url = "https://my-custom-runpod.proxy.runpod.net"
    res_post = client.post(
        "/api/v1/config",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"runpod_port": new_url},
    )
    assert res_post.status_code == 200
    assert res_post.json()["current_config"]["runpod_port"] == new_url
    assert inference_service.get_base_url() == new_url
