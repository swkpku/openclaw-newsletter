"""Collector for AlternativeTo listings and reviews."""

import hashlib
import logging

from bs4 import BeautifulSoup

from src.collectors.base import BaseCollector
from src.config import ALTERNATIVETO_URL
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class AlternativeToCollector(BaseCollector):
    """Scrapes AlternativeTo for alternative listings, comments, and reviews."""

    name = "alternativeto"

    def collect(self, state: StateManager) -> list[ContentItem]:
        resp = self._get(ALTERNATIVETO_URL)
        soup = BeautifulSoup(resp.text, "html.parser")

        items: list[ContentItem] = []

        # Look for alternative product listings
        for card in soup.select(
            ".app-listing, .alternative-item, article, .card, .listing-item"
        ):
            title_el = card.select_one("h2, h3, h4, .title, .name, a.app-name")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title:
                continue

            link_el = card.select_one("a[href]")
            url = link_el["href"] if link_el else ""
            if url and url.startswith("/"):
                url = f"https://alternativeto.net{url}"

            desc_el = card.select_one("p, .description, .text")
            description = desc_el.get_text(strip=True) if desc_el else ""

            item_hash = hashlib.md5(title.encode()).hexdigest()[:12]
            item_id = f"altto:{item_hash}"
            if state.is_covered(item_id):
                continue

            items.append(
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title=title,
                    url=url,
                    description=description,
                    content_type="alternative",
                )
            )

        # Look for user comments and reviews
        for comment in soup.select(".comment, .review, .user-review"):
            text_el = comment.select_one("p, .text, .body, .content")
            if not text_el:
                continue
            text = text_el.get_text(strip=True)
            if not text:
                continue

            author_el = comment.select_one(".user, .author, .username")
            author = author_el.get_text(strip=True) if author_el else ""

            item_hash = hashlib.md5(text.encode()).hexdigest()[:12]
            item_id = f"altto:{item_hash}"
            if state.is_covered(item_id):
                continue

            items.append(
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title=f"Review on AlternativeTo",
                    url=ALTERNATIVETO_URL,
                    description=text[:500],
                    author=author,
                    content_type="review",
                )
            )

        return items
