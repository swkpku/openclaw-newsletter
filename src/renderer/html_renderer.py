"""Renders newsletter issues to static HTML using Jinja2."""

import logging
import os

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

    def render_issue(self, issue: NewsletterIssue) -> str:
        """Render a newsletter issue to HTML and save to docs/issues/."""
        template = self.env.get_template("newsletter.html")
        html = template.render(issue=issue, date=issue.date)

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
        html = template.render(latest_issue=latest_issue_filename)

        filepath = os.path.join(self.config.docs_dir, "index.html")
        with open(filepath, "w") as f:
            f.write(html)

        logger.info(f"Rendered index page to {filepath}")
