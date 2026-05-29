#!/usr/bin/env python3
"""Seed catalog components from the retrieval/prompt taxonomy.

Turns the method options in `docs/concepts/retrieval-and-prompt-taxonomy.md` (R0–R6 + P1–P5)
into real, schema-valid `processor` components — the swappable building blocks the
governed-model-call recipe's options reference. This is the ITERATION mechanism: each method
in the taxonomy → one component here. Re-run to (re)write; extend COMPONENTS to add the rest
(the taxonomy lists ~50 method options; this seeds the first 20 + the bundle pipeline).

    python3 scripts/seed_retrieval_taxonomy_components.py        # write the YAMLs
    python3 scripts/validate.py catalog/processors/retrieval     # gate them

Not filler: every entry is a DISTINCT method (BM25 ≠ dense ≠ rerank ≠ chunk…) with its real
mechanism, the deterministic/freezable flag (the cost story), and a taxonomy step ref (R0–R6).
"""
from __future__ import annotations

from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "catalog" / "processors" / "retrieval"
DATE = "2026-05-29"
TAXO = "docs/concepts/retrieval-and-prompt-taxonomy.md"

# Each: slug, name, step (R0–R6/P/post), process_kind, capability, deterministic, side_effects,
# inputs, outputs, why (the real mechanism + when-to-use, grounded in the taxonomy).
COMPONENTS = [
    ("recursive-character-chunker", "Recursive-character chunker", "R2", "chunk.recursive",
     ["format_conversion"], True, "none", ["document", "chunk_size", "overlap"], ["chunks"],
     "Split a document along a separator hierarchy (paragraph→sentence→word) into ~256–512-token "
     "chunks with ~10–15% overlap. The robust general-purpose default; respects structure better "
     "than fixed-size, no model cost (freezable)."),
    ("page-aware-chunker", "Page / structure-aware chunker", "R2", "chunk.layout_aware",
     ["format_conversion"], True, "none", ["document", "layout"], ["chunks"],
     "Chunk on headings/tables/page anchors so citations resolve to a real location and tables stay "
     "intact. Needs structured source (PDF/HTML); preserves citable anchors. Deterministic."),
    ("bm25-keyword-retrieve", "BM25 / keyword retrieve", "R1", "retrieve.lexical_bm25",
     ["retrieval"], True, "read", ["query", "corpus", "top_k"], ["candidates"],
     "Okapi-BM25 lexical retrieval — the leg that GUARANTEES exact surface-form matching for rare "
     "terms, codes, identifiers and named entities (~94% recall on exact-match queries), where "
     "embeddings over-generalize. Zero inference; interpretable. Non-negotiable hybrid leg."),
    ("dense-vector-retrieve", "Dense bi-encoder retrieve (ANN)", "R1", "retrieve.dense_vector",
     ["retrieval", "embedding"], False, "read", ["query", "index", "top_k"], ["candidates"],
     "Embed the query and ANN-search (HNSW/IVF) a dense vector index for paraphrase/synonymy recall "
     "BM25 misses. Sub-ms semantic recall; single-vector bottleneck on exact tokens. Pair with a "
     "lexical leg (hybrid)."),
    ("fuzzy-trigram-retrieve", "Fuzzy / trigram retrieve", "R1", "retrieve.fuzzy_trigram",
     ["retrieval"], True, "read", ["query", "corpus", "max_distance"], ["candidates"],
     "Substring/typo/name matching via trigram (pg_trgm) + edit/phonetic distance — language-agnostic, "
     "in-DB, catches misspellings and name variants. Character-level only; not a semantic ranker."),
    ("exact-id-lookup", "Exact-identifier lookup", "R1", "retrieve.exact_id",
     ["retrieval"], True, "read", ["identifier", "corpus"], ["match"],
     "Deterministic hit on a structured identifier (CVE/NDC/FIPS/K-number/SKU/statute section). Only "
     "fires when the id is present, but when it does it is exact — the governance-grade retrieval leg."),
    ("hybrid-retrieve-fuse", "Hybrid retrieve (lexical + dense)", "R1", "retrieve.hybrid",
     ["retrieval"], False, "read", ["query", "corpus", "index", "top_k"], ["candidates"],
     "Run a lexical (BM25) leg and a dense leg in parallel and hand both candidate lists to fusion "
     "(R3). The recommended default: exact-term safety + semantic recall. Most tasks start here."),
    ("rrf-fusion", "Reciprocal Rank Fusion", "R3", "rerank.reciprocal_rank_fusion",
     ["reranking"], True, "none", ["ranked_lists", "k"], ["fused_list"],
     "Merge multiple retrieval legs by reciprocal rank (k≈60) — no score normalization, robust across "
     "incompatible BM25/cosine scales, no labels needed. The default fusion; switch to convex "
     "combination once ≥50 labeled query-doc pairs exist. Deterministic (freezable)."),
    ("cross-encoder-reranker", "Cross-encoder reranker", "R3", "rerank.cross_encoder",
     ["reranking"], False, "read", ["query", "candidates", "top_n"], ["reranked"],
     "Jointly encode query+doc to rescore the fused top-50→100 and keep the top-5 — the single "
     "highest-precision lever in the pipeline (~40%+ recall@k / MRR lift); cost is bounded by "
     "candidate count, not corpus size. Open-weight (bge-reranker-v2-m3) is commercial-safe."),
    ("mmr-diversity-select", "MMR diversity select", "R5", "select.mmr_diversity",
     ["routing"], True, "none", ["candidates", "lambda", "k"], ["selected"],
     "Maximal-Marginal-Relevance selection — trades relevance against diversity to cut near-duplicate "
     "redundancy and broaden coverage of the final top-k. Deterministic; λ tunes the trade-off."),
    ("simhash-dedupe", "SimHash / LSH de-duplicate", "R5", "select.dedupe_simhash",
     ["verification"], True, "none", ["candidates", "threshold"], ["deduped"],
     "Remove near-duplicate chunks (SimHash fingerprint + exact-hash) that waste context budget before "
     "placement. Deterministic and cheap; threshold-tuned. Freezable."),
    ("source-precedence-select", "Source-precedence / recency select", "R5", "select.source_precedence",
     ["governance", "routing"], True, "none", ["candidates", "policy"], ["selected", "conflicts"],
     "Where governance shows up at read time: primary, signed, valid-through sources win ties; "
     "contradictions across sources are FLAGGED rather than silently averaged. Needs source metadata "
     "+ a precedence policy. Deterministic."),
    ("context-placer-edge", "Edge context placement", "R6", "assemble.context_placement",
     ["format_conversion"], True, "none", ["chunks", "query", "instructions"], ["assembled_prompt"],
     "Place the most-relevant evidence at the edges (first AND last) in structured, source-tagged, "
     "delimited blocks, with task instructions last — directly mitigates the 'lost in the middle' "
     "attention drop and enables per-claim citation. Deterministic."),
    ("hyde-query-expander", "HyDE query expander", "R0", "query.hyde",
     ["generation", "retrieval"], False, "external_call", ["query"], ["expanded_query"],
     "Generate a hypothetical answer-document with the model and embed it to bridge the short-query↔"
     "long-doc gap for dense retrieval. Strong zero-shot recall lift; one LLM call + hallucination "
     "risk, so reserve for short/conversational queries against long technical corpora."),
    ("multi-query-expander", "Multi-query / RAG-fusion expander", "R0", "query.multi_query",
     ["generation", "retrieval"], False, "external_call", ["query", "n"], ["query_variants"],
     "Rephrase the query into N variants, retrieve each, and union via RRF — covers multiple phrasings "
     "and lifts recall when a single transform is insufficient. N× retrieval; the recall escalation."),
    ("extractive-span-selector", "Extractive span selector", "R4", "summarize.extractive",
     ["summarization", "extraction"], True, "none", ["chunks", "query"], ["spans"],
     "Deterministically select the query-relevant spans from reranked chunks — cheap, faithful, keeps "
     "the EXACT citable text (no paraphrase). Preferred compression for governed pipelines (freezable)."),
    ("contextual-compressor", "Contextual compressor", "R4", "summarize.contextual_compression",
     ["summarization"], False, "external_call", ["chunks", "query"], ["compressed"],
     "LLM extracts only the query-relevant content from each chunk to cut tokens and 'lost-in-the-middle' "
     "dilution. Strong token reduction; one model call + can drop nuance — use when extractive isn't enough."),
    ("system-prompt-builder", "System-prompt builder", "P2", "assemble.prompt_template",
     ["generation", "governance"], True, "none", ["task", "constraints", "schema"], ["system_prompt"],
     "Assemble the instruction contract — task, hard constraints, the grounding/citation requirement, "
     "and an explicit abstention policy ('if the corpus doesn't support it, say so') — SEPARATE from the "
     "persona. The cite-or-abstain contract is what converts retrieval into governed output."),
    ("prompt-injection-screen", "Prompt-injection screen", "P5", "gate.prompt_injection",
     ["safety_gating"], True, "none", ["input"], ["safe", "reason"],
     "A guard before the model call: block (and route to review) if the input tries to extract or "
     "override the system prompt, or carries injection riding in retrieved chunks. Delimit + role-"
     "separate + heuristic/classifier screen. For governed pipelines, halt-on-detect, don't proceed."),
    ("json-repair-coerce", "JSON repair / coerce", "post", "coerce.json_repair",
     ["format_conversion", "verification"], True, "none", ["model_output", "schema"], ["json", "recovered"],
     "Parse the model output as JSON; if malformed, repair/reformat once before re-verification. The "
     "deterministic post-call recovery the typed-envelope (P4) contracts against. Freezable."),
]


