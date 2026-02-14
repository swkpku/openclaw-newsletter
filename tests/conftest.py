"""Shared fixtures for OpenClaw Newsletter tests."""

import json
import tempfile
from pathlib import Path

import pytest

from src.config import Config
from src.models.data_models import ContentItem


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_config():
    """Provide a sample Config object for tests."""
    return Config(
        anthropic_api_key="test-key",
        github_token="test-github-token",
        request_timeout=10,
        max_retries=2,
        retry_backoff_factor=1.5,
    )


@pytest.fixture
def sample_content_item():
    """Provide a sample ContentItem for tests."""
    return ContentItem(
        id="test-item-1",
        source="test_collector",
        title="Test Item Title",
        url="https://example.com/item",
        description="This is a test item description.",
        author="test_author",
        published_at="2025-01-15T12:00:00Z",
        content_type="article",
        metadata={"likes": 10, "comments": 5},
    )


@pytest.fixture
def sample_content_items():
    """Provide multiple sample ContentItems for tests."""
    return [
        ContentItem(
            id=f"item-{i}",
            source="test_collector",
            title=f"Test Item {i}",
            url=f"https://example.com/item-{i}",
            description=f"Description for item {i}",
            author=f"author_{i}",
            published_at=f"2025-01-{15 + i:02d}T12:00:00Z",
            content_type="article",
            metadata={"likes": i * 10, "comments": i * 2},
        )
        for i in range(1, 6)
    ]


@pytest.fixture
def state_file(temp_dir):
    """Provide a path to a temporary state file."""
    return str(temp_dir / "test_state.json")


@pytest.fixture
def existing_state_file(temp_dir):
    """Provide a state file with pre-existing data."""
    state_path = temp_dir / "existing_state.json"
    state_data = {
        "covered_items": ["existing-1", "existing-2", "existing-3"],
        "last_run": "2025-01-14T10:00:00",
    }
    state_path.write_text(json.dumps(state_data))
    return str(state_path)
