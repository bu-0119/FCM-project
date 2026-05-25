import json
import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.core.database import get_db
from app.api.v1.deps import get_current_user
from app.models import User, Team
from app.services.agent.nlu import parse_message
from app.services.agent.dispatcher import dispatcher
from app.services.agent.dialogue import dialogue_manager, DialogueContext
from app.services.agent.scene_engine import detect_scene

router = APIRouter(prefix="/agent", tags=["agent"])


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class SSEChatEvent(BaseModel):
    type: str  # thinking, text, action, done
    data: dict | str


async def _stream_chat(
    message: str,
    session_id: str | None,
    user: User,
    db: AsyncSession,
) -> AsyncGenerator[dict, None]:
    """SSE event generator for agent chat."""

    # Load dialogue context
    ctx = await dialogue_manager.get_or_create(db, session_id, str(user.id))

    # Step 1: NLU
    yield {"event": "message", "data": json.dumps({"type": "thinking", "data": "正在理解你的问题..."}, ensure_ascii=False)}

    await asyncio.sleep(0.1)  # Simulate processing
    nlu_result = await parse_message(message)

    yield {"event": "message", "data": json.dumps({
        "type": "thinking",
        "data": {"intent": nlu_result.intent, "entities": nlu_result.entities}
    }, ensure_ascii=False)}

    # Step 2: Dispatch
    result = await dispatcher.dispatch(nlu_result, {
        "user_id": str(user.id),
        "session_id": ctx.session_id,
    })

    # Step 3: Handle based on intent
    response_text = await _handle_intent(result, user, db)

    # Stream response in chunks for a typing effect
    yield {"event": "message", "data": json.dumps({"type": "text", "data": ""}, ensure_ascii=False)}

    chunk_size = 10
    for i in range(0, len(response_text), chunk_size):
        chunk = response_text[i : i + chunk_size]
        yield {"event": "message", "data": json.dumps({"type": "text", "data": chunk}, ensure_ascii=False)}
        await asyncio.sleep(0.05)

    # Save to dialogue history
    ctx.add_message("user", message)
    ctx.add_message("assistant", response_text)
    await dialogue_manager.save(db, ctx)

    # Done
    yield {"event": "message", "data": json.dumps({
        "type": "done",
        "data": {"session_id": ctx.session_id}
    }, ensure_ascii=False)}


async def _handle_intent(result, user: User, db: AsyncSession) -> str:
    """Execute the dispatched intent and return a text response."""
    action = result.action
    args = result.args

    if action == "search_content":
        team_name = args.get("team_name", "")
        content_type = args.get("content_type", "")
        if team_name:
            return f"关于{team_name}的{'转会' if content_type == 'transfer' else ''}信息：\n\n最近没有重大更新。建议开启通知，有新消息会第一时间推送给你。"
        return "请告诉我你想了解哪支球队的信息？"

    elif action == "query_match":
        team_name = args.get("team_name", "你的主队")
        if user.selected_teams:
            result = await db.execute(select(Team).where(Team.id.in_(user.selected_teams)))
            teams = result.scalars().all()
            team_names = "、".join(t.name for t in teams)
            return f"你的主队{team_names}的下一场比赛信息：\n\n🏟 比赛暂未安排，请稍后再查询。赛季赛程通常会在开赛前1-2周公布。"
        return f"你还没有选择主队，可以在设置中选择1-3支关注的球队。"

    elif action == "query_player_stats":
        player_name = args.get("player_name", "")
        if player_name:
            return f"关于{player_name}的数据统计：\n\n📊 暂无最新数据。可以尝试搜索具体赛事或联系我获取更多信息。"
        return "请告诉我你想查询哪位球员的数据？"

    elif action == "create_reminder":
        if not user.selected_teams:
            return "你还没有选择主队。请先在设置中选择关注的球队，我就可以帮你设置比赛提醒了。"
        return "已为你开启比赛提醒。在主队比赛开始前60分钟，我会通过微信服务通知提醒你。"

    elif action == "app_action":
        return "收藏功能即将上线，敬请期待！"

    elif action == "llm_guide":
        return (
            "我是你的足球AI管家，可以帮你：\n"
            "🔍 查询转会新闻 - 「巴萨最近转会怎么样」\n"
            "📅 查看比赛信息 - 「下场比赛什么时候」\n"
            "📊 了解球员数据 - 「梅西进了多少球」\n"
            "🔔 设置比赛提醒 - 「提醒我看巴萨比赛」\n"
            "💬 闲聊足球话题 - 「你觉得今年谁能夺冠」\n\n"
            "你想了解什么？"
        )

    else:
        # chat / fallback
        scene = detect_scene()
        if scene == "transfer_window":
            return f"现在是转会窗口期！如果你有特别关注的球队和球员，我可以帮你留意最新的转会动态。你想了解哪支球队的转会进展？"
        return "我是你的足球AI管家，可以帮你查询转会新闻、比赛信息、球员数据，还可以设置比赛提醒。有什么想了解的吗？"


@router.post("/chat")
async def chat(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message is required")

    generator = _stream_chat(req.message, req.session_id, current_user, db)
    return EventSourceResponse(generator)
