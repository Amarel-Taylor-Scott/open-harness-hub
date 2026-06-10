#!/usr/bin/env python3
"""Backs `processor/catalog-search`.

Lightweight, stdlib-only retrieval over the OHH catalog. Stage 1 of the
pipeline-recommendation flow:

    user prompt
       │
       ▼
    catalog_search  ──► top 30 candidate manifests (BM25 + tag match)
       │
       ▼
    gemma_reranker  ──► top 5 with rationale
       │
       ▼
    pipeline_recommender  ──► assembled recommendation

Signals combined:
  - BM25 token overlap on (name + description + tags) — primary
  - tag-set Jaccard on (industry, capability, modality, free tags) — boost
  - type-bias — caller can prefer pipelines vs. harnesses vs. anything
  - id-prefix-match — exact-slug bonus

Cheap (no embedding model required by default). Optional embedding signal
can be added later by attaching a precomputed vector index; the
implementation gracefully degrades to BM25-only when no index is present.

CLI:
    python -m scripts.processors.catalog_search --self-test
    python -m scripts.processors.catalog_search \\
        --prompt "I need to grade an ESG supplier disclosure" --top-k 10
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "catalog"
DEFAULT_ROW_DIR = ROOT / "dist" / "catalog-db-export-rows-smoke"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.db.catalog_row_source import iter_components_from_rows, row_source_status

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")

# Common English stopwords + OHH-specific noise tokens (we drop these from BM25 vocab).
STOPWORDS = {
    "a", "an", "the", "of", "and", "or", "for", "to", "in", "on", "at", "by", "with",
    "is", "are", "be", "as", "this", "that", "from", "it", "its", "our", "we", "you",
    "your", "any", "all", "each", "into", "via", "use", "uses", "using", "used",
    "i", "need", "want", "would", "like", "can", "could", "should", "do", "does",
}


def _tokens(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "") if t.lower() not in STOPWORDS and len(t) >= 2]


def _doc_text(manifest: dict) -> str:
    parts = [
        manifest.get("name", ""),
        manifest.get("description", ""),
        " ".join(manifest.get("tags", []) or []),
        " ".join(manifest.get("industry", []) or []),
        " ".join(manifest.get("capability", []) or []),
        manifest.get("task", "") if manifest.get("type") == "pipeline" else "",
    ]
    return "\n".join(p for p in parts if p)


@dataclass
class Candidate:
    id: str
    type: str
    name: str
    score: float
    bm25: float
    jaccard: float
    matched_tokens: list[str] = field(default_factory=list)
    manifest_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "score": round(self.score, 4),
            "bm25": round(self.bm25, 4),
            "jaccard": round(self.jaccard, 4),
            "matched_tokens": list(self.matched_tokens)[:12],
            "manifest_path": self.manifest_path,
        }


# ─── Corpus loading + BM25 index ────────────────────────────────────────────


@dataclass
class CorpusDoc:
    id: str
    type: str
    name: str
    manifest_path: str
    tokens: Counter  # term-frequency Counter
    structural_set: set[str]  # for Jaccard boost
    length: int


def load_corpus(types_filter: set[str] | None = None) -> list[CorpusDoc]:
    try:
        import yaml
    except ImportError:
        sys.stderr.write("pyyaml is required: pip install pyyaml\n")
        sys.exit(2)
    docs: list[CorpusDoc] = []
    for path in CATALOG.rglob("*.yaml"):
        if "_inbox" in path.parts:
            continue
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError):
            continue
        if not isinstance(data, dict) or "id" not in data or "type" not in data:
            continue
        if types_filter and data["type"] not in types_filter:
            continue
        tokens = Counter(_tokens(_doc_text(data)))
        structural = set()
        for fname, prefix in [("industry", "industry"), ("capability", "capability"),
                              ("modality", "modality"), ("tags", "tag")]:
            for v in data.get(fname) or []:
                structural.add(f"{prefix}:{v}")
        docs.append(
            CorpusDoc(
                id=data["id"],
                type=data["type"],
                name=data.get("name", data["id"]),
                manifest_path=str(path.relative_to(ROOT)),
                tokens=tokens,
                structural_set=structural,
                length=sum(tokens.values()) or 1,
            )
        )
    return docs


def load_corpus_from_rows(row_dir: Path, types_filter: set[str] | None = None) -> list[CorpusDoc]:
    """Load search corpus from database-shaped row sets.

    `row_dir` should contain the JSONL files produced by either
    `catalog_manifest_bridge.py` or `catalog_db_export_plan.py` + psql.
    This is the first operational read path that does not walk catalog YAML.
    """
    docs: list[CorpusDoc] = []
    for component in iter_components_from_rows(row_dir):
        if types_filter and component.type not in types_filter:
            continue
        manifest = component.manifest
        tokens = Counter(_tokens(_doc_text(manifest)))
        structural: set[str] = set()
        for fname, prefix in [("industry", "industry"), ("capability", "capability"),
                              ("modality", "modality"), ("tags", "tag")]:
            for value in manifest.get(fname) or []:
                structural.add(f"{prefix}:{value}")
        docs.append(CorpusDoc(
            id=component.id,
            type=component.type,
            name=str(manifest.get("name") or component.id),
            manifest_path=component.source_path,
            tokens=tokens,
            structural_set=structural,
            length=sum(tokens.values()) or 1,
        ))
    return docs


def _bm25_score(query_tokens: list[str], doc: CorpusDoc, idf: dict[str, float],
                avgdl: float, k1: float = 1.5, b: float = 0.75) -> tuple[float, list[str]]:
    """Standard BM25 with token overlap reporting."""
    score = 0.0
    matched: list[str] = []
    for term in query_tokens:
        tf = doc.tokens.get(term, 0)
        if tf == 0:
            continue
        matched.append(term)
        i = idf.get(term, 0.0)
        denom = tf + k1 * (1 - b + b * doc.length / avgdl)
        score += i * (tf * (k1 + 1) / denom)
    return score, matched


def _build_idf(corpus: list[CorpusDoc]) -> tuple[dict[str, float], float]:
    n_docs = len(corpus)
    df: Counter = Counter()
    for doc in corpus:
        for term in doc.tokens:
            df[term] += 1
    idf: dict[str, float] = {}
    for term, df_count in df.items():
        # BM25+ form: idf = log((N - df + 0.5) / (df + 0.5) + 1)
        idf[term] = math.log((n_docs - df_count + 0.5) / (df_count + 0.5) + 1.0)
    avgdl = sum(d.length for d in corpus) / max(n_docs, 1)
    return idf, avgdl


def _query_structural_set(prompt: str, intent_tags: list[str] | None) -> set[str]:
    """Heuristic: if the prompt mentions known industry / capability names, treat as a hint."""
    out: set[str] = set()
    for tag in intent_tags or []:
        out.add(f"tag:{tag}")
    text = prompt.lower()
    # Light heuristic — picks up the most-cited terms only.
    HINTS = {
        "esg": "industry:esg", "supply chain": "industry:supply_chain",
        "csddd": "tag:csddd", "csrd": "tag:csrd", "sdg": "tag:sdg",
        "legal": "industry:legal", "statute": "tag:statute", "regulation": "tag:regulation",
        "wikipedia": "tag:wikipedia", "npov": "tag:npov",
        "healthcare": "industry:healthcare", "radiology": "industry:healthcare.radiology",
        "contract": "industry:legal.contract", "aml": "industry:finance.aml",
        "code review": "industry:software.codereview", "security": "industry:security",
        "saas": "industry:software", "launch": "tag:launch",
        "compliance": "industry:compliance", "gdpr": "industry:privacy.gdpr",
        "annex iv": "tag:eu-ai-act", "eu ai act": "industry:ai_governance.eu_act",
    }
    for word, tag in HINTS.items():
        if word in text:
            out.add(tag)
    return out


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    return len(a & b) / len(a | b)


# ─── Public entrypoint ──────────────────────────────────────────────────────


def run(
    prompt: str,
    top_k: int = 30,
    types_filter: list[str] | None = None,
    intent_tags: list[str] | None = None,
    bm25_weight: float = 1.0,
    jaccard_weight: float = 0.5,
    type_bias: dict[str, float] | None = None,
    row_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Search the catalog. Returns top-k candidates with combined score.

    Args:
        prompt: free-text user query (e.g., "I need a pipeline to grade ESG suppliers")
        top_k: candidates to return
        types_filter: optional list of component types to restrict to (e.g., ['pipeline','harness'])
        intent_tags: optional explicit hints
        type_bias: optional dict {type_name: multiplier}, default favors pipeline+harness
    """
    if not prompt or not prompt.strip():
        return {"prompt": prompt, "candidates": [], "stats": {"reason": "empty_prompt"}}

    types_set = set(types_filter) if types_filter else None
    row_dir_value = row_dir or os.environ.get("OH_CATALOG_ROW_DIR")
    selected_row_dir = Path(row_dir_value) if row_dir_value else None
    if selected_row_dir is not None:
        corpus = load_corpus_from_rows(selected_row_dir, types_set)
        corpus_source = "database_rows"
    else:
        corpus = load_corpus(types_set)
        corpus_source = "catalog_yaml"
    if not corpus:
        return {"prompt": prompt, "candidates": [], "stats": {"reason": "empty_corpus"}}

    idf, avgdl = _build_idf(corpus)
    q_tokens = _tokens(prompt)
    q_struct = _query_structural_set(prompt, intent_tags)
    # Default bias: pipelines + harnesses preferred (they're "things you run")
    bias = type_bias or {
        "pipeline": 1.30, "harness": 1.20, "tool": 1.10,
        "rule-pack": 1.00, "knowledge-pack": 0.95, "rubric": 0.95,
        "persona": 0.90, "adapter": 0.85, "processor": 0.85,
        "pattern": 0.85, "dataset": 0.80, "schema": 0.70,
        "benchmark": 0.95,
    }

    candidates: list[Candidate] = []
    for doc in corpus:
        bm25, matched = _bm25_score(q_tokens, doc, idf, avgdl)
        jac = _jaccard(q_struct, doc.structural_set)
        combined = (bm25_weight * bm25) + (jaccard_weight * jac * 10.0)
        combined *= bias.get(doc.type, 1.0)
        if combined <= 0:
            continue
        candidates.append(
            Candidate(
                id=doc.id, type=doc.type, name=doc.name,
                score=combined, bm25=bm25, jaccard=jac,
                matched_tokens=matched, manifest_path=doc.manifest_path,
            )
        )

    candidates.sort(key=lambda c: -c.score)
    top = candidates[:top_k]
    return {
        "prompt": prompt,
        "candidates": [c.to_dict() for c in top],
        "stats": {
            "corpus_size": len(corpus),
            "corpus_source": corpus_source,
            "row_dir": str(selected_row_dir) if selected_row_dir is not None else "",
            "row_source_status": row_source_status(selected_row_dir) if selected_row_dir is not None else None,
            "matched_at_least_one_token": len(candidates),
            "returned": len(top),
            "query_tokens": q_tokens,
            "query_structural_hints": sorted(q_struct),
        },
    }


