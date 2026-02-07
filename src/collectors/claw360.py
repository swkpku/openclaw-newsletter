"""Collector for CLAW360 ecosystem listings."""

import hashlib
import logging

from bs4 import BeautifulSoup

from src.collectors.base import BaseCollector
from src.config import CLAW360_URL
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class Claw360Collector(BaseCollector):
    """Scrapes CLAW360 for service listings and integration cards."""

    name = "claw360"

    def collect(self, state: StateManager) -> list[ContentItem]:
        resp = self._get(CLAW360_URL)
        soup = BeautifulSoup(resp.text, "html.parser")

        items: list[ContentItem] = []
        for card in soup.select("article, .card, .service, .listing, .integration"):
            title_el = card.select_one("h2, h3, h4, .title, .name")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title:
                continue

            link_el = card.select_one("a[href]")
            url = link_el["href"] if link_el else ""
            if url and url.startswith("/"):
                url = CLAW360_URL + url

            desc_el = card.select_one("p, .description, .summary")
            description = desc_el.get_text(strip=True) if desc_el else ""

            item_hash = hashlib.md5(title.encode()).hexdigest()[:12]
            item_id = f"claw360:{item_hash}"
            if state.is_covered(item_id):
                continue

            items.append(
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title=title,
                    url=url,
                    description=description,
                    content_type="service_listing",
                )
            )

        return items
