#!/usr/bin/env python3
"""scripts.check_native_format_full_stack — the END-TO-END proof (C-NATIVE-1) for Native Format Preservation.

This is the synthesis proof: it drives the REAL Lane B runtime (NativeExportService -> NativeFormatPreserver +
NativeProjectionBuilder + SidecarWriter) and the REAL Lane C API handler (scripts/api_native_handler) across
JSON + CSV + Markdown for the key output modes, and asserts the whole feature contract holds together:

  ORIG_PRESERVED   the ORIGINAL source bytes/sha256 survive every mode; rollback recovers them byte-for-byte
                   and every receipt records original_overwritten == False (the lossless-distillation law).
  SAME_SCHEMA      schema_preserving keeps the customer's exact shape — JSON keys+nesting, CSV columns+order+
                   delimiter+newline — changing ONLY a VERIFIED value, each backed by a NativeDiff entry.
  SIDECAR          a *_with_sidecar mode carries the governance power off to the side: field_facts (with source
                   handles), held_out_claims, conflicts, reconciliations, verification_receipts, warnings,
                   field_map, source_hash — without touching the native output's shape.
  HELD_OUT_KEPT    a claim omitted from the native answer is HELD OUT in the sidecar, never erased, and its
                   value never leaks into the served native output (omitted != deleted).
  NO_TRUTH_BYPASS  an UNVERIFIED value change is refused at the runtime (lossless law) AND held out at the API
                   (defense-in-depth); a non-mutating mode can never smuggle in a value change.
  REHYDRATE        given a native export + sidecar, a consumer reaches the ORIGINAL source bytes/hash via the
                   shared source_hash (export/sidecar/diff all pivot back); the on-disk original is unchanged.

It prints one row per (FORMAT, MODE) plus the cross-cutting NO_TRUTH_BYPASS / REHYDRATE checks driven through
the real API, then a summary table:
  FORMAT | MODE | ORIG_PRESERVED | SAME_SCHEMA | SIDECAR | HELD_OUT_KEPT | NO_TRUTH_BYPASS | REHYDRATE | STATUS

Deterministic + offline + stdlib only: ids content-addressed; injected ``now``; no RNG, no network, no
secrets; a tempfile.mkdtemp models the "original on disk is never overwritten" guarantee and is cleaned up.

CLI: python3 scripts/check_native_format_full_stack.py --self-test
"""
from __future__ import annotations

import argparse
import csv as _csv
import hashlib
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.native import NativeExportService, SidecarWriter  # noqa: E402
from src.baltor.native.native_format_preserver import NativeFormatPreserver  # noqa: E402
from scripts.api_native_handler import (  # noqa: E402
    _enforce_no_truth_bypass, _modes, _reset_sources_for_test, handle)

#: injected wall-clock — deterministic, offline (matches the sibling native proofs + the API handler).
_NOW = "2026-06-05T00:00:00Z"
_PRESERVER = NativeFormatPreserver()

#: the deadline the source documents themselves carry (the value the unverified change would try to keep).
_SOURCE_VALUE = "30 days"
#: a held-out claim whose value appears in NO source text, so "held-out never served" is a clean substring
#: test across every mode (a lower-authority FAQ figure that lost reconciliation to the verified Reg-E fact).
_HELD_OUT_VALUE = "45 calendar days"
#: the verified Reg-E deadline that DOES get applied in a mutating mode (each backed by a receipt + diff).
_VERIFIED_VALUE = "10 business days"


# --------------------------------------------------------------------------------------------------------- #
# shape helpers (value-independent schema fingerprints)                                                      #
# --------------------------------------------------------------------------------------------------------- #
def _json_shape(text: str) -> list:
    """Leaf JSON-pointer field order — the JSON schema-shape (keys + nesting), value-independent."""
    return _PRESERVER._json_contract(json.loads(text), text.encode(), "", "").field_order


def _csv_shape(text: str) -> dict:
    rows = list(_csv.reader(io.StringIO(text)))
    return {"columns": rows[0] if rows else [], "row_count": max(0, len(rows) - 1)}


