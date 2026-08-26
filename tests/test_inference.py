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
            content="Hola, soy Myelina IA.",
            date="2026-08-22 04:45:00 UTC",
            message=ChatMessage(role=MessageRole.ASSISTANT, content="Hola, soy Myelina IA."),
            done=True,
        )
        res = client.post(
            "/api/v1/inference/chat",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "messages": [
                    {"role": "sistema", "content": "Eres un asistente amigable."},
                    {"role": "usuario", "content": "Hola, ¿cómo te llamas?"},
                    {"role": "asistente", "content": "Me llamo Myelina IA."},
                    {"role": "user", "content": "¿Qué puedes hacer?"},
                    {"role": "agent", "content": "Puedo razonar y responder preguntas."}
                ]
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["model"] == "llama3.1:8b"
        assert data["content"] == "Hola, soy Myelina IA."
        assert data["date"] == "2026-08-22 04:45:00 UTC"
        assert data["message"]["content"] == "Hola, soy Myelina IA."


def test_inference_generate_with_auth(client, auth_token):
    with patch("services.inference.inference_service.generate", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = GenerateResponse(
            model="llama3.1:8b",
            content="Respuesta generada",
            response="Respuesta generada",
            date="2026-08-22 04:45:00 UTC",
            done=True,
        )
        res = client.post(
            "/api/v1/inference/generate",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"prompt": "Explica la fotosintesis"},
        )
        assert res.status_code == 200
        assert res.json()["content"] == "Respuesta generada"
        assert res.json()["response"] == "Respuesta generada"
        assert "date" in res.json()


def test_inference_chat_with_api_key(client, auth_token):
    # 1. Create a user token using the JWT auth_token
    token_res = client.post(
        "/api/v1/auth/tokens",
        headers={"Authorization": f"Bearer {auth_token}"},
        json={"label": "bot_client_token"},
    )
    assert token_res.status_code == 201
    api_key = token_res.json()["token"]

    # 2. Call /api/v1/inference/chat using the generated API Key directly
    with patch("services.inference.inference_service.chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = ChatResponse(
            model="llama3.1:8b",
            content="Respuesta autenticada con API key.",
            date="2026-08-22 04:45:00 UTC",
            message=ChatMessage(role=MessageRole.ASSISTANT, content="Respuesta autenticada con API key."),
            done=True,
        )
        res = client.post(
            "/api/v1/inference/chat",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "messages": [
                    {"role": "user", "content": "Probando API Key"}
                ]
            },
        )
        assert res.status_code == 200
        assert res.json()["content"] == "Respuesta autenticada con API key."


def test_inference_chat_with_images(client, auth_token):
    sample_base64_img = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="
    with patch("services.inference.inference_service.chat", new_callable=AsyncMock) as mock_chat:
        mock_chat.return_value = ChatResponse(
            model="llava:7b",
            content="En la imagen se observa un punto blanco.",
            date="2026-08-26 00:30:00 UTC",
            message=ChatMessage(
                role=MessageRole.ASSISTANT,
                content="En la imagen se observa un punto blanco.",
            ),
            done=True,
        )
        res = client.post(
            "/api/v1/inference/chat",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "model": "llava:7b",
                "messages": [
                    {
                        "role": "user",
                        "content": "¿Qué hay en esta imagen?",
                        "images": [sample_base64_img],
                    }
                ],
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["model"] == "llava:7b"
        assert "punto blanco" in data["content"]
