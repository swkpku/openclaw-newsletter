"""Collector for Product Hunt product page."""

import hashlib
import logging

from bs4 import BeautifulSoup

from src.collectors.base import BaseCollector
from src.config import PRODUCT_HUNT_URL
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class ProductHuntCollector(BaseCollector):
    """Scrapes Product Hunt for product info, reviews, and upvotes."""

    name = "product_hunt"

    def collect(self, state: StateManager) -> list[ContentItem]:
        resp = self._get(PRODUCT_HUNT_URL)
        soup = BeautifulSoup(resp.text, "html.parser")

        items: list[ContentItem] = []

        # Product info section
        title_el = soup.select_one("h1, .product-name, [data-test='product-name']")
        tagline_el = soup.select_one(
            ".tagline, .product-tagline, [data-test='product-tagline']"
        )
        if title_el:
            title = title_el.get_text(strip=True)
            tagline = tagline_el.get_text(strip=True) if tagline_el else ""

            upvote_el = soup.select_one(
                ".upvote-count, [data-test='vote-count'], .vote-count"
            )
            upvotes = upvote_el.get_text(strip=True) if upvote_el else ""

            item_hash = hashlib.md5(title.encode()).hexdigest()[:12]
            item_id = f"ph:{item_hash}"
            if not state.is_covered(item_id):
                items.append(
                    ContentItem(
                        id=item_id,
                        source=self.name,
                        title=f"Product Hunt: {title}",
                        url=PRODUCT_HUNT_URL,
                        description=tagline,
                        content_type="product_listing",
                        metadata={"upvotes": upvotes},
                    )
                )

        # Reviews section
        for review in soup.select(".review, .comment, [data-test='review']"):
            text_el = review.select_one("p, .text, .body, .content")
            if not text_el:
                continue
            text = text_el.get_text(strip=True)
            if not text:
                continue

            author_el = review.select_one(".user, .author, .username")
            author = author_el.get_text(strip=True) if author_el else ""

            item_hash = hashlib.md5(text.encode()).hexdigest()[:12]
            item_id = f"ph:{item_hash}"
            if state.is_covered(item_id):
                continue

            items.append(
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title="Product Hunt review",
                    url=PRODUCT_HUNT_URL,
                    description=text[:500],
                    author=author,
                    content_type="review",
                )
            )

        return items
