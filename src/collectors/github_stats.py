"""Collector for GitHub repository statistics."""

import logging
import re
from datetime import date

from src.collectors.base import BaseCollector
from src.config import GITHUB_API_BASE, GITHUB_OWNER, GITHUB_REPO
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class GitHubStatsCollector(BaseCollector):
    """Fetches repository statistics (stars, forks, contributors, etc.)."""

    name = "github_stats"

    def collect(self, state: StateManager) -> list[ContentItem]:
        today = date.today().isoformat()
        item_id = f"stats:{today}"
        if state.is_covered(item_id):
            return []

        headers = {}
        if self.config.github_token:
            headers["Authorization"] = f"token {self.config.github_token}"

        # Fetch repo overview
        repo_url = f"{GITHUB_API_BASE}/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
        repo_resp = self._get(repo_url, headers=headers)
        repo = repo_resp.json()

        stats = {
            "stargazers_count": repo.get("stargazers_count", 0),
            "forks_count": repo.get("forks_count", 0),
            "open_issues_count": repo.get("open_issues_count", 0),
            "subscribers_count": repo.get("subscribers_count", 0),
        }

        # Fetch contributor count via Link header pagination
        contrib_url = (
            f"{GITHUB_API_BASE}/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
            f"/contributors?per_page=1&anon=true"
        )
        contrib_resp = self._get(contrib_url, headers=headers)
        contributor_count = self._parse_last_page(contrib_resp)
        stats["contributor_count"] = contributor_count

        return [
            ContentItem(
                id=item_id,
                source=self.name,
                title=f"OpenClaw repo stats for {today}",
                url=repo.get("html_url", ""),
                description=(
                    f"{stats['stargazers_count']} stars, "
                    f"{stats['forks_count']} forks, "
                    f"{stats['contributor_count']} contributors"
                ),
                published_at=today,
                content_type="stats",
                metadata=stats,
            )
        ]

    @staticmethod
    def _parse_last_page(resp) -> int:
        """Extract total count from the Link header's last page number."""
        link = resp.headers.get("Link", "")
        match = re.search(r'[&?]page=(\d+)[^>]*>;\s*rel="last"', link)
        if match:
            return int(match.group(1))
        # If no Link header, the response itself is the only page
        data = resp.json()
        return len(data) if isinstance(data, list) else 1
