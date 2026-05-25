import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, Notification, NotificationType


class WeChatPushService:
    """Send WeChat subscribe messages. Mocked for dev."""

    async def send_match_reminder(
        self, db: AsyncSession, user: User, team_name: str, match_info: str, kickoff_time: str
    ):
        notification = Notification(
            id=uuid.uuid4(),
            user_id=user.id,
            type=NotificationType.match_reminder,
            title=f"比赛提醒 - {team_name}",
            body=f"{match_info}\n开球时间: {kickoff_time}\n点击查看详情",
            data={"team_name": team_name, "kickoff": kickoff_time},
        )
        db.add(notification)
        # In production: call WeChat subscribe message API

    async def send_transfer_news(
        self, db: AsyncSession, user: User, title: str, summary: str
    ):
        notification = Notification(
            id=uuid.uuid4(),
            user_id=user.id,
            type=NotificationType.transfer_news,
            title=title,
            body=summary,
            data={"title": title},
        )
        db.add(notification)

    async def send_daily_summary(
        self, db: AsyncSession, user: User, summary: str, item_count: int
    ):
        notification = Notification(
            id=uuid.uuid4(),
            user_id=user.id,
            type=NotificationType.daily_summary,
            title=f"今日足球快报 - {item_count}条更新",
            body=summary,
            data={"item_count": item_count},
        )
        db.add(notification)

    async def send_agent_message(self, db: AsyncSession, user: User, title: str, body: str):
        notification = Notification(
            id=uuid.uuid4(),
            user_id=user.id,
            type=NotificationType.agent_message,
            title=title,
            body=body,
        )
        db.add(notification)


push_service = WeChatPushService()
