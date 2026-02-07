"""Collector for security vendor RSS feeds."""

import logging

import feedparser

from src.collectors.base import BaseCollector
from src.config import SECURITY_RSS_FEEDS
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)

_SECURITY_KEYWORDS = ["openclaw", "ai agent security", "ai assistant"]


class SecurityFeedsCollector(BaseCollector):
    """Parses security vendor RSS feeds for relevant security content."""

    name = "security_feeds"

    def collect(self, state: StateManager) -> list[ContentItem]:
        items: list[ContentItem] = []

        for feed_url in SECURITY_RSS_FEEDS:
            try:
                resp = self._get(feed_url)
            except Exception as e:
                logger.warning(f"[security_feeds] Failed to fetch {feed_url}: {e}")
                continue

            feed = feedparser.parse(resp.text)

            for entry in feed.entries:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                combined = f"{title} {summary}".lower()

                if not any(kw in combined for kw in _SECURITY_KEYWORDS):
                    continue

                link = entry.get("link", "")
                item_id = f"security:{link}"
                if state.is_covered(item_id):
                    continue

                items.append(
                    ContentItem(
                        id=item_id,
                        source=self.name,
                        title=title,
                        url=link,
                        description=summary,
                        author=entry.get("author", ""),
                        published_at=entry.get("published", ""),
                        content_type="security_article",
                        metadata={"feed": feed_url},
                    )
                )

        return items
