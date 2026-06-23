"""check_observability_providers — proof for architecture/observability_providers.json (backs registry #33).

A POINTER-ONLY catalog of external observability providers (metrics/traces/logs/errors/llm_traces) a compiled
workflow can auto-instrument with. Enforces: required fields; signal in the legend; open_source/otel_compatible
are booleans; pointer-only (short ref, no bulk data); coverage (>=10 providers, >=4 signals); serves_truth=false.

Deterministic, offline, stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_DOC = _REPO / "architecture" / "observability_providers.json"
_REQ = ("id", "name", "signal", "model", "open_source", "otel_compatible", "ref")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    doc = json.loads(_DOC.read_text())
    providers = doc.get("providers", [])
    legend = set(doc.get("signal_legend", {}))
    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")
        if args.self_test and not ok:
            print(f"  [XX] {name}{(' — ' + detail) if detail else ''}")

    ck("serves_truth is false", doc.get("serves_truth") is False)
    ck(">=10 providers", len(providers) >= 10, str(len(providers)))
    ck("signal_legend defined", len(legend) >= 4, str(sorted(legend)))

    ids: set[str] = set()
    signals: set[str] = set()
    for p in providers:
        pid = p.get("id", "?")
        for f in _REQ:
            ck(f"{pid}: has '{f}'", f in p and p.get(f) is not None and p.get(f) != "")
        ck(f"{pid}: unique id", pid not in ids, "duplicate")
        ids.add(pid)
        signals.add(p.get("signal", ""))
        ck(f"{pid}: signal in legend", p.get("signal") in legend, str(p.get("signal")))
        ck(f"{pid}: open_source is bool", isinstance(p.get("open_source"), bool))
        ck(f"{pid}: otel_compatible is bool", isinstance(p.get("otel_compatible"), bool))
        ck(f"{pid}: ref is a short pointer string", isinstance(p.get("ref"), str) and len(p.get("ref", "")) < 80)
        ck(f"{pid}: stores no bulk data (pointer-only)", not any(isinstance(v, list) and len(v) > 3 for v in p.values()))

    ck(">=4 signal types", len(signals) >= 4, str(sorted(signals)))

    if fails:
        print(f"\nFAIL - check_observability_providers: {len(fails)} of {checks} assertions failed")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"PASS - check_observability_providers: {len(providers)} pointer-only observability providers across "
          f"{len(signals)} signal types; {checks} assertions; serves_truth=false.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
