"""Collector for academic news from CACM and Scientific American RSS feeds."""

import logging

import feedparser

from src.collectors.base import BaseCollector
from src.config import CACM_RSS_URL, SCIENTIFIC_AMERICAN_RSS, SEARCH_KEYWORDS
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)

_ACADEMIC_KEYWORDS = SEARCH_KEYWORDS + ["AI assistant"]


class AcademicNewsCollector(BaseCollector):
    """Parses CACM and Scientific American RSS feeds for OpenClaw-related articles."""

    name = "academic_news"

    def collect(self, state: StateManager) -> list[ContentItem]:
        items: list[ContentItem] = []
        for feed_url in (CACM_RSS_URL, SCIENTIFIC_AMERICAN_RSS):
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

            if not any(kw.lower() in text for kw in _ACADEMIC_KEYWORDS):
                continue

            link = entry.get("link", "")
            item_id = f"academic:{link}"
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
                    content_type="academic_article",
                    metadata={"feed_url": url},
                )
            )

        return items
