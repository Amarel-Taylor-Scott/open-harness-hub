#!/usr/bin/env python3
"""check_embedding_port — the embedding plane has a REAL agnostic port (working baseline, not a stub).

Proves: select_embedder is agnostic + registry-populated; 'auto' is an always-available deterministic LEXICAL embedder
(fixed-dim, L2-normalized, works offline); learned/API embedders are honest 'not wired'; a future embedder drops in via
register_embedder_adapter; adapter_layers marks embedding WIRED + drop-in-tested. serves_truth=false.

  python3 _repos/shared-backend-components/scripts/check_embedding_port.py --self-test
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from src.teleon.synthesis.component_search import py_const_src_teleon_synthesis_component_search__INDEX_DIM
from src.teleon.retrieval.embedding_port import (py_class_src_teleon_retrieval_embedding_port__LexicalEmbedder, py_class_src_teleon_retrieval_embedding_port__NotWiredEmbedder, py_function_src_teleon_retrieval_embedding_port__available_embedders,
                                                 py_function_src_teleon_retrieval_embedding_port__register_embedder_adapter, py_function_src_teleon_retrieval_embedding_port__select_embedder)

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    e = py_function_src_teleon_retrieval_embedding_port__select_embedder("auto")
    ck("'auto' -> always-available lexical embedder", isinstance(e, py_class_src_teleon_retrieval_embedding_port__LexicalEmbedder))
    v = e.embed("governed AI context")
    ck(f"fixed-dim ({py_const_src_teleon_synthesis_component_search__INDEX_DIM}) + L2-normalized + deterministic",
       len(v) == py_const_src_teleon_synthesis_component_search__INDEX_DIM and abs(math.sqrt(sum(x * x for x in v)) - 1.0) < 1e-6 and v == py_function_src_teleon_retrieval_embedding_port__select_embedder("auto").embed("governed AI context"))
    ck("different text -> different vector", e.embed("ocr scanned doc") != v)
    m = py_function_src_teleon_retrieval_embedding_port__select_embedder("openai_embed")
    ck("a model embedder is honest 'not wired'", isinstance(m, py_class_src_teleon_retrieval_embedding_port__NotWiredEmbedder))
    try:
        m.embed("x"); ck("not-wired raises on use", False)
    except RuntimeError:
        ck("not-wired raises on use", True)
    av = py_function_src_teleon_retrieval_embedding_port__available_embedders()
    ck("embedders populated FROM the tool_registry plane", {"sentence_transformers", "bge_embed"} <= (set(av["registry_embedders"]) | set(av["wired"])))
    py_function_src_teleon_retrieval_embedding_port__register_embedder_adapter("my_future_embedder", py_class_src_teleon_retrieval_embedding_port__LexicalEmbedder)
    ck("drop-in: a newly registered embedder is selectable", py_function_src_teleon_retrieval_embedding_port__select_embedder("my_future_embedder").name == "lexical")
    layer = next((l for l in json.loads((_resource("architecture") / "adapter_layers.json").read_text())["layers"] if l["layer"] == "embedding"), None)
    ck("adapter_layers: embedding WIRED + drop-in-tested", layer and layer["status"] == "wired" and layer["drop_in_tested"] and layer["port_module"])
    print("\n" + ("PASS - check_embedding_port: agnostic embedding port; lexical baseline always-wired; model embedders "
                  "honest; drop-in; layer wired." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
