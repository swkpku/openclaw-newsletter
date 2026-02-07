"""Collector for ClawHunt product and bounty listings."""

import hashlib
import logging

from bs4 import BeautifulSoup

from src.collectors.base import BaseCollector
from src.config import CLAWHUNT_SH_URL, CLAWHUNT_SPACE_URL
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class ClawhuntCollector(BaseCollector):
    """Scrapes ClawHunt sites for product and bounty listings."""

    name = "clawhunt"

    def collect(self, state: StateManager) -> list[ContentItem]:
        items: list[ContentItem] = []

        for base_url in (CLAWHUNT_SPACE_URL, CLAWHUNT_SH_URL):
            try:
                resp = self._get(base_url)
            except Exception as e:
                logger.warning(f"[clawhunt] Failed to fetch {base_url}: {e}")
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            for card in soup.select(
                "article, .card, .product, .bounty, .listing, .item"
            ):
                title_el = card.select_one("h2, h3, h4, .title, .name")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                if not title:
                    continue

                link_el = card.select_one("a[href]")
                url = link_el["href"] if link_el else ""
                if url and url.startswith("/"):
                    url = base_url + url

                desc_el = card.select_one("p, .description, .summary")
                description = desc_el.get_text(strip=True) if desc_el else ""

                item_hash = hashlib.md5(title.encode()).hexdigest()[:12]
                item_id = f"clawhunt:{item_hash}"
                if state.is_covered(item_id):
                    continue

                items.append(
                    ContentItem(
                        id=item_id,
                        source=self.name,
                        title=title,
                        url=url,
                        description=description,
                        content_type="product_listing",
                        metadata={"site": base_url},
                    )
                )

        return items
