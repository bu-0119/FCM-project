from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.database import get_db
from app.models import Team, League

router = APIRouter(prefix="/teams", tags=["teams"])


class TeamResponse(BaseModel):
    id: int
    name: str
    name_en: str | None
    crest_url: str | None
    league_id: int | None
    league_name: str | None
    keywords: list

    model_config = {"from_attributes": True}


@router.get("", response_model=list[TeamResponse])
async def list_teams(db: AsyncSession = Depends(get_db)):
    # Join with league to get league name
    result = await db.execute(
        select(Team, League.name.label("league_name"))
        .outerjoin(League, Team.league_id == League.id)
        .order_by(League.id, Team.id)
    )
    rows = result.all()

    teams = []
    for team, league_name in rows:
        team_dict = {
            "id": team.id,
            "name": team.name,
            "name_en": team.name_en,
            "crest_url": team.crest_url,
            "league_id": team.league_id,
            "league_name": league_name,
            "keywords": team.keywords,
        }
        teams.append(team_dict)
    return teams


@router.get("/{team_id}")
async def get_team(team_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Team, League.name.label("league_name"))
        .outerjoin(League, Team.league_id == League.id)
        .where(Team.id == team_id)
    )
    row = result.one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Team not found")
    team, league_name = row
    return {
        "id": team.id,
        "name": team.name,
        "name_en": team.name_en,
        "crest_url": team.crest_url,
        "league_id": team.league_id,
        "league_name": league_name,
        "keywords": team.keywords,
    }
