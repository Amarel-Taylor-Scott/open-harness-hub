"""check_formula_registry — proof for architecture/formula_registry.json (backs registry #98).

Named DETERMINISTIC formulas the compiler applies instead of an LLM. Enforces each is a well-formed SPEC
(id / domain / expression / variables / units), ids unique, coverage (>=10 formulas across >=5 domains), and that
it is a SPEC CATALOG only (expression is a string, variables is a dict — nothing is eval'd here). serves_truth=false.
Deterministic, offline, stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_DOC = _REPO / "architecture" / "formula_registry.json"
_REQ = ("id", "domain", "expression", "variables", "units", "source")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    doc = json.loads(_DOC.read_text())
    formulas = doc.get("formulas", [])
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
    ck(">=10 formulas", len(formulas) >= 10, str(len(formulas)))

    ids: set[str] = set()
    domains: set[str] = set()
    for f in formulas:
        fid = f.get("id", "?")
        for r in _REQ:
            ck(f"{fid}: has '{r}'", bool(f.get(r)))
        ck(f"{fid}: unique id", fid not in ids, "duplicate")
        ids.add(fid)
        domains.add(f.get("domain", ""))
        ck(f"{fid}: expression is a string (spec, not eval'd)", isinstance(f.get("expression"), str))
        ck(f"{fid}: variables is a non-empty dict", isinstance(f.get("variables"), dict) and len(f.get("variables", {})) >= 1)
        # every symbol named in variables should appear in the expression (spec is self-consistent)
        expr = f.get("expression", "")
        ck(f"{fid}: variables appear in the expression", all(v in expr for v in f.get("variables", {})),
           str([v for v in f.get("variables", {}) if v not in expr]))

    ck(">=5 domains", len(domains) >= 5, str(sorted(domains)))

    if fails:
        print(f"\nFAIL - check_formula_registry: {len(fails)} of {checks} assertions failed")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"PASS - check_formula_registry: {len(formulas)} deterministic formula specs across {len(domains)} "
          f"domains, self-consistent (variables in expression); spec-only (no eval); {checks} assertions; serves_truth=false.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
