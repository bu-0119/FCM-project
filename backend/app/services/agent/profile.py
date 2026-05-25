from collections import Counter
from datetime import datetime, timezone, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserBehavior, ContentType


class UserProfileVector:
    """Learned user preferences from behavior history."""

    def __init__(self, user: User):
        self.user = user
        self.content_type_weights: dict[str, float] = {}
        self.player_ids: list[str] = []
        self.activity_time_slots: list[str] = []
        self.interaction_style: str = "balanced"  # concise, detailed, balanced


async def update_profile(db: AsyncSession, user: User) -> UserProfileVector:
    """Update user profile vector from behavior history."""
    profile = UserProfileVector(user)

    # Analyze last 30 days of behavior
    since = datetime.now(timezone.utc) - timedelta(days=30)
    result = await db.execute(
        select(UserBehavior)
        .where(UserBehavior.user_id == user.id, UserBehavior.created_at >= since)
    )
    behaviors = result.scalars().all()

    # Content type weights from views/search
    content_actions = [b for b in behaviors if b.target_type == "content"]
    type_counts = Counter(
        (b.extra_data or {}).get("content_type", "unknown")
        for b in content_actions
    )
    total = sum(type_counts.values()) or 1
    profile.content_type_weights = {
        ct: round(count / total, 2) for ct, count in type_counts.most_common()
    }

    # Time slot preferences
    hours = [b.created_at.hour for b in behaviors]
    if hours:
        avg_hour = sum(hours) / len(hours)
        if avg_hour < 10:
            profile.activity_time_slots = ["morning"]
        elif avg_hour < 18:
            profile.activity_time_slots = ["afternoon"]
        else:
            profile.activity_time_slots = ["evening"]

    # Interaction style from query patterns
    searches = [b for b in behaviors if b.action == "search"]
    if searches:
        avg_detail = sum(len((b.extra_data or {}).get("query", "")) for b in searches) / len(searches)
        if avg_detail < 5:
            profile.interaction_style = "concise"
        elif avg_detail > 20:
            profile.interaction_style = "detailed"

    # Update user preference tags
    tags = []
    if profile.content_type_weights.get("transfer", 0) > 0.2:
        tags.append("transfer_fan")
    if profile.content_type_weights.get("data", 0) > 0.2:
        tags.append("data_nerd")
    if profile.interaction_style == "concise":
        tags.append("quick_reader")
    user.preference_tags = list(set((user.preference_tags or []) + tags))

    return profile
