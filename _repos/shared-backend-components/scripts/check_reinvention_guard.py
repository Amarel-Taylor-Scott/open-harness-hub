"""check_reinvention_guard — proof for the reinvention guardrail (_repos/teleon/backend/src/teleon/registry/reinvention_guard.py).

The 'you're reinventing a solved problem' guardrail, grounded in the federation. Proves the PRECISION DISCIPLINE:
it FIRES (with real grounded matches) on solved problems, and stays QUIET on genuinely-novel work + non-build
messages. Grounding makes it precise (not vibes). Deterministic, offline, stdlib only.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.registry.reinvention_guard import py_function_src_teleon_registry_reinvention_guard__check, py_function_src_teleon_registry_reinvention_guard__detect_intent  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")
        if args.self_test and not ok:
            print(f"  [{'ok' if ok else 'XX'}] {name}{(' — ' + detail) if detail else ''}")

    # FIRES on a solved problem, with grounded matches from the federation
    pdf = py_function_src_teleon_registry_reinvention_guard__check("Let me write a function to parse a PDF and extract text from scratch")
    ck("fires on 'reinvent PDF parsing'", pdf["fire"] is True)
    ck("grounds the fire in real registry matches", bool(pdf.get("existing")) and any(pdf["existing"].values()))
    ck("fire is Tier 2 (grounded)", pdf.get("tier") == 2)
    ck("fire is governed (non-truth)", pdf.get("serves_truth") is False)

    addr = py_function_src_teleon_registry_reinvention_guard__check("I'll implement my own address validation")
    ck("fires on 'reinvent address validation'", addr["fire"] is True)

    # QUIET on genuinely-novel work (no solved-domain signal) — the precision discipline
    novel = py_function_src_teleon_registry_reinvention_guard__check("Let me build a novel quantum-resistant consensus protocol from scratch")
    ck("quiet on genuinely-novel work", novel["fire"] is False)

    # QUIET on non-build messages
    chat = py_function_src_teleon_registry_reinvention_guard__check("what is the weather in Tokyo today")
    ck("quiet on non-build message", chat["fire"] is False and chat["tier"] == 0)

    # Tier 0 detection is sane
    t0 = py_function_src_teleon_registry_reinvention_guard__detect_intent("let me build a CSV parser from scratch")
    ck("Tier 0 detects build intent", t0["build_intent"] is True)
    ck("Tier 0 extracts the solved domain", "csv" in t0["candidate_domains"] or "parse" in t0["candidate_domains"])

    if fails:
        print(f"\nFAIL - check_reinvention_guard: {len(fails)} of {checks} assertions failed")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"PASS - check_reinvention_guard: the guardrail fires on solved problems (grounded in the federation) + "
          f"stays quiet on genuinely-novel/non-build work; {checks} assertions; serves_truth=false.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
