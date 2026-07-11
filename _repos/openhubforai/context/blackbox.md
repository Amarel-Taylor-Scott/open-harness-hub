# OpenHubForAI — blackbox view (what this component is, owns, and does)

**Purpose.** This is the standalone briefing for a session managing **only** OpenHubForAI: the open
ecosystem (eval harnesses · templates · skills · conformance tests · runtime-adapter examples) plus
the **open CapabilityTask spec (CTS)**, and the OpenHubForAI hub/registry surfaces. It states what
this component internally owns, its key subsystems, its current state, and where the detailed source
docs live. The companion `edges.md` covers how it connects to the other five components and the
compatibility contracts that must hold when it is managed separately.

**Grounding.** Every claim below summarizes and links an existing repo doc or machine source. Where a
number appears, the doc/manifest it is computed from is named — no count is hand-typed here. If this
file and a cited source disagree, the source wins; this is a consolidation, not a new authority.

Primary sources synthesized here:

- `architecture/portfolio_dependency_law.json` → `layers.openhubforai` — the machine role definition (proof: `scripts/check_portfolio_dependency_law.py`).
- `src/openhubforai/README.md` + `src/openhubforai/__init__.py` — what the code package owns and its import-freedom law.
- `docs/spec/OPENHUBFORAI_SPEC.md` — the open CapabilityTask / harness spec (the portable standard).
- `docs/strategy/teleon-baltor-openhubforai-portfolio.md` §"The OpenHubForAI family" + the method-hub boundary — the hub family and the Baltor method spine.
- `docs/BIBLE.md` §4 "The OpenHubForAI surfaces + the 103 registries" — the two-layer surface/registry model and the named rosters.
- `_repos/_shared/ARCHITECTURE-MAP.md` §"OpenHubForAI" — the one-paragraph portfolio-level definition.

---

## 1. What OpenHubForAI is (one paragraph)

OpenHubForAI is the **open registry storefront Teleon, Baltor, and AIDevObserver consume** and the **neutral
home of the standard**: reference context, tools, models, steps, DAG components, primitives, primitive/task
templates, reconciliation/robustness/enrichment rules, modules, skills, harnesses, evals, templates, and specs.
It is a focused **hub family, not one junk drawer**, and — this is load-bearing — **none of its hubs is a truth
authority (discovery ≠ trust)**. It is the neutral home of the
open **CapabilityTask spec (CTS)**: the tagline is *"Teleon implements the open CapabilityTask Spec,"* not
"Teleon invented a proprietary task format." Package root: `src/openhubforai`.
Source: `architecture/portfolio_dependency_law.json` → `layers.openhubforai.role`; `_repos/_shared/ARCHITECTURE-MAP.md` §4; `docs/strategy/teleon-baltor-openhubforai-portfolio.md` (line 62, "Teleon implements the open CapabilityTask Spec").

**What the code package owns** (verbatim scope from `src/openhubforai/README.md` §"What OpenHubForAI owns"):
public eval harnesses · open task examples · standard CapabilityTask examples · skill packs · runtime-adapter
examples · template registry · benchmark suites · conformance tests · community contributions · reference task
packages · **the open CapabilityTask spec**.

---

## 2. The open CapabilityTask / harness spec (CTS) — the portable standard

The spec is the portable, vendor-neutral layer distilled from the reference implementation. It lives at
`docs/spec/OPENHUBFORAI_SPEC.md`. The load-bearing shape (read the spec for the full detail):

- **One YAML manifest per component**, validated against a published JSON Schema; the same envelope shape for
  every type. There are **14 component types** (`docs/spec/OPENHUBFORAI_SPEC.md` §1): harness · pipeline ·
  persona · rule-pack · knowledge-pack · logic-pack · tool · adapter · processor · rubric · dataset · schema ·
  benchmark · pattern.
- **Envelope fields** (`§2`): `id` (`"<type>/<kebab-slug>"`, globally unique) · `type` · `version` (semver) ·
  `lifecycle` (experimental|beta|stable|deprecated) · industry/capability/modality · `trust_boundary` ·
  `lifecycle_position` (pre_api|api|post_api|cross_cutting) · optional cross-standards alignment (EU AI Act /
  NIST AI RMF / ISO 42001 / DPV / HIPAA Safe Harbor).
- **Composition primitives** (`§3`): a pipeline is a DAG over step kinds (harness · rule_pack · tool · adapter ·
  branch · loop · knowledge_pack · processor · embedder · chunker · judge · escalate · dispatch · parallel ·
  report · deliver · pipeline). A `pipeline` step invokes a sub-pipeline.
- **The six-step canonical chain** (`§4`) — the invariant shape mined from production pipelines: structured
  input → prose → PII/PHI-safe text → deterministic red-flag hits → citations from a domain corpus → scored
  output with rationale → audit trace. Documented as running the identical chain across ESG/supply-chain DD,
  healthcare radiology, legal contract review, and AppSec code review, with only the persona/GREP-pack/
  knowledge-pack/rubric changing.
