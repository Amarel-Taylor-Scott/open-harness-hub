#!/usr/bin/env python3
"""check_component_standardization — the uniform Component layer: ONE invoke shape over bespoke ports (seam 1), a
compiled spec that LOWERS + RUNS end-to-end on real ports (seam 2), and a conformance gate (swap-in is proof-gated).

Proves: real ports answer the uniform invoke offline (embedding text->vector, reranker query+docs->ranked_docs); a
plane with no wired port is HONESTLY unavailable (never a fake output); a new invoker drops in via register; a 2-node
compiled DAG lowers + executes on real ports; the conformance gate passes a conforming adapter + an honest-unavailable
one and FAILS a non-conforming one. serves_truth=false.

  python3 _repos/shared-backend-components/scripts/check_component_standardization.py --self-test
"""
from __future__ import annotations

import src.teleon.components.registry as REG
from src.teleon.components import (py_class_src_teleon_components_registry__ComponentUnavailable as ComponentUnavailable,
                                   py_function_src_teleon_components_conformance__assert_conforms as assert_conforms,
                                   py_function_src_teleon_components_lowering__run_compiled as run_compiled,
                                   py_function_src_teleon_components_registry__make_component as make_component,
                                   py_function_src_teleon_components_registry__register_component_invoker as register_component_invoker)


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    # (seam 1) real ports answer the UNIFORM invoke shape, offline + deterministic
    emb = make_component("embedding", plane="embedding").invoke({"text": "hello world"})
    ck("uniform invoke: embedding text->{vector} (offline lexical baseline)", isinstance(emb.get("vector"), list) and emb["vector"])
    rer = make_component("reranker", plane="reranker").invoke({"query": "alpha", "ranked_docs": ["beta", "alpha doc", "gamma"]})
    ck("uniform invoke: reranker query+docs->{ranked_docs}", isinstance(rer.get("ranked_docs"), list) and len(rer["ranked_docs"]) == 3)

    # honest-unavailable: a typed plane with no wired invoker raises (never fabricates)
    try:
        make_component("solver", plane="constraint_solver").invoke({"record": {}})
        ck("a plane with no wired invoker is HONESTLY unavailable", False)
    except ComponentUnavailable:
        ck("a plane with no wired invoker is HONESTLY unavailable", True)

    # drop-in: a newly registered invoker is usable with zero caller change (agnostic-adapter rule)
    register_component_invoker("templating", lambda inp: {"code": "rendered " + str(inp.get("record"))})
    drop = make_component("tmpl", plane="templating").invoke({"record": {"x": 1}})
    ck("drop-in: a newly registered invoker is immediately usable", drop.get("code", "").startswith("rendered"))

    # (seam 2) a compiled spec LOWERS + RUNS end-to-end on real ports (ocr-stub -> real embedding), via the executor
    _orig_ocr = REG.py_var_src_teleon_components_registry___PLANE_INVOKERS.get("ocr")
    register_component_invoker("ocr", lambda inp: {"text": "extracted from " + str(inp.get("document"))})
    try:
        res = run_compiled([{"step": "x", "component": "ocr", "plane": "ocr"},
                            {"step": "y", "component": "embedding", "plane": "embedding"}],
                           [["x", "y"]], {"document": "/tmp/lease.pdf"})
        ok = isinstance(res["bus"].get("y"), dict) and "vector" in res["bus"]["y"] and res["path"] == ["x", "y"]
        ck("seam 2: a 2-node compiled DAG LOWERS + RUNS end-to-end on real ports (ocr->embedding)", ok, str(res.get("path")))
    finally:
        REG.py_var_src_teleon_components_registry___PLANE_INVOKERS.pop("ocr", None)
        if _orig_ocr:
            register_component_invoker("ocr", _orig_ocr)

    # conformance gate: conforming adapter passes; honest-unavailable passes; a wrong-type adapter FAILS
    ck("conformance: a real conforming adapter (embedding) passes", assert_conforms(make_component("embedding", plane="embedding"))["conformant"] is True)
    ck("conformance: an honest-unavailable adapter passes (offline lane is OK)", assert_conforms(make_component("s", plane="constraint_solver"))["conformant"] is True)
    register_component_invoker("ner", lambda inp: {"not_entities": 1})    # declares produces=[entities] but returns wrong key
    ck("conformance: a NON-conforming adapter (wrong output type) FAILS the gate", assert_conforms(make_component("bad", plane="ner"))["conformant"] is False)
    REG.py_var_src_teleon_components_registry___PLANE_INVOKERS.pop("ner", None)

    print("\n" + ("PASS - check_component_standardization: uniform invoke over bespoke ports (seam 1) + compiled-spec "
                  "lowering that RUNS on real ports (seam 2) + a proof-gated conformance check. Maximum flexibility, "
                  "drop-in, honest-unavailable." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
