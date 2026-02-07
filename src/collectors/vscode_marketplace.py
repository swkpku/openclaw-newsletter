"""Collector for OpenClaw VS Code Marketplace extension data."""

import logging

from src.collectors.base import BaseCollector
from src.config import VSCODE_EXTENSION_NAME, VSCODE_MARKETPLACE_URL
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class VSCodeMarketplaceCollector(BaseCollector):
    """Fetches install count, rating, and version from VS Code Marketplace."""

    name = "vscode_marketplace"

    def collect(self, state: StateManager) -> list[ContentItem]:
        payload = {
            "filters": [
                {
                    "criteria": [
                        {"filterType": 7, "value": VSCODE_EXTENSION_NAME}
                    ]
                }
            ],
            "flags": 914,
        }

        resp = self._post(
            VSCODE_MARKETPLACE_URL,
            json=payload,
            headers={"Content-Type": "application/json", "Accept": "application/json;api-version=6.0-preview.1"},
        )
        data = resp.json()

        results = data.get("results", [])
        if not results:
            logger.warning("[vscode_marketplace] No results returned.")
            return []

        extensions = results[0].get("extensions", [])
        if not extensions:
            logger.warning("[vscode_marketplace] No extensions found.")
            return []

        ext = extensions[0]
        display_name = ext.get("displayName", VSCODE_EXTENSION_NAME)

        # Extract version from versions list
        versions = ext.get("versions", [])
        version = versions[0].get("version", "unknown") if versions else "unknown"

        item_id = f"vscode:{version}"
        if state.is_covered(item_id):
            return []

        # Extract statistics
        stats = ext.get("statistics", [])
        install_count = 0
        average_rating = 0.0
        for stat in stats:
            name = stat.get("statisticName", "")
            if name == "install":
                install_count = int(stat.get("value", 0))
            elif name == "averagerating":
                average_rating = round(float(stat.get("value", 0)), 2)

        return [
            ContentItem(
                id=item_id,
                source=self.name,
                title=f"{display_name} v{version} on VS Code Marketplace",
                url=f"https://marketplace.visualstudio.com/items?itemName={VSCODE_EXTENSION_NAME}",
                description=ext.get("shortDescription", ""),
                published_at=ext.get("lastUpdated", ""),
                content_type="extension",
                metadata={
                    "version": version,
                    "install_count": install_count,
                    "average_rating": average_rating,
                    "publisher": ext.get("publisher", {}).get("displayName", ""),
                },
            )
        ]
