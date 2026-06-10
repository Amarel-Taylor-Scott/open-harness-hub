# Handoff checkpoint — Capability requests & build-on-demand (2026-05-28)

Self-contained brief for the next agent. Read this top to bottom; it links the
canonical docs you need and states exactly what is built, paused, and next.

## 1. What this session decided (the one idea)

A user who hits a wall — "I need X and the catalog doesn't have it" — is a
**monetizable demand event**, not a dead end. We capture that wall as a
**capability-request**: a *typed empty slot* for a component we don't have yet.
It is fulfilled by a **premium agent build** (hosted build-on-demand) or a
**community build** (contributor earns credits when the shared component works).
This is the recurring-revenue engine; the export button stays free (see §2).

**Locked design (owner-confirmed):** a capability-request is **NOT an eighth
primitive**. It is an operational object (like `review-ticket`) that:
- carries the `target_type` it will become (one of the 14 component types), so
  it stays inside the seven-primitive model — a *typed slot*, not a new role;
- sits at maturity **`abstract`** — the only pre-component tier; never
  tenant-visible as a component;
- leaves `abstract` only by **promotion**, which mints a real component at
  `experimental` — gated by the **two-axis lift gate** (lift AND durability,
  `scripts/eval/durable_gap_harness.py`). The gate is what stops a build-agent
  from manufacturing junk.

Two orthogonal axes, kept clean: *role* (seven primitives) vs *maturity*
(`abstract < experimental < beta < stable`), mirroring the existing
`lifecycle` vs `lifecycle_position` split.

## 2. Business framing (the conversation that led here)

- **Concern raised:** "join → build a pipeline → export → leave" yields no
  recurring revenue; charging ~$5/pipeline taxes the easiest-to-replicate part.
