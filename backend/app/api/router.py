"""Main API router aggregator."""

from fastapi import APIRouter

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.sessions import router as sessions_router
from app.api.attachments import router as attachments_router
from app.api.messages import router as messages_router
from app.api.exercises import router as exercises_router
from app.api.qcm import router as qcm_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(sessions_router)
api_router.include_router(attachments_router)
api_router.include_router(messages_router)
api_router.include_router(exercises_router)
api_router.include_router(qcm_router)
