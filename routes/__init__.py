from fastapi import APIRouter
from routes.auth import router as auth_router
from routes.debug import router as debug_router
from routes.error import router as error_router, register_error_handlers
from routes.inference import router as inference_router
from routes.config import router as config_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(debug_router)
api_router.include_router(inference_router)
api_router.include_router(config_router)

__all__ = [
    "api_router",
    "auth_router",
    "debug_router",
    "error_router",
    "register_error_handlers",
    "inference_router",
    "config_router",
]
