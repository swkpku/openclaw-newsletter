"""Collector for OpenClaw Homebrew formula stats."""

import logging

from src.collectors.base import BaseCollector
from src.config import HOMEBREW_API_URL
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class HomebrewStatsCollector(BaseCollector):
    """Fetches install counts and version info from Homebrew."""

    name = "homebrew_stats"

    def collect(self, state: StateManager) -> list[ContentItem]:
        resp = self._get(HOMEBREW_API_URL)
        data = resp.json()

        version = data.get("versions", {}).get("stable", "")
        if not version:
            logger.warning("[homebrew_stats] Could not determine stable version.")
            return []

        item_id = f"homebrew:{version}"
        if state.is_covered(item_id):
            return []

        # Extract 30-day install analytics
        install_30d = data.get("analytics", {}).get("install", {}).get("30d", {})
        total_installs = 0
        if isinstance(install_30d, dict):
            # The value is a dict mapping formula name -> count
            for count in install_30d.values():
                if isinstance(count, int):
                    total_installs += count

        return [
            ContentItem(
                id=item_id,
                source=self.name,
                title=f"openclaw-cli {version} on Homebrew",
                url="https://formulae.brew.sh/formula/openclaw-cli",
                description=data.get("desc", ""),
                content_type="package",
                metadata={
                    "version": version,
                    "installs_30d": total_installs,
                    "homepage": data.get("homepage", ""),
                    "license": data.get("license", ""),
                },
            )
        ]
