"""Collector for Wikipedia article revision history."""

import logging

from src.collectors.base import BaseCollector
from src.config import WIKIPEDIA_API_URL, WIKIPEDIA_ARTICLE
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class WikipediaCollector(BaseCollector):
    """Fetches recent revisions of the OpenClaw Wikipedia article."""

    name = "wikipedia"

    def collect(self, state: StateManager) -> list[ContentItem]:
        resp = self._get(
            WIKIPEDIA_API_URL,
            params={
                "action": "query",
                "titles": WIKIPEDIA_ARTICLE,
                "prop": "revisions",
                "rvlimit": "10",
                "rvprop": "ids|timestamp|user|comment",
                "format": "json",
            },
        )
        data = resp.json()

        pages = data.get("query", {}).get("pages", {})
        items: list[ContentItem] = []

        for page_id, page in pages.items():
            if page_id == "-1":
                logger.info("[wikipedia] Article not found.")
                continue

            for rev in page.get("revisions", []):
                revid = rev.get("revid", "")
                item_id = f"wiki:{revid}"
                if state.is_covered(item_id):
                    continue

                comment = rev.get("comment", "")
                user = rev.get("user", "")
                timestamp = rev.get("timestamp", "")

                items.append(
                    ContentItem(
                        id=item_id,
                        source=self.name,
                        title=f"Wikipedia edit: {comment or 'No summary'}",
                        url=f"https://en.wikipedia.org/w/index.php?oldid={revid}",
                        description=comment,
                        author=user,
                        published_at=timestamp,
                        content_type="wiki_revision",
                        metadata={"revid": revid},
                    )
                )

        return items
