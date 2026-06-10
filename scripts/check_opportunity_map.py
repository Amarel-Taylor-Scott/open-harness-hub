#!/usr/bin/env python3
"""scripts.check_opportunity_map — proof: architecture/opportunities.json is complete + actionable. Every
non-M10 section in the maturity matrix has an opportunity (or a deprecation reason); every P0 has done_when +
a proof plan; no opportunity is vague ("research" with no output). This keeps the opportunity map honest +
executable rather than aspirational.

CLI: python3 scripts/check_opportunity_map.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_VALID_PRI = {"P0", "P1", "P2"}
_FIELDS = ("opportunity_id", "title", "category", "why_it_matters", "current_state", "target_state",
           "files_to_touch", "proofs_to_add", "dependencies", "risk", "priority", "estimated_complexity",
           "owner_section", "done_when")
_NON_M10 = {"candidate", "experimental", "m6_proof", "m7_api", "m8_ui", "m0_absent", "m1_folder", "m2_contract",
            "m3_port", "m4_impl", "m5_integrated"}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    opps = json.loads((_REPO / "architecture" / "opportunities.json").read_text())["opportunities"]
    matrix = json.loads((_REPO / "architecture" / "section_maturity_matrix.json").read_text())["sections"]
    check("opportunities.json has entries", len(opps) >= 5, str(len(opps)))

    missing_fields, bad_pri, empty_output = [], [], []
    for o in opps:
        for f in _FIELDS:
            if f not in o:
                missing_fields.append(f"{o.get('opportunity_id')}.{f}")
        if o.get("priority") not in _VALID_PRI:
            bad_pri.append(f"{o.get('opportunity_id')}={o.get('priority')}")
        # no opportunity may be a no-op: it must change files OR add a proof
        if not (o.get("files_to_touch") or o.get("proofs_to_add")):
            empty_output.append(o.get("opportunity_id"))
    check("every opportunity declares all required fields", missing_fields == [], str(missing_fields[:6]))
    check("every opportunity has a valid priority", bad_pri == [], str(bad_pri))
    check("no opportunity is a no-op (must touch files or add a proof)", empty_output == [], str(empty_output))

    no_done, no_proofplan = [], []
    for o in opps:
        if o["priority"] == "P0":
            if not o.get("done_when"):
                no_done.append(o["opportunity_id"])
            if not o.get("proofs_to_add"):
                no_proofplan.append(o["opportunity_id"])
    check("every P0 opportunity has done_when", no_done == [], str(no_done))
    check("every P0 opportunity has a proof plan", no_proofplan == [], str(no_proofplan))

    owned = {o["owner_section"] for o in opps}
    uncovered = [s["section_id"] for s in matrix
                 if s.get("status") in _NON_M10 and s["section_id"] not in owned]
    check("every non-M10 section has an opportunity", uncovered == [], str(uncovered))

    print(f"\n{'PASS — check_opportunity_map: opportunities complete + actionable; every P0 has done_when + a proof plan; every non-M10 section is covered; no no-op opportunities.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: opportunity map.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
