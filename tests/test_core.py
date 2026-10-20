"""Tests standard tap features using the built-in SDK tests library."""

import datetime as dt
import os

from singer_sdk.testing import SuiteConfig, get_tap_test_class

from tap_rakutenadvertising.tap import TapRakutenAdvertising

CI = "CI" in os.environ


def _one_week_ago() -> str:
    val = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=7)
    return val.strftime("%Y-%m-%d")


# Config is loaded from environment variables (populated from .env via conftest.py).
# In production / Meltano, the same env vars are set by the .env file.
SAMPLE_CONFIG = {
    "auth_token": os.environ.get("TAP_RAKUTENADVERTISING_AUTH_TOKEN", "test_token"),
    "start_date": os.environ.get("TAP_RAKUTENADVERTISING_START_DATE", _one_week_ago()),
}


# Run standard built-in tap tests from the SDK:
# Most streams return 0 records for a test publisher account,
# so we ignore the "no records returned" assertion.
TestTapRakutenAdvertising = get_tap_test_class(
    tap_class=TapRakutenAdvertising,
    config=SAMPLE_CONFIG,
    include_tap_tests=not CI,
    include_stream_tests=not CI,
    include_stream_attribute_tests=not CI,
    suite_config=SuiteConfig(ignore_no_records=True),
)
