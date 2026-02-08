"""Sends newsletter issues as emails via the Buttondown API."""

import logging
import os
import requests

from src.config import Config
from src.models.data_models import NewsletterIssue

logger = logging.getLogger(__name__)

BUTTONDOWN_API_URL = "https://api.buttondown.com/v1/emails"


class EmailSender:
    """Sends a newsletter issue to subscribers via Buttondown."""

    def __init__(self, config: Config):
        self.config = config

    def is_available(self) -> bool:
        return bool(self.config.buttondown_api_key)

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

        # Read the rendered HTML file
        filepath = os.path.join(self.config.issues_dir, issue_filename)
        try:
            with open(filepath) as f:
                html_body = f.read()
        except FileNotFoundError:
            logger.error("Issue file not found: %s", filepath)
            return False

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
