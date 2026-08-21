import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from core.database import Base, get_db
from models.user import User, UserRole

# In-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


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

    # 2. Register admin user
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
