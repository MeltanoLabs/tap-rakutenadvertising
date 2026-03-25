"""Stream type classes for tap-rakutenadvertising."""

from __future__ import annotations

import datetime
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

import xmltodict
from singer_sdk import OpenAPISchema, StreamSchema
from singer_sdk.pagination import SinglePagePaginator

from tap_rakutenadvertising.client import (
    EventsPaginator,
    RakutenAdvertisingStream,
    RakutenPaginator,
)

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

if TYPE_CHECKING:
    from collections.abc import Iterable

    import requests
    from singer_sdk.helpers.types import Context

OPENAPI_SOURCE = OpenAPISchema(Path(__file__).parent / "openapi.json")

EVENTS_PAGE_SIZE = 1000
ADVERTISERS_PAGE_SIZE = 200
PARTNERSHIPS_PAGE_SIZE = 200
PUBLISHER_CONVERSIONS_PAGE_SIZE = 1000


class AdvertisersStream(RakutenAdvertisingStream):
    """Advertisers stream from /v2/advertisers."""

    name = "advertisers"
    path = "/v2/advertisers"
    primary_keys = ("id",)
    replication_key = None
    records_jsonpath = "$.advertisers[*]"

    schema: ClassVar[StreamSchema] = StreamSchema(OPENAPI_SOURCE, key="Advertiser")

    @override
    def get_new_paginator(self) -> RakutenPaginator:
        return RakutenPaginator(start_value=0)

    @override
    def get_url_params(
        self,
        context: Context | None,
        next_page_token: Any | None,
    ) -> dict[str, Any]:
        return {"page": next_page_token, "limit": ADVERTISERS_PAGE_SIZE}


class EventsStream(RakutenAdvertisingStream):
    """Events/Transactions stream from /events/1.0/transactions."""

    name = "events"
    path = "/events/1.0/transactions"
    primary_keys = ("etransaction_id",)
    replication_key = "process_date"
    records_jsonpath = "$[*]"

    schema: ClassVar[StreamSchema] = StreamSchema(OPENAPI_SOURCE, key="Event")

    @override
    def get_new_paginator(self) -> EventsPaginator:
        return EventsPaginator(start_value=1, page_size=EVENTS_PAGE_SIZE)

    @override
    def get_url_params(
        self,
        context: Context | None,
        next_page_token: Any | None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "page": next_page_token,
            "limit": EVENTS_PAGE_SIZE,
        }
        start_value = self.get_starting_replication_key_value(context)
        if start_value:
            params["process_date_start"] = start_value
        elif self.config.get("start_date"):
            params["process_date_start"] = self.config["start_date"]
        return params


class AdvertiserSearchStream(RakutenAdvertisingStream):
    """Advertiser Search stream from /advertisersearch/1.0 (XML response)."""

    name = "advertiser_search"
    path = "/advertisersearch/1.0"
    primary_keys = ("mid",)
    replication_key = None

    schema: ClassVar[StreamSchema] = StreamSchema(OPENAPI_SOURCE, key="AdvertiserSearchMerchant")

    @override
    def get_new_paginator(self) -> SinglePagePaginator:
        return SinglePagePaginator()

    @override
    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse XML response from Advertiser Search API."""
        data = xmltodict.parse(response.text)
        # Navigate XML structure: midlist > merchant
        midlist = data.get("midlist", data)
        merchants = midlist.get("merchant", [])
        if isinstance(merchants, dict):
            merchants = [merchants]
        for merchant in merchants:
            record: dict[str, Any] = {}
            mid = merchant.get("mid")
            record["mid"] = int(mid) if mid is not None else None
            record["merchantname"] = merchant.get("merchantname")
            yield record


class PartnershipsStream(RakutenAdvertisingStream):
    """Partnerships stream from /v1/partnerships."""

    name = "partnerships"
    path = "/v1/partnerships"
    primary_keys = ("advertiser_id",)
    replication_key = None
    records_jsonpath = "$.partnerships[*]"

    schema: ClassVar[StreamSchema] = StreamSchema(OPENAPI_SOURCE, key="Partnership")

    @override
    def get_new_paginator(self) -> RakutenPaginator:
        return RakutenPaginator(start_value=1)

    @override
    def get_url_params(
        self,
        context: Context | None,
        next_page_token: Any | None,
    ) -> dict[str, Any]:
        return {"page": next_page_token, "limit": PARTNERSHIPS_PAGE_SIZE}

    @override
    def post_process(
        self,
        row: dict,
        context: Context | None = None,
    ) -> dict | None:
        """Flatten the nested advertiser object."""
        advertiser = row.pop("advertiser", {})
        row["advertiser_id"] = advertiser.get("id")
        row["advertiser_name"] = advertiser.get("name")
        row["advertiser_network"] = advertiser.get("network")
        row["advertiser_status"] = advertiser.get("status")
        row["advertiser_categories"] = advertiser.get("categories")
        row["advertiser_details"] = advertiser.get("details")
        return row


class PublisherContributedConversionsStream(RakutenAdvertisingStream):
    """Publisher Contributed Conversions from /v1/publishers/contributed-conversions."""

    name = "publisher_contributed_conversions"
    path = "/v1/publishers/contributed-conversions"
    primary_keys = ("publisher_id", "order_id", "order_datetime")
    replication_key = "order_datetime"
    records_jsonpath = "$.data[*]"

    schema: ClassVar[StreamSchema] = StreamSchema(OPENAPI_SOURCE, key="ContributedConversion")

    @override
    def get_new_paginator(self) -> RakutenPaginator:
        return RakutenPaginator(start_value=1)

    @override
    def get_url_params(
        self,
        context: Context | None,
        next_page_token: Any | None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "page": next_page_token,
            "limit": PUBLISHER_CONVERSIONS_PAGE_SIZE,
        }
        start_value = self.get_starting_replication_key_value(context)
        if start_value:
            params["start_date"] = str(start_value)[:10]
        elif self.config.get("start_date"):
            params["start_date"] = self.config["start_date"][:10]
        params["end_date"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        return params
