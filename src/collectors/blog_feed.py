"""Collector for the official OpenClaw blog RSS feed."""

import logging

import feedparser

from src.collectors.base import BaseCollector
from src.config import OFFICIAL_BLOG_RSS
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class BlogFeedCollector(BaseCollector):
    """Parses the official OpenClaw blog RSS feed for new posts."""

    name = "blog_feed"

    def collect(self, state: StateManager) -> list[ContentItem]:
        resp = self._get(OFFICIAL_BLOG_RSS)
        feed = feedparser.parse(resp.text)

        items: list[ContentItem] = []
        for entry in feed.entries:
            link = entry.get("link", "")
            item_id = f"blog:{link}"
            if state.is_covered(item_id):
                continue

            items.append(
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title=entry.get("title", ""),
                    url=link,
                    description=entry.get("summary", ""),
                    published_at=entry.get("published", ""),
                    content_type="blog_post",
                )
            )

        return items
