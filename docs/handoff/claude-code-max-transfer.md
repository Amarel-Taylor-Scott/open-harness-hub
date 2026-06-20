# Claude Code Max Transfer

Updated: 2026-06-09

Use this when handing the AI Done Right prototype family to Claude Code Max.

## Start Here

Read in this order:

1. `README.md`
2. `CLAUDE.md`
3. `docs/goals/aidoneright-portfolio-loop.md`
4. `docs/handoff/handoff-freshness.md`
5. `docs/handoff/openhub-surface-counts.md`
6. `docs/architecture/service-auth-and-consumption-model.md`
7. `dist/sites/openharness-design/START-HERE-CLAUDE-CODE.md`
8. `dist/sites/openharness-design/README.md`
9. `dist/sites/openharness-design/HANDOFF.md`
10. `dist/sites/openharness-design/CLAUDE-CODE.md`
11. `dist/sites/openharness-design/MARKETING.md`
12. `dist/sites/openharness-design/POSITIONING-AUDIT.md`
13. `dist/sites/openharness-design/BACKEND-STACK.md`
14. `dist/sites/openharness-design/UX-BACKLOG.md`
15. `dist/sites/openharness-design/shared/products.js`
16. `dist/sites/openharness-design/screens/INDEX.md`

Then inspect the Control Tower, parent site, Baltor, Teleon, all live hubs, all
private bench hubs, the method-spine docs, and the production-readiness gap.

## One-Line Goal

```text
/goal follow the instructions in docs/goals/aidoneright-portfolio-loop.md
```

## Current Portfolio Facts

- AI Done Right parent + Baltor + Teleon + 21 Open*Hub prototype surfaces
- 9 live Open*Hub registries
- 12 private bench hubs
- Full method spine: OpenReconciliationHub, OpenHardeningHub,
  OpenEnrichmentHub, OpenOptimizationHub, OpenVerificationHub
- `products.js` is the current design-bundle source of truth
- Demo Control Tower is a projection/control surface, not a truth writer
- Service-auth docs are part of the handoff and must stay current

## Proofs Before Transfer

```bash
python3 scripts/check_ai_done_right_surface_family.py --self-test
python3 scripts/check_service_auth_consumption_model.py --self-test
python3 scripts/check_handoff_docs_freshness.py --self-test
```

## Held Items

Do not deploy cloud, use production secrets, call network LLMs, run live
third-party diagnostics, or invent public URLs. Mark provider/cloud work as
candidate or HELD unless explicitly authorized.

Next loop prompt: use the one-line goal above, then pick one proof-backed
increment from the priority ladder in `docs/goals/aidoneright-portfolio-loop.md`.
