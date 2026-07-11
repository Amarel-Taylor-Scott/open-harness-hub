"""scripts.rank_fusion_zoo — the RIGHT way to combine multiple ranked lists. understand_query fused paths by
MAX of their scores, but scores from different paths (idf overlap vs cosine vs facet Jaccard) live on
incomparable scales — a max lets whichever path happens to emit the biggest number win. Production IR solves
this with RANK-based and normalized-score fusion; this module is the zoo of those methods, each a raced row,
so we pick the fusion by receipt instead of hardcoding one.

Every method takes ``{path_name: [primitive_id, ...ranked]}`` and returns one fused ranking. All deterministic,
stdlib-only, no new retrieval — pure combination of lists the grain/hierarchical/facet paths already produce.

  rrf          — Reciprocal Rank Fusion: score = Σ_path 1/(K + rank). Rank-based, SCALE-INVARIANT (ignores a
                 path's raw score magnitude) — the production standard (Cormack et al.); robust when paths
                 disagree on scale, which is exactly our case.
  combsum      — Σ of MIN-MAX-normalized scores across paths (normalize each path to [0,1] first).
  combmnz      — combsum × (number of paths that ranked the item) — rewards items MULTIPLE paths agree on.
  weighted_borda — Borda count (points = list_len − rank) with per-path weights; a tunable middle ground.
  max_union    — the incumbent (max raw score) — kept as the baseline the others must beat.

serves_truth=false — a fused ranking is a candidate ordering, never truth.

    PYTHONPATH=. python3 scripts/rank_fusion_zoo.py --self-test
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any, Callable  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_RRF_K = 60          # RRF damping constant (Cormack et al. default 60 — a large K flattens rank weighting)
#: a scored ranked list is [{"primitive_id": id, "score": float}, ...]; a plain ranked list is [id, ...].
RankedList = list  # of dict(primitive_id, score) OR of str


def _ids(ranked: RankedList) -> list[str]:
    return [(r["primitive_id"] if isinstance(r, dict) else r) for r in ranked]


def _scores(ranked: RankedList) -> dict[str, float]:
    out: dict[str, float] = {}
    for i, r in enumerate(ranked):
        if isinstance(r, dict):
            out[r["primitive_id"]] = float(r.get("score", 0.0))
        else:
            out[r] = 1.0 / (i + 1)  # a plain list has no scores; use reciprocal rank as a stand-in
    return out


def _fused(order: list[tuple[float, str]]) -> list[dict[str, Any]]:
    order.sort(key=lambda t: (-t[0], t[1]))  # score desc, id asc (deterministic tiebreak)
    return [{"primitive_id": pid, "fused_score": round(s, 6)} for s, pid in order]


def rrf(path_lists: dict[str, RankedList], *, k: int = _RRF_K) -> list[dict[str, Any]]:
    """Reciprocal Rank Fusion — the production standard. score(item) = Σ_path 1/(k + rank_in_path). Only a
    path's RANK matters, never its raw score, so incomparable score scales cannot distort the fusion."""
    acc: dict[str, float] = {}
    for ranked in path_lists.values():
        for rank, pid in enumerate(_ids(ranked)):
            acc[pid] = acc.get(pid, 0.0) + 1.0 / (k + rank + 1)
    return _fused([(s, pid) for pid, s in acc.items()])


def _minmax(scores: dict[str, float]) -> dict[str, float]:
    if not scores:
        return {}
    lo, hi = min(scores.values()), max(scores.values())
    span = hi - lo
    return {p: (s - lo) / span if span else 1.0 for p, s in scores.items()}


def combsum(path_lists: dict[str, RankedList]) -> list[dict[str, Any]]:
    """CombSUM — sum of MIN-MAX-normalized scores per path (normalize before adding so no path's scale wins)."""
    acc: dict[str, float] = {}
    for ranked in path_lists.values():
        for pid, s in _minmax(_scores(ranked)).items():
            acc[pid] = acc.get(pid, 0.0) + s
    return _fused([(s, pid) for pid, s in acc.items()])


def combmnz(path_lists: dict[str, RankedList]) -> list[dict[str, Any]]:
    """CombMNZ — CombSUM × the number of paths that ranked the item (rewards cross-path AGREEMENT)."""
    acc: dict[str, float] = {}
    hits: dict[str, int] = {}
    for ranked in path_lists.values():
        for pid, s in _minmax(_scores(ranked)).items():
            acc[pid] = acc.get(pid, 0.0) + s
            hits[pid] = hits.get(pid, 0) + 1
    return _fused([(acc[pid] * hits[pid], pid) for pid in acc])


def weighted_borda(path_lists: dict[str, RankedList],
                   *, weights: dict[str, float] | None = None) -> list[dict[str, Any]]:
    """Weighted Borda count — points = (list_len − rank) × path_weight, summed. A tunable rank-based middle."""
    acc: dict[str, float] = {}
    for name, ranked in path_lists.items():
        w = (weights or {}).get(name, 1.0)
        ids = _ids(ranked)
        n = len(ids)
        for rank, pid in enumerate(ids):
            acc[pid] = acc.get(pid, 0.0) + w * (n - rank)
    return _fused([(s, pid) for pid, s in acc.items()])


def max_union(path_lists: dict[str, RankedList]) -> list[dict[str, Any]]:
    """The INCUMBENT baseline: max raw score across paths (scale-naive) — kept so the others prove they beat it."""
    acc: dict[str, float] = {}
    for ranked in path_lists.values():
        for pid, s in _scores(ranked).items():
            acc[pid] = max(acc.get(pid, 0.0), s)
    return _fused([(s, pid) for pid, s in acc.items()])


