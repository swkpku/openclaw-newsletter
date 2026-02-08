"""Collector for OpenClaw GitHub releases."""

import logging
from datetime import datetime, timedelta, timezone

from src.collectors.base import BaseCollector
from src.config import GITHUB_API_BASE, GITHUB_OWNER, GITHUB_REPO
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class GitHubReleasesCollector(BaseCollector):
    """Fetches recent releases from the OpenClaw GitHub repository."""

    name = "github_releases"

    def collect(self, state: StateManager) -> list[ContentItem]:
        url = f"{GITHUB_API_BASE}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases"
        headers = {}
        if self.config.github_token:
            headers["Authorization"] = f"token {self.config.github_token}"

        resp = self._get(url, headers=headers, params={"per_page": 15})
        releases = resp.json()

        # Only include releases from the last 3 days
        cutoff = datetime.now(timezone.utc) - timedelta(days=3)

        items: list[ContentItem] = []
        for rel in releases:
            # Skip releases older than 3 days
            published = rel.get("published_at", "")
            if published:
                try:
                    pub_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
                    if pub_dt < cutoff:
                        continue
                except ValueError:
                    pass

            item_id = f"release:{rel['tag_name']}"
            if state.is_covered(item_id):
                continue

            items.append(
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title=rel.get("name") or rel["tag_name"],
                    url=rel.get("html_url", ""),
                    description=rel.get("body", "") or "",
                    author=rel.get("author", {}).get("login", ""),
                    published_at=rel.get("published_at", ""),
                    content_type="release",
                    metadata={
                        "tag_name": rel["tag_name"],
                        "prerelease": rel.get("prerelease", False),
                        "draft": rel.get("draft", False),
                    },
                )
            )

        return items
