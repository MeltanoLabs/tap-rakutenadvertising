"""REST client handling, including RakutenAdvertisingStream base class."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

import xmltodict
from singer_sdk.authenticators import BearerTokenAuthenticator
from singer_sdk.pagination import BaseHATEOASPaginator, BasePageNumberPaginator
from singer_sdk.streams import RESTStream

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

if TYPE_CHECKING:
    from collections.abc import Callable

    import requests
    from singer_sdk.helpers.types import Context


class RakutenPaginator(BaseHATEOASPaginator):
    """Paginator for Rakuten APIs that use _metadata._links.next."""

    @override
    def get_next_url(self, response: requests.Response) -> str | None:
        data = response.json()
        return data.get("_metadata", {}).get("_links", {}).get("next")


class EventsPaginator(BasePageNumberPaginator):
    """Paginator for the Events API which returns a flat JSON array."""

    def __init__(self, page_size: int, *args: Any, **kwargs: Any) -> None:
        """Initialize the paginator with a page size limit."""
        kwargs.setdefault("start_value", 1)
        super().__init__(*args, **kwargs)
        self._page_size = page_size

    def has_more(self, response: requests.Response) -> bool:
        """If the response has as many records as the limit, there may be more."""
        data = response.json()
        return len(data) >= self._page_size


class XMLPagePaginator(BasePageNumberPaginator):
    """Paginator for XML endpoints that include TotalPages in their response."""

    def __init__(
        self,
        current_page_key: str = "PageNumber",
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize the paginator with the XML key used to track the current page."""
        kwargs.setdefault("start_value", 1)
        super().__init__(*args, **kwargs)
        self._current_page_key = current_page_key

    def has_more(self, response: requests.Response) -> bool:
        """Check if there are more pages by comparing current page to total pages."""
        data = xmltodict.parse(response.text)
        root = next(iter(data.values()))
        if not root:
            return False
        total_pages = int(root.get("TotalPages", -1))
        current_page = int(root.get(self._current_page_key, 1))
        return current_page < total_pages


class LinkLocatorPaginator(BasePageNumberPaginator):
    """Paginator for Link Locator XML endpoints with path-based pagination."""

    def __init__(
        self,
        response_key: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize the paginator with the XML key used to find response items."""
        kwargs.setdefault("start_value", 1)
        super().__init__(*args, **kwargs)
        self._response_key = response_key

    def has_more(self, response: requests.Response) -> bool:
        """Check if there are more pages by looking for ns1:return items."""
        data = xmltodict.parse(response.text)
        root = next(iter(data.values()))
        if not root:
            return False
        response_items = root.get(self._response_key, {})
        if isinstance(response_items, dict):
            response_items = [response_items]
        if not response_items:
            return False
        return any("ns1:return" in item for item in response_items)


class RakutenAdvertisingStream(RESTStream):
    """RakutenAdvertising stream class."""

    records_jsonpath = "$[*]"

    @override
    @property
    def url_base(self) -> str:
        """Return the API URL root, configurable via tap settings."""
        return self.config.get("api_url", "https://api.linksynergy.com")

    @override
    @property
    def authenticator(self) -> BearerTokenAuthenticator:
        """Return a new authenticator object."""
        return BearerTokenAuthenticator(token=self.config.get("auth_token", ""))


class RakutenXMLStream(RakutenAdvertisingStream):
    """Base class for legacy XML endpoints that require token as a query parameter."""

    @override
    @property
    def authenticator(self) -> Callable:  # type: ignore[override]
        """No Bearer auth; legacy XML endpoints require the token as a query param."""
        return lambda r: r

    @override
    def get_url_params(
        self,
        context: Context | None,
        next_page_token: Any | None,
    ) -> dict[str, Any]:
        return {"token": self.config["auth_token"]}
