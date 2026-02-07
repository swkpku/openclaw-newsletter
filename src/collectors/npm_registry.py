"""Collector for OpenClaw npm package registry data."""

import logging

from src.collectors.base import BaseCollector
from src.config import NPM_PACKAGE_URL
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)

NPM_DOWNLOADS_URL = "https://api.npmjs.org/downloads/point/last-week/openclaw"


class NpmRegistryCollector(BaseCollector):
    """Fetches version and download data from the npm registry."""

    name = "npm_registry"

    def collect(self, state: StateManager) -> list[ContentItem]:
        resp = self._get(NPM_PACKAGE_URL)
        data = resp.json()

        latest_version = data.get("dist-tags", {}).get("latest", "")
        if not latest_version:
            logger.warning("[npm_registry] Could not determine latest version.")
            return []

        item_id = f"npm:{latest_version}"
        if state.is_covered(item_id):
            return []

        # Fetch weekly download count
        download_count = 0
        try:
            dl_resp = self._get(NPM_DOWNLOADS_URL)
            dl_data = dl_resp.json()
            download_count = dl_data.get("downloads", 0)
        except Exception as e:
            logger.warning(f"[npm_registry] Failed to fetch download stats: {e}")

        version_info = data.get("versions", {}).get(latest_version, {})

        return [
            ContentItem(
                id=item_id,
                source=self.name,
                title=f"openclaw v{latest_version} on npm",
                url=f"https://www.npmjs.com/package/openclaw",
                description=version_info.get("description", ""),
                published_at=data.get("time", {}).get(latest_version, ""),
                content_type="package",
                metadata={
                    "version": latest_version,
                    "weekly_downloads": download_count,
                    "license": version_info.get("license", ""),
                },
            )
        ]
