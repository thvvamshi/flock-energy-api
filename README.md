# Flock Energy API

A production-ready FastAPI service that wraps the legacy Urja Meter Ops portal and exposes a clean, structured REST API for meter data access.

## Overview

This project provides a lightweight integration layer between a modern API and the legacy portal without exposing the portal's internal implementation details. It is designed for read-only access to meter metadata, location information, and energy consumption data.

## Features

- Meter listing, search, and pagination
- Meter detail retrieval and network hierarchy
- Meter location lookup
- Energy and consumption reading endpoints
- Session-based authentication against the portal
- Automatic re-authentication on session expiry
- Upstream error handling and normalization
- Pydantic-based response models
- OpenAPI-generated documentation
- Automated test coverage using mocked upstream responses

## Architecture

```text
Client
  |
  v
FastAPI
  |
  v
PortalClient
  |
  v
Urja Meter Ops
```

Portal-specific logic is isolated in `PortalClient`, while `models.py` normalizes upstream responses into clean application-facing models.

## Project Structure

```text
flock-energy-api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── client.py
│   ├── models.py
│   └── config.py
├── tests/
│   └── test_app.py
├── openapi.json
├── PROTOCOL.md
├── REFLECTION.md
├── README.md
├── requirements.txt
├── pyproject.toml
├── uv.lock
├── .env.example
├── .gitignore
└── .env
```

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Setup

Clone the repository:

```bash
git clone <repository-url>
cd flock-energy-api
```

Install dependencies:

```bash
uv sync
```

Create a local `.env` file from `.env.example`:

```env
URJA_BASE_URL=https://urja-ops.flockenergy.tech
URJA_EMAIL=your-email
URJA_PASSWORD=your-password
REQUEST_TIMEOUT=10
```

> Never commit `.env` files or expose portal credentials in shared repositories.

## Run the API

Start the service:

```bash
uv run uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API docs:

```text
http://127.0.0.1:8000/docs
```

OpenAPI specification:

```text
openapi.json
```

## API Endpoints

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/meters` | List and search meters |
| `GET` | `/api/v1/meters/{meter_id}` | Retrieve meter details and hierarchy |
| `GET` | `/api/v1/meters/{meter_id}/location` | Retrieve meter coordinates |
| `GET` | `/api/v1/meters/{meter_id}/consumption` | Retrieve energy readings |

### Example Request

```bash
curl "http://127.0.0.1:8000/api/v1/meters?q=J100000"
```

### Example Response

```json
{
  "items": [
    {
      "meter_id": "J100000",
      "serial_number": "SE33962",
      "make": "HPL",
      "phase": "single",
      "status": "Decommissioned",
      "dt_code": "DT-001"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

## Testing

Run the test suite:

```bash
uv run pytest
```

Current status:

```text
27 passed
```

The tests use mocked upstream responses so they remain isolated from the live portal and do not depend on external service availability.

## Design Decisions

- No HTML scraping: the service uses discovered machine-readable endpoints exposed by the portal.
- Small, maintainable architecture: the implementation stays focused on the assignment without unnecessary abstraction.
- API normalization: portal-specific field names, numeric strings, timestamps, and serialized payloads are converted into consistent API models.
- Session resilience: the client automatically re-authenticates once when the portal session expires.
- No caching: omitted because no upstream freshness policy was defined in the requirements.
- No frontend: intentionally kept outside the scope of the API service.

## Assumptions and Limitations

- The portal is treated as read-only.
- Energy timestamps do not include timezone information, so no timezone is assumed.
- The portal's observed page size is 20.
- Consumption date filtering was not implemented because no verified upstream date-filter mechanism was identified.
- The integration depends on the portal's current response formats and may require updates if those formats change.

## Documentation

- [`PROTOCOL.md`](PROTOCOL.md) — reverse-engineered portal behavior, authentication flow, endpoints, response formats, and edge cases.
- [`REFLECTION.md`](REFLECTION.md) — engineering notes and implementation reflections.
- [`openapi.json`](openapi.json) — generated OpenAPI schema for the API.

## Future Improvements

Potential enhancements if the project expands:

- Broader live-portal integration coverage
- Structured logging and metrics
- More granular upstream error handling
- Caching and freshness policy support
- Optional consumption date filtering
- Local indexing for advanced cross-meter queries

## Status

The core assignment requirements are implemented and validated with automated tests. Optional extension work was intentionally kept out of scope to preserve a small, maintainable, and focused solution.

A clean REST API wrapper around the legacy **Urja Meter Ops** portal, providing programmatic access to meter information without exposing the portal's internal implementation details.

## Features

- Meter listing, search, and pagination
- Meter details and network hierarchy
- Meter location
- Energy/consumption readings
- Session-based portal authentication
- Automatic re-authentication on session expiry
- Upstream error handling
- Pydantic-based response normalization
- OpenAPI documentation
- Automated tests

## Architecture

```text
Client
  |
  v
