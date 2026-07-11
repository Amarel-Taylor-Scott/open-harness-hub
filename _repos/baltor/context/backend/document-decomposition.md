# Raw document decomposition — the step the six-stage view hides

> The front-end stages (Source → Reconciliation → Anti-Fragility → Enhancement →
> Optimization → Consumption) show the *flow*. But **"Source Systems" contains an entire
> sub-pipeline**: turning a raw artifact (a 1,000-page PDF, a DOCX, a slide deck, a scanned
> image) into a **tree of addressable, typed context objects**. This doc specifies that tree
> — the part **Baltor owns** — and keeps the heavy parsing as swappable infrastructure.

## Why this is load-bearing
A 1,000-page PDF cannot enter a context window whole, and a claim must be able to cite *one
paragraph* or *one figure*, not "the document." Everything downstream depends on decomposition:
- **Smallest-safe-pack** + **source-handle expansion** only work if the document is already a
  tree of small, individually-addressable nodes.
- **Verification / freshness / rot** operate per node: when the source hash changes, you
  re-decompose and **diff the tree** (which paragraphs/tables actually changed), not "the doc
  is stale."
- **Retrieval** chunks *reference* leaf objects; they are not the source of truth (the node is).

## The product boundary (what Baltor owns vs. what's swappable)
- **Baltor owns the CONTRACT:** the recursive typed-object model, the source-handle fragment
  addressing, lineage (which parser, which confidence, which bytes), and the normalization of
  *any* parser's output into this tree.
- **Swappable infra (the Parser Manager adapter, `ParserProvider`):** the actual byte-level
  parse. Primary **Docling** (MIT, broad formats, layout/table models); fallback
  **Unstructured** (Apache-2.0); **LiteParse** (Apache-2.0) for fast local parsing with
  bounding boxes/OCR/screenshots. The parse itself is a `side_effects: external_call`-class
  step behind the adapter; Baltor consumes whatever it emits. (Per
  `research/backend-tool-verification.md`; avoid Marker/PyMuPDF4LLM as primary — restricted
  weights / AGPL.)

## The decomposition tree (recursive ContextObjects)
Every node is a `ContextObject` with `parent_ref`, an `object_kind`, an `ordinal` (reading
order under its parent), a positional `span`/`bbox`+`page_no`, and **its own source handle**.

```
Document                      ctx://<src>/<docid>
└─ Page (×N)                  ctx://<src>/<docid>#page=487
   └─ Block (layout region)   ctx://<src>/<docid>#page=487&block=3
      ├─ paragraph            (text + reading order)
      ├─ heading / title
      ├─ table                (cells → structured rows; also a rendered image artifact)
      ├─ figure / image       (caption + extracted image artifact in object store)
      ├─ diagram / chart      (caption + image; optional extracted data)
      ├─ equation             (LaTeX/MathML)
      ├─ code_block
      ├─ list / list_item
      ├─ footnote / caption
      └─ form_field
```

`object_kind` is an **open vocabulary** (extend per source); the closed set above is the seed.

## The processing steps (the sub-pipeline inside "Source Systems")
1. **Ingest + snapshot** — fetch via the source connector; write raw bytes to object store;
   compute `content_hash` (the CDC identity). *(Mirrors `_repos/shared-backend-components/scripts/ingest/sanctions_feed_live.py`:
   fetch → hash → lineage.)*
2. **Page split** — explode into pages; render a page image per page (object store) for
   bbox/figure work and human review.
3. **Layout / block detection** — per page, detect layout regions (the Parser Manager adapter).
4. **Typed classification** — label each block (`paragraph`/`table`/`figure`/…).
5. **Extraction** — text (+ OCR for scans), table → structured cells, figure/diagram → image
   artifact (+ optional extracted data), equation → LaTeX.
6. **Reading-order + relationship linking** — order siblings; link captions↔figures,
   headings↔sections, footnotes↔references (`context_relationships`).
7. **Normalize → ContextObject tree** — Baltor maps the parser's output into the recursive
   tree, assigning stable IDs + source-handle fragments + lineage per node.
8. **Chunk-for-retrieval** — build retrieval chunks that **reference** leaf object IDs (never
   copy text as a second source of truth); embed chunks → vector index.
9. **Claims attach to LEAVES** — verification/freshness operate on the smallest node that
   carries the assertion, so provenance is paragraph- or figure-precise.

## Source-handle addressing (the thing that makes expansion possible)
Extend the existing `ctx://` scheme with fragments:
```
ctx://acme/confluence/doc/123#page=487&block=3&para=2
ctx://acme/sec/10-K/0001#page=12&table=2
ctx://acme/spec/api.pdf#figure=12.2
```
A context pack carries the **handle + the leaf node**, not the document. Expansion (policy-gated)
walks *up* (parent context) or *down* (children) on demand — the 1,000-page PDF never enters a
window whole.

## Storage split (don't over-store text)
| What | Where |
|---|---|
| Raw bytes, rendered page images, extracted figures/tables-as-image, large markdown exports | **Object store** (S3 / R2 / MinIO) |
| The object tree (nodes, kinds, ordinals, spans, parent_ref), relationships, claims, lineage, parser confidence | **Postgres** — object table + long tables (`context_objects`, `context_relationships`, `context_claims`, `context_events`) |
| Chunk embeddings (referencing leaf `object_id`s) | **Vector index** (Qdrant primary / pgvector for the demo) — *not* the source of truth |
| Path/traversal queries over the tree + cross-doc links | **Graph index** (Graphiti primary; **NOT** Kuzu — archived Oct 2025; see verified catalog) |

## Lineage, confidence, and rot
- Every node records `parser_id`, `parser_version`, `parser_confidence`. Low-confidence nodes
  (bad OCR, ambiguous table) route to **steward review** before they can be served.
- On a source `content_hash` change: **re-decompose → diff the tree** → emit per-node rot
  signals (`changed`/`added`/`removed`), re-verify only the affected claims, refresh only the
  affected packs. (Reuse `scripts/foundry/scrapers.detect_change`.)

## Minimum to prove the contract (recommended next build — mirrors the sanctions proof)
A `_repos/shared-backend-components/scripts/ingest/document_decompose.py` that:
- takes a structured fixture (a small multi-section doc as JSON/markdown) and produces the
  **recursive ContextObject tree** with source-handle fragments + lineage, **deterministically,
  offline** (the heavy PDF byte-parse is the `ParserProvider` SEAM behind a `CannedParser`);
- proves: a claim attached to a leaf is citeable by fragment; expansion returns exactly that
  node; a changed fixture re-decomposes and diffs to the changed leaves only.
This proves the part Baltor owns without committing to a PDF dependency — the Docling/LiteParse
adapter slots behind the same interface in a network/dep-permitted environment.
