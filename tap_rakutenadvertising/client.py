"""REST client handling, including RakutenAdvertisingStream base class."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from singer_sdk.authenticators import BearerTokenAuthenticator
from singer_sdk.pagination import BasePageNumberPaginator, SinglePagePaginator  # noqa: F401
from singer_sdk.streams import RESTStream

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

if TYPE_CHECKING:
    import requests


class RakutenPaginator(BasePageNumberPaginator):
    """Paginator for Rakuten APIs that use _metadata._links.next."""

    def has_more(self, response: requests.Response) -> bool:
        """Check if there are more pages by looking at _metadata._links.next."""
        data = response.json()
        metadata = data.get("_metadata", {})
        links = metadata.get("_links", {})
        return links.get("next") is not None


class EventsPaginator(BasePageNumberPaginator):
    """Paginator for the Events API which returns a flat JSON array."""

    def __init__(self, start_value: int, page_size: int, *args: Any, **kwargs: Any) -> None:
        super().__init__(start_value, *args, **kwargs)
        self._page_size = page_size

    def has_more(self, response: requests.Response) -> bool:
        """If the response has as many records as the limit, there may be more."""
        data = response.json()
        return len(data) >= self._page_size


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
        return BearerTokenAuthenticator(token=self.config["auth_token"])
