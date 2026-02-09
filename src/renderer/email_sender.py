"""Sends newsletter issues as emails via the Buttondown API."""

import logging
import os
from datetime import datetime

import requests
from jinja2 import Environment, FileSystemLoader

from src.config import Config
from src.models.data_models import NewsletterIssue

logger = logging.getLogger(__name__)

BUTTONDOWN_API_URL = "https://api.buttondown.com/v1/emails"


class EmailSender:
    """Sends a newsletter issue to subscribers via Buttondown."""

    def __init__(self, config: Config):
        self.config = config
        self.env = Environment(
            loader=FileSystemLoader(config.templates_dir),
            autoescape=False,
        )

    def is_available(self) -> bool:
        return bool(self.config.buttondown_api_key)

    @staticmethod
    def _format_date(iso_date: str) -> str:
        """Convert ISO date like '2026-02-07' to 'Friday, February 7, 2026'."""
        try:
            dt = datetime.strptime(iso_date, "%Y-%m-%d")
            return dt.strftime("%A, %B %-d, %Y")
        except (ValueError, TypeError):
            return iso_date

    def _render_email_html(self, issue: NewsletterIssue) -> str:
        """Render the email-specific template with inlined styles."""
        template = self.env.get_template("email.html")
        return template.render(
            issue=issue,
            date=self._format_date(issue.date),
            site_url=self.config.site_url,
        )

    def send(self, issue: NewsletterIssue, issue_filename: str) -> bool:
        """Send the newsletter issue as an email to all subscribers.

        Args:
            issue: The assembled newsletter issue.
            issue_filename: Filename of the rendered HTML (e.g. '2026-02-08.html').

        Returns:
            True if the email was sent successfully, False otherwise.
        """
        if not self.is_available():
            logger.warning("BUTTONDOWN_API_KEY not set; skipping email send")
            return False

        html_body = self._render_email_html(issue)

        subject = f"OpenClaw Newsletter - {issue.date}"

        headers = {
            "Authorization": f"Token {self.config.buttondown_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "subject": subject,
            "body": html_body,
            "status": "about_to_send",
        }

        try:
            resp = requests.post(
                BUTTONDOWN_API_URL,
                headers=headers,
                json=payload,
                timeout=self.config.request_timeout,
            )
            resp.raise_for_status()
            logger.info("Email sent successfully for %s", issue.date)
            return True
        except requests.RequestException:
            logger.exception("Failed to send email for %s", issue.date)
            return False
