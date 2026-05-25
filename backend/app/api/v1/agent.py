from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.llm import get_llm_client, llm_chat
from app.api.v1.deps import get_current_user
from app.models import User, Team, Content
from app.services.agent.nlu import parse_message
from app.services.agent.dispatcher import dispatcher
from app.services.agent.dialogue import dialogue_manager
from app.services.agent.scene_engine import detect_scene

router = APIRouter(prefix="/agent", tags=["agent"])

SYSTEM_PROMPT = """你是「足球AI管家」，一个专业的足球助手。你的用户是中国球迷。
规则：
- 用中文回复，语气热情、专业
- 回答基于你的足球知识，包括球队、球员、赛事、转会等
- 如果用户询问实时数据（比分、赛程等），诚实说明你无法获取实时信息，建议开启通知
- 保持回复简洁，一般不超过200字
- 适当使用 emoji 增加趣味性"""


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    intent: str


async def _llm_response(ctx, user_message: str, system_extra: str = "") -> str:
    """Call LLM with conversation history + system prompt. Falls back to template."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT + system_extra}]
    messages.extend(ctx.get_messages_for_llm())
    messages.append({"role": "user", "content": user_message})

    llm_reply = await llm_chat(messages)
    if llm_reply:
        return llm_reply

    # Fallback if no LLM configured
    return None


async def _handle_intent(result, ctx, message: str, user: User, db: AsyncSession) -> str:
    action = result.action
    args = result.args
    team_name = args.get("team_name", "")

    # Build context for LLM
    sys_extra = ""
    if user.selected_teams:
        team_result = await db.execute(select(Team).where(Team.id.in_(user.selected_teams)))
        teams = team_result.scalars().all()
        team_info = "、".join(f"{t.name}({t.name_en})" for t in teams)
        sys_extra += f"\n用户的主队：{team_info}"

    # Try LLM first for conversational intents
    if action == "chat":
        llm_reply = await _llm_response(ctx, message, sys_extra)
        if llm_reply:
            return llm_reply
        return "我是你的足球AI管家，可以帮你查询转会新闻、比赛信息、球员数据，还可以设置比赛提醒。有什么想了解的吗？"

    elif action == "guide":
        llm_reply = await _llm_response(ctx, message, sys_extra)
        if llm_reply:
            return llm_reply
        return "我是你的足球AI管家，可以帮你查转会、看赛程、聊足球。你想了解什么？"

    elif action == "query_transfer":
        llm_reply = await _llm_response(ctx, message, sys_extra + "\n用户正在询问转会信息，请根据你的知识回答。如果没有最新信息，可以聊聊历史转会或转会期策略。")
        if llm_reply:
            return llm_reply
        if team_name:
            return f"关于{team_name}的转会信息：\n\n建议开启通知，有新消息会第一时间推送给你。"
        return "请告诉我你想了解哪支球队的转会信息？"

    elif action == "query_match":
        llm_reply = await _llm_response(ctx, message, sys_extra + "\n用户正在询问比赛信息。如果有实时性的内容，请说明你无法获取实时数据。")
        if llm_reply:
            return llm_reply
        if user.selected_teams:
            return f"你的主队下一场比赛信息暂未更新。建议开启比赛提醒功能。"
        return "你还没有选择主队，可以在「我的」页面中选择1-3支关注的球队。"

    elif action == "query_player":
        llm_reply = await _llm_response(ctx, message, sys_extra)
        if llm_reply:
            return llm_reply
        return "请告诉我你想了解哪位球员？"

    elif action == "set_reminder":
        if not user.selected_teams:
            return "你还没有选择主队。请先在「我的」页面中选择关注的球队，我就可以帮你设置比赛提醒了。"
        return "已为你开启比赛提醒！在主队比赛开始前，我会通过微信服务通知提醒你。"

    elif action == "app_action":
        return "收藏功能即将上线，敬请期待！"

    else:
        # Fallback to LLM chat
        llm_reply = await _llm_response(ctx, message, sys_extra)
        if llm_reply:
            return llm_reply
        return "我是你的足球AI管家，有什么可以帮你的吗？"


@router.post("/chat", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message is required")

    # Load dialogue context
    ctx = await dialogue_manager.get_or_create(db, req.session_id, str(current_user.id))

    # NLU with LLM client
    llm_client = get_llm_client()
    nlu_result = await parse_message(req.message, llm_client)

    # Dispatch
    result = await dispatcher.dispatch(nlu_result, {
        "user_id": str(current_user.id),
        "session_id": ctx.session_id,
    })

    # Generate response (LLM when available, template fallback)
    response_text = await _handle_intent(result, ctx, req.message, current_user, db)

    # Save to dialogue history
    ctx.add_message("user", req.message)
    ctx.add_message("assistant", response_text)
    await dialogue_manager.save(db, ctx)

    return ChatResponse(
        reply=response_text,
        session_id=ctx.session_id,
        intent=nlu_result.intent,
    )
