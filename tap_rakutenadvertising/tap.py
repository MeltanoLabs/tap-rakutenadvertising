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
    ).to_dict()

    def discover_streams(self) -> list:
        """Return a list of discovered streams."""
        return [
            streams.AdvertisersStream(self),
            streams.EventsStream(self),
            streams.AdvertiserSearchStream(self),
            streams.PartnershipsStream(self),
            streams.PublisherContributedConversionsStream(self),
        ]


if __name__ == "__main__":
    TapRakutenAdvertising.cli()
