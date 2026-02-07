"""Collector for OpenClaw on the DigitalOcean Marketplace."""

import logging
from datetime import date

from bs4 import BeautifulSoup

from src.collectors.base import BaseCollector
from src.config import DIGITALOCEAN_URL
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class DigitalOceanCollector(BaseCollector):
    """Scrapes the DigitalOcean Marketplace page for OpenClaw."""

    name = "digitalocean"

    def collect(self, state: StateManager) -> list[ContentItem]:
        today = date.today().isoformat()
        item_id = f"do:{today}"
        if state.is_covered(item_id):
            return []

        try:
            resp = self._get(DIGITALOCEAN_URL)
            soup = BeautifulSoup(resp.text, "html.parser")

            # Extract page title
            title_tag = soup.find("h1")
            title = title_tag.get_text(strip=True) if title_tag else "OpenClaw on DigitalOcean"

            # Extract description from meta or first paragraph
            description = ""
            meta_desc = soup.find("meta", attrs={"name": "description"})
            if meta_desc:
                description = meta_desc.get("content", "")
            if not description:
                first_p = soup.find("p")
                if first_p:
                    description = first_p.get_text(strip=True)

            # Look for deployment/stats info
            stats = {}
            stat_elements = soup.find_all(class_=lambda c: c and "stat" in c.lower()) if soup else []
            for el in stat_elements:
                text = el.get_text(strip=True)
                if text:
                    stats[f"stat_{len(stats)}"] = text

            return [
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title=title,
                    url=DIGITALOCEAN_URL,
                    description=description[:500],
                    content_type="marketplace",
                    metadata=stats,
                )
            ]
        except Exception as e:
            logger.warning(f"[digitalocean] Failed to parse marketplace page: {e}")
            return []
