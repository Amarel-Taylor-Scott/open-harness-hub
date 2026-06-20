#!/usr/bin/env python3
"""scripts.check_native_output_modes — proof (C-NATIVE-1): the native OUTPUT-MODE registry
(architecture/native_output_modes.json) is the canonical, well-formed single source for the 8 output_modes.

Asserts the contract the rest of the native lane relies on:
  - all 8 documented modes are present (native_passthrough, native_passthrough_with_sidecar, schema_preserving,
    schema_preserving_with_sidecar, annotated_native, baltor_native, dual, compare);
  - ONLY the value-changing modes set mutates_values=true: schema_preserving, schema_preserving_with_sidecar,
    compare. Every other mode is mutates_values=false (the original value is never replaced in those modes);
  - native_passthrough (and native_passthrough_with_sidecar) is byte_identical=true; no other mode is;
  - every _with_sidecar / dual / compare / annotated mode sets emits_sidecar=true; the two plain
    passthrough/schema_preserving/baltor_native lanes are explicit about emits_sidecar;
  - each mode is well-formed (id/description/best_for + the three bool flags), with no duplicate ids.

Deterministic + offline: reads only the committed registry file. CLI: python3 scripts/check_native_output_modes.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_MODES_FILE = _REPO / "architecture" / "native_output_modes.json"

#: the 8 modes that MUST exist (matches prompts/baltor-native-format-preservation.md + the lane spec).
_REQUIRED = ("native_passthrough", "native_passthrough_with_sidecar", "schema_preserving",
             "schema_preserving_with_sidecar", "annotated_native", "baltor_native", "dual", "compare")
#: the ONLY modes allowed to set mutates_values=true (same-shape with a VERIFIED value change + NativeDiff).
_MUTATING = frozenset({"schema_preserving", "schema_preserving_with_sidecar", "compare"})
#: the ONLY modes that are byte-for-byte identical to the source bytes.
_BYTE_IDENTICAL = frozenset({"native_passthrough", "native_passthrough_with_sidecar"})
#: modes that MUST emit a SidecarOverlay.
_SIDECAR = frozenset({"native_passthrough_with_sidecar", "schema_preserving_with_sidecar", "annotated_native",
                      "dual", "compare"})


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    check("native_output_modes.json exists", _MODES_FILE.exists())
    if not _MODES_FILE.exists():
        print("1 FAILURES: ['registry file missing']")
        return 1
    data = json.loads(_MODES_FILE.read_text(encoding="utf-8"))
    modes = data.get("output_modes", [])
    by_id = {m.get("id"): m for m in modes if isinstance(m, dict)}

    check("exactly 8 modes defined", len(modes) == 8, str(len(modes)))
    check("no duplicate mode ids", len(by_id) == len(modes), f"{len(by_id)} unique / {len(modes)} rows")
    for mid in _REQUIRED:
        check(f"mode present: {mid}", mid in by_id)
    check("no unexpected modes", set(by_id) <= set(_REQUIRED), str(sorted(set(by_id) - set(_REQUIRED))))

    for mid in _REQUIRED:
        m = by_id.get(mid)
        if not isinstance(m, dict):
            continue
        check(f"{mid}: well-formed (description/best_for + 3 bool flags)",
              bool(m.get("description")) and isinstance(m.get("best_for"), list) and m["best_for"]
              and isinstance(m.get("mutates_values"), bool) and isinstance(m.get("emits_sidecar"), bool)
              and isinstance(m.get("byte_identical"), bool))
        check(f"{mid}: mutates_values == {mid in _MUTATING}", bool(m.get("mutates_values")) == (mid in _MUTATING),
              f"got {m.get('mutates_values')}")
        check(f"{mid}: byte_identical == {mid in _BYTE_IDENTICAL}",
              bool(m.get("byte_identical")) == (mid in _BYTE_IDENTICAL), f"got {m.get('byte_identical')}")
        check(f"{mid}: emits_sidecar == {mid in _SIDECAR}", bool(m.get("emits_sidecar")) == (mid in _SIDECAR),
              f"got {m.get('emits_sidecar')}")
        # a byte-identical mode can never mutate values (the bytes ARE the source).
        if mid in _BYTE_IDENTICAL:
            check(f"{mid}: byte_identical implies not mutates_values", not m.get("mutates_values"))

    # cross-cutting invariant: every mutating mode is NOT byte_identical (changing a value changes bytes).
    for mid in _MUTATING:
        m = by_id.get(mid, {})
        check(f"{mid}: mutating mode is not byte_identical", not m.get("byte_identical"))

    msg = ("PASS — check_native_output_modes: registry has all 8 output_modes; only schema_preserving/"
           "schema_preserving_with_sidecar/compare mutate values; native_passthrough(+_with_sidecar) is "
           "byte_identical; sidecar/duplicate/wellformed invariants hold.")
    print(f"\n{msg if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: native output-mode registry is the canonical 8-mode source.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
