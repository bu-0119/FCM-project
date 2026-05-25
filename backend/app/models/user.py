import uuid
from datetime import date, datetime, timezone

from sqlalchemy import String, Date, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    wechat_openid: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(64))
    avatar_url: Mapped[str | None] = mapped_column(String(512))
    selected_teams: Mapped[list] = mapped_column(JSONB, default=list)  # [1, 5, 12]
    team_change_date: Mapped[date | None] = mapped_column(Date)
    preference_tags: Mapped[list] = mapped_column(JSONB, default=list)  # ["transfer_fan", "data_nerd"]
    notify_settings: Mapped[dict] = mapped_column(JSONB, default=dict)  # {match_reminder: 60, daily_summary: "9:00"}
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    posts = relationship("Post", back_populates="user")
    comments = relationship("Comment", back_populates="user")
    likes = relationship("Like", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
