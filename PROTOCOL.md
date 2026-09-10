# Urja Meter Ops — Portal Protocol

This document describes the observed behavior of the legacy Urja Meter Ops portal identified during the investigation for this assignment.

The portal is a browser-based SvelteKit application. Although it does not expose a documented public API, the browser communicates with several machine-readable endpoints that provide the required meter data.

---

## 1. Portal

```text
Base URL:
https://urja-ops.flockenergy.tech
```

The portal provides:

- Meter listing and search
- Meter details
- Network hierarchy
- Meter location
- Energy and consumption readings

The integration uses the portal as a read-only upstream system.

---

## 2. Authentication

The portal uses session-based authentication.

### Login

```http
POST /login
```

The login request uses:

```http
Content-Type: application/x-www-form-urlencoded
X-SvelteKit-Action: true
Accept: application/json
```

The form fields are:

```text
email
password
```

Example request structure:

```text
email=<email>&password=<password>
```

A successful login returns `200 OK` and creates a session cookie:

```text
__Secure-better-auth.session_token
```

The observed cookie includes:

```text
Max-Age=3600
Path=/
HttpOnly
Secure
SameSite=Lax
```

The API wrapper keeps this session server-side and does not expose the portal session cookie to API consumers.

---

## 3. Session Handling

The `PortalClient` uses a persistent HTTP client so the authentication cookie can be reused across requests.

If an authenticated request returns:

```http
401 Unauthorized
```

then the client:

1. Marks the current session as expired.
2. Logs in again.
3. Retries the original request once.

The retry is limited to a single attempt to avoid an infinite authentication loop.

---

## 4. Meter Listing

### UI Route

The visible meter page is:

```http
GET /meters
```

The page is rendered by SvelteKit.

The meter table contains:

* Meter
* Serial
* Make
* Phase
* Status
* DT

The observed dataset contains:

```text
total = 403
page size = 20
```

The UI therefore displays approximately 21 pages.

---

## Machine-Readable Endpoint

The actual meter data is retrieved from:

```http
GET /portal/meters/search?q=&page=1
```

This returns JSON.

Example:

```json
{
  "data": [
    {
      "meterId": "J100000",
      "serialNo": "SE33962",
      "make": "HPL",
      "phaseType": "single",
      "installStatus": "Decommissioned",
      "dtCode": "DT-001"
    },
    {
      "meterId": "J100001",
      "serialNo": "GE84132",
      "make": "L&T",
      "phaseType": "single",
      "installStatus": "Installed",
      "dtCode": "DT-002"
    }
  ],
  "total": 403,
  "page": 1,
  "pageSize": 20
}
```

The integration uses this endpoint instead of scraping the meter table HTML.

---

# 5. Meter Search

The search parameter is:

```text
q
```

It can be used to search by meter ID or serial number.

For example:

```http
GET /portal/meters/search?q=J100000&page=1
```

returns the matching meter.

Searching by serial number was also verified:

```http
GET /portal/meters/search?q=SE33962&page=1
```

This returned the meter associated with that serial number.

The clean API exposes the same functionality through:

```http
GET /api/v1/meters?q={query}
```

---

# 6. Meter Pagination

The portal uses:

```text
page
```

as the pagination parameter.

Example:

```http
GET /portal/meters/search?q=&page=2
```

Page 2 was verified successfully.

The observed page size is:

```text
20
```

The portal response provides:

```text
total
page
pageSize
```

The clean API maps these to:

```text
total
page
page_size
```

---

# 7. Meter Detail

## UI Route

The visible meter detail page is:

```text
/meters/{meter_id}
```

For example:

```text
/meters/J100000
```

The HTML page itself is not used for data extraction.

---

## SvelteKit Data Endpoint

The browser requests:

```http
GET /meters/{meter_id}/__data.json
```

During investigation, the browser request was observed as:

```http
GET /meters/J100000/__data.json?x-sveltekit-invalidated=001
```

The integration successfully uses:

```http
GET /meters/J100000/__data.json
```

---

# 8. SvelteKit Serialized Response

The meter detail response is not normal nested JSON.

It contains a structure similar to:

```json
{
  "type": "data",
  "nodes": [
    null,
    {},
    {
      "type": "data",
      "data": [...]
    }
  ]
}
```

The `data` array contains values that reference other positions in the same array.

For example:

```json
{
  "meterId": 1,
  "detail": 2,
  "hierarchy": 21
}
```

means that the actual values are stored at referenced positions in the array.

The detail parameters use the same approach:

```text
parameterName
parameterValue
```

where the values are references into the serialized data array.

