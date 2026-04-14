"""RakutenAdvertising tap class."""

from __future__ import annotations

from typing import TYPE_CHECKING

from singer_sdk import Tap
from singer_sdk import typing as th

from tap_rakutenadvertising import streams

if TYPE_CHECKING:
    from tap_rakutenadvertising.client import RakutenAdvertisingStream


class TapRakutenAdvertising(Tap):
    """Singer tap for RakutenAdvertising."""

    name = "tap-rakutenadvertising"

    config_jsonschema = th.PropertiesList(
        th.Property(
            "auth_token",
            th.StringType(nullable=True),
            required=False,
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
        th.Property(
            "security_token",
            th.StringType(nullable=True),
            secret=True,
            title="Security Token",
            description=(
                "Security token for the Advanced Reports API. "
                "This is NOT the Bearer token. "
                "Obtain from Rakuten publisher dashboard. "
                "Required for advanced_reports_* streams."
            ),
        ),
        th.Property(
            "advanced_reports_pay_id",
            th.IntegerType(nullable=True),
            description=(
                "Payment ID for Advanced Reports advertiser payments streams "
                "(reportid 2/22). Retrieve from the payment history summary report."
            ),
        ),
        th.Property(
            "advanced_reports_invoice_id",
            th.IntegerType(nullable=True),
            description=(
                "Invoice ID for Advanced Reports payment details streams "
                "(reportid 3/23). Retrieve from the advertiser payments report."
            ),
        ),
        th.Property(
            "advanced_reports_network_id",
            th.IntegerType(nullable=True),
            description="Optional network ID filter for Advanced Reports (1, 3, 5, 41)",
        ),
        th.Property(
            "reporting_api_token",
            th.StringType(nullable=True),
            secret=True,
            title="Reporting Platform API Token",
            description=(
                "API token for the Rakuten Reporting Platform "
                "(ran-reporting.rakutenmarketing.com). "
                "Found in the report URL under 'token=' parameter. "
                "Required for reporting_* streams."
            ),
        ),
        th.Property(
            "reporting_report_keys",
            th.StringType(nullable=True),
            title="Reporting Platform Report Keys",
            description=(
                "Comma-separated report keys for the Reporting Platform "
                "(e.g. 'data_team_monthly_report_us,sales-and-activity-report'). "
                "Each key becomes a separate stream."
            ),
        ),
        th.Property(
            "reporting_region",
            th.StringType(nullable=True),
            default="en",
            description="Region code for the Reporting Platform API (default: en)",
        ),
        th.Property(
            "reporting_date_type",
            th.StringType(nullable=True),
            default="transaction",
            description=(
                "Date type for Reporting Platform reports. "
                "One of: transaction, process."
            ),
        ),
    ).to_dict()

    def discover_streams(self) -> list[RakutenAdvertisingStream]:
        """Return a list of discovered streams."""
        stream_list: list[RakutenAdvertisingStream] = []
        if self.config.get("auth_token"):
            stream_list.extend([
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
            ])
        if self.config.get("auth_token") and self.config.get("security_token"):
            stream_list.extend([
                streams.AdvancedReportsPaymentHistoryStream(self),
                streams.AdvancedReportsAdvertiserPaymentsV1Stream(self),
                streams.AdvancedReportsPaymentDetailsV1Stream(self),
                streams.AdvancedReportsAdvertiserPaymentsV2Stream(self),
                streams.AdvancedReportsPaymentDetailsV2Stream(self),
            ])
        if self.config.get("reporting_api_token") and self.config.get(
            "reporting_report_keys"
        ):
            for raw_key in self.config["reporting_report_keys"].split(","):
                report_key = raw_key.strip()
                if report_key:
                    stream_list.append(
                        streams.ReportingPlatformStream(self, report_key=report_key)
                    )
        return stream_list


if __name__ == "__main__":
    TapRakutenAdvertising.cli()
