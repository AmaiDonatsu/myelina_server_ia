from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import HTMLResponse

from core.config import settings

router = APIRouter(tags=["Debug"])

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "template" / "debug_ui.html"


@router.get(
    "/debug_settings",
    response_class=HTMLResponse,
    summary="UI de Configuración y Autenticación en modo Debug",
    description="Retorna una interfaz gráfica web para registrarse (con selección de rol USER/ADMIN), iniciar sesión y probar endpoints. Solo accesible cuando DEBUG=True.",
)
def debug_settings_ui():
    if not settings.DEBUG:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Página no encontrada. El servidor no está en modo DEBUG.",
        )

    if not TEMPLATE_PATH.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La plantilla template/debug_ui.html no se encuentra.",
        )

    content = TEMPLATE_PATH.read_text(encoding="utf-8")
    return HTMLResponse(content=content, status_code=status.HTTP_200_OK)