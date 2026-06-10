#!/usr/bin/env python3
"""scripts.check_native_export_no_truth_bypass — proof (C-NATIVE-1, NEGATIVELY TESTED): a native export NEVER
serves an unverified value as a confirmed fact, and held-out claims stay in the sidecar (never silently applied).

This is the governance heart of native preservation. We feed the handler's defense-in-depth enforcement
(`api_native_handler._enforce_no_truth_bypass`) and the registry-level rule a set of ADVERSARIAL export
payloads and assert each one is caught:
  - a non-mutating mode (e.g. native_passthrough) that nonetheless claims a diff -> diff suppressed;
  - a native field whose value DIFFERS from source but carries a non-servable claim_status
    (candidate/unverified/held_out/...) -> downgraded out of the served output, flagged held_out;
  - a native field whose value differs from source but has NO matching NativeDiff entry -> held out (no silent
    change). And the positive control: a properly VERIFIED + diffed change in a mutating mode is allowed.

Also checks the registry rule that ONLY schema_preserving / schema_preserving_with_sidecar / compare may
mutate values, so no other mode can be (mis)configured to apply a value change at all.

Deterministic + offline. CLI: python3 scripts/check_native_export_no_truth_bypass.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.api_native_handler import _enforce_no_truth_bypass

_REPO = Path(__file__).resolve().parents[1]
_MODES_FILE = _REPO / "architecture" / "native_output_modes.json"


def _modes() -> dict:
    data = json.loads(_MODES_FILE.read_text(encoding="utf-8"))
    return {m["id"]: m for m in data["output_modes"]}


def _self_test() -> int:
    fails: list[str] = []
    modes = _modes()

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # ── ADVERSARIAL 1: a non-mutating mode that smuggles in a diff -> diff must be suppressed ──
    attack1 = {"native_output": {"deadline": "10 days"},
               "diff": {"changed_fields": [{"path": "/deadline", "old": "30", "new": "10"}]},
               "native_field_status": []}
    out1 = _enforce_no_truth_bypass(attack1, modes["native_passthrough"])
    check("non-mutating mode: smuggled diff is suppressed",
          out1.get("diff", {}).get("changed_fields") == [])
    check("non-mutating mode: a warning records the suppression",
          any("does not mutate values" in str(w) for w in out1.get("warnings", [])))

    # ── ADVERSARIAL 2: a field differs from source but carries a non-servable claim_status -> held out ──
    attack2 = {"native_output": {"deadline": "10 days"}, "diff": {"changed_fields": []},
               "native_field_status": [{"path": "/deadline", "differs_from_source": True,
                                        "claim_status": "candidate"}]}
    out2 = _enforce_no_truth_bypass(attack2, modes["schema_preserving"])
    f2 = next(f for f in out2["native_field_status"] if f["path"] == "/deadline")
    check("unverified (candidate) differing field is NOT served as differing", f2.get("differs_from_source") is False)
    check("unverified differing field is flagged held_out", f2.get("held_out") is True)
    check("unverified differing field records a warning", any("not VERIFIED" in str(w) for w in out2.get("warnings", [])))

    # ── ADVERSARIAL 3: a field differs from source but has NO NativeDiff entry -> held out (no silent change) ──
    attack3 = {"native_output": {"deadline": "10 days"}, "diff": {"changed_fields": []},
               "native_field_status": [{"path": "/deadline", "differs_from_source": True, "claim_status": "fact"}]}
    out3 = _enforce_no_truth_bypass(attack3, modes["schema_preserving"])
    f3 = next(f for f in out3["native_field_status"] if f["path"] == "/deadline")
    check("differing field with no diff entry is held out (no silent apply)",
          f3.get("differs_from_source") is False and f3.get("held_out") is True)

    # ── POSITIVE CONTROL: a properly VERIFIED + diffed change in a mutating mode is allowed through ──
    good = {"native_output": {"deadline": "10 business days"},
            "diff": {"changed_fields": [{"path": "/deadline", "old": "30 days", "new": "10 business days",
                                         "decision": "resolved_by_authority", "receipt_id": "vr-abc"}]},
            "native_field_status": [{"path": "/deadline", "differs_from_source": True, "claim_status": "fact"}]}
    outg = _enforce_no_truth_bypass(good, modes["schema_preserving"])
    fg = next(f for f in outg["native_field_status"] if f["path"] == "/deadline")
    check("VERIFIED + diffed change in a mutating mode is allowed", fg.get("differs_from_source") is True
          and not fg.get("held_out"))
    check("allowed change keeps its NativeDiff entry", len(outg.get("diff", {}).get("changed_fields", [])) == 1)
    check("allowed change adds no spurious held-out warning",
          not any("not VERIFIED" in str(w) or "held out" in str(w) for w in outg.get("warnings", [])))

    # ── REGISTRY RULE: only the three value-changing modes may mutate values at all ──
    mutating = {mid for mid, m in modes.items() if m.get("mutates_values")}
    check("only schema_preserving/_with_sidecar/compare may mutate values",
          mutating == {"schema_preserving", "schema_preserving_with_sidecar", "compare"}, str(sorted(mutating)))
    check("passthrough modes can never mutate values",
          not modes["native_passthrough"]["mutates_values"]
          and not modes["native_passthrough_with_sidecar"]["mutates_values"])
    check("annotated_native/baltor_native/dual never mutate values",
          not any(modes[m]["mutates_values"] for m in ("annotated_native", "baltor_native", "dual")))

    # ── garbage in -> no crash, marked unavailable ──
    out_bad = _enforce_no_truth_bypass("not a dict", modes["compare"])
    check("non-dict payload degrades safely (no crash)", out_bad.get("available") is False)

    msg = ("PASS — check_native_export_no_truth_bypass: smuggled diffs are suppressed in non-mutating modes; "
           "unverified/undiffed differing fields are held out (never served as fact); only the three mutating "
           "modes may change a value; a properly verified+diffed change is allowed.")
    print(f"\n{msg if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof (negative): native export never serves an unverified value.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
