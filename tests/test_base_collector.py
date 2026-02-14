"""Tests for BaseCollector class."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.collectors.base import BaseCollector
from src.config import Config
from src.models.data_models import ContentItem
from src.state.state_manager import StateManager


class ConcreteCollector(BaseCollector):
    """Concrete implementation of BaseCollector for testing."""

    name = "test_collector"

    def __init__(self, config: Config, items_to_return: list = None, should_raise: bool = False):
        super().__init__(config)
        self._items_to_return = items_to_return or []
        self._should_raise = should_raise

    def collect(self, state: StateManager) -> list[ContentItem]:
        if self._should_raise:
            raise RuntimeError("Test error")
        return self._items_to_return


class UnavailableCollector(BaseCollector):
    """Collector that's unavailable (missing API key)."""

    name = "unavailable_collector"

    def is_available(self) -> bool:
        return False

    def collect(self, state: StateManager) -> list[ContentItem]:
        return []


class TestBaseCollectorInit:
    """Tests for BaseCollector initialization."""

    def test_init_creates_session(self, sample_config):
        """BaseCollector should create a requests session."""
        collector = ConcreteCollector(sample_config)
        assert collector.session is not None
        assert collector.session.headers["User-Agent"] == "OpenClawNewsletter/1.0"

    def test_init_stores_config(self, sample_config):
        """BaseCollector should store the config."""
        collector = ConcreteCollector(sample_config)
        assert collector.config is sample_config


class TestBaseCollectorIsAvailable:
    """Tests for is_available method."""

    def test_default_is_available_returns_true(self, sample_config):
        """Default is_available should return True."""
        collector = ConcreteCollector(sample_config)
        assert collector.is_available() is True

    def test_unavailable_collector(self, sample_config):
        """Unavailable collector should return False."""
        collector = UnavailableCollector(sample_config)
        assert collector.is_available() is False


class TestBaseCollectorRun:
    """Tests for run method."""

    def test_run_returns_items_on_success(self, sample_config, sample_content_items, state_file):
        """run should return CollectorResult with items on success."""
        collector = ConcreteCollector(sample_config, items_to_return=sample_content_items)
        state = StateManager(state_file)

        result = collector.run(state)

        assert result.collector_name == "test_collector"
        assert len(result.items) == 5
        assert result.error is None
        assert result.skipped is False

    def test_run_returns_error_on_exception(self, sample_config, state_file):
        """run should return CollectorResult with error on exception."""
        collector = ConcreteCollector(sample_config, should_raise=True)
        state = StateManager(state_file)

        result = collector.run(state)

        assert result.collector_name == "test_collector"
        assert result.items == []
        assert result.error == "Test error"
        assert result.skipped is False

    def test_run_skips_unavailable_collector(self, sample_config, state_file):
        """run should skip unavailable collectors."""
        collector = UnavailableCollector(sample_config)
        state = StateManager(state_file)

        result = collector.run(state)

        assert result.collector_name == "unavailable_collector"
        assert result.skipped is True
        assert result.items == []


class TestBaseCollectorIsRetryable:
    """Tests for _is_retryable static method."""

    def test_connection_error_is_retryable(self):
        """ConnectionError should be retryable."""
        exc = requests.ConnectionError("Connection failed")
        assert BaseCollector._is_retryable(exc) is True

    def test_timeout_is_retryable(self):
        """Timeout should be retryable."""
        exc = requests.Timeout("Request timed out")
        assert BaseCollector._is_retryable(exc) is True

    def test_5xx_http_error_is_retryable(self):
        """5xx HTTP errors should be retryable."""
        response = MagicMock()
        response.status_code = 500
        exc = requests.HTTPError(response=response)
        assert BaseCollector._is_retryable(exc) is True

        response.status_code = 503
        exc = requests.HTTPError(response=response)
        assert BaseCollector._is_retryable(exc) is True

    def test_4xx_http_error_not_retryable(self):
        """4xx HTTP errors should not be retryable."""
        response = MagicMock()
        response.status_code = 404
        exc = requests.HTTPError(response=response)
        assert BaseCollector._is_retryable(exc) is False

        response.status_code = 401
        exc = requests.HTTPError(response=response)
        assert BaseCollector._is_retryable(exc) is False

    def test_generic_request_exception_not_retryable(self):
        """Generic RequestException should not be retryable."""
        exc = requests.RequestException("Generic error")
        assert BaseCollector._is_retryable(exc) is False


