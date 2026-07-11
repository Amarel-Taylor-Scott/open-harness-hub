# openhubforai (`aidoneright-openhubforai`)

The **open, product-neutral home of the CapabilityTask spec (CTS)** and the open ecosystem — primitives,
primitive/task templates, eval harnesses, skills, conformance tests, and the plain-YAML component catalog —
that Teleon, Baltor, and AIDevObserver consume but none of them owns. This is the **open registry storefront**
and the **neutral home of the
standard**; its credibility is its neutrality, and **none of its hubs is a truth authority (discovery ≠
trust)**.

## What this repo is

- **The open CapabilityTask spec (CTS)** — the portable, vendor-neutral standard Teleon implements against
  (`docs/spec/OPENHUBFORAI_SPEC.md`): one YAML manifest per component, 14 component types, a shared
  envelope, DAG composition primitives, the six-step canonical chain, and 7 composable success-criteria
  kinds. *"Teleon implements the open CapabilityTask Spec"* — not a proprietary task format.
- **The catalog** — plain-YAML components and reusable capability artifacts under `catalog/` (one directory per
  type), validated against `schemas/*.schema.json` with controlled `vocabularies/`. This is the open registry
  storefront Teleon, Baltor, and AIDevObserver consume.
- **The 13 standards emitters** (`scripts/emit/`) — write one manifest, get 13 published standards-format
  publications for free (Croissant · MCP server · Agent Skill · HF cards · lm-eval · promptfoo ·
  CycloneDX-ML · OpenLineage · C2PA · EU AI Act Annex IV · SPDX 3.0 · …).
- **The ecosystem code package** `src/openhubforai/` — the storefront/hub engine and catalog access,
  **import-free of Teleon and Baltor** by law (that import-freedom is the standard's credibility).
- **The web storefront** `web/openhubforai/` — the browsable OpenHubForAI app, served via the showcase,
  reaching the catalog over the `/registry/...` seam.

The north-star proof is the CTS six-step canonical chain running the **identical shape** across four
reference verticals — ESG / supply-chain due diligence, healthcare radiology, legal contract review, and
AppSec code review — with only the persona / rule-pack / knowledge-pack / rubric changing.

## Layout

- **`CLAUDE.md`** — the agent operating manual for a session managing only this repo (read it first).
- **`context/`** — this repo's self-contained briefing, everything a session opening only this folder needs:
  - **`context/blackbox.md`** — what OpenHubForAI internally *is* and owns (the spec, the catalog, the code
    package, the web surface, the hub family, the Baltor method spine, current state).
  - **`context/edges.md`** — how it connects to the other five components (AI Done Right · Teleon · Baltor ·
    AIDevObserver · Backend) + `_shared`: the dependency law, the seams, and the compatibility contracts to
    preserve when this repo is developed separately.
  - Deeper source docs under `context/{spec,architecture,design,handoff,howto,reference,research,status}/`.
- **`EDGES.md`** — the machine-generated cross-repo edge list (what this repo exposes, may consume, is
  consumed by, and must never depend on).

## How to work in it

1. Read `../dev-rules-context/standards/README.md` (the inherited laws), then `CLAUDE.md`, then
   `context/blackbox.md` + `context/edges.md`.
2. Follow the **default fast path** in `CLAUDE.md`: change one thing, validate/index only the changed paths,
   run the `run_proofs` umbrella — do not start with a full rebuild.
3. **Reuse-first.** Before building anything, check it does not already exist in `catalog/`,
   `scripts/emit/`, `src/openhubforai/`, or `../dev-rules-context/_shared/`. Above all, **do not rebuild
   the registry search** — the federation query engine is Teleon-owned; this repo *queries* it over the
   `/registry/...` seam.
4. Keep the standard neutral: never import `src.teleon.*` or `src.baltor.*` from `src/openhubforai/**`
   (enforced by `scripts/check_portfolio_dependency_law.py`).

The standards this repo inherits live in **`../dev-rules-context/standards/`** — linked, not copied. Shared
portfolio truth (architecture map, glossary, standards statement) lives in
**`../dev-rules-context/_shared/`**.

## Edges (from `EDGES.md`)

- **Role:** the OPEN ecosystem + the open CapabilityTask spec (CTS) — primitives, primitive/task templates,
  eval harnesses, skills, conformance packs, and reusable capability artifacts; stays product-neutral.
- **Exposes:** `capabilitytask-spec` · `eval-harnesses` · `task-templates` · `conformance-tests` · `skills`.
- **May consume (via published interface only):**
  - **`aidoneright-dev-rules-context`** — `standards/*`, `contracts/surface-registry.json`,
    `tools/check_*.py`, `_shared/*`.
  - **`aidoneright-shared-backend-components`** — `registry`, `primitives`, `codegraph`, `eval-harness`,
    `storage-tiers`, `credential-plane`.
- **Consumed by:** `aidoneright`, `teleon`, `baltor`, `aidevobserver` (keep these interfaces stable).
- **Forbidden (the boundary law — never depend on these):**
  - **`teleon`** — the open spec stays neutral; Teleon consumes OpenHubForAI, not the reverse.
  - **`baltor`** — the open ecosystem must not require the applied product.

Consume a neighbor ONLY via its exposed interface listed above — never read or import its source.
