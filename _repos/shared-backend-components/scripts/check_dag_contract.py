#!/usr/bin/env python3
"""check_dag_contract — building a VERIFIED WORKING DAG from many components: type-compatible edges + every input
satisfied + a terminal output + a real-executor dry-run. Stricter than acyclic+hallucination-free.

Proves: a type-valid multi-component chain verifies; a type-incompatible edge FAILS; a dangling/unsatisfied input FAILS;
a cycle FAILS; an un-typed plane never false-fails; the dry-run executes through the real pipeline_dag engine.

  python3 _repos/shared-backend-components/scripts/check_dag_contract.py --self-test
"""
from __future__ import annotations

from src.teleon.synthesis.dag_contract import py_function_src_teleon_synthesis_dag_contract__verify_buildable_dag


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    # a type-valid 3-component chain: ocr(document->text) -> embedding(text->vector) -> vector_store(vector->ranked_docs)
    good_nodes = [{"step": "x", "plane": "ocr"}, {"step": "y", "plane": "embedding"}, {"step": "z", "plane": "vector_store"}]
    good_edges = [["x", "y"], ["y", "z"]]
    v = py_function_src_teleon_synthesis_dag_contract__verify_buildable_dag(good_nodes, good_edges)
    ck("a type-valid multi-component chain is VERIFIED WORKING", v["verified_working"], str(v))
    ck("verdict reports the terminal output node", v["output_nodes"] == ["z"])
    ck("the dry-run executed through the real pipeline_dag engine", v["dry_run_ok"] is True)

    # type-incompatible edge: tts(->audio) -> field_parsing(text->) — audio is not a field_parsing input
    bad = py_function_src_teleon_synthesis_dag_contract__verify_buildable_dag([{"step": "a", "plane": "tts"}, {"step": "b", "plane": "field_parsing"}], [["a", "b"]])
    ck("a TYPE-INCOMPATIBLE edge fails verification (gating, not a warning)",
       not bad["verified_working"] and ["a", "b"] in bad["type_incompatible_edges"])

    # unsatisfied input: a reranker needs (query, ranked_docs); with only 'document' as a graph input + no upstream -> dangling
    uns = py_function_src_teleon_synthesis_dag_contract__verify_buildable_dag([{"step": "r", "plane": "reranker"}], [], graph_inputs=("document",))
    ck("a node whose input TYPE no upstream/graph-input provides FAILS (no dangling inputs)",
       not uns["verified_working"] and "r" in uns["unsatisfied_inputs"])

    # cycle
    cyc = py_function_src_teleon_synthesis_dag_contract__verify_buildable_dag([{"step": "a", "plane": "llm"}, {"step": "b", "plane": "llm"}], [["a", "b"], ["b", "a"]])
    ck("a CYCLE fails verification (must be a pipeline)", not cyc["verified_working"] and not cyc["acyclic"])

    # un-typed plane never false-fails (partial coverage): caching/image_gen are not in the contract
    unt = py_function_src_teleon_synthesis_dag_contract__verify_buildable_dag([{"step": "a", "plane": "ocr"}, {"step": "b", "plane": "caching"}], [["a", "b"]])
    ck("an UN-TYPED plane edge does not false-fail (treated satisfiable)", unt["type_incompatible_edges"] == [])

    print("\n" + ("PASS - check_dag_contract: verified-working DAG build = acyclic + type-compatible edges + satisfiable "
                  "inputs + terminal output + real-executor dry-run; failure modes each caught." if not fails
                  else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
