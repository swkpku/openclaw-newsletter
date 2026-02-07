"""Collector for Substack newsletter feeds mentioning OpenClaw."""

import logging

import feedparser

from src.collectors.base import BaseCollector
from src.config import SEARCH_KEYWORDS, SUBSTACK_FEEDS
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class SubstackCollector(BaseCollector):
    """Parses multiple Substack/newsletter RSS feeds for OpenClaw mentions."""

    name = "substack"

    def collect(self, state: StateManager) -> list[ContentItem]:
        items: list[ContentItem] = []
        for feed_url in SUBSTACK_FEEDS:
            try:
                items.extend(self._parse_feed(feed_url, state))
            except Exception:
                logger.warning(f"[{self.name}] Failed to parse {feed_url}")
                continue
        return items

    def _parse_feed(self, url: str, state: StateManager) -> list[ContentItem]:
        resp = self._get(url)
        feed = feedparser.parse(resp.text)

        items: list[ContentItem] = []
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            text = f"{title} {summary}".lower()

            if not any(kw.lower() in text for kw in SEARCH_KEYWORDS):
                continue

            link = entry.get("link", "")
            item_id = f"substack:{link}"
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
                    content_type="newsletter_article",
                    metadata={"feed_url": url},
                )
            )

        return items