FastAPI
  |
  v
PortalClient
  |
  v
Urja Meter Ops
````

Portal-specific communication is isolated in `PortalClient`, while `models.py` converts upstream responses into clean API models.

## Project Structure

```text
flock-energy-api/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── client.py
│   ├── models.py
│   └── config.py
├── tests/
│   └── test_app.py
├── openapi.json
├── PROTOCOL.md
├── REFLECTION.md
├── README.md
├── requirements.txt
├── pyproject.toml
├── uv.lock
├── .env.example
└── .gitignore
```

## Requirements

* Python 3.12+
* [uv](https://docs.astral.sh/uv/)

## Setup

Clone the repository:

```bash
git clone <repository-url>
cd flock-energy-api
```

Install dependencies:

```bash
uv sync
```

Create `.env` from `.env.example`:

```env
URJA_BASE_URL=https://urja-ops.flockenergy.tech
URJA_EMAIL=your-email
URJA_PASSWORD=your-password
REQUEST_TIMEOUT=10
```

> Never commit `.env` or expose portal credentials.

## Run

```bash
uv run uvicorn app.main:app --reload
```

API:

```text
http://127.0.0.1:8000
```

Interactive documentation:

```text
http://127.0.0.1:8000/docs
```

OpenAPI specification:

```text
openapi.json
```

## API

| Method | Endpoint                                | Description                 |
| ------ | --------------------------------------- | --------------------------- |
| `GET`  | `/health`                               | Health check                |
| `GET`  | `/api/v1/meters`                        | List/search meters          |
| `GET`  | `/api/v1/meters/{meter_id}`             | Meter details and hierarchy |
| `GET`  | `/api/v1/meters/{meter_id}/location`    | Meter coordinates           |
| `GET`  | `/api/v1/meters/{meter_id}/consumption` | Energy readings             |

### Example

```bash
curl "http://127.0.0.1:8000/api/v1/meters?q=J100000"
```

Example response:

```json
{
  "items": [
    {
      "meter_id": "J100000",
      "serial_number": "SE33962",
      "make": "HPL",
      "phase": "single",
      "status": "Decommissioned",
      "dt_code": "DT-001"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

## Testing

Run the test suite:

```bash
uv run pytest
```

Current suite:

```text
27 passed
```

Tests use mocked upstream responses so they do not depend on the live portal.

## Design Decisions

* **No HTML scraping:** uses the portal's discovered machine-readable endpoints.
* **Small architecture:** keeps the implementation focused on the assignment rather than adding unnecessary layers.
* **API normalization:** portal-specific field names, numeric strings, timestamps, and SvelteKit serialization are converted into clean API models.
* **Session recovery:** automatically re-authenticates once when the portal session expires.
* **No caching:** omitted because upstream freshness requirements were not established.
* **No frontend:** intentionally outside the core API scope.

## Assumptions & Limitations

* The portal is treated as read-only.
* Energy timestamps do not contain timezone information, so no timezone is assumed.
* The observed portal page size is 20.
* Consumption date filtering was not implemented because no verified upstream date-filter mechanism was identified.
* The integration depends on the portal's current response formats and may require updates if the portal changes.

## Documentation

* [`PROTOCOL.md`](PROTOCOL.md) — reverse-engineered portal behavior, authentication, endpoints, response formats, and quirks.
* [`REFLECTION.md`](REFLECTION.md) — engineering reflection and lessons learned.
* [`openapi.json`](openapi.json) — OpenAPI specification for the clean API.

## Future Improvements

With more time, I would add:

* More real-portal integration coverage
* Structured logging and metrics
* More granular upstream error handling
* Appropriate caching/freshness policies
* Optional consumption date filtering
* Local indexing for advanced cross-meter queries

## Status

Core assignment requirements are implemented and tested. Optional extensions were intentionally kept out of scope to maintain a small, maintainable solution.

