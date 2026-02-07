"""Collector for StackOverflow questions tagged with openclaw."""

import logging

from src.collectors.base import BaseCollector
from src.config import STACKOVERFLOW_API_URL
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class StackOverflowCollector(BaseCollector):
    """Fetches recent StackOverflow questions tagged with openclaw."""

    name = "stackoverflow"

    def collect(self, state: StateManager) -> list[ContentItem]:
        resp = self._get(
            f"{STACKOVERFLOW_API_URL}/search",
            params={
                "order": "desc",
                "sort": "activity",
                "tagged": "openclaw",
                "site": "stackoverflow",
            },
        )
        data = resp.json()

        items: list[ContentItem] = []
        for question in data.get("items", []):
            question_id = question.get("question_id", "")
            item_id = f"so:{question_id}"
            if state.is_covered(item_id):
                continue

            creation_date = question.get("creation_date", "")

            items.append(
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title=question.get("title", ""),
                    url=question.get("link", ""),
                    description="",
                    author=question.get("owner", {}).get("display_name", ""),
                    published_at=str(creation_date),
                    content_type="question",
                    metadata={
                        "score": question.get("score", 0),
                        "answer_count": question.get("answer_count", 0),
                        "is_answered": question.get("is_answered", False),
                        "tags": question.get("tags", []),
                    },
                )
            )

        return items
