"""check_vertical_playbooks — proof for architecture/vertical_playbooks.json (backs registry #93).

Each vertical playbook is a management-workflow SHAPE + the registries that COMPOSE it into a DAG. Enforces:
  - required fields; stages + composes_registries are non-empty lists; ids unique; >=6 playbooks, >=4 domains;
  - every composes_registries entry is a REAL registry id in registry_ontology (the playbook ties to the federation);
  - NO insurance vertical (repo rule: stay away from insurance); serves_truth=false.

Deterministic, offline, stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_DOC = _REPO / "architecture" / "vertical_playbooks.json"
_ONT = _REPO / "architecture" / "registry_ontology.json"
_REQ = ("id", "domain", "stages", "incumbents", "composes_registries", "governance", "loop")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    doc = json.loads(_DOC.read_text())
    playbooks = doc.get("playbooks", [])
    real_registry_ids = {r["id"] for r in json.loads(_ONT.read_text()).get("registries", [])}
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
    ck(">=6 playbooks", len(playbooks) >= 6, str(len(playbooks)))

    ids: set[str] = set()
    domains: set[str] = set()
    for p in playbooks:
        pid = p.get("id", "?")
        for f in _REQ:
            ck(f"{pid}: has '{f}'", bool(p.get(f)))
        ck(f"{pid}: unique id", pid not in ids, "duplicate")
        ids.add(pid)
        domains.add(p.get("domain", ""))
        ck(f"{pid}: stages is a non-empty list", isinstance(p.get("stages"), list) and len(p.get("stages", [])) >= 2)
        comp = p.get("composes_registries", [])
        ck(f"{pid}: composes_registries non-empty", isinstance(comp, list) and len(comp) >= 1)
        # each composed registry is a REAL registry id (the playbook ties to the federation)
        for rid in comp:
            ck(f"{pid}: composes a real registry '{rid}'", rid in real_registry_ids,
               f"not in ontology (ids like {sorted(real_registry_ids)[:3]}...)")
        # repo rule: no insurance vertical
        blob = f"{pid} {p.get('domain', '')}".lower()
        ck(f"{pid}: not an insurance vertical (repo rule)", "insurance" not in blob)

    ck(">=4 domains", len(domains) >= 4, str(sorted(domains)))

    if fails:
        print(f"\nFAIL - check_vertical_playbooks: {len(fails)} of {checks} assertions failed")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"PASS - check_vertical_playbooks: {len(playbooks)} vertical playbooks across {len(domains)} domains, "
          f"each composing REAL registries; no insurance; {checks} assertions; serves_truth=false.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
