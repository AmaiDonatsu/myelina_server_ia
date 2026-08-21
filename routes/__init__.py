from fastapi import APIRouter
from routes.auth import router as auth_router
from routes.debug import router as debug_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(debug_router)

__all__ = ["api_router", "auth_router", "debug_router"]