class TestBaseCollectorGet:
    """Tests for _get method."""

    def test_get_success(self, sample_config):
        """_get should return response on success."""
        collector = ConcreteCollector(sample_config)

        with patch.object(collector.session, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            response = collector._get("https://api.example.com/test")

            assert response is mock_response
            mock_get.assert_called_once()

    def test_get_sets_default_timeout(self, sample_config):
        """_get should set default timeout from config."""
        collector = ConcreteCollector(sample_config)

        with patch.object(collector.session, "get") as mock_get:
            mock_response = MagicMock()
            mock_get.return_value = mock_response

            collector._get("https://api.example.com/test")

            call_kwargs = mock_get.call_args[1]
            assert call_kwargs["timeout"] == sample_config.request_timeout

    def test_get_retries_on_transient_error(self, sample_config):
        """_get should retry on transient errors."""
        collector = ConcreteCollector(sample_config)

        with patch.object(collector.session, "get") as mock_get:
            # First call fails, second succeeds
            mock_response = MagicMock()
            mock_get.side_effect = [
                requests.ConnectionError("Connection failed"),
                mock_response,
            ]

            with patch("time.sleep"):  # Speed up test
                response = collector._get("https://api.example.com/test")

            assert response is mock_response
            assert mock_get.call_count == 2

    def test_get_raises_after_max_retries(self, sample_config):
        """_get should raise after max retries exceeded."""
        collector = ConcreteCollector(sample_config)

        with patch.object(collector.session, "get") as mock_get:
            mock_get.side_effect = requests.ConnectionError("Connection failed")

            with patch("time.sleep"):  # Speed up test
                with pytest.raises(requests.ConnectionError):
                    collector._get("https://api.example.com/test")

            # Should have tried max_retries times
            assert mock_get.call_count == sample_config.max_retries

    def test_get_does_not_retry_4xx_errors(self, sample_config):
        """_get should not retry 4xx errors."""
        collector = ConcreteCollector(sample_config)

        with patch.object(collector.session, "get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = requests.HTTPError(response=mock_response)
            mock_get.return_value = mock_response

            with pytest.raises(requests.HTTPError):
                collector._get("https://api.example.com/test")

            # Should only try once (no retries)
            assert mock_get.call_count == 1


class TestBaseCollectorPost:
    """Tests for _post method."""

    def test_post_success(self, sample_config):
        """_post should return response on success."""
        collector = ConcreteCollector(sample_config)

        with patch.object(collector.session, "post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            response = collector._post(
                "https://api.example.com/test",
                json={"key": "value"},
            )

            assert response is mock_response
            mock_post.assert_called_once()

    def test_post_retries_on_5xx(self, sample_config):
        """_post should retry on 5xx errors."""
        collector = ConcreteCollector(sample_config)

        with patch.object(collector.session, "post") as mock_post:
            mock_fail_response = MagicMock()
            mock_fail_response.status_code = 500
            mock_fail_response.raise_for_status.side_effect = requests.HTTPError(
                response=mock_fail_response
            )

            mock_success_response = MagicMock()
            mock_success_response.status_code = 200

            mock_post.side_effect = [
                mock_fail_response,
                mock_success_response,
            ]

            with patch("time.sleep"):
                response = collector._post("https://api.example.com/test")

            assert response is mock_success_response
            assert mock_post.call_count == 2


class TestBaseCollectorGraphQL:
    """Tests for _graphql method."""

    def test_graphql_success(self, sample_config):
        """_graphql should execute query and return data."""
        collector = ConcreteCollector(sample_config)

        with patch.object(collector, "_post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "data": {"repository": {"name": "openclaw"}},
            }
            mock_post.return_value = mock_response

            result = collector._graphql(
                "query { repository(owner: $owner, name: $name) { name } }",
                variables={"owner": "openclaw", "name": "openclaw"},
            )

            assert result == {"repository": {"name": "openclaw"}}

    def test_graphql_raises_on_errors(self, sample_config):
        """_graphql should raise RuntimeError on GraphQL errors."""
        collector = ConcreteCollector(sample_config)

        with patch.object(collector, "_post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "errors": [{"message": "Not found"}],
            }
            mock_post.return_value = mock_response

            with pytest.raises(RuntimeError, match="GraphQL errors"):
                collector._graphql("query { invalid }")

    def test_graphql_includes_auth_header(self, sample_config):
        """_graphql should include Authorization header."""
        collector = ConcreteCollector(sample_config)

        with patch.object(collector, "_post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = {"data": {}}
            mock_post.return_value = mock_response

            collector._graphql("query { viewer { login } }")

            call_kwargs = mock_post.call_args[1]
            assert "headers" in call_kwargs
            assert "Authorization" in call_kwargs["headers"]
            assert call_kwargs["headers"]["Authorization"] == f"Bearer {sample_config.github_token}"
