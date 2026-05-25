import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Team, Content, ContentType
from app.data.sources.rss import rss_parser, RSSItem
from app.data.sources.football_data import football_data
from app.services.content.filter import team_content_filter


class ContentCollector:
    """Pulls content from external sources and persists matched items."""

    async def collect_rss(self, db: AsyncSession):
        """Fetch RSS feeds and match to teams."""
        all_feeds = await rss_parser.fetch_all()

        # Load all team keywords
        result = await db.execute(select(Team))
        teams = result.scalars().all()

        for source, items in all_feeds.items():
            for item in items:
                matched_team = team_content_filter.match_team(item, teams)
                if matched_team is None:
                    continue

                content_type = team_content_filter.classify(item)
                if await self._exists(db, item.link):
                    continue

                content = Content(
                    id=uuid.uuid4(),
                    team_id=matched_team.id,
                    content_type=content_type,
                    title=item.title,
                    summary=item.summary[:500] if item.summary else None,
                    source_url=item.link,
                    tags=team_content_filter.extract_tags(item.title + " " + (item.summary or ""), matched_team),
                    published_at=item.published,
                )
                db.add(content)

    async def collect_match_data(self, db: AsyncSession):
        """Fetch upcoming matches for tracked teams."""
        result = await db.execute(select(Team))
        teams = result.scalars().all()

        for team in teams:
            matches = await football_data.get_team_matches(team.id)
            if matches is None:
                continue

            for match in matches.get("matches", [])[:5]:
                home = match.get("homeTeam", {}).get("name", "")
                away = match.get("awayTeam", {}).get("name", "")
                utc_date = match.get("utcDate", "")
                title = f"{home} vs {away}"
                summary = f"比赛时间: {utc_date}\n主队: {home}\n客队: {away}"
                match_id = match.get("id")

                if await self._exists(db, str(match_id)):
                    continue

                content = Content(
                    id=uuid.uuid4(),
                    team_id=team.id,
                    content_type=ContentType.match,
                    title=title,
                    summary=summary,
                    source_url=f"https://www.football-data.org/matches/{match_id}",
                    tags=["match", home, away],
                    published_at=datetime.fromisoformat(utc_date) if utc_date else None,
                )
                db.add(content)

    async def _exists(self, db: AsyncSession, source_url: str) -> bool:
        result = await db.execute(
            select(Content).where(Content.source_url == source_url)
        )
        return result.scalar_one_or_none() is not None


content_collector = ContentCollector()
