"""Collector for LearnClaw changelog entries."""

import hashlib
import logging

from bs4 import BeautifulSoup

from src.collectors.base import BaseCollector
from src.config import LEARNCLAW_URL
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class LearnClawCollector(BaseCollector):
    """Scrapes the LearnClaw changelog for new entries."""

    name = "learnclaw"

    def collect(self, state: StateManager) -> list[ContentItem]:
        resp = self._get(LEARNCLAW_URL)
        soup = BeautifulSoup(resp.text, "html.parser")

        items: list[ContentItem] = []
        entries = soup.find_all(["h2", "h3", "article", "li"])

        for entry in entries:
            title = entry.get_text(strip=True)
            if not title or len(title) > 200:
                continue

            title_hash = hashlib.md5(title.encode()).hexdigest()[:12]
            item_id = f"learnclaw:{title_hash}"
            if state.is_covered(item_id):
                continue

            link_el = entry.find("a", href=True)
            link = link_el["href"] if link_el else LEARNCLAW_URL

            description = ""
            sibling = entry.find_next_sibling()
            if sibling and sibling.name in ("p", "ul", "ol", "div"):
                description = sibling.get_text(strip=True)[:500]

            items.append(
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title=title,
                    url=link,
                    description=description,
                    content_type="changelog",
                )
            )

        return items
