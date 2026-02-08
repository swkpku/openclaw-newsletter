"""AI writer that uses Claude to generate newsletter section content."""

import logging
import re
from html import escape

from src.config import Config
from src.generator.prompts import SECTION_PROMPTS, SYSTEM_PROMPT
from src.models.data_models import ContentItem

logger = logging.getLogger(__name__)

MAX_DESCRIPTION_LENGTH = 200


class AIWriter:
    """Generates newsletter section HTML using the Claude API."""

    def __init__(self, config: Config):
        self.config = config
        self.client = None
        if config.anthropic_api_key:
            try:
                import anthropic

                self.client = anthropic.Anthropic(api_key=config.anthropic_api_key)
                logger.info("Anthropic client initialized")
            except ImportError:
                logger.warning("anthropic package not installed; AI generation disabled")

    def is_available(self) -> bool:
        """Return True if the Claude API client is configured."""
        return self.client is not None

    def generate_section(self, section_id: str, items: list[ContentItem]) -> str:
        """Generate HTML content for a newsletter section using Claude.

        Falls back to simple HTML list if the API is unavailable or the call fails.
        """
        if not items:
            return ""

        prompt_template = SECTION_PROMPTS.get(section_id)
        if not prompt_template:
            logger.warning("No prompt template for section '%s'; using fallback", section_id)
            return self._fallback_html(items)

        if not self.is_available():
            logger.info("AI unavailable; generating fallback HTML for '%s'", section_id)
            return self._fallback_html(items)

        data_text = self._format_items(items)
        user_prompt = prompt_template.format(data=data_text)

        try:
            response = self.client.messages.create(
                model=self.config.claude_model,
                max_tokens=2500,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )
            content = response.content[0].text
            content = self._fix_truncated_html(content)
            logger.info("Generated AI content for section '%s' (%d chars)", section_id, len(content))
            return content
        except Exception:
            logger.exception("Claude API call failed for section '%s'; using fallback", section_id)
            return self._fallback_html(items)

    @staticmethod
    def _fix_truncated_html(html: str) -> str:
        """Close any unclosed HTML tags left by truncated AI output."""
        closable = ["strong", "a", "li", "ul"]
        for tag in closable:
            open_count = len(re.findall(rf"<{tag}[\s>]", html))
            close_count = len(re.findall(rf"</{tag}>", html))
            for _ in range(open_count - close_count):
                html += f"</{tag}>"
        return html

    @staticmethod
    def _engagement_score(item: ContentItem) -> int:
        """Compute a unified engagement score from varied metadata keys."""
        m = item.metadata
        if not m:
            return 0
        score = 0
        # Social interactions (likes, retweets, shares, upvotes)
        score += m.get("like_count", 0)
        score += m.get("likes", 0)
        score += m.get("retweet_count", 0) * 2
        score += m.get("quote_count", 0)
        score += m.get("shares", 0)
        score += m.get("upvotes", 0)
        # Discussion signals (comments, replies, answers)
        score += m.get("reply_count", 0)
        score += m.get("num_comments", 0) * 2
        score += m.get("comments", 0) * 2
        score += m.get("answer_count", 0) * 2
        # Aggregated scores (Reddit score, HN points, SO score)
        score += m.get("score", 0)
        score += m.get("points", 0)
        return score

    def _format_items(self, items: list[ContentItem]) -> str:
        """Format ContentItems ranked by engagement for the AI prompt."""
        # Sort by engagement so the AI sees trending content first
        ranked = sorted(items, key=self._engagement_score, reverse=True)

        parts: list[str] = []
        for item in ranked:
            eng = self._engagement_score(item)
            label = ""
            if eng >= 100:
                label = " [TRENDING]"
            elif eng >= 30:
                label = " [HOT]"

            lines = [f"- Title: {item.title}{label}"]
            if item.url:
                lines.append(f"  URL: {item.url}")
            if item.description:
                desc = self._clean_description(item.description)
                if desc:
                    lines.append(f"  Description: {desc}")
            if item.author:
                lines.append(f"  Author: {item.author}")
            if item.published_at:
                lines.append(f"  Published: {item.published_at}")
            if eng > 0:
                lines.append(f"  Engagement: {eng}")
            if item.metadata:
                for key, value in item.metadata.items():
                    lines.append(f"  {key}: {value}")
            parts.append("\n".join(lines))
        return "\n\n".join(parts)

    @staticmethod
    def _clean_description(text: str) -> str:
        """Clean and truncate a description for display."""
        if not text:
            return ""
        # Strip HTML comments
        text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
        # Strip HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        # Strip Greptile bot boilerplate
        text = re.sub(
            r"Greptile (?:Overview|Summary|Confidence Score)[^\n]*", "", text
        )
        text = re.sub(r"Context used:.*", "", text, flags=re.DOTALL)
        # Strip markdown headings
        text = re.sub(r"#{1,6}\s+", "", text)
        # Strip markdown bold/italic
        text = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", text)
        # Strip markdown links [text](url) -> text
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        # Strip markdown images ![alt](url)
        text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
        # Strip markdown code fences (matched pairs)
        text = re.sub(r"```[^`]*```", "", text, flags=re.DOTALL)
        # Strip orphaned triple-backtick markers (from truncated fences)
        text = text.replace("```", "")
        # Strip inline code backticks
        text = re.sub(r"`([^`]*)`", r"\1", text)
        # Strip any remaining stray backticks
        text = text.replace("`", "")
        # Strip markdown horizontal rules
        text = re.sub(r"^[-*_]{3,}\s*$", "", text, flags=re.MULTILINE)
        # Strip markdown table rows
        text = re.sub(r"^\|.*\|$", "", text, flags=re.MULTILINE)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        # Take first meaningful chunk
        if len(text) > MAX_DESCRIPTION_LENGTH:
            text = text[:MAX_DESCRIPTION_LENGTH].rsplit(" ", 1)[0] + "..."
        return text

    def _fallback_html(self, items: list[ContentItem]) -> str:
        """Generate a simple HTML list when AI is unavailable."""
        if not items:
            return ""
        html_parts = ["<ul>"]
        for item in items:
            title = escape(item.title)
            if item.url:
                link = f'<a href="{escape(item.url)}">{title}</a>'
            else:
                link = title
            desc_clean = self._clean_description(item.description)
            # Suppress description if it just repeats the title
            if desc_clean and not item.title.startswith(desc_clean[:40]):
                desc = f" &mdash; {escape(desc_clean)}"
            else:
                desc = ""
            html_parts.append(f"  <li>{link}{desc}</li>")
        html_parts.append("</ul>")
        return "\n".join(html_parts)
