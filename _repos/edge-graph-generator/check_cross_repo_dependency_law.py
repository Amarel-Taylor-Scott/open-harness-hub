#!/usr/bin/env python3
"""tools/check_cross_repo_dependency_law — the PORTABLE enforcement of contracts/surface-registry.json.

Drop this into any surface repo's CI. It proves the cross-repo dependency boundary instead of trusting
prose: every declared `may_depend_on` edge points at a real surface and is NOT a forbidden edge; the graph
is acyclic; and (when a repo declares what it CONSUMES) each consumed surface is actually allowed. A surface
becomes aware of another only through the other's published interface — importing its source is the edge this
gate forbids.

Reads contracts/surface-registry.json (next to this tools/ dir by default). Offline, deterministic,
`--self-test`-able. This is the multi-repo generalization of the reference project's
scripts/check_portfolio_dependency_law.py.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _resolve_registry() -> Path:
    """Find surface-registry.json robustly, whether this tool sits in edge-graph-generator/ (registry is in
    the sibling dev-rules-context/) or inside dev-rules-context/tools/ (registry is a sibling contracts/).
    No single hardcoded path that breaks when the tool moves."""
    for c in (HERE.parent / "dev-rules-context" / "contracts" / "surface-registry.json",
              HERE.parent / "contracts" / "surface-registry.json",
              HERE / "contracts" / "surface-registry.json"):
        if c.exists():
            return c
    return HERE.parent / "dev-rules-context" / "contracts" / "surface-registry.json"


DEFAULT_REGISTRY = _resolve_registry()


def load_registry(path: Path) -> dict:
    return json.loads(path.read_text())


def _forbidden_set(reg: dict) -> set[tuple[str, str]]:
    return {(e["from"], e["to"]) for e in reg.get("forbidden_edges", [])}


def _has_cycle(surfaces: dict[str, dict]) -> list[str]:
    """Return a cycle path if the may_depend_on graph has one, else []."""
    WHITE, GREY, BLACK = 0, 1, 2
    color = {s: WHITE for s in surfaces}
    stack: list[str] = []

    def visit(node: str) -> list[str]:
        color[node] = GREY
        stack.append(node)
        for dep in surfaces.get(node, {}).get("may_depend_on", []):
            if dep not in surfaces:
                continue
            if color.get(dep) == GREY:
                return stack[stack.index(dep):] + [dep]
            if color.get(dep) == WHITE:
                c = visit(dep)
                if c:
                    return c
        color[node] = BLACK
        stack.pop()
        return []

    for s in surfaces:
        if color[s] == WHITE:
            c = visit(s)
            if c:
                return c
    return []


def validate_registry(reg: dict) -> list[str]:
    """Return a list of violations (empty == the registry is internally consistent + legal)."""
    problems: list[str] = []
    surfaces = reg.get("surfaces", {})
    forbidden = _forbidden_set(reg)
    for name, spec in surfaces.items():
        for dep in spec.get("may_depend_on", []):
            if dep not in surfaces:
                problems.append(f"{name}.may_depend_on -> unknown surface {dep!r}")
            if (name, dep) in forbidden:
                problems.append(f"{name} -> {dep} is a may_depend_on edge AND a forbidden_edge (contradiction)")
    for e in reg.get("forbidden_edges", []):
        for endpoint in (e["from"], e["to"]):
            if endpoint not in surfaces:
                problems.append(f"forbidden_edge references unknown surface {endpoint!r}")
    cycle = _has_cycle(surfaces)
    if cycle:
        problems.append("dependency CYCLE: " + " -> ".join(cycle))
    return problems


def check_repo_consumes(reg: dict, surface: str, consumes: list[str]) -> list[str]:
    """A repo (this `surface`) declares what it CONSUMES; verify each is allowed. Empty == legal."""
    problems: list[str] = []
    surfaces = reg.get("surfaces", {})
    if surface not in surfaces:
        return [f"unknown surface {surface!r} (not in registry)"]
    allowed = set(surfaces[surface].get("may_depend_on", []))
    forbidden = _forbidden_set(reg)
    for c in consumes:
        if c not in surfaces:
            problems.append(f"{surface} consumes unknown surface {c!r}")
        elif (surface, c) in forbidden:
            problems.append(f"{surface} consumes {c} — FORBIDDEN edge")
        elif c not in allowed:
            problems.append(f"{surface} consumes {c} — not in its may_depend_on (undeclared cross-repo dependency)")
    return problems


def self_test() -> int:
    reg = {
        "surfaces": {
            "rules": {"may_depend_on": []},
            "substrate": {"may_depend_on": ["rules"]},
            "teleon": {"may_depend_on": ["rules", "substrate"]},
            "baltor": {"may_depend_on": ["rules", "substrate", "teleon"]},
        },
        "forbidden_edges": [{"from": "teleon", "to": "baltor", "why": "infra not product-specific"},
                            {"from": "substrate", "to": "teleon", "why": "substrate is neutral"}],
    }
    checks = [
        ("legal registry validates clean", validate_registry(reg) == []),
        ("baltor may consume teleon", check_repo_consumes(reg, "baltor", ["teleon", "substrate"]) == []),
        ("teleon may NOT consume baltor (forbidden)", len(check_repo_consumes(reg, "teleon", ["baltor"])) == 1),
        ("consuming an undeclared surface fails", len(check_repo_consumes(reg, "substrate", ["teleon"])) == 1),
        ("consuming an unknown surface fails", len(check_repo_consumes(reg, "baltor", ["ghost"])) == 1),
    ]
    # a cycle is detected
    bad = {"surfaces": {"a": {"may_depend_on": ["b"]}, "b": {"may_depend_on": ["a"]}}, "forbidden_edges": []}
    checks.append(("cycle detected", any("CYCLE" in p for p in validate_registry(bad))))
    # a may_depend_on that is also forbidden is a contradiction
    contra = {"surfaces": {"a": {"may_depend_on": ["b"]}, "b": {"may_depend_on": []}},
              "forbidden_edges": [{"from": "a", "to": "b", "why": "x"}]}
    checks.append(("may_depend_on vs forbidden contradiction caught", any("contradiction" in p for p in validate_registry(contra))))

    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - check_cross_repo_dependency_law:\n  " + "\n  ".join(failed)); return 1
    print("PASS - check_cross_repo_dependency_law: portable cross-repo boundary proof — validates the surface "
          "registry (unknown edges, forbidden-vs-allowed contradictions, cycles) and a repo's declared consumes "
          "(forbidden / undeclared cross-repo dependency). Awareness only via published interface, never source.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Enforce the cross-repo surface dependency law.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    ap.add_argument("--surface", help="this repo's surface name (to check its declared consumes)")
    ap.add_argument("--consumes", nargs="*", default=[], help="surfaces this repo consumes")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if not args.registry.exists():
        print(f"registry not found: {args.registry}"); return 2
    reg = load_registry(args.registry)
    problems = validate_registry(reg)
    if args.surface:
        problems += check_repo_consumes(reg, args.surface, args.consumes)
    if problems:
        print("FAIL - cross-repo dependency law violated:\n  " + "\n  ".join(problems)); return 1
    n = len(reg.get("surfaces", {}))
    print(f"PASS - cross-repo dependency law: {n} surfaces, registry consistent"
          + (f", {args.surface} consumes {args.consumes} — all allowed" if args.surface else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
