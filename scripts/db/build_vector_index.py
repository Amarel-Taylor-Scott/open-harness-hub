#!/usr/bin/env python3
"""Build vector indexes for the Open Harness Hub catalog.

Emits two JSONL streams under db/vector/:

  - oh_catalog.jsonl   — one row per artifact (the catalog index).
                          Embedding of name + description + tags.
  - oh_knowledge.jsonl — one row per knowledge / rule leaf (e.g. a
                          single GREP rule, one RAG doc, one ICD-10
                          code, one FATF section). Embedding of the
                          leaf body text.

Each row has rich, hierarchical metadata so downstream vector backends
(Pinecone / Weaviate / Qdrant / Chroma / pgvector) can filter as well
as approximate-nearest-neighbor search.

Embedder selection (in priority order):
  1. sentence-transformers/all-MiniLM-L6-v2  (D = 384)
  2. scikit-learn TF-IDF                     (D depends on corpus)
  3. hash-based bag-of-words fallback        (D = 256)

The fallback embedder is deterministic, license-free, and good enough
to demonstrate the row shape. For real semantic search install
sentence-transformers.

Usage:
  python scripts/db/build_vector_index.py
  python scripts/db/build_vector_index.py --embedder hash    # force fallback
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Iterable

try:
    import yaml
except ImportError:
    sys.stderr.write("pyyaml is required: pip install pyyaml\n")
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent.parent
CATALOG = ROOT / "catalog"
OUT_DIR = ROOT / "db" / "vector"

# ---- Embedder selection ---------------------------------------------------

def get_embedder(prefer: str = "auto"):
    if prefer in ("auto", "sbert"):
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            dim = model.get_sentence_embedding_dimension()
            def embed(texts):
                return [list(map(float, v)) for v in model.encode(texts, show_progress_bar=False)]
            return "sentence-transformers/all-MiniLM-L6-v2", dim, embed
        except Exception:
            if prefer == "sbert":
                raise

    if prefer in ("auto", "tfidf"):
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
            from sklearn.decomposition import TruncatedSVD  # type: ignore
            dim = 128
            def make_embed(corpus):
                vec = TfidfVectorizer(max_features=4096, ngram_range=(1, 2), stop_words="english")
                X = vec.fit_transform(corpus)
                svd = TruncatedSVD(n_components=min(dim, X.shape[1] - 1)) if X.shape[1] > 1 else None
                if svd is not None:
                    X = svd.fit_transform(X)
                else:
                    X = X.toarray()
                rows = [list(map(float, row)) for row in X]
                # Pad to dim
                rows = [r + [0.0] * (dim - len(r)) for r in rows]
                return rows
            return "tfidf+svd", dim, make_embed
        except Exception:
            if prefer == "tfidf":
                raise

    # Hash bag-of-words fallback (D = 256).
    dim = 256
    def embed(texts):
        out = []
        for t in texts:
            v = [0.0] * dim
            for tok in re.findall(r"[a-z0-9]+", (t or "").lower()):
                h = int(hashlib.md5(tok.encode()).hexdigest()[:8], 16)
                v[h % dim] += 1.0
            n = sum(x * x for x in v) ** 0.5
            if n > 0:
                v = [x / n for x in v]
            out.append(v)
        return out
    return "hash-bow", dim, embed


# ---- Catalog row construction --------------------------------------------

def text_for_artifact(m: dict) -> str:
    bits = [
        m.get("name", ""),
        m.get("description", ""),
        " ".join(m.get("tags", []) or []),
        " ".join(m.get("industry", []) or []),
        " ".join(m.get("capability", []) or []),
    ]
    return " · ".join(b.strip() for b in bits if b)


def catalog_rows(manifests: list[tuple[Path, dict]]) -> list[dict]:
    rows = []
    for path, m in manifests:
        rows.append({
            "artifact_id":  m["id"],
            "type":         m["type"],
            "name":         m.get("name", ""),
            "industry":     m.get("industry", []) or [],
            "capability":   m.get("capability", []) or [],
            "modality":     m.get("modality", []) or [],
            "lifecycle":    m.get("lifecycle"),
            "lifecycle_position": m.get("lifecycle_position"),
            "trust_boundary": m.get("trust_boundary"),
            "tags":         m.get("tags", []) or [],
            "license":      m.get("license"),
            "text":         text_for_artifact(m),
            "source_path":  str(path.relative_to(ROOT)),
        })
    return rows


def derive_lifecycle_position(m: dict) -> str:
    """Mirrors scripts/build_catalog_index.py for consistency."""
    t = m.get("type", "")
    name = m.get("id", "").split("/", 1)[-1].lower()
    if t == "pipeline":       return "cross_cutting.composition"
    if t == "benchmark":      return "cross_cutting.evaluation"
    if t in ("dataset", "schema"): return "cross_cutting.data"
    if t == "adapter":        return "api.model_call"
    if t == "tool":           return "api.tool_call"
    if t == "persona":        return "pre_api.context_assembly"
    if t == "rubric":         return "post_api.evaluation"
    if t in ("knowledge-pack", "logic-pack"): return "pre_api.context_assembly"
    if t == "rule-pack":
        f = m.get("family", "")
        if f in ("privacy", "schema"):                       return "pre_api.input_gating"
        if f == "grep":      return "post_api.output_safety" if "output" in name else "pre_api.input_gating"
        if f == "glob":      return "pre_api.input_gating"
        if f == "classifier":return "pre_api.classification"
        if f == "heuristic": return "post_api.output_safety" if "output" in name else "pre_api.input_gating"
        if f in ("rag", "citation"):                         return "pre_api.context_assembly"
        if f == "online_search":                             return "pre_api.query_sanitization"
        if f == "routing":                                   return "pre_api.classification"
        return "pre_api.input_gating"
    if t == "harness":
        k = m.get("kind", "model_harness")
        if k == "safety_gate":   return "post_api.output_safety" if "output" in name else "pre_api.input_gating"
        if k == "utility_surface": return "cross_cutting.composition"
        return "api.model_call"
    return "cross_cutting"


# ---- Knowledge / rule leaf extraction ------------------------------------

def leaf_rows(manifests: list[tuple[Path, dict]]) -> list[dict]:
    rows = []
    for path, m in manifests:
        type_ = m.get("type")
        industry = m.get("industry", []) or []
        if type_ == "rule-pack":
            for rule in m.get("rules", []) or []:
                rid = f"{m['id']}#{rule.get('id', '_')}"
                body = rule.get("label") or rule.get("notes") or rule.get("pattern") or rule.get("condition") or ""
                rows.append({
                    "leaf_id":   rid,
                    "pack_id":   m["id"],
                    "leaf_type": "rule",
                    "rule_family": m.get("family"),
                    "rule_id":     rule.get("id"),
                    "severity":    rule.get("severity"),
                    "category":    rule.get("category"),
                    "industry":    industry,
                    "language":    m.get("language"),
                    "text":        body,
                })
        elif type_ == "knowledge-pack":
            for f in m.get("files", []) or []:
                rel = path.parent / f["path"]
                if not rel.exists():
                    continue
                if f.get("format") in ("jsonl", None) and rel.suffix == ".jsonl":
                    for i, line in enumerate(rel.read_text().splitlines()):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        body = obj.get("text") or obj.get("descriptor") or obj.get("label") or ""
                        if not body:
                            body = " ".join(str(v) for v in obj.values() if isinstance(v, str))
                        rows.append({
                            "leaf_id":   f"{m['id']}#{obj.get('id') or obj.get('code') or i}",
                            "pack_id":   m["id"],
                            "leaf_type": (m.get("content_types", []) or ["rag_doc"])[0],
                            "industry":  industry,
                            "language":  m.get("language"),
                            "text":      body,
                            "extra":     obj,
                        })
    return rows


# ---- Driver ---------------------------------------------------------------

def collect_manifests() -> list[tuple[Path, dict]]:
    out: list[tuple[Path, dict]] = []
    for path in CATALOG.rglob("*.yaml"):
        if "_inbox" in path.parts or any(p == "data" for p in path.parts):
            continue
        try:
            data = yaml.safe_load(path.read_text())
        except yaml.YAMLError:
            continue
        if isinstance(data, dict) and "id" in data and "type" in data:
            # Pre-fill lifecycle_position if missing for downstream consumers.
            data.setdefault("lifecycle_position", derive_lifecycle_position(data))
            out.append((path, data))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--embedder", choices=["auto", "sbert", "tfidf", "hash"], default="auto")
    args = ap.parse_args()

    manifests = collect_manifests()
    cat_rows = catalog_rows(manifests)
    knw_rows = leaf_rows(manifests)

    # Embedder.
    if args.embedder == "tfidf":
        name, dim, make_embed = get_embedder("tfidf")
        cat_texts = [r["text"] for r in cat_rows]
        knw_texts = [r["text"] for r in knw_rows]
        cat_vecs = make_embed(cat_texts) if cat_texts else []
        knw_vecs = make_embed(knw_texts) if knw_texts else []
    else:
        name, dim, embed = get_embedder(args.embedder)
        cat_vecs = embed([r["text"] for r in cat_rows])
        knw_vecs = embed([r["text"] for r in knw_rows])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cat_path = OUT_DIR / "oh_catalog.jsonl"
    knw_path = OUT_DIR / "oh_knowledge.jsonl"
    meta_path = OUT_DIR / "_meta.json"

    with cat_path.open("w") as f:
        for row, vec in zip(cat_rows, cat_vecs):
            f.write(json.dumps({**row, "embedding": vec}) + "\n")
    with knw_path.open("w") as f:
        for row, vec in zip(knw_rows, knw_vecs):
            f.write(json.dumps({**row, "embedding": vec}) + "\n")
    meta_path.write_text(json.dumps({
        "embedder": name,
        "dim": dim,
        "catalog_rows": len(cat_rows),
        "knowledge_rows": len(knw_rows),
    }, indent=2))

    print(f"embedder: {name} (dim={dim})")
    print(f"  catalog index   → {cat_path.relative_to(ROOT)}  ({len(cat_rows)} rows)")
    print(f"  knowledge index → {knw_path.relative_to(ROOT)}  ({len(knw_rows)} rows)")
    print(f"  meta            → {meta_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
