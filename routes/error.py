from pathlib import Path
from fastapi import APIRouter, FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

router = APIRouter(tags=["Error Handling"])

TEMPLATES_PATH = Path(__file__).resolve().parent.parent / "template"
NOT_FOUND_TEMPLATE = TEMPLATES_PATH / "404.html"


def render_404_html(path: str = "") -> str:
    """Lee y procesa la plantilla HTML para el error 404."""
    if NOT_FOUND_TEMPLATE.exists():
        content = NOT_FOUND_TEMPLATE.read_text(encoding="utf-8")
        return content.replace("{{ path }}", path)
    return f"<!DOCTYPE html><html><body><h1>404 - Not Found</h1><p>Ruta: {path}</p></body></html>"


@router.get(
    "/404",
    response_class=HTMLResponse,
    summary="Vista de prueba 404 Not Found",
    description="Renderiza directamente la plantilla HTML 404 personalizada.",
)
def get_404_page(request: Request):
    html_content = render_404_html(path=request.url.path)
    return HTMLResponse(content=html_content, status_code=status.HTTP_404_NOT_FOUND)


async def not_found_exception_handler(request: Request, exc: Exception):
    """
    Manejador global de errores 404 para FastAPI.
    - Si la petición proviene de una API (comienza con /api/ o cabecera 'Accept: application/json'),
      retorna una respuesta JSON estructurada.
    - Si la petición proviene de un navegador web, retorna la interfaz HTML 404 estilizada.
    """
    path = request.url.path
    accept_header = request.headers.get("accept", "")

    # Determinar si la petición espera JSON
    is_api_request = path.startswith("/api/") or "application/json" in accept_header

    if is_api_request:
        detail = getattr(exc, "detail", "Recurso no encontrado")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": detail, "path": path},
        )

    html_content = render_404_html(path=path)
    return HTMLResponse(content=html_content, status_code=status.HTTP_404_NOT_FOUND)


async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Maneja excepciones HTTP de Starlette/FastAPI."""
    if exc.status_code == status.HTTP_404_NOT_FOUND:
        return await not_found_exception_handler(request, exc)

    headers = getattr(exc, "headers", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers,
    )


def register_error_handlers(app: FastAPI) -> None:
    """Registra los manejadores de excepciones en la instancia de FastAPI."""
    app.add_exception_handler(404, not_found_exception_handler)
    app.add_exception_handler(StarletteHTTPException, custom_http_exception_handler)