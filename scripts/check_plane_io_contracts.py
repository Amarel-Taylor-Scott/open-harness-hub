#!/usr/bin/env python3
"""check_plane_io_contracts — typed I/O contracts per plane are well-formed, GROUNDED in the real planes, and drive the
compiler's pre-runtime type check (the Haystack/Langflow port-typing pattern).

Proves: every typed plane has non-empty consumes+produces drawn from ONE type vocabulary; every contract plane is a REAL
plane (no invented planes); edge_compatible() correctly accepts a type-matching edge and flags a mismatch; an edge touching
an un-typed plane is treated as compatible (never blocks). serves_truth=false.

  python3 scripts/check_plane_io_contracts.py --self-test
"""
from __future__ import annotations

import json
from pathlib import Path

from src.teleon.synthesis.io_contracts import edge_compatible, load_contracts, plane_io

REPO = Path(__file__).resolve().parents[1]


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    c = load_contracts()
    vocab = set(c["type_vocabulary"])
    planes = c["planes"]
    ck("contract loads with a non-empty type vocabulary + planes", bool(vocab) and bool(planes))
    ck("serves_truth=false (types the flow, does not judge truth)", c.get("serves_truth") is False)
    ck("every typed plane has non-empty consumes + produces",
       all(p.get("consumes") and p.get("produces") for p in planes.values()))
    bad_types = {t for p in planes.values() for t in (p.get("consumes", []) + p.get("produces", [])) if t not in vocab}
    ck("all I/O types are drawn from the ONE vocabulary (no off-vocab types)", not bad_types, str(bad_types))

    real = {x["plane"] for x in json.loads((REPO / "architecture" / "tool_planes.json").read_text())["planes"]}
    ck("every contract plane is a REAL plane (grounded, no invented planes)", set(planes) <= real,
       str(set(planes) - real))
    ck("the composing planes are typed (ocr/data_extraction/embedding/vector_store/reranker/validation/llm)",
       {"ocr", "data_extraction", "embedding", "vector_store", "reranker", "validation", "llm"} <= set(planes))

    # the pre-runtime type check (this is what makes the contract load-bearing, not decorative)
    ck("edge_compatible: a type-matching edge is accepted (ocr text -> field_parsing text)",
       edge_compatible("ocr", "field_parsing"))
    ck("edge_compatible: a mismatch is FLAGGED (tts audio -> field_parsing text)",
       not edge_compatible("tts", "field_parsing"))
    ck("edge_compatible: chain ocr->embedding->vector_store is type-valid",
       edge_compatible("ocr", "embedding") and edge_compatible("embedding", "vector_store"))
    ck("edge_compatible: an UN-TYPED plane never blocks (treated compatible)",
       edge_compatible("ocr", "a_plane_not_in_the_contract") and edge_compatible(None, "llm"))
    ck("plane_io returns the contract for a typed plane and None for an un-typed one",
       plane_io("embedding") is not None and plane_io("nope") is None)

    print("\n" + ("PASS - check_plane_io_contracts: typed I/O contracts per plane, grounded in real planes, driving the "
                  "compiler's pre-runtime edge type-check (Haystack/Langflow port typing)." if not fails
                  else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
