from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.v1.deps import get_user_from_db
from app.models import User, Notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    id: str
    type: str
    title: str
    body: str | None
    is_read: bool
    sent_at: str

    model_config = {"from_attributes": True}


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int
    page: int
    size: int


class UpdateNotifySettings(BaseModel):
    match_reminder: int | None = None  # minutes before kickoff
    daily_summary: str | None = None  # preferred time, e.g. "9:00"


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    page: int = Query(1, ge=1),
    size: int = Query(20, le=50),
    current_user: User = Depends(get_user_from_db),
    db: AsyncSession = Depends(get_db),
):
    base_query = select(Notification).where(Notification.user_id == current_user.id)

    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    unread_query = select(func.count()).select_from(
        select(Notification).where(
            Notification.user_id == current_user.id, Notification.is_read == False
        ).subquery()
    )
    unread_count = (await db.execute(unread_query)).scalar() or 0

    items_query = (
        base_query.order_by(Notification.sent_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    result = await db.execute(items_query)
    items = result.scalars().all()

    return NotificationListResponse(
        items=items, total=total, unread_count=unread_count, page=page, size=size
    )


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_read(
    notification_id: str,
    current_user: User = Depends(get_user_from_db),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == current_user.id
        )
    )
    notification = result.scalar_one_or_none()
    if notification is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.add(notification)
    await db.flush()
    return notification


@router.get("/settings")
async def get_settings(current_user: User = Depends(get_user_from_db)):
    return current_user.notify_settings or {}


@router.put("/settings")
async def update_settings(
    req: UpdateNotifySettings,
    current_user: User = Depends(get_user_from_db),
    db: AsyncSession = Depends(get_db),
):
    settings = current_user.notify_settings or {}
    if req.match_reminder is not None:
        settings["match_reminder"] = req.match_reminder
    if req.daily_summary is not None:
        settings["daily_summary"] = req.daily_summary
    current_user.notify_settings = settings
    db.add(current_user)
    await db.flush()
    return settings
