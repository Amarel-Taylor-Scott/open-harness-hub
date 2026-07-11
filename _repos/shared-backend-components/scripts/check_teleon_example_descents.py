#!/usr/bin/env python3
"""check_teleon_example_descents — proof of the two canonical Teleon example descents.

Both encode the same owner insight: "don't reach for the expensive frontier default when a cheaper BOUNDED path meets
the requirement." Both pick the cheapest-that-meets path, beat the frontier/grounded baseline on cost, stay GOVERNED
(serves_truth=false; honest MISSING / HELD-OUT), name real models from the registry, and record into the ONE descent
brain so the meta-learner learns both patterns.

  DEMO 1  document -> defined-schema extraction: text/OCR + deterministic rules + prune/compress + cheapest-capable
          LLM, escalating to a frontier LLM only as far as the document forces. (most people send the whole doc to a
          frontier model — unnecessary.)
  DEMO 2  enrich via search + LLM: cheapest grounded search provider + cheap-model synthesis, grounding preserved.
          (most people use Gemini Grounded Search — cheaper grounded options exist.)

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_teleon_example_descents.py --self-test
"""
from __future__ import annotations

import os
import sys
import tempfile

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.extraction import document_extraction_cascade as dx
from src.teleon.enrichment import search_enrich as se
from src.teleon.evolution.descent_attempt_store import DescentAttemptStore


def _self_test() -> int:
    fails: list[str] = []

    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    with tempfile.TemporaryDirectory() as d:
        brain = DescentAttemptStore(os.path.join(d, "examples.jsonl"))

        # ── DEMO 1: document -> defined-schema extraction ──
        all_structured = {"agency_license_no": dx.STRUCTURED, "agency_name": dx.STRUCTURED, "issue_date": dx.STRUCTURED}
        r_struct = dx.extract_measured(all_structured, {"has_text_layer": True, "scanned": False}, available_keys=("LLM_API_KEY",))
        ck("[extract] an all-structured schema is filled by deterministic rules with NO LLM (cheapest)",
           r_struct["met_requirement"] and not r_struct["used_llm"], str(r_struct["path"]))

        sav = dx.extraction_savings(available_keys=("LLM_API_KEY",), confidence_floor=0.8)        # strict bar
        lenient = dx.extraction_savings(available_keys=("LLM_API_KEY",), confidence_floor=0.5)    # lenient bar
        ck("[extract] the cascade meets the full schema requirement", sav["met_requirement"])
        ck("[extract] even at a STRICT bar the cascade beats always-frontier (rules free + compress the one frontier call)",
           sav["cascade_cost"] < sav["frontier_only_cost"] and sav["pct_saved"] >= 40, f"{sav['pct_saved']}% saved (strict)")
        ck("[extract] at a LENIENT bar a cheap model suffices -> the saving is even bigger (the floor moves the tier)",
           lenient["pct_saved"] > sav["pct_saved"], f"lenient {lenient['pct_saved']}% > strict {sav['pct_saved']}%")
        ck("[extract] the LLM tiers name a REAL cheap + frontier model from model_index (lineage)",
           bool(sav["model_lineage"].get("cheap_llm")) and bool(sav["model_lineage"].get("frontier_llm")), str(sav["model_lineage"]))

        no_key = dx.extract_measured(dx.EMPLOYMENT_AGENCY_SCHEMA, {"has_text_layer": True, "scanned": False}, available_keys=())
        ck("[extract] without an LLM key, unstructured fields are reported MISSING honestly (never fabricated)",
           no_key["missing"] and not no_key["used_llm"])

        e_sav = dx.record_extraction_descent(brain, available_keys=("LLM_API_KEY",))
        ck("[extract] the extraction descent is recorded into the brain", any(r["unit_id"] == "extraction:document_schema_cascade" for r in brain.all()))
        ck("[extract] extraction never serves truth (a candidate for the verification rail)", e_sav["serves_truth"] is False)

        # ── DEMO 2: enrich via search + LLM ──
        providers = se.load_providers()
        ck("[enrich] the registry has the expensive grounded baseline (gemini_grounded)", se.baseline_provider()["provider_id"] == "gemini_grounded")
        ck("[enrich] cheaper grounded search providers exist as the descent substrate",
           any(p["returns_sources"] and p["cost_per_query_usd"] < se.baseline_provider()["cost_per_query_usd"] and p["status"] != "baseline" for p in providers))

        pick = se.select_provider(grounding_required=True, quality_floor_rank=2)
        ck("[enrich] the descent picks a CHEAPER grounded provider, not the expensive default",
           pick["provider_id"] != "gemini_grounded" and pick["returns_sources"], pick["provider_id"])
        ck("[enrich] a free-but-low-quality provider is NOT picked under a quality floor (cheapest-that-MEETS)",
           pick["provider_id"] != "duckduckgo", pick["provider_id"])

        q = next(iter(se._FIXTURE_SOURCES))
        es = se.enrichment_savings(q)
        ck("[enrich] the descended path is much cheaper than the grounded-synthesis baseline (the headline)",
           es["descended_cost"] < es["baseline_cost"] and es["pct_saved"] >= 50, f"{es['pct_saved']}% saved")
        ck("[enrich] grounding is preserved — the answer carries source handles (provenance)",
           es["grounded"] and len(es["sources"]) >= 1)

        out = se.enrich(q)
        ck("[enrich] the synthesized answer never serves truth (a candidate)", out["serves_truth"] is False)
        ungrounded = se.enrich("a query with no sources at all", grounding_required=True)
        ck("[enrich] an UNGROUNDED answer is HELD OUT, not served as truth (the grounding law)",
           ungrounded["status"] == "held_out" and ungrounded["answer"] == "")

        se.record_enrichment_descent(brain, q)
        ck("[enrich] the enrichment descent is recorded into the SAME brain", any(r["unit_id"] == "enrichment:search_plus_llm" for r in brain.all()))

        # ── BOTH feed one meta-learner ──
        ck("both example descents land in the ONE descent brain (the meta-learner learns both patterns)",
           len({r["unit_id"] for r in brain.all()}) >= 2 and len(brain.training_examples()) >= 2)

    print("\n" + ("PASS - check_teleon_example_descents: BOTH canonical demos descend off the expensive default — "
                  f"document->schema extraction saves {sav['pct_saved']}% vs always-frontier (rules before LLM, cheap "
                  f"before frontier, honest MISSING), and search+LLM enrichment saves {es['pct_saved']}% vs grounded-"
                  f"synthesis (cheapest grounded provider + cheap model, grounding preserved, ungrounded held out). "
                  f"Both name real models and feed the one brain. serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_teleon_example_descents.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
