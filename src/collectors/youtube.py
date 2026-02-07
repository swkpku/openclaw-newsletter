"""Collector for YouTube videos about OpenClaw."""

import logging

from src.collectors.base import BaseCollector
from src.config import YOUTUBE_API_URL
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class YouTubeCollector(BaseCollector):
    """Fetches OpenClaw-related videos via the YouTube Data API v3."""

    name = "youtube"

    def is_available(self) -> bool:
        return bool(self.config.youtube_api_key)

    def collect(self, state: StateManager) -> list[ContentItem]:
        search_url = f"{YOUTUBE_API_URL}/search"
        params = {
            "part": "snippet",
            "q": "openclaw",
            "type": "video",
            "order": "date",
            "maxResults": 10,
            "key": self.config.youtube_api_key,
        }

        resp = self._get(search_url, params=params)
        data = resp.json()

        items: list[ContentItem] = []
        for entry in data.get("items", []):
            video_id = entry.get("id", {}).get("videoId", "")
            if not video_id:
                continue
            item_id = f"yt:{video_id}"
            if state.is_covered(item_id):
                continue

            snippet = entry.get("snippet", {})
            items.append(
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title=snippet.get("title", ""),
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    description=snippet.get("description", ""),
                    author=snippet.get("channelTitle", ""),
                    published_at=snippet.get("publishedAt", ""),
                    content_type="youtube_video",
                    metadata={
                        "channelTitle": snippet.get("channelTitle", ""),
                        "channelId": snippet.get("channelId", ""),
                        "thumbnailUrl": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                    },
                )
            )

        return items
