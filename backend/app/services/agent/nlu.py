import json
import re

from app.config import settings


SYSTEM_PROMPT = """You are an NLU engine for a football AI assistant. Extract intent and entities from Chinese text.

Intents:
- query_transfer: transfer rumors/news about a team/player
- query_match: match schedule, results, live scores
- query_player: player stats, info, injuries
- set_reminder: user wants to set match reminder
- app_action: bookmark, share, or other app action
- chat: casual conversation, opinion, prediction
- guide: asking about capabilities

Entities: team_name, player_name, content_type (transfer/match/data/player_story/fun_fact), time_ref (upcoming/past/live)

Output ONLY valid JSON:
{"intent": "...", "entities": {"team_name": null, "player_name": null, "content_type": null, "time_ref": null}, "confidence": 0.0-1.0}
"""


class NLUResult:
    def __init__(self, intent: str, entities: dict, confidence: float):
        self.intent = intent
        self.entities = entities
        self.confidence = confidence


async def parse_message(message: str, llm_client=None) -> NLUResult:
    """Extract intent and entities from user message using LLM when available,
    falls back to rule-based parsing."""

    if llm_client and settings.llm_api_key:
        return await _llm_parse(message, llm_client)
    return _rule_parse(message)


async def _llm_parse(message: str, llm_client) -> NLUResult:
    try:
        response = await llm_client.chat.completions.create(
            model=settings.llm_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            temperature=0.1,
            max_tokens=200,
        )
        text = response.choices[0].message.content.strip()
        # Extract JSON from response
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            data = json.loads(match.group())
            return NLUResult(
                intent=data.get("intent", "chat"),
                entities=data.get("entities", {}),
                confidence=data.get("confidence", 0.5),
            )
    except Exception:
        pass
    return _rule_parse(message)


def _rule_parse(message: str) -> NLUResult:
    """Rule-based fallback NLU parser."""
    msg_lower = message.lower()

    # Keyword matching
    if any(w in message for w in ["转会", "transfer", "签约", "离队", "租借"]):
        intent = "query_transfer"
    elif any(w in message for w in ["比赛", "match", "赛程", "比分", "开球"]):
        intent = "query_match"
    elif any(w in message for w in ["球员", "player", "进了多少", "数据", "stats"]):
        intent = "query_player"
    elif any(w in message for w in ["提醒", "remind", "通知", "alert"]):
        intent = "set_reminder"
    elif any(w in message for w in ["收藏", "bookmark", "分享", "share"]):
        intent = "app_action"
    elif any(w in message for w in ["你能", "可以", "功能", "帮助", "help", "guide"]):
        intent = "guide"
    else:
        intent = "chat"

    entities = {"team_name": None, "player_name": None, "content_type": None, "time_ref": None}

    # Simple entity extraction
    team_keywords = {
        "巴萨": "Barcelona", "巴塞罗那": "Barcelona",
        "皇马": "Real Madrid", "皇家马德里": "Real Madrid",
        "曼联": "Manchester United", "曼城": "Manchester City",
        "利物浦": "Liverpool", "拜仁": "Bayern Munich",
        "尤文": "Juventus", "米兰": "AC Milan",
        "巴黎": "PSG", "切尔西": "Chelsea",
        "阿森纳": "Arsenal", "多特": "Dortmund",
    }
    for keyword, team in team_keywords.items():
        if keyword in message:
            entities["team_name"] = team
            break

    if "转会" in message:
        entities["content_type"] = "transfer"
    elif "比赛" in message:
        entities["content_type"] = "match"
    elif "数据" in message:
        entities["content_type"] = "data"
    elif "球员" in message:
        entities["content_type"] = "player_story"

    return NLUResult(intent=intent, entities=entities, confidence=0.6)
