from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import get_current_admin
from core.config import settings
from models.user import User
from models.config import SystemConfig
from schemas.config import ConfigResponse
from services.inference import inference_service

router = APIRouter(tags=["Configuración"])


@router.get(
    "/config",
    summary="Obtener configuraciones del servidor (Solo Administradores)",
    description="Retorna la configuración actual en tiempo de ejecución del servidor.",
)
def get_system_config(
    _admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    configs = db.query(SystemConfig).all()
    saved_config = {c.key: c.value for c in configs}

    return {
        "runpod_port": saved_config.get("runpod_port", inference_service.get_base_url()),
        "ai_inference_url": inference_service.get_base_url(),
        "default_ai_model": saved_config.get("default_ai_model", settings.DEFAULT_AI_MODEL),
        "ai_request_timeout": float(saved_config.get("ai_request_timeout", settings.AI_REQUEST_TIMEOUT)),
        "all_settings": saved_config,
    }


@router.post(
    "/config",
    response_model=ConfigResponse,
    summary="Actualizar configuraciones del servidor (Solo Administradores)",
    description=(
        "Permite a usuarios administradores modificar dinámicamente parámetros del servidor. "
        "Por ejemplo: {'runpod_port': 'https://04tenxdnwyyxfp-11434.proxy.runpod.net'} "
        "para cambiar la URL del servidor de inferencia sin necesidad de reiniciar ni editar el archivo .env."
    ),
)
async def update_system_config(
    request: Request,
    _admin_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    try:
        body_dict = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cuerpo de la petición JSON no válido",
        )

    if not isinstance(body_dict, dict) or not body_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes proporcionar al menos una configuración a actualizar.",
        )

    updated_keys = []

    for key, value in body_dict.items():
        if value is None:
            continue
        val_str = str(value).strip()

        # Guardar / actualizar en base de datos
        db_cfg = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if not db_cfg:
            db_cfg = SystemConfig(key=key, value=val_str)
            db.add(db_cfg)
        else:
            db_cfg.value = val_str

        # Manejo de URL de inferencia / runpod_port
        if key in ("runpod_port", "ai_inference_url", "AI_INFERENCE_URL", "inference_url"):
            clean_url = val_str.rstrip("/")
            inference_service.set_base_url(clean_url)
            # Asegurar que esté guardado también bajo la clave estándar 'runpod_port'
            if key != "runpod_port":
                rp_cfg = db.query(SystemConfig).filter(SystemConfig.key == "runpod_port").first()
                if not rp_cfg:
                    rp_cfg = SystemConfig(key="runpod_port", value=clean_url)
                    db.add(rp_cfg)
                else:
                    rp_cfg.value = clean_url

        elif key in ("default_ai_model", "DEFAULT_AI_MODEL", "model"):
            settings.DEFAULT_AI_MODEL = val_str

        elif key in ("ai_request_timeout", "AI_REQUEST_TIMEOUT", "timeout"):
            try:
                timeout_val = float(val_str)
                settings.AI_REQUEST_TIMEOUT = timeout_val
                inference_service.timeout = timeout_val
            except ValueError:
                pass

        updated_keys.append(key)

    db.commit()

    return ConfigResponse(
        status="success",
        message=f"Configuración actualizada con éxito: {', '.join(updated_keys)}",
        current_config={
            "runpod_port": inference_service.get_base_url(),
            "ai_inference_url": inference_service.get_base_url(),
            "default_ai_model": settings.DEFAULT_AI_MODEL,
            "ai_request_timeout": settings.AI_REQUEST_TIMEOUT,
        },
    )
