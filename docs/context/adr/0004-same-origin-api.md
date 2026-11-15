# ADR 0004: API behind the same CloudFront domain

- Status: accepted · Date: 2026-11-15

**Decision.** CloudFront routes `/api/*` to the HTTP API (no caching, all headers but Host forwarded) and
everything else to S3. A CloudFront Function serves `index.html` for client-side routes.

**Why.** One URL, no CORS, local dev proxies the same paths to the demo.
