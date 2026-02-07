"""Base collector with shared HTTP client, retry logic, and error handling."""

import logging
import time
from abc import ABC, abstractmethod

import requests

from src.config import Config
from src.models.data_models import CollectorResult, ContentItem
from src.state.state_manager import StateManager

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Abstract base class for all content collectors."""

    name: str = "base"

    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "OpenClawNewsletter/1.0"})

    def is_available(self) -> bool:
        """Override to return False if required API keys are missing."""
        return True

    @abstractmethod
    def collect(self, state: StateManager) -> list[ContentItem]:
        """Fetch new content items, filtering out already-covered ones."""
        ...

    def run(self, state: StateManager) -> CollectorResult:
        """Execute the collector with error handling."""
        if not self.is_available():
            logger.info(f"[{self.name}] Skipped (missing API key or unavailable).")
            return CollectorResult(collector_name=self.name, skipped=True)
        try:
            items = self.collect(state)
            logger.info(f"[{self.name}] Collected {len(items)} new items.")
            return CollectorResult(collector_name=self.name, items=items)
        except Exception as e:
            logger.warning(f"[{self.name}] Failed: {e}")
            return CollectorResult(collector_name=self.name, error=str(e))

    @staticmethod
    def _is_retryable(exc: requests.RequestException) -> bool:
        """Return True if the error is transient and worth retrying."""
        if isinstance(exc, (requests.ConnectionError, requests.Timeout)):
            return True
        if isinstance(exc, requests.HTTPError) and exc.response is not None:
            return exc.response.status_code >= 500
        return False

    def _get(self, url: str, **kwargs) -> requests.Response:
        """HTTP GET with retry and timeout. Only retries on 5xx/connection errors."""
        kwargs.setdefault("timeout", self.config.request_timeout)
        last_exc = None
        for attempt in range(self.config.max_retries):
            try:
                resp = self.session.get(url, **kwargs)
                resp.raise_for_status()
                return resp
            except requests.RequestException as e:
                last_exc = e
                if not self._is_retryable(e) or attempt >= self.config.max_retries - 1:
                    break
                wait = self.config.retry_backoff_factor ** attempt
                logger.warning(
                    f"[{self.name}] Retry {attempt + 1}/{self.config.max_retries} "
                    f"for {url} in {wait}s: {e}"
                )
                time.sleep(wait)
        raise last_exc  # type: ignore[misc]

    def _post(self, url: str, **kwargs) -> requests.Response:
        """HTTP POST with retry and timeout. Only retries on 5xx/connection errors."""
        kwargs.setdefault("timeout", self.config.request_timeout)
        last_exc = None
        for attempt in range(self.config.max_retries):
            try:
                resp = self.session.post(url, **kwargs)
                resp.raise_for_status()
                return resp
            except requests.RequestException as e:
                last_exc = e
                if not self._is_retryable(e) or attempt >= self.config.max_retries - 1:
                    break
                wait = self.config.retry_backoff_factor ** attempt
                logger.warning(
                    f"[{self.name}] Retry {attempt + 1}/{self.config.max_retries} "
                    f"for {url} in {wait}s: {e}"
                )
                time.sleep(wait)
        raise last_exc  # type: ignore[misc]

    def _graphql(self, query: str, variables: dict | None = None) -> dict:
        """Execute a GitHub GraphQL query."""
        headers = {"Authorization": f"Bearer {self.config.github_token}"}
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        resp = self._post(
            "https://api.github.com/graphql",
            json=payload,
            headers=headers,
        )
        data = resp.json()
        if "errors" in data:
            raise RuntimeError(f"GraphQL errors: {data['errors']}")
        return data["data"]
