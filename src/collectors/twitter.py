"""Collector for Twitter/X mentions via the Twitter API v2."""

import logging

from src.collectors.base import BaseCollector
from src.config import TWITTER_API_URL
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class TwitterCollector(BaseCollector):
    """Fetches recent tweets mentioning OpenClaw via Twitter API v2."""

    name = "twitter"

    def is_available(self) -> bool:
        return bool(self.config.twitter_bearer_token)

    def collect(self, state: StateManager) -> list[ContentItem]:
        url = f"{TWITTER_API_URL}/tweets/search/recent"
        headers = {
            "Authorization": f"Bearer {self.config.twitter_bearer_token}",
        }
        params = {
            "query": "openclaw",
            "max_results": 20,
            "tweet.fields": "created_at,public_metrics,author_id",
        }

        resp = self._get(url, headers=headers, params=params)
        data = resp.json()

        items: list[ContentItem] = []
        for tweet in data.get("data", []):
            tweet_id = tweet["id"]
            item_id = f"tweet:{tweet_id}"
            if state.is_covered(item_id):
                continue

            metrics = tweet.get("public_metrics", {})
            items.append(
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title=tweet.get("text", "")[:120],
                    url=f"https://twitter.com/i/web/status/{tweet_id}",
                    description=tweet.get("text", ""),
                    author=tweet.get("author_id", ""),
                    published_at=tweet.get("created_at", ""),
                    content_type="tweet",
                    metadata={
                        "like_count": metrics.get("like_count", 0),
                        "retweet_count": metrics.get("retweet_count", 0),
                        "reply_count": metrics.get("reply_count", 0),
                        "quote_count": metrics.get("quote_count", 0),
                    },
                )
            )

        return items
