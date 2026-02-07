"""Collector for OpenClaw Docker Hub repository data."""

import logging
from datetime import date

from src.collectors.base import BaseCollector
from src.config import DOCKER_HUB_URL
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class DockerHubCollector(BaseCollector):
    """Fetches pull counts, stars, and latest tags from Docker Hub."""

    name = "docker_hub"

    def collect(self, state: StateManager) -> list[ContentItem]:
        resp = self._get(DOCKER_HUB_URL)
        data = resp.json()

        last_updated = data.get("last_updated", "")
        last_updated_date = last_updated[:10] if last_updated else date.today().isoformat()

        item_id = f"docker:{last_updated_date}"
        if state.is_covered(item_id):
            return []

        pull_count = data.get("pull_count", 0)
        star_count = data.get("star_count", 0)

        # Fetch latest tags
        latest_tags = []
        try:
            tags_resp = self._get(f"{DOCKER_HUB_URL}/tags?page_size=5")
            tags_data = tags_resp.json()
            for tag in tags_data.get("results", []):
                latest_tags.append(tag.get("name", ""))
        except Exception as e:
            logger.warning(f"[docker_hub] Failed to fetch tags: {e}")

        return [
            ContentItem(
                id=item_id,
                source=self.name,
                title="openclaw/openclaw on Docker Hub",
                url="https://hub.docker.com/r/openclaw/openclaw",
                description=data.get("description", "") or data.get("full_description", "") or "",
                published_at=last_updated,
                content_type="package",
                metadata={
                    "pull_count": pull_count,
                    "star_count": star_count,
                    "latest_tags": latest_tags,
                },
            )
        ]
