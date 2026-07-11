#!/usr/bin/env python3
"""model_portfolio — the full open-source model portfolio across TYPES (embedding, sparse/term-importance,
late-interaction/connection, classification, intent), all downloadable + local, all lanes (build out, don't prune).

Owner (2026-07-10): "find more ways to download open source embedding models, text-importance models, label-importance
models, semantic-classification models, intent models, connection models, etc" + "build out ALL mechanisms, tune in
the real world." This catalogs every model TYPE reachable WITHOUT torch (fastembed ONNX + Ollama + prototype heads),
so the linker has many independent LANES to fuse, weighted later by real-world usage — not pruned by a lab test.

TYPES:
  - dense            : the 30+ fastembed ONNX dense embedders + Ollama (embedder_zoo) — semantic recall vectors.
  - sparse           : SPLADE_PP / BM42 / BM25 / miniCOIL — LEARNED-SPARSE term weights = TEXT/KEYWORD IMPORTANCE.
  - late_interaction : ColBERTv2 / answerai-colbert / jina-colbert — token-level LATE INTERACTION = CONNECTION model.
  - classification   : embedding-prototype zero-shot over label descriptions (LABEL IMPORTANCE), trainable from
                       labelled examples (a prototype = mean of example embeddings). Works on ANY dense model.
  - intent           : classification over an INTENT label set (same mechanism, intent vocabulary).
  - image            : CLIP / jina-clip (future: code diagrams / screenshots).

Downloads are lazy (first use fetches the ONNX / pulls the Ollama model). serves_truth=false — every lane is a
candidate signal fused by weight, decided in the real world.

    PYTHONPATH=. python3 scripts/model_portfolio.py --self-test
    PYTHONPATH=. python3 scripts/model_portfolio.py --catalog       # every type x model (no downloads)
    PYTHONPATH=. python3 scripts/model_portfolio.py --verify sparse  # actually load+run one model of a type
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable, Optional

_HERE = Path(__file__).resolve()
_REPO = _HERE.parent.parent
for _p in (str(_REPO), str(_REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── the catalog per TYPE (models to download/build as lanes) ────────────────────────────────────────────────────
SPARSE_MODELS = ["prithivida/Splade_PP_en_v1", "Qdrant/bm42-all-minilm-l6-v2-attentions", "Qdrant/bm25", "Qdrant/minicoil-v1"]
LATE_INTERACTION_MODELS = ["colbert-ir/colbertv2.0", "answerdotai/answerai-colbert-small-v1", "jinaai/jina-colbert-v2"]
IMAGE_MODELS = ["Qdrant/clip-ViT-B-32-vision", "jinaai/jina-clip-v1"]
#: intent label vocabulary — extend freely (each is a lane the classifier scores). Descriptions embed to prototypes.
INTENT_LABELS = {
    "retrieve_capability": "find or search for an existing capability, primitive, or function to reuse",
    "compose_pipeline": "wire or compose multiple primitives into a pipeline or workflow",
    "transform_data": "transform, map, convert, normalize, or reshape data",
    "validate_check": "validate, verify, check, or screen an input against rules",
    "generate_new": "write new code or a novel algorithm from scratch",
    "explain_understand": "explain, describe, or understand how something works",
    "fix_debug": "fix a bug, debug an error, or repair failing behavior",
}


def _lazy_dense_models() -> list[str]:
    try:
        from scripts import embedder_zoo as _z  # noqa: PLC0415
        return list(_z.EMBEDDER_BACKENDS)
    except Exception:  # noqa: BLE001
        return []


def catalog() -> dict[str, Any]:
    """Every TYPE x model in the portfolio (no downloads) — the breadth we build out."""
    return {"dense": _lazy_dense_models(), "sparse": SPARSE_MODELS, "late_interaction": LATE_INTERACTION_MODELS,
            "classification": ["embedding_prototype (any dense model)"], "intent": list(INTENT_LABELS),
            "image": IMAGE_MODELS,
            "types": 6, "note": "all torch-free (fastembed ONNX + Ollama + prototype heads); lanes fused by "
                                "real-world-tuned weights, not lab-pruned. serves_truth=false"}


# ── SPARSE (term importance) ─────────────────────────────────────────────────────────────────────────────────
_sparse_cache: dict[str, Any] = {}


def embed_sparse(text: str, model: str = SPARSE_MODELS[0]) -> dict[int, float]:
    """Learned-sparse term weights: token-id -> importance. SPLADE/BM42 give which terms MATTER (text importance)."""
    from fastembed import SparseTextEmbedding  # noqa: PLC0415
    m = _sparse_cache.get(model)
    if m is None:
        m = _sparse_cache[model] = SparseTextEmbedding(model_name=model)
    r = next(iter(m.embed([text])))
    return {int(i): float(v) for i, v in zip(r.indices.tolist(), r.values.tolist())}


def sparse_dot(a: dict[int, float], b: dict[int, float]) -> float:
    """Sparse relevance = weighted term-overlap dot product (the learned-sparse retrieval score)."""
    return sum(a[k] * b.get(k, 0.0) for k in a)


# ── LATE INTERACTION (connection) ────────────────────────────────────────────────────────────────────────────
_li_cache: dict[str, Any] = {}


def embed_late_interaction(text: str, model: str = LATE_INTERACTION_MODELS[0]):
    """ColBERT token-level matrix (n_tokens x dim). MaxSim between query+doc token matrices = fine-grained CONNECTION."""
    from fastembed import LateInteractionTextEmbedding  # noqa: PLC0415
    m = _li_cache.get(model)
    if m is None:
        m = _li_cache[model] = LateInteractionTextEmbedding(model_name=model)
    return next(iter(m.embed([text])))


def maxsim(qtok, dtok) -> float:
    """ColBERT MaxSim: for each query token, its best-matching doc token, summed — the late-interaction score."""
    import numpy as np  # noqa: PLC0415
    q, d = np.asarray(qtok), np.asarray(dtok)
    return float(np.sum(np.max(q @ d.T, axis=1))) / max(1, len(q))


# ── CLASSIFICATION / INTENT (label importance) via embedding prototypes ──────────────────────────────────────
def _unit(v):
    import numpy as np  # noqa: PLC0415
    a = np.asarray(v, float)
    n = np.linalg.norm(a) or 1.0
    return a / n


def train_prototypes(label_examples: dict[str, list[str]], *, embed: Callable) -> dict[str, Any]:
    """A prototype = the MEAN embedding of a label's example texts (trainable: add examples -> better prototype)."""
    import numpy as np  # noqa: PLC0415
    protos = {}
    for label, examples in label_examples.items():
        vs = [_unit(embed(e)) for e in examples]
        protos[label] = _unit(np.mean(np.stack(vs), axis=0)) if vs else None
    return protos


