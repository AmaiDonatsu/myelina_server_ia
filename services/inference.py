import json
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, Any, List, Optional
import httpx
from fastapi import HTTPException, status

from core.config import settings
from schemas.inference import ChatRequest, GenerateRequest, ChatResponse, GenerateResponse, ChatMessage, MessageRole


class InferenceService:
    def __init__(self, base_url: str = settings.AI_INFERENCE_URL, timeout: float = settings.AI_REQUEST_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def set_base_url(self, new_url: str) -> None:
        """Actualiza dinámicamente la URL base de inferencia."""
        self.base_url = new_url.rstrip("/")
        settings.AI_INFERENCE_URL = self.base_url

    def get_base_url(self) -> str:
        """Retorna la URL base actual."""
        return self.base_url

    def load_from_db(self, db_session: Optional[Any] = None) -> None:
        """Carga las configuraciones guardadas en la base de datos si existen."""
        try:
            from core.database import SessionLocal
            from models.config import SystemConfig
            session = db_session or SessionLocal()
            try:
                cfg = session.query(SystemConfig).filter(
                    SystemConfig.key.in_(["runpod_port", "ai_inference_url", "AI_INFERENCE_URL", "inference_url"])
                ).first()
                if cfg and cfg.value:
                    self.set_base_url(cfg.value)

                model_cfg = session.query(SystemConfig).filter(
                    SystemConfig.key.in_(["default_ai_model", "DEFAULT_AI_MODEL", "model"])
                ).first()
                if model_cfg and model_cfg.value:
                    settings.DEFAULT_AI_MODEL = model_cfg.value

                timeout_cfg = session.query(SystemConfig).filter(
                    SystemConfig.key.in_(["ai_request_timeout", "AI_REQUEST_TIMEOUT", "timeout"])
                ).first()
                if timeout_cfg and timeout_cfg.value:
                    self.timeout = float(timeout_cfg.value)
                    settings.AI_REQUEST_TIMEOUT = self.timeout
            finally:
                if not db_session:
                    session.close()
        except Exception:
            pass

    async def check_health(self) -> Dict[str, Any]:
        """Verifica la conectividad con la instancia de Ollama en RunPod."""
        url = f"{self.base_url}/"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return {
                        "status": "connected",
                        "service": "ollama",
                        "endpoint": self.base_url,
                        "message": response.text.strip(),
                    }
                return {
                    "status": "unhealthy",
                    "status_code": response.status_code,
                    "endpoint": self.base_url,
                }
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"No se pudo conectar con el servidor de inferencia en RunPod ({self.base_url}): {str(exc)}",
            )

    async def list_models(self) -> List[Dict[str, Any]]:
        """Obtiene la lista de modelos disponibles en el servidor de inferencia."""
        url = f"{self.base_url}/api/tags"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Error al obtener modelos desde el servidor de inferencia: {response.text}",
                    )
                data = response.json()
                return data.get("models", [])
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Error de conexión con el servidor de inferencia: {str(exc)}",
            )

    @staticmethod
    def _normalize_role(role: Any) -> str:
        role_str = role.value if hasattr(role, "value") else str(role)
        role_lower = role_str.lower()
        if role_lower in ("agent", "model", "asistente", "assistant"):
            return "assistant"
        if role_lower in ("usuario", "user"):
            return "user"
        if role_lower in ("sistema", "system"):
            return "system"
        return role_lower

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Envía un historial de conversación al modelo y retorna la respuesta generada."""
        url = f"{self.base_url}/api/chat"
        model_name = request.model or settings.DEFAULT_AI_MODEL

        messages_payload = []
        for m in request.messages:
            msg_dict: Dict[str, Any] = {
                "role": self._normalize_role(m.role),
                "content": m.content,
            }
            if m.images:
                msg_dict["images"] = m.images
            messages_payload.append(msg_dict)

        payload = {
            "model": model_name,
            "messages": messages_payload,
            "stream": False,
            "options": {
                "temperature": request.temperature,
                "top_p": request.top_p,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Error del modelo de IA: {response.text}",
                    )
                data = response.json()
                msg = data.get("message", {})
                msg_content = msg.get("content", "")
                created_at_val = data.get("created_at") or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

                return ChatResponse(
                    model=data.get("model", model_name),
                    content=msg_content,
                    date=str(created_at_val),
                    message=ChatMessage(
                        role=MessageRole(self._normalize_role(msg.get("role", "assistant"))),
                        content=msg_content,
                    ),
                    done=data.get("done", True),
                    total_duration=data.get("total_duration"),
                    prompt_eval_count=data.get("prompt_eval_count"),
                    eval_count=data.get("eval_count"),
                )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Tiempo de espera agotado ({self.timeout}s) esperando respuesta del modelo {model_name}.",
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Error de conexión con el servidor de inferencia: {str(exc)}",
            )

    async def chat_stream(self, request: ChatRequest) -> AsyncGenerator[str, None]:
        """Transmite la respuesta del modelo en tiempo real token por token (SSE)."""
        url = f"{self.base_url}/api/chat"
        model_name = request.model or settings.DEFAULT_AI_MODEL

        messages_payload = []
        for m in request.messages:
            msg_dict: Dict[str, Any] = {
                "role": self._normalize_role(m.role),
                "content": m.content,
            }
            if m.images:
                msg_dict["images"] = m.images
            messages_payload.append(msg_dict)

        payload = {
            "model": model_name,
            "messages": messages_payload,
            "stream": True,
            "options": {
                "temperature": request.temperature,
                "top_p": request.top_p,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        yield f"data: {json.dumps({'error': f'Error del modelo: {error_text.decode()}'})}\n\n"
                        return

                    async for line in response.aiter_lines():
                        if line:
                            yield f"data: {line}\n\n"
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        """Genera una respuesta a partir de un prompt simple (admite imágenes en base64)."""
        url = f"{self.base_url}/api/generate"
        model_name = request.model or settings.DEFAULT_AI_MODEL

        payload = {
            "model": model_name,
            "prompt": request.prompt,
            "system": request.system,
            "stream": False,
            "options": {
                "temperature": request.temperature,
            },
        }
        if request.images:
            payload["images"] = request.images

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=response.status_code,
                        detail=f"Error del modelo de IA: {response.text}",
                    )
                data = response.json()
                resp_content = data.get("response", "")
                created_at_val = data.get("created_at") or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

                return GenerateResponse(
                    model=data.get("model", model_name),
                    content=resp_content,
                    response=resp_content,
                    date=str(created_at_val),
                    done=data.get("done", True),
                    total_duration=data.get("total_duration"),
                )
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Tiempo de espera agotado esperando la respuesta del modelo.",
            )
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Error de conexión con el servidor de inferencia: {str(exc)}",
            )


# Instancia única del servicio
inference_service = InferenceService()
