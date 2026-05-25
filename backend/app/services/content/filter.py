import re

from app.models import Team, ContentType
from app.data.sources.rss import RSSItem


class TeamContentFilter:
    """Match content to teams and classify content type."""

    TYPE_KEYWORDS = {
        ContentType.transfer: ["transfer", "转会", "签约", "离队", "租借", "rumour", "rumor", "deal", "fee"],
        ContentType.match: ["match", "比赛", "比分", "score", "goal", "win", "lose", "draw", "defeat"],
        ContentType.player_story: ["player", "球员", "story", "profile", "采访", "injury", "伤病"],
        ContentType.data: ["stats", "数据", "record", "top scorer", "射手", "ranking", "排名"],
        ContentType.fun_fact: ["fun fact", "趣闻", "curious", "amazing", "history", "历史"],
    }

    def match_team(self, item: RSSItem, teams: list[Team]) -> Team | None:
        """Check if an RSS item matches any tracked team by keywords."""
        text = f"{item.title} {item.summary}".lower()
        for team in teams:
            keywords = team.keywords or [team.name, team.name_en]
            for kw in keywords:
                if kw and kw.lower() in text:
                    return team
        return None

    def classify(self, item: RSSItem) -> ContentType:
        """Classify content type based on keyword matching."""
        text = f"{item.title} {item.summary}".lower()
        scores: dict[ContentType, int] = {}
        for ct, keywords in self.TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in text)
            if score > 0:
                scores[ct] = score
        if scores:
            return max(scores, key=scores.get)
        return ContentType.transfer  # default for football news

    def extract_tags(self, text: str, team: Team) -> list[str]:
        """Extract tags from content text."""
        tags = [team.name]
        if team.name_en:
            tags.append(team.name_en)

        # Extract mentioned player names (simple pattern)
        for kw in (team.keywords or []):
            if kw and kw not in tags:
                tags.append(kw)

        # Common tag patterns
        if re.search(r"goal|进球|hat.trick|帽子戏法", text, re.IGNORECASE):
            tags.append("goal")
        if re.search(r"transfer|转会|签约", text, re.IGNORECASE):
            tags.append("transfer")
        if re.search(r"injury|伤病|受伤", text, re.IGNORECASE):
            tags.append("injury")

        return list(set(tags))[:10]


team_content_filter = TeamContentFilter()
