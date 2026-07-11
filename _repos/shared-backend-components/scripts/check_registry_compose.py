"""check_registry_compose — proof for the playbook->DAG compiler (_repos/teleon/backend/src/teleon/registry/compose.py).

Proves 'how registries become a tool': a vertical playbook compiles into a DAG plan whose stages map to REAL
composing registries (some queryable on the menu, some policy/runtime), and a universal intent compiles into a
mixed tool that picks the right ingredient. Deterministic, offline, stdlib only.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.registry.compose import py_function_src_teleon_registry_compose__compile_playbook, py_function_src_teleon_registry_compose__compile_universal  # noqa: E402


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

    # vertical tool: dental_clinic compiles into a DAG plan
    dag = py_function_src_teleon_registry_compose__compile_playbook("dental_clinic")
    ck("dental_clinic compiles", dag.get("available") is True)
    ck("has loop stages", len(dag.get("stages", [])) >= 4)
    ck("composes real registries", len(dag.get("composes", [])) >= 1)
    on_menu = [c for c in dag.get("composes", []) if c["on_menu"]]
    ck("at least one composed registry is queryable on the menu", len(on_menu) >= 1,
       str([c["registry"] for c in dag.get("composes", [])]))
    ck("queryable registries return ingredients", all(c["ingredients"] for c in on_menu))
    ck("policy registries honestly flagged off-menu", any(not c["on_menu"] for c in dag.get("composes", [])))
    ck("carries governance + is candidate-only", bool(dag.get("governance")) and dag.get("candidate_dag") is True)
    ck("serves_truth false", dag.get("serves_truth") is False)

    # unknown playbook -> honest
    ck("unknown playbook -> available False", py_function_src_teleon_registry_compose__compile_universal and py_function_src_teleon_registry_compose__compile_playbook("nope").get("available") is False)

    # universal/mixed tool: a 'weather' intent picks the weather portal
    uni = py_function_src_teleon_registry_compose__compile_universal("weather")
    lp = next((p for p in uni["picks"] if p["registry"] == "lookup_portals"), {})
    ck("universal tool picks the weather portal", any("Weather" in i for i in lp.get("ingredients", [])),
       str(lp.get("ingredients")))
    ck("universal is a candidate DAG", uni.get("candidate_dag") is True and uni.get("serves_truth") is False)

    if fails:
        print(f"\nFAIL - check_registry_compose: {len(fails)} of {checks} assertions failed")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"PASS - check_registry_compose: playbooks compile into DAG plans over REAL registries (vertical + "
          f"universal), governed + candidate-only; {checks} assertions; serves_truth=false.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
