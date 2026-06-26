# Codex Transfer

> Historical snapshot (2026-06-09). Kept for lineage. It describes an earlier state and may name superseded things (for example Hanken Grotesk, surface_server as the renderer, OpenHubForAI as the headline brand). Current canonical: docs/BIBLE.md, docs/CURRENT-STATE.md, and docs/DESIGN-BIBLE.md.

Updated: 2026-06-09

This file is the Codex-facing transfer note for continuing the AI Done Right
portfolio loop.

## Paste This

```text
/goal follow the instructions in docs/goals/aidoneright-portfolio-loop.md
```

Use one proof-backed increment per cycle. Verify current state first, then fix
the highest-priority mismatch without cloud, installs, production secrets,
network LLM calls, fake URLs, or overclaims.

## Current State To Trust Only After Proof

- Source of truth: `dist/sites/openharness-design/shared/products.js`
- Current count: 24 design-family surfaces
- Parent/product split: AI Done Right parent + Baltor + Teleon
- OpenHubForAI count: 21 prototype surfaces
- Live hubs: 9
- Private bench hubs: 12
- Operational Demo Control Tower registry: 20 surfaces
- Static launch sites in `scripts/portfolio_lib.py`: 7

## Boundaries To Preserve

- AI Done Right is the parent/platform brand.
- Baltor governs context/truth.
- Teleon runs capabilities.
- Open*Hubs are registries/discovery surfaces only.
- Discovery is not trust.
- Output is not truth.
- Dashboards are projection-only.

## Required Files To Keep Fresh

- `README.md`
- `CLAUDE.md`
- `docs/goals/aidoneright-portfolio-loop.md`
- `docs/handoff/handoff-freshness.md`
- `docs/handoff/claude-code-max-transfer.md`
- `docs/handoff/openhub-surface-counts.md`
- `docs/architecture/service-auth-and-consumption-model.md`
- `architecture/service_auth_consumption_model.json`
- `dist/sites/openharness-design/START-HERE-CLAUDE-CODE.md`
- `dist/sites/openharness-design/HANDOFF.md`
- `dist/sites/openharness-design/CLAUDE-CODE.md`
- `dist/sites/openharness-design/MARKETING.md`
- `dist/sites/openharness-design/POSITIONING-AUDIT.md`
- `dist/sites/openharness-design/BACKEND-STACK.md`
- `dist/sites/openharness-design/UX-BACKLOG.md`
- `dist/sites/openharness-design/screens/INDEX.md`

## Checks

```bash
python3 scripts/check_ai_done_right_surface_family.py --self-test
python3 scripts/check_service_auth_consumption_model.py --self-test
python3 scripts/check_handoff_docs_freshness.py --self-test
```

If backend flywheel checks are not applicable to the prototype/design bundle,
mark them `NOT_APPLICABLE_DESIGN_REPO` and run static/design checks instead.
