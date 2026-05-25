from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models import Content, ContentType

router = APIRouter(prefix="/content", tags=["content"])


class ContentResponse(BaseModel):
    id: str
    team_id: int
    content_type: str
    title: str
    summary: str | None
    source_url: str | None
    tags: list[str]
    published_at: str | None
    created_at: str

    model_config = {"from_attributes": True}


class FeedResponse(BaseModel):
    items: list[ContentResponse]
    total: int
    page: int
    size: int


@router.get("/feed", response_model=FeedResponse)
async def content_feed(
    team_id: int | None = Query(None),
    content_type: ContentType | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    conditions = []
    if team_id is not None:
        conditions.append(Content.team_id == team_id)
    if content_type is not None:
        conditions.append(Content.content_type == content_type)

    base_query = select(Content)
    if conditions:
        base_query = base_query.where(*conditions)

    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    items_query = (
        base_query.order_by(Content.published_at.desc().nullslast(), Content.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(items_query)
    items = result.scalars().all()

    return FeedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
    )


@router.get("/search", response_model=list[ContentResponse])
async def search_content(
    q: str = Query(..., min_length=1),
    team_id: int | None = Query(None),
    limit: int = Query(20, le=50),
    db: AsyncSession = Depends(get_db),
):
    conditions = [
        (Content.title.ilike(f"%{q}%")) | (Content.summary.ilike(f"%{q}%"))
    ]
    if team_id is not None:
        conditions.append(Content.team_id == team_id)

    query = (
        select(Content)
        .where(*conditions)
        .order_by(Content.published_at.desc().nullslast())
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()
