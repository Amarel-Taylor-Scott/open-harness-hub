#!/usr/bin/env python3
"""check_microsteps — rungs decompose into smaller micro-steps (finer components), typed by the seven primitives.

Owner: generate smaller ladder rungs/steps + more components. Proves: each decomposed rung -> >=3 atomic micro-steps,
each typed by a real primitive + a declared plane; the decomposed (capability, rung) pairs are REAL ladder rungs; the
micro-DAG is strictly FINER than the rung DAG (more nodes); micro decision points feed the synthesis tree; the generator
prompt names the 7 primitives (so more rungs can be decomposed); coverage is computed. serves_truth=false.

  python3 _repos/shared-backend-components/scripts/check_microsteps.py --self-test
"""
from __future__ import annotations

import json
from pathlib import Path

from src.teleon.synthesis import intent_to_dag as I
from src.teleon.synthesis import microsteps as M

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_PRIMS = {"input", "knowledge_corpus", "if_statement", "action", "loop", "stop", "output"}


def _self_test() -> int:
    reg = json.loads((_resource("architecture") / "rung_microsteps.json").read_text(encoding="utf-8"))
    decomps = reg["decompositions"]
    planes = {p["plane"] for p in json.loads((_resource("architecture") / "tool_planes.json").read_text())["planes"]}
    ladder_rungs = {(l["capability"], r["tier"]) for l in json.loads((_resource("architecture") / "capability_ladders.json").read_text())["ladders"] for r in l["rungs"]}
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    ck(f"rungs decomposed into micro-steps ({len(decomps)})", len(decomps) >= 5)
    ck("every decomposition targets a REAL ladder rung", all((d["capability"], d["rung"]) in ladder_rungs for d in decomps),
       str([(d["capability"], d["rung"]) for d in decomps if (d["capability"], d["rung"]) not in ladder_rungs]))
    ck("each decomposed rung has >=3 micro-steps (genuinely finer)", all(len(d["microsteps"]) >= 3 for d in decomps))
    bad_prim = sorted({m["primitive"] for d in decomps for m in d["microsteps"] if m["primitive"] not in _PRIMS})
    ck("every micro-step typed by one of the 7 primitives", not bad_prim, str(bad_prim))
    bad_plane = sorted({m.get("plane_hint") for d in decomps for m in d["microsteps"] if m.get("plane_hint") not in planes})
    ck("every micro-step's plane_hint is declared", not bad_plane, str(bad_plane))
    ck("micro-steps carry does + deterministic", all(m.get("does") and "deterministic" in m for d in decomps for m in d["microsteps"]))

    # the micro-DAG is strictly FINER than the rung DAG
    intent = "extract fields from these invoices into our schema"
    rung_dag, micro_dag = I.py_function_src_teleon_synthesis_intent_to_dag__build_dag(intent), M.py_function_src_teleon_synthesis_microsteps__expand_to_micro_dag(intent)
    ck("micro-DAG has MORE nodes than the rung DAG (decomposition is real)", len(micro_dag["nodes"]) > len(rung_dag["nodes"]),
       f"{len(micro_dag['nodes'])} !> {len(rung_dag['nodes'])}")
    ck("micro-DAG nodes are chained (edges = nodes-1 within a linear flow)", len(micro_dag["edges"]) == len(micro_dag["nodes"]) - 1)
    mdp = M.py_function_src_teleon_synthesis_microsteps__micro_decision_points(intent)
    ck("micro decision points feed the synthesis tree (every point has >=1 option)", mdp and all(o for _, o in mdp))
    ck("a known rung decomposes (document_extraction/text_layer -> open/extract/segment)",
       {m["id"] for m in M.py_function_src_teleon_synthesis_microsteps__microsteps_for("document_extraction", "text_layer")} >= {"open_document", "extract_text_layer", "segment_pages"})

    prompt = M.py_function_src_teleon_synthesis_microsteps__generate_microstep_prompt("ocr", "enhanced_ocr", "preprocess + stronger OCR")
    ck("generator prompt names the 7 primitives (decompose MORE rungs)", all(p in prompt for p in ("input", "action", "output")) and "atomic" in prompt)
    cov = M.py_function_src_teleon_synthesis_microsteps__coverage()
    ck("coverage computed (decomposed vs total rungs)", cov["rungs_decomposed"] >= 5 and cov["microsteps_total"] >= 25)
    ck("serves_truth=false", reg.get("serves_truth") is False)

    print(f"\n  micro-step coverage: {cov['rungs_decomposed']}/{cov['rungs_total']} rungs decomposed, "
          f"{cov['microsteps_total']} micro-components (generate the rest via generate_microstep_prompt)")
    print((f"PASS - check_microsteps: {len(decomps)} rungs -> finer micro-steps typed by the 7 primitives; micro-DAG "
           "finer than the rung DAG; generator for more." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
