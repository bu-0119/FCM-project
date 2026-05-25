from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import feedparser
import httpx


@dataclass
class RSSItem:
    title: str
    link: str
    summary: str
    published: datetime | None
    source: str


class RSSParser:
    """Generic RSS/Atom feed parser for football news sources."""

    FEEDS = {
        "espn": "https://www.espn.com/espn/rss/soccer/news",
        "bbc": "https://feeds.bbci.co.uk/sport/football/rss.xml",
        "sky": "https://feeds.feedburner.com/skysports/football",
        "goal": "https://www.goal.com/feeds/en/news",
    }

    async def fetch_feed(self, source: str) -> list[RSSItem]:
        url = self.FEEDS.get(source)
        if not url:
            return []

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=15.0)
            if resp.status_code != 200:
                return []

            feed = feedparser.parse(resp.text)
            items = []
            for entry in feed.entries[:20]:
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    published = datetime(*entry.updated_parsed[:6])

                items.append(RSSItem(
                    title=entry.get("title", ""),
                    link=entry.get("link", ""),
                    summary=entry.get("summary", ""),
                    published=published,
                    source=source,
                ))
            return items

    async def fetch_all(self) -> dict[str, list[RSSItem]]:
        results = {}
        for source in self.FEEDS:
            items = await self.fetch_feed(source)
            results[source] = items
        return results


rss_parser = RSSParser()
