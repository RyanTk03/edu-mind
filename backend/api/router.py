from fastapi import APIRouter
from routes.auth        import router as auth_router
from routes.users       import router as users_router
from routes.sessions    import router as sessions_router
from routes.attachments import router as attachments_router
from routes.messages    import router as messages_router
from routes.exercises   import router as exercises_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(sessions_router)
api_router.include_router(attachments_router)
api_router.include_router(messages_router)
api_router.include_router(exercises_router)
