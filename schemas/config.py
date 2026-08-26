from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class ConfigUpdateRequest(BaseModel):
    """
    Esquema de solicitud para actualizar configuraciones dinámicas del sistema.
    Permite enviar pares clave-valor como {"runpod_port": "https://..."}
    """
    runpod_port: Optional[str] = Field(
        default=None,
        description="URL o endpoint de RunPod / Ollama para inferencia de IA",
        json_schema_extra={"example": "https://04tenxdnwyyxfp-11434.proxy.runpod.net"}
    )
    default_ai_model: Optional[str] = Field(
        default=None,
        description="Modelo de IA predeterminado",
        json_schema_extra={"example": "llava:7b"}
    )
    ai_request_timeout: Optional[float] = Field(
        default=None,
        ge=5.0,
        le=600.0,
        description="Tiempo de espera en segundos para solicitudes de inferencia"
    )

    model_config = ConfigDict(extra="allow")


class ConfigResponse(BaseModel):
    status: str = "success"
    message: str
    current_config: Dict[str, Any]
