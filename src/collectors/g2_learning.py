"""Collector for G2 Learning Hub RSS feed."""

import logging

import feedparser

from src.collectors.base import BaseCollector
from src.config import G2_LEARNING_URL, SEARCH_KEYWORDS
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class G2LearningCollector(BaseCollector):
    """Parses G2 Learning Hub RSS feed for AI assistant and openclaw mentions."""

    name = "g2_learning"

    def collect(self, state: StateManager) -> list[ContentItem]:
        resp = self._get(G2_LEARNING_URL)
        feed = feedparser.parse(resp.text)

        items: list[ContentItem] = []
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            combined = f"{title} {summary}".lower()

            if not any(kw.lower() in combined for kw in SEARCH_KEYWORDS):
                continue

            link = entry.get("link", "")
            item_id = f"g2:{link}"
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
                    content_type="article",
                )
            )

        return items
