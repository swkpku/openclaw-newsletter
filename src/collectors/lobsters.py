"""Collector for Lobsters stories mentioning OpenClaw."""

import logging

import feedparser

from src.collectors.base import BaseCollector
from src.config import LOBSTERS_RSS_URL, SEARCH_KEYWORDS
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class LobstersCollector(BaseCollector):
    """Parses the Lobsters RSS feed and filters for OpenClaw-related stories."""

    name = "lobsters"

    def collect(self, state: StateManager) -> list[ContentItem]:
        resp = self._get(LOBSTERS_RSS_URL)
        feed = feedparser.parse(resp.text)

        items: list[ContentItem] = []
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            text = f"{title} {summary}".lower()

            if not any(kw.lower() in text for kw in SEARCH_KEYWORDS):
                continue

            link = entry.get("link", "")
            item_id = f"lobsters:{link}"
            if state.is_covered(item_id):
                continue

            items.append(
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title=title,
                    url=link,
                    description=summary,
                    published_at=entry.get("published", ""),
                    content_type="lobsters_story",
                )
            )

        return items
