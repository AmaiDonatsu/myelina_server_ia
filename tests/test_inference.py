from unittest.mock import patch, AsyncMock
import pytest
from schemas.inference import ChatResponse, ChatMessage, MessageRole, GenerateResponse


@pytest.fixture
def auth_token(client):
    # Register and login a user to get bearer token
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "ai_tester",
            "email": "tester@myelina.ai",
            "password": "password123",
            "role": "user",
        },
    )
    res = client.post(
        "/api/v1/auth/login",
        data={"username": "ai_tester", "password": "password123"},
    )
    return res.json()["access_token"]


def test_inference_endpoints_require_authentication(client):
    # Chat requires auth
    res = client.post(
        "/api/v1/inference/chat",
        json={"messages": [{"role": "user", "content": "Hola"}]},
    )
    assert res.status_code == 401

    # Models requires auth
    res = client.get("/api/v1/inference/models")
    assert res.status_code == 401

    # Status requires auth
    res = client.get("/api/v1/inference/status")
    assert res.status_code == 401


def test_inference_status_with_auth(client, auth_token):
    with patch("services.inference.inference_service.check_health", new_callable=AsyncMock) as mock_health:
        mock_health.return_value = {
            "status": "connected",
            "service": "ollama",
            "endpoint": "https://iapx06g61diaeb-11434.proxy.runpod.net",
        }
        res = client.get(
            "/api/v1/inference/status",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert res.status_code == 200
        assert res.json()["status"] == "connected"


def test_inference_models_with_auth(client, auth_token):
    with patch("services.inference.inference_service.list_models", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = [
            {"name": "llama3.1:8b", "model": "llama3.1:8b", "size": 4920753328}
        ]
        res = client.get(
            "/api/v1/inference/models",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert res.status_code == 200
        assert len(res.json()["models"]) == 1
        assert res.json()["models"][0]["name"] == "llama3.1:8b"


def test_inference_chat_with_auth(client, auth_token):
    with patch("services.inference.inference_service.chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = ChatResponse(
            model="llama3.1:8b",
            message=ChatMessage(role=MessageRole.ASSISTANT, content="Hola, soy Myelina IA."),
            done=True,
        )
        res = client.post(
            "/api/v1/inference/chat",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "messages": [
                    {"role": "user", "content": "Hola mundo"}
                ]
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["model"] == "llama3.1:8b"
        assert data["message"]["content"] == "Hola, soy Myelina IA."


def test_inference_generate_with_auth(client, auth_token):
    with patch("services.inference.inference_service.generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = GenerateResponse(
            model="llama3.1:8b",
            response="Respuesta generada",
            done=True,
        )
        res = client.post(
            "/api/v1/inference/generate",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"prompt": "Explica la fotosintesis"},
        )
        assert res.status_code == 200
        assert res.json()["response"] == "Respuesta generada"