The application therefore dereferences the SvelteKit response before returning it through the clean API.

---

# 9. Meter Detail Data

The observed meter detail response contains:

```text
Meter ID
Serial No
Make
Phase Type
Installation Status
Installation Type
```

For the investigated meter:

```text
Meter ID:
J100000

Serial No:
SE33962

Make:
HPL

Phase Type:
single

Installation Status:
Decommissioned

Installation Type:
Whole Current
```

The clean API converts these values into a structured response.

---

# 10. Network Hierarchy

The meter detail response also contains the network hierarchy.

Observed fields:

```text
Zone
Circle
Division
Subdivision
Sub Station
Feeder
DT
```

Example:

```text
Zone:
Jaipur Zone 1 (Z-01)

Circle:
Circle 1 (C-01)

Division:
Division 1 (D-01)

Subdivision:
Subdivision 1 (SD-01)

Sub Station:
Substation 1 (SS-01)

Feeder:
Feeder 1 (F-001)

DT:
Malviya Nagar DT 1 (DT-001)
```

The clean API exposes this hierarchy as part of:

```http
GET /api/v1/meters/{meter_id}
```

---

# 11. Meter Location

The portal provides meter coordinates through:

```http
GET /portal/meters/{meter_id}/geo
```

For example:

```http
GET /portal/meters/J100000/geo
```

Observed response:

```json
{
  "data": {
    "latitude": "26.938961002479868",
    "longitude": "75.83095696146852"
  }
}
```

The portal returns coordinates as strings.

The clean API converts them to numeric values:

```json
{
  "meter_id": "J100000",
  "latitude": 26.938961002479868,
  "longitude": 75.83095696146852
}
```

---

# 12. Meter Energy / Consumption

The portal provides energy readings through:

```http
GET /portal/meters/{meter_id}/energy
```

For example:

```http
GET /portal/meters/J100000/energy
```

Observed response structure:

```json
{
  "data": [
    {
      "timestamp": "23/06/2026 23:30",
      "kwh": "48438.74",
      "kvah": "52313.84",
      "voltR": "226"
    }
  ]
}
```

---

# 13. Energy Reading Fields

The portal returns:

```text
timestamp
kwh
kvah
voltR
```

The clean API maps them to:

| Portal field | Clean API field |
| ------------ | --------------- |
| `timestamp`  | `timestamp`     |
| `kwh`        | `kwh`           |
| `kvah`       | `kvah`          |
| `voltR`      | `voltage_r`     |

The numeric values are returned by the portal as strings and are converted to numbers by the API.

---

# 14. Energy Timestamp Format

The portal uses:

```text
DD/MM/YYYY HH:mm
```

Example:

```text
23/06/2026 23:30
```

The clean API converts this to an ISO-style datetime:

```text
2026-06-23T23:30:00
```

The source timestamp does not contain timezone information.

Therefore, the API preserves it as a timezone-naive datetime rather than assuming a timezone.

---

# 15. Observed Energy Dataset

For the investigated meter, the energy endpoint returned:

```text
337 readings
```

The observed range was:

```text
23/06/2026 23:30
through
30/06/2026 23:30
```

The readings occur at 30-minute intervals.

The observed `kwh` and `kvah` values increase over time, while `voltR` varies between readings.

No verified date-range query parameters were identified during the investigation.

Therefore, the clean API currently returns the readings provided by the portal without adding unsupported date filtering.

---

# 16. Portal-to-API Mapping

| Clean API                                   | Portal                                 |
| ------------------------------------------- | -------------------------------------- |
| `GET /api/v1/meters`                        | `GET /portal/meters/search?q=&page=`   |
| `GET /api/v1/meters/{meter_id}`             | `GET /meters/{meter_id}/__data.json`   |
| `GET /api/v1/meters/{meter_id}/location`    | `GET /portal/meters/{meter_id}/geo`    |
| `GET /api/v1/meters/{meter_id}/consumption` | `GET /portal/meters/{meter_id}/energy` |

Authentication:

```http
POST /login
```

---

# 17. Portal Quirks

## UI routes are different from data endpoints

The visible meter page:

```text
/meters
```

does not need to be scraped.

The actual meter data comes from:

```text
/portal/meters/search
```

---

## Meter details use SvelteKit serialization

The detail endpoint:

```text
/meters/{meter_id}/__data.json
```

uses indexed references inside a data array.

The API must dereference these values before exposing them.

---

## Numeric values are strings

The portal returns:

```text
latitude
longitude
kwh
kvah
voltR
```

as strings.

The clean API converts them to numeric values.

---

## Timestamps are not ISO formatted

The portal uses:

