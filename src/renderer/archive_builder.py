"""Builds the archive listing page from existing issue files."""

import logging
import os
import re
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from src.config import Config

logger = logging.getLogger(__name__)


class ArchiveBuilder:
    """Builds the archive listing page."""

    def __init__(self, config: Config):
        self.config = config
        self.env = Environment(
            loader=FileSystemLoader(config.templates_dir),
            autoescape=False,
        )

    def build(self) -> None:
        """Scan docs/issues/ and render the archive page."""
        issues = self._scan_issues()
        template = self.env.get_template("archive.html")
        og_image = f"{self.config.site_url}/assets/og-image.svg" if self.config.site_url else ""
        html = template.render(
            issues=issues,
            buttondown_username=self.config.buttondown_username,
            site_url=self.config.site_url,
            hide_header_subscribe=True,
            og_title="OpenClaw Newsletter - Archive",
            og_description="Browse past issues of the OpenClaw Newsletter",
            og_url=f"{self.config.site_url}/archive.html" if self.config.site_url else "",
            og_image=og_image,
        )

        filepath = os.path.join(self.config.docs_dir, "archive.html")
        with open(filepath, "w") as f:
            f.write(html)

        logger.info(f"Built archive page with {len(issues)} issues.")

    def _scan_issues(self) -> list[dict]:
        """Scan the issues directory for HTML files."""
        issues_dir = self.config.issues_dir
        if not os.path.exists(issues_dir):
            return []

        entries = []
        for filename in sorted(os.listdir(issues_dir), reverse=True):
            if not filename.endswith(".html"):
                continue
            match = re.match(r"(\d{4}-\d{2}-\d{2})\.html", filename)
            if not match:
                continue
            date_str = match.group(1)
            # Count sections by scanning the HTML for section IDs
            filepath = os.path.join(issues_dir, filename)
            section_count, total_items = self._count_sections(filepath)
            display_date = self._format_date(date_str)
            entries.append(
                {
                    "filename": filename,
                    "date": date_str,
                    "display_date": display_date,
                    "section_count": section_count,
                    "total_items": total_items,
                }
            )

        return entries

    def _count_sections(self, filepath: str) -> tuple[int, int]:
        """Count sections and list items in an issue HTML file."""
        try:
            with open(filepath, "r") as f:
                content = f.read()
            section_count = content.count('class="section"')
            total_items = content.count("<li>")
            return section_count, total_items
        except Exception:
            return 0, 0

    @staticmethod
    def _format_date(iso_date: str) -> str:
        """Convert '2026-02-07' to 'February 7, 2026'."""
        try:
            dt = datetime.strptime(iso_date, "%Y-%m-%d")
            return dt.strftime("%B %-d, %Y")
        except (ValueError, TypeError):
            return iso_date

    def get_latest_issue(self) -> str | None:
        """Return the filename of the most recent issue, or None."""
        issues = self._scan_issues()
        if issues:
            return issues[0]["filename"]
        return None
