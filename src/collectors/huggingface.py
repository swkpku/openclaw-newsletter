"""Collector for OpenClaw-related models on Hugging Face."""

import logging

from src.collectors.base import BaseCollector
from src.config import HUGGINGFACE_API_URL
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class HuggingFaceCollector(BaseCollector):
    """Fetches OpenClaw-related models from the Hugging Face API."""

    name = "huggingface"

    def collect(self, state: StateManager) -> list[ContentItem]:
        url = f"{HUGGINGFACE_API_URL}/models"
        resp = self._get(
            url,
            params={
                "search": "openclaw",
                "sort": "downloads",
                "direction": "-1",
                "limit": "5",
            },
        )
        models = resp.json()

        items: list[ContentItem] = []
        for model in models:
            model_id = model.get("modelId", "")
            if not model_id:
                continue

            item_id = f"hf:{model_id}"
            if state.is_covered(item_id):
                continue

            downloads = model.get("downloads", 0)
            likes = model.get("likes", 0)

            items.append(
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title=model_id,
                    url=f"https://huggingface.co/{model_id}",
                    description=model.get("pipeline_tag", ""),
                    author=model_id.split("/")[0] if "/" in model_id else "",
                    published_at=model.get("lastModified", ""),
                    content_type="model",
                    metadata={
                        "downloads": downloads,
                        "likes": likes,
                        "tags": model.get("tags", []),
                    },
                )
            )

        return items
