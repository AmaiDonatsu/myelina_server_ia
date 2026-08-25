from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class UserTokenCreate(BaseModel):
    label: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Etiqueta identificadora del token (ej. 'mi_token', 'postman_dev', 'frontend')",
        json_schema_extra={"example": "mi_token"}
    )
    expires_in_days: Optional[int] = Field(
        default=None,
        ge=1,
        description="Días de validez del token antes de expirar (opcional, por defecto sin expiración)"
    )
    scopes: Optional[str] = Field(
        default="all",
        description="Alcance o permisos permitidos para el token (ej. 'all', 'inference:read', 'inference:write')"
    )


class UserTokenCreatedResponse(BaseModel):
    id: int
    label: str
    token: str = Field(..., description="Token de API generado en texto plano. Se muestra UNA SOLA VEZ.")
    prefix: str = Field(..., description="Prefijo del token para identificación segura")
    scopes: str
    revoked: bool
    created_at: datetime
    expires_at: Optional[datetime] = None
    message: str = Field(
        default="Token generado con éxito. Cópialo y guárdalo en un lugar seguro; no podrás volver a verlo.",
        description="Aviso de seguridad para el usuario"
    )

    model_config = ConfigDict(from_attributes=True)


class UserTokenInfoResponse(BaseModel):
    id: int
    label: str
    prefix: str
    scopes: str
    revoked: bool
    created_at: datetime
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
