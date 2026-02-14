"""Tests for AIWriter class."""

from unittest.mock import MagicMock, patch

import pytest

from src.config import Config
from src.generator.ai_writer import AIWriter
from src.models.data_models import ContentItem


@pytest.fixture
def config_with_key():
    """Config with Anthropic API key."""
    return Config(anthropic_api_key="test-api-key")


@pytest.fixture
def config_without_key():
    """Config without Anthropic API key."""
    return Config(anthropic_api_key="")


@pytest.fixture
def items_with_engagement():
    """Content items with varying engagement levels."""
    return [
        ContentItem(
            id="trending-item",
            source="twitter",
            title="Trending Post",
            url="https://example.com/trending",
            description="This is trending",
            metadata={"like_count": 150, "retweet_count": 50},
        ),
        ContentItem(
            id="hot-item",
            source="hackernews",
            title="Hot Post",
            url="https://example.com/hot",
            description="This is hot",
            metadata={"points": 50, "num_comments": 10},
        ),
        ContentItem(
            id="normal-item",
            source="blog",
            title="Normal Post",
            url="https://example.com/normal",
            description="This is normal",
            metadata={"likes": 5},
        ),
    ]


class TestAIWriterInit:
    """Tests for AIWriter initialization."""

    def test_init_without_key(self, config_without_key):
        """AIWriter should initialize without API key but be unavailable."""
        writer = AIWriter(config_without_key)
        assert writer.client is None
        assert writer.is_available() is False

    def test_init_with_key_but_no_anthropic_package(self, config_with_key):
        """AIWriter should handle missing anthropic package gracefully."""
        with patch.dict("sys.modules", {"anthropic": None}):
            with patch("builtins.__import__", side_effect=ImportError):
                writer = AIWriter(config_with_key)
                assert writer.client is None


class TestAIWriterIsAvailable:
    """Tests for is_available method."""

    def test_unavailable_without_client(self, config_without_key):
        """is_available should return False without client."""
        writer = AIWriter(config_without_key)
        assert writer.is_available() is False


class TestAIWriterFixTruncatedHtml:
    """Tests for _fix_truncated_html static method."""

    def test_converts_markdown_bold(self):
        """Should convert **text** to <strong>text</strong>."""
        html = "This is **bold** text"
        result = AIWriter._fix_truncated_html(html)
        assert result == "This is <strong>bold</strong> text"

    def test_converts_markdown_links(self):
        """Should convert [text](url) to <a href>."""
        html = "Check out [this link](https://example.com)"
        result = AIWriter._fix_truncated_html(html)
        assert result == 'Check out <a href="https://example.com">this link</a>'

    def test_closes_unclosed_strong_tags(self):
        """Should close unclosed <strong> tags."""
        html = "<strong>Bold text without closing"
        result = AIWriter._fix_truncated_html(html)
        assert result.endswith("</strong>")

    def test_closes_unclosed_anchor_tags(self):
        """Should close unclosed <a> tags."""
        html = '<a href="url">Link text without closing'
        result = AIWriter._fix_truncated_html(html)
        assert result.endswith("</a>")

    def test_closes_unclosed_list_items(self):
        """Should close unclosed <li> tags."""
        html = "<ul><li>Item 1<li>Item 2"
        result = AIWriter._fix_truncated_html(html)
        assert result.count("</li>") == 2

    def test_closes_unclosed_ul_tags(self):
        """Should close unclosed <ul> tags."""
        html = "<ul><li>Item 1</li>"
        result = AIWriter._fix_truncated_html(html)
        assert result.endswith("</ul>")

    def test_handles_already_valid_html(self):
        """Should not modify already valid HTML."""
        html = "<ul><li>Item</li></ul>"
        result = AIWriter._fix_truncated_html(html)
        assert result == html


