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

    # Short titles that are just nav/section headings, not real content
    _SKIP_TITLES = {
        "added", "changed", "fixed", "removed", "deprecated", "security",
        "start", "docs", "blog", "faq", "contact", "search", "home",
        "start here", "learning paths", "labs", "core concepts",
        "integrations", "troubleshooting", "changelog", "cookie policy",
        "privacy policy", "terms of service",
    }

    def collect(self, state: StateManager) -> list[ContentItem]:
        resp = self._get(LEARNCLAW_URL)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Scope to main content area to avoid nav/footer
        main = soup.find("main") or soup.find("article") or soup

        items: list[ContentItem] = []
        # Only look at version headings (h2) — each represents a release
        entries = main.find_all("h2")

        for entry in entries:
            title = entry.get_text(strip=True)
            if not title or len(title) > 200 or len(title) < 5:
                continue

            # Skip boilerplate headings
            if title.lower().strip("# ") in self._SKIP_TITLES:
                continue

            title_hash = hashlib.md5(title.encode()).hexdigest()[:12]
            item_id = f"learnclaw:{title_hash}"
            if state.is_covered(item_id):
                continue

            link_el = entry.find("a", href=True)
            link = link_el["href"] if link_el else LEARNCLAW_URL

            # Collect the content between this h2 and the next one
            description_parts: list[str] = []
            sibling = entry.find_next_sibling()
            while sibling and sibling.name != "h2":
                text = sibling.get_text(strip=True)
                if text:
                    description_parts.append(text)
                sibling = sibling.find_next_sibling()
            description = " ".join(description_parts)[:500]

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
