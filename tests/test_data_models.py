"""Tests for data models."""

import pytest

from src.models.data_models import (
    CollectorResult,
    ContentItem,
    NewsletterIssue,
    NewsletterSection,
)


class TestContentItem:
    """Tests for ContentItem dataclass."""

    def test_create_minimal_content_item(self):
        """ContentItem should be creatable with minimal required fields."""
        item = ContentItem(
            id="test-1",
            source="test_source",
            title="Test Title",
        )
        assert item.id == "test-1"
        assert item.source == "test_source"
        assert item.title == "Test Title"
        assert item.url == ""
        assert item.description == ""
        assert item.metadata == {}

    def test_create_full_content_item(self, sample_content_item):
        """ContentItem should accept all fields."""
        assert sample_content_item.id == "test-item-1"
        assert sample_content_item.url == "https://example.com/item"
        assert sample_content_item.author == "test_author"
        assert sample_content_item.metadata == {"likes": 10, "comments": 5}

    def test_to_dict(self, sample_content_item):
        """to_dict should return all fields as dictionary."""
        d = sample_content_item.to_dict()
        assert d["id"] == "test-item-1"
        assert d["source"] == "test_collector"
        assert d["title"] == "Test Item Title"
        assert d["url"] == "https://example.com/item"
        assert d["description"] == "This is a test item description."
        assert d["author"] == "test_author"
        assert d["published_at"] == "2025-01-15T12:00:00Z"
        assert d["content_type"] == "article"
        assert d["metadata"] == {"likes": 10, "comments": 5}

    def test_from_dict(self):
        """from_dict should create ContentItem from dictionary."""
        data = {
            "id": "dict-item",
            "source": "dict_source",
            "title": "Dict Title",
            "url": "https://example.com",
            "description": "Dict description",
            "author": "dict_author",
            "published_at": "2025-01-15T00:00:00Z",
            "content_type": "post",
            "metadata": {"score": 42},
        }
        item = ContentItem.from_dict(data)
        assert item.id == "dict-item"
        assert item.source == "dict_source"
        assert item.title == "Dict Title"
        assert item.metadata == {"score": 42}

    def test_from_dict_ignores_extra_fields(self):
        """from_dict should ignore fields not in dataclass."""
        data = {
            "id": "item-1",
            "source": "test",
            "title": "Title",
            "extra_field": "should be ignored",
            "another_extra": 123,
        }
        item = ContentItem.from_dict(data)
        assert item.id == "item-1"
        assert not hasattr(item, "extra_field")

    def test_roundtrip_dict_conversion(self, sample_content_item):
        """to_dict -> from_dict should preserve all data."""
        d = sample_content_item.to_dict()
        restored = ContentItem.from_dict(d)
        assert restored.id == sample_content_item.id
        assert restored.title == sample_content_item.title
        assert restored.metadata == sample_content_item.metadata


class TestCollectorResult:
    """Tests for CollectorResult dataclass."""

    def test_create_successful_result(self, sample_content_items):
        """CollectorResult should hold successful collection results."""
        result = CollectorResult(
            collector_name="test_collector",
            items=sample_content_items,
        )
        assert result.collector_name == "test_collector"
        assert len(result.items) == 5
        assert result.error is None
        assert result.skipped is False

    def test_create_error_result(self):
        """CollectorResult should hold error information."""
        result = CollectorResult(
            collector_name="failing_collector",
            error="Connection timeout",
        )
        assert result.collector_name == "failing_collector"
        assert result.items == []
        assert result.error == "Connection timeout"

    def test_create_skipped_result(self):
        """CollectorResult should indicate skipped collectors."""
        result = CollectorResult(
            collector_name="optional_collector",
            skipped=True,
        )
        assert result.skipped is True
        assert result.items == []


class TestNewsletterSection:
    """Tests for NewsletterSection dataclass."""

    def test_create_section(self, sample_content_items):
        """NewsletterSection should be creatable with items."""
        section = NewsletterSection(
            id="releases",
            title="Release Updates",
            items=sample_content_items,
        )
        assert section.id == "releases"
        assert section.title == "Release Updates"
        assert len(section.items) == 5

    def test_has_content_with_items(self, sample_content_items):
        """has_content should return True when items exist."""
        section = NewsletterSection(
            id="test",
            title="Test Section",
            items=sample_content_items,
        )
        assert section.has_content is True

    def test_has_content_with_html(self):
        """has_content should return True when content_html exists."""
        section = NewsletterSection(
            id="test",
            title="Test Section",
            content_html="<p>Some content</p>",
        )
        assert section.has_content is True

    def test_has_content_empty(self):
        """has_content should return False when empty."""
        section = NewsletterSection(
            id="empty",
            title="Empty Section",
        )
        assert section.has_content is False

    def test_has_content_empty_items_list(self):
        """has_content should return False with empty items list."""
        section = NewsletterSection(
            id="empty",
            title="Empty Section",
            items=[],
            content_html="",
        )
        assert section.has_content is False


class TestNewsletterIssue:
    """Tests for NewsletterIssue dataclass."""

    def test_create_issue(self, sample_content_items):
        """NewsletterIssue should be creatable with sections."""
        sections = [
            NewsletterSection(id="releases", title="Releases", items=sample_content_items[:2]),
            NewsletterSection(id="community", title="Community", items=sample_content_items[2:]),
        ]
        issue = NewsletterIssue(date="2025-01-15", sections=sections)

        assert issue.date == "2025-01-15"
        assert len(issue.sections) == 2
        assert issue.total_items == 5

    def test_auto_sets_generated_at(self):
        """NewsletterIssue should auto-set generated_at timestamp."""
        issue = NewsletterIssue(date="2025-01-15")
        assert issue.generated_at != ""

    def test_auto_calculates_total_items(self, sample_content_items):
        """NewsletterIssue should auto-calculate total_items."""
        sections = [
            NewsletterSection(id="sec1", title="Section 1", items=sample_content_items[:2]),
            NewsletterSection(id="sec2", title="Section 2", items=sample_content_items[2:4]),
        ]
        issue = NewsletterIssue(date="2025-01-15", sections=sections)
        assert issue.total_items == 4

    def test_active_sections_filters_empty(self, sample_content_items):
        """active_sections should filter out empty sections."""
        sections = [
            NewsletterSection(id="full", title="Full", items=sample_content_items[:2]),
            NewsletterSection(id="empty", title="Empty"),
            NewsletterSection(id="html", title="HTML", content_html="<p>Content</p>"),
        ]
        issue = NewsletterIssue(date="2025-01-15", sections=sections)

        active = issue.active_sections
        assert len(active) == 2
        assert active[0].id == "full"
        assert active[1].id == "html"

    def test_preserves_explicit_total_items(self, sample_content_items):
        """NewsletterIssue should preserve explicitly set total_items."""
        sections = [
            NewsletterSection(id="sec1", title="Section 1", items=sample_content_items[:2]),
        ]
        issue = NewsletterIssue(date="2025-01-15", sections=sections, total_items=100)
        # If total_items is explicitly set to non-zero, it should be preserved
        # Based on the code, __post_init__ only sets if not self.total_items
        assert issue.total_items == 100
