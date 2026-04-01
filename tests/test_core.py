"""Tests standard tap features using the built-in SDK tests library."""

import datetime
import os

from singer_sdk.testing import get_tap_test_class

from tap_rakutenadvertising.tap import TapRakutenAdvertising

CI = "CI" in os.environ


def _one_week_ago() -> str:
    dt = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)
    return dt.strftime("%Y-%m-%d")


SAMPLE_CONFIG = {
    "auth_token": "test_token",
    "start_date": _one_week_ago(),
}


# Run standard built-in tap tests from the SDK:
TestTapRakutenAdvertising = get_tap_test_class(
    tap_class=TapRakutenAdvertising,
    config=SAMPLE_CONFIG,
    include_tap_tests=not CI,
    include_stream_tests=not CI,
    include_stream_attribute_tests=not CI,
)
