#!/usr/bin/env python3
"""scripts.check_native_markdown_sidecar — proof (C-NATIVE-1): Markdown default = original UNCHANGED + sidecar.

Asserts, deterministically + offline:
  - default Markdown mode (native_passthrough_with_sidecar) returns the note BYTE-FOR-BYTE unchanged — strict
    preservation never edits the note; the governance rides entirely in the sidecar (.baltor/<name>.baltor.json);
  - the sidecar carries verified field_facts (with source handles), the HELD-OUT claims (omitted != deleted),
    and the verification receipts;
  - the optional annotated_native mode ADDS an annotation block while RETAINING 100% of the original content
    above it (no content is lost or edited);
  - the original is never overwritten; rollback recovers the exact note bytes.

CLI: python3 _repos/shared-backend-components/scripts/check_native_markdown_sidecar.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
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
    note = ("# Billing Error Policy\n\n"
            "We resolve billing errors within 30 days.\n\n"
            "- Contact support\n- Provide your account number\n")
    raw = note.encode("utf-8")
    src_hash = hashlib.sha256(raw).hexdigest()

    fact = {"artifact_id": "fact-rege-10", "source_handle": "ctx://cfpb/reg-e/1005.11#deadline",
            "claim_status": "fact", "object": "10 business days", "content_hash": "h-rege-10"}
    held = {"artifact_id": "faq-30", "claim_status": "fact", "source_handle": "ctx://cfpb/faq#deadline",
            "object": "30 days"}

    # 1) DEFAULT markdown mode: original byte-for-byte unchanged + sidecar
    d = svc.export(raw, output_mode="native_passthrough_with_sidecar", hint="markdown",
                   field_facts=[SidecarWriter.field_fact("#billing-error-policy", artifact=fact, receipt_id="vr-md-1")],
                   held_out_claims=[SidecarWriter.held_out(held, reason="lower-authority FAQ superseded by Reg E")],
                   field_map=[SidecarWriter.map_row("#billing-error-policy", source_handle=fact["source_handle"],
                                                    artifact_id=fact["artifact_id"], claim_status="fact")],
                   verification_receipts=[{"receipt_id": "vr-md-1", "decision": "allow"}],
                   warnings=["served fact (10 business days) differs from the note text (30 days) — see field_facts"],
                   now=_NOW)
    check("default markdown returns the note BYTE-FOR-BYTE unchanged",
          d["native_output"]["text"].encode("utf-8") == raw and d["native_output"]["byte_identical_to_source"])
    check("default markdown adds NO annotations to the note", d["native_output"]["annotations_added"] == 0)

    sc = d["sidecar"]
    check("sidecar carries verified field_facts with a source handle",
          len(sc["field_facts"]) == 1 and sc["field_facts"][0]["source_handle"] == fact["source_handle"]
          and sc["field_facts"][0]["object"] == "10 business days")
    check("sidecar carries held-out claims (omitted != deleted)",
          len(sc["held_out_claims"]) == 1 and sc["held_out_claims"][0]["artifact_id"] == "faq-30")
    check("sidecar carries verification receipts", len(sc["verification_receipts"]) == 1)
    check("sidecar carries warnings (note text vs verified fact)", len(sc["warnings"]) == 1)
    check("sidecar source_hash links back to the note for rehydration", sc["source_hash"] == src_hash)

    # 2) annotated mode: adds without losing any original content
    a = svc.export(raw, output_mode="annotated_native", hint="markdown", now=_NOW)
    txt = a["native_output"]["text"]
    check("annotated_native RETAINS 100% of the original note (as a prefix)", txt.startswith(note), txt[:60])
    check("annotated_native added an annotation block", a["native_output"]["annotations_added"] == 1
          and "baltor:native-annotations" in txt and src_hash in txt)
    check("annotated_native did NOT delete or edit any original line",
          all(line in txt for line in note.splitlines() if line))

    # 3) original never overwritten; rollback recovers exact bytes
    contract = svc._preserver.preserve(raw, hint="markdown")
    check("rollback recovers the exact original note bytes", svc.rehydrate_original(contract) == raw)
    check("receipt records original_overwritten == False",
          d["receipt"]["original_overwritten"] is False and a["receipt"]["original_overwritten"] is False)

    # determinism
    d2 = svc.export(raw, output_mode="native_passthrough_with_sidecar", hint="markdown",
                    field_facts=[SidecarWriter.field_fact("#billing-error-policy", artifact=fact, receipt_id="vr-md-1")],
                    now=_NOW)
    d3 = svc.export(raw, output_mode="native_passthrough_with_sidecar", hint="markdown",
                    field_facts=[SidecarWriter.field_fact("#billing-error-policy", artifact=fact, receipt_id="vr-md-1")],
                    now=_NOW)
    check("deterministic: identical export -> identical sidecar id + receipt id",
          d2["sidecar"]["sidecar_id"] == d3["sidecar"]["sidecar_id"]
          and d2["receipt"]["receipt_id"] == d3["receipt"]["receipt_id"])

    print(f"\n{'PASS — check_native_markdown_sidecar: default markdown returns the note byte-for-byte unchanged + a governed sidecar (facts/held-out/receipts/warnings); annotated mode adds without losing content; original never overwritten; deterministic.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: native Markdown unchanged + sidecar.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
