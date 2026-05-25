"""Seed database with initial team data for development."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Team, League


async def seed_teams(db: AsyncSession):
    # Check if already seeded
    result = await db.execute(select(Team))
    if result.scalars().first() is not None:
        return

    leagues = [
        League(name="英超", name_en="Premier League"),
        League(name="西甲", name_en="La Liga"),
        League(name="德甲", name_en="Bundesliga"),
        League(name="意甲", name_en="Serie A"),
        League(name="法甲", name_en="Ligue 1"),
        League(name="中超", name_en="Chinese Super League"),
    ]
    for league in leagues:
        db.add(league)
    await db.flush()

    # Map league names to their IDs
    league_map = {l.name: l.id for l in leagues}

    teams_data = [
        # 英超
        ("曼城", "Manchester City", 1, ["曼城", "Man City", "City", "哈兰德", "Haaland", "瓜迪奥拉", "Guardiola"]),
        ("曼联", "Manchester United", 1, ["曼联", "Man United", "Man Utd", "红魔", "B费", "Fernandes"]),
        ("利物浦", "Liverpool", 1, ["利物浦", "Liverpool", "红军", "萨拉赫", "Salah", "渣叔"]),
        ("阿森纳", "Arsenal", 1, ["阿森纳", "Arsenal", "枪手", "萨卡", "Saka"]),
        ("切尔西", "Chelsea", 1, ["切尔西", "Chelsea", "蓝军", "帕尔默", "Palmer"]),
        # 西甲
        ("巴塞罗那", "Barcelona", 2, ["巴萨", "Barcelona", "Barca", "梅西", "Messi", "莱万", "Lewandowski"]),
        ("皇家马德里", "Real Madrid", 2, ["皇马", "Real Madrid", "银河战舰", "姆巴佩", "Mbappe", "贝林厄姆", "Bellingham"]),
        ("马德里竞技", "Atletico Madrid", 2, ["马竞", "Atletico Madrid", "床单军团", "格列兹曼", "Griezmann"]),
        # 德甲
        ("拜仁慕尼黑", "Bayern Munich", 3, ["拜仁", "Bayern", "慕尼黑", "凯恩", "Kane", "穆西亚拉", "Musiala"]),
        ("多特蒙德", "Borussia Dortmund", 3, ["多特", "Dortmund", "大黄蜂", "马尔科", "Reus"]),
        # 意甲
        ("尤文图斯", "Juventus", 4, ["尤文", "Juventus", "斑马军团", "弗拉霍维奇", "Vlahovic"]),
        ("AC米兰", "AC Milan", 4, ["米兰", "AC Milan", "红黑军团", "莱奥", "Leao"]),
        ("国际米兰", "Inter Milan", 5, ["国米", "Inter Milan", "蓝黑军团", "劳塔罗", "Lautaro"]),
        # 法甲
        ("巴黎圣日耳曼", "Paris Saint-Germain", 5, ["巴黎", "PSG", "大巴黎", "登贝莱", "Dembele"]),
        # 中超
        ("上海海港", "Shanghai Port", 6, ["上海海港", "海港", "上港", "武磊"]),
        ("北京国安", "Beijing Guoan", 6, ["北京国安", "国安", "御林军"]),
        ("广州队", "Guangzhou FC", 6, ["广州", "广州队", "恒大"]),
    ]

    for name, name_en, league_idx, keywords in teams_data:
        league_id = league_map[list(league_map.keys())[league_idx - 1]]
        team = Team(name=name, name_en=name_en, league_id=league_id, keywords=keywords)
        db.add(team)

    await db.flush()
