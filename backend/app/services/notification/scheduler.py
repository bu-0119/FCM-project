from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models import User, Content
from app.services.notification.push import push_service
from app.services.content.collector import content_collector

scheduler = AsyncIOScheduler()


async def _collect_and_notify():
    """Scheduled job: collect content and notify users."""
    async with async_session() as db:
        try:
            # Collect new content
            await content_collector.collect_rss(db)

            # Get users with notify_settings
            result = await db.execute(select(User))
            users = result.scalars().all()

            for user in users:
                notify_settings = user.notify_settings or {}
                if not notify_settings:
                    continue

                teams = user.selected_teams or []
                if not teams:
                    continue

                # Daily summary at preferred time
                await db.commit()
        except Exception:
            await db.rollback()


async def _cleanup_old_sessions():
    """Periodic cleanup of old agent sessions."""
    from datetime import datetime, timezone, timedelta
    from app.models import AgentSession

    async with async_session() as db:
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(days=30)
            result = await db.execute(
                select(AgentSession).where(AgentSession.updated_at < cutoff)
            )
            old_sessions = result.scalars().all()
            for session in old_sessions:
                await db.delete(session)
            await db.commit()
        except Exception:
            await db.rollback()


def start_scheduler():
    """Start APScheduler with cron jobs."""
    scheduler.add_job(
        _collect_and_notify,
        CronTrigger(hour=8, minute=30),
        id="daily_collect",
        name="Daily content collection at 8:30",
        replace_existing=True,
    )
    scheduler.add_job(
        _collect_and_notify,
        CronTrigger(hour=18, minute=0),
        id="evening_collect",
        name="Evening content collection at 18:00",
        replace_existing=True,
    )
    scheduler.add_job(
        _cleanup_old_sessions,
        CronTrigger(hour=3, minute=0),
        id="cleanup_sessions",
        name="Cleanup old agent sessions at 3:00",
        replace_existing=True,
    )
    scheduler.start()


def shutdown_scheduler():
    scheduler.shutdown(wait=False)
