# Source approval and collection policy

Reviewed: 30 October 2026  
Purpose: official transport advisory monitoring for TransitNotice.

## Collection rules enforced by the application

- Only the HTTPS endpoint configured in each named source adapter is requested.
- The adapter checks that pagination or redirects remain on the source's official host.
- Requests use a short timeout, a three-attempt ceiling and exponential backoff for server errors or rate limits.
- No login, CAPTCHA, access-control bypass, private data collection or browser automation is used.
- A source error creates a failed collection run. It does not delete older notices or treat old notices as live.
- Live scheduling has a five-minute minimum. The supplied configuration uses ten minutes.

## Approved source adapters

| Source | Official endpoint used | Fields mapped | Permission and limits | Default state |
| --- | --- | --- | --- | --- |
| Massachusetts Bay Transportation Authority (MBTA) | `https://api-v3.mbta.com/alerts` | alert ID, headers/descriptions, route and stop entities, active periods, created time, effect/cause and source URL | MBTA documents its V3 API as an alert interface. Anonymous requests have stricter limits; its response headers expose current rate-limit values. An optional backend-only key can increase the limit. | Disabled while demo mode is on |
| Chicago Transit Authority (CTA) | `https://lapi.transitchicago.com/api/1.0/alerts.aspx?outputType=JSON` | alert ID, headline, descriptions, impact, event window, alert URL and affected services | CTA’s Customer Alerts API documentation says the developer must read and agree to its terms. TransitNotice leaves this adapter locked until `CTA_TERMS_ACCEPTED=true` is intentionally set by the project owner. | Locked |

## Evidence checked

- MBTA's official V3 API portal identifies the API as its schedule, real-time and alert information interface and says a key is not required for experimentation. Its official Swagger definition lists `GET /alerts`, documents the `filter[datetime]` option and documents rate-limit response headers.
- CTA's official Customer Alerts documentation identifies the detailed alerts endpoint, describes its JSON output, maps alert IDs, descriptions, event dates and affected services, and requires agreement to its terms of use.

This review confirms that the application targets official public interfaces. It does not claim an individual agency has approved a particular deployment. The project owner must review current terms again before enabling a live source.

## Refresh and failure policy

1. A scheduler checks enabled sources at the configured interval.
2. A successful complete snapshot upserts records by `(agency, external_id)`.
3. An unchanged record only updates observed and confirmed timestamps.
4. A changed record creates a new revision and one alert delivery key.
5. An active record absent from one complete snapshot is retained with a missing counter.
6. It becomes withdrawn after the second consecutive complete absence.
7. A request failure does not increase the missing counter.
8. If no successful source check arrives within `STALE_AFTER_MINUTES`, the source and its notices are labelled stale.

## Time zones

All stored timestamps use timezone-aware values. MBTA time values without an offset are interpreted in `America/New_York`; CTA time values without an offset are interpreted in `America/Chicago`; display time is converted by the visitor's browser. This rule is documented so the same input produces the same status during testing.

## Notes for a live deployment

- Replace the local development PostgreSQL password.
- Put API keys and SMTP credentials only in the backend `.env`.
- Keep the refresh interval conservative and follow every agency's current rate limit.
- Attribute source data where the agency requests or recommends it.
- Monitor failure logs and stop a source if its current terms no longer permit the intended use.
