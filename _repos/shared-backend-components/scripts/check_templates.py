#!/usr/bin/env python3
"""check_templates — the template library (retrieve-and-mutate, the biggest efficiency lever).

Proves: retrieve_template finds the right skeleton for an intent (and None when nothing matches); mutate fills slots into
a concrete DAG, drops unfilled OPTIONAL slots (rerouting their edges) and reports unfilled REQUIRED slots; a mutated
template is a VERIFIED-WORKING build; mine_template proposes a new template from a trace (the library grows itself).
serves_truth=false.

  python3 _repos/shared-backend-components/scripts/check_templates.py --self-test
"""
from __future__ import annotations

from src.teleon.synthesis import templates as T
from src.teleon.synthesis.dag_contract import py_function_src_teleon_synthesis_dag_contract__verify_buildable_dag


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    ck("retrieve: an extraction intent matches the document_extraction template",
       (T.py_function_src_teleon_synthesis_templates__retrieve_template("extract fields from these invoice pdfs into our schema") or {}).get("template_id") == "document_extraction")
    ck("retrieve: a Q&A intent matches rag_qa",
       (T.py_function_src_teleon_synthesis_templates__retrieve_template("answer questions grounded in these documents") or {}).get("template_id") == "rag_qa")
    ck("retrieve: an unrelated intent matches nothing (honest None)", T.py_function_src_teleon_synthesis_templates__retrieve_template("xyzzy nonsense plugh") is None)

    doc = T.py_function_src_teleon_synthesis_templates__retrieve_template("extract invoice fields")
    # mutate: fill the required slots, leave the optional ocr_fallback unfilled -> dropped + edges rerouted
    m = T.py_function_src_teleon_synthesis_templates__mutate(doc, {"parse": "pdfplumber", "fields": "llm", "validate": "jsonschema"})
    steps = {n["step"] for n in m["nodes"]}
    ck("mutate fills required slots into concrete components", {"parse", "fields", "validate"} <= steps and not m["unfilled_required"])
    ck("mutate DROPS an unfilled optional slot (ocr_fallback) + reroutes its edges",
       "ocr_fallback" not in steps and all("ocr_fallback" not in e for e in m["edges"]))
    # the mutated template is a verified-working build (every node typed via its plane)
    v = py_function_src_teleon_synthesis_dag_contract__verify_buildable_dag(m["nodes"], m["edges"])
    ck("a mutated template is a VERIFIED-WORKING DAG", v["verified_working"], str(v))

    # an unfilled REQUIRED slot is reported (left for the composer to fill), not silently dropped
    m2 = T.py_function_src_teleon_synthesis_templates__mutate(doc, {"parse": "pdfplumber"})
    ck("mutate reports unfilled REQUIRED slots (fields/validate)", set(m2["unfilled_required"]) == {"fields", "validate"})

    # mine: a winning trace becomes a candidate template (the library grows itself)
    mined = T.py_function_src_teleon_synthesis_templates__mine_template([{"step": "a", "plane": "ocr"}, {"step": "b", "plane": "llm"}], [["a", "b"]],
                            capability_family="ocr_then_llm", keywords=["scan", "read"])
    ck("mine_template proposes a template (slots = the trace's planes)", mined["mined"] is True and len(mined["slots"]) == 2 and mined["slots"][0]["plane"] == "ocr")

    print("\n" + ("PASS - check_templates: retrieve-and-mutate (proven skeleton, not from scratch) + optional-slot pruning "
                  "+ verified-working mutation + trace mining." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