- **Success criteria** (`§5`): seven first-class composable kinds (rubric · regex · semantic · llm_judge ·
  deterministic · tool_validate · composite AND/OR/NOT), each with a severity and per-criterion pass/fail trace.
- **Standards alignment** (`§6`): one manifest emits to **13 published standards formats** via `scripts/emit/`
  (croissant · mcp_server · agent_skill · hf_model_card · hf_dataset_card · hf_space · lm_eval_harness ·
  promptfoo · cyclonedx_ml · openlineage · c2pa · eu_ai_act_annex_iv · spdx_3). "Write one manifest; get
  thirteen standards-format publications for free."
- **Vocabularies** (`§7`): controlled lists in `vocabularies/` (industries · capabilities · modalities ·
  lifecycle-position · applied-layers · leaf-types).
- **License:** MIT, same as the reference implementation (`§License`). No central server, no API key, no
  platform lock-in — the catalog is plain YAML in git and the CLI works against any fork (`§9`, `§10`).

The spec itself records the reference implementation state as **v0.4.0+ (200 components, 4 working verticals,
13 standards-format emitters)** (`docs/spec/OPENHUBFORAI_SPEC.md` §intro). Treat that as the spec doc's own
figure; the live catalog count is computed by the build, not this file.

---

## 3. Key subsystems (the code package + the catalog)

### 3a. The catalog — plain YAML in git (the component layer)

The catalog root is `catalog/` (marked live, not legacy, by `catalog/_STATUS.md`), with one directory per
component type: `adapters/ · benchmarks/ · datasets/ · harnesses/ · knowledge-packs/ · logic-packs/ ·
patterns/ · personas/ · pipelines/ · processors/ · rubrics/ · rule-packs/ · tools/`. Manifests validate against
`schemas/*.schema.json` (envelope base `schemas/_common.schema.json`); controlled lists live in
`vocabularies/`; standards emitters live in `scripts/emit/`.
Source: `catalog/` directory listing + `catalog/_STATUS.md`; `docs/spec/OPENHUBFORAI_SPEC.md` §9.

### 3b. The code package `src/openhubforai/`

The ecosystem-layer Python (import-free of Teleon and Baltor — see `edges.md`). Modules present:
`hub_engine.py` · `hub_site.py` · `hub_settings.py` · `component_store.py` · `browsing_registry.py` ·
`discovery.py` · `generators.py` · `intake.py` · `research_catalog.py` · `licenses.py` · `auth_kit/realm.py`.
Source: `src/openhubforai/` file listing; scope in `src/openhubforai/README.md`.

### 3c. The web surface

The browsable OpenHubForAI storefront app lives at `web/openhubforai/` (the built-out app served via the
showcase, not a skinny replacement — see the surface rules in `CLAUDE.md`). It reaches the catalog over the
`/registry/...` seam (detailed in `edges.md`).
Source: `web/openhubforai/` app; seam table in `_repos/_shared/ARCHITECTURE-MAP.md` §"The seams".

---

## 4. The hub family + the two-layer surface/registry model

**Hub = storefront · registry = catalog behind it** — the count people get wrong. A hub is a *surface* (a
branded storefront + one-liner + substrate); a registry is a *typed catalog* of one object TYPE. Each registry
carries a `maps_to_hub` field, so many registries roll up into one hub. You **query registries** (via the
`RegistryPort`, which lives in Teleon — see `edges.md`); you **browse hubs**. Registry kinds: **static**
(curated + indexed), **discovery** (crawls for new components), **meta** (pointer-only — indexes where external
registries live; pointer ≠ copy, discovery ≠ trust).
Source: `docs/BIBLE.md` §4 "TWO LAYERS — don't conflate them".

**UI consolidation (owner 2026-06-25):** all hubs + registries live under **one site — `OpenHubForAI.io`**; each
hub/registry is a **section / facet**, not a separate domain. The backend keeps per-hub/registry **data
separation** (separate datasets/databases); only the UI/UX is unified. `OpenHubForAI.io` replaces
`OpenHubForAI.org` as the preferred public site.
Source: `docs/BIBLE.md` §4 (UI/UX consolidation note); `docs/strategy/teleon-baltor-openhubforai-portfolio.md` line 50.

**The focused open hub family** (bridge graph `architecture/open_hubs_bridge_graph.json`; none is a truth
authority): **OpenContextHub** (reference context artifacts — *reference context is not served truth; Baltor
governs it*) → **OpenSkillsHub** (the open skill graph) → **OpenToolsHub** (the open tool graph) →
**OpenHubForAI.io** (the proof layer: harnesses · rubrics · eval packs · fixtures · templates · datasets ·
conformance packs).
Source: `docs/strategy/teleon-baltor-openhubforai-portfolio.md` §"The OpenHubForAI family" (lines 42–63).

