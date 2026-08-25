import os
from typing import List, Dict, Any, Optional
import httpx


class MyelinaServerClient:
    """Cliente HTTP ligero para interactuar con la API de Myelina Server IA."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 120.0,
    ):
        self.base_url = (base_url or os.getenv("MYELINA_SERVER_URL", "http://localhost:8000/api/v1")).rstrip("/")
        self.api_key = api_key or os.getenv("MYELINA_API_KEY")
        self.timeout = timeout

    @property
    def auth_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key.strip()}"
        return headers

    def login(self, username: str, password: str) -> str:
        """Inicia sesión con credenciales para obtener un JWT temporal."""
        url = f"{self.base_url}/auth/login/json"
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, json={"username": username, "password": password})
            if response.status_code != 200:
                detail = response.json().get("detail", response.text) if response.headers.get("content-type", "").startswith("application/json") else response.text
                raise RuntimeError(f"Fallo en login ({response.status_code}): {detail}")
            data = response.json()
            self.api_key = data["access_token"]
            return self.api_key

    def create_api_key(self, label: str, expires_in_days: Optional[int] = None) -> Dict[str, Any]:
        """Crea una API Key persistente (myelina_...) para el usuario."""
        url = f"{self.base_url}/auth/tokens"
        payload = {"label": label, "expires_in_days": expires_in_days}
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, json=payload, headers=self.auth_headers)
            if response.status_code != 201:
                detail = response.json().get("detail", response.text)
                raise RuntimeError(f"Error creando API Key ({response.status_code}): {detail}")
            data = response.json()
            self.api_key = data["token"]
            return data

    def check_status(self) -> Dict[str, Any]:
        """Verifica la conectividad con el backend y el servidor de inferencia."""
        url = f"{self.base_url}/inference/status"
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, headers=self.auth_headers)
            if response.status_code == 200:
                return response.json()
            return {"status": "error", "status_code": response.status_code, "detail": response.text}

    def list_models(self) -> List[Dict[str, Any]]:
        """Lista los modelos de IA disponibles."""
        url = f"{self.base_url}/inference/models"
        with httpx.Client(timeout=self.timeout) as client:
            response = client.get(url, headers=self.auth_headers)
            if response.status_code == 200:
                return response.json().get("models", [])
            return []

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
    ) -> Dict[str, Any]:
        """Envía el historial de mensajes al endpoint de chat de inferencia."""
        if not self.api_key:
            raise ValueError("No hay un token o API Key configurado en el cliente.")

        url = f"{self.base_url}/inference/chat"
        payload = {
            "messages": messages,
            "temperature": temperature,
            "stream": False,
        }
        if model:
            payload["model"] = model

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(url, json=payload, headers=self.auth_headers)
            if response.status_code != 200:
                error_detail = response.text
                try:
                    error_detail = response.json().get("detail", response.text)
                except Exception:
                    pass
                raise RuntimeError(f"Error en inferencia ({response.status_code}): {error_detail}")
            return response.json()
