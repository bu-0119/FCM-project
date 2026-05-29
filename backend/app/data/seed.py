"""Seed database with initial team data. Uses football-data.org API if key configured."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Team, League
from app.data.sources.football_data import football_data, COMPETITIONS

# Hardcoded fallback: league order must match COMPETITIONS dict
FALLBACK_TEAMS = {
    "PL": [
        ("曼城", "Manchester City", ["曼城", "Man City", "Haaland", "哈兰德", "瓜迪奥拉"]),
        ("曼联", "Manchester United", ["曼联", "Man United", "红魔", "B费", "Fernandes"]),
        ("利物浦", "Liverpool", ["利物浦", "Liverpool", "红军", "萨拉赫", "Salah"]),
        ("阿森纳", "Arsenal", ["阿森纳", "Arsenal", "枪手", "萨卡", "Saka"]),
        ("切尔西", "Chelsea", ["切尔西", "Chelsea", "蓝军", "帕尔默", "Palmer"]),
        ("热刺", "Tottenham Hotspur", ["热刺", "Spurs", "孙兴慜", "Son"]),
        ("纽卡斯尔联", "Newcastle United", ["纽卡", "Newcastle", "纽卡斯尔"]),
        ("阿斯顿维拉", "Aston Villa", ["维拉", "Villa"]),
    ],
    "PD": [
        ("巴塞罗那", "FC Barcelona", ["巴萨", "Barcelona", "Barca", "莱万", "Lewandowski"]),
        ("皇家马德里", "Real Madrid", ["皇马", "Real Madrid", "姆巴佩", "Mbappe", "贝林厄姆"]),
        ("马德里竞技", "Atlético de Madrid", ["马竞", "Atletico", "格列兹曼", "Griezmann"]),
        ("塞维利亚", "Sevilla FC", ["塞维利亚", "Sevilla"]),
        ("皇家社会", "Real Sociedad", ["皇家社会", "Sociedad"]),
        ("比利亚雷亚尔", "Villarreal CF", ["比利亚雷亚尔", "Villarreal", "黄潜"]),
        ("毕尔巴鄂竞技", "Athletic Club", ["毕尔巴鄂", "毕巴", "Athletic"]),
        ("瓦伦西亚", "Valencia CF", ["瓦伦西亚", "Valencia", "蝙蝠军团"]),
    ],
    "BL1": [
        ("拜仁慕尼黑", "FC Bayern München", ["拜仁", "Bayern", "慕尼黑", "凯恩", "Kane"]),
        ("多特蒙德", "Borussia Dortmund", ["多特", "Dortmund", "大黄蜂"]),
        ("莱比锡", "RB Leipzig", ["莱比锡", "Leipzig"]),
        ("勒沃库森", "Bayer 04 Leverkusen", ["勒沃库森", "Leverkusen", "药厂"]),
        ("法兰克福", "Eintracht Frankfurt", ["法兰克福", "Frankfurt"]),
        ("斯图加特", "VfB Stuttgart", ["斯图加特", "Stuttgart"]),
    ],
    "SA": [
        ("尤文图斯", "Juventus FC", ["尤文", "Juventus", "斑马军团", "弗拉霍维奇"]),
        ("AC米兰", "AC Milan", ["米兰", "AC Milan", "红黑军团", "莱奥", "Leao"]),
        ("国际米兰", "Inter Milan", ["国米", "Inter Milan", "蓝黑军团", "劳塔罗"]),
        ("那不勒斯", "SSC Napoli", ["那不勒斯", "Napoli", "Kvaratskhelia"]),
        ("罗马", "AS Roma", ["罗马", "Roma"]),
        ("拉齐奥", "SS Lazio", ["拉齐奥", "Lazio", "蓝鹰"]),
        ("亚特兰大", "Atalanta BC", ["亚特兰大", "Atalanta"]),
        ("佛罗伦萨", "ACF Fiorentina", ["佛罗伦萨", "Fiorentina", "紫百合"]),
    ],
    "FL1": [
        ("巴黎圣日耳曼", "Paris Saint-Germain", ["巴黎", "PSG", "大巴黎", "登贝莱", "Dembele"]),
        ("马赛", "Olympique de Marseille", ["马赛", "Marseille"]),
        ("里昂", "Olympique Lyonnais", ["里昂", "Lyon"]),
        ("摩纳哥", "AS Monaco", ["摩纳哥", "Monaco"]),
        ("里尔", "LOSC Lille", ["里尔", "Lille"]),
        ("尼斯", "OGC Nice", ["尼斯", "Nice"]),
    ],
}


async def seed_teams(db: AsyncSession):
    # Check if already seeded
    result = await db.execute(select(Team))
    if result.scalars().first() is not None:
        return

    # Create leagues from competition codes
    leagues_map = {}
    for code, comp in COMPETITIONS.items():
        league = League(name=comp["name"], name_en=comp["name_en"], code=code)
        db.add(league)
        leagues_map[code] = league
    await db.flush()

    # Try fetching real team data from football-data.org
    api_teams = {}
    if football_data.available:
        for code in COMPETITIONS:
            teams = await football_data.get_competition_teams(code)
            if teams:
                api_teams[code] = teams

    if api_teams:
        _seed_from_api(db, leagues_map, api_teams)
    else:
        _seed_from_fallback(db, leagues_map)

    await db.flush()


def _seed_from_api(db, leagues_map: dict, api_teams: dict):
    """Seed teams from football-data.org API response."""
    for code, teams in api_teams.items():
        league = leagues_map.get(code)
        if not league:
            continue
        for t in teams:
            name_cn = t["name"] or t.get("short_name", "") or t["name_en"]
            name_en = t["name_en"]
            keywords = [name_cn, name_en, t.get("short_name", "")]
            keywords = list(set(k for k in keywords if k))

            team = Team(
                name=name_cn,
                name_en=name_en,
                crest_url=t.get("crest_url", ""),
                league_id=league.id,
                api_id=t.get("api_id"),
                keywords=keywords,
            )
            db.add(team)


def _seed_from_fallback(db, leagues_map: dict):
    """Seed teams from hardcoded fallback data."""
    for code, teams in FALLBACK_TEAMS.items():
        league = leagues_map.get(code)
        if not league:
            continue
        for name, name_en, keywords in teams:
            team = Team(
                name=name,
                name_en=name_en,
                league_id=league.id,
                keywords=[name, name_en] + [k for k in keywords if k not in (name, name_en)],
            )
            db.add(team)