class TestAIWriterEngagementScore:
    """Tests for _engagement_score static method."""

    def test_empty_metadata(self):
        """Should return 0 for empty metadata."""
        item = ContentItem(id="test", source="test", title="Test")
        score = AIWriter._engagement_score(item)
        assert score == 0

    def test_like_count(self):
        """Should count likes."""
        item = ContentItem(
            id="test", source="test", title="Test",
            metadata={"like_count": 10},
        )
        score = AIWriter._engagement_score(item)
        assert score == 10

    def test_retweet_count_weighted(self):
        """Should weight retweets at 2x."""
        item = ContentItem(
            id="test", source="test", title="Test",
            metadata={"retweet_count": 10},
        )
        score = AIWriter._engagement_score(item)
        assert score == 20

    def test_comments_weighted(self):
        """Should weight comments at 2x."""
        item = ContentItem(
            id="test", source="test", title="Test",
            metadata={"num_comments": 10},
        )
        score = AIWriter._engagement_score(item)
        assert score == 20

    def test_combined_engagement(self, items_with_engagement):
        """Should combine multiple engagement signals."""
        trending = items_with_engagement[0]
        score = AIWriter._engagement_score(trending)
        # 150 likes + 50*2 retweets = 250
        assert score == 250

    def test_hackernews_points_and_comments(self, items_with_engagement):
        """Should count HN points and comments."""
        hot = items_with_engagement[1]
        score = AIWriter._engagement_score(hot)
        # 50 points + 10*2 comments = 70
        assert score == 70


class TestAIWriterCleanDescription:
    """Tests for _clean_description static method."""

    def test_empty_description(self):
        """Should handle empty descriptions."""
        assert AIWriter._clean_description("") == ""
        assert AIWriter._clean_description(None) == ""

    def test_strips_html_comments(self):
        """Should strip HTML comments."""
        text = "Text <!-- comment --> more text"
        result = AIWriter._clean_description(text)
        assert "<!--" not in result
        assert "comment" not in result

    def test_strips_html_tags(self):
        """Should strip HTML tags."""
        text = "<p>Paragraph</p> <strong>bold</strong>"
        result = AIWriter._clean_description(text)
        assert "<p>" not in result
        assert "<strong>" not in result
        assert "Paragraph" in result
        assert "bold" in result

    def test_strips_markdown_headings(self):
        """Should strip markdown headings."""
        text = "### Heading\nContent"
        result = AIWriter._clean_description(text)
        assert "###" not in result
        assert "Heading" in result

    def test_strips_markdown_bold(self):
        """Should strip markdown bold markers."""
        text = "This is **bold** text"
        result = AIWriter._clean_description(text)
        assert "**" not in result
        assert "bold" in result

    def test_strips_markdown_links(self):
        """Should convert markdown links to text."""
        text = "Check [this link](https://example.com)"
        result = AIWriter._clean_description(text)
        assert "[" not in result
        assert "https" not in result
        assert "this link" in result

    def test_strips_markdown_images(self):
        """Should strip markdown image syntax (URL removed)."""
        text = "Image: ![alt text](https://example.com/img.png)"
        result = AIWriter._clean_description(text)
        # The URL and markdown syntax should be stripped
        assert "https://example.com" not in result
        assert "](https" not in result

    def test_strips_code_fences(self):
        """Should strip code fences."""
        text = "Code:\n```python\nprint('hello')\n```\nMore text"
        result = AIWriter._clean_description(text)
        assert "```" not in result

    def test_strips_inline_code(self):
        """Should strip inline code backticks."""
        text = "Use the `command` function"
        result = AIWriter._clean_description(text)
        assert "`" not in result
        assert "command" in result

    def test_truncates_long_descriptions(self):
        """Should truncate descriptions over 200 chars."""
        text = "a" * 300
        result = AIWriter._clean_description(text)
        assert len(result) <= 203  # 200 + "..."
        assert result.endswith("...")

    def test_collapses_whitespace(self):
        """Should collapse multiple whitespace."""
        text = "Text  with    multiple   spaces"
        result = AIWriter._clean_description(text)
        assert "  " not in result


