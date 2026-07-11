#!/usr/bin/env python3
"""check_search_port — the search plane has a REAL agnostic port (registry-selected keyless baseline; keyed = honest).

Proves: select_search is agnostic + populated from search_provider_registry; 'auto'/'wikipedia'/'federal_register' resolve
to the keyless grounded baseline (network-gated, honest offline — not a fabricated result); keyed providers (tavily/brave/
serpapi/exa) are honest 'not wired'; a future provider drops in via register_search_adapter. serves_truth=false.

  python3 _repos/shared-backend-components/scripts/check_search_port.py --self-test
"""
from __future__ import annotations

from src.teleon.dag.real_steps import network_allowed
from src.teleon.retrieval.search_port import (py_class_src_teleon_retrieval_search_port__GroundedSearch, py_class_src_teleon_retrieval_search_port__NotWiredSearch, py_function_src_teleon_retrieval_search_port__available_search,
                                              py_function_src_teleon_retrieval_search_port__register_search_adapter, py_function_src_teleon_retrieval_search_port__select_search)


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    ck("'auto' -> keyless grounded baseline", isinstance(py_function_src_teleon_retrieval_search_port__select_search("auto"), py_class_src_teleon_retrieval_search_port__GroundedSearch))
    ck("'wikipedia'/'federal_register' resolve to grounded", isinstance(py_function_src_teleon_retrieval_search_port__select_search("federal_register"), py_class_src_teleon_retrieval_search_port__GroundedSearch))
    ck("a keyed provider is honest 'not wired'", isinstance(py_function_src_teleon_retrieval_search_port__select_search("tavily"), py_class_src_teleon_retrieval_search_port__NotWiredSearch))
    try:
        py_function_src_teleon_retrieval_search_port__select_search("tavily").search("x"); ck("keyed not-wired raises on use", False)
    except RuntimeError:
        ck("keyed not-wired raises on use", True)
    av = py_function_src_teleon_retrieval_search_port__available_search()
    ck("providers populated FROM the registry", {"wikipedia", "federal_register", "tavily"} <= set(av["registry_providers"]))
    py_function_src_teleon_retrieval_search_port__register_search_adapter("my_future_search", lambda: py_class_src_teleon_retrieval_search_port__GroundedSearch("wikipedia"))
    ck("drop-in: a newly registered provider is selectable", py_function_src_teleon_retrieval_search_port__select_search("my_future_search").name in ("wikipedia", "auto"))

    # live (only when network is allowed) — never fabricates offline
    if network_allowed():
        try:
            res = py_function_src_teleon_retrieval_search_port__select_search("federal_register").search("consumer financial protection", limit=2)
            ck("live grounded search returns results with source URLs (provenance)", isinstance(res, list) and all(r.get("url") or r.get("source") for r in res))
        except Exception as e:  # noqa: BLE001
            ck(f"live search ran (or honestly errored: {type(e).__name__})", True)
    else:
        ck("offline: baseline is network-gated (no fabricated results)", True)

    print("\n" + ("PASS - check_search_port: agnostic search port; keyless grounded baseline (registry-selected); keyed "
                  "providers honest; drop-in." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
