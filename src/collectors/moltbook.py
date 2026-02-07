"""Collector for Moltbook posts about OpenClaw."""

import logging

from src.collectors.base import BaseCollector
from src.config import MOLTBOOK_API_URL
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class MoltbookCollector(BaseCollector):
    """Fetches OpenClaw-tagged posts from the Moltbook API."""

    name = "moltbook"

    def is_available(self) -> bool:
        return bool(self.config.moltbook_token)

    def collect(self, state: StateManager) -> list[ContentItem]:
        url = f"{MOLTBOOK_API_URL}/posts"
        headers = {"Authorization": f"Bearer {self.config.moltbook_token}"}
        params = {"tag": "openclaw", "limit": 20}

        resp = self._get(url, headers=headers, params=params)
        data = resp.json()

        items: list[ContentItem] = []
        for post in data if isinstance(data, list) else data.get("posts", []):
            post_id = str(post.get("id", ""))
            item_id = f"moltbook:{post_id}"
            if state.is_covered(item_id):
                continue

            items.append(
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title=post.get("title", "") or post.get("content", "")[:120],
                    url=post.get("url", ""),
                    description=post.get("content", "") or "",
                    author=post.get("author", {}).get("name", "") if isinstance(post.get("author"), dict) else str(post.get("author", "")),
                    published_at=post.get("created_at", "") or post.get("published_at", ""),
                    content_type="moltbook_post",
                    metadata={
                        "tags": post.get("tags", []),
                        "likes": post.get("likes", 0),
                        "shares": post.get("shares", 0),
                    },
                )
            )

        return items