- **Resolution:** the *export* is the commodity (it's the funnel). Recurring
  value is the **governance / live layer** and **build-on-demand**. This maps
  exactly onto the repo's existing **execution-class** axis:
  - **Freezable → free funnel:** `text-operation` + `static-information`
    components (processor, rule-pack, pattern, persona, static knowledge) — pure,
    cacheable, run forever offline.
  - **Live-dependent → recurring:** `code-executing` (tool, harness, adapter,
    pipeline) + **dynamic** Knowledge Corpus (CDC/freshness/revocation), PLUS
    build-on-demand fulfillment of capability-requests.
- The execution-class table in the taxonomy doc IS the pricing boundary; it
  already existed — we just named it.

## 3. Output-hygiene / prompt-strategy components (a question that came up)

JSON conformance/repair, char cleaning, markdown repair, compression,
redaction, translation, slang replacement — **these are not a taxonomy gap.**
They are already `processor` (**Action: Transform**) at lifecycle positions
`pre_api.query_sanitization` and `post_api.format_coercion` (which literally
reads "JSON repair, schema validation, structured-output verification"). Slang
/ synonym replacement is a `keyword` Knowledge Corpus; model-assisted
translation is a `harness`/`tool`. These are mostly **freezable** (funnel) and a
great population target — the mined repo list is full of implementations
(outlines, baml, markitdown, unstructured, …). Action item: populate them; no
schema change needed.

## 4. What was built this session (all validated)

| File | Change |
|---|---|
| `vocabularies/lifecycle.yaml` | Added `abstract` as the lowest maturity tier; documented as pre-component, never tenant-visible. **Deliberately NOT** added to the `_common.schema.json` component envelope `lifecycle` enum (a real component is never `abstract`). |
| `schemas/_common.schema.json` | Extracted the inline 14-type enum into a named `$def` `componentType`; envelope `type` now `$ref`s it. Single-source (No-Magic-Values). Behavior-preserving. |
| `schemas/capability-request.schema.json` | **New** standalone operational schema. Fields: `target_type` (`$ref` componentType), `maturity` (const `abstract`), `status`, `fulfillment` (agent_build/community), `requested_by` + `demand_count` (demand signal), `seed_repos` (repo-catalog refs), `research_area_id`, `lift_gate` (status + lift_reason/durability_class pointing to `reason_codes.py`), `build_job_id`, `review_ticket_ids`, `promotion_decision_id`, `promoted_component_id`, `reward` (credits for works+shared). **Not** in `validate.py` TYPE_TO_SCHEMA. |
| `docs/concepts/component-taxonomy-and-stages.md` | New section "Not an eighth primitive: the capability-request (a typed empty slot)" + promotion-path diagram + pricing-boundary note. |
| `data/capability-requests/README.md`, `requests.jsonl` | New dir + one seed example (PDF-table-extractor `tool`, seed_repos: kreuzberg / unstructured / opendataloader-pdf). |
| `docs/strategy/product-market-monetization-brief.md` | Added "Build-on-demand & demand capture" subsection (free-funnel exports vs live/recurring layer; capability-requests; contributor credits) + build-on-demand in the usage-add-ons pricing row. |

**Validation status (passing):** all touched schemas are valid JSON Schema;
`componentType` extraction confirmed behavior-preserving (14 types; envelope
`type → $ref`); seed example validates; negative test confirms a bad
`target_type` is rejected; 5 real components (adapter/dataset/knowledge-pack)
still validate via the fast-path `scripts/validate.py`.

## 5. Canonical references for the next agent

- `docs/codex/master-goal.md` — the one goal (foundation + consistency > volume).
- `docs/concepts/component-taxonomy-and-stages.md` — seven primitives, stages,
  execution classes, and now the capability-request slot. **Authoritative.**
- `docs/concepts/capability-valleys.md`, `docs/strategy/north-stars.md` — the
  capability-gap thesis (build for the negative space).
- `docs/strategy/product-market-monetization-brief.md` — **the canonical
  product/market/monetization doc**; updated this session with build-on-demand +
  capability-requests + the freezable-vs-live pricing boundary. Read its
  "Build-on-demand & demand capture" subsection.
- `scripts/eval/reason_codes.py` — single source for lift_reason / durability_class.
- `scripts/eval/durable_gap_harness.py` — the two-axis lift gate.
- `scripts/acquisition/github_repo_harvester.py` — repo miner (`normalize`,
  `_classify`, `_gate`); reuse its logic, don't reinvent.
- `docs/codex/no-magic-values.md` — single-source-of-truth rules.

## 6. PAUSED work — the 2,000-repo merge

The owner pasted ~2,000 GitHub repos. Captured verbatim at
**`data/repo-catalog/incoming-repos.txt`**. Status:
- The existing harvest (`data/repo-catalog/prompt-engineering-repos.{jsonl,csv}`,
  2,031 rows) is **prompt-engineering-topic-weighted**, so it caught the
  long-tail DSPy/prompt repos but **missed** major document/OCR/RAG/framework
  repos. Spot check: `EvoMap/evolver`, `holo-q/errloom`, `OctAg0nO/harness`
  PRESENT; `langgenius/dify`, `microsoft/markitdown`, `PaddlePaddle/PaddleOCR`,
  `kreuzberg-dev/kreuzberg` ABSENT → the list has genuinely new source surface
  (esp. pre-LLM intake/OCR components).
- **Why paused:** the second message reframed these as candidate
  capability-request *seed material*, so a blind bulk merge was premature.
- **To finish:** dedupe `incoming-repos.txt` against the existing catalog;
  enrich the new ones via the GitHub API (stars/license/topics/description) so
  `github_repo_harvester.normalize()` can family/camp/gate them; merge + rewrite
  `summary.json`. Needs `GH_TOKEN`/`GITHUB_TOKEN` (≈2k calls). **Safety gate:**
  the list contains jailbreak/WormGPT/DAN repos — they must land as
  `reference-only · do-not-ingest`, never wrapped.

## 7. Next steps (NOT built — proposed)

1. **Build-on-demand engine** — agent that takes a capability-request, researches
   `seed_repos`, and builds a candidate component. Wire to
   `object-factory-job` (likely needs a new `component_build` job_type),
   `review-ticket`, and `promotion-decision`.
2. **Lift-gate wiring** — connect `capability-request.lift_gate` to
   `durable_gap_harness.py`; only `passed` may promote.
3. **Credits/reward ledger + premium billing** — the `reward` object is defined
   but there is no ledger or billing yet. Open owner questions: credit economics,
   premium price points, who can submit community builds.
4. **Surface capability-requests** in the conversational builder / showcase as
   buildable empty slots (demand aggregation via `demand_count`).
5. **Populate hygiene `processor` components** (§3) from the repo list.
6. **Finish the §6 repo merge.**

## 8. Repo state caveat

Branch `feat/scale-goals-and-hygiene`. The working tree is very large
(~7,775 changed paths, incl. generated `dist/` and submodules) — the
session-specific edits are exactly the files in §4 + §6's `incoming-repos.txt`.
Nothing was committed this session.
