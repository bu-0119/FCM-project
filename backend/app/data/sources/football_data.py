from typing import Any

import httpx

from app.config import settings

BASE_URL = "https://api.football-data.org/v4"


class FootballDataClient:
    """Client for football-data.org API."""

    def __init__(self):
        self.headers = {"X-Auth-Token": settings.football_data_api_key} if settings.football_data_api_key else None

    async def _get(self, path: str, params: dict | None = None) -> dict | None:
        if not self.headers:
            return None  # No API key configured
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{BASE_URL}{path}", headers=self.headers, params=params)
            if resp.status_code == 200:
                return resp.json()
            return None

    async def get_team_matches(self, team_id: int, status: str = "SCHEDULED", limit: int = 5) -> dict | None:
        return await self._get(f"/teams/{team_id}/matches", params={"status": status, "limit": limit})

    async def get_competition_standings(self, competition_id: int) -> dict | None:
        return await self._get(f"/competitions/{competition_id}/standings")

    async def get_team_squad(self, team_id: int) -> dict | None:
        return await self._get(f"/teams/{team_id}")

    async def get_top_scorers(self, competition_id: int, limit: int = 10) -> dict | None:
        return await self._get(f"/competitions/{competition_id}/scorers", params={"limit": limit})


football_data = FootballDataClient()
