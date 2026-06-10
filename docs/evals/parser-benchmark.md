# Parser bakeoff — WRAP OmniDocBench (don't rebuild)

The Parser Manager picks among several parsers (`scripts/parser_router.py` → a `ParserProvider`
adapter). Which one wins per document type is an **evaluation**, not a guess — and a canonical
benchmark already exists, so we **wrap it rather than rebuild it**.

## Use the canonical benchmark
**[OmniDocBench](https://github.com/opendatalab/OmniDocBench)** (opendatalab, CVPR 2025) is the
authoritative document-parsing/evaluation benchmark and, as of its 2026-03 update, already scores
**Dolphin-v2, MinerU2.5, Marker, Docling** and others on reading order, tables, formulas, layout,
and text. We consume its results; we do **not** stand up a parallel parser bakeoff.

## Candidates (verified — research/backend-tool-verification.md) + when each wins
| Parser | License / hosting | Best for | Caveat |
|---|---|---|---|
| **Docling** (primary) | MIT, local | broad coverage, complex layout (AI layout/table models) | heavier deps |
| **Unstructured** (fallback) | Apache-2.0, hybrid | mixed enterprise docs, ETL baseline | — |
| **LiteParse** | Apache-2.0, local | fast local parsing + bounding boxes/OCR | newer |
| **Marker** | GPL/restricted weights | table/equation/forms-heavy PDFs | weights restricted above a revenue threshold; slow per page |
| **MinerU 2.5** | open license | scanned + scientific/technical PDFs | GPU-favored |
| **OpenDataLoader-PDF** | OSS, Java core | **deterministic, no-GPU → regulated / air-gapped** | newer |
| **Dolphin-v2** (ByteDance) | OSS | high layout fidelity | **weak on complex tables** |

## Evaluation dimensions (the ones the router cares about)
reading-order accuracy · table extraction · figure/diagram detection · OCR confidence · bbox
precision · markdown fidelity · JSON-structure quality · speed · memory · **local-only fit** ·
containerization fit · parser-lineage quality.

## Pipeline
`OmniDocBench scores → per-(parser, doc-type) ToolEvidenceCard updates → scripts/parser_router.route()`
recommendations → adapter selected behind `ParserProvider`; low-confidence parses route to steward
review (the Document-Decomposition flywheel). The router decision is deterministic + offline
(`scripts/parser_router.py --self-test`); the byte-parse + the live OmniDocBench run are the seams.

**Do NOT** route to a flagged/benchmark-only parser as a production primary without an OmniDocBench
score + a ToolEvidenceCard `decision`.
