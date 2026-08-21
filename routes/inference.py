from typing import Union
from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from core.security import get_current_user
from models.user import User
from schemas.inference import (
    ChatRequest,
    ChatResponse,
    GenerateRequest,
    GenerateResponse,
    ModelsListResponse,
)
from services.inference import inference_service

router = APIRouter(prefix="/inference", tags=["Inferencia IA"])


@router.get(
    "/status",
    summary="Estado del servidor de inferencia RunPod",
    description="Verifica la conectividad directa con la instancia de Ollama alojada en RunPod.",
)
async def check_inference_status(
    _current_user: User = Depends(get_current_user),
):
    return await inference_service.check_health()


@router.get(
    "/models",
    response_model=ModelsListResponse,
    summary="Listar modelos disponibles",
    description="Obtiene los modelos y pesos de IA cargados actualmente en el servidor de RunPod.",
)
async def list_available_models(
    _current_user: User = Depends(get_current_user),
):
    models = await inference_service.list_models()
    return {"models": models}


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Generar respuesta de conversación (Chat)",
    description="Recibe un historial de conversación completo y devuelve la respuesta del modelo. Soporta streaming si se especifica stream=True.",
)
async def chat_completion(
    request: ChatRequest,
    _current_user: User = Depends(get_current_user),
) -> Union[ChatResponse, StreamingResponse]:
    if request.stream:
        return StreamingResponse(
            inference_service.chat_stream(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    return await inference_service.chat(request)


@router.post(
    "/generate",
    response_model=GenerateResponse,
    summary="Generación simple de texto (Prompt)",
    description="Envía un prompt o instrucción directa al modelo y retorna el texto generado.",
)
async def generate_completion(
    request: GenerateRequest,
    _current_user: User = Depends(get_current_user),
):
    return await inference_service.generate(request)
