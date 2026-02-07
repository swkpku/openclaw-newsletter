"""Collector for TLDR newsletter mentions of OpenClaw."""

import hashlib
import logging

from bs4 import BeautifulSoup

from src.collectors.base import BaseCollector
from src.config import SEARCH_KEYWORDS, TLDR_URL
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class TldrNewsCollector(BaseCollector):
    """Scrapes TLDR newsletter pages for OpenClaw mentions."""

    name = "tldr_news"

    def collect(self, state: StateManager) -> list[ContentItem]:
        resp = self._get(TLDR_URL)
        soup = BeautifulSoup(resp.text, "html.parser")

        items: list[ContentItem] = []
        links = soup.find_all("a", href=True)

        for link_el in links:
            href = link_el.get("href", "")
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue

            parent = link_el.parent
            text_block = parent.get_text(strip=True) if parent else ""
            title = link_el.get_text(strip=True)
            combined = f"{title} {text_block}".lower()

            if not any(kw.lower() in combined for kw in SEARCH_KEYWORDS):
                continue

            url_hash = hashlib.md5(href.encode()).hexdigest()[:12]
            item_id = f"tldr:{url_hash}"
            if state.is_covered(item_id):
                continue

            items.append(
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title=title or href,
                    url=href,
                    description=text_block[:500],
                    content_type="tldr_mention",
                )
            )

        return items
