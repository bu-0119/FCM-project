from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models import User, Team
from app.api.v1.deps import get_current_user_id
from app.api.v1.schemas import BaseSchema

router = APIRouter(prefix="/users", tags=["users"])


class UserProfileResponse(BaseSchema):
    id: str
    nickname: str | None
    avatar_url: str | None
    selected_teams: list
    preference_tags: list
    notify_settings: dict


class UpdateProfileRequest(BaseModel):
    nickname: str | None = None
    avatar_url: str | None = None


class UpdateTeamsRequest(BaseModel):
    team_ids: list[int]


async def _get_user(db: AsyncSession, user_id: str) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    return await _get_user(db, user_id)


@router.put("/me", response_model=UserProfileResponse)
async def update_profile(
    req: UpdateProfileRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(db, user_id)
    if req.nickname is not None:
        user.nickname = req.nickname
    if req.avatar_url is not None:
        user.avatar_url = req.avatar_url
    await db.flush()
    return user


@router.get("/me/teams", response_model=list[dict])
async def get_my_teams(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(db, user_id)
    if not user.selected_teams:
        return []
    result = await db.execute(
        select(Team).where(Team.id.in_(user.selected_teams))
    )
    teams = result.scalars().all()
    return [
        {"id": t.id, "name": t.name, "name_en": t.name_en, "crest_url": t.crest_url}
        for t in teams
    ]


@router.put("/me/teams", response_model=UserProfileResponse)
async def update_teams(
    req: UpdateTeamsRequest,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    if len(req.team_ids) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 teams allowed")
    if len(req.team_ids) != len(set(req.team_ids)):
        raise HTTPException(status_code=400, detail="Duplicate teams not allowed")

    user = await _get_user(db, user_id)
    user.selected_teams = req.team_ids
    user.team_change_date = date.today()
    await db.flush()
    return user