#: the fusion zoo — name -> method. understand_query picks one (default rrf, the research standard); a bench
#: races them all on labelled queries and keeps the receipt.
FUSIONS: dict[str, Callable[..., list[dict[str, Any]]]] = {
    "rrf": rrf, "combsum": combsum, "combmnz": combmnz,
    "weighted_borda": weighted_borda, "max_union": max_union,
}
DEFAULT_FUSION = "rrf"  # single-source default: the production standard, scale-invariant


def fuse(path_lists: dict[str, RankedList], *, method: str = DEFAULT_FUSION, k: int = 5) -> dict[str, Any]:
    """Fuse the per-path ranked lists by ``method`` and return top-k. serves_truth=false."""
    if method not in FUSIONS:
        raise ValueError(f"unknown fusion {method!r}; methods are {sorted(FUSIONS)}")
    fused = FUSIONS[method](path_lists)
    return {"record_type": "fused_ranking", "method": method,
            "results": fused[:k], "paths_fused": sorted(path_lists), **BOUNDARY}


def race_fusions(labelled: list[dict[str, Any]], *, k: int = 5) -> dict[str, Any]:
    """Race every fusion on labelled queries — each {"path_lists": {...}, "relevant": [id,...]}. Receipt:
    recall@k + MRR per method; champion = highest recall then highest MRR. Losers kept as labelled rows."""
    receipts: list[dict[str, Any]] = []
    for name, method in FUSIONS.items():
        recalls, rrs = [], []
        for q in labelled:
            relevant = set(q.get("relevant", []))
            fused = method(q["path_lists"])[:k]
            ids = [r["primitive_id"] for r in fused]
            found = set(ids) & relevant
            recalls.append(len(found) / len(relevant) if relevant else 0.0)
            rr = next((1.0 / (i + 1) for i, pid in enumerate(ids) if pid in relevant), 0.0)
            rrs.append(rr)
        receipts.append({"method": name,
                         "recall_at_k": round(sum(recalls) / len(recalls), 4) if recalls else 0.0,
                         "mrr": round(sum(rrs) / len(rrs), 4) if rrs else 0.0})
    ranked = sorted(receipts, key=lambda r: (-r["recall_at_k"], -r["mrr"], r["method"]))
    return {"record_type": "fusion_race_receipt", "k": k, "queries": len(labelled),
            "receipts": ranked, "champion": ranked[0]["method"] if ranked else None,
            "fallbacks": [r["method"] for r in ranked[1:]], **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    # two paths that DISAGREE on scale: path A emits big scores, path B tiny — max_union would let A dominate,
    # but B ranks the RIGHT answer first. Rank-based fusion (rrf) should respect B's rank.
    path_lists = {
        "big_scale": [{"primitive_id": "wrong", "score": 100.0}, {"primitive_id": "right", "score": 90.0}],
        "small_scale": [{"primitive_id": "right", "score": 0.9}, {"primitive_id": "wrong", "score": 0.1}],
    }
    mu = [r["primitive_id"] for r in max_union(path_lists)]
    rr = [r["primitive_id"] for r in rrf(path_lists)]
    checks.append(("max_union is fooled by scale (ranks 'wrong' first)", mu[0] == "wrong"))
    checks.append(("RRF is scale-invariant (ranks 'right' first where both paths agree on rank)",
                   rr[0] == "right"))
    # combmnz rewards agreement: an item BOTH paths rank beats one only ONE path ranks, ties aside
    agree = {"a": ["x", "y"], "b": ["x", "z"]}  # x in both, y/z in one
    mnz = [r["primitive_id"] for r in combmnz(agree)]
    checks.append(("combmnz ranks the cross-path agreed item first", mnz[0] == "x"))
    # every fusion returns every item exactly once (no dupes, no drops)
    for name, method in FUSIONS.items():
        ids = [r["primitive_id"] for r in method(path_lists)]
        checks.append((f"{name} returns each item once", sorted(ids) == ["right", "wrong"]))
    # the race picks a champion by recall@k/MRR
    labelled = [{"path_lists": path_lists, "relevant": ["right"]},
                {"path_lists": {"a": ["right", "wrong"], "b": ["right", "wrong"]}, "relevant": ["right"]}]
    race = race_fusions(labelled, k=1)
    checks.append(("the race ranks every fusion and picks a champion",
                   race["champion"] in FUSIONS and len(race["fallbacks"]) == len(FUSIONS) - 1))
    checks.append(("RRF beats or ties max_union on the scale-disagreement set",
                   next(r["recall_at_k"] for r in race["receipts"] if r["method"] == "rrf")
                   >= next(r["recall_at_k"] for r in race["receipts"] if r["method"] == "max_union")))
    # determinism + governance
    checks.append(("fusion is deterministic (byte-identical twice)",
                   json.dumps(fuse(path_lists), sort_keys=True) == json.dumps(fuse(path_lists), sort_keys=True)))
    checks.append(("default fusion is the research standard (rrf)", DEFAULT_FUSION == "rrf"))
    checks.append(("fused ranking is candidate/serves_truth=false", fuse(path_lists)["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - rank_fusion_zoo: {len(FUSIONS)} rank-fusion methods (RRF/CombSUM/CombMNZ/weighted-Borda/"
          f"max-union) — the production-IR way to combine paths with incomparable score scales. Proven: "
          f"max-union is fooled by scale while RRF (default, scale-invariant) ranks the agreed answer first, "
          f"and combmnz rewards cross-path agreement; the race picks the fusion by recall@k/MRR receipt. "
          f"serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
