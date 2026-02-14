"""Tests for the StateManager class."""

import json
from pathlib import Path

import pytest

from src.state.state_manager import StateManager


class TestStateManagerInit:
    """Tests for StateManager initialization."""

    def test_init_creates_empty_state_when_no_file(self, state_file):
        """StateManager should create empty state when file doesn't exist."""
        manager = StateManager(state_file)
        assert manager.state["covered_items"] == set()
        assert manager.state.get("last_run") is None

    def test_init_loads_existing_state(self, existing_state_file):
        """StateManager should load state from existing file."""
        manager = StateManager(existing_state_file)
        assert "existing-1" in manager.state["covered_items"]
        assert "existing-2" in manager.state["covered_items"]
        assert "existing-3" in manager.state["covered_items"]
        assert manager.last_run == "2025-01-14T10:00:00"

    def test_init_handles_corrupt_json(self, temp_dir):
        """StateManager should handle corrupt JSON gracefully."""
        corrupt_file = temp_dir / "corrupt.json"
        corrupt_file.write_text("not valid json {{{")
        manager = StateManager(str(corrupt_file))
        assert manager.state["covered_items"] == set()

    def test_init_with_custom_max_entries(self, state_file):
        """StateManager should accept custom max_entries."""
        manager = StateManager(state_file, max_entries=100)
        assert manager.max_entries == 100


class TestStateManagerCoverage:
    """Tests for marking and checking item coverage."""

    def test_is_covered_returns_false_for_new_item(self, state_file):
        """is_covered should return False for uncovered items."""
        manager = StateManager(state_file)
        assert manager.is_covered("new-item") is False

    def test_is_covered_returns_true_after_marking(self, state_file):
        """is_covered should return True after marking an item."""
        manager = StateManager(state_file)
        manager.mark_covered("new-item")
        assert manager.is_covered("new-item") is True

    def test_mark_covered_adds_to_set(self, state_file):
        """mark_covered should add item to covered_items set."""
        manager = StateManager(state_file)
        manager.mark_covered("item-1")
        manager.mark_covered("item-2")
        assert "item-1" in manager.state["covered_items"]
        assert "item-2" in manager.state["covered_items"]

    def test_mark_items_covered_bulk(self, state_file):
        """mark_items_covered should add multiple items at once."""
        manager = StateManager(state_file)
        manager.mark_items_covered(["item-1", "item-2", "item-3"])
        assert len(manager.state["covered_items"]) == 3
        assert all(
            f"item-{i}" in manager.state["covered_items"]
            for i in range(1, 4)
        )

    def test_duplicate_items_not_duplicated(self, state_file):
        """Marking same item twice should not create duplicates."""
        manager = StateManager(state_file)
        manager.mark_covered("item-1")
        manager.mark_covered("item-1")
        assert len(manager.state["covered_items"]) == 1


class TestStateManagerSave:
    """Tests for saving state to file."""

    def test_save_creates_file(self, state_file):
        """save should create the state file."""
        manager = StateManager(state_file)
        manager.mark_covered("item-1")
        manager.save()
        assert Path(state_file).exists()

    def test_save_writes_valid_json(self, state_file):
        """save should write valid JSON to file."""
        manager = StateManager(state_file)
        manager.mark_covered("item-1")
        manager.save()

        with open(state_file) as f:
            data = json.load(f)

        assert "covered_items" in data
        assert "item-1" in data["covered_items"]

    def test_save_sets_last_run_timestamp(self, state_file):
        """save should update last_run timestamp."""
        manager = StateManager(state_file)
        manager.save()

        with open(state_file) as f:
            data = json.load(f)

        assert "last_run" in data
        assert data["last_run"] is not None

    def test_saved_state_can_be_reloaded(self, state_file):
        """Saved state should be loadable by a new StateManager."""
        manager1 = StateManager(state_file)
        manager1.mark_items_covered(["item-1", "item-2", "item-3"])
        manager1.save()

        manager2 = StateManager(state_file)
        assert manager2.is_covered("item-1")
        assert manager2.is_covered("item-2")
        assert manager2.is_covered("item-3")


class TestStateManagerPruning:
    """Tests for state pruning to prevent unbounded growth."""

    def test_prune_limits_entries(self, state_file):
        """_prune should limit entries to max_entries."""
        manager = StateManager(state_file, max_entries=10)
        # Add more items than max_entries
        for i in range(20):
            manager.mark_covered(f"item-{i}")

        manager.save()

        assert len(manager.state["covered_items"]) == 10

    def test_prune_does_not_affect_under_limit(self, state_file):
        """_prune should not remove items when under limit."""
        manager = StateManager(state_file, max_entries=100)
        for i in range(10):
            manager.mark_covered(f"item-{i}")

        manager.save()

        assert len(manager.state["covered_items"]) == 10


class TestStateManagerLastRun:
    """Tests for last_run property."""

    def test_last_run_none_for_new_state(self, state_file):
        """last_run should be None for fresh state."""
        manager = StateManager(state_file)
        assert manager.last_run is None

    def test_last_run_returns_timestamp(self, existing_state_file):
        """last_run should return stored timestamp."""
        manager = StateManager(existing_state_file)
        assert manager.last_run == "2025-01-14T10:00:00"

    def test_last_run_updated_after_save(self, state_file):
        """last_run should be updated after save."""
        manager = StateManager(state_file)
        assert manager.last_run is None
        manager.save()
        assert manager.last_run is not None
