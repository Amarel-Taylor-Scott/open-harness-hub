# AI Done Right - Brand Family Prototype Summary

This tracked design note records the current AI Done Right family handoff. The
full local prototype bundle lives in:

```text
dist/sites/openharness-design/
```

Start there when handing the work to Claude Code Max:

```text
START-HERE-CLAUDE-CODE.md
README.md
CLAUDE-CODE.md
HANDOFF.md
IMPLEMENTATION-GUIDANCE.md
BACKEND-STACK.md
Design Acceptance Scorecard.html
```

The repo-level Codex goal is:

```text
docs/codex/ai-done-right-family-polish-goal.md
```

## Brand

Parent company: **AI Done Right** (`aidoneright.dev`)  
Tagline: **AI, done right.**  
Thesis: **discovery is not trust**.

Legacy paths such as `context-is-everything/` and `context-enrichment/` stay in
place for prototype cross-link stability. Displayed brand and product names are
current.

## Family Shape

The current design-family snapshot is:

```text
AI Done Right                     parent / portfolio
  Products
    Baltor.ai                     context assurance
    Teleon.dev                    purpose-driven runtime
  Live Open*Hub registries
    OpenContextHub.io
    OpenSkillsHub.io
    OpenToolsHub.io
    OpenSkillToTool.io
    OpenMCPHub.io
    OpenCompressionHub.io
    OpenBenchmarkHub.io
    OpenReviewHub.io
    OpenHarnessHub.io
  Private bench
    OpenTemplatesHub.io
    OpenEndpointHub.io
    OpenEnvironmentHub.io
    OpenSandboxHub.io
    OpenAgentHub.io
    OpenReceiptHub.io
    OpenStateHub.io
  Baltor method spine
    OpenReconciliationHub.io
    OpenHardeningHub.io
    OpenEnrichmentHub.io
    OpenOptimizationHub.io
    OpenVerificationHub.io
```

Snapshot count: parent + 2 products + 21 Open*Hubs = 24 surfaces. Do not treat
this as a magic value; recompute from `shared/products.js` in the prototype
bundle before changing docs, screenshots, or Control Tower copy.

Focused proof:

```bash
python3 scripts/check_ai_done_right_surface_family.py --self-test
```

## Baltor Method Spine

| Hub | Stage | Hero | Method family |
| --- | --- | --- | --- |
| OpenReconciliationHub.io | Reconcile | Cluster alignment. | dedupe; link evidence; surface conflicts |
| OpenHardeningHub.io | Harden | Robust object hardening. | detect fragile values; create durable objects; refresh over time |
| OpenEnrichmentHub.io | Enhance | Context enrichment. | add metadata; connect objects; increase robustness |
| OpenOptimizationHub.io | Optimize | Pack shaping. | summarize; structure; rank |
| OpenVerificationHub.io | Verify | Cited and provable. | bind claims to sources; prove by hash; hold out the unprovable |

These are private-first registry surfaces. They open the method language around
Baltor's engine, but they do not become truth authorities. Baltor governs truth.

## Branded-House Contract

- One shared design system.
- One shared type scale, spacing system, surface primitive, and dark-mode
  mechanism.
- One source of brand identity and accents in the prototype:
  `shared/products.js`.
- One hub engine: `makeHub(cfg)` for all 21 Open*Hub registry sites.
- Private bench hubs use muted accents and a private-preview state until
  owner-gated release.

Production must enforce private-first access server-side. The prototype only
renders the intended state.

## Production Gaps

The prototypes are design artifacts. A production build still needs:

1. Vite/Next or equivalent with precompiled JSX.
2. A real backend, API, datastore, ingest, verification, and engine pipeline.
3. Real auth, persistence, billing, tenant management, and audit.
4. Real registry data and source provenance.
5. Service-to-service auth and consumption per:

```text
docs/architecture/service-auth-and-consumption-model.md
```

## Do Not Regress

- Do not rename legacy prototype folders unless every relative link is swept.
- Do not hardcode counts, colors, ports, or brand copy that has an owning
  registry.
- Do not present private bench hubs as public production surfaces.
- Do not present Open*Hub discovery as trust.
- Do not let Teleon own Baltor truth or Baltor become a generic runtime.
