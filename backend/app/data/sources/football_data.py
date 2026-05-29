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

# Famous team name → Chinese name mapping
TEAM_NAME_CN = {
    # 英超
    "Arsenal FC": "阿森纳", "Chelsea FC": "切尔西", "Liverpool FC": "利物浦",
    "Manchester City FC": "曼城", "Manchester United FC": "曼联",
    "Tottenham Hotspur FC": "热刺", "Newcastle United FC": "纽卡斯尔联",
    "Aston Villa FC": "阿斯顿维拉", "Everton FC": "埃弗顿",
    "West Ham United FC": "西汉姆联", "Brighton & Hove Albion FC": "布莱顿",
    "Brentford FC": "布伦特福德", "Crystal Palace FC": "水晶宫",
    "Wolverhampton Wanderers FC": "狼队", "Nottingham Forest FC": "诺丁汉森林",
    "Fulham FC": "富勒姆", "AFC Bournemouth": "伯恩茅斯",
    "Ipswich Town FC": "伊普斯维奇", "Leicester City FC": "莱斯特城",
    "Southampton FC": "南安普顿", "Leeds United FC": "利兹联",
    "Burnley FC": "伯恩利", "Sheffield United FC": "谢菲尔德联",
    # 西甲
    "FC Barcelona": "巴塞罗那", "Real Madrid CF": "皇家马德里",
    "Atlético de Madrid": "马德里竞技", "Sevilla FC": "塞维利亚",
    "Real Sociedad de Fútbol": "皇家社会", "Real Betis Balompié": "皇家贝蒂斯",
    "Villarreal CF": "比利亚雷亚尔", "Valencia CF": "瓦伦西亚",
    "Athletic Club": "毕尔巴鄂竞技", "RCD Espanyol de Barcelona": "西班牙人",
    "CA Osasuna": "奥萨苏纳", "RC Celta de Vigo": "塞尔塔",
    "Rayo Vallecano de Madrid": "巴列卡诺", "Getafe CF": "赫塔费",
    "Girona FC": "赫罗纳", "Deportivo Alavés": "阿拉维斯",
    "UD Las Palmas": "拉斯帕尔马斯", "RCD Mallorca": "马略卡",
    "CD Leganés": "莱加内斯", "Real Valladolid CF": "巴拉多利德",
    # 德甲
    "FC Bayern München": "拜仁慕尼黑", "Borussia Dortmund": "多特蒙德",
    "RB Leipzig": "RB莱比锡", "Bayer 04 Leverkusen": "勒沃库森",
    "Eintracht Frankfurt": "法兰克福", "VfB Stuttgart": "斯图加特",
    "Borussia Mönchengladbach": "门兴格拉德巴赫", "SC Freiburg": "弗赖堡",
    "TSG 1899 Hoffenheim": "霍芬海姆", "1. FSV Mainz 05": "美因茨",
    "FC Augsburg": "奥格斯堡", "VfL Wolfsburg": "沃尔夫斯堡",
    "1. FC Union Berlin": "柏林联合", "SV Werder Bremen": "云达不莱梅",
    "1. FC Heidenheim 1846": "海登海姆", "FC St. Pauli 1910": "圣保利",
    "Holstein Kiel": "基尔", "1. FC Köln": "科隆",
    # 意甲
    "Juventus FC": "尤文图斯", "AC Milan": "AC米兰", "Inter Milan": "国际米兰",
    "SSC Napoli": "那不勒斯", "AS Roma": "罗马", "SS Lazio": "拉齐奥",
    "Atalanta BC": "亚特兰大", "ACF Fiorentina": "佛罗伦萨",
    "Bologna FC 1909": "博洛尼亚", "Torino FC": "都灵",
    "Udinese Calcio": "乌迪内斯", "Genoa CFC": "热那亚",
    "Cagliari Calcio": "卡利亚里", "Parma Calcio 1913": "帕尔马",
    "Empoli FC": "恩波利", "Hellas Verona FC": "维罗纳",
    "Venezia FC": "威尼斯", "Como 1907": "科莫",
    "US Lecce": "莱切", "AC Monza": "蒙扎",
    # 法甲
    "Paris Saint-Germain FC": "巴黎圣日耳曼", "Olympique de Marseille": "马赛",
    "Olympique Lyonnais": "里昂", "AS Monaco FC": "摩纳哥",
    "LOSC Lille": "里尔", "OGC Nice": "尼斯",
    "RC Lens": "朗斯", "Stade Rennais FC 1901": "雷恩",
    "FC Nantes": "南特", "Montpellier HSC": "蒙彼利埃",
    "Stade Brestois 29": "布雷斯特", "Toulouse FC": "图卢兹",
    "RC Strasbourg Alsace": "斯特拉斯堡", "AJ Auxerre": "欧塞尔",
    "Angers SCO": "昂热", "Le Havre AC": "勒阿弗尔",
    "AS Saint-Étienne": "圣埃蒂安", "Stade de Reims": "兰斯",
    # 欧冠
    "PSV": "PSV埃因霍温", "Feyenoord Rotterdam": "费耶诺德",
    "AFC Ajax": "阿贾克斯", "FC Porto": "波尔图",
    "Sport Lisboa e Benfica": "本菲卡", "Sporting Clube de Portugal": "葡萄牙体育",
    "Club Brugge KV": "布鲁日", "SK Slavia Praha": "布拉格斯拉维亚",
    "FC København": "哥本哈根", "FK Bodø/Glimt": "博德闪耀",
    "Celtic FC": "凯尔特人", "Rangers FC": "格拉斯哥流浪者",
    "FK Crvena Zvezda": "贝尔格莱德红星", "GNK Dinamo": "萨格勒布迪纳摩",
    "Galatasaray SK": "加拉塔萨雷", "Fenerbahçe SK": "费内巴切",
    "FK Shakhtar Donetsk": "顿涅茨克矿工", "Olympiacos FC": "奥林匹亚科斯",
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
