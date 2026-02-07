"""Collector for Discord announcements via the Discord Bot API."""

import logging

from src.collectors.base import BaseCollector
from src.config import DISCORD_GUILD_ID
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class DiscordFeedCollector(BaseCollector):
    """Fetches announcements from a configured Discord guild channel."""

    name = "discord_feed"

    def is_available(self) -> bool:
        return bool(self.config.discord_bot_token)

    def collect(self, state: StateManager) -> list[ContentItem]:
        if not DISCORD_GUILD_ID:
            logger.info("[discord_feed] No guild ID configured; returning empty.")
            return []

        # Fetch channels to find an announcements channel
        headers = {"Authorization": f"Bot {self.config.discord_bot_token}"}
        channels_url = f"https://discord.com/api/v10/guilds/{DISCORD_GUILD_ID}/channels"
        resp = self._get(channels_url, headers=headers)
        channels = resp.json()

        # Find announcement channel (type 5) or fall back to first text channel
        channel_id = None
        for ch in channels:
            if ch.get("type") == 5:  # GUILD_ANNOUNCEMENT
                channel_id = ch["id"]
                break
        if not channel_id:
            for ch in channels:
                if ch.get("type") == 0:  # GUILD_TEXT
                    channel_id = ch["id"]
                    break
        if not channel_id:
            logger.info("[discord_feed] No suitable channel found.")
            return []

        messages_url = f"https://discord.com/api/v10/channels/{channel_id}/messages?limit=20"
        resp = self._get(messages_url, headers=headers)
        messages = resp.json()

        items: list[ContentItem] = []
        for msg in messages:
            message_id = msg["id"]
            item_id = f"discord:{message_id}"
            if state.is_covered(item_id):
                continue

            content = msg.get("content", "")
            author_info = msg.get("author", {})
            items.append(
                ContentItem(
                    id=item_id,
                    source=self.name,
                    title=content[:120] if content else "(attachment)",
                    url=f"https://discord.com/channels/{DISCORD_GUILD_ID}/{channel_id}/{message_id}",
                    description=content,
                    author=author_info.get("username", ""),
                    published_at=msg.get("timestamp", ""),
                    content_type="discord_message",
                    metadata={
                        "channel_id": channel_id,
                        "attachments": len(msg.get("attachments", [])),
                    },
                )
            )

        return items
