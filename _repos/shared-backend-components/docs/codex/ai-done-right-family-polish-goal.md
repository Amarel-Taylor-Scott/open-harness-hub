# Goal: AI Done Right Family Polish And Research Loop

This is the Codex/Claude Code Max handoff goal for polishing and researching
the full AI Done Right portfolio family: Baltor, Teleon, the parent portfolio,
OpenHubForAI, every OpenHubForAI registry, and the shared backend/security
plane that makes the prototypes production-real.

The work is not limited to today's visible static pages. Each loop must discover
the current surfaces from their owning registries and files, then improve the
highest-impact product, design, backend, auth, research, or handoff gap.

## Mission

Turn the AI Done Right family from high-fidelity prototypes plus repo
architecture into a production-ready implementation brief:

- **AI Done Right** is the parent/platform company at `aidoneright.dev`.
- **Baltor.ai** is the paid context-assurance product: verified, current,
  reconciled, optimized, and provable context for AI-assisted work.
- **Teleon.dev** is the paid purpose-driven runtime: intent-native,
  eval-gated, self-adaptive capability execution.
- **OpenHubForAI registries** are the open top-of-funnel registries. Discovery is not trust;
  every open artifact remains candidate until governed by the right product
  layer.
- **The full Baltor engine spine** is represented as private-first method hubs:
  Reconcile, Harden, Enhance, Optimize, Verify.
- **The service plane** has a credible auth, API key, service-account,
  workload-identity, audit, and tenant-boundary model.

## Read First

1. `AGENTS.md`
2. `CLAUDE.md`
3. `README.md`
4. `docs/codex/baltor-always-in-memory-context.md`
5. `docs/codex/baltor-clean-context.md`
6. `_repos/shared-backend-components/context/codex/repo-polish-loop-goal.md`
7. `docs/architecture/service-auth-and-consumption-model.md`
8. `services/registry.yaml`
9. `architecture/brand.json`
10. `architecture/company_portfolio_map.json`
11. `architecture/demo_surface_registry.json`
12. `docs/BIBLE.md` (north star)
13. `docs/DESIGN-BIBLE.md` (the UI: shared kit `web/<brand>/kit` + the showcase renderer, light theme + Inter)
14. `docs/INTEGRATION-BIBLE.md` (FE↔BE seams + deploy)
15. `_repos/aidoneright/context/design/aidoneright-claude-design/START-HERE.md`
16. `_repos/aidoneright/context/design/aidoneright-claude-design/README.md`
17. `dist/sites/aidoneright-design/README.md` (the richer reference bundle)
18. `dist/sites/aidoneright-design/Design Acceptance Scorecard.html` (the branded-house gate)

Focused proof:

```bash
python3 scripts/check_ai_done_right_surface_family.py --self-test
```

This reads `dist/sites/aidoneright-design/shared/products.js`, verifies the
product/open/private layer split, confirms the 9 live OpenHubForAI registries, 12 private
bench hubs, five Baltor method hubs, and checks that every referenced prototype
HTML exists.

When these disagree, do not guess. Resolve drift at the owning source or record
the contradiction and pick the smallest durable repair.

## Surface Family

Recompute the surface inventory every loop. Do not preserve stale fixed counts.
As of the 2026-06-09 handoff, the design family is:

- Parent: AI Done Right, legacy path `context-is-everything/`.
- Products: Baltor.ai and Teleon.dev.
- Live OpenHubForAI registries: OpenContextHub, OpenSkillsHub, OpenToolsHub,
  OpenSkillToTool, OpenMCPHub, OpenCompressionHub, OpenBenchmarkHub,
  OpenReviewHub, OpenHubForAI.
- Private bench: OpenTemplatesHub, OpenEndpointHub, OpenEnvironmentHub,
  OpenSandboxHub, OpenAgentHub, OpenReceiptHub, OpenStateHub.
- Baltor method hubs: OpenReconciliationHub, OpenHardeningHub,
  OpenEnrichmentHub, OpenOptimizationHub, OpenVerificationHub.

The current high-level total is parent + 2 products + 21 OpenHubForAI registries = 24
surfaces. Treat this as a checked snapshot, not a durable magic value.

