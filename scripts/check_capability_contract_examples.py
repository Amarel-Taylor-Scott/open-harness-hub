#!/usr/bin/env python3
"""scripts.check_capability_contract_examples — proof (C35): every slot declares a non-empty input/output
contract, and every referenced contract example (schemas/examples/*.json) exists, is valid JSON, names a real
slot + a real adapter in that slot, and carries input + output objects. The contract is what stays stable when
the adapter behind a slot is swapped — so it must be exemplified, not just named.

CLI: python3 scripts/check_capability_contract_examples.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))
from src.baltor.runtime.registry.capability_registry import CapabilityRegistry  # noqa: E402

_MIN_EXAMPLES = 4  # at least one each across pre-LLM / post-LLM / meta to prove the pattern generalizes


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    reg = CapabilityRegistry()

    no_contract = [s["capability_slot"] for s in reg.slots()
                   if not (str(s.get("input_schema", "")).strip() and str(s.get("output_schema", "")).strip())]
    check("every slot declares a non-empty input + output contract", no_contract == [], str(no_contract))

    examples = [(s["capability_slot"], s["contract_example"], s.get("adapter_id"))
                for s in reg.slots() if s.get("contract_example")]
    check(f"at least {_MIN_EXAMPLES} slots reference a contract example", len(examples) >= _MIN_EXAMPLES, str(len(examples)))

    valid_adapter_ids = {a.get("adapter_id") for s in reg.slots() for a in s["adapters"]}
    bad = []
    for slot, path, wired in examples:
        fp = _REPO / path
        if not fp.exists():
            bad.append(f"{slot}: missing {path}"); continue
        try:
            ex = json.loads(fp.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            bad.append(f"{slot}: invalid JSON {path}: {e}"); continue
        if ex.get("capability_slot") != slot:
            bad.append(f"{slot}: example capability_slot={ex.get('capability_slot')!r} mismatch")
        if ex.get("adapter_id") not in valid_adapter_ids:
            bad.append(f"{slot}: example adapter_id {ex.get('adapter_id')!r} not a real adapter")
        if not isinstance(ex.get("input"), dict) or not isinstance(ex.get("output"), dict):
            bad.append(f"{slot}: example missing input/output objects")
    check("every referenced contract example exists, parses, and names a real slot+adapter with input+output",
          bad == [], str(bad[:6]))

    print(f"\n{'PASS — check_capability_contract_examples: every slot has an I/O contract; referenced examples are valid and grounded in real slots+adapters.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: capability contract examples.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
