"""Stream type classes for tap-rakutenadvertising."""

from __future__ import annotations

import datetime
import sys
from importlib.resources import files
from typing import TYPE_CHECKING, Any, ClassVar
from urllib.parse import parse_qs

import xmltodict
from singer_sdk import OpenAPISchema, StreamSchema
from singer_sdk.pagination import SinglePagePaginator

from tap_rakutenadvertising.client import (
    EventsPaginator,
    LinkLocatorPaginator,
    RakutenAdvertisingStream,
    RakutenPaginator,
    XMLPagePaginator,
)

if sys.version_info >= (3, 12):
    from typing import override
else:
    from typing_extensions import override

if TYPE_CHECKING:
    from collections.abc import Iterable
    from urllib.parse import ParseResult

    import requests
    from singer_sdk.helpers.types import Context

OPENAPI_SOURCE = OpenAPISchema(files("tap_rakutenadvertising").joinpath("openapi.json"))

EVENTS_PAGE_SIZE = 1000
ADVERTISERS_PAGE_SIZE = 200
PARTNERSHIPS_PAGE_SIZE = 200
PUBLISHER_CONVERSIONS_PAGE_SIZE = 1000
OFFERS_PAGE_SIZE = 200
COMMISSIONING_LISTS_PAGE_SIZE = 200
COUPONS_PAGE_SIZE = 500
PRODUCT_SEARCH_PAGE_SIZE = 100


