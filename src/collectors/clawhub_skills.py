"""Collector for new skills from the ClawHub repository."""

import logging
import re

from src.collectors.base import BaseCollector
from src.config import CLAWHUB_OWNER, CLAWHUB_REPO, GITHUB_API_BASE
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)

# Commit subjects that are housekeeping noise, not real skill updates
_SKIP_PATTERN = re.compile(
    r"^(Merge |chore[:(]|Update README|update README|"
    r"fix lint|fix formatting|remove debug|new fix$)",
    re.IGNORECASE,
)


class ClawHubSkillsCollector(BaseCollector):
    """Fetches recent commits and releases from the ClawHub repo to find new skills."""

    name = "clawhub_skills"

    def collect(self, state: StateManager) -> list[ContentItem]:
        headers = {}
        if self.config.github_token:
            headers["Authorization"] = f"token {self.config.github_token}"

        # Fetch recent commits
        commits_url = (
            f"{GITHUB_API_BASE}/repos/{CLAWHUB_OWNER}/{CLAWHUB_REPO}"
            f"/commits?per_page=20"
        )
        resp = self._get(commits_url, headers=headers)
        commits = resp.json()

        items: list[ContentItem] = []
        for commit in commits:
            sha = commit.get("sha", "")
            item_id = f"clawhub:{sha[:8]}"
            if state.is_covered(item_id):
                continue

            commit_data = commit.get("commit", {})
            message = commit_data.get("message", "")
            title = message.split("\n", 1)[0]

            # Skip housekeeping commits
            if _SKIP_PATTERN.search(title):
                continue

            author_name = commit_data.get("author", {}).get("name", "")
            commit_date = commit_data.get("author", {}).get("date", "")

            # Use body (after first line) as description, not the full message
            body = message.split("\n", 1)[1].strip() if "\n" in message else ""

            items.append(
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title=title,
                    url=commit.get("html_url", ""),
                    description=body,
                    author=author_name,
                    published_at=commit_date,
                    content_type="clawhub_commit",
                    metadata={
                        "sha": sha,
                        "repo": f"{CLAWHUB_OWNER}/{CLAWHUB_REPO}",
                    },
                )
            )

        return items
