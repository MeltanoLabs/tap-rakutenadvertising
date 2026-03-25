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

Stream schemas are sourced directly from the OpenAPI specification at
`tap_rakutenadvertising/openapi.json` using the Singer SDK's `OpenAPISchema` integration.

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
