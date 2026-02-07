"""Collector for OpenClaw-related events via Eventbrite API."""

import logging

from src.collectors.base import BaseCollector
from src.config import EVENTBRITE_API_URL
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class EventsCollector(BaseCollector):
    """Fetches OpenClaw-related events from Eventbrite."""

    name = "events"

    def is_available(self) -> bool:
        return bool(self.config.eventbrite_token)

    def collect(self, state: StateManager) -> list[ContentItem]:
        url = f"{EVENTBRITE_API_URL}/events/search/"
        params = {
            "q": "openclaw AI",
            "token": self.config.eventbrite_token,
        }

        resp = self._get(url, params=params)
        data = resp.json()

        items: list[ContentItem] = []
        for event in data.get("events", []):
            event_id = str(event.get("id", ""))
            item_id = f"event:{event_id}"
            if state.is_covered(item_id):
                continue

            venue = event.get("venue", {}) or {}
            start = event.get("start", {}) or {}
            items.append(
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title=event.get("name", {}).get("text", "") if isinstance(event.get("name"), dict) else str(event.get("name", "")),
                    url=event.get("url", ""),
                    description=event.get("description", {}).get("text", "")[:500] if isinstance(event.get("description"), dict) else str(event.get("description", ""))[:500],
                    published_at=start.get("utc", ""),
                    content_type="event",
                    metadata={
                        "venue_name": venue.get("name", ""),
                        "venue_city": venue.get("address", {}).get("city", "") if isinstance(venue.get("address"), dict) else "",
                        "start_local": start.get("local", ""),
                        "start_utc": start.get("utc", ""),
                        "is_online": event.get("online_event", False),
                    },
                )
            )

        return items