```text
DD/MM/YYYY HH:mm
```

The clean API converts them to ISO-style datetime values.

---

## No timezone is provided

The observed energy timestamps contain no timezone information.

No timezone is assumed by the API.

---

## Session expiry

The authentication cookie has a finite lifetime.

The client therefore supports one automatic re-login when an authenticated request receives `401`.

---

# 18. Error Handling

The portal client translates low-level failures into application exceptions.

```text
PortalError
├── PortalAuthenticationError
├── PortalNotFoundError
└── PortalUnavailableError
```

### Authentication failure

A failed portal authentication is represented as:

```text
PortalAuthenticationError
```

The clean API returns:

```http
502 Bad Gateway
```

---

### Portal resource not found

A portal `404` is represented as:

```text
PortalNotFoundError
```

The clean API returns:

```http
404 Not Found
```

with:

```json
{
  "detail": "Meter not found."
}
```

---

### Timeout

A portal timeout becomes:

```text
PortalUnavailableError
```

and the clean API returns:

```http
502 Bad Gateway
```

---

### Network failure

Connection/request failures are also represented as:

```text
PortalUnavailableError
```

and returned as:

```http
502 Bad Gateway
```

---

### Invalid JSON

If an expected JSON endpoint returns invalid JSON, the portal client treats it as an upstream failure.

---

### Invalid response structure

A syntactically valid response can still be unusable if it does not contain the expected fields or SvelteKit structure.

The normalization layer validates the response before returning it.

The clean API returns:

```http
502 Bad Gateway
```

for an invalid upstream payload.

---

# 19. Data Normalization

The clean API intentionally does not mirror the portal's field names or serialization format.

### Meter

Portal:

```json
{
  "meterId": "J100000",
  "serialNo": "SE33962",
  "make": "HPL",
  "phaseType": "single",
  "installStatus": "Decommissioned",
  "dtCode": "DT-001"
}
```

Clean API:

```json
{
  "meter_id": "J100000",
  "serial_number": "SE33962",
  "make": "HPL",
  "phase": "single",
  "status": "Decommissioned",
  "dt_code": "DT-001"
}
```

### Location

Portal:

```json
{
  "latitude": "26.938961002479868",
  "longitude": "75.83095696146852"
}
```

Clean API:

```json
{
  "latitude": 26.938961002479868,
  "longitude": 75.83095696146852
}
```

### Consumption

Portal:

```json
{
  "timestamp": "23/06/2026 23:30",
  "kwh": "48438.74",
  "kvah": "52313.84",
  "voltR": "226"
}
```

Clean API:

```json
{
  "timestamp": "2026-06-23T23:30:00",
  "kwh": 48438.74,
  "kvah": 52313.84,
  "voltage_r": 226.0
}
```

---

# 20. Important Implementation Decisions

## Use machine-readable endpoints

The integration uses the portal's JSON/data endpoints instead of scraping HTML.

This reduces coupling to the portal's UI.

## Keep portal logic isolated

Portal-specific paths, authentication, session handling, and upstream errors are contained inside `PortalClient`.

## Normalize at the boundary

Portal-specific field names, types, timestamps, and SvelteKit serialization are converted before data reaches the clean API layer.

## Do not expose portal internals

Consumers only interact with the clean `/api/v1` endpoints.

They do not need to understand:

* SvelteKit
* `__data.json`
* Portal-specific routes
* Session cookies
* Serialized reference arrays

---

# 21. Known Unknowns

The following behavior was not established during the investigation and is therefore not assumed by the implementation.

### Consumption date filtering

No verified `from`/`to` parameters were identified for the energy endpoint.

### Caching

No freshness requirements were established.

### Bulk extraction

A separate bulk dataset mechanism was not implemented or relied upon.

### Hierarchy consistency

The hierarchy was observed in meter details, but a complete investigation of hierarchy consistency across all meters was outside the core scope.

### Invalid meter behavior

An invalid meter ID does not necessarily produce a clean HTTP `404` from the SvelteKit detail endpoint. The endpoint can return a successful HTTP response whose data does not match the expected structure.

The client therefore validates the response structure rather than relying only on the HTTP status code.

---

# 22. Current Integration Scope

The current integration supports:

```text
Authentication
    |
    +-- Login
    +-- Session cookie
    +-- Session re-authentication

Meters
    |
    +-- Search
    +-- Pagination
    +-- Details
    +-- Network hierarchy
    +-- Location
    +-- Consumption
```

The integration intentionally does not attempt to reproduce the entire portal.

Its purpose is to provide a stable API boundary around the useful meter data while keeping the legacy portal's implementation details isolated.
