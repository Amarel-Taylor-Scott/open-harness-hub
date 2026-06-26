#!/usr/bin/env python3
"""scripts.check_native_export_same_schema — proof (C-NATIVE-1): schema_preserving output schema == input schema.

The headline guarantee: a customer can drop Baltor in WITHOUT changing their data model. This proof compares the
SHAPE signature (keys + nesting for JSON; columns + order + delimiter + newline for CSV) of the input against the
schema_preserving output and asserts they are identical — across all the schema-preserving + passthrough + dual +
compare modes. The negative control proves the check has teeth: an output that DROPPED a key is detected as a
schema mismatch (FAIL), so a lossy projection can never pass as "same schema".

Deterministic + offline + stdlib only.

CLI: python3 scripts/check_native_export_same_schema.py --self-test
"""
from __future__ import annotations

import argparse
import csv as _csv
import io
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.native import NativeExportService, OUTPUT_MODES  # noqa: E402
from src.baltor.native.native_format_preserver import NativeFormatPreserver  # noqa: E402

_NOW = "2026-06-05T00:00:00Z"
_PRESERVER = NativeFormatPreserver()


def _json_shape(text: str) -> list:
    """Leaf JSON-pointer field order — the JSON schema-shape (keys + nesting), value-independent."""
    return _PRESERVER._json_contract(json.loads(text), text.encode(), "", "").field_order


def _csv_shape(text: str, *, delimiter: str = ",") -> dict:
    rows = list(_csv.reader(io.StringIO(text), delimiter=delimiter))
    return {"columns": rows[0] if rows else [], "row_count": max(0, len(rows) - 1)}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    svc = NativeExportService()

    # ── JSON: schema (field order) identical across every relevant mode ──
    raw_json = ('{"company": "Acme Bank", "policy": {"deadline": "30 days", "tiers": [1, 2, 3]}, '
                '"active": true}').encode("utf-8")
    in_shape = _json_shape(raw_json.decode())
    changes = [{"path": "/policy/deadline", "new_value": "10 business days",
                "decision": "verified_update", "receipt_id": "vr-1"}]
    for mode in ("native_passthrough", "native_passthrough_with_sidecar", "schema_preserving",
                 "schema_preserving_with_sidecar", "compare"):
        vc = changes if mode in ("schema_preserving", "schema_preserving_with_sidecar", "compare") else None
        out = svc.export(raw_json, output_mode=mode, verified_changes=vc, now=_NOW)
        out_shape = _json_shape(out["native_output"]["text"])
        check(f"JSON output schema == input schema [{mode}]", out_shape == in_shape,
              f"in={in_shape} out={out_shape}")

    # the contract's own shape_signature also matches input==schema_preserving output
    c_in = _PRESERVER.preserve(raw_json)
    sp = svc.export(raw_json, output_mode="schema_preserving", verified_changes=changes, now=_NOW)
    c_out = _PRESERVER.preserve(sp["native_output"]["text"].encode())
    check("JSON shape_signature identical (contract-level)", c_in.shape_signature() == c_out.shape_signature())

    # ── CSV: columns/order identical; delimiter + newline preserved ──
    raw_csv = "company,deadline,note\r\nAcme,30 days,ok\r\nBeta,5 days,fine\r\n".encode("utf-8")
    in_csv = _csv_shape(raw_csv.decode())
    csv_changes = [{"path": "row.0.col.deadline", "new_value": "10 business days",
                    "decision": "verified_update", "receipt_id": "vr-c"}]
    for mode in ("native_passthrough", "schema_preserving", "schema_preserving_with_sidecar"):
        vc = csv_changes if mode.startswith("schema_preserving") else None
        out = svc.export(raw_csv, output_mode=mode, hint="csv", verified_changes=vc, now=_NOW)
        out_csv = _csv_shape(out["native_output"]["text"])
        check(f"CSV output schema == input schema [{mode}]",
              out_csv["columns"] == in_csv["columns"] and out_csv["row_count"] == in_csv["row_count"],
              f"in={in_csv} out={out_csv}")
    out_pre = svc.export(raw_csv, output_mode="schema_preserving", hint="csv", verified_changes=csv_changes, now=_NOW)
    check("CSV delimiter + newline preserved",
          "\r\n" in out_pre["native_output"]["text"]
          and out_pre["native_shape_contract"]["delimiter"] == ",")

    # ── NEGATIVE CONTROL: a projection that DROPPED a key must be detected as a schema mismatch ──
    lossy = json.loads(raw_json.decode())
    del lossy["active"]                       # simulate a lossy export that drops a key
    lossy_shape = _json_shape(json.dumps(lossy))
    check("NEGATIVE: a dropped-key output is detected as a schema MISMATCH (check has teeth)",
          lossy_shape != in_shape, "dropped 'active' but shapes compared equal — check is blind")

    # ── every declared OUTPUT_MODE is exportable without error (mode vocabulary coverage) ──
    ctx = {"schema_version": "ContextResponse", "response_id": "ctxresp-demo"}
    for mode in OUTPUT_MODES:
        vc = changes if mode in ("schema_preserving", "schema_preserving_with_sidecar", "compare") else None
        r = svc.export(raw_json, output_mode=mode, verified_changes=vc, context_response=ctx, now=_NOW)
        check(f"output_mode '{mode}' exports without error", "native_output" in r and "receipt" in r)
    # dual + baltor_native surface the advanced ContextResponse
    dual = svc.export(raw_json, output_mode="dual", context_response=ctx, now=_NOW)
    check("dual surfaces both native_output AND context_response",
          dual["native_output"]["byte_identical_to_source"] and dual["context_response"] == ctx)

    print(f"\n{'PASS — check_native_export_same_schema: schema_preserving output schema == input schema for JSON (keys+nesting) and CSV (columns/order/delimiter/newline) across modes; every output_mode exports; negative dropped-key control fails as expected.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: native export same schema (JSON + CSV).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
