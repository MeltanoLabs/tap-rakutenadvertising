# CLAUDE.md - AI Agent Development Guide for tap-rakutenadvertising

This document provides guidance for AI coding agents and developers working on this Singer tap.

## Project Overview

- **Project Type**: Singer Tap (Extractor)
- **Source**: Rakuten Advertising (multiple APIs)
- **Stream Type**: REST (JSON, XML, and CSV responses)
- **Authentication**: Bearer Token (core), Security Token (advanced reports), API Token (reporting platform)
- **Framework**: Meltano Singer SDK v0.53.6
- **Python**: 3.10+
- **Package Manager**: [uv](https://docs.astral.sh/uv/)
- **Linter**: Ruff (all rules enabled, line length 100)
- **Build System**: Hatchling with hatch-vcs

## Architecture

This tap extracts data from three separate Rakuten APIs:

1. **Rakuten Advertising API** (`api.linksynergy.com`) — 13 core streams, Bearer token auth, JSON/XML responses
2. **Advanced Reports API** (`api.linksynergy.com/advancedreports/1.0`) — 5 streams, separate security token via query param, JSON/CSV responses
3. **Reporting Platform** (`ran-reporting.rakutenmarketing.com`) — dynamic streams from report keys, API token via query param, CSV responses

### Key Components

1. **Tap Class** (`tap_rakutenadvertising/tap.py`): Entry point, 18 config properties, conditional stream registration in `discover_streams()`
2. **Client** (`tap_rakutenadvertising/client.py`): `RakutenAdvertisingStream` base class, `BearerTokenAuthenticator`, 4 custom paginators
3. **Streams** (`tap_rakutenadvertising/streams.py`): 20+ stream classes across 3 API categories, OpenAPI + inline schemas
4. **OpenAPI Schema** (`tap_rakutenadvertising/openapi.json`): Schema definitions for core streams, loaded via `OpenAPISchema`/`StreamSchema`
5. **Tests** (`tests/`): SDK integration tests (`test_core.py`), paginator unit tests (`test_paginators.py`), `.env` loading (`conftest.py`)

### Stream Categories

**Core Streams** (always registered):
`advertisers`, `events`, `advertiser_search`, `partnerships`, `publisher_contributed_conversions`, `offers`, `commissioning_lists`, `coupons`, `product_search`, `text_links`, `banner_links`, `drm_links`, `creative_categories`

**Advanced Reports Streams** (registered when `security_token` is configured):
`advanced_reports_payment_history`, `advanced_reports_advertiser_payments_v1`, `advanced_reports_payment_details_v1`, `advanced_reports_advertiser_payments_v2`, `advanced_reports_payment_details_v2`

**Reporting Platform Streams** (registered when `reporting_api_token` + `reporting_report_keys` are configured):
Dynamic — each comma-separated report key creates a `reporting_<key>` stream.

### Custom Paginators (in `client.py`)

| Paginator | Used By | Strategy |
|-----------|---------|----------|
| `RakutenPaginator` | advertisers, partnerships, offers, commissioning_lists, publisher_contributed_conversions | HATEOAS (`_metadata._links.next`) |
| `EventsPaginator` | events | Page number; has more if `len(data) >= page_size` |
| `XMLPagePaginator` | advertiser_search, coupons, product_search | XML `TotalPages` / `PageNumber` comparison |
| `LinkLocatorPaginator` | text_links, banner_links, drm_links | XML; checks for `ns1:return` items |
| `SinglePagePaginator` | creative_categories, all advanced reports | SDK built-in; single request, no pagination |

### Response Format Handling

- **JSON** — Most core streams use `records_jsonpath`
- **XML** — `advertiser_search`, `coupons`, `product_search`, Link Locator streams — parsed with `xmltodict`
- **CSV** — Reporting Platform streams — parsed with `csv.DictReader`
- **JSON/CSV auto-detect** — Advanced Reports streams detect via `content-type` header

### Graceful Error Handling

Several streams handle specific API errors gracefully instead of crashing:

- **`creative_categories`**: 500 "Invalid Merchant ID" when `link_locator_advertiser_id=-1` — logs warning, returns 0 records
- **`publisher_contributed_conversions`**: 403 "You cannot consume this service" — logs warning, returns 0 records
- **`events`**: Automatically clamps `start_date` to last 29 days (API limit), always sends both `process_date_start` and `process_date_end`

Pattern used: override `validate_response()` to detect the error and return early, override `parse_response()` to yield nothing for that status code.

## Dependencies

### Runtime
| Package | Version | Purpose |
|---------|---------|---------|
| `singer-sdk[faker]` | `~=0.53.6` | Core Singer SDK framework |
| `requests` | `~=2.33.0` | HTTP client |
| `xmltodict` | `~=1.0.4` | XML response parsing |
| `typing-extensions` | `>=4.5.0` | `@override` decorator for Python < 3.12 |

### Test / Dev
| Package | Purpose |
|---------|---------|
| `pytest>=9` | Test runner |
| `python-dotenv>=1.1` | Load `.env` file in tests |
| `singer-sdk[testing]` | SDK integration test suite |
| `ruff>=0.15` | Linter (all rules, line-length 100) |
| `mypy` / `ty` | Type checking |

## Configuration

### Config Sources (Priority Order)

| Context | Source | Details |
|---------|--------|---------|
| **Meltano (production)** | `.env` file | Meltano reads `TAP_RAKUTENADVERTISING_*` env vars automatically |
| **Tests** | `.env` file | `conftest.py` loads via `python-dotenv`, `test_core.py` reads `os.environ` |
| **Manual CLI** | `config.json` | `tap-rakutenadvertising --config config.json` |
| **CI** | GitHub Secrets | `TAP_RAKUTENADVERTISING_*` passed via tox `pass_env` |

### All 18 Config Properties

| Property | Type | Required | Default | Used By |
|----------|------|----------|---------|---------|
| `auth_token` | string (secret) | Yes | — | All core + advanced reports streams |
| `start_date` | datetime | No | — | Incremental streams |
| `api_url` | string | No | `https://api.linksynergy.com` | All core + advanced reports streams |
| `offer_status` | string | No | `active` | `offers` |
| `product_search_keyword` | string | No | — | `product_search` |
| `product_search_mid` | integer | No | — | `product_search` |
| `link_locator_advertiser_id` | integer | No | `-1` | Link Locator + creative_categories |
| `link_locator_category_id` | integer | No | `-1` | Link Locator streams |
| `banner_size_code` | integer | No | `-1` | `banner_links` |
| `security_token` | string (secret) | No | — | Advanced Reports streams |
| `advanced_reports_pay_id` | integer | No | — | Reports 2/22 |
| `advanced_reports_invoice_id` | integer | No | — | Reports 3/23 |
| `advanced_reports_network_id` | integer | No | — | Advanced Reports (filter) |
| `reporting_api_token` | string (secret) | No | — | Reporting Platform streams |
| `reporting_report_keys` | string | No | — | Reporting Platform streams |
| `reporting_region` | string | No | `en` | Reporting Platform streams |
| `reporting_date_type` | string | No | `transaction` | Reporting Platform streams |

### Keeping Files in Sync

When adding/modifying config properties, update **all four** files:

1. `tap_rakutenadvertising/tap.py` — `config_jsonschema` in `TapRakutenAdvertising`
2. `meltano.yml` — `settings` block
3. `.env.example` — commented-out env var entries
4. `README.md` — config table

**Setting kind mappings:**

| Python Type | Meltano Kind |
|-------------|--------------|
| `StringType` | `string` |
| `IntegerType` | `integer` |
| `BooleanType` | `boolean` |
| `NumberType` | `number` |
| `DateTimeType` | `date_iso8601` |

Properties with `secret=True` → `sensitive: true` in `meltano.yml`.

## Development Guidelines

### Quick Commands

```bash
# Install dependencies
uv sync

# Run linter (ALWAYS run before committing)
ruff check tap_rakutenadvertising/ tests/

# Run all tests (needs valid token in .env)
uv run pytest

# Run only unit tests (no API credentials needed)
uv run pytest tests/test_paginators.py

# Discover streams
uv run tap-rakutenadvertising --config config.json --discover

# Full sync
uv run tap-rakutenadvertising --config config.json

# Sync with stderr/stdout separation
uv run tap-rakutenadvertising --config config.json 2>stderr.log 1>stdout.log
```

### Ruff Linting

This project uses `ruff` with **all rules enabled** (`select = ["ALL"]`). Key rules to watch for:

- **ANN** — Type annotations required (except in tests)
- **D** — Google-style docstrings required (except in tests)
- **ARG002** — Unused method arguments: use `# noqa: ARG002` for SDK-mandated signatures
- **PLR2004** — Magic values: extract to named constants (e.g. `HTTP_INTERNAL_SERVER_ERROR = 500`)
- **E501** — Line length max 100 characters

### Adding a New Core Stream

1. Add schema to `tap_rakutenadvertising/openapi.json` under `components.schemas`
2. Define stream class in `streams.py`:
   ```python
   class MyNewStream(RakutenAdvertisingStream):
       name = "my_new_stream"
       path = "/v1/my-endpoint"
       primary_keys = ("id",)
       replication_key = None
       schema: ClassVar[StreamSchema] = StreamSchema(OPENAPI_SOURCE, key="MyComponent")

       @override
       def get_new_paginator(self) -> RakutenPaginator:
           return RakutenPaginator()
   ```
3. Register in `TapRakutenAdvertising.discover_streams()` in `tap.py`
4. Run `ruff check` and `uv run pytest`

### Adding a New Advanced Reports Stream

1. Subclass `AdvancedReportsBaseStream` in `streams.py`
2. Set `name`, `report_id`, `primary_keys`, and `schema` (use `_open_schema()` helper)
3. Override `_get_report_params()` for report-specific query parameters
4. Register in `discover_streams()` inside the `if self.config.get("security_token"):` block

### Adding a New Reporting Platform Report

No code changes needed — just add the report key to `reporting_report_keys` config. Each key dynamically creates a `reporting_<key>` stream via `ReportingPlatformStream`.

### Schema Patterns

**OpenAPI schemas** — used by core streams:
```python
schema: ClassVar[StreamSchema] = StreamSchema(OPENAPI_SOURCE, key="SchemaName")
```

**Open/flexible schemas** — used by advanced reports and reporting platform (unknown fields):
```python
schema: ClassVar[dict] = _open_schema(
    th.Property("known_field", th.StringType),
)
# _open_schema() adds "additionalProperties": true
```

**Inline schemas** — for fully-known structures not in openapi.json:
```python
schema = th.PropertiesList(
    th.Property("id", th.StringType, required=True),
    th.Property("name", th.StringType),
).to_dict()
```

### Authentication Patterns

**Core streams** — Bearer token via `BearerTokenAuthenticator` (defined in `client.py`):
```python
# Inherited from RakutenAdvertisingStream — no override needed
```

**Advanced Reports** — Bearer token for HTTP auth + security token as query param:
```python
# get_url_params() adds: {"token": self.config["security_token"]}
```

**Reporting Platform** — No HTTP auth, API token as query param:
```python
@property
def authenticator(self) -> Callable:
    return lambda r: r  # No-op; SDK requires a callable
```

### Handling API Errors Gracefully

When an API returns errors for specific accounts/permissions but shouldn't crash the whole sync:

```python
@override
def validate_response(self, response: requests.Response) -> None:
    if response.status_code == HTTP_FORBIDDEN and "specific error" in response.text.lower():
        self.logger.warning("Stream %s: descriptive message", self.name)
        return  # Don't raise
    super().validate_response(response)

@override
def parse_response(self, response: requests.Response) -> Iterable[dict]:
    if response.status_code == HTTP_FORBIDDEN:
        return  # Yield nothing
    yield from super().parse_response(response)
```

### Conditional Stream Registration

Streams are conditionally registered in `discover_streams()` based on config:

```python
def discover_streams(self) -> list:
    stream_list = [...]  # Core streams always registered

    if self.config.get("security_token"):
        stream_list.extend([...])  # Advanced Reports

    if self.config.get("reporting_api_token") and self.config.get("reporting_report_keys"):
        for raw_key in self.config["reporting_report_keys"].split(","):
            report_key = raw_key.strip()
            if report_key:
                stream_list.append(
                    streams.ReportingPlatformStream(self, report_key=report_key)
                )

    return stream_list
```

### Testing

**Test structure:**

| File | Type | Needs API Token? |
|------|------|-----------------|
| `tests/conftest.py` | Loads `.env` file | N/A |
| `tests/test_core.py` | SDK integration tests (all streams) | Yes |
| `tests/test_paginators.py` | Unit tests for 4 custom paginators | No |

**Integration tests** use `SuiteConfig(ignore_no_records=True)` because most streams return 0 records for a test publisher account.

**Integration tests are skipped in CI** (`include_*_tests=not CI`) since the Bearer token is short-lived and there's no OAuth refresh flow.

**To run tests locally:**
1. Put a valid `TAP_RAKUTENADVERTISING_AUTH_TOKEN` in `.env`
2. Run `uv run pytest`
3. Note: Bearer tokens from the Rakuten Developer Portal are short-lived (minutes)

### Known API Quirks

1. **Bearer tokens expire quickly** — Generated from https://developers.rakutenadvertising.com, they last only a few minutes. No OAuth refresh flow is implemented yet.
2. **Events API 30-day limit** — `process_date_start` must be within the last 30 days. Older data requires the "Signature Orders Report" from the Publisher Dashboard.
3. **Events API requires paired dates** — `process_date_start` and `process_date_end` must always be sent together.
4. **Events date format** — Must be `"YYYY-MM-DD HH:mm:ss"`, not ISO 8601.
5. **creative_categories with advertiser_id=-1** — Returns 500 "Invalid Merchant ID" for some accounts.
6. **publisher_contributed_conversions permissions** — Returns 403 if the account lacks entitlement.
7. **advertisers response has undocumented fields** — `network` and `logo_url` appear in API responses but not in the OpenAPI spec.
8. **Link Locator XML responses** — Use `ns1:` namespaced keys; `_strip_ns1()` helper removes the prefix.
9. **Reporting Platform CSV** — Uses UTF-8 BOM encoding (`utf-8-sig`), parsed with `csv.DictReader`.

## File Structure

```
tap-rakutenadvertising/
├── tap_rakutenadvertising/
│   ├── __init__.py
│   ├── tap.py              # Tap class, 18 config properties, discover_streams()
│   ├── client.py           # Base stream class, authenticator, 4 custom paginators
│   ├── streams.py          # 20+ stream classes, helpers, schema definitions
│   └── openapi.json        # OpenAPI schemas for core streams
├── tests/
│   ├── __init__.py
│   ├── conftest.py         # Loads .env via python-dotenv
│   ├── test_core.py        # SDK integration tests (needs API token)
│   └── test_paginators.py  # Unit tests for custom paginators (no API needed)
├── .env                    # Local secrets (gitignored) — single source of truth
├── .env.example            # Template for .env
├── config.json             # Alternative config for --config CLI usage (gitignored)
├── meltano.yml             # Meltano plugin definition, settings, validation groups
├── pyproject.toml          # Dependencies, tool config (ruff, pytest, mypy, tox)
├── README.md               # User-facing documentation
└── CLAUDE.md               # This file — AI agent development guide
```

## Common Pitfalls

1. **Rate Limiting**: The SDK's built-in `backoff` handles retries for 5xx errors automatically. Don't add custom retry logic.
2. **Token Expiry**: Bearer tokens expire in minutes. For development, generate a new token immediately before running tests.
3. **Schema Mismatches**: The `advertisers` stream warns about `network`/`logo_url` not in schema — this is expected.
4. **XML Parsing**: Always use `xmltodict.parse()` and handle both dict and list returns (single vs. multiple items).
5. **CSV Parsing**: Use `response.encoding = "utf-8-sig"` before `csv.DictReader` for Reporting Platform responses.
6. **State Management**: Don't modify state directly; use SDK methods like `get_starting_replication_key_value()`.
7. **Timezone Handling**: Use `datetime.timezone.utc` everywhere. Parse ISO 8601 with `.replace("Z", "+00:00")`.
8. **Ruff strictness**: All rules enabled. Run `ruff check` before every commit. Use `# noqa:` sparingly with specific codes.

## Bumping the Singer SDK Version

1. Check the [deprecation guide](https://sdk.meltano.com/en/latest/deprecation.html)
2. Update `singer-sdk~=X.Y` in `pyproject.toml`
3. Run `uv sync && uv run pytest`
4. Run `uv run pytest -W error::DeprecationWarning`
5. Check the [changelog](https://github.com/meltano/sdk/blob/main/CHANGELOG.md) for behavioral changes

## Reporting SDK Issues

File issues at https://github.com/meltano/sdk/issues/new/choose with:
- SDK version (`uv run tap-rakutenadvertising --version`)
- Python version
- Minimal reproduction case
