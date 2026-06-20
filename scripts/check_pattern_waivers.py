#!/usr/bin/env python3
"""scripts.check_pattern_waivers — proof: architecture/pattern_waivers.json is well-formed and honest.
Every waiver carries owner + replacement_plan + proof_that_safe + expires_by_pass; every waiver's
pattern_id is one of the canonical 25; every waiver's file_path points at a real file (a waiver for a
file that no longer exists is stale debt); and — the forcing function — a waiver whose status=="expired"
FAILS the proof, as does an "active" waiver whose current_pass has moved past expires_by_pass. A negative
fixture in a temp dir proves an expired waiver is actually rejected.

CLI: python3 scripts/check_pattern_waivers.py --self-test
"""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_WAIVERS = _REPO / "architecture" / "pattern_waivers.json"

CANONICAL_PATTERN_IDS = {
    "source_adapter_pattern", "parser_provider_pattern", "ingestion_sync_pattern", "source_artifact_pattern",
    "durable_command_pattern", "worker_claim_loop_pattern", "processor_harness_pattern",
    "artifact_envelope_pattern", "provider_adapter_pattern", "api_projection_route_pattern",
    "ui_projection_page_pattern", "proof_script_pattern", "documentation_page_pattern",
    "contract_schema_pattern", "capability_catalog_entry_pattern", "optimization_candidate_pattern",
    "reconciliation_decision_pattern", "held_out_warning_pattern", "watchtower_verification_task_pattern",
    "tenant_isolation_pattern", "structured_logging_pattern", "review_pack_pattern",
    "section_maturity_entry_pattern", "dependency_emulator_pattern", "multi_source_fixture_pattern",
}
_REQUIRED_KEYS = ("waiver_id", "pattern_id", "file_path", "reason", "owner",
                  "expires_by_pass", "replacement_plan", "proof_that_safe", "status")
_STATUS_ENUM = {"active", "expired", "closed"}


def _waiver_violations(data: dict) -> list[str]:
    """Return the list of violations in a waivers doc. A waiver is invalid if: it is missing a required key;
    its status is not in the enum; status=='expired'; or status=='active' but current_pass > expires_by_pass."""
    current_pass = data.get("current_pass", 0)
    out: list[str] = []
    for w in data.get("waivers", []):
        wid = w.get("waiver_id", "<no-id>")
        miss = [k for k in _REQUIRED_KEYS if not w.get(k) and w.get(k) != 0]
        if miss:
            out.append(f"{wid}:missing {miss}")
        if w.get("status") not in _STATUS_ENUM:
            out.append(f"{wid}:bad-status {w.get('status')}")
        if w.get("pattern_id") not in CANONICAL_PATTERN_IDS:
            out.append(f"{wid}:bad-pattern {w.get('pattern_id')}")
        if w.get("status") == "expired":
            out.append(f"{wid}:EXPIRED (debt must be paid)")
        if w.get("status") == "active" and isinstance(w.get("expires_by_pass"), int) and current_pass > w["expires_by_pass"]:
            out.append(f"{wid}:active-but-past-expiry (pass {current_pass} > {w['expires_by_pass']})")
    return out


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    data = json.loads(_WAIVERS.read_text(encoding="utf-8"))
    check("pattern_waivers.json parses + has version/waivers/current_pass",
          all(k in data for k in ("version", "waivers", "current_pass")))

    # 1) current repo waivers are all valid (no expired / no past-expiry / all keys present)
    violations = _waiver_violations(data)
    check("every current waiver is valid (keys present, canonical pattern, not expired, not past expiry)",
          violations == [], str(violations))

    # 2) every waiver's file_path points at a real file (stale debt is a failure)
    missing_paths = [w.get("waiver_id") for w in data.get("waivers", [])
                     if w.get("file_path") and not (_REPO / w["file_path"]).exists()]
    check("every waiver file_path points at a file that exists", missing_paths == [], str(missing_paths))

    # 3) NEGATIVE TEST: an expired waiver MUST be rejected (the forcing function bites).
    tmp = Path(tempfile.mkdtemp(prefix="waiver_neg_"))
    try:
        expired_doc = {
            "version": "1.0", "current_pass": 5,
            "waivers": [{
                "waiver_id": "WVR-NEG-expired", "pattern_id": "documentation_page_pattern",
                "file_path": "scripts/context_workers/common.py", "reason": "synthetic",
                "owner": "test", "expires_by_pass": 2, "replacement_plan": "x",
                "proof_that_safe": "y", "status": "expired",
            }],
        }
        (tmp / "w.json").write_text(json.dumps(expired_doc), encoding="utf-8")
        neg = _waiver_violations(expired_doc)
        check("negative test: an EXPIRED waiver is rejected", neg != [], "expired waiver was not flagged")

        past_doc = dict(expired_doc)
        past_doc["waivers"] = [dict(expired_doc["waivers"][0], status="active", expires_by_pass=2)]
        neg2 = _waiver_violations(past_doc)
        check("negative test: an ACTIVE waiver past its expires_by_pass is rejected", neg2 != [])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"\n{'PASS — check_pattern_waivers: every waiver is owned, justified, time-boxed, and points at a real file; expired / past-expiry waivers fail (debt gets paid).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: pattern waivers are owned, time-boxed, and not expired.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
