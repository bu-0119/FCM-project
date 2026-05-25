from dataclasses import dataclass
from typing import Any, Callable, Awaitable

from app.services.agent.nlu import NLUResult


@dataclass
class DispatchResult:
    action: str
    args: dict[str, Any]
    handler: Callable[..., Awaitable[Any]] | None = None


class IntentDispatcher:
    """Maps NLU intents to service actions."""

    def __init__(self):
        self._registry: dict[str, Callable] = {}

    def register(self, intent: str, handler: Callable):
        self._registry[intent] = handler

    async def dispatch(self, nlu_result: NLUResult, context: dict | None = None) -> DispatchResult:
        intent = nlu_result.intent
        entities = nlu_result.entities

        context = context or {}

        action_map = {
            "query_transfer": "search_content",
            "query_match": "query_match",
            "query_player": "query_player_stats",
            "set_reminder": "create_reminder",
            "app_action": "app_action",
            "chat": "llm_chat",
            "guide": "llm_guide",
        }

        action = action_map.get(intent, "llm_chat")
        args = {
            "intent": intent,
            "team_name": entities.get("team_name"),
            "player_name": entities.get("player_name"),
            "content_type": entities.get("content_type"),
            "time_ref": entities.get("time_ref"),
            "user_id": context.get("user_id"),
            "session_id": context.get("session_id"),
        }

        handler = self._registry.get(action)
        return DispatchResult(action=action, args=args, handler=handler)


dispatcher = IntentDispatcher()
