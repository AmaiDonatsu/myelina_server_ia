import pytest


def test_root_and_health(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Bienvenido" in response.json()["message"]

    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_register_user(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "securepassword123",
            "role": "user",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "testuser@example.com"
    assert data["role"] == "user"
    assert data["is_active"] is True
    assert "id" in data


def test_register_duplicate_username(client):
    user_payload = {
        "username": "duplicate_user",
        "email": "first@example.com",
        "password": "securepassword123",
    }
    client.post("/api/v1/auth/register", json=user_payload)
    
    # Try registering again with same username
    user_payload_dup = {
        "username": "duplicate_user",
        "email": "second@example.com",
        "password": "securepassword123",
    }
    response = client.post("/api/v1/auth/register", json=user_payload_dup)
    assert response.status_code == 400
    assert "nombre de usuario ya se encuentra registrado" in response.json()["detail"]


def test_login_oauth2_form_and_get_me(client):
    # 1. Register user
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "johndoe",
            "email": "johndoe@example.com",
            "password": "mypassword123",
        },
    )

    # 2. Login via form data (OAuth2 standard)
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "johndoe", "password": "mypassword123"},
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    token = token_data["access_token"]

    # 3. Access protected route /me
    me_response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["username"] == "johndoe"
    assert me_data["email"] == "johndoe@example.com"
    assert me_data["role"] == "user"


def test_login_json(client):
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "alice",
            "email": "alice@example.com",
            "password": "passwordalice",
        },
    )

    # Login via JSON endpoint
    response = client.post(
        "/api/v1/auth/login/json",
        json={"username": "alice", "password": "passwordalice"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_role_based_access_control(client):
    # 1. Register normal user
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "normal_user",
            "email": "normal@example.com",
            "password": "password123",
            "role": "user",
        },
    )
    user_token = client.post(
        "/api/v1/auth/login",
        data={"username": "normal_user", "password": "password123"},
    ).json()["access_token"]

    # 2. Register admin user (with DEBUG=True)
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "admin_user",
            "email": "admin@example.com",
            "password": "adminpassword123",
            "role": "admin",
        },
    )
    admin_token = client.post(
        "/api/v1/auth/login",
        data={"username": "admin_user", "password": "adminpassword123"},
    ).json()["access_token"]

    # 3. Normal user attempts to access /admin/users -> 403 Forbidden
    resp_user = client.get(
        "/api/v1/auth/admin/users",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp_user.status_code == 403
    assert "Permisos insuficientes" in resp_user.json()["detail"]

    # 4. Admin user accesses /admin/users -> 200 OK
    resp_admin = client.get(
        "/api/v1/auth/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp_admin.status_code == 200
    users_list = resp_admin.json()
    assert len(users_list) == 2


def test_create_and_use_user_api_key(client):
    # 1. Register & login
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "token_master",
            "email": "master@myelina.ai",
            "password": "securepassword123",
        },
    )
    jwt_token = client.post(
        "/api/v1/auth/login",
        data={"username": "token_master", "password": "securepassword123"},
    ).json()["access_token"]

    # 2. Create an API Key with label "mi_token"
    res_create = client.post(
        "/api/v1/auth/tokens",
        headers={"Authorization": f"Bearer {jwt_token}"},
        json={"label": "mi_token"},
    )
    assert res_create.status_code == 201
    token_data = res_create.json()
    assert token_data["label"] == "mi_token"
    assert "token" in token_data
    raw_api_key = token_data["token"]
    assert raw_api_key.startswith("myelina_")
    token_id = token_data["id"]

    # 3. Disallow duplicate label for the same user
    res_duplicate = client.post(
        "/api/v1/auth/tokens",
        headers={"Authorization": f"Bearer {jwt_token}"},
        json={"label": "mi_token"},
    )
    assert res_duplicate.status_code == 400
    assert "Ya existe un token con la etiqueta" in res_duplicate.json()["detail"]

    # 4. Allow another token with a different label
    res_token2 = client.post(
        "/api/v1/auth/tokens",
        headers={"Authorization": f"Bearer {jwt_token}"},
        json={"label": "mi_segundo_token"},
    )
    assert res_token2.status_code == 201
    assert res_token2.json()["label"] == "mi_segundo_token"

    # 5. Access protected route (/me) directly with the raw API Key (NO JWT session needed)
    res_me = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {raw_api_key}"},
    )
    assert res_me.status_code == 200
    assert res_me.json()["username"] == "token_master"

    # 6. List user tokens (does not leak raw key)
    res_list = client.get(
        "/api/v1/auth/tokens",
        headers={"Authorization": f"Bearer {raw_api_key}"},
    )
    assert res_list.status_code == 200
    tokens = res_list.json()
    assert len(tokens) == 2
    for t in tokens:
        assert "token" not in t
        assert "prefix" in t

    # 7. Revoke token
    res_revoke = client.post(
        f"/api/v1/auth/tokens/{token_id}/revoke",
        headers={"Authorization": f"Bearer {jwt_token}"},
    )
    assert res_revoke.status_code == 200
    assert res_revoke.json()["revoked"] is True

    # 8. Access with revoked token should fail (401)
    res_me_revoked = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {raw_api_key}"},
    )
    assert res_me_revoked.status_code == 401
    assert "revocado" in res_me_revoked.json()["detail"]


def test_invalid_and_expired_api_keys(client):
    # Invalid key
    res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer myelina_invalidkey1234567890"},
    )
    assert res.status_code == 401
