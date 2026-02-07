"""Collector for Dev.to articles tagged with OpenClaw."""

import logging

from src.collectors.base import BaseCollector
from src.config import DEVTO_API_URL
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class DevToCollector(BaseCollector):
    """Fetches OpenClaw-tagged articles from the Dev.to API."""

    name = "devto"

    def collect(self, state: StateManager) -> list[ContentItem]:
        resp = self._get(
            DEVTO_API_URL,
            params={"tag": "openclaw", "per_page": 20},
        )
        articles = resp.json()

        items: list[ContentItem] = []
        for article in articles:
            article_id = article.get("id", "")
            item_id = f"devto:{article_id}"
            if state.is_covered(item_id):
                continue

            user = article.get("user", {})

            items.append(
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title=article.get("title", ""),
                    url=article.get("url", ""),
                    description=article.get("description", ""),
                    author=user.get("username", ""),
                    published_at=article.get("published_at", ""),
                    content_type="devto_article",
                )
            )

        return items