def build(c: tuple) -> dict:
    slug, name, step, pk, cap, det, side, ins, outs, why = c
    return {
        "id": f"processor/{slug}",
        "type": "processor",
        "version": "0.1.0",
        "name": name,
        "description": f"{why}\n\nRetrieval/prompt taxonomy step {step} (see {TAXO}). One swappable "
                       f"method-component for the governed-model-call recipe; lift is measured at the "
                       f"pipeline level, not on this component.",
        "authors": [{"name": "Open Harness Hub contributors"}],
        "license": "MIT",
        "industry": ["cross_industry", "ai"],
        "capability": cap,
        "modality": ["text", "structured"],
        "lifecycle": "experimental",
        "trust_boundary": "local",
        "tags": ["retrieval-taxonomy", f"step-{step.lower()}", "rag", "freezable" if det else "model-assisted"],
        "created": DATE,
        "updated": DATE,
        "process_kind": pk,
        "deterministic": det,
        "idempotent": True,
        "streaming": False,
        "inputs": [{"name": n, "type": "object"} for n in ins],
        "outputs": [{"name": n, "type": "object"} for n in outs],
        "side_effects": side,
        "on_error": "raise",
        "implementations": [{"kind": "callable", "path": f"scripts.processors.retrieval.{slug.replace('-', '_')}.run", "language": "python"}],
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    for c in COMPONENTS:
        comp = build(c)
        dest = OUT / f"{c[0]}.yaml"
        dest.write_text(yaml.safe_dump(comp, sort_keys=False, allow_unicode=True, width=100), encoding="utf-8")
        written.append(str(dest.relative_to(REPO)))
    print(f"wrote {len(written)} retrieval-taxonomy components to {OUT.relative_to(REPO)}/")
    for w in written:
        print("  " + w)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