# ─── Self-test ──────────────────────────────────────────────────────────────


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        marker = "ok" if ok else "FAIL"
        print(f"  [{marker}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    print("[self-test] _tokens drops stopwords")
    toks = _tokens("I need a pipeline to grade ESG suppliers")
    check("no stopword 'i'", "i" not in toks)
    check("no stopword 'need'", "need" not in toks)
    check("keeps 'pipeline'", "pipeline" in toks)
    check("keeps 'esg'", "esg" in toks)

    print("[self-test] BM25 against a tiny synthetic corpus")
    fake_corpus = [
        CorpusDoc(id="pipeline/esg-supplier-grading", type="pipeline",
                  name="ESG supplier grading", manifest_path="x",
                  tokens=Counter(_tokens("Grade ESG supplier disclosure against CSDDD")),
                  structural_set={"industry:esg", "industry:supply_chain"},
                  length=10),
        CorpusDoc(id="pipeline/cookie-recipe-finder", type="pipeline",
                  name="Cookie recipe finder", manifest_path="x",
                  tokens=Counter(_tokens("Find chocolate chip cookie recipes online")),
                  structural_set={"industry:food"},
                  length=10),
    ]
    idf, avgdl = _build_idf(fake_corpus)
    s1, _ = _bm25_score(_tokens("ESG supplier"), fake_corpus[0], idf, avgdl)
    s2, _ = _bm25_score(_tokens("ESG supplier"), fake_corpus[1], idf, avgdl)
    check("ESG query ranks ESG doc above cookie doc", s1 > s2, detail=f"{s1=}, {s2=}")

    print("[self-test] structural hint extraction")
    s = _query_structural_set("I need a pipeline to grade ESG supplier disclosures under CSDDD", None)
    check("ESG industry hint present", "industry:esg" in s)
    check("CSDDD tag hint present", "tag:csddd" in s)

    print("[self-test] live catalog search returns ESG pipeline for ESG prompt")
    res = run("I need a pipeline to grade an ESG supplier disclosure against CSDDD", top_k=5)
    top_ids = [c["id"] for c in res["candidates"]]
    check("at least one ESG-related candidate in top 5",
          any("esg" in cid.lower() or "supplier" in cid.lower() for cid in top_ids),
          detail=str(top_ids))

    if DEFAULT_ROW_DIR.exists():
        print("[self-test] database row corpus search returns ESG pipeline for ESG prompt")
        row_res = run(
            "I need a pipeline to grade an ESG supplier disclosure against CSDDD",
            top_k=5,
            row_dir=DEFAULT_ROW_DIR,
        )
        row_top_ids = [c["id"] for c in row_res["candidates"]]
        check("row corpus source marked database_rows", row_res["stats"].get("corpus_source") == "database_rows")
        check("row corpus has components", row_res["stats"].get("corpus_size", 0) > 0)
        check("row source has ESG-related candidate in top 5",
              any("esg" in cid.lower() or "supplier" in cid.lower() for cid in row_top_ids),
              detail=str(row_top_ids))

    print(f"\n{'all self-tests passed.' if not failures else f'{len(failures)} failures: {failures}'}")
    return 0 if not failures else 1


# ─── CLI ────────────────────────────────────────────────────────────────────


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Catalog search (BM25 + tag-set Jaccard).")
    p.add_argument("--prompt", help="Free-text user query")
    p.add_argument("--top-k", type=int, default=10)
    p.add_argument("--type", action="append", help="Restrict to these component types (repeatable)")
    p.add_argument("--intent-tag", action="append", help="Explicit tag hint (repeatable)")
    p.add_argument("--row-dir", help="Read database-shaped row sets instead of walking catalog YAML")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)

    if args.self_test:
        return _self_test()
    if not args.prompt:
        p.error("--prompt or --self-test required")

    res = run(prompt=args.prompt, top_k=args.top_k, types_filter=args.type, intent_tags=args.intent_tag, row_dir=args.row_dir)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
