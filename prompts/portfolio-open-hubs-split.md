> **EDITOR'S NOTE (captured 2026-06-06 from the owner).** Canonical spec for the OPEN HUBS SPLIT — the portfolio
> grows from 4 to **7 entities**. Executed INCREMENTALLY (not as one Workflow run). **DONE + proven (flywheel 337):**
> the 4-hub split is real and visible — 3 new sites (OpenContextHub.io, OpenSkillsHub.io, OpenToolsHub.io) +
> OpenHarnessHub narrowed to harnesses-only and moved to `.io`, all built from the single source
> `scripts/portfolio_lib.py`, served locally + on real TryCloudflare URLs, passing every portfolio rubric
> (brand/quality/security/customer/distinct/technical/trycloudflare). The company boundary model
> (`architecture/company_portfolio_map.json`) now has 7 entities (data-separated; proven). The cross-hub
> **bridge graph** (`architecture/open_hubs_bridge_graph.json` + `check_open_hubs_bridge_graph.py`) is built +
> proven: each hub owns one artifact kind, none is a truth authority (Baltor governs, Teleon runs).
> **QUEUED (the deep OpenContextHub contract subsystem — PART 3/4/7/8/9):** the 9 context_hub schemas, the
> open_context_registry + visibility/provenance policies + example artifacts, the `/api/opencontext*` projections,
> the OpenContextHub rubrics, and the `check_open_context_harness_redteam.py` redteam. Build next.

# /workflows /portfolio-add-opencontext-openskills-opentools-openharness-io

Seven entities under AI Done Right (founding thesis: ContextIsEverything): **Teleon.dev** · **Baltor** · **OpenContextHub.io** ·
**OpenSkillsHub.io** · **OpenToolsHub.io** · **OpenHarnessHub.io** (replaces .org). Do not merge into one
website; do not blur boundaries; no open hub is a runtime or a truth authority; no customer-private data in open
hubs.

**Relationship:** OpenContextHub provides reusable context → OpenSkillsHub teaches how → OpenToolsHub gives
execution → OpenHarnessHub proves it works → Teleon runs/evolves capabilities → Baltor governs context + decides
truth → AI Done Right coordinates.

## OPEN HUBS CLAUSE (carry forward)
The portfolio includes OpenContextHub.io, OpenSkillsHub.io, OpenToolsHub.io, and OpenHarnessHub.io.
OpenContextHub owns reference context artifacts/packs/schemas/source-handle maps/decomposition maps/native
sidecar examples/context fixtures. OpenSkillsHub owns agent skills/playbooks/workflows/SKILL.md packages.
OpenToolsHub owns executable tools/MCP servers/APIs/CLIs/adapters/workers with visibility policies.
OpenHarnessHub.io owns harnesses/rubrics/eval packs/fixtures/templates/datasets/conformance packs — replacing
.org as preferred. NONE is a truth authority; Baltor governs context, Teleon runs capabilities.

## Boundaries (proven in company_portfolio_map.json + open_hubs_bridge_graph.json)
| Entity | Owns | Not |
|---|---|---|
| OpenContextHub.io | context artifacts/packs/schemas/source-handle maps/decomposition/sidecars/fixtures | runtime · truth authority · private data lake · skill/tool/harness registry |
| OpenSkillsHub.io | skills/playbooks/workflows/SKILL.md/agent instructions/provenance | executable tools · eval harnesses · context truth |
| OpenToolsHub.io | executable tools/MCP/APIs/CLIs/adapters/workers/gating metadata | skill reasoning · context truth · eval rubrics |
| OpenHarnessHub.io | harnesses/rubrics/evals/fixtures/templates/datasets/conformance | skill registry · tool execution · context truth |

## QUEUED — deep OpenContextHub contract subsystem (build next; PART 3/4/7/8/9 of the owner spec)
- `schemas/context_hub/{ContextArtifact,SourceArtifactRef,ContextPackManifest,ContextSchemaArtifact,
  SourceHandleMap,DecompositionMap,NativeSidecarExample,ContextVisibilityPolicy,ContextProvenanceRecord}.v1`
  + register in `contract_registry.json`.
- `architecture/{open_context_registry,context_artifact_graph,context_visibility_policy,context_provenance_policy}.json`
  with example artifacts (CFPB Reg E pack, FAQ-30 held-out, source-handle map, decomposition map, sidecar,
  context-response schema) — each provenance + visibility + truth-status non-authoritative.
- Visibility codes: 100 PUBLIC_REFERENCE · 200 PUBLIC_METADATA · 300 GATED_CONTEXT_PACK · 400 CUSTOMER_PRIVATE
  · 500 INTERNAL_ONLY · 900 QUARANTINED.
- `/api/opencontext[/search|/graph|/provenance|/visibility]` + `/api/{openskills,opentools,openharness}` (projection-only).
- `rubrics/openContextHub/*.json` + `scripts/check_open_context_{contracts,registry,api,rubrics}.py` +
  `scripts/check_open_context_harness_redteam.py` (publishes private context · artifact-as-CanonicalFact ·
  served-without-governance · missing handle/provenance · OHH-claims-skill/tool/context · .org-as-canonical → all fail safe).
- ContextArtifact is NOT CanonicalFact; OpenContextHub is NOT a truth authority; Baltor governs before serving.
