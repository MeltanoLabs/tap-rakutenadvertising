"""Tests standard tap features using the built-in SDK tests library."""

import datetime

from singer_sdk.testing import get_tap_test_class

from tap_rakutenadvertising.tap import TapRakutenAdvertising

SAMPLE_CONFIG = {
    "auth_token": "test_token",
    "start_date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"),
}


# Run standard built-in tap tests from the SDK:
TestTapRakutenAdvertising = get_tap_test_class(
    tap_class=TapRakutenAdvertising,
    config=SAMPLE_CONFIG,
)