# --------------------------------------------------------------------------------------------------------- #
# governed-context fixtures shared across formats (one verified change + one held-out claim)                 #
# --------------------------------------------------------------------------------------------------------- #
def _governed(native_path: str) -> dict:
    """The verified fact + held-out claim + field map + receipts used for any *_with_sidecar export, keyed by
    the native path of the field being governed (JSON-pointer for JSON, row.col for CSV, anchor for Markdown)."""
    fact = {"artifact_id": "fact-rege-10", "source_handle": "ctx://cfpb/reg-e/1005.11#deadline",
            "claim_status": "fact", "object": _VERIFIED_VALUE, "content_hash": "h-rege-10"}
    held = {"artifact_id": "faq-30", "claim_status": "fact", "source_handle": "ctx://cfpb/faq#deadline",
            "object": _HELD_OUT_VALUE}
    return {
        "field_facts": [SidecarWriter.field_fact(native_path, artifact=fact, receipt_id="vr-fs-1")],
        "held_out_claims": [SidecarWriter.held_out(held, reason="lower-authority FAQ superseded by Reg E")],
        "field_map": [SidecarWriter.map_row(native_path, source_handle=fact["source_handle"],
                                            artifact_id=fact["artifact_id"], claim_status="fact")],
        "conflicts": [{"conflict_type": "deadline_mismatch", "winner": "fact-rege-10", "held_out": "faq-30"}],
        "reconciliations": [{"decision": "resolved_by_authority", "winning_artifact_id": "fact-rege-10"}],
        "verification_receipts": [{"receipt_id": "vr-fs-1", "artifact_id": "fact-rege-10", "decision": "allow"}],
        "warnings": [{"native_path": native_path, "reason": "value corrected from source; see diff + receipt"}],
    }


# --------------------------------------------------------------------------------------------------------- #
# per-format drivers — each returns (rows, fails); a row is the per-mode summary cell dict                   #
# --------------------------------------------------------------------------------------------------------- #
def _drive_format(svc: NativeExportService, fmt: str, raw: bytes, hint: str, native_path: str,
                  verified_changes: list, shape_fn, check) -> list[dict]:
    """Run the key output modes for one format through the REAL runtime and assert the cross-cutting
    invariants. Returns a list of summary-row dicts (one per mode)."""
    src_hash = hashlib.sha256(raw).hexdigest()
    # the schema fingerprint is only meaningful for the structured formats; markdown is compared by bytes/prefix.
    in_shape = shape_fn(raw.decode("utf-8")) if fmt in ("json", "csv") else None
    contract = svc._preserver.preserve(raw, hint=hint)
    rows: list[dict] = []

    # the matrix of modes we exercise per format (passthrough, schema_preserving, +sidecar, compare, annotated).
    modes = ["native_passthrough", "native_passthrough_with_sidecar", "schema_preserving",
             "schema_preserving_with_sidecar", "compare"]
    if fmt == "markdown":
        modes.append("annotated_native")        # markdown's add-without-removing path

    for mode in modes:
        mutating = mode in ("schema_preserving", "schema_preserving_with_sidecar", "compare")
        with_sidecar = mode.endswith("_with_sidecar") or mode in ("compare",)
        gov = _governed(native_path) if (with_sidecar or mode == "annotated_native") else {}
        out = svc.export(raw, output_mode=mode, hint=hint,
                         verified_changes=(verified_changes if mutating else None),
                         now=_NOW, **gov)
        no = out["native_output"]
        tag = f"{fmt}/{mode}"

        # ── ORIG_PRESERVED: rollback recovers the EXACT original bytes; receipt records no overwrite. ──
        rollback_ok = (svc.rehydrate_original(contract) == raw
                       and out["rollback"]["source_hash"] == src_hash
                       and out["receipt"]["original_overwritten"] is False
                       and out["native_shape_contract"]["source_hash"] == src_hash)
        check(f"[{tag}] ORIGINAL preserved (rollback==raw, original_overwritten False)", rollback_ok)

        # ── SAME_SCHEMA: for non-markdown, the projected output's schema fingerprint equals the input's. ──
        same_schema = "n/a"
        if fmt in ("json", "csv"):
            out_shape = shape_fn(no["text"])
            ok_schema = (out_shape == in_shape)
            check(f"[{tag}] output schema == input schema", ok_schema, f"in={in_shape} out={out_shape}")
            same_schema = ok_schema
        else:
            # markdown: passthrough/sidecar keep the note byte-for-byte; annotated keeps it as a prefix.
            if mode == "annotated_native":
                ok_md = no["text"].startswith(raw.decode("utf-8")) and no["annotations_added"] == 1
                check(f"[{tag}] annotated note retains 100% of the original as a prefix", ok_md)
            else:
                ok_md = no["text"].encode("utf-8") == raw and no["byte_identical_to_source"]
                check(f"[{tag}] markdown note returned byte-for-byte unchanged", ok_md)
            same_schema = ok_md

        # passthrough family must be byte-identical; mutating family must NOT claim byte-identical.
        if mode in ("native_passthrough", "native_passthrough_with_sidecar"):
            check(f"[{tag}] passthrough is byte-identical to source", no["byte_identical_to_source"])

        # ── SAME_SCHEMA value change: for the STRUCTURED formats, a mutating mode applies EXACTLY the verified
        #    value into the same shape, recorded as a NativeDiff with a receipt. Markdown is deliberately
        #    different: its note text is NEVER silently edited — the verified fact rides in the sidecar's
        #    field_facts (asserted by the SIDECAR check), so a markdown mutating mode applies no diff. ──
        if mutating and fmt in ("json", "csv"):
            cf = out["diff"]["changed_fields"]
            ok_diff = (len(cf) == 1 and cf[0]["new"] == _VERIFIED_VALUE
                       and cf[0].get("receipt_id") and cf[0]["path"] == native_path)
            check(f"[{tag}] exactly one VERIFIED change, recorded as a NativeDiff with a receipt", ok_diff, str(cf))
            check(f"[{tag}] the verified value IS present in the native output", _VERIFIED_VALUE in no["text"])
        elif mutating and fmt == "markdown":
            check(f"[{tag}] markdown note is NOT silently edited (verified fact rides in the sidecar)",
                  no["text"].encode("utf-8") == raw and out["diff"]["changed_fields"] == [])

        # ── SIDECAR + HELD_OUT_KEPT: the *_with_sidecar / compare modes carry governance + hold-out. ──
        sidecar_ok = "n/a"
        held_out_ok = "n/a"
        sc = out.get("sidecar")
        if with_sidecar:
            required = ("field_facts", "held_out_claims", "conflicts", "reconciliations",
                        "verification_receipts", "warnings", "field_map", "source_hash", "artifact_ids")
            sidecar_ok = bool(sc) and all(k in sc for k in required) and sc["source_hash"] == src_hash
            check(f"[{tag}] sidecar carries facts/held-out/conflicts/receipts/lineage + source_hash", sidecar_ok)
            check(f"[{tag}] sidecar field_facts carry a source handle",
                  bool(sc) and len(sc["field_facts"]) == 1
                  and sc["field_facts"][0]["source_handle"] == "ctx://cfpb/reg-e/1005.11#deadline")
            # held-out is preserved AND never leaks into the served native output.
            held_present = bool(sc) and len(sc["held_out_claims"]) == 1 and sc["held_out_claims"][0]["artifact_id"] == "faq-30"
            held_leaked = _HELD_OUT_VALUE in no["text"]
            held_out_ok = held_present and not held_leaked
            check(f"[{tag}] held-out claim preserved in sidecar AND not served in native output", held_out_ok,
                  f"present={held_present} leaked={held_leaked}")
        else:
            check(f"[{tag}] non-sidecar mode emits no sidecar", sc is None)

        rows.append({"format": fmt, "mode": mode, "orig": rollback_ok, "schema": same_schema,
                     "sidecar": sidecar_ok, "held_out": held_out_ok, "no_bypass": "n/a", "rehydrate": "n/a"})

    # ── NO_TRUTH_BYPASS at the RUNTIME: an unverified change (no receipt) is REFUSED, never silently applied. ──
    refused = False
    try:
        svc.export(raw, output_mode="schema_preserving", hint=hint,
                   verified_changes=[{"path": native_path, "new_value": _HELD_OUT_VALUE}], now=_NOW)
    except ValueError:
        refused = True
    check(f"[{fmt}] runtime REFUSES an unverified value change (no receipt) — lossless law", refused)
    for r in rows:
        r["no_bypass"] = refused if r["mode"] in ("schema_preserving", "schema_preserving_with_sidecar",
                                                  "compare") else "n/a"
    return rows


# --------------------------------------------------------------------------------------------------------- #
# API-driven cross-cutting checks: no-truth-bypass (defense-in-depth) + rehydration to the original          #
# --------------------------------------------------------------------------------------------------------- #
def _drive_api(tmp: Path, check) -> bool:
    """Drive the REAL API handler end-to-end: ingest stores the exact bytes (no truth mutation, no fact
    served); export/sidecar/diff all pivot back to the SAME source_hash; the on-disk original is never
    overwritten; and the API's defense-in-depth holds out an unverified differing field. Returns rehydrate_ok."""
    _reset_sources_for_test()
    original = {"complaint_id": "BILL-782", "deadline": _HELD_OUT_VALUE, "product": "Credit card"}
    original_bytes = json.dumps(original, sort_keys=True, separators=(",", ":")).encode("utf-8")
    expected_hash = hashlib.sha256(original_bytes).hexdigest()
    src_file = tmp / "original.json"
    src_file.write_bytes(original_bytes)

    # 1) INGEST stores the source; writes no canonical truth; serves no fact.
    code, ing = handle("POST", "/api/native/ingest", {"tenant_id": "demo", "content": original, "format": "json"})
    check("[api] ingest 200; no canonical truth; no fact served",
          code == 200 and ing.get("mutated_canonical_truth") is False and ing.get("served_fact") is False)
    source_id = ing.get("source_id")
    check("[api] stored source_hash == sha256(original bytes) (rehydrate to exact bytes)",
          ing.get("source_hash") == expected_hash)
    check("[api] the on-disk original is unchanged after ingest (never overwritten)",
          src_file.read_bytes() == original_bytes)

    # 2) export / sidecar / diff all carry the SAME source_hash -> pivot back to the original.
    c_e, exp = handle("GET", f"/api/native/export/{source_id}", {"mode": "schema_preserving_with_sidecar"})
    c_s, side = handle("GET", f"/api/native/sidecar/{source_id}", {})
    c_d, dif = handle("GET", f"/api/native/diff/{source_id}", {})
    rehydrate_ok = (c_e == 200 and c_s == 200 and c_d == 200
                    and exp.get("source_hash") == expected_hash
                    and side.get("source_hash") == expected_hash
                    and dif.get("source_hash") == expected_hash)
    check("[api] export/sidecar/diff all pivot back to the source_hash (rehydrate)", rehydrate_ok)
    check("[api] export does not leak raw bytes", "raw_bytes" not in json.dumps(exp))

    # 3) deterministic / idempotent ingest; original still untouched.
    _, ing2 = handle("POST", "/api/native/ingest", {"tenant_id": "demo", "content": original, "format": "json"})
    check("[api] re-ingest is content-addressed to the SAME source_id; original still unchanged",
          ing2.get("source_id") == source_id and src_file.read_bytes() == original_bytes)

    # 4) NO_TRUTH_BYPASS defense-in-depth: an unverified differing field is held out, never served as fact.
    modes = _modes()
    attack = {"native_output": {"deadline": _VERIFIED_VALUE}, "diff": {"changed_fields": []},
              "native_field_status": [{"path": "/deadline", "differs_from_source": True, "claim_status": "candidate"}]}
    enforced = _enforce_no_truth_bypass(attack, modes.get("schema_preserving", {}))
    f = next((x for x in enforced["native_field_status"] if x["path"] == "/deadline"), {})
    check("[api] unverified differing field is held out (never served as fact)",
          f.get("differs_from_source") is False and f.get("held_out") is True)
    smuggle = {"native_output": {}, "diff": {"changed_fields": [{"path": "/x", "old": "a", "new": "b"}]},
               "native_field_status": []}
    suppressed = _enforce_no_truth_bypass(smuggle, modes.get("native_passthrough", {}))
    check("[api] non-mutating mode suppresses a smuggled diff",
          suppressed.get("diff", {}).get("changed_fields") == [])

    _reset_sources_for_test()
    return rehydrate_ok


# --------------------------------------------------------------------------------------------------------- #
def _fmt_cell(v) -> str:
    if v is True:
        return "ok"
    if v is False:
        return "FAIL"
    return str(v)


def _print_table(rows: list[dict], rehydrate_ok: bool) -> None:
    hdr = ["FORMAT", "MODE", "ORIG_PRESERVED", "SAME_SCHEMA", "SIDECAR", "HELD_OUT_KEPT",
           "NO_TRUTH_BYPASS", "REHYDRATE", "STATUS"]
    table = [hdr]
    for r in rows:
        cells = [r["format"], r["mode"], _fmt_cell(r["orig"]), _fmt_cell(r["schema"]),
                 _fmt_cell(r["sidecar"]), _fmt_cell(r["held_out"]), _fmt_cell(r["no_bypass"]),
                 _fmt_cell(rehydrate_ok)]
        # STATUS = PASS unless any concrete (non-"n/a") cell is FAIL.
        bad = any(c == "FAIL" for c in cells)
        cells.append("FAIL" if bad else "PASS")
        table.append(cells)
    widths = [max(len(row[i]) for row in table) for i in range(len(hdr))]
    print()
    for i, row in enumerate(table):
        print("  " + " | ".join(c.ljust(widths[j]) for j, c in enumerate(row)))
        if i == 0:
            print("  " + "-+-".join("-" * w for w in widths))


def _self_test() -> int:
    fails: list[str] = []
    tmp = Path(tempfile.mkdtemp(prefix="native_full_stack_"))
    try:
        def check(name: str, ok: bool, detail: str = "") -> None:
            print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
            if not ok:
                fails.append(name)

        svc = NativeExportService()
        rows: list[dict] = []

        # ── JSON ── nested object; verified change at a deep JSON-pointer.
        raw_json = ('{"company": "Acme Bank", "policy": {"deadline": "30 days", "tiers": [1, 2, 3]}, '
                    '"note": "billing error"}').encode("utf-8")
        rows += _drive_format(
            svc, "json", raw_json, "json", "/policy/deadline",
            [{"path": "/policy/deadline", "new_value": _VERIFIED_VALUE,
              "decision": "verified_update", "receipt_id": "vr-fs-1"}], _json_shape, check)

        # ── CSV ── CRLF + columns/order; verified change addressed by (row, column).
        raw_csv = ("company,deadline,note\r\nAcme Bank,30 days,ok\r\nBeta Corp,5 days,fine\r\n").encode("utf-8")
        rows += _drive_format(
            svc, "csv", raw_csv, "csv", "row.0.col.deadline",
            [{"path": "row.0.col.deadline", "new_value": _VERIFIED_VALUE,
              "decision": "verified_update", "receipt_id": "vr-fs-1"}], _csv_shape, check)

        # ── Markdown ── default unchanged + sidecar; annotated adds without removing. (No value changes —
        #    markdown's governance rides in the sidecar; the note text is never silently edited.)
        raw_md = ("# Billing Error Policy\n\nWe resolve billing errors within 30 days.\n\n"
                  "- Contact support\n- Provide your account number\n").encode("utf-8")
        rows += _drive_format(svc, "markdown", raw_md, "markdown", "#billing-error-policy", [], None, check)

        # ── cross-cutting API checks (no-truth-bypass defense-in-depth + rehydration to the original) ──
        rehydrate_ok = _drive_api(tmp, check)
        for r in rows:
            r["rehydrate"] = rehydrate_ok

        # ── determinism: re-running an export yields identical output + receipt ids ──
        d1 = svc.export(raw_json, output_mode="schema_preserving", hint="json",
                        verified_changes=[{"path": "/policy/deadline", "new_value": _VERIFIED_VALUE,
                                           "decision": "verified_update", "receipt_id": "vr-fs-1"}], now=_NOW)
        d2 = svc.export(raw_json, output_mode="schema_preserving", hint="json",
                        verified_changes=[{"path": "/policy/deadline", "new_value": _VERIFIED_VALUE,
                                           "decision": "verified_update", "receipt_id": "vr-fs-1"}], now=_NOW)
        check("deterministic: identical export -> identical output hash + receipt id",
              d1["native_output"]["bytes_sha256"] == d2["native_output"]["bytes_sha256"]
              and d1["receipt"]["receipt_id"] == d2["receipt"]["receipt_id"])

        _print_table(rows, rehydrate_ok)

        msg = ("PASS — check_native_format_full_stack: across JSON + CSV + Markdown and every key output mode, "
               "the ORIGINAL is preserved (rollback==raw, never overwritten); schema_preserving keeps the exact "
               "schema and changes only a VERIFIED value (each a NativeDiff + receipt); the sidecar carries "
               "facts/held-out/conflicts/receipts/lineage; held-out is kept and never served; an unverified "
               "change is refused at the runtime and held out at the API; and an export rehydrates to the "
               "original via source_hash. Deterministic + offline.")
        print(f"\n{msg if not fails else f'{len(fails)} FAILURES: {fails}'}")
        return 0 if not fails else 1
    finally:
        _reset_sources_for_test()
        shutil.rmtree(tmp, ignore_errors=True)


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="End-to-end proof: Native Format Preservation full stack "
                                            "(runtime + API; JSON/CSV/Markdown across modes).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
