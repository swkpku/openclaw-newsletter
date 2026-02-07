"""Collector for Medium articles tagged with OpenClaw."""

import logging

import feedparser

from src.collectors.base import BaseCollector
from src.config import MEDIUM_RSS_URL
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class MediumCollector(BaseCollector):
    """Parses the Medium RSS feed for OpenClaw-tagged articles."""

    name = "medium"

    def collect(self, state: StateManager) -> list[ContentItem]:
        resp = self._get(MEDIUM_RSS_URL)
        feed = feedparser.parse(resp.text)

        items: list[ContentItem] = []
        for entry in feed.entries:
            link = entry.get("link", "")
            item_id = f"medium:{link}"
            if state.is_covered(item_id):
                continue

            author = entry.get("author", "")
            if not author:
                author = entry.get("dc_creator", "")

            items.append(
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title=entry.get("title", ""),
                    url=link,
                    description=entry.get("summary", ""),
                    author=author,
                    published_at=entry.get("published", ""),
                    content_type="medium_article",
                )
            )

        return items
