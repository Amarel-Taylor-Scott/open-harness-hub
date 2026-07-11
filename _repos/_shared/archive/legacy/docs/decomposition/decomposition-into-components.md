# Decomposition into components — tested (Chunk 2)

How an ingested artifact (a CFPB complaint record, a 1,000-page PDF, a DOCX, a scan) becomes a
**recursive tree of addressable, typed context objects** — the atomic *components* — instead of one
text blob. Every claim below is from a passing proof (commands + output included).

Spec it implements: `docs/backend/document-decomposition.md` + `docs/backend/raw-document-processing.md`.
Component vocabulary: `docs/concepts/component-taxonomy-and-stages.md` (the seven primitives).

## The model
```
raw artifact
  → document (root context object)
     → page
        → paragraph / table / figure / ocr-span      ← typed nodes
             → table cell                              ← recursion continues
```
Each node is a **ContextObject** with: a coordinate-precise `ctx://…#fragment` handle, an `object_type`,
per-node **lineage + content hash**, and `provenance.wasDerivedFrom` its parent. **Claims attach to
LEAF nodes**, never to the blob.

## The two modules (Baltor owns the tree; the parser is swappable)
- `scripts/ingest/document_decompose.py` — the recursive object model + `ctx://` fragment handles +
  expansion + re-decompose→diff (Baltor-owned, proven offline; a `CannedParser` stands in for the
  byte-level parse).
- `scripts/ingest/decompose_to_context_objects.py` — the **bridge**: normalizes any parser's nodes into
  the canonical `schemas/context/context-object.schema.json` (every node validated).
- **SEAM (swappable infra):** the actual parse/layout/OCR is a `ParserProvider` — Docling (primary) /
  LiteParse / Unstructured (`research/backend-tool-verification.md`); the contract is identical.

## Run it
```bash
PYTHONPATH=. python3 scripts/ingest/document_decompose.py --self-test
PYTHONPATH=. python3 scripts/ingest/decompose_to_context_objects.py --self-test
```

## What it proves (verified output)
`document_decompose --self-test` (GREEN):
- `1 document + 3 pages`; `node count = 13 (recursion incl. table cells)`
- `paragraph addressable by fragment handle` + `carries bbox (coordinate-precise)`
- `table cell addressable`; `figure carries artifact pointer (not text)`; `low-confidence OCR span flagged for review`
- **digestible front / expandable back:** `expansion returns exactly the cited leaf` · `can pull the
  parent page only on request` · `whole-doc text is NOT in the leaf payload (pack stays minimal)`
- **rot via re-decompose→diff:** `diff isolates exactly the changed table cell` · `removing a page emits
  page_count_changed + node_removed` · `no spurious page_count_changed on an edit`
- **scale:** `1,000-page doc → 1,000 page nodes` → `>2,000 addressable micro-objects (not one blob)`,
  `each page-1000 paragraph independently addressable`; `decompose is deterministic`.

`decompose_to_context_objects --self-test` (GREEN):
- `every decomposed node validates against context-object.schema.json` · `object count == node count`
- `paragraph → source_excerpt with body text` + `FragmentSelector bbox evidence` +
  `provenance.wasDerivedFrom = its page` · `table node → object_type 'table'` ·
  `root → object_type 'document', no parent` · `low-confidence OCR span is NOT promotion-eligible` · deterministic.

## A real decomposed component (from the CFPB ingestion, Chunk 1)
The CFPB connector's context objects carry the full governed shape — a decomposed node IS a complete
component:
```
keys: body, classification, context_object_id, current_version_id, evidence, facets,
      five_w_one_h, kind, lineage, native_id, object_type, policy, provenance,
      source_handles, source_system, source_url, summary, title
```
- `context_object_id: context-object/cfpb-complaint-demo-1001` + `current_version_id: …-2c18726d968b`
  (immutable versioned).
- `evidence[0].source_handle: ctx://cfpb/consumer-complaints/complaint/demo-1001` with a
  `DataPositionSelector{field: complaint_id}` — the expandable-back pointer.
- `facets.cfpb` (product/company/state/submitted_via) + `facets.baltor_demo.narrative_policy =
  unverified_allegation_do_not_certify_as_fact` — governance on the component itself.
- `five_w_one_h` (who/what/when/where/why/how) — the COM facet model, already present.

## Component vocabulary (how nodes relate to the registry)
- The **context object** is the *atomic* component — one addressable, typed, source-linked unit.
- The repo's **catalog/** holds the *reusable* component types built on top (adapters, datasets,
  harnesses, knowledge-packs, logic-packs, patterns, personas, pipelines, processors, rubrics,
  rule-packs, tools — 13 types, ~2,672 components; visible on `/dev`).
- The **seven primitives** (Input · Knowledge Corpus · If Statement · Action · Loop · Stop/End · Output)
  are the canonical taxonomy — `docs/concepts/component-taxonomy-and-stages.md`. A decomposed CFPB tree
  feeds the **Knowledge Corpus** primitive; claims on its leaves drive **If Statement** checks
  (e.g. the Reg-E-supersedes-FAQ contradiction).

## Why this matters (the contract)
1. **Minimal packs:** only the cited leaf is served; the blob never enters the context window.
2. **Provable:** every claim → a leaf handle → expandable to the exact source span.
3. **Rot-aware:** re-decompose + diff flags exactly which node changed (page/cell), driving refresh.
4. **Parser-agnostic:** the tree + handles are Baltor's; the byte-level parser swaps behind `ParserProvider`.

## Finer grain: structured record → atomic single-sentence facts (tested)
A complaint object (one component) is still coarse. `scripts/ingest/decompose_structured.py` breaks a
**structured record** into the smallest useful, independently-addressable components:
- **atomic facts** — one single-sentence fact per structured field, each with its own `ctx://…#field`
  handle and `claim_status='fact'` (promotion-eligible).
- **sentence chunks** — free-text fields (a complaint narrative) split into single sentences, each held
  out as `claim_status='unverified_allegation'`, `promotion_eligible=False` — the pack's governance, now
  at sentence grain.

Run: `PYTHONPATH=. python3 scripts/ingest/decompose_structured.py --self-test` (GREEN, 9 checks).
Real output — one CFPB complaint → **6 atomic facts + 2 held-out allegations**:
```
FACT  …/complaint/demo-1001#product           → "Complaint demo-1001: product is Credit reporting…"
FACT  …/complaint/demo-1001#company_response  → "Complaint demo-1001: company response is Closed with explanation."
ALLEG …/complaint/demo-1001#complaint_what_happened.s0 → "They reported an account that is not mine."  (promotion_eligible=False)
```
Each fact is a single sentence + an exact `#field` handle (expandable back); narrative sentences are
per-sentence (`#field.sN`) and never certifiable. This is the "smaller items / single-sentence facts"
grain on top of the per-record object — claims/If-Statements attach to one atomic fact.

## Sequencing: structured now, unstructured next
Structured decomposition (records → facts) is **working + proven** (this section). The **unstructured**
path (PDFs/DOCX/scans → the recursive tree) already exists as `document_decompose` (proven on a
1,000-page doc) but the *next* step is to run it on **real unstructured CFPB/regulatory PDFs** behind a
real `ParserProvider` (Docling) — deferred until the structured grain is wired through the pack/serve
path. Backlog, not done here.

## Test status
- `document_decompose --self-test` GREEN · `decompose_to_context_objects --self-test` GREEN — both are
  continuous flywheel proofs. CFPB component shape shown above is from the real `demo_cfpb_context_pack`
  run (Chunk 1: `docs/ingestion/cfpb-ingestion.md`).
