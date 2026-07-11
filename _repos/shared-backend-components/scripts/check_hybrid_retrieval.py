#!/usr/bin/env python3
"""check_hybrid_retrieval — Reciprocal Rank Fusion (the standard hybrid-retrieval combine) is correct + deterministic.

Proves: RRF fuses multiple ranked lists on RANK (no score-scale calibration); a doc top of one list ranks high even if
absent from the other; hybrid_search fuses the VECTOR (embedding) + LEXICAL (BM25) baselines into one ranking, is
deterministic, and finds the on-topic doc. serves_truth=false (it ranks candidates, it does not verify them).

  python3 _repos/shared-backend-components/scripts/check_hybrid_retrieval.py --self-test
"""
from __future__ import annotations

from src.teleon.retrieval.hybrid import py_const_src_teleon_retrieval_hybrid__RRF_K, py_function_src_teleon_retrieval_hybrid__hybrid_search, py_function_src_teleon_retrieval_hybrid__reciprocal_rank_fusion


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    # RRF math: a doc ranked #1 in both lists wins; rank-based, order-stable
    fused = py_function_src_teleon_retrieval_hybrid__reciprocal_rank_fusion([["a", "b", "c"], ["a", "c", "b"]])
    keys = [k for k, _ in fused]
    ck("RRF: a doc top of BOTH lists ranks first", keys[0] == "a")
    ck("RRF score = sum of 1/(k+rank) across lists", abs(dict(fused)["a"] - (1 / (py_const_src_teleon_retrieval_hybrid__RRF_K + 1) + 1 / (py_const_src_teleon_retrieval_hybrid__RRF_K + 1))) < 1e-9)
    # a doc present in only one list still contributes (recall from either signal)
    fused2 = py_function_src_teleon_retrieval_hybrid__reciprocal_rank_fusion([["x"], ["y"]])
    ck("RRF: a doc in only ONE list still scores (hybrid recall)", set(k for k, _ in fused2) == {"x", "y"})
    ck("RRF: empty input -> empty", py_function_src_teleon_retrieval_hybrid__reciprocal_rank_fusion([]) == [])

    # hybrid_search fuses the vector + lexical baselines over real docs (deterministic, no network)
    docs = ["the cat sat on the mat", "quarterly revenue grew 12 percent", "a dog barked at the moon",
            "annual financial report and revenue figures"]
    r1 = py_function_src_teleon_retrieval_hybrid__hybrid_search("revenue growth report", docs)
    r2 = py_function_src_teleon_retrieval_hybrid__hybrid_search("revenue growth report", docs)
    ck("hybrid_search is DETERMINISTIC (same query+docs -> same ranking)", r1 == r2)
    ck("hybrid_search returns (doc_index, score) best-first over all docs", len(r1) == len(docs) and all(isinstance(i, int) for i, _ in r1))
    top_doc = docs[r1[0][0]]
    ck("hybrid_search ranks an on-topic doc first (revenue/report)", "revenue" in top_doc or "report" in top_doc)
    ck("hybrid_search: top=2 truncates", len(py_function_src_teleon_retrieval_hybrid__hybrid_search("revenue", docs, top=2)) == 2)
    ck("hybrid_search: empty docs -> empty", py_function_src_teleon_retrieval_hybrid__hybrid_search("x", []) == [])

    print("\n" + ("PASS - check_hybrid_retrieval: Reciprocal Rank Fusion combines the vector + lexical(BM25) baselines into "
                  "one ranking, rank-based (no score calibration), deterministic." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
