"""Collector for recent GitHub issues and pull requests."""

import logging

from src.collectors.base import BaseCollector
from src.config import GITHUB_API_BASE, GITHUB_OWNER, GITHUB_REPO
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class GitHubActivityCollector(BaseCollector):
    """Fetches recent issues and PRs from the OpenClaw GitHub repository."""

    name = "github_activity"

    def collect(self, state: StateManager) -> list[ContentItem]:
        url = (
            f"{GITHUB_API_BASE}/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
            f"/issues?state=all&sort=updated&per_page=30"
        )
        headers = {}
        if self.config.github_token:
            headers["Authorization"] = f"token {self.config.github_token}"

        resp = self._get(url, headers=headers)
        entries = resp.json()

        items: list[ContentItem] = []
        for entry in entries:
            is_pr = "pull_request" in entry
            number = entry["number"]
            item_id = f"pr:{number}" if is_pr else f"issue:{number}"

            if state.is_covered(item_id):
                continue

            labels = [lbl["name"] for lbl in entry.get("labels", [])]
            content_type = "pull_request" if is_pr else "issue"

            items.append(
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title=entry["title"],
                    url=entry.get("html_url", ""),
                    description=(entry.get("body", "") or "")[:500],
                    author=entry.get("user", {}).get("login", ""),
                    published_at=entry.get("created_at", ""),
                    content_type=content_type,
                    metadata={
                        "number": number,
                        "state": entry.get("state", ""),
                        "labels": labels,
                        "comments": entry.get("comments", 0),
                        "updated_at": entry.get("updated_at", ""),
                    },
                )
            )

        return items
