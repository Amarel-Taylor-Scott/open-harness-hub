#!/usr/bin/env python3
"""scripts.check_native_json_roundtrip — proof (C-NATIVE-1): Baltor returns JSON in the customer's OWN shape.

Asserts, deterministically + offline:
  - native_passthrough is BYTE-IDENTICAL to the source (the original is never overwritten);
  - schema_preserving returns the SAME keys + nested structure, changing ONLY a value that carries a
    verification receipt — and every applied change appears as a NativeDiff entry (path/old/new/receipt_id);
  - an unverified value change (no receipt_id) is REFUSED, never silently applied (lossless law);
  - the sidecar carries field_facts WITH source handles + the held-out claims (omitted != deleted);
  - the export receipt records original_overwritten == False; rollback recovers the exact original bytes.

CLI: python3 scripts/check_native_json_roundtrip.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.native import NativeExportService, SidecarWriter  # noqa: E402

_NOW = "2026-06-05T00:00:00Z"


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    svc = NativeExportService()
    # a real customer source given as RAW bytes (the drop-in case) with nested structure
    raw = ('{"company": "Acme Bank",\n  "policy": {"deadline": "30 days", "tiers": [1, 2, 3]},\n'
           '  "note": "Charged twice for one purchase. No refund yet."}').encode("utf-8")
    src_hash = hashlib.sha256(raw).hexdigest()

    # 1) passthrough is byte-identical
    p = svc.export(raw, output_mode="native_passthrough", now=_NOW)
    check("native_passthrough is byte-identical to source",
          p["native_output"]["text"].encode("utf-8") == raw and p["native_output"]["byte_identical_to_source"])
    check("passthrough receipt records original_overwritten == False",
          p["receipt"]["original_overwritten"] is False)

    # 2) schema_preserving with one VERIFIED change -> same keys/structure, only the value changed
    fact = {"artifact_id": "fact-rege-10", "source_handle": "ctx://cfpb/reg-e/1005.11#deadline",
            "claim_status": "fact", "object": "10 business days", "content_hash": "h-rege-10"}
    held = {"artifact_id": "alleg-1", "claim_status": "unverified_allegation",
            "source_handle": "ctx://acme/note#s0", "text": "Charged twice for one purchase"}
    sp = svc.export(raw, output_mode="schema_preserving_with_sidecar",
                    verified_changes=[{"path": "/policy/deadline", "new_value": "10 business days",
                                       "decision": "verified_update", "receipt_id": "vr-abc"}],
                    field_facts=[SidecarWriter.field_fact("/policy/deadline", artifact=fact, receipt_id="vr-abc")],
                    held_out_claims=[SidecarWriter.held_out(held, reason="narrative allegation — not a fact")],
                    field_map=[SidecarWriter.map_row("/policy/deadline", source_handle=fact["source_handle"],
                                                     artifact_id=fact["artifact_id"], claim_status="fact")],
                    verification_receipts=[{"receipt_id": "vr-abc", "decision": "allow"}], now=_NOW)
    src_obj = json.loads(raw.decode())
    out_obj = json.loads(sp["native_output"]["text"])
    check("schema_preserving keeps the SAME top-level keys", list(out_obj.keys()) == list(src_obj.keys()),
          str(list(out_obj.keys())))
    check("schema_preserving keeps the SAME nested keys + structure",
          list(out_obj["policy"].keys()) == list(src_obj["policy"].keys())
          and out_obj["policy"]["tiers"] == [1, 2, 3])
    check("schema_preserving changed ONLY the verified value",
          out_obj["policy"]["deadline"] == "10 business days" and out_obj["note"] == src_obj["note"]
          and out_obj["company"] == src_obj["company"])
    cf = sp["diff"]["changed_fields"]
    check("exactly one NativeDiff entry with old/new/receipt_id",
          len(cf) == 1 and cf[0]["path"] == "/policy/deadline" and cf[0]["old"] == "30 days"
          and cf[0]["new"] == "10 business days" and cf[0]["receipt_id"] == "vr-abc", str(cf))

    # 3) the sidecar carries field_facts WITH source handles + held-out claims (omitted != deleted)
    sc = sp["sidecar"]
    check("sidecar field_facts carry a source handle",
          len(sc["field_facts"]) == 1 and sc["field_facts"][0]["source_handle"] == fact["source_handle"])
    check("sidecar held_out_claims preserved (omitted != deleted)",
          len(sc["held_out_claims"]) == 1 and sc["held_out_claims"][0]["artifact_id"] == "alleg-1")
    check("sidecar carries the source_hash (rehydration link)", sc["source_hash"] == src_hash)
    check("sidecar field_map links native_path -> source_handle -> artifact",
          len(sc["field_map"]) == 1 and sc["field_map"][0]["native_path"] == "/policy/deadline"
          and sc["field_map"][0]["artifact_id"] == fact["artifact_id"])

    # 4) an UNVERIFIED change (no receipt) is refused, never silently applied
    refused = False
    try:
        svc.export(raw, output_mode="schema_preserving",
                   verified_changes=[{"path": "/policy/deadline", "new_value": "0 days"}], now=_NOW)
    except ValueError:
        refused = True
    check("unverified value change is REFUSED (lossless law)", refused)

    # 5) rollback recovers the EXACT original bytes; original was never overwritten
    contract = svc._preserver.preserve(raw)  # frozen shape — original retained
    check("rollback recovers the exact original bytes", svc.rehydrate_original(contract) == raw)
    check("export receipt records original_overwritten == False",
          sp["receipt"]["original_overwritten"] is False and sp["rollback"]["source_hash"] == src_hash)

    # determinism: same inputs -> same output hash + same receipt id
    sp2 = svc.export(raw, output_mode="schema_preserving",
                     verified_changes=[{"path": "/policy/deadline", "new_value": "10 business days",
                                        "decision": "verified_update", "receipt_id": "vr-abc"}], now=_NOW)
    sp3 = svc.export(raw, output_mode="schema_preserving",
                     verified_changes=[{"path": "/policy/deadline", "new_value": "10 business days",
                                        "decision": "verified_update", "receipt_id": "vr-abc"}], now=_NOW)
    check("deterministic: identical export -> identical output hash + receipt id",
          sp2["native_output"]["bytes_sha256"] == sp3["native_output"]["bytes_sha256"]
          and sp2["receipt"]["receipt_id"] == sp3["receipt"]["receipt_id"])

    print(f"\n{'PASS — check_native_json_roundtrip: passthrough byte-identical; schema_preserving keeps keys+nesting and changes only the verified value (each with a NativeDiff); unverified change refused; sidecar carries facts+handles+held-out; original never overwritten; deterministic.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: native JSON same-shape roundtrip.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
