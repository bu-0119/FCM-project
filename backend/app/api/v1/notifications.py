from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.v1.deps import get_current_user_id
from app.api.v1.schemas import BaseSchema
from app.models import User, Notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


async def _get_user(db: AsyncSession, user_id: str) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


class NotificationResponse(BaseSchema):
    id: str
    type: str
    title: str
    body: str | None
    is_read: bool
    sent_at: str


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int
    page: int
    size: int


class UpdateNotifySettings(BaseModel):
    match_reminder: int | None = None
    daily_summary: str | None = None


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    page: int = Query(1, ge=1),
    size: int = Query(20, le=50),
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(db, user_id)
    base_query = select(Notification).where(Notification.user_id == user.id)

    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    unread_query = select(func.count()).select_from(
        select(Notification).where(
            Notification.user_id == user.id, Notification.is_read == False
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
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(db, user_id)
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id, Notification.user_id == user.id
        )
    )
    notification = result.scalar_one_or_none()
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.add(notification)
    await db.flush()
    return notification


@router.get("/settings")
async def get_settings(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(db, user_id)
    return user.notify_settings or {}


@router.put("/settings")
async def update_settings(
    req: UpdateNotifySettings,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(db, user_id)
    settings = user.notify_settings or {}
    if req.match_reminder is not None:
        settings["match_reminder"] = req.match_reminder
    if req.daily_summary is not None:
        settings["daily_summary"] = req.daily_summary
    user.notify_settings = settings
    db.add(user)
    await db.flush()
    return settings
