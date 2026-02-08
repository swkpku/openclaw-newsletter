"""Builds the RSS feed from existing issue files."""

import logging
import os
import re
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from src.config import Config

logger = logging.getLogger(__name__)


class RSSBuilder:
    """Builds an RSS 2.0 feed from published issues."""

    def __init__(self, config: Config):
        self.config = config
        self.env = Environment(
            loader=FileSystemLoader(config.templates_dir),
            autoescape=False,
        )

    def build(self) -> None:
        """Scan docs/issues/ and render the RSS feed."""
        issues = self._scan_issues()
        template = self.env.get_template("rss.xml")
        xml = template.render(issues=issues, site_url=self.config.site_url)

        filepath = os.path.join(self.config.docs_dir, "rss.xml")
        with open(filepath, "w") as f:
            f.write(xml)

        logger.info(f"Built RSS feed with {len(issues)} issues.")

    def _scan_issues(self) -> list[dict]:
        """Scan the issues directory for HTML files (max 20)."""
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
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            entries.append(
                {
                    "filename": filename,
                    "date": date_str,
                    "pub_date": dt.strftime("%a, %d %b %Y 00:00:00 +0000"),
                }
            )
            if len(entries) >= 20:
                break

        return entries
