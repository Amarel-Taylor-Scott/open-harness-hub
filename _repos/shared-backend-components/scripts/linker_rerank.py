#!/usr/bin/env python3
"""linker_rerank — cheap RECALL over the shortlist, STRONG-model rerank on the top-K (handoff step 1).

Owner concern (2026-07-10): the 40M-vector store is model2vec (older, static, cosines cluster high) — search quality
is limited. The research-bundle fix (and the biggest quality win without re-embedding 40M vectors) is a two-stage
retrieve: **cheap model2vec RECALL** pulls a shortlist over the millions, then a **STRONG model** (EmbeddingGemma /
BGE-large / jina-code) RE-EMBEDS just the query + the shortlist (~20-50 texts) and REORDERS them. You pay the strong
model on K items per query, not on the whole corpus.

`rerank_candidates` is the reusable seam; `rerank_bench` measures MRR BEFORE (recall order) vs AFTER (strong rerank)
per strong model on paraphrased queries, so we PROVE the lift. Reuses `embedder_zoo` (the 18-backend portfolio incl.
the advanced models) + `capability_embedding.card_embed_text` (the one embed surface). serves_truth=false.

    PYTHONPATH=. python3 scripts/linker_rerank.py --self-test
    PYTHONPATH=. python3 scripts/linker_rerank.py --bench --sample 300 --models fastembed_bge_small,model2vec_potion_8m
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Callable, Optional

_HERE = Path(__file__).resolve()
_REPO = _HERE.parent.parent
for _p in (str(_REPO), str(_REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    import numpy as np
except Exception:  # pragma: no cover
    np = None  # type: ignore


def _card_text(card: dict[str, Any]) -> str:
    from scripts import capability_embedding as _ce  # noqa: PLC0415
    return _ce.card_embed_text(card) or str(card.get("title") or "")


def _unit(v):
    a = np.asarray(v, dtype="float32")
    n = np.linalg.norm(a) or 1.0
    return a / n


def _batch_embed(texts: list[str], model: str, embed: Callable) -> "np.ndarray":
    """Batch-embed with the strong model where the backend supports it (fastembed/model2vec), else per-text."""
    from scripts import embedder_zoo as _z  # noqa: PLC0415
    spec = _z.EMBEDDER_BACKENDS.get(model, {})
    kind = spec.get("kind")
    if kind == "onnx_local" and _z._load_fastembed(spec["model"]) is not None:
        mat = np.asarray(list(_z._load_fastembed(spec["model"]).embed(texts)), dtype="float32")
    elif kind == "static_pretrained" and _z._load_m2v(spec["model"]) is not None:
        mat = np.asarray(_z._load_m2v(spec["model"]).encode(texts), dtype="float32")
    else:
        mat = np.asarray([embed(t, model) for t in texts], dtype="float32")
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms


def rerank_candidates(query: str, candidates: list[dict[str, Any]], cards: Any, *, model: str,
                      embed: Optional[Callable] = None) -> list[dict[str, Any]]:
    """Reorder a shortlist by STRONG-model query↔card cosine. `candidates`=[{primitive_id,score}]; `cards`=id->card
    or a list. Returns candidates with `rerank_score`, sorted. The shortlist is small, so this is cheap."""
    if np is None:
        return candidates
    if embed is None:
        from scripts import embedder_zoo as _z  # noqa: PLC0415
        embed = _z.embed
    idx = cards if isinstance(cards, dict) else {c.get("primitive_id"): c for c in cards}
    texts = [_card_text(idx.get(c.get("primitive_id"), {})) for c in candidates]
    if not texts:
        return candidates
    qv = _unit(embed(query, model))
    M = _batch_embed(texts, model, embed)
    sims = M @ qv
    out = [{**c, "rerank_score": round(float(sims[i]), 6)} for i, c in enumerate(candidates)]
    out.sort(key=lambda r: (-r["rerank_score"], str(r.get("primitive_id"))))
    return out


# ================================================================================================================
# Before/after benchmark — recall (model2vec) then strong rerank; MRR before vs after
# ================================================================================================================
_STOP = frozenset({"the", "a", "an", "of", "to", "for", "and", "with", "into", "from", "by"})
_SWAP = {"emit": "produce", "count": "tally", "validate": "check", "sort": "order", "parse": "decode",
         "insert": "add", "hash": "digest", "extract": "pull", "normalize": "standardize", "resolve": "look up"}


def _paraphrase(title: str) -> str:
    w = re.sub(r"[^a-z0-9]+", " ", str(title).lower()).split()
    if w and w[0] in _SWAP:
        w[0] = _SWAP[w[0]]
    kept = [x for x in w if x not in _STOP] or w
    return " ".join(reversed(kept))


def _mrr(ranked_ids, relevant, k):
    hit = next((i for i, pid in enumerate(ranked_ids[:k]) if pid in relevant), None)
    return 1.0 / (hit + 1) if hit is not None else 0.0


def rerank_bench(cards: list[dict[str, Any]], labelled: Optional[list] = None, *, recall_model: str = "model2vec_potion_8m",
                 rerank_models: Optional[list[str]] = None, k_recall: int = 20, k_final: int = 10,
                 embed: Optional[Callable] = None, paraphrase: bool = True) -> dict[str, Any]:
    """MRR BEFORE (recall order) vs AFTER (strong rerank) per rerank model, on (paraphrased) title queries."""
    if np is None:
        raise RuntimeError("numpy required")
    if embed is None:
        from scripts import embedder_zoo as _z  # noqa: PLC0415
        embed = _z.embed
    rerank_models = rerank_models or ["fastembed_bge_small"]
    ids = [c.get("primitive_id") for c in cards]
    labelled = labelled or [({"q": _paraphrase(c["title"]) if paraphrase else c["title"], "rel": {c["primitive_id"]}})
                            for c in cards if c.get("title")]
    labelled = [(l["q"], l["rel"]) for l in labelled]
    # RECALL matrix (model2vec over the whole sample) — built once
    R = _batch_embed([_card_text(c) for c in cards], recall_model, embed)
    idx = {c.get("primitive_id"): c for c in cards}
    before = 0.0
    recall_hit = 0.0
    shortlists = []
    for q, rel in labelled:
        qv = _unit(embed(q, recall_model))
        order = np.argsort(-(R @ qv))[:k_recall]
        sl_ids = [ids[int(i)] for i in order]
        shortlists.append((q, rel, [{"primitive_id": pid, "score": 0.0} for pid in sl_ids]))
        before += _mrr(sl_ids, rel, k_final)
        recall_hit += 1.0 if (rel & set(sl_ids)) else 0.0  # is the answer even in the shortlist?
    n = len(labelled)
    result: dict[str, Any] = {"n_queries": n, "recall_model": recall_model, "k_recall": k_recall, "k_final": k_final,
                              "workload": "paraphrase" if paraphrase else "title",
                              "recall_at_shortlist": round(recall_hit / n, 4),
                              "mrr_before_rerank": round(before / n, 4), "rerank": {}}
    for rm in rerank_models:
        after = 0.0
        for q, rel, sl in shortlists:
            reranked = rerank_candidates(q, sl, idx, model=rm, embed=embed)
            after += _mrr([c["primitive_id"] for c in reranked], rel, k_final)
        result["rerank"][rm] = {"mrr_after": round(after / n, 4),
                                "lift": round(after / n - before / n, 4)}
    return {**result, "candidate": True, "serves_truth": False}


# ================================================================================================================
# Self-test (offline, deterministic embed stub)
# ================================================================================================================
def _fixture(n=12):
    base = [("Count Order Items", "OrderItemBatch", "OrderItemCount"),
            ("Normalize Party Name", "RawPartyName", "CanonicalPartyName"),
            ("Validate Security Scheme", "SecuritySchemeMap", "AuthValidationReport"),
            ("Sort Invoice Lines", "InvoiceLineList", "SortedInvoiceLineList"),
            ("Hash Password", "PlaintextPassword", "PasswordDigest"),
            ("Parse OpenAPI Document", "OpenApiBytes", "OpenApiDocument")]
    out = []
    for i in range(n):
        t, ie, oe = base[i % len(base)]
        out.append({"primitive_id": f"p:{i}", "title": f"{t} {i}", "blackbox": f"{t} operation.",
                    "input_edge": ie, "output_edge": oe})
    return out


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []
    if np is None:
        print("FAIL - linker_rerank: numpy required"); return 1
    cards = _fixture(12)

    # a deterministic "strong" embed stub that scores a query HIGHEST for the card whose title tokens it shares
    # (so rerank has real signal), plus a "weak" recall stub that only coarsely orders (shares the tail token).
    def _vec(text, salt):
        toks = set(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())
        base = [1.0 if t in toks else 0.0 for t in ("count","normalize","validate","sort","hash","parse",
                                                     "order","party","security","invoice","password","openapi")]
        return base + [float(salt)]
    strong = lambda t, m: _vec(t, 0)
    weak = lambda t, m: _vec(t, 0)[:1] + [float(len(t) % 3)]  # weak: near-random order

    # (1) rerank reorders a shortlist by strong query↔card similarity (the matching card rises to #1).
    target = cards[4]  # Hash Password 4
    shortlist = [{"primitive_id": c["primitive_id"], "score": 0.0} for c in cards]  # unordered
    rr = rerank_candidates("hash the password", shortlist, cards, model="strong", embed=strong)
    checks.append((f"rerank floats the matching card to #1 ({rr[0]['primitive_id']})",
                   rr[0]["primitive_id"] in {"p:4", "p:10"}, json.dumps(rr[0])))  # p:4/p:10 are Hash Password

    # (2) BENCH: strong rerank IMPROVES MRR over the weak recall order.
    rec = rerank_bench(cards, recall_model="weak", rerank_models=["strong"], k_recall=12, k_final=5,
                       embed=lambda t, m: (strong if m == "strong" else weak)(t, m), paraphrase=False)
    lift = rec["rerank"]["strong"]["lift"]
    checks.append((f"strong rerank lifts MRR (before {rec['mrr_before_rerank']} -> after {rec['rerank']['strong']['mrr_after']}, lift {lift})",
                   lift > 0 and rec["recall_at_shortlist"] == 1.0, json.dumps(rec["rerank"])))

    # (3) DETERMINISM.
    r2 = rerank_candidates("hash the password", shortlist, cards, model="strong", embed=strong)
    checks.append(("rerank deterministic", [c["primitive_id"] for c in rr] == [c["primitive_id"] for c in r2], ""))

    ok = all(c[1] for c in checks)
    print(f"{'PASS' if ok else 'FAIL'} - linker_rerank: cheap recall -> STRONG-model rerank on the shortlist; "
          f"before/after MRR bench proves the lift. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Strong-model rerank on the recall shortlist + before/after MRR benchmark.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--bench", action="store_true", help="real before/after bench on a corpus sample")
    ap.add_argument("--sample", type=int, default=300)
    ap.add_argument("--models", default="fastembed_bge_small", help="comma-separated rerank models")
    ap.add_argument("--recall", default="model2vec_potion_8m")
    ap.add_argument("--k-recall", type=int, default=20)
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.bench:
        from scripts import primitive_facet_enrichment as _fe  # noqa: PLC0415
        cards = _fe.load_cards(sample=args.sample)
        rec = rerank_bench(cards, recall_model=args.recall, rerank_models=[m.strip() for m in args.models.split(",")],
                           k_recall=args.k_recall)
        print(json.dumps(rec, indent=2))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
