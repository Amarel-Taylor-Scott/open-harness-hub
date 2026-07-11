#!/usr/bin/env python3
"""scripts.baltor_acceptance — the stakeholder "does the product actually work?" smoke test.

One command that runs the WHOLE Baltor motion over BOTH bundled corpora (acme + cfpb) via the
shipped engines (it composes `demo_full_app.run_demo` — it does NOT reimplement anything) and prints
one human-readable PASS/FAIL with the headline outcome per corpus. Distinct from the dev watchdog
(`baltor_flywheel.py`, which runs every module's unit self-test): this is the end-to-end product
acceptance check a non-developer can read.

CLI:
    python3 _repos/shared-backend-components/scripts/baltor_acceptance.py             # human report; exit 0 iff the product works
    python3 _repos/shared-backend-components/scripts/baltor_acceptance.py --self-test # assert the expected end-to-end outcomes
"""
from __future__ import annotations

import argparse

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _RR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.demo_full_app import run_demo, CORPORA


def acceptance() -> dict:
    """Run both corpora end-to-end and summarize the product-level outcome (deterministic)."""
    rows: list[dict] = []
    for corpus in CORPORA:
        d = run_demo(corpus=corpus)
        intr, sw = d["interrogation"], d["swarm"]
        tb = d["compression"]["token_budget"]
        patch = sw["consensus"]["context_pack_patch"]
        row = {
            "corpus": corpus, "label": CORPORA[corpus]["label"],
            "answer": intr["answer_value"],
            "authority": (intr["authority"]["subject_id"] if intr["authority"] else None),
            "contradiction_caught": bool(intr["contradictions"]),
            "source_cited": bool(intr["source_handles"]) and all(h.startswith("ctx://") for h in intr["source_handles"]),
            "reviews_routed": len(sw["review_requests"]),
            "proposed_fix": (f"{patch['from_value']}→{patch['to_value']}" if patch else None),
            "patch_applied": (patch["applied"] if patch else None),
            "tokens": f"{tb['estimated_before']}→{tb['estimated_after']}",
            "canonical_mutated": d["canonical_mutated"],
        }
        row["ok"] = (row["answer"] is not None and row["contradiction_caught"] and row["source_cited"]
                     and row["reviews_routed"] >= 1 and row["patch_applied"] is False
                     and row["canonical_mutated"] is False)
        rows.append(row)
    return {"rows": rows, "passed": all(r["ok"] for r in rows)}


def _report(rep: dict) -> str:
    lines = ["=== Baltor product acceptance (end-to-end, both corpora) ==="]
    for r in rep["rows"]:
        lines.append(
            f"  [{'PASS' if r['ok'] else 'FAIL'}] {r['label']}: answer={r['answer']} "
            f"(authority {r['authority']}) · contradiction caught={r['contradiction_caught']} · "
            f"source-cited={r['source_cited']} · reviews routed={r['reviews_routed']} · "
            f"proposed fix {r['proposed_fix']} (applied={r['patch_applied']}) · "
            f"pack {r['tokens']} tokens · canonical_mutated={r['canonical_mutated']}")
    lines.append(f"\nOVERALL: {'PASS — the product works end-to-end on both corpora.' if rep['passed'] else 'FAIL'}")
    return "\n".join(lines)


def _self_test() -> int:
    failures: list[str] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    rep = acceptance()
    by = {r["corpus"]: r for r in rep["rows"]}
    chk("both corpora ran", set(by) == set(CORPORA), str(set(by)))
    chk("acme: answer 5, fix 3→5", by["acme"]["answer"] == 5 and by["acme"]["proposed_fix"] == "3→5")
    chk("cfpb: answer 10, fix 30→10", by["cfpb"]["answer"] == 10 and by["cfpb"]["proposed_fix"] == "30→10")
    for c, r in by.items():
        chk(f"{c}: contradiction caught + source-cited", r["contradiction_caught"] and r["source_cited"])
        chk(f"{c}: >=1 review routed, patch NOT applied, no canonical mutation",
            r["reviews_routed"] >= 1 and r["patch_applied"] is False and r["canonical_mutated"] is False)
    chk("OVERALL acceptance PASS", rep["passed"] is True)
    chk("acceptance is deterministic (byte-identical re-run)", acceptance() == rep)

    print(f"\n{'PASS — baltor_acceptance: the product works end-to-end on BOTH corpora (acme answer 5 / cfpb answer 10; contradiction caught + source-cited; review routed; fix proposed not applied; no canonical mutation); deterministic.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Baltor end-to-end product acceptance smoke test.")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    rep = acceptance()
    print(_report(rep))
    return 0 if rep["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(_main())
