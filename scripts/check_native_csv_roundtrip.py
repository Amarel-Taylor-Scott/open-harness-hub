#!/usr/bin/env python3
"""scripts.check_native_csv_roundtrip — proof (C-NATIVE-1): Baltor returns CSV in the customer's OWN shape.

Asserts, deterministically + offline:
  - the detected shape preserves columns + order + delimiter + newline exactly;
  - native_passthrough is byte-identical to the source CSV;
  - schema_preserving keeps the SAME header columns/order, changing only a VERIFIED cell value addressed by
    (row, column) — each change emits a NativeDiff entry; other cells/rows are untouched;
  - the sidecar table carries facts/warnings/receipts + the row/col field map;
  - an unverified cell change is refused; the original is never overwritten.

CLI: python3 scripts/check_native_csv_roundtrip.py --self-test
"""
from __future__ import annotations

import argparse
import csv as _csv
import hashlib
import io
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
    # a CSV with a CRLF newline + a quoted field containing a comma — both must survive byte-for-byte
    csv_text = ('company,deadline,note\r\n'
                'Acme Bank,30 days,"charged twice, no refund"\r\n'
                'Beta Corp,5 days,ok\r\n')
    raw = csv_text.encode("utf-8")
    src_hash = hashlib.sha256(raw).hexdigest()

    # shape detection: columns/order/delimiter/newline preserved
    contract = svc._preserver.preserve(raw, hint="csv")
    check("columns + order detected", contract.columns == ["company", "deadline", "note"], str(contract.columns))
    check("delimiter detected as ','", contract.delimiter == ",", repr(contract.delimiter))
    check("newline detected as CRLF", contract.newline == "\r\n", repr(contract.newline))

    # 1) passthrough is byte-identical
    p = svc.export(raw, output_mode="native_passthrough", hint="csv", now=_NOW)
    check("native_passthrough is byte-identical to source CSV",
          p["native_output"]["text"].encode("utf-8") == raw and p["native_output"]["byte_identical_to_source"])

    # 2) schema_preserving: change only one VERIFIED cell, addressed by (row, column)
    fact = {"artifact_id": "fact-rege-10", "source_handle": "ctx://cfpb/reg-e/1005.11#deadline",
            "claim_status": "fact", "object": "10 business days", "content_hash": "h-rege-10"}
    held = {"artifact_id": "alleg-1", "claim_status": "unverified_allegation",
            "source_handle": "ctx://acme#row.0.col.note.s0", "text": "charged twice, no refund"}
    sp = svc.export(raw, output_mode="schema_preserving_with_sidecar", hint="csv",
                    verified_changes=[{"path": "row.0.col.deadline", "new_value": "10 business days",
                                       "decision": "verified_update", "receipt_id": "vr-csv-1"}],
                    field_facts=[SidecarWriter.field_fact("row.0.col.deadline", artifact=fact, receipt_id="vr-csv-1")],
                    held_out_claims=[SidecarWriter.held_out(held, reason="free-text allegation")],
                    field_map=[SidecarWriter.map_row("row.0.col.deadline", source_handle=fact["source_handle"],
                                                     artifact_id=fact["artifact_id"], claim_status="fact")],
                    verification_receipts=[{"receipt_id": "vr-csv-1", "decision": "allow"}], now=_NOW)
    out_rows = list(_csv.reader(io.StringIO(sp["native_output"]["text"]), delimiter=","))
    check("schema_preserving keeps the SAME header columns + order",
          out_rows[0] == ["company", "deadline", "note"], str(out_rows[0]))
    check("schema_preserving changed ONLY the verified cell",
          out_rows[1] == ["Acme Bank", "10 business days", "charged twice, no refund"], str(out_rows[1]))
    check("other rows untouched", out_rows[2] == ["Beta Corp", "5 days", "ok"], str(out_rows[2]))
    check("output preserves the CRLF newline", "\r\n" in sp["native_output"]["text"])
    cf = sp["diff"]["changed_fields"]
    check("exactly one NativeDiff entry with old/new/receipt_id",
          len(cf) == 1 and cf[0]["path"] == "row.0.col.deadline" and cf[0]["old"] == "30 days"
          and cf[0]["new"] == "10 business days" and cf[0]["receipt_id"] == "vr-csv-1", str(cf))

    # 3) sidecar table carries facts/warnings/receipts + the row/col field map
    sc = sp["sidecar"]
    check("sidecar field_facts carry a source handle",
          len(sc["field_facts"]) == 1 and sc["field_facts"][0]["source_handle"] == fact["source_handle"])
    check("sidecar held_out_claims preserved", len(sc["held_out_claims"]) == 1)
    check("sidecar field_map uses row/col native_path",
          sc["field_map"][0]["native_path"] == "row.0.col.deadline")
    check("sidecar carries verification receipts", len(sc["verification_receipts"]) == 1)

    # 4) unverified cell change refused; original never overwritten
    refused = False
    try:
        svc.export(raw, output_mode="schema_preserving", hint="csv",
                   verified_changes=[{"path": "row.0.col.deadline", "new_value": "0 days"}], now=_NOW)
    except ValueError:
        refused = True
    check("unverified cell change is REFUSED", refused)
    check("rollback recovers the exact original CSV bytes", svc.rehydrate_original(contract) == raw)
    check("receipt records original_overwritten == False and source_hash",
          sp["receipt"]["original_overwritten"] is False and sp["receipt"]["source_hash"] == src_hash)

    print(f"\n{'PASS — check_native_csv_roundtrip: columns/order/delimiter/CRLF-newline preserved; passthrough byte-identical; schema_preserving changes only the verified cell (row,col) with a NativeDiff; sidecar carries facts/held-out/receipts + row/col field map; unverified change refused; original never overwritten.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: native CSV same-shape roundtrip.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
