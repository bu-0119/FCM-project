from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.teams import router as teams_router
from app.api.v1.content import router as content_router
from app.api.v1.agent import router as agent_router
from app.api.v1.social import router as social_router
from app.api.v1.notifications import router as notifications_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(users_router)
router.include_router(teams_router)
router.include_router(content_router)
router.include_router(agent_router)
router.include_router(social_router)
router.include_router(notifications_router)
