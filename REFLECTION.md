# Reflection

## 1. What assumptions did you make?

I treated the Urja Meter Ops portal as a read-only upstream dependency and designed the API to expose clean, stable consumer-facing responses rather than mirror portal-specific routes or formats.

I also avoided assuming a timezone for energy timestamps because the portal does not provide one, and I preserved the observed pagination behavior of 20 meters per page to remain faithful to the upstream system.

## 2. Which part was the most difficult, and how did you get unstuck?

The most difficult part was the meter detail endpoint. The critical data was embedded in SvelteKit's `__data.json` response, which uses indexed references rather than standard nested JSON objects.

I resolved this by inspecting the browser's network traffic and response structure, then implementing a normalization layer to resolve those references into clean Pydantic models suitable for the API.

## 3. If you had another day, what would you improve?

I would strengthen reliability and observability by:

- Testing a wider range of real meter responses
- Adding structured logging and metrics
- Investigating consumption date filtering behavior more deeply
- Evaluating caching for meter and energy data
- Adding stronger integration tests against the live portal

## 4. What mistake did you make while solving this?

The main mistake was initially focusing on the visible portal screens instead of the underlying network requests. That led me toward an HTML-scraping approach, which was unnecessary and less robust.

Once I examined the live traffic, I identified the more reliable machine-readable endpoints, including `/portal/meters/search` and the SvelteKit `__data.json` payload. This shift simplified the integration and made the implementation more dependable.

## 5. If you were reviewing your own submission, what would you criticise?

The primary limitation is that the solution remains focused on the core assignment scope. It does not yet include caching, bulk ingestion, advanced filtering, a local index, or a frontend layer.

The automated tests are also mocked, so they may not detect future changes in the live portal. A production-ready version would benefit from controlled integration testing and stronger observability.

Overall, the implementation remains intentionally small and well-structured, with a clear separation between the legacy portal protocol and the clean consumer-facing API.