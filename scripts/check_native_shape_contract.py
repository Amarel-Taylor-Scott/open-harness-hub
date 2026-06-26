#!/usr/bin/env python3
"""scripts.check_native_shape_contract — proof (C-NATIVE-1, Lane A NATIVE CONTRACTS): the five native
format-preservation contract schemas exist, parse with stdlib-validator keywords only, each ships a valid
example that PASSES and at least one invalid example that FAILS, and the load-bearing governance invariants
hold:

  * NativeDiff — every changed field REQUIRES a receipt_id (a same-schema value may change ONLY when
    verified; NO change is allowed without a receipt — the original is never silently overwritten).
  * NativeExportReceipt — REQUIRES source_hash AND export_hash so an export is reproducible/auditable.
  * SidecarOverlay — REQUIRES held_out_claims AND field_map keys to exist (even when empty) so a reader
    can always distinguish omission (held out, still visible) from erasure (never allowed).

Lossless-distillation framing: the original input is never overwritten — the projection is a view, the
diff records every verified change with a receipt, and the sidecar keeps held-out claims visible. Stdlib-only,
deterministic, offline.

CLI: python3 scripts/check_native_shape_contract.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.runtime.schema_validator import validate as _validate

_REPO = Path(__file__).resolve().parents[1]
_SCHEMA_DIR = _REPO / "schemas" / "native"
_EX_DIR = _SCHEMA_DIR / "examples"

#: every native contract schema this lane owns (filename stem under schemas/native).
_SCHEMAS = ["NativeShapeContract", "NativeProjection", "SidecarOverlay", "NativeDiff", "NativeExportReceipt"]
#: keywords the stdlib schema_validator understands (no others allowed anywhere in a schema node).
_ALLOWED_KEYWORDS = {"type", "required", "properties", "enum", "additionalProperties", "items",
                     "$id", "title", "description"}


def _keys_ok(node) -> bool:
    """Recursively assert a schema node only uses stdlib-validator keywords."""
    if not isinstance(node, dict):
        return True
    for k, v in node.items():
        if k == "properties" and isinstance(v, dict):
            if not all(_keys_ok(sub) for sub in v.values()):
                return False
            continue
        if k == "items" and isinstance(v, dict):
            if not _keys_ok(v):
                return False
            continue
        if k not in _ALLOWED_KEYWORDS:
            return False
    return True


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    schemas: dict[str, dict] = {}
    examples: dict[str, dict] = {}
    for stem in _SCHEMAS:
        sp = _SCHEMA_DIR / f"{stem}.schema.json"
        ep = _EX_DIR / f"{stem}.example.json"
        check(f"{stem} schema file exists", sp.is_file(), str(sp))
        check(f"{stem} example file exists", ep.is_file(), str(ep))
        if sp.is_file():
            schemas[stem] = json.loads(sp.read_text(encoding="utf-8"))
        if ep.is_file():
            examples[stem] = json.loads(ep.read_text(encoding="utf-8"))

    # every schema declares $id native/<Stem>, type object, additionalProperties:false, required + properties,
    # and uses ONLY stdlib-validator keywords (so the proof validator is authoritative for these contracts).
    for stem, sc in schemas.items():
        check(f"{stem} $id is native/{stem}", sc.get("$id") == f"native/{stem}", str(sc.get("$id")))
        check(f"{stem} is an object with additionalProperties:false",
              sc.get("type") == "object" and sc.get("additionalProperties") is False)
        check(f"{stem} declares required + properties", bool(sc.get("required")) and bool(sc.get("properties")))
        check(f"{stem} uses only stdlib-validator keywords", _keys_ok(sc))

    # valid example passes; every invalid example is correctly REJECTED.
    for stem, ex in examples.items():
        sc = schemas[stem]
        valid = ex.get("valid")
        check(f"{stem} has a 'valid' example", valid is not None)
        if valid is not None:
            errs = _validate(valid, sc)
            check(f"{stem} valid example validates clean", errs == [], str(errs[:4]))
        invalids = [(k, v) for k, v in ex.items() if k.startswith("invalid")]
        check(f"{stem} ships at least one invalid example", len(invalids) >= 1)
        for k, v in invalids:
            check(f"{stem} {k} is correctly REJECTED", _validate(v, sc) != [])

    # ---- NativeDiff: every changed field REQUIRES a receipt_id (no verified change without a receipt) ----
    nd = schemas.get("NativeDiff", {})
    cf_items = nd.get("properties", {}).get("changed_fields", {}).get("items", {})
    cf_required = set(cf_items.get("required", []))
    check("NativeDiff changed_fields[].required includes path/old_value/new_value/decision/receipt_id",
          {"path", "old_value", "new_value", "decision", "receipt_id"} <= cf_required,
          str(sorted({"path", "old_value", "new_value", "decision", "receipt_id"} - cf_required)))
    check("NativeDiff REQUIRES receipt_id on a changed field", "receipt_id" in cf_required)
    nd_valid = examples.get("NativeDiff", {}).get("valid", {})
    if nd and nd_valid:
        # a changed field with NO receipt_id must be rejected (the load-bearing rule)
        broken = json.loads(json.dumps(nd_valid))
        broken["changed_fields"][0].pop("receipt_id", None)
        check("NativeDiff rejects a changed field missing receipt_id", _validate(broken, nd) != [])
        # an empty changed_fields array is the normal passthrough case (allowed)
        empty = json.loads(json.dumps(nd_valid)); empty["changed_fields"] = []
        check("NativeDiff allows an empty changed_fields (passthrough = no change)", _validate(empty, nd) == [])

    # ---- NativeExportReceipt: REQUIRES source_hash AND export_hash (reproducible/auditable) ----
    ner = schemas.get("NativeExportReceipt", {})
    ner_req = set(ner.get("required", []))
    check("NativeExportReceipt requires source_hash AND export_hash",
          {"source_hash", "export_hash"} <= ner_req, str(sorted({"source_hash", "export_hash"} - ner_req)))
    ner_valid = examples.get("NativeExportReceipt", {}).get("valid", {})
    if ner and ner_valid:
        for f in ("source_hash", "export_hash"):
            broken = {k: v for k, v in ner_valid.items() if k != f}
            check(f"NativeExportReceipt rejects a receipt missing '{f}'", _validate(broken, ner) != [])

    # ---- SidecarOverlay: held_out_claims AND field_map keys MUST exist (omission != erasure) ----
    so = schemas.get("SidecarOverlay", {})
    so_req = set(so.get("required", []))
    check("SidecarOverlay requires held_out_claims AND field_map keys",
          {"held_out_claims", "field_map"} <= so_req, str(sorted({"held_out_claims", "field_map"} - so_req)))
    so_valid = examples.get("SidecarOverlay", {}).get("valid", {})
    if so and so_valid:
        for f in ("held_out_claims", "field_map"):
            broken = {k: v for k, v in so_valid.items() if k != f}
            check(f"SidecarOverlay rejects a sidecar missing '{f}' key", _validate(broken, so) != [])
        # held_out_claims/field_map MAY be empty arrays — empty means 'none held out', not 'erased'
        empty = json.loads(json.dumps(so_valid)); empty["held_out_claims"] = []; empty["field_map"] = []
        check("SidecarOverlay allows empty held_out_claims/field_map (present-but-empty, not erased)",
              _validate(empty, so) == [])
        # a verified field fact carries source_handle + verification lineage (governance, not just a value)
        ff = so_valid.get("field_facts", [])
        check("SidecarOverlay example field_facts carry source_handle + verification_receipt_id",
              all(f.get("source_handle") and f.get("verification_receipt_id")
                  for f in ff if f.get("claim_status") == "verified") and len(ff) > 0)

    # ---- output_mode is a bounded enum across the projection/diff/receipt contracts (no 'overwrite' mode) ----
    expected_modes = {"native_passthrough", "native_passthrough_with_sidecar", "schema_preserving",
                      "schema_preserving_with_sidecar", "annotated_native", "baltor_native", "dual", "compare"}
    for stem in ("NativeProjection", "NativeDiff", "NativeExportReceipt"):
        sc = schemas.get(stem, {})
        modes = set(sc.get("properties", {}).get("output_mode", {}).get("enum", []))
        check(f"{stem} output_mode enum == the 8 native output modes", modes == expected_modes,
              str(sorted(expected_modes ^ modes)))
        check(f"{stem} output_mode enum has NO destructive 'overwrite' mode",
              not any("overwrite" in m for m in modes))

    print(f"\n{'PASS — check_native_shape_contract: 5 native contract schemas exist + parse (stdlib keywords only); each has a passing valid example and a rejected invalid example; NativeDiff requires receipt_id per changed field; NativeExportReceipt requires source_hash AND export_hash; SidecarOverlay requires held_out_claims + field_map (present, may be empty — omission is never erasure); output_mode is a bounded enum with no overwrite mode.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: native format-preservation contract schemas are complete + governance-enforcing.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
