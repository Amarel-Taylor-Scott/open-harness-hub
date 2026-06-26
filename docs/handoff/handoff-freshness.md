# AI Done Right Handoff Freshness

> Historical snapshot (2026-06-09). Kept for lineage. It describes an earlier state and may name superseded things (for example Hanken Grotesk, surface_server as the renderer, OpenHubForAI as the headline brand). Current canonical: docs/BIBLE.md, docs/CURRENT-STATE.md, and docs/DESIGN-BIBLE.md.

Updated: 2026-06-09

This is the tracked handoff freshness page for the AI Done Right prototype
family. The design bundle remains the detailed source; this page records the
current transfer state and the proof commands to run before handing the repo to
Claude Code Max, Codex, or another coding agent.

## Current Verified Shape

- Parent brand: AI Done Right (`aidoneright.dev`)
- Products: 2 - Baltor and Teleon
- OpenHubForAI prototype surfaces: 21
- Live OpenHubForAI registries: 9
- Private bench hubs: 12
- Total design-family surfaces: 24 - parent + 2 products + 21 OpenHubForAI registries
- Operational Demo Control Tower registry surfaces: 20
- Static launch sites served by `scripts/portfolio_lib.py`: 7

Authoritative sources:

- `dist/sites/openharness-design/shared/products.js`
- `dist/sites/openharness-design/README.md`
- `dist/sites/openharness-design/START-HERE-CLAUDE-CODE.md`
- `dist/sites/openharness-design/HANDOFF.md`
- `dist/sites/openharness-design/CLAUDE-CODE.md`
- `dist/sites/openharness-design/screens/INDEX.md`
- `.agent/aidoneright-current-state-verification.json`

## Required Transfer Contents

The handoff bundle must include or point to:

- `README.md`
- `START-HERE-CLAUDE-CODE.md`
- `HANDOFF.md`
- `CLAUDE.md` / `CLAUDE-CODE.md`
- `MARKETING.md`
- `POSITIONING-AUDIT.md`
- `BACKEND-STACK.md`
- `UX-BACKLOG.md`
- `products.js`
- screenshots/screens index: `screens/INDEX.md`
- Control Tower
- parent site
- Baltor
- Teleon
- all live hubs
- all private bench hubs
- method-spine docs
- service-auth docs
- production-readiness gap
- next loop prompt

## Boundary State

AI Done Right is the parent/platform brand. The legacy
`contextiseverything` slug remains a path/code identifier where needed.

Baltor governs context and truth. Teleon runs capabilities. OpenHubForAI registries are
registries and discovery surfaces only: discovery is not trust, output is not
truth, and benchmark result is not promotion authority. Dashboards and control
towers are projection-only.

## Service-Auth Handoff

Production work must carry the service-auth model forward:

- Architecture brief: `docs/architecture/service-auth-and-consumption-model.md`
- Policy: `architecture/service_auth_consumption_model.json`
- Proof: `python3 scripts/check_service_auth_consumption_model.py --self-test`

No raw secrets belong in prototypes, docs, logs, receipts, screenshots, or
browser surfaces. Use secret refs and redacted examples only.

## Freshness Proof

Run:

```bash
python3 scripts/check_ai_done_right_surface_family.py --self-test
python3 scripts/check_service_auth_consumption_model.py --self-test
python3 scripts/check_handoff_docs_freshness.py --self-test
```

If these disagree, repair the source of truth or the handoff doc before
launching another loop.
