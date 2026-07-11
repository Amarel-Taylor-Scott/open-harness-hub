# Local preview — not production

These portfolio sites are **static local previews**, not production hosting.

- Served by `python -m http.server` on 127.0.0.1 (ports 9100-9104) for review.
- TryCloudflare URLs are **temporary, random session URLs** that die with the tunnel process — fine for
  sharing a preview, not for production.
- The pages store **no data and write no truth** (no forms, no POST, no mutation endpoints). They describe the
  products; the actual dashboards/demos are governed by their own systems.
- No external JS/CSS/CDN/analytics/secrets.

## Path to production (next, after brand/trademark clearance)
1. Register/confirm domains: `teleon.dev` (owned), `baltor.ai`, `openharnesshub.org`, the holding-company domain.
2. Named Cloudflare tunnels (or static hosting) bound to those domains — durable URLs.
3. Per-company deployment in the same region/private network but separable accounts (see
   `docs/portfolio/infrastructure-topology.md`).
