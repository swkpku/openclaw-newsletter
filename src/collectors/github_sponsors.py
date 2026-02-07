"""Collector for GitHub Sponsors information via GraphQL."""

import logging
from datetime import date

from src.collectors.base import BaseCollector
from src.config import GITHUB_OWNER
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)

SPONSORS_QUERY = """
{
  organization(login: "%s") {
    sponsorshipsAsMaintainer(first: 10) {
      totalCount
      nodes {
        sponsorEntity {
          ... on User { login }
          ... on Organization { login }
        }
      }
    }
  }
}
"""


class GitHubSponsorsCollector(BaseCollector):
    """Fetches sponsor information for the OpenClaw organization via GraphQL."""

    name = "github_sponsors"

    def is_available(self) -> bool:
        # GraphQL requires authentication
        return bool(self.config.github_token)

    def collect(self, state: StateManager) -> list[ContentItem]:
        today = date.today().isoformat()
        item_id = f"sponsors:{today}"
        if state.is_covered(item_id):
            return []

        query = SPONSORS_QUERY % GITHUB_OWNER
        data = self._graphql(query)

        sponsorships = data.get("organization", {}).get(
            "sponsorshipsAsMaintainer", {}
        )
        total_count = sponsorships.get("totalCount", 0)
        nodes = sponsorships.get("nodes", [])
        sponsor_logins = [
            node.get("sponsorEntity", {}).get("login", "")
            for node in nodes
            if node.get("sponsorEntity")
        ]

        return [
            ContentItem(
                id=item_id,
                source=self.name,
                title=f"OpenClaw sponsors ({total_count} total)",
                url=f"https://github.com/sponsors/{GITHUB_OWNER}",
                description=f"{total_count} sponsors supporting OpenClaw",
                published_at=today,
                content_type="sponsors",
                metadata={
                    "total_count": total_count,
                    "recent_sponsors": sponsor_logins,
                },
            )
        ]