def classify(text: str, prototypes: dict[str, Any], *, embed: Callable) -> dict[str, Any]:
    """Zero-shot / prototype semantic classification: nearest label prototype to the text embedding."""
    tv = _unit(embed(text))
    scores = {lbl: float(tv @ p) for lbl, p in prototypes.items() if p is not None}
    best = max(scores, key=scores.get) if scores else None
    return {"label": best, "scores": {k: round(v, 4) for k, v in sorted(scores.items(), key=lambda kv: -kv[1])}}


def classify_intent(query: str, *, embed: Callable, labels: Optional[dict] = None) -> dict[str, Any]:
    """Intent classification over INTENT_LABELS (label description = the prototype text)."""
    labels = labels or INTENT_LABELS
    protos = {lbl: _unit(embed(desc)) for lbl, desc in labels.items()}
    return classify(query, protos, embed=embed)


def available(kind: str, model: Optional[str] = None) -> bool:
    """Whether a type's model can load right now (guards downloads in a probe)."""
    try:
        if kind == "sparse":
            embed_sparse("probe", model or SPARSE_MODELS[0]); return True
        if kind == "late_interaction":
            embed_late_interaction("probe", model or LATE_INTERACTION_MODELS[0]); return True
    except Exception:  # noqa: BLE001
        return False
    return True


