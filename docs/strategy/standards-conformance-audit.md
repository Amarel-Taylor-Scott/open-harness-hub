---
title: Standards-conformance audit
status: canonical map (snapshot 2026-05-29)
audience: anyone touching scripts/emit/, schemas/_common, docs/ns/context.jsonld, or SPEC §18
---

# Standards-conformance audit

This is the canonical conformance map for the hub's **standards surface**:
the JSON-LD `@context`, the `_common` envelope, the controlled vocabularies,
the emitters under `scripts/emit/`, and SPEC §18 (Standards alignment). It
exists so the surface does not get re-audited from scratch every quarter, and
so the concrete fixes can be sequenced and split into disjoint work items.

**Posture is "emit, don't replace" (SPEC §18.2):** the YAML manifests in
`catalog/` are the single source of truth; renderers emit standards-conformant
outputs from them; we cite external vocabularies by IRI rather than
re-publishing them (SPEC §18.4). This audit grades how faithfully that posture
is actually implemented, not whether the posture is right — it is. The full
landscape rationale lives in [[standards-landscape]]; product framing for the
CEaaS serving surfaces is in [[context-enrichment-service]] and
[[two-services-shared-infrastructure]].

**Headline:** the external posture is strong — the emitters pin current,
relevant specs and the choice of targets is defensible. Conformance debt is
**concentrated in three places**, not spread thin: (1) two CEaaS serving
surfaces declared with non-existent implementation modules that pass CI
silently, (2) a handful of stale spec pins / non-conformant fields, and (3) a
governance/addressability layer that was declared in the schema and SPEC but
is essentially unadopted in the catalog. Each is broken out below with a
ranked remediation list. **This doc is additive — it references SPEC.md, the
emitters, and the schemas; it does not edit them.**

---

## 1. The standards surface (what was audited)

| Surface | File(s) | Role |
|---|---|---|
| JSON-LD `@context` | `docs/ns/context.jsonld` | Maps hub terms → schema.org, DCAT, SKOS, PROV-O, DPV, SPDX, Croissant, MCP, custom `ohh:` ns. SPEC §18.1. |
| Common envelope | `schemas/_common.schema.json` | Shared `$defs` (envelope, governance fields, model targets). Every component schema `$ref`s it. |
| Controlled vocabularies | `vocabularies/*.yaml` | Industry · capability · modality · trust-boundary · lifecycle · lifecycle-position · leaf-types · HIPAA Safe Harbor. SPEC §2. |
| Emitters | `scripts/emit/*.py` (+ `all.py` driver) | "Emit, don't replace" renderers. SPEC §18.2. |
| Spec binding | `taxonomy/SPEC.md` §18 (canonical; surfaced at `docs/reference/spec.md`) | Names the targets, IRIs, and additive envelope fields. |

The validator that gates all of this (`scripts/validate.py`, run by
`.github/workflows/emit.yml`) checks exactly three things per manifest:
JSON-Schema validity, controlled-vocabulary membership
(industry/capability/modality/leaf-types), and ref-resolution against known
component IDs. **It does not resolve `implementations[].path` callable paths,
and it does not lint emitter output against the upstream spec.** Those two
blind spots are where drift #1 and #2 hide.

---

## 2. Emitter-by-emitter conformance (the strong part)

`scripts/emit/all.py` runs **13 emitters** in sequence. The external posture
is good: each pins a current, relevant spec.

