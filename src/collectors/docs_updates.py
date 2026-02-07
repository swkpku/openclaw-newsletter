"""Collector for OpenClaw documentation updates."""

import hashlib
import logging

from bs4 import BeautifulSoup

from src.collectors.base import BaseCollector
from src.config import DOCS_URL
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class DocsUpdatesCollector(BaseCollector):
    """Scrapes the OpenClaw docs site for changelog and recent updates."""

    name = "docs_updates"

    def collect(self, state: StateManager) -> list[ContentItem]:
        items: list[ContentItem] = []
        for path in ("/changelog", "/updates", ""):
            url = f"{DOCS_URL}{path}"
            try:
                items.extend(self._scrape_changelog(url, state))
            except Exception:
                logger.debug(f"[{self.name}] No content at {url}")
                continue
            if items:
                break
        return items

    def _scrape_changelog(self, url: str, state: StateManager) -> list[ContentItem]:
        resp = self._get(url)
        soup = BeautifulSoup(resp.text, "html.parser")

        items: list[ContentItem] = []
        entries = soup.find_all(["h2", "h3", "article", "section"])

        for entry in entries:
            title = entry.get_text(strip=True)
            if not title or len(title) > 200:
                continue

            title_hash = hashlib.md5(title.encode()).hexdigest()[:12]
            item_id = f"docs:{title_hash}"
            if state.is_covered(item_id):
                continue

            description = ""
            sibling = entry.find_next_sibling()
            if sibling and sibling.name in ("p", "ul", "ol", "div"):
                description = sibling.get_text(strip=True)[:500]

            items.append(
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title=title,
                    url=url,
                    description=description,
                    content_type="docs_update",
                )
            )

        return items
