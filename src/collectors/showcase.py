"""Collector for the OpenClaw showcase and shoutouts pages."""

import hashlib
import logging

from bs4 import BeautifulSoup

from src.collectors.base import BaseCollector
from src.config import SHOWCASE_URL, SHOUTOUTS_URL
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class ShowcaseCollector(BaseCollector):
    """Scrapes the OpenClaw showcase and shoutouts pages for featured projects."""

    name = "showcase"

    def collect(self, state: StateManager) -> list[ContentItem]:
        items: list[ContentItem] = []
        for page_url in (SHOWCASE_URL, SHOUTOUTS_URL):
            items.extend(self._scrape_page(page_url, state))
        return items

    def _scrape_page(self, url: str, state: StateManager) -> list[ContentItem]:
        resp = self._get(url)
        soup = BeautifulSoup(resp.text, "html.parser")

        items: list[ContentItem] = []
        cards = soup.find_all(["article", "div"], class_=lambda c: c and "card" in c)
        if not cards:
            cards = soup.find_all("article")

        for card in cards:
            title_el = card.find(["h2", "h3", "h4", "a"])
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            link_el = card.find("a", href=True)
            link = link_el["href"] if link_el else ""

            url_hash = hashlib.md5((link or title).encode()).hexdigest()[:12]
            item_id = f"showcase:{url_hash}"
            if state.is_covered(item_id):
                continue

            desc_el = card.find("p")
            description = desc_el.get_text(strip=True) if desc_el else ""

            items.append(
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title=title,
                    url=link,
                    description=description,
                    content_type="showcase",
                    metadata={"page": url},
                )
            )

        return items