| Emitter | Target + pin | Pin location | Source component(s) | Conformance |
|---|---|---|---|---|
| `mcp_server.py` | MCP **2025-11-25** | module docstring → spec URL | `tool`, `processor` | Current. Also covers the `tools/list` JSON-RPC view (see §4 — SPEC lists this as a separate `mcp_tools_list.py` that never shipped). |
| `croissant.py` | Croissant **1.0** (MLCommons) | docstring | `dataset`, `knowledge-pack` | Current. JSON-LD ML dataset standard. |
| `cyclonedx_ml.py` | CycloneDX-ML **1.6** | `specVersion: "1.6"` | release bundle | Current. AIBOM. |
| `spdx_3.py` | SPDX **3.0.1** (AI + Dataset profiles) | `specVersion: "SPDX-3.0.1"`; `@context` → spdx-3-model context | release bundle | Current. **But** the hub's own `context.jsonld` still binds the SPDX 2.x RDF-terms prefix (drift #2c). |
| `openlineage.py` | OpenLineage **v2** (facets 1-0-0 / 1-1-0) | `_schemaURL` per facet | pipeline / benchmark run | Current. |
| `c2pa.py` | C2PA **2.1** | docstring spec URL; `claim_generator_info` | image/audio/video output | **Stale** — C2PA has moved to 2.3 (drift #2b). |
| `agent_skill.py` | Agent Skills (open standard, agentskills.io) | n/a (open) | `harness`, `pipeline` | Emits a **non-conformant `when_to_use` frontmatter key** (drift #2a). |
| `hf_model_card.py` | HF Model Card | docstring | `harness` | OK. |
| `hf_dataset_card.py` | HF Dataset Card | docstring | `dataset`, `knowledge-pack` | OK. |
| `hf_space.py` | HF Space frontmatter | docstring | `harness` (deploy) | OK. |
| `lm_eval_harness.py` | lm-evaluation-harness YAML | docstring | `benchmark` | OK. |
| `promptfoo.py` | promptfoo config | docstring | `benchmark` | OK. |
| `eu_ai_act_annex_iv.py` | EU AI Act Annex IV dossier | docstring | components with `eu_ai_act_risk: high_risk` | Renderer OK; **starves for input** — almost no manifest sets the field (drift #3). |

The deliberate non-targets (Linked Data Platform, MLMD, OpenAI Evals, HELM as
a direct emit target, Kaggle metadata) are documented in SPEC §18.6 and remain
the right calls.

---

## 3. Drift #1 — dangling CEaaS serving surfaces (integrity hole, passes CI silently)

**This is the highest-severity finding** because it is an *integrity* problem,
not a cosmetic one: the catalog asserts a capability that has no
implementation, and nothing in CI catches it.

Two `deliver.*` processors declare `implementations[].kind: callable` with a
Python `path` under a directory that **does not exist**:

| Manifest | `process_kind` | Declared impl path | Module status |
|---|---|---|---|
| `catalog/processors/deliver/serve-mcp-corpus.yaml` | `deliver.mcp_serve` | `scripts.processors.deliver.serve_mcp_corpus.run` | **missing** — no `scripts/processors/deliver/` directory exists |
| `catalog/processors/deliver/emit-llms-txt.yaml` | `deliver.llms_txt` | `scripts.processors.deliver.emit_llms_txt.run` | **missing** — same |

These are the two consumption surfaces that matter most to the CEaaS product
(serve a governed corpus over MCP; render it as `llms.txt` / `llms-full.txt` —
the emerging doc-tier convention). They were seeded as catalog rows by
`scripts/seed/ceaas_components.py` ahead of the implementations.

**Why CI stays green:** `scripts/validate.py` validates the manifest against
`schemas/processor.schema.json`, checks vocabularies, and resolves component
*refs* — but it never imports or stat-checks an `implementations[].path`. And
`scripts/emit/all.py` never touches these two processors (they have no
emitter; they ARE the serving runtime). So the broken link is exercised by
nothing in the pipeline. A reader of the catalog reasonably concludes the hub
can serve over MCP and emit `llms.txt` today; it cannot.

**Why it matters for the product thesis:** governance is the moat. A catalog
that claims a deliverable surface it can't run undermines the
measured/governed posture exactly where the CEaaS wedge lives. This is the
honest-counting rule applied to capability, not just to component counts.

**Remediation (disjoint code item, not this doc):**
1. Implement `scripts/processors/deliver/serve_mcp_corpus.py:run` and
   `scripts/processors/deliver/emit_llms_txt.py:run` (the `emit-llms-txt` one
   is deterministic and cheap — a renderer over a governed corpus — so it is
   the natural first cut), **or** demote both manifests to
   `lifecycle: experimental` with the `implementations` block removed until the
   modules land.
2. **Close the blind spot:** add a validator pass that resolves every
   `implementations[].kind: callable` `path` to an importable
   `module:function` and fails if it is missing. This is the structural fix —
   it prevents the next dangling impl, not just these two. (Same spirit as the
   no-magic-values CI drift checks: a claim made in two places gets a check
   that fails on divergence.)

---

## 4. Drift #2 — stale spec pins / non-conformant fields

Lower severity than #1 (these emit *plausible* output, just not *current* or
*spec-exact* output), but each is a one-file fix.

### 2a. Agent Skills `when_to_use` is not a spec frontmatter key

`scripts/emit/agent_skill.py` writes a `when_to_use` key into the SKILL.md
YAML frontmatter (for both harness and pipeline skills). The Agent Skills
specification has the loading host read **`description`** to decide when a
skill applies; `when_to_use` is not a recognized frontmatter field. Tools that
strictly parse the frontmatter will ignore it; the "when to use" signal is
silently dropped.

*Fix:* fold the `when_to_use` sentences into `description` (respecting the
length cap already enforced) and drop the non-standard key. Disjoint code item.

### 2b. C2PA pinned to 2.1; current is 2.3

`scripts/emit/c2pa.py` (docstring + `claim_generator_info.version`) targets the
**2.1** specification. SPEC §18.2 also says "C2PA v2.1". C2PA has since shipped
2.2 and 2.3. The emitted manifest shape is largely stable across these, but the
pin should track current so downstream validators don't reject on version.

*Fix:* bump the emitter to the current C2PA version and update the SPEC §18.2
row to match. Disjoint code item.

### 2c. SPDX RDF-terms 2.x prefix inside a 3.0 world

`docs/ns/context.jsonld` binds `"spdx": "http://spdx.org/rdf/terms#"` — that is
the **SPDX 2.x** RDF vocabulary namespace. Meanwhile `scripts/emit/spdx_3.py`
correctly emits **SPDX 3.0.1** and uses the 3.0 model context
(`https://spdx.github.io/spdx-3-model/spdx-context.jsonld`). The hub's own
context therefore advertises a 2.x SPDX prefix it never uses for the 3.0
output, which is internally inconsistent.

*Fix:* align the `spdx:` prefix in `context.jsonld` to the SPDX 3.0 namespace
(or drop it if license IRIs are the only SPDX touchpoint and they already
resolve via `https://spdx.org/licenses/{id}.html` per SPEC §18.4). Disjoint
code item.

### 2d. (Spec-vs-reality) `mcp_tools_list.py` named in SPEC, never a file

SPEC §18.2 lists **`mcp_tools_list.py`** as a separate renderer for the MCP
`tools/list` JSON-RPC view. No such file exists; that responsibility lives
inside `mcp_server.py`. This is a SPEC-table-vs-reality mismatch, not a missing
capability. Conversely, `agent_skill.py` **ships and runs in `all.py`** but is
**absent from the SPEC §18.2 emitter table**. Both are pure-doc drifts.

*Fix:* reconcile the SPEC §18.2 table with the actual `scripts/emit/`
contents — remove the `mcp_tools_list.py` row (or note it as consolidated into
`mcp_server.py`) and add the `agent_skill.py` row. Disjoint doc/spec item.

---

## 5. Drift #3 — unused governance-envelope fields + unbuilt inline JSON-LD addressability

SPEC §18.3 added an additive governance + addressability layer to the envelope.
The schema fields exist and validate; **adoption in the catalog is near-zero**,
and the addressability half was never built at all. Measured across **2,633
catalog YAML manifests** (snapshot 2026-05-29):

| Field (envelope, additive) | Manifests using it | Adoption |
|---|---|---|
| `eu_ai_act_risk` | 4 | ~0.15% |
| `data_protection` (DPV-aligned) | 2 | ~0.08% |
| `nist_ai_rmf_controls` | 0 | 0% |
| `iso_42001_controls` | 0 | 0% |
| inline `@context` (SPEC §18.3) | 0 | 0% |
| inline `@id` | 0 | 0% |
| inline `@type` | 0 | 0% |

Two distinct problems are bundled here:

**(a) NIST / ISO / EU-AI-Act fields are dead weight.** They are optional and
additive (so they cost nothing to *keep*), but at 0–4 manifests they cannot be
relied on as a filter, a governance signal, or input to the
`eu_ai_act_annex_iv.py` emitter (which consequently has almost nothing to
render). Either they get populated from a real mapping (the durable, structural
move — tie control IDs to component categories so the value isn't hand-typed
per row, per no-magic-values) or they should be acknowledged as
forward-declarations, not live governance metadata.

**(b) "JSON-LD-addressable" is asserted but unbuilt.** SPEC §18 opens with
"every manifest is **JSON-LD-addressable**" and §18.3 shows inline
`@context` / `@id` / `@type` in the envelope. **No manifest carries any of
these.** Addressability today exists only externally — via the standalone
`docs/ns/context.jsonld` and the emitter outputs — not inline on the YAML as
promised. The claim in §18 overstates what is implemented.

*Note (observed, not one of the three drifts):* the JSON-LD `@id` pattern and
`ohh:` namespace use `open-harness-hub.dev` (741 files), whereas the product
domain is `openharnesshub.com` (3 files). That is internally consistent so it
doesn't break anything, but the canonical IRI base will need a deliberate
decision before anyone treats the `@id`s as resolvable URLs. Tracked separately.

*Remediation:* (b) is the higher-value fix — either build inline JSON-LD
emission (a small step in the page/index build that injects `@context`/`@id`/
`@type` from the envelope, keeping YAML as source of truth) **or** soften the
SPEC §18 wording from "is JSON-LD-addressable" to "is JSON-LD-addressable *via
the emitters and `/ns/context.jsonld`*". (a) is a populate-or-acknowledge
decision. Both are disjoint items.

---

## 6. Ranked remediation backlog (each a disjoint item)

Ordered by severity × structural-durability (fix the thing that prevents the
*next* drift, not just this instance):

1. **Add an `implementations[].path` resolver check to `scripts/validate.py`.**
   Structural; closes the drift-#1 blind spot permanently and would have caught
   the two dangling processors at commit time. (Highest leverage.)
2. **Resolve the two dangling CEaaS surfaces** — implement
   `serve_mcp_corpus.run` / `emit_llms_txt.run` (start with the deterministic
   `emit-llms-txt`), or demote the manifests until the modules exist.
3. **Drop the non-standard `when_to_use` key** from `agent_skill.py`; fold the
   signal into `description`.
4. **Bump the C2PA pin** in `c2pa.py` (and SPEC §18.2) to current (2.3).
5. **Align the `spdx:` prefix** in `context.jsonld` to the SPDX 3.0 namespace.
6. **Reconcile the SPEC §18.2 emitter table** with `scripts/emit/` (drop
   `mcp_tools_list.py`; add `agent_skill.py`).
7. **Decide the governance-field posture** — populate `eu_ai_act_risk` /
   NIST / ISO from a structural mapping, or annotate them as
   forward-declarations.
8. **Build inline JSON-LD emission** (or soften the §18 "addressable" claim).

Items 1–6 are small and high-confidence. Items 7–8 are scoped decisions, not
mechanical edits, and should be sequenced after the integrity fixes land.

---

## 7. What this audit deliberately does not claim

- It does **not** re-litigate the choice of emit targets — SPEC §18.6's
  non-adoption list stands.
- It does **not** treat the `open-harness-hub.dev` vs `openharnesshub.com` split
  as a conformance bug; it is internally consistent and tracked elsewhere.
- It does **not** edit SPEC.md, the emitters, the schema, or the context — the
  fixes above are split into disjoint code/doc items so they can land
  independently without conflicting on this map.

See also: [[standards-landscape]] · [[context-enrichment-service]] ·
[[two-services-shared-infrastructure]] · `docs/codex/no-magic-values.md` ·
`docs/codex/schema-extensibility.md` · `taxonomy/SPEC.md` §18.
