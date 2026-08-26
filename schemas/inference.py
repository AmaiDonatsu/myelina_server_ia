from enum import Enum
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    AGENT = "agent"
    MODEL = "model"
    # Alias en español para máxima compatibilidad
    USUARIO = "usuario"
    ASISTENTE = "asistente"
    SISTEMA = "sistema"


class ChatMessage(BaseModel):
    role: MessageRole = Field(..., description="Rol del emisor del mensaje (system, user, assistant, usuario, etc.)")
    content: str = Field(..., description="Contenido del mensaje de texto")
    images: Optional[List[str]] = Field(
        default=None,
        description="Lista opcional de imágenes codificadas en base64 para modelos multimodales/visión (ej. llava:7b, llama3.2-vision)",
        json_schema_extra={"example": ["iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="]}
    )


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(
        ...,
        min_length=1,
        description="Historial de conversación con la IA (admite texto e imágenes en base64 para modelos de visión)",
        json_schema_extra={
            "example": [
                {
                    "role": "user",
                    "content": "¿Qué hay en esta imagen?",
                    "images": ["<imagen_en_base64_aquí>"]
                }
            ]
        }
    )
    model: Optional[str] = Field(
        default=None,
        description="Nombre del modelo a utilizar (ej. llama3.1:8b, llava:7b). Si es omitido, usa el modelo predeterminado configurado"
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
    model: Optional[str] = Field(default=None, description="Nombre del modelo (ej. llama3.1:8b, llava:7b)")
    images: Optional[List[str]] = Field(default=None, description="Lista opcional de imágenes en base64")
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    stream: Optional[bool] = Field(default=False)


class ChatResponse(BaseModel):
    model: str = Field(..., description="Nombre del modelo que generó la respuesta")
    content: str = Field(..., description="Texto de la respuesta generada")
    date: str = Field(..., description="Fecha/hora de generación de la respuesta")
    message: ChatMessage = Field(..., description="Objeto del mensaje estructurado")
    done: bool = True
    total_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None


class GenerateResponse(BaseModel):
    model: str = Field(..., description="Nombre del modelo")
    content: str = Field(..., description="Texto generado")
    response: str = Field(..., description="Texto generado (compatibilidad Ollama)")
    date: str = Field(..., description="Fecha/hora de generación")
    done: bool = True
    total_duration: Optional[int] = None


class ModelInfo(BaseModel):
    name: str
    model: str
    size: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


class ModelsListResponse(BaseModel):
    models: List[ModelInfo]
