# Through-the-gateway journey — 2026-06-09T20:28:02.227Z

Gateway: http://127.0.0.1:8080 · Result: **PASS**

| # | step | ok | detail |
|---|---|---|---|
| 1 | gateway-serves-bundle | ok | gateway :8080 serves the static design bundle |
| 2 | core-health-through-gateway | ok | platform-core via /api/core/* — ok (llm anthropic=false, openai=false) |
| 3 | core-llm-501-no-bypass | ok | LLM plane returns 401 with no key set (no fake completion — honesty rule) |

Video: `artifacts/e2e/videos/gateway-journey.mp4`

_Through-the-gateway proof: one /api/<plane>/* namespace (handoff services.json). identity-through-gateway pending G-12 (host networking / authorized bind); core + sites proven here._