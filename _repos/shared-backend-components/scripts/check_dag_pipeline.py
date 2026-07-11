#!/usr/bin/env python3
"""check_dag_pipeline — proof of the flexible DAG step system for extraction + enrichment.

Extraction/enrichment are DAGs of reusable steps (route/filter/chunk/retrieve/rerank/extract/synthesize/merge), not a
linear OCR->model cascade. This proves the engine: data-flow execution, If-branching, Loop fan-out + fan-in merge, and
the DESCENT choosing the cheapest viable alternative per choice-point as the requirement floor moves. serves_truth=false.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_dag_pipeline.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.dag import example_pipelines as ex


def _self_test() -> int:
    fails: list[str] = []

    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # ── EXTRACTION DAG ──
    dag = ex.build_extraction_dag()

    # routing/choice: a text-layer doc uses the cheap text extractor, NOT OCR/vision
    r = dag.run(ex.extraction_inputs(has_text_layer=True), floor=0.8)
    ck("[extract] text-layer doc -> pdf_text_extract (cheapest viable acquire), not OCR/vision",
       r["chosen_alternatives"]["acquire"] == "pdf_text_extract", str(r["chosen_alternatives"]))
    ck("[extract] a scanned doc (no text layer) -> OCR is chosen instead (routing)",
       dag.run(ex.extraction_inputs(has_text_layer=False, scanned=True), floor=0.8)["chosen_alternatives"]["acquire"] == "ocr")

    # the descent: the floor moves the EXTRACT tier (regex -> cheap_llm -> frontier) and cost rises
    lenient = dag.run(ex.extraction_inputs(), floor=0.5)
    strict = dag.run(ex.extraction_inputs(), floor=0.95)
    ck("[extract] lenient floor picks a cheap extractor; strict floor escalates the tier",
       lenient["chosen_alternatives"]["extract"] != strict["chosen_alternatives"]["extract"],
       f"{lenient['chosen_alternatives']['extract']} vs {strict['chosen_alternatives']['extract']}")
    ck("[extract] a higher requirement floor costs more (escalation is real)",
       strict["total_cost"] > lenient["total_cost"], f"{strict['total_cost']} vs {lenient['total_cost']}")

    # fan-out (Loop) + fan-in (merge): chunk produced a list; per-chunk extract mapped over it; merge collapsed it
    ck("[extract] chunk fans OUT to a list of passages (Loop)", isinstance(r["bus"]["passages"], list) and len(r["bus"]["passages"]) == 3)
    ck("[extract] per-chunk extract maps over the chunks (a list of per-chunk fields)", isinstance(r["bus"]["chunk_fields"], list))
    ck("[extract] merge fans IN to a single schema (fan-in)", isinstance(r["bus"]["schema"], dict) and r["bus"]["schema"].get("_validated"))
    ck("[extract] the pipeline produces an output + a path receipt", r["bus"].get("output") and len(r["path"]) >= 5)
    ck("[extract] serves_truth is false (candidate for the verification rail)", r["serves_truth"] is False)

    # ── ENRICHMENT DAG (same engine) ──
    edag = ex.build_enrichment_dag()
    e_cheap = edag.run(ex.enrichment_inputs(), floor=0.8)
    e_strict = edag.run(ex.enrichment_inputs(), floor=0.95)
    ck("[enrich] at floor 0.8 the descent picks cheap search + cheap synthesis (not premium)",
       e_cheap["chosen_alternatives"]["search"] == "web_search_cheap" and e_cheap["chosen_alternatives"]["synthesize"] == "cheap_synthesize")
    ck("[enrich] a strict floor escalates to the premium grounded providers (costs more)",
       e_strict["total_cost"] > e_cheap["total_cost"], f"{e_strict['total_cost']} vs {e_cheap['total_cost']}")
    ck("[enrich] rerank narrows sources to top-k (a real retrieve step, not OCR->model)", len(e_cheap["bus"]["topk"]) == 3)
    ck("[enrich] the answer carries source handles (grounding/provenance) + is served",
       e_cheap["bus"]["final"]["grounded"] and e_cheap["bus"]["final"]["status"] == "served")
    ck("[enrich] serves_truth is false (the synthesis is a candidate)", e_cheap["bus"]["final"]["serves_truth"] is False)

    # ── one engine, both pipelines ──
    ck("the SAME DAG engine runs both extraction and enrichment (composable, not bespoke)",
       type(dag).__name__ == "DAG" and type(edag).__name__ == "DAG")

    print("\n" + ("PASS - check_dag_pipeline: extraction + enrichment are flexible DAGs over reusable steps — data-flow "
                  "execution with If-routing (text vs OCR), Loop fan-out (chunk) + fan-in (merge), and a descent that "
                  "picks the cheapest viable alternative per choice-point as the requirement floor moves. One engine, "
                  "both pipelines; serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_dag_pipeline.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
