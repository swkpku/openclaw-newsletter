"""Collector for tech news articles about OpenClaw via NewsAPI."""

import hashlib
import logging

from src.collectors.base import BaseCollector
from src.config import NEWSAPI_DOMAINS, NEWSAPI_URL
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class TechNewsCollector(BaseCollector):
    """Fetches OpenClaw coverage from major tech news outlets via NewsAPI."""

    name = "tech_news"

    def is_available(self) -> bool:
        return bool(self.config.newsapi_key)

    def collect(self, state: StateManager) -> list[ContentItem]:
        resp = self._get(
            NEWSAPI_URL,
            params={
                "q": "openclaw",
                "domains": NEWSAPI_DOMAINS,
                "apiKey": self.config.newsapi_key,
                "pageSize": 20,
                "sortBy": "publishedAt",
            },
        )
        data = resp.json()

        items: list[ContentItem] = []
        for article in data.get("articles", []):
            article_url = article.get("url", "")
            url_hash = hashlib.md5(article_url.encode()).hexdigest()[:12]
            item_id = f"news:{url_hash}"
            if state.is_covered(item_id):
                continue

            items.append(
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title=article.get("title", ""),
                    url=article_url,
                    description=article.get("description", "") or "",
                    author=article.get("author", "") or "",
                    published_at=article.get("publishedAt", ""),
                    content_type="tech_news",
                    metadata={
                        "source_name": article.get("source", {}).get("name", ""),
                        "source_id": article.get("source", {}).get("id", ""),
                    },
                )
            )

        return items