# ── self-test (offline; prototype classifier with a deterministic stub; sparse/LI verified via --verify) ──────
def _self_test() -> int:
    import numpy as np
    checks: list[tuple[str, bool, str]] = []

    cat = catalog()
    checks.append((f"catalog spans {cat['types']} model types (dense/sparse/late_interaction/classification/intent/image)",
                   cat["types"] == 6 and len(cat["sparse"]) >= 3 and len(cat["late_interaction"]) >= 3
                   and len(cat["dense"]) >= 15, json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in cat.items() if isinstance(v, list)})))

    # deterministic embed stub: bag-of-keywords vector so prototypes/classification have real signal.
    _VOCAB = ["find", "search", "reuse", "compose", "wire", "pipeline", "transform", "convert", "validate", "check",
              "write", "novel", "explain", "understand", "fix", "bug", "debug"]

    def stub(t):
        toks = set(t.lower().split())
        return [1.0 if w in toks else 0.0 for w in _VOCAB] + [0.1]

    # (2) INTENT classification routes a query to the right intent (semantic classification / intent model).
    r = classify_intent("search for an existing function to reuse", embed=stub)
    checks.append((f"intent classifier routes 'search to reuse' -> {r['label']}",
                   r["label"] == "retrieve_capability", json.dumps(list(r["scores"])[:3])))
    r2 = classify_intent("fix the failing bug in this code", embed=stub)
    checks.append((f"intent classifier routes 'fix the bug' -> {r2['label']}", r2["label"] == "fix_debug", ""))

    # (3) TRAINABLE prototypes: adding labelled examples builds a prototype that classifies held-out text.
    protos = train_prototypes({"transform_data": ["transform convert the data", "normalize reshape rows"],
                               "validate_check": ["validate check the input", "verify screen the value"]}, embed=stub)
    c = classify("convert and transform the columns", protos, embed=stub)
    checks.append((f"trained prototype classifies held-out text -> {c['label']}", c["label"] == "transform_data", ""))

    # (4) SPARSE dot + maxsim are well-defined (unit math, no download).
    sd = sparse_dot({1: 0.5, 2: 0.5}, {2: 1.0, 3: 1.0})
    ms = maxsim([[1.0, 0.0], [0.0, 1.0]], [[1.0, 0.0], [0.0, 1.0]])
    checks.append((f"sparse_dot ({sd}) + colbert maxsim ({ms}) compute correctly", abs(sd - 0.5) < 1e-9 and abs(ms - 1.0) < 1e-9, ""))

    ok = all(c[1] for c in checks)
    print(f"{'PASS' if ok else 'FAIL'} - model_portfolio: {cat['types']} model TYPES (dense {len(cat['dense'])} / "
          f"sparse {len(cat['sparse'])} / late-interaction {len(cat['late_interaction'])} / classification / "
          f"intent {len(cat['intent'])} / image {len(cat['image'])}) — torch-free, all lanes. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="The full open-source model portfolio across types (build out, don't prune).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--catalog", action="store_true", help="every type x model (no downloads)")
    ap.add_argument("--verify", default=None, help="load+run one model of a type: sparse|late_interaction")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.catalog:
        print(json.dumps(catalog(), indent=2))
        return 0
    if args.verify == "sparse":
        w = embed_sparse("hash a password into a salted digest")
        print(json.dumps({"sparse_model": SPARSE_MODELS[0], "n_terms": len(w),
                          "top_weight": round(max(w.values()), 4) if w else 0}, indent=2))
        return 0
    if args.verify == "late_interaction":
        m = embed_late_interaction("hash a password")
        print(json.dumps({"colbert_model": LATE_INTERACTION_MODELS[0], "shape": list(getattr(m, "shape", []))}, indent=2))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
