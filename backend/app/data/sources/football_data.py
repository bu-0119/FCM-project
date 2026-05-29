import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://api.football-data.org/v4"

# Competition IDs for football-data.org
COMPETITIONS = {
    "PL":  {"id": 2021, "name": "英超", "name_en": "Premier League"},
    "PD":  {"id": 2014, "name": "西甲", "name_en": "La Liga"},
    "BL1": {"id": 2002, "name": "德甲", "name_en": "Bundesliga"},
    "SA":  {"id": 2019, "name": "意甲", "name_en": "Serie A"},
    "FL1": {"id": 2015, "name": "法甲", "name_en": "Ligue 1"},
    "CL":  {"id": 2001, "name": "欧冠", "name_en": "Champions League"},
}

# Famous team name → Chinese name mapping (used as fallback)
TEAM_NAME_CN = {
    "Arsenal FC": "阿森纳", "Chelsea FC": "切尔西", "Liverpool FC": "利物浦",
    "Manchester City FC": "曼城", "Manchester United FC": "曼联",
    "Tottenham Hotspur FC": "热刺", "Newcastle United FC": "纽卡斯尔联",
    "FC Barcelona": "巴塞罗那", "Real Madrid CF": "皇家马德里",
    "Atlético de Madrid": "马德里竞技", "Sevilla FC": "塞维利亚",
    "FC Bayern München": "拜仁慕尼黑", "Borussia Dortmund": "多特蒙德",
    "RB Leipzig": "莱比锡", "Bayer 04 Leverkusen": "勒沃库森",
    "Juventus FC": "尤文图斯", "AC Milan": "AC米兰", "Inter Milan": "国际米兰",
    "SSC Napoli": "那不勒斯", "AS Roma": "罗马",
    "Paris Saint-Germain FC": "巴黎圣日耳曼", "Olympique de Marseille": "马赛",
    "Olympique Lyonnais": "里昂", "AS Monaco FC": "摩纳哥",
}


class FootballDataClient:
    """Client for football-data.org free API."""

    def __init__(self):
        self._key = settings.football_data_api_key or None
        self._available = bool(self._key)
        if not self._available:
            logger.info("football-data.org: no API key configured, using hardcoded data")

    @property
    def available(self) -> bool:
        return self._available

    async def _get(self, path: str, params: dict | None = None) -> dict | None:
        if not self._available:
            return None
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(
                    f"{BASE_URL}{path}",
                    headers={"X-Auth-Token": self._key},
                    params=params,
                )
                if resp.status_code == 200:
                    return resp.json()
                if resp.status_code == 429:
                    logger.warning("football-data.org rate limited, waiting...")
                else:
                    logger.warning(f"football-data.org error {resp.status_code}: {resp.text[:200]}")
            except Exception as e:
                logger.warning(f"football-data.org request failed: {e}")
            return None

    async def get_competition_teams(self, competition_code: str) -> list[dict]:
        """Fetch all teams in a competition. Returns list of team dicts."""
        comp = COMPETITIONS.get(competition_code)
        if not comp:
            return []
        data = await self._get(f"/competitions/{comp['id']}/teams")
        if not data or "teams" not in data:
            return []

        teams = []
        for t in data["teams"]:
            cn_name = TEAM_NAME_CN.get(t.get("name", ""), "")
            teams.append({
                "name": cn_name or t.get("name", ""),
                "name_en": t.get("name", ""),
                "short_name": t.get("shortName", ""),
                "crest_url": t.get("crest", ""),
                "api_id": t.get("id"),
                "league_code": competition_code,
            })
        return teams

    async def get_team_matches(self, team_api_id: int, status: str = "SCHEDULED", limit: int = 5) -> dict | None:
        return await self._get(f"/teams/{team_api_id}/matches", params={"status": status, "limit": limit})

    async def get_competition_standings(self, competition_code: str) -> dict | None:
        comp = COMPETITIONS.get(competition_code)
        if not comp:
            return None
        return await self._get(f"/competitions/{comp['id']}/standings")

    async def get_today_matches(self) -> dict | None:
        """Get all matches scheduled for today."""
        return await self._get("/matches")

    async def get_team_detail(self, team_api_id: int) -> dict | None:
        return await self._get(f"/teams/{team_api_id}")

    async def get_top_scorers(self, competition_code: str, limit: int = 10) -> dict | None:
        comp = COMPETITIONS.get(competition_code)
        if not comp:
            return None
        return await self._get(f"/competitions/{comp['id']}/scorers", params={"limit": limit})


football_data = FootballDataClient()
