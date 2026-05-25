from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AgentSession


class DialogueContext:
    """Manages session context for multi-turn conversations."""

    def __init__(self, session_id: str, user_id: str | None = None):
        self.session_id = session_id
        self.user_id = user_id
        self.history: list[dict[str, str]] = []  # [{"role": "user"|"assistant", "content": "..."}]
        self.state: dict[str, Any] = {}  # Arbitrary conversation state
        self.max_history = 20

    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]

    def get_messages_for_llm(self) -> list[dict[str, str]]:
        return self.history

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "history": self.history[-10:],  # persist last 10
            "state": self.state,
        }


class DialogueManager:
    """Creates, loads, and persists dialogue sessions."""

    def __init__(self):
        self._active: dict[str, DialogueContext] = {}

    async def get_or_create(
        self, db: AsyncSession, session_id: str | None, user_id: str
    ) -> DialogueContext:
        if session_id and session_id in self._active:
            return self._active[session_id]

        if session_id:
            result = await db.execute(
                select(AgentSession).where(AgentSession.id == session_id)
            )
            session = result.scalar_one_or_none()
            if session:
                ctx = DialogueContext(session_id=str(session.id), user_id=user_id)
                ctx.history = (session.context or {}).get("history", [])
                ctx.state = (session.context or {}).get("state", {})
                self._active[session_id] = ctx
                return ctx

        # Create new session
        new_id = str(uuid.uuid4())
        ctx = DialogueContext(session_id=new_id, user_id=user_id)
        self._active[new_id] = ctx

        # Persist to DB
        db_session = AgentSession(id=new_id, user_id=user_id, context=ctx.to_dict())
        db.add(db_session)

        return ctx

    async def save(self, db: AsyncSession, ctx: DialogueContext):
        result = await db.execute(
            select(AgentSession).where(AgentSession.id == ctx.session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            session.context = ctx.to_dict()
            session.updated_at = datetime.now(timezone.utc)
            db.add(session)

    def remove(self, session_id: str):
        self._active.pop(session_id, None)


dialogue_manager = DialogueManager()
