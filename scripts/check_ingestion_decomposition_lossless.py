#!/usr/bin/env python3
"""scripts.check_ingestion_decomposition_lossless — apply-proof: the EXISTING ingest/decompose is lossless.

Decomposition is the first distillation: a raw record becomes atomic facts + held-out narrative sentences.
This proof RUNS the shipped decomposer (``scripts.ingest.decompose_structured`` — it does NOT modify it)
and stores the raw payload via the shipped content-addressed object store (``LocalContentAddressedObjectStore``),
then asserts the lossless law holds:

  * the RAW payload is preserved (round-trips byte-for-byte through the content-addressed store via an
    opaque ``payload_ref``) — decomposition never overwrites the raw record;
  * the NORMALIZED record + the DECOMPOSED atomic facts both survive, each fact with its expandable
    ``#field`` source handle;
  * the held-out narrative allegations survive as per-sentence components with ``#field.sN`` handles
    (held out, NOT certified as fact, NOT promotion-eligible);
  * EVERY input field is accounted for — no scalar field is silently dropped (orphaned) from the parse;
  * RE-DECOMPOSE does not delete the prior parse: the decomposer is deterministic (the prior parse is
    reproducible), and a re-parse with a CHANGED parser version is stored SIDE-BY-SIDE — the prior parse
    tree remains retrievable from the store.

It also feeds the real raw->facts transform into the Lane-C :class:`InformationRetentionReport` and asserts
``safe_to_promote``. Deterministic + offline (content-addressed ids; no clock/RNG). The retention builder is
imported BY FILE PATH so this lane runs even before the Lane-B store lands.

CLI: PYTHONPATH=. python3 scripts/check_ingestion_decomposition_lossless.py --self-test
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.ingest.decompose_structured import (  # noqa: E402
    CLAIM_ALLEGATION,
    CLAIM_FACT,
    decompose_cfpb_complaint,
)
from src.baltor.adapters.object_store.local_object_store import (  # noqa: E402
    LocalContentAddressedObjectStore,
)

_TENANT = "demo"
#: the raw CFPB complaint the decomposer ingests (structured scalars + a free-text narrative).
_RAW = {"complaint_id": "BILL-901", "product": "Mortgage", "issue": "Loan servicing",
        "company": "Acme Loans", "state": "CA", "company_response": "Closed with explanation", "timely": "Yes",
        "consumer_complaint_narrative": "They lost my payment. I called twice. Nothing was fixed."}
#: which raw fields are free-text narrative (held out), not structured facts.
_NARRATIVE_FIELDS = {"consumer_complaint_narrative"}


def _load_isolated(name: str, relpath: str):
    p = (_REPO / relpath).resolve()
    spec = importlib.util.spec_from_file_location(name, p)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


RR = _load_isolated("baltor_distillation_retention_report_ingest", "src/baltor/distillation/retention_report.py")


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    store = LocalContentAddressedObjectStore()

    # ── 1) the RAW payload is preserved (content-addressed; round-trips byte-for-byte) ──
    raw_bytes = json.dumps(_RAW, sort_keys=True).encode()
    ref = store.put(_TENANT, raw_bytes, mime_type="application/json")["payload_ref"]
    check("raw payload stored under an opaque content-addressed payload_ref", ref.startswith("objref:sha256:"))
    check("raw payload rehydrates byte-for-byte (decompose never overwrites raw)", store.get(ref) == raw_bytes)

    # ── 2) run the SHIPPED decomposer: normalized + decomposed facts + held-out allegations all survive ──
    parse_v1 = decompose_cfpb_complaint(_RAW, native_id="BILL-901")
    facts = [c for c in parse_v1["components"] if c["claim_status"] == CLAIM_FACT]
    allegations = [c for c in parse_v1["components"] if c["claim_status"] == CLAIM_ALLEGATION]
    check("decomposition produced atomic facts", len(facts) >= 1, str(len(facts)))
    check("decomposition produced held-out narrative allegations", len(allegations) >= 1, str(len(allegations)))

    # field handles on facts; sentence handles on allegations.
    check("every atomic fact carries an expandable #field source handle",
          all("#" in f["source_handle"] and ".s" not in f["source_handle"] for f in facts),
          str([f["source_handle"] for f in facts][:2]))
    check("every held-out allegation carries a per-sentence #field.sN source handle",
          all(".s" in a["source_handle"] for a in allegations),
          str([a["source_handle"] for a in allegations]))
    check("held-out allegations are NOT certified as fact (claim_status unverified_allegation)",
          all(a["claim_status"] == CLAIM_ALLEGATION for a in allegations))
    check("held-out allegations are NOT promotion-eligible (not served as truth)",
          all(not a["promotion_eligible"] for a in allegations))

    # ── 3) EVERY scalar input field is accounted for — none silently dropped (orphaned) ──
    scalar_fields = {k for k, v in _RAW.items() if k not in _NARRATIVE_FIELDS and v not in ("", None)}
    fact_fields = {f["field"] for f in facts}
    check("every structured input field becomes a fact (no field silently dropped)",
          scalar_fields <= fact_fields, str(sorted(scalar_fields - fact_fields)))
    narrative_sentences = _RAW["consumer_complaint_narrative"].replace("!", ".").count(".")
    check("every narrative sentence becomes a held-out chunk (no sentence silently dropped)",
          len(allegations) == narrative_sentences, f"{len(allegations)} vs {narrative_sentences}")

    # ── 4) RE-DECOMPOSE does not delete the prior parse: deterministic + a new parser stored side-by-side ──
    check("re-decompose is deterministic (the prior parse is reproducible, not destroyed)",
          parse_v1 == decompose_cfpb_complaint(_RAW, native_id="BILL-901"))
    # store parse v1, then a v2 from a CHANGED parser (different handle prefix) — BOTH must remain retrievable.
    ref_v1 = store.put(_TENANT, json.dumps(parse_v1, sort_keys=True).encode())["payload_ref"]
    parse_v2 = decompose_cfpb_complaint(_RAW, native_id="BILL-901",
                                        source_handle_prefix="ctx://cfpb/v2/complaint")
    ref_v2 = store.put(_TENANT, json.dumps(parse_v2, sort_keys=True).encode())["payload_ref"]
    check("a re-parse with a changed parser yields a DIFFERENT parse tree", ref_v1 != ref_v2)
    check("the PRIOR parse tree is still retrievable after the re-parse (not deleted)",
          json.loads(store.get(ref_v1)) == parse_v1)
    check("the NEW parse tree is also retrievable (stored side-by-side, not overwriting)",
          json.loads(store.get(ref_v2)) == parse_v2)
    check("the raw payload is STILL retrievable after both re-parses (raw never overwritten)",
          store.get(ref) == raw_bytes)

    # ── 5) feed the real raw->facts transform into the retention report → safe_to_promote ──
    # inputs = the raw scalar fields (as input facts); outputs = the decomposed atomic facts; held_out = the
    # narrative allegations. Match input ids to output fact ids by field so lineage resolves.
    fact_by_field = {f["field"]: f for f in facts}
    inputs = []
    for field in sorted(scalar_fields):
        f = fact_by_field.get(field)
        if f is None:
            continue
        inputs.append({"artifact_id": f["fact_id"], "claim_status": "fact", "artifact_type": "atomic_fact",
                       "source_handle": f["source_handle"]})
    outputs = [{"artifact_id": f["fact_id"], "claim_status": "fact", "artifact_type": "atomic_fact",
                "source_handle": f["source_handle"]} for f in facts]
    held = [{"artifact_id": a["fact_id"], "claim_status": CLAIM_ALLEGATION,
             "artifact_type": "narrative_allegation", "source_handle": a["source_handle"]} for a in allegations]
    report = RR.build_retention_report(
        transform_type="decompose", inputs=inputs + held, outputs=outputs, served=outputs, held_out=held)
    check("retention report: the real decomposition transform is safe_to_promote", report.safe_to_promote,
          str(report.notes))
    check("retention report: zero dropped source handles in decomposition", report.dropped_source_handle_count == 0)
    check("retention report: the held-out allegations are counted, not lost", report.held_out_count == len(held))

    ok = not fails
    print(
        f"\n{'PASS — check_ingestion_decomposition_lossless: the EXISTING ingest/decompose is lossless — the raw payload round-trips byte-for-byte via the content-addressed store; normalized + decomposed atomic facts (with #field handles) + held-out narrative allegations (with #field.sN handles, NOT certified, NOT promotable) all survive; every input field/sentence is accounted for; re-decompose is deterministic and a changed-parser re-parse is stored side-by-side without deleting the prior parse tree or the raw payload; the InformationRetentionReport confirms safe_to_promote.' if ok else f'{len(fails)} FAILURES: {fails}'}"
    )
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Apply-proof: the existing ingest/decompose is lossless.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
