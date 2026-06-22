#!/usr/bin/env python3
"""check_reranker_port — the reranker plane has a REAL agnostic port (loop adapter-gap closed, not a stub).

Proves: select_reranker is agnostic + registry-populated; the 'auto' baseline is an always-available deterministic
LEXICAL reranker that ranks a relevant doc first (works offline, no dep); model/API rerankers (bge/cohere/...) are honest
'not wired' until present; a future reranker drops in via register_reranker_adapter with zero caller change; and
adapter_layers marks reranker WIRED + drop-in-tested. serves_truth=false.

  python3 scripts/check_reranker_port.py --self-test
"""
from __future__ import annotations

import json
from pathlib import Path

from src.teleon.retrieval.reranker_port import (LexicalReranker, NotWiredReranker, available_rerankers,
                                                register_reranker_adapter, select_reranker)

REPO = Path(__file__).resolve().parents[1]


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    r = select_reranker("auto")
    ck("'auto' resolves to the always-available lexical baseline", isinstance(r, LexicalReranker))
    docs = ["the cat sat on the mat", "quantum computing", "a dog and a cat play", "compliance rules"]
    ranked = r.rank("cat", docs, top_k=2)
    ck("lexical reranker ranks a relevant doc first (works, not a stub)", docs[ranked[0][0]].find("cat") >= 0 and len(ranked) == 2)
    ck("deterministic", r.rank("cat", docs) == select_reranker("auto").rank("cat", docs))
    ck("ranking is sorted by score desc", [s for _, s in r.rank("cat dog", docs)] == sorted((s for _, s in r.rank("cat dog", docs)), reverse=True))

    m = select_reranker("bge_reranker")
    ck("a model reranker is honest 'not wired' (no fabricated ranking)", isinstance(m, NotWiredReranker))
    try:
        m.rank("x", ["y"]); ck("not-wired raises on use", False)
    except RuntimeError:
        ck("not-wired raises on use", True)

    av = available_rerankers()
    ck("rerankers populated FROM the tool_registry plane", {"bge_reranker", "rank_bm25"} <= (set(av["registry_rerankers"]) | set(av["wired"])))
    # drop-in: a future reranker wires with zero caller change
    register_reranker_adapter("my_future_reranker", LexicalReranker)
    ck("drop-in: a newly registered reranker is selectable", select_reranker("my_future_reranker").name == "lexical_bm25")

    layer = next(l for l in json.loads((REPO / "architecture" / "adapter_layers.json").read_text())["layers"] if l["layer"] == "reranker")
    ck("adapter_layers: reranker is WIRED + drop-in-tested (gap closed)", layer["status"] == "wired" and layer["drop_in_tested"] and layer["port_module"])

    print("\n" + ("PASS - check_reranker_port: agnostic reranker port; lexical baseline always-wired + working; model "
                  "rerankers honest; drop-in; adapter gap closed." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
