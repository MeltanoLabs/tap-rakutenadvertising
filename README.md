# tap-rakutenadvertising

`tap-rakutenadvertising` is a Singer tap for the [Rakuten Advertising Affiliate API](https://developers.rakutenadvertising.com/documentation/en-US/affiliate_apis).

Built with the [Meltano Tap SDK](https://sdk.meltano.com) for Singer Taps.

## Streams

### Core Streams (Rakuten Advertising API)

| Stream | Endpoint | Replication | Primary Key(s) |
|:-------|:---------|:------------|:---------------|
| `advertisers` | `GET /v2/advertisers` | Full table | `id` |
| `events` | `GET /events/1.0/transactions` | Incremental (`process_date`) | `etransaction_id` |
| `advertiser_search` | `GET /advertisersearch/1.0` | Full table | `mid` |
| `partnerships` | `GET /v1/partnerships` | Full table | `advertiser_id` |
| `publisher_contributed_conversions` | `GET /v1/publishers/contributed-conversions` | Incremental (`order_datetime`) | `publisher_id`, `order_id`, `order_datetime` |
| `offers` | `GET /v1/offers` | Full table | `goid` |
| `commissioning_lists` | `GET /v1/commissioninglists` | Full table | `list_id` |
| `coupons` | `GET /coupon/1.0` | Full table | `clickurl` |
| `product_search` | `GET /productsearch/1.0` | Full table | `mid`, `sku` |
| `text_links` | `GET /linklocator/1.0/getTextLinks/...` | Full table | `linkID` |
| `banner_links` | `GET /linklocator/1.0/getBannerLinks/...` | Full table | `linkID` |
| `drm_links` | `GET /linklocator/1.0/getDRMLinks/...` | Full table | `linkID` |
| `creative_categories` | `GET /linklocator/1.0/getCreativeCategories/...` | Full table | `mid`, `catId` |

### Advanced Reports Streams

These streams use the `/advancedreports/1.0` endpoint and require a separate `security_token` (not the Bearer token). Enable by setting the `security_token` config.

| Stream | Report ID | Primary Key(s) | Required Config |
|:-------|:---------:|:---------------|:----------------|
| `advanced_reports_payment_history` | 1 | `payment_id` | `security_token` |
| `advanced_reports_advertiser_payments_v1` | 2 | `invoice_id` | `security_token`, `advanced_reports_pay_id` |
| `advanced_reports_payment_details_v1` | 3 | `transaction_id` | `security_token`, `advanced_reports_invoice_id` |
| `advanced_reports_advertiser_payments_v2` | 22 | `invoice_id` | `security_token`, `advanced_reports_pay_id` |
| `advanced_reports_payment_details_v2` | 23 | `transaction_id` | `security_token`, `advanced_reports_invoice_id` |

### Reporting Platform Streams

These streams pull CSV reports from `ran-reporting.rakutenmarketing.com` — the same API used by Fivetran. Requires `reporting_api_token` and `reporting_report_keys`. Each comma-separated report key becomes a separate stream named `reporting_<key>` (hyphens replaced with underscores).

| Stream | Endpoint | Replication |
|:-------|:---------|:------------|
| `reporting_<report_key>` | `GET /{region}/reports/{key}/filters` | Full table |

For example, setting `reporting_report_keys=product-success-report` creates a stream named `reporting_product_success_report`.

### Stream Schemas

Core stream schemas are sourced directly from the OpenAPI specification at
`tap_rakutenadvertising/openapi.json` using the Singer SDK's `OpenAPISchema` integration.

Advanced Reports and Reporting Platform streams use open schemas (`additionalProperties: true`) since the API response fields are not fully documented.

### Stream Notes

- **`events`**: The Rakuten Events API only allows querying data from the last 30 days. If `start_date` is older than 30 days, it is automatically clamped. Both `process_date_start` and `process_date_end` are required by the API and are set automatically.
- **`product_search`**: Requires at least `product_search_keyword` or `product_search_mid` to be configured. The API returns a maximum of 5,000 results.
- **`coupons`**: Uses `clickurl` as the primary key since the API does not provide a unique coupon identifier.
- **`text_links`, `banner_links`, `drm_links`**: Use the Link Locator API with path-based parameters. Configure `link_locator_advertiser_id` and `link_locator_category_id` to filter results (default `-1` = all). Date range defaults to `start_date` config through today.
- **`creative_categories`**: Returns creative categories for the configured `link_locator_advertiser_id`. When set to `-1` (all), some API accounts receive a 500 "Invalid Merchant ID" error — this is handled gracefully with a warning and 0 records.
- **`publisher_contributed_conversions`**: Requires specific account permissions. If the API returns 403 "You cannot consume this service", the stream logs a warning and returns 0 records.
- **`offers`**: The `offer_status` config parameter is required by the API (default: `active`). Nested advertiser and offer rules data is included.
- **Advanced Reports**: Report IDs 2/22 require `advanced_reports_pay_id` (from report 1). Report IDs 3/23 require `advanced_reports_invoice_id` (from report 2/22). If the required ID is not configured, the stream logs a warning and returns 0 records.

## Installation

Install from GitHub:

```bash
uv tool install git+https://github.com/MeltanoLabs/tap-rakutenadvertising.git@main
```

## Configuration

### Accepted Config Options

| Setting | Required | Default | Description |
|:--------|:--------:|:-------:|:------------|
| `auth_token` | Yes | — | Bearer token for the Rakuten Advertising API |
| `start_date` | No | 6 months ago | Earliest date to sync incremental streams (ISO 8601) |
| `api_url` | No | `https://api.linksynergy.com` | Base URL for the Rakuten Advertising API |
| `offer_status` | No | `active` | Filter for the `offers` stream (`active`, `available`, `upcoming`) |
| `product_search_keyword` | No | — | Search keyword for the `product_search` stream |
| `product_search_mid` | No | — | Advertiser ID filter for the `product_search` stream |
| `link_locator_advertiser_id` | No | `-1` | Advertiser ID for Link Locator streams (`-1` = all) |
| `link_locator_category_id` | No | `-1` | Category ID for Link Locator streams (`-1` = all) |
| `banner_size_code` | No | `-1` | Banner size code for the `banner_links` stream (`-1` = all) |
| `security_token` | No | — | Security token for Advanced Reports API (not the Bearer token) |
| `advanced_reports_pay_id` | No | — | Payment ID for Advanced Reports (reportid 2/22) |
| `advanced_reports_invoice_id` | No | — | Invoice ID for Advanced Reports (reportid 3/23) |
| `advanced_reports_network_id` | No | — | Network ID filter for Advanced Reports (1, 3, 5, 41) |
| `reporting_api_token` | No | — | API token for the Reporting Platform (`ran-reporting.rakutenmarketing.com`) |
| `reporting_report_keys` | No | — | Comma-separated report keys (each becomes a stream) |
| `reporting_region` | No | `en` | Region code for the Reporting Platform API |
| `reporting_date_type` | No | `transaction` | Date type for Reporting Platform (`transaction` or `process`) |

A full list of supported settings and capabilities is available by running:

```bash
tap-rakutenadvertising --about
```

### Source Authentication and Authorization

This tap uses up to three different authentication mechanisms depending on which streams you enable:

1. **Bearer Token** (`auth_token`) — Required for all core streams. Generate from the [Rakuten Advertising Developer Portal](https://developers.rakutenadvertising.com). Note: these tokens are short-lived.

2. **Security Token** (`security_token`) — Required for Advanced Reports streams. Obtain from the Rakuten publisher dashboard. This is a separate token from the Bearer token.

3. **Reporting API Token** (`reporting_api_token`) — Required for Reporting Platform streams. Found in the report URL under the `token=` parameter in the Rakuten publisher dashboard Reports section.

### Configure using environment variables

This tap reads configuration from environment variables prefixed with `TAP_RAKUTENADVERTISING_`. Create a `.env` file in the project root:

```bash
# .env
TAP_RAKUTENADVERTISING_AUTH_TOKEN=your_bearer_token
TAP_RAKUTENADVERTISING_START_DATE=2024-01-01T00:00:00Z

# Advanced Reports (optional)
TAP_RAKUTENADVERTISING_SECURITY_TOKEN=your_security_token

# Reporting Platform (optional)
TAP_RAKUTENADVERTISING_REPORTING_API_TOKEN=your_reporting_token
TAP_RAKUTENADVERTISING_REPORTING_REPORT_KEYS=product-success-report
```

When using Meltano, environment variables are loaded automatically from `.env`. For standalone usage:

```bash
tap-rakutenadvertising --config=ENV --discover
```

## Usage

You can run `tap-rakutenadvertising` by itself or in a pipeline using [Meltano](https://meltano.com/).

### Executing the Tap Directly

```bash
tap-rakutenadvertising --version
tap-rakutenadvertising --help

# Discover available streams
tap-rakutenadvertising --config config.json --discover > catalog.json

# Run a full sync
tap-rakutenadvertising --config config.json --catalog catalog.json
```

### Testing with [Meltano](https://www.meltano.com)

_**Note:** This tap will work in any Singer environment and does not require Meltano._

```bash
# Install meltano
uv tool install meltano

# Test invocation
meltano invoke tap-rakutenadvertising --version

# Run a test EL pipeline
meltano run tap-rakutenadvertising target-jsonl
```

## Developer Resources

### Initialize your Development Environment

Prerequisites: Python 3.10+, [uv](https://docs.astral.sh/uv/)

```bash
git clone https://github.com/MeltanoLabs/tap-rakutenadvertising.git
cd tap-rakutenadvertising
uv sync
```

### Configuration for Development

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
# Edit .env with your actual tokens
```

The `.env` file is loaded automatically by both the test suite and Meltano.

### Create and Run Tests

```bash
# Run all tests (requires valid auth_token in .env)
uv run pytest

# Run only unit tests (no API credentials needed)
uv run pytest tests/test_paginators.py
```

You can also test the CLI directly:

```bash
uv run tap-rakutenadvertising --help
uv run tap-rakutenadvertising --config config.json --discover
```

### Adding New Streams

1. Add a record-level schema component to `tap_rakutenadvertising/openapi.json` under `components.schemas`.
2. Define a new stream class in `tap_rakutenadvertising/streams.py` referencing the component:
   ```python
   class MyNewStream(RakutenAdvertisingStream):
       name = "my_new_stream"
       path = "/v1/my-endpoint"
       primary_keys = ("id",)
       replication_key = None
       schema: ClassVar[StreamSchema] = StreamSchema(OPENAPI_SOURCE, key="MyComponent")
   ```
3. Register the stream in `TapRakutenAdvertising.discover_streams()` in `tap_rakutenadvertising/tap.py`.

### SDK Dev Guide

See the [dev guide](https://sdk.meltano.com/en/latest/dev_guide.html) for more instructions on how to use the SDK to develop your own taps and targets.
