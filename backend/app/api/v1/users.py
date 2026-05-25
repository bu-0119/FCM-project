from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models import User, Team
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


class UserProfileResponse(BaseModel):
    id: str
    nickname: str | None
    avatar_url: str | None
    selected_teams: list[int]
    preference_tags: list[str]
    notify_settings: dict

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    nickname: str | None = None
    avatar_url: str | None = None


class UpdateTeamsRequest(BaseModel):
    team_ids: list[int]  # max 3


@router.get("/me", response_model=UserProfileResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserProfileResponse)
async def update_profile(
    req: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await db.merge(current_user)
    if req.nickname is not None:
        user.nickname = req.nickname
    if req.avatar_url is not None:
        user.avatar_url = req.avatar_url
    await db.flush()
    return user


@router.get("/me/teams", response_model=list[dict])
async def get_my_teams(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.selected_teams:
        return []
    result = await db.execute(
        select(Team).where(Team.id.in_(current_user.selected_teams))
    )
    teams = result.scalars().all()
    return [
        {"id": t.id, "name": t.name, "name_en": t.name_en, "crest_url": t.crest_url}
        for t in teams
    ]


@router.put("/me/teams", response_model=UserProfileResponse)
async def update_teams(
    req: UpdateTeamsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if len(req.team_ids) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 teams allowed")
    if len(req.team_ids) != len(set(req.team_ids)):
        raise HTTPException(status_code=400, detail="Duplicate teams not allowed")

    user = await db.merge(current_user)
    user.selected_teams = req.team_ids
    user.team_change_date = date.today()
    await db.flush()
    return user
