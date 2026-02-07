"""Collector for new skills from awesome-openclaw-skills repositories."""

import logging
import re

from src.collectors.base import BaseCollector
from src.config import AWESOME_SKILLS_REPOS, GITHUB_API_BASE
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)

# Commit subjects that are housekeeping noise, not real skill additions
_SKIP_PATTERN = re.compile(
    r"^(Merge |chore[:(]|Update README|update README|"
    r"fix lint|fix formatting|fix readme|Clean README|"
    r"new fix$|Add authors$|Add zips|Remove zips)",
    re.IGNORECASE,
)


class AwesomeSkillsCollector(BaseCollector):
    """Fetches recent commits from awesome-openclaw-skills repos to find new skills."""

    name = "awesome_skills"

    def collect(self, state: StateManager) -> list[ContentItem]:
        headers = {}
        if self.config.github_token:
            headers["Authorization"] = f"token {self.config.github_token}"

        items: list[ContentItem] = []
        for repo_info in AWESOME_SKILLS_REPOS:
            owner = repo_info["owner"]
            repo = repo_info["repo"]
            repo_items = self._collect_from_repo(owner, repo, headers, state)
            items.extend(repo_items)

        return items

    def _collect_from_repo(
        self,
        owner: str,
        repo: str,
        headers: dict,
        state: StateManager,
    ) -> list[ContentItem]:
        url = (
            f"{GITHUB_API_BASE}/repos/{owner}/{repo}/commits?per_page=10"
        )
        resp = self._get(url, headers=headers)
        commits = resp.json()

        items: list[ContentItem] = []
        for commit in commits:
            sha = commit.get("sha", "")
            item_id = f"awesome:{owner}:{sha[:8]}"
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
                    content_type="awesome_commit",
                    metadata={
                        "sha": sha,
                        "repo": f"{owner}/{repo}",
                    },
                )
            )

        return items
