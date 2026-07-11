#!/usr/bin/env python3
"""check_component_search — every component is labelled (text+keywords+vector) and search/compose actually works.

Owner: label components/registries with text+keywords+vectors -> a search tool that composes components. Proves: the index
covers all component kinds; the lexical embedding is deterministic + normalized + fixed-dim; search returns RELEVANT
components (a 'rerank' query surfaces a reranker; a 'forecast' query surfaces time-series); compose() returns candidate
components per ladder rung (the search-driven option set the synthesizer branches over). serves_truth=false.

  python3 _repos/shared-backend-components/scripts/check_component_search.py --self-test
"""
from __future__ import annotations

import math

from scripts.build_component_index import collect
from src.teleon.synthesis.component_search import py_const_src_teleon_synthesis_component_search__INDEX_DIM, py_function_src_teleon_synthesis_component_search__compose, py_function_src_teleon_synthesis_component_search__embed, py_function_src_teleon_synthesis_component_search__index_entry, py_function_src_teleon_synthesis_component_search__search


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    # deterministic, normalized, fixed-dim lexical embedding
    v1, v2 = py_function_src_teleon_synthesis_component_search__embed("fast cross-encoder reranker"), py_function_src_teleon_synthesis_component_search__embed("fast cross-encoder reranker")
    ck("embedding deterministic", v1 == v2)
    ck(f"embedding fixed-dim ({py_const_src_teleon_synthesis_component_search__INDEX_DIM}) + L2-normalized", len(v1) == py_const_src_teleon_synthesis_component_search__INDEX_DIM and abs(math.sqrt(sum(x * x for x in v1)) - 1.0) < 1e-6)
    ck("different text -> different vector", py_function_src_teleon_synthesis_component_search__embed("ocr scanned document") != v1)

    # build an in-memory index (no file dependency) + search/compose against it
    idx = collect()
    ck("index covers all kinds", {r["kind"] for r in idx} == {"tool", "ml_model", "microstep", "plane", "rung", "external_api"})
    ck("every component labelled with text+keywords+vector", all(r["text"] and r["keywords"] and len(r["vector"]) == py_const_src_teleon_synthesis_component_search__INDEX_DIM for r in idx))

    rerank = py_function_src_teleon_synthesis_component_search__search("cross encoder reranker relevance", k=5, index=idx)
    ck("search 'reranker' surfaces a reranker component", any("rerank" in h["id"].lower() or "reranker" in " ".join(h["keywords"]) for h in rerank[:4]), str([h["id"] for h in rerank[:4]]))
    fc = py_function_src_teleon_synthesis_component_search__search("forecast a time series", k=5, index=idx)
    ck("search 'forecast' surfaces time-series components", any("time_series" in " ".join(h["keywords"]) or "forecast" in h["id"].lower() or "sktime" in h["id"].lower() or "arima" in h["id"].lower() for h in fc[:3]), str([h["id"] for h in fc[:3]]))
    ocr = py_function_src_teleon_synthesis_component_search__search("read text from a scanned image", k=5, index=idx)
    ck("search 'scanned image' surfaces ocr/vision components", any(("ocr" in h["id"].lower()) or ("ocr" in " ".join(h["keywords"])) or ("vision" in " ".join(h["keywords"])) for h in ocr[:4]), str([h["id"] for h in ocr[:4]]))
    ck("search is ranked (descending score)", [h["score"] for h in rerank] == sorted((h["score"] for h in rerank), reverse=True))
    ck("kind filter works", all(h["kind"] == "tool" for h in py_function_src_teleon_synthesis_component_search__search("reranker", k=5, index=idx, kind="tool")))

    # compose: candidate components per rung for a real capability
    comp = py_function_src_teleon_synthesis_component_search__compose("document_extraction", k=3, index=idx)
    ck("compose returns candidates per rung", comp and all(isinstance(v, list) and v for v in comp.values()))
    ck("compose surfaces sensible components (tables rung -> a table tool)", any("camelot" in c or "tabula" in c or "tables" in c for c in comp.get("tables", [])), str(comp.get("tables")))
    ck("index entries serves_truth=false", all(r["serves_truth"] is False for r in idx))

    print("\n" + (f"PASS - check_component_search: {len(idx)} components labelled (text+keywords+vector); search relevant; "
                  "compose returns per-rung candidates." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
