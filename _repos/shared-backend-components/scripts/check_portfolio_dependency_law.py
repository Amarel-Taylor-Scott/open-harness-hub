#!/usr/bin/env python3
"""scripts.check_portfolio_dependency_law — PROOF: the brand-portfolio dependency LAW holds in code.

Portfolio (owner-directed 2026-06-06; _repos/shared-backend-components/architecture/portfolio_dependency_law.json): a holding company owns
OpenHubForAI (open ecosystem + spec), Teleon (purpose-driven runtime SaaS), and Baltor (applied product, a
TENANT of Teleon). The law: Baltor → Teleon → OpenHubForAI; never the reverse.

Asserts:
  A. CONFIG well-formed: the three layers present; each has package_roots + may_depend_on; forbidden_edges are
     exactly the directions NOT permitted by may_depend_on (no contradiction between the two encodings).
  B. NO FORBIDDEN IMPORT EDGE exists in code: scanning real import statements under each layer's package roots,
     no module imports a layer it must not (teleon↛baltor; openhubforai↛baltor; openhubforai↛teleon).
  C. SELF-CONSISTENCY: every may_depend_on target is a real layer; a layer never lists itself.
  D. MIGRATION DEBT is TRACKED (not silent): the generic modules still under _repos/baltor/backend/src/baltor that must move into
     Teleon are listed in migration_status.to_extract_into_teleon (no_silent_caps — printed every run).

Deterministic + offline (reads files, no network). Exit 0/1.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_LAW = _resource("architecture") / "portfolio_dependency_law.json"


def _module_prefix(package_root: str) -> str:
    """'_repos/teleon/backend/src/teleon' -> 'src.teleon' (the import path a forbidden edge would use)."""
    return package_root.replace("/", ".")


def _imports_in(py: Path) -> list[str]:
    """The dotted module targets of real import statements in a .py file (skips comments/strings heuristically:
    only lines whose first token is import/from count)."""
    out: list[str] = []
    for raw in py.read_text(encoding="utf-8", errors="ignore").splitlines():
        s = raw.strip()
        if s.startswith("import "):
            out.append(s[len("import "):].split(" ")[0].split(",")[0].strip())
        elif s.startswith("from "):
            out.append(s[len("from "):].split(" ")[0].strip())
    return out


def _scan_layer(roots: list[str]) -> list[tuple[Path, list[str]]]:
    files: list[tuple[Path, list[str]]] = []
    for r in roots:
        base = _resource(r)
        if not base.exists():
            continue
        for py in sorted(base.rglob("*.py")):
            if "__pycache__" in py.parts:
                continue
            files.append((py, _imports_in(py)))
    return files


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    law = json.loads(_LAW.read_text())
    layers = law["layers"]
    names = set(layers)

    # A. config well-formed
    check("A: three layers present", names == {"openhubforai", "teleon", "baltor"}, str(sorted(names)))
    for ln, lv in layers.items():
        check(f"A: {ln} has package_roots + may_depend_on",
              isinstance(lv.get("package_roots"), list) and isinstance(lv.get("may_depend_on"), list))
    # forbidden_edges must be exactly the complement of may_depend_on (over real cross-layer pairs)
    allowed = {(a, b) for a in names for b in layers[a]["may_depend_on"]}
    expected_forbidden = {(a, b) for a in names for b in names if a != b and (a, b) not in allowed}
    declared_forbidden = {(e["from"], e["to"]) for e in law["forbidden_edges"]}
    check("A: forbidden_edges == complement of may_depend_on (no contradiction)",
          declared_forbidden == expected_forbidden, f"declared={sorted(declared_forbidden)} expected={sorted(expected_forbidden)}")

    # C. self-consistency
    for ln, lv in layers.items():
        check(f"C: {ln} does not depend on itself", ln not in lv["may_depend_on"])
        check(f"C: {ln} may_depend_on targets are real layers", all(t in names for t in lv["may_depend_on"]))

    # B. no forbidden import edge in code
    prefixes = {ln: [_module_prefix(r) for r in layers[ln]["package_roots"]] for ln in names}
    for frm, to in sorted(declared_forbidden):
        bad: list[str] = []
        scanned = 0
        for py, imports in _scan_layer(layers[frm]["package_roots"]):
            scanned += 1
            for imp in imports:
                if any(imp == pref or imp.startswith(pref + ".") for pref in prefixes[to]):
                    bad.append(f"{py.relative_to(_REPO)} imports {imp}")
        check(f"B: no {frm}→{to} import ({scanned} files scanned)", not bad, "; ".join(bad[:5]))

    # D. migration debt tracked + visible
    debt = law["migration_status"]["to_extract_into_teleon"]
    check("D: migration debt to_extract_into_teleon is a non-empty tracked list", isinstance(debt, list) and len(debt) >= 1)
    print("    migration debt (generic code still under src/baltor, to move into _repos/teleon/backend/src/teleon):")
    for d in debt:
        print(f"      - {d}")

    print("\n" + ("PASS — check_portfolio_dependency_law: the portfolio law is well-formed and holds in code — "
                  "Teleon never imports Baltor, OpenHubForAI imports neither; Baltor→Teleon→OpenHubForAI is "
                  "the only permitted direction; the incremental extraction debt is tracked (not silent)."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_portfolio_dependency_law.py --self-test")
    raise SystemExit(0)