class TestAIWriterFormatItems:
    """Tests for _format_items method."""

    def test_formats_items_for_prompt(self, config_without_key, items_with_engagement):
        """Should format items as text for AI prompt."""
        writer = AIWriter(config_without_key)
        result = writer._format_items(items_with_engagement)

        assert "Trending Post" in result
        assert "Hot Post" in result
        assert "Normal Post" in result

    def test_sorts_by_engagement(self, config_without_key, items_with_engagement):
        """Should sort items by engagement score (highest first)."""
        writer = AIWriter(config_without_key)
        result = writer._format_items(items_with_engagement)

        # Trending (250) should appear before Hot (70) which should appear before Normal (5)
        trending_pos = result.find("Trending Post")
        hot_pos = result.find("Hot Post")
        normal_pos = result.find("Normal Post")

        assert trending_pos < hot_pos < normal_pos

    def test_adds_trending_label(self, config_without_key, items_with_engagement):
        """Should add [TRENDING] label for engagement >= 100."""
        writer = AIWriter(config_without_key)
        result = writer._format_items(items_with_engagement)

        assert "[TRENDING]" in result

    def test_adds_hot_label(self, config_without_key, items_with_engagement):
        """Should add [HOT] label for engagement >= 30."""
        writer = AIWriter(config_without_key)
        result = writer._format_items(items_with_engagement)

        assert "[HOT]" in result

    def test_includes_url(self, config_without_key, items_with_engagement):
        """Should include URL in formatted output."""
        writer = AIWriter(config_without_key)
        result = writer._format_items(items_with_engagement)

        assert "https://example.com/trending" in result


class TestAIWriterFallbackHtml:
    """Tests for _fallback_html method."""

    def test_empty_items(self, config_without_key):
        """Should return empty string for no items."""
        writer = AIWriter(config_without_key)
        result = writer._fallback_html([])
        assert result == ""

    def test_generates_list_html(self, config_without_key, sample_content_items):
        """Should generate <ul> list HTML."""
        writer = AIWriter(config_without_key)
        result = writer._fallback_html(sample_content_items)

        assert result.startswith("<ul>")
        assert result.endswith("</ul>")
        assert "<li>" in result

    def test_creates_links_for_urls(self, config_without_key, sample_content_items):
        """Should create <a> tags for items with URLs."""
        writer = AIWriter(config_without_key)
        result = writer._fallback_html(sample_content_items)

        assert '<a href="' in result
        assert "</a>" in result

    def test_handles_items_without_urls(self, config_without_key):
        """Should handle items without URLs gracefully."""
        items = [
            ContentItem(id="no-url", source="test", title="No URL Item"),
        ]
        writer = AIWriter(config_without_key)
        result = writer._fallback_html(items)

        assert "No URL Item" in result
        assert '<a href="">' not in result

    def test_escapes_html_in_titles(self, config_without_key):
        """Should escape HTML special chars in titles."""
        items = [
            ContentItem(
                id="html-title",
                source="test",
                title="Title with <script> & special chars",
                url="https://example.com",
            ),
        ]
        writer = AIWriter(config_without_key)
        result = writer._fallback_html(items)

        assert "&lt;script&gt;" in result
        assert "&amp;" in result

    def test_includes_cleaned_description(self, config_without_key):
        """Should include cleaned descriptions."""
        items = [
            ContentItem(
                id="desc-item",
                source="test",
                title="Item",
                url="https://example.com",
                description="This is a **markdown** description",
            ),
        ]
        writer = AIWriter(config_without_key)
        result = writer._fallback_html(items)

        assert "markdown" in result
        assert "**" not in result


class TestAIWriterGenerateSection:
    """Tests for generate_section method."""

    def test_returns_empty_for_no_items(self, config_without_key):
        """Should return empty string for no items."""
        writer = AIWriter(config_without_key)
        result = writer.generate_section("releases", [])
        assert result == ""

    def test_uses_fallback_when_no_prompt_template(self, config_without_key, sample_content_items):
        """Should use fallback HTML when no prompt template exists."""
        writer = AIWriter(config_without_key)
        result = writer.generate_section("nonexistent_section", sample_content_items)

        assert "<ul>" in result
        assert "<li>" in result

    def test_uses_fallback_when_unavailable(self, config_without_key, sample_content_items):
        """Should use fallback HTML when AI is unavailable."""
        writer = AIWriter(config_without_key)
        result = writer.generate_section("releases", sample_content_items)

        assert "<ul>" in result
        assert "<li>" in result