## Baltor Spine

The five method hubs open Baltor's context-governance engine as private-first
registries:

| Hub | Stage | Hero | Method family |
| --- | --- | --- | --- |
| OpenReconciliationHub.io | Reconcile | Cluster alignment. | dedupe; link evidence; surface conflicts |
| OpenHardeningHub.io | Harden | Robust object hardening. | detect fragile values; create durable objects; refresh over time |
| OpenEnrichmentHub.io | Enhance | Context enrichment. | add metadata; connect objects; increase robustness |
| OpenOptimizationHub.io | Optimize | Pack shaping. | summarize; structure; rank |
| OpenVerificationHub.io | Verify | Cited and provable. | bind claims to sources; prove by hash; hold out the unprovable |

These are private-first, config-only `makeHub` surfaces. They are design
artifacts and lead-gen/standards surfaces; they do not become truth authorities.
Baltor governs truth.

## Workstreams

Each loop should pick the highest-impact failing workstream.

1. **Surface fidelity**
   - Open every route that the handoff claims exists.
   - Run `python3 scripts/check_ai_done_right_surface_family.py --self-test`
     before trusting handoff counts or route-family claims.
   - Verify no horizontal overflow, no text collisions, clean dark mode, and
     shared-token compliance.
   - Use the Design Acceptance Scorecard as the branded-house gate.

2. **Baltor product depth**
   - Improve the engine pages, guided demos, source handles, receipts,
     conflict disclosure, freshness labels, and context-pack examples.
   - Preserve the rule: held-out contradictions are disclosed, never served as
     the winning answer.

3. **Portfolio and brand clarity**
   - Keep AI Done Right as the parent display brand.
   - Preserve legacy paths unless every cross-link is swept.
   - Keep products and OpenHubForAI registries distinct: Baltor governs what agents know;
     Teleon governs what agents do; OpenHubForAI registries make components discoverable.

4. **Prototype-to-production gap**
   - Replace in-browser Babel with a real build plan.
   - Convert `shared/` into a reusable component package.
   - Map fixtures to real APIs, databases, queues, billing, auth, and audit.

5. **Service consumption and auth**
   - Implement the model in
     `docs/architecture/service-auth-and-consumption-model.md`.
   - Keep `architecture/service_auth_consumption_model.json` synchronized with
     `services/registry.yaml`.
   - Run `python3 scripts/check_service_auth_consumption_model.py --self-test`
     after changing either file.
   - Decide which calls use user session auth, external API keys, OAuth client
     credentials, mTLS/workload identity, queue identity, or signed publisher
     identity.
   - No shared god tokens. No raw keys in docs, screenshots, fixtures, or git.

6. **Research and competitive landscape**
   - Research Baltor competitors, adjacent tools, auth patterns, service mesh,
     registry trust, API security, source provenance, receipts, and compliance.
   - Mark research as candidate intelligence until it is implemented and
     verified.
   - Use dates and source links for market, security, legal, or dependency
     claims.

7. **Handoff completeness**
   - Keep README, CLAUDE-CODE, HANDOFF, per-folder READMEs, screenshots index,
     Control Tower, service docs, and root repo context in sync.
   - If a bundle/zip predates current surfaces, mark it stale or regenerate it.

## Score Order

Pick the first failing item:

1. Broken or missing surface that the handoff says is built.
2. Stale count or route map that would mislead Claude Code Max.
3. Security/auth gap that could create shared credentials, tenant leakage, or
   fake private-first enforcement.
4. Baltor truth-boundary issue: discovery presented as trust, candidate
   presented as verified, or contradiction silently hidden.
5. Frontend/design-system drift from shared tokens and branded-house rules.
6. Prototype-to-production gap not represented in docs or code.
7. Research claim without date, link, status, or implementation boundary.
8. Cleanup and consistency pass.

## Output Contract

For every loop:

- Record the surfaces and files inspected.
- Make the smallest durable change that clears the selected gate.
- Run focused checks for touched docs/code.
- Update the handoff context if the current repo shape changed.
- End with the next highest-value gate.

Do not stop because one route, verifier, tunnel, dependency, or research path is
blocked. Record the blocker and switch to the next gate.
