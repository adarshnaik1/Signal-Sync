"""
Marketaux API client for fetching financial news articles.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

import requests

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.helpers import get_api_key, published_after_date, validate_api_response


BASE_URL = "https://api.marketaux.com/v1/news/all"
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2


class MarketauxAPIError(Exception):
    """Raised when Marketaux API returns an error response."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class MarketauxClient:
    """
    Lightweight client for the Marketaux news API.
    Handles query building, retries, and rate-limit responses.
    """

    def __init__(self, api_token: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize the client.

        Args:
            api_token: Optional API token; loads from env if omitted.
            timeout: Request timeout in seconds.
        """
        self.api_token = api_token or get_api_key()
        self.timeout = timeout
        self.session = requests.Session()

    def build_params(
        self,
        symbol: str,
        limit: int = 50,
        days: int = 7,
        language: str = "en",
        filter_entities: bool = True,
    ) -> Dict[str, Any]:
        """Build query parameters for the news/all endpoint."""
        return {
            "api_token": self.api_token,
            "symbols": symbol.strip().upper(),
            "language": language,
            "filter_entities": str(filter_entities).lower(),
            "limit": max(1, min(limit, 100)),
            "published_after": published_after_date(days),
        }

    def fetch_news(
        self,
        symbol: str,
        limit: int = 50,
        days: int = 7,
        language: str = "en",
        filter_entities: bool = True,
    ) -> Dict[str, Any]:
        """
        Fetch company-related financial news from Marketaux.

        Args:
            symbol: Stock symbol (e.g. RELIANCE.NS).
            limit: Maximum number of articles.
            days: Lookback window in days.
            language: Article language filter.
            filter_entities: Whether to filter by matched entities.

        Returns:
            Parsed JSON response including meta and data.

        Raises:
            MarketauxAPIError: On HTTP or API-level failures.
            ValueError: On invalid configuration.
        """
        if not symbol or not symbol.strip():
            raise ValueError("Stock symbol is required.")

        params = self.build_params(symbol, limit, days, language, filter_entities)
        return self._request_with_retry(params)

    def _request_with_retry(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute GET request with retry on rate limits and transient errors."""
        last_error: Optional[Exception] = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.session.get(
                    BASE_URL,
                    params=params,
                    timeout=self.timeout,
                )
                return self._handle_response(response)
            except MarketauxAPIError as exc:
                last_error = exc
                if exc.status_code == 429 and attempt < MAX_RETRIES:
                    wait = RETRY_BACKOFF_SECONDS * attempt
                    time.sleep(wait)
                    continue
                raise
            except requests.RequestException as exc:
                last_error = exc
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_SECONDS * attempt)
                    continue
                raise MarketauxAPIError(f"Network error: {exc}") from exc

        raise MarketauxAPIError(f"Request failed after retries: {last_error}")

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Parse HTTP response and raise on errors."""
        status = response.status_code

        try:
            payload = response.json()
        except ValueError as exc:
            raise MarketauxAPIError(
                f"Invalid JSON response (HTTP {status}).",
                status_code=status,
            ) from exc

        if status == 401:
            raise MarketauxAPIError(
                "Unauthorized: invalid or missing API token.",
                status_code=status,
            )
        if status == 429:
            raise MarketauxAPIError(
                "Rate limit exceeded. Please wait and try again.",
                status_code=status,
            )
        if status >= 400:
            message = payload.get("error", {}).get("message", response.text[:200])
            raise MarketauxAPIError(
                f"API request failed (HTTP {status}): {message}",
                status_code=status,
            )

        validate_api_response(payload)
        return payload