def _strip_ns1(record: dict) -> dict:
    """Strip ns1: namespace prefix from all keys in a record."""
    return {k.replace("ns1:", ""): v for k, v in record.items()}


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
        return RakutenPaginator()

    @override
    def get_url_params(
        self,
        context: Context | None,
        next_page_token: ParseResult | None,
    ) -> dict[str, Any]:
        if next_page_token is not None:
            return parse_qs(next_page_token.query)

        return {"page": 1, "limit": ADVERTISERS_PAGE_SIZE}


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
        return EventsPaginator(page_size=EVENTS_PAGE_SIZE)

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
        if start_value := self.get_starting_replication_key_value(context):
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
        return RakutenPaginator()

    @override
    def get_url_params(
        self,
        context: Context | None,
        next_page_token: ParseResult | None,
    ) -> dict[str, Any]:
        if next_page_token is not None:
            return parse_qs(next_page_token.query)

        return {"page": 1, "limit": PARTNERSHIPS_PAGE_SIZE}

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
        return RakutenPaginator()

    @override
    def get_url_params(
        self,
        context: Context | None,
        next_page_token: ParseResult | None,
    ) -> dict[str, Any]:
        if next_page_token is not None:
            return parse_qs(next_page_token.query)

        params: dict[str, Any] = {
            "page": next_page_token,
            "limit": PUBLISHER_CONVERSIONS_PAGE_SIZE,
        }
        if start_dt := self.get_starting_timestamp(context):
            params["start_date"] = start_dt.strftime("%Y-%m-%d")

        params["end_date"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        return params


class OffersStream(RakutenAdvertisingStream):
    """Offers stream from /v1/offers."""

    name = "offers"
    path = "/v1/offers"
    primary_keys = ("goid",)
    replication_key = None
    records_jsonpath = "$.offers[*]"

    schema: ClassVar[StreamSchema] = StreamSchema(OPENAPI_SOURCE, key="Offer")

    @override
    def get_new_paginator(self) -> RakutenPaginator:
        return RakutenPaginator()

    @override
    def get_url_params(
        self,
        context: Context | None,
        next_page_token: ParseResult | None,
    ) -> dict[str, Any]:
        if next_page_token is not None:
            return parse_qs(next_page_token.query)

        return {
            "page": next_page_token,
            "limit": OFFERS_PAGE_SIZE,
            "offer_status": self.config.get("offer_status", "active"),
        }

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
        row["advertiser_details"] = advertiser.get("details")
        return row


class CommissioningListsStream(RakutenAdvertisingStream):
    """Commissioning Lists stream from /v1/commissioninglists."""

    name = "commissioning_lists"
    path = "/v1/commissioninglists"
    primary_keys = ("list_id",)
    replication_key = None
    records_jsonpath = "$.commissioninglists[*]"

    schema: ClassVar[StreamSchema] = StreamSchema(OPENAPI_SOURCE, key="CommissioningList")

    @override
    def get_new_paginator(self) -> RakutenPaginator:
        return RakutenPaginator()

    @override
    def get_url_params(
        self,
        context: Context | None,
        next_page_token: ParseResult | None,
    ) -> dict[str, Any]:
        if next_page_token is not None:
            return parse_qs(next_page_token.query)

        return {"page": next_page_token, "limit": COMMISSIONING_LISTS_PAGE_SIZE}

    @override
    def post_process(
        self,
        row: dict,
        context: Context | None = None,
    ) -> dict | None:
        """Flatten the nested advertiser object."""
        advertiser = row.pop("advertiser", {})
        row["advertiser_id"] = advertiser.get("id")
        row["advertiser_details"] = advertiser.get("details")
        return row


class CouponsStream(RakutenAdvertisingStream):
    """Coupons stream from /coupon/1.0 (XML response)."""

    name = "coupons"
    path = "/coupon/1.0"
    primary_keys = ("clickurl",)
    replication_key = None

    schema: ClassVar[StreamSchema] = StreamSchema(OPENAPI_SOURCE, key="Coupon")

    @override
    def get_new_paginator(self) -> XMLPagePaginator:
        return XMLPagePaginator(current_page_key="PageNumberRequested")

    @override
    def get_url_params(
        self,
        context: Context | None,
        next_page_token: Any | None,
    ) -> dict[str, Any]:
        return {"pagenumber": next_page_token, "resultsperpage": COUPONS_PAGE_SIZE}

    @override
    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse XML response from Coupon Feed API."""
        data = xmltodict.parse(response.text)
        root = next(iter(data.values()))
        links = root.get("link", [])
        if isinstance(links, dict):
            links = [links]
        for link in links:
            record: dict[str, Any] = {}
            record["advertiserid"] = int(link["advertiserid"]) if link.get("advertiserid") else None
            record["advertisername"] = link.get("advertisername")

            network = link.get("network", {})
            if isinstance(network, dict) and (nid := network.get("@id")):
                record["network_id"] = nid
            else:
                record["network_id"] = None

            record["offerdescription"] = link.get("offerdescription")
            record["offerstartdate"] = link.get("offerstartdate")
            record["offerenddate"] = link.get("offerenddate")
            record["couponcode"] = link.get("couponcode")
            record["couponrestriction"] = link.get("couponrestriction")
            record["clickurl"] = link.get("clickurl")
            record["impressionpixel"] = link.get("impressionpixel")
            record["categories"] = link.get("categories", [])
            record["promotiontypes"] = link.get("promotiontypes", [])
            yield record


class ProductSearchStream(RakutenAdvertisingStream):
    """Product Search stream from /productsearch/1.0 (XML response)."""

    name = "product_search"
    path = "/productsearch/1.0"
    primary_keys = ("mid", "sku")
    replication_key = None

    schema: ClassVar[StreamSchema] = StreamSchema(OPENAPI_SOURCE, key="Product")

    @override
    def get_new_paginator(self) -> XMLPagePaginator:
        return XMLPagePaginator()

    @override
    def get_url_params(
        self,
        context: Context | None,
        next_page_token: Any | None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "pagenumber": next_page_token,
            "max": PRODUCT_SEARCH_PAGE_SIZE,
        }
        keyword = self.config.get("product_search_keyword")
        if keyword:
            params["keyword"] = keyword
        mid = self.config.get("product_search_mid")
        if mid:
            params["mid"] = mid
        return params

    @override
    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse XML response from Product Search API."""
        data = xmltodict.parse(response.text)
        root = next(iter(data.values()))
        items = root.get("item", [])
        if isinstance(items, dict):
            items = [items]
        for item in items:
            record: dict[str, Any] = {}
            mid = item.get("mid")
            record["mid"] = int(mid) if mid is not None else None
            record["merchantname"] = item.get("merchantname")
            record["linkid"] = str(item.get("linkid", "")) if item.get("linkid") else None
            record["createdon"] = item.get("createdon")
            record["sku"] = str(item.get("sku", "")) if item.get("sku") else None
            record["productname"] = item.get("productname")
            category = item.get("category", {})
            if isinstance(category, dict):
                record["category_primary"] = category.get("primary")
                record["category_secondary"] = category.get("secondary")
            else:
                record["category_primary"] = None
                record["category_secondary"] = None
            price = item.get("price", {})
            record["price"] = (
                price.get("#text") if isinstance(price, dict) else str(price) if price else None
            )
            saleprice = item.get("saleprice", {})
            record["saleprice"] = (
                saleprice.get("#text")
                if isinstance(saleprice, dict)
                else str(saleprice)
                if saleprice
                else None
            )
            upccode = item.get("upccode")
            record["upccode"] = str(upccode) if upccode and upccode != {} else None
            description = item.get("description", {})
            if isinstance(description, dict):
                record["description_short"] = description.get("short")
                record["description_long"] = description.get("long")
            else:
                record["description_short"] = None
                record["description_long"] = None
            record["keywords"] = item.get("keywords")
            record["linkurl"] = item.get("linkurl")
            record["imageurl"] = item.get("imageurl")
            yield record


def _format_date_mmddyyyy(date_str: str | None) -> str:
    """Convert an ISO date string or YYYY-MM-DD to MMDDYYYY format."""
    if not date_str:
        return datetime.datetime.now(datetime.timezone.utc).strftime("%m%d%Y")
    try:
        dt = datetime.datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%m%d%Y")
    except ValueError:
        return datetime.datetime.now(datetime.timezone.utc).strftime("%m%d%Y")


class TextLinksStream(RakutenAdvertisingStream):
    """Text Links stream from Link Locator API (XML response, path-based pagination)."""

    name = "text_links"
    path = "/linklocator/1.0/getTextLinks/-1/-1/01012000/01012030/-1/1"
    primary_keys = ("linkID",)
    replication_key = None
    _response_key = "ns1:getTextLinksResponse"

    schema: ClassVar[StreamSchema] = StreamSchema(OPENAPI_SOURCE, key="TextLink")

    @override
    def get_new_paginator(self) -> LinkLocatorPaginator:
        return LinkLocatorPaginator(response_key=self._response_key)

    @override
    def get_url(self, context: Context | None) -> str:
        """Build URL with path parameters including page number."""
        adv = self.config.get("link_locator_advertiser_id", -1)
        cat = self.config.get("link_locator_category_id", -1)
        start = _format_date_mmddyyyy(self.config.get("start_date"))
        end = datetime.datetime.now(datetime.timezone.utc).strftime("%m%d%Y")
        page = self._page_token if hasattr(self, "_page_token") and self._page_token else 1
        return f"{self.url_base}/linklocator/1.0/getTextLinks/{adv}/{cat}/{start}/{end}/-1/{page}"

    @override
    def get_url_params(
        self,
        context: Context | None,
        next_page_token: Any | None,
    ) -> dict[str, Any]:
        return {}

    @override
    def prepare_request(
        self,
        context: Context | None,
        next_page_token: Any | None,
    ) -> requests.PreparedRequest:
        """Store page token before preparing request."""
        self._page_token = next_page_token
        return super().prepare_request(context, next_page_token)

    @override
    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse XML response from Link Locator API."""
        data = xmltodict.parse(response.text)
        root = next(iter(data.values()))
        response_items = root.get(self._response_key, [])
        if isinstance(response_items, dict):
            response_items = [response_items]
        for item in response_items:
            ret = item.get("ns1:return")
            if ret is None:
                continue
            if isinstance(ret, dict):
                ret = [ret]
            for record in ret:
                yield _strip_ns1(record)


class BannerLinksStream(RakutenAdvertisingStream):
    """Banner Links stream from Link Locator API (XML response, path-based pagination)."""

    name = "banner_links"
    path = "/linklocator/1.0/getBannerLinks/-1/-1/01012000/01012030/-1/-1/1"
    primary_keys = ("linkID",)
    replication_key = None
    _response_key = "ns1:getBannerLinksResponse"

    schema: ClassVar[StreamSchema] = StreamSchema(OPENAPI_SOURCE, key="BannerLink")

    @override
    def get_new_paginator(self) -> LinkLocatorPaginator:
        return LinkLocatorPaginator(response_key=self._response_key)

    @override
    def get_url(self, context: Context | None) -> str:
        """Build URL with path parameters including page number."""
        adv = self.config.get("link_locator_advertiser_id", -1)
        cat = self.config.get("link_locator_category_id", -1)
        start = _format_date_mmddyyyy(self.config.get("start_date"))
        end = datetime.datetime.now(datetime.timezone.utc).strftime("%m%d%Y")
        banner_size = self.config.get("banner_size_code", -1)
        page = self._page_token if hasattr(self, "_page_token") and self._page_token else 1
        return (
            f"{self.url_base}/linklocator/1.0/getBannerLinks"
            f"/{adv}/{cat}/{start}/{end}/{banner_size}/-1/{page}"
        )

    @override
    def get_url_params(
        self,
        context: Context | None,
        next_page_token: Any | None,
    ) -> dict[str, Any]:
        return {}

    @override
    def prepare_request(
        self,
        context: Context | None,
        next_page_token: Any | None,
    ) -> requests.PreparedRequest:
        """Store page token before preparing request."""
        self._page_token = next_page_token
        return super().prepare_request(context, next_page_token)

    @override
    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse XML response from Link Locator API."""
        data = xmltodict.parse(response.text)
        root = next(iter(data.values()))
        response_items = root.get(self._response_key, [])
        if isinstance(response_items, dict):
            response_items = [response_items]
        for item in response_items:
            ret = item.get("ns1:return")
            if ret is None:
                continue
            if isinstance(ret, dict):
                ret = [ret]
            for record in ret:
                yield _strip_ns1(record)


class DRMLinksStream(RakutenAdvertisingStream):
    """DRM Links stream from Link Locator API (XML response, path-based pagination)."""

    name = "drm_links"
    path = "/linklocator/1.0/getDRMLinks/-1/-1/01012000/01012030/-1/1"
    primary_keys = ("linkID",)
    replication_key = None
    _response_key = "ns1:getDRMLinksResponse"

    schema: ClassVar[StreamSchema] = StreamSchema(OPENAPI_SOURCE, key="DRMLink")

    @override
    def get_new_paginator(self) -> LinkLocatorPaginator:
        return LinkLocatorPaginator(response_key=self._response_key)

    @override
    def get_url(self, context: Context | None) -> str:
        """Build URL with path parameters including page number."""
        adv = self.config.get("link_locator_advertiser_id", -1)
        cat = self.config.get("link_locator_category_id", -1)
        start = _format_date_mmddyyyy(self.config.get("start_date"))
        end = datetime.datetime.now(datetime.timezone.utc).strftime("%m%d%Y")
        page = self._page_token if hasattr(self, "_page_token") and self._page_token else 1
        return f"{self.url_base}/linklocator/1.0/getDRMLinks/{adv}/{cat}/{start}/{end}/-1/{page}"

    @override
    def get_url_params(
        self,
        context: Context | None,
        next_page_token: Any | None,
    ) -> dict[str, Any]:
        return {}

    @override
    def prepare_request(
        self,
        context: Context | None,
        next_page_token: Any | None,
    ) -> requests.PreparedRequest:
        """Store page token before preparing request."""
        self._page_token = next_page_token
        return super().prepare_request(context, next_page_token)

    @override
    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse XML response from Link Locator API."""
        data = xmltodict.parse(response.text)
        root = next(iter(data.values()))
        response_items = root.get(self._response_key, [])
        if isinstance(response_items, dict):
            response_items = [response_items]
        for item in response_items:
            ret = item.get("ns1:return")
            if ret is None:
                continue
            if isinstance(ret, dict):
                ret = [ret]
            for record in ret:
                yield _strip_ns1(record)


class CreativeCategoriesStream(RakutenAdvertisingStream):
    """Creative Categories stream from Link Locator API (XML response)."""

    name = "creative_categories"
    path = "/linklocator/1.0/getCreativeCategories/-1"
    primary_keys = ("mid", "catId")
    replication_key = None

    schema: ClassVar[StreamSchema] = StreamSchema(OPENAPI_SOURCE, key="CreativeCategory")

    @override
    def get_new_paginator(self) -> SinglePagePaginator:
        return SinglePagePaginator()

    @override
    def get_url(self, context: Context | None) -> str:
        """Build URL with advertiser ID path parameter."""
        adv = self.config.get("link_locator_advertiser_id", -1)
        return f"{self.url_base}/linklocator/1.0/getCreativeCategories/{adv}"

    @override
    def get_url_params(
        self,
        context: Context | None,
        next_page_token: Any | None,
    ) -> dict[str, Any]:
        return {}

    @override
    def parse_response(self, response: requests.Response) -> Iterable[dict]:
        """Parse XML response from Creative Categories API."""
        data = xmltodict.parse(response.text)
        root = next(iter(data.values()))
        response_items = root.get("ns1:getCreativeCategoriesResponse", [])
        if isinstance(response_items, dict):
            response_items = [response_items]
        for item in response_items:
            ret = item.get("ns1:return")
            if ret is None:
                continue
            if isinstance(ret, dict):
                ret = [ret]
            for record in ret:
                yield _strip_ns1(record)
