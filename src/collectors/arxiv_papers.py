"""Collector for ArXiv research papers."""

import logging
import xml.etree.ElementTree as ET

from src.collectors.base import BaseCollector
from src.config import ARXIV_API_URL
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)

_ATOM_NS = "{http://www.w3.org/2005/Atom}"


class ArxivPapersCollector(BaseCollector):
    """Fetches recent ArXiv papers related to OpenClaw and AI assistants."""

    name = "arxiv_papers"

    def collect(self, state: StateManager) -> list[ContentItem]:
        resp = self._get(
            ARXIV_API_URL,
            params={
                "search_query": "all:openclaw+OR+all:AI+personal+assistant",
                "start": "0",
                "max_results": "10",
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            },
        )

        root = ET.fromstring(resp.text)

        items: list[ContentItem] = []
        for entry in root.findall(f"{_ATOM_NS}entry"):
            entry_id_el = entry.find(f"{_ATOM_NS}id")
            if entry_id_el is None or not entry_id_el.text:
                continue

            entry_url = entry_id_el.text.strip()
            # ArXiv entry IDs look like http://arxiv.org/abs/2401.12345v1
            arxiv_id = entry_url.rstrip("/").split("/")[-1]
            item_id = f"arxiv:{arxiv_id}"
            if state.is_covered(item_id):
                continue

            title_el = entry.find(f"{_ATOM_NS}title")
            title = title_el.text.strip() if title_el is not None and title_el.text else ""

            summary_el = entry.find(f"{_ATOM_NS}summary")
            summary = summary_el.text.strip() if summary_el is not None and summary_el.text else ""

            author_el = entry.find(f"{_ATOM_NS}author/{_ATOM_NS}name")
            author = author_el.text.strip() if author_el is not None and author_el.text else ""

            published_el = entry.find(f"{_ATOM_NS}published")
            published = published_el.text.strip() if published_el is not None and published_el.text else ""

            items.append(
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title=title,
                    url=entry_url,
                    description=summary[:500],
                    author=author,
                    published_at=published,
                    content_type="research_paper",
                    metadata={"arxiv_id": arxiv_id},
                )
            )

        return items
