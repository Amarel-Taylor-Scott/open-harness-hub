# Events + A/B loop (E2E) — 2026-06-09T22:46:33.888Z

App http://127.0.0.1:8000 → events plane http://127.0.0.1:9420 · Result: **PASS**

| # | step | ok | detail |
|---|---|---|---|
| 1 | landing-page-view-and-exposure | ok | landing rendered; builder_cta variant=A (sticky), page+exposure beaconed |
| 2 | trigger-builder-cta-conversion | ok | builder_cta conversion beaconed |
| 3 | read-ab-summary-from-plane | ok | A/B readout LIVE — builder_cta:A exp=1 conv=1 |

Video: `artifacts/e2e/videos/events-ab-flow.mp4`

_Real browser → beacon → live events plane → /summary A/B readout. anon ids only; no PII._