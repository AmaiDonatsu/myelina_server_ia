from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    role: MessageRole = Field(..., description="Rol del emisor del mensaje (system, user, assistant)")
    content: str = Field(..., description="Contenido del mensaje de texto")


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(
        ...,
        min_length=1,
        description="Historial de conversación con la IA",
        json_schema_extra={
            "example": [
                {"role": "system", "content": "Eres un asistente de IA experto y conciso."},
                {"role": "user", "content": "¿Qué es la mielina en neurociencia?"}
            ]
        }
    )
    model: Optional[str] = Field(
        default=None,
        description="Nombre del modelo a utilizar. Si es omitido, usa el modelo predeterminado configurado (llama3.1:8b)"
    )
    temperature: Optional[float] = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Temperatura de muestreo para controlar la creatividad de la respuesta"
    )
    top_p: Optional[float] = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Top-p (nucleus sampling)"
    )
    stream: Optional[bool] = Field(
        default=False,
        description="Si es True, transmite la respuesta en tiempo real (Server-Sent Events / SSE)"
    )


class GenerateRequest(BaseModel):
    prompt: str = Field(..., description="Prompt o instrucción individual a procesar")
    system: Optional[str] = Field(default=None, description="Instrucción de sistema opcional")
    model: Optional[str] = Field(default=None, description="Nombre del modelo")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    stream: Optional[bool] = Field(default=False)


class ChatResponse(BaseModel):
    model: str
    message: ChatMessage
    done: bool = True
    total_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None


class GenerateResponse(BaseModel):
    model: str
    response: str
    done: bool = True
    total_duration: Optional[int] = None


class ModelInfo(BaseModel):
    name: str
    model: str
    size: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


class ModelsListResponse(BaseModel):
    models: List[ModelInfo]