### Counts (all computed — never trust this prose over the check)

- **Surfaces named across design + data:** ~35, from `architecture/hub_profiles.json` (32 detailed profiles) +
  `architecture/candidate_open_hubs.json` (9 existing + 20 candidates). The full name roster is in
  `docs/BIBLE.md` §4(a).
- **Currently-registered roster:** lives in `web/*/kit/products.js` `OPENHUB_REGISTRIES` (documented as **8
  live + 13 preview** as of 2026-07-01 in `docs/BIBLE.md` §4(a)); the count is computed by
  `scripts/check_ai_done_right_surface_family.py`, never hand-counted. `CLAUDE.md` frames the current
  design-family snapshot as **22 OpenHubForAI registries** (9 live open + 13 private-bench). Run
  `python3 scripts/check_ai_done_right_surface_family.py --self-test` before trusting any family count.
- **The 103 registries** — the named data profiles under the hubs: single source
  `architecture/registry_ontology.json`, count computed by `check_registry_ontology` (**103** as of
  2026-06-25). Records come from population engines, never hand-building. The full name list is in
  `docs/BIBLE.md` §4(b).
Source: `docs/BIBLE.md` §4(a)+(b); `CLAUDE.md` §"Portfolio".

---

## 5. The Baltor method spine (the private-bench method-hubs)

The **Baltor method spine** is a set of method-hubs on the private bench:
**OpenReconciliationHub · OpenHardeningHub · OpenEnrichmentHub · OpenOptimizationHub · OpenVerificationHub**,
plus **OpenRoutingHub** (model-routing policy; owner-proposed 2026-06-09). They are **STORE components — they
register method SPECS only** (candidate; discovery ≠ trust).

**Method-hub boundary (LOCKED 2026-06-21):** *Baltor SELECTS a method (via Teleon) → RUNS it on customer data →
OWNS the resulting truth.* The spec lives in the store; execution and governed truth live in Baltor, with no
duplicated implementation. Baltor's moat is the governed DATA + receipts, not the technique — so publishing
specs leaks no moat. (The *execution* side — e.g. `scripts/artifact_graph/reconciliation.py` `Reconciler` per
`docs/section-cards/reconciliation.md` — is Baltor's, not OpenHubForAI's; OpenHubForAI holds only the spec.)
Source: `docs/strategy/teleon-baltor-openhubforai-portfolio.md` lines 54–58; `CLAUDE.md` §"Portfolio"; `docs/BIBLE.md` §4 (Baltor method spine line).

---

## 6. Current state (what to trust as of this snapshot)

- **Import-freedom holds and is enforced.** The package imports neither `src.teleon.*` nor `src.baltor.*`,
  enforced by `scripts/check_portfolio_dependency_law.py`. This neutrality is the credibility of the standard.
  Source: `src/openhubforai/__init__.py` (ARCHITECTURAL LAW docstring).
- **The spec is published and portable** (`docs/spec/OPENHUBFORAI_SPEC.md`), with 13 working emitters in
  `scripts/emit/` and the catalog live under `catalog/`.
- **The registry federation query engine that stocks/searches the catalog is Teleon-owned** (`src/teleon/
  registry/{port,search,populate,...}.py`), NOT part of `src/openhubforai/`. When building browse UI, build
  over that existing federated search — do NOT rebuild it. This is the single most important reuse boundary for
  a session managing OpenHubForAI. Source: `docs/BIBLE.md` §4 ("do NOT rebuild the search; build the browse UI
  over it"); detailed in `edges.md`.
- Counts/rosters drift; always recompute via the named checks rather than trusting prose.

---

## 7. Pointers to the detailed source docs

(These live under `docs/…` today; after the file moves they are expected under `_repos/openhubforai/context/` — the
canonical content is unchanged, only the path.)

- **The spec:** `docs/spec/OPENHUBFORAI_SPEC.md`.
- **The hub family + method-hub boundary:** `docs/strategy/teleon-baltor-openhubforai-portfolio.md` §"The OpenHubForAI family".
- **The surfaces + 103 registries (named rosters + count sources):** `docs/BIBLE.md` §4.
- **Package scope + import law:** `src/openhubforai/README.md`, `src/openhubforai/__init__.py`.
- **Machine sources:** `architecture/portfolio_dependency_law.json` (`layers.openhubforai`), `architecture/hub_profiles.json`, `architecture/candidate_open_hubs.json`, `architecture/registry_ontology.json`, `architecture/open_hubs_bridge_graph.json`.
- **Portfolio-level definition + seams:** `_repos/_shared/ARCHITECTURE-MAP.md`; shared laws: `_repos/_shared/STANDARDS.md`.
- **Additional briefs:** `_repos/openhubforai/context/design/aidoneright-claude-design/OpenHubForAI-BRIEF.md`; `_repos/_shared/archive/legacy/openhubforai/context/handoff/openhub-surface-counts.md` (archived; recompute counts via the named checks).
