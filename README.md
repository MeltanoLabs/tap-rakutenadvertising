# tap-rakutenadvertising

`tap-rakutenadvertising` is a Singer tap for the [Rakuten Advertising Affiliate API](https://developers.rakutenadvertising.com/documentation/en-US/affiliate_apis).

Built with the [Meltano Tap SDK](https://sdk.meltano.com) for Singer Taps.

## Streams

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

Stream schemas are sourced directly from the OpenAPI specification at
`tap_rakutenadvertising/openapi.json` using the Singer SDK's `OpenAPISchema` integration.

### Stream Notes

- **`product_search`**: Requires at least `product_search_keyword` or `product_search_mid` to be configured. The API returns a maximum of 5,000 results.
- **`coupons`**: Uses `clickurl` as the primary key since the API does not provide a unique coupon identifier.
- **`text_links`, `banner_links`, `drm_links`**: Use the Link Locator API with path-based parameters. Configure `link_locator_advertiser_id` and `link_locator_category_id` to filter results (default `-1` = all). Date range defaults to `start_date` config through today.
- **`creative_categories`**: Returns creative categories for the configured `link_locator_advertiser_id` (default `-1` = all).
- **`offers`**: The `offer_status` config parameter is required by the API (default: `active`). Nested advertiser and offer rules data is included.

## Installation

Install from GitHub:

```bash
uv tool install git+https://github.com/ORG_NAME/tap-rakutenadvertising.git@main
```

## Configuration

### Accepted Config Options

| Setting | Required | Default | Description |
|:--------|:--------:|:-------:|:------------|
| `auth_token` | ✅ | — | Bearer token for the Rakuten Advertising API |
| `start_date` | ☐ | 6 months ago | Earliest date to sync incremental streams (ISO 8601, e.g. `2024-01-01T00:00:00Z`) |
| `api_url` | ☐ | `https://api.linksynergy.com` | Base URL for the Rakuten Advertising API |
| `offer_status` | ☐ | `active` | Filter for the `offers` stream. One of: `active`, `available`, `upcoming` |
| `product_search_keyword` | ☐ | — | Search keyword for the `product_search` stream |
| `product_search_mid` | ☐ | — | Advertiser ID filter for the `product_search` stream |
| `link_locator_advertiser_id` | ☐ | `-1` | Advertiser ID for Link Locator streams (`-1` = all) |
| `link_locator_category_id` | ☐ | `-1` | Category ID for Link Locator streams (`-1` = all) |
| `banner_size_code` | ☐ | `-1` | Banner size code for the `banner_links` stream (`-1` = all) |

A full list of supported settings and capabilities is available by running:

```bash
tap-rakutenadvertising --about
```

### Source Authentication and Authorization

Generate a Bearer token from the [Rakuten Advertising developer portal](https://developers.rakutenadvertising.com). Pass it via the `auth_token` config setting or the `TAP_RAKUTENADVERTISING_AUTH_TOKEN` environment variable.

### Configure using environment variables

This tap automatically imports environment variables from a `.env` file when invoked with `--config=ENV`:

```bash
# .env
TAP_RAKUTENADVERTISING_AUTH_TOKEN=your_token_here
TAP_RAKUTENADVERTISING_START_DATE=2024-01-01T00:00:00Z
TAP_RAKUTENADVERTISING_API_URL=https://api.linksynergy.com
```

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
git clone https://github.com/ORG_NAME/tap-rakutenadvertising.git
cd tap-rakutenadvertising
uv sync
```

### Create and Run Tests

```bash
uv run pytest
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
