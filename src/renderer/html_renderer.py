"""Renders newsletter issues to static HTML using Jinja2."""

import logging
import os
import re
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from src.config import Config
from src.models.data_models import NewsletterIssue

logger = logging.getLogger(__name__)


class HTMLRenderer:
    """Renders NewsletterIssue objects to HTML files."""

    def __init__(self, config: Config):
        self.config = config
        self.env = Environment(
            loader=FileSystemLoader(config.templates_dir),
            autoescape=False,
        )

    @staticmethod
    def _format_date(iso_date: str) -> str:
        """Convert ISO date like '2026-02-07' to 'Friday, February 7, 2026'."""
        try:
            dt = datetime.strptime(iso_date, "%Y-%m-%d")
            return dt.strftime("%A, %B %-d, %Y")
        except (ValueError, TypeError):
            return iso_date

    @staticmethod
    def _make_og_description(issue: "NewsletterIssue") -> str:
        """Extract first ~155 chars of top_stories content, HTML-stripped."""
        for section in issue.sections:
            if section.id == "top_stories" and section.content_html:
                text = re.sub(r"<[^>]+>", "", section.content_html)
                text = re.sub(r"\[TRENDING:\s*\d+\s*engagement\]", "", text)
                text = " ".join(text.split())
                if len(text) > 155:
                    return text[:152] + "..."
                return text
        return "Daily updates from the OpenClaw ecosystem"

    def _common_vars(self) -> dict:
        """Template variables shared across all pages."""
        og_image = f"{self.config.site_url}/assets/og-image.svg" if self.config.site_url else ""
        return {
            "buttondown_username": self.config.buttondown_username,
            "site_url": self.config.site_url,
            "og_image": og_image,
        }

    def render_issue(self, issue: NewsletterIssue) -> str:
        """Render a newsletter issue to HTML and save to docs/issues/."""
        template = self.env.get_template("newsletter.html")

        og_title = f"OpenClaw Newsletter - {issue.date}"
        og_description = self._make_og_description(issue)
        og_url = f"{self.config.site_url}/issues/{issue.date}.html" if self.config.site_url else ""

        html = template.render(
            issue=issue,
            date=self._format_date(issue.date),
            og_title=og_title,
            og_description=og_description,
            og_url=og_url,
            **self._common_vars(),
        )

        os.makedirs(self.config.issues_dir, exist_ok=True)
        filename = f"{issue.date}.html"
        filepath = os.path.join(self.config.issues_dir, filename)

        with open(filepath, "w") as f:
            f.write(html)

        logger.info(f"Rendered issue to {filepath}")
        return filename

    def render_index(self, latest_issue_filename: str | None) -> None:
        """Render the index page with redirect to latest issue."""
        template = self.env.get_template("index.html")
        html = template.render(
            latest_issue=latest_issue_filename,
            og_title="OpenClaw Newsletter",
            og_description="Daily updates from the OpenClaw ecosystem",
            og_url=self.config.site_url or "",
            **self._common_vars(),
        )

        filepath = os.path.join(self.config.docs_dir, "index.html")
        with open(filepath, "w") as f:
            f.write(html)

        logger.info(f"Rendered index page to {filepath}")
