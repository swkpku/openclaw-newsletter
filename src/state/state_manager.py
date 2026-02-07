"""State management for tracking covered content and deduplication."""

import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class StateManager:
    """Manages state.json to track which content items have been covered."""

    def __init__(self, state_file: str = "state.json", max_entries: int = 500):
        self.state_file = state_file
        self.max_entries = max_entries
        self.state = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load state file: {e}. Starting fresh.")
        return {"covered_items": [], "last_run": None}

    def save(self) -> None:
        self.state["last_run"] = datetime.utcnow().isoformat()
        self._prune()
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)
        logger.info(f"State saved with {len(self.state['covered_items'])} entries.")

    def is_covered(self, item_id: str) -> bool:
        return item_id in self.state["covered_items"]

    def mark_covered(self, item_id: str) -> None:
        if item_id not in self.state["covered_items"]:
            self.state["covered_items"].append(item_id)

    def mark_items_covered(self, item_ids: list[str]) -> None:
        for item_id in item_ids:
            self.mark_covered(item_id)

    def _prune(self) -> None:
        """Keep only the most recent entries to prevent unbounded growth."""
        items = self.state["covered_items"]
        if len(items) > self.max_entries:
            self.state["covered_items"] = items[-self.max_entries :]
            logger.info(f"Pruned state to {self.max_entries} entries.")

    @property
    def last_run(self) -> str | None:
        return self.state.get("last_run")
