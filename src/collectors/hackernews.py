"""Collector for Hacker News stories mentioning OpenClaw."""

import logging

from src.collectors.base import BaseCollector
from src.config import HACKERNEWS_API_URL
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class HackerNewsCollector(BaseCollector):
    """Fetches OpenClaw-related stories from the Hacker News Algolia API."""

    name = "hackernews"

    def collect(self, state: StateManager) -> list[ContentItem]:
        resp = self._get(
            HACKERNEWS_API_URL,
            params={"query": "openclaw", "tags": "story", "hitsPerPage": 20},
        )
        data = resp.json()

        items: list[ContentItem] = []
        for hit in data.get("hits", []):
            object_id = hit.get("objectID", "")
            item_id = f"hn:{object_id}"
            if state.is_covered(item_id):
                continue

            items.append(
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title=hit.get("title", ""),
                    url=hit.get("url", ""),
                    author=hit.get("author", ""),
                    published_at=hit.get("created_at", ""),
                    content_type="hackernews_story",
                    metadata={
                        "points": hit.get("points", 0),
                        "num_comments": hit.get("num_comments", 0),
                        "hn_url": f"https://news.ycombinator.com/item?id={object_id}",
                    },
                )
            )

        return items
