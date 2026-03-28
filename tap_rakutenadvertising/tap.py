"""RakutenAdvertising tap class."""

from __future__ import annotations

from singer_sdk import Tap
from singer_sdk import typing as th

from tap_rakutenadvertising import streams


class TapRakutenAdvertising(Tap):
    """Singer tap for RakutenAdvertising."""

    name = "tap-rakutenadvertising"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "auth_token",
            th.StringType(nullable=False),
            required=True,
            secret=True,
            title="Auth Token",
            description="The token to authenticate against RakutenAdvertising",
        ),
        th.Property(
            "start_date",
            th.DateTimeType(nullable=True),
            description="The earliest record date to sync",
        ),
        th.Property(
            "api_url",
            th.StringType(nullable=False),
            title="API URL",
            default="https://api.linksynergy.com",
            description="The base URL for the Rakuten Advertising API",
        ),
        th.Property(
            "offer_status",
            th.StringType(nullable=False),
            default="active",
            description="Filter for the offers stream. One of: active, available, upcoming",
        ),
        th.Property(
            "product_search_keyword",
            th.StringType(nullable=True),
            description="Search keyword for the product_search stream",
        ),
        th.Property(
            "product_search_mid",
            th.IntegerType(nullable=True),
            description="Advertiser ID filter for the product_search stream",
        ),
        th.Property(
            "link_locator_advertiser_id",
            th.IntegerType(nullable=True),
            default=-1,
            description="Advertiser ID for Link Locator streams (-1 = all)",
        ),
        th.Property(
            "link_locator_category_id",
            th.IntegerType(nullable=True),
            default=-1,
            description="Category ID for Link Locator streams (-1 = all)",
        ),
        th.Property(
            "banner_size_code",
            th.IntegerType(nullable=True),
            default=-1,
            description="Banner size code for the banner_links stream (-1 = all)",
        ),
    ).to_dict()

    def discover_streams(self) -> list:
        """Return a list of discovered streams."""
        return [
            streams.AdvertisersStream(self),
            streams.EventsStream(self),
            streams.AdvertiserSearchStream(self),
            streams.PartnershipsStream(self),
            streams.PublisherContributedConversionsStream(self),
            streams.OffersStream(self),
            streams.CommissioningListsStream(self),
            streams.CouponsStream(self),
            streams.ProductSearchStream(self),
            streams.TextLinksStream(self),
            streams.BannerLinksStream(self),
            streams.DRMLinksStream(self),
            streams.CreativeCategoriesStream(self),
        ]


if __name__ == "__main__":
    TapRakutenAdvertising.cli()
