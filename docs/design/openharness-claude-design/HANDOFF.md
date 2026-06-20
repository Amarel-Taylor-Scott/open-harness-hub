# AI Done Right - Tracked Design Handoff

This tracked handoff supersedes the older three-brand OpenHarness prototype
brief. The current local design bundle is:

```text
dist/sites/openharness-design/
```

Read order for Claude Code Max:

1. `docs/codex/ai-done-right-family-polish-goal.md`
2. `docs/architecture/service-auth-and-consumption-model.md`
3. `dist/sites/openharness-design/START-HERE-CLAUDE-CODE.md`
4. `dist/sites/openharness-design/README.md`
5. `dist/sites/openharness-design/CLAUDE-CODE.md`
6. `dist/sites/openharness-design/HANDOFF.md`
7. `dist/sites/openharness-design/IMPLEMENTATION-GUIDANCE.md`
8. `dist/sites/openharness-design/BACKEND-STACK.md`

## Current Contract

AI Done Right is a branded house:

- Parent: AI Done Right.
- Products: Baltor.ai and Teleon.dev.
- Open funnel: 9 live Open*Hub registries.
- Private bench: 7 substrate registries plus 5 Baltor method hubs.
- Shared foundation: tokens, primitives, site kit, `makeHub`, and
  `shared/products.js`.

The full current family is parent + 2 products + 21 Open*Hubs. Recompute before
editing docs or screenshots.

Focused proof:

```bash
python3 scripts/check_ai_done_right_surface_family.py --self-test
```

## Implementation Priorities

1. Port `shared/oh-tokens.css` and `shared/oh-components.css`.
2. Port `shared/oh-site.jsx` as the reusable site/account kit.
3. Port `shared/oh-hub.jsx` as the config-driven registry engine.
4. Bring over Teleon first to prove the kit.
5. Bring over the 9 live hubs and their bespoke hooks.
6. Bring over the parent portfolio and Demo Control Tower.
7. Bring over Baltor and the 12 private-bench hubs.
8. Implement the backend, service auth, audit, billing, and data model.

## Baltor Spine

The private-first method hubs complete the Baltor engine:

```text
Reconcile -> Harden -> Enhance -> Optimize -> Verify
```

The corresponding hubs are:

```text
OpenReconciliationHub.io
OpenHardeningHub.io
OpenEnrichmentHub.io
OpenOptimizationHub.io
OpenVerificationHub.io
```

These are standards/lead-gen registry surfaces. Baltor remains the context
truth authority.

## Service Auth Requirement

Do not treat API keys as the internal service-to-service model. Production
needs:

- user OIDC/session auth;
- scoped external API keys or OAuth clients;
- service accounts and short-lived scoped service tokens;
- mTLS/SPIFFE or cloud workload identity for internal production calls;
- private bench access enforcement;
- tenant, object, purpose, and data-class authorization;
- audit events and receipts for privileged calls.

The current architecture brief is:

```text
docs/architecture/service-auth-and-consumption-model.md
```

## Verification Gates

- Design Acceptance Scorecard stays green.
- No horizontal overflow.
- Dark mode works across the family.
- Brand and accent values come from owning sources.
- Route maps and surface counts are generated or recomputed.
- Private-first is not claimed as production security until enforced
  server-side.
