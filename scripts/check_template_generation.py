#!/usr/bin/env python3
"""scripts.check_template_generation — proof: the component generator renders standards-conformant scaffolds.

Drives scripts/generate_from_template.py in a deterministic temp repo (templates/ + catalog copied in, no
network): the generator can render the PROOF template and the DOCS template, REFUSES a missing required
variable, REFUSES overwrite without --force, writes a content-addressed generation receipt, and the generated
proof contains "--self-test". This is the enforcement that the factory's generator actually works.

Deterministic + offline + --self-test + PASS/FAIL + exit 0/1.

CLI: python3 scripts/check_template_generation.py --self-test
"""
from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _RR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.generate_from_template import GenerationError, generate

_REPO = Path(__file__).resolve().parents[1]
_CATALOG = _REPO / "architecture" / "template_catalog.json"


def _temp_repo() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="check_tmpl_gen_"))
    (tmp / "architecture").mkdir(parents=True, exist_ok=True)
    shutil.copy(_CATALOG, tmp / "architecture" / "template_catalog.json")
    shutil.copytree(_REPO / "templates", tmp / "templates")
    return tmp


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    tmp = _temp_repo()
    try:
        # 1) refuses a missing required variable
        try:
            generate("proof.self_test", {"proof_name": "x"}, repo=tmp, write_receipt=False)
            check("refuses missing required variable", False, "did not raise")
        except GenerationError as e:
            check("refuses missing required variable", "missing required" in str(e))

        # 2) renders the proof template; the generated proof contains --self-test
        proof_vars = {"proof_name": "demo_proof", "title": "Demo proof", "owner": "scripts/demo.py",
                      "subject_module": "scripts.demo"}
        rec = generate("proof.self_test", proof_vars, repo=tmp)
        gen_proof = tmp / "scripts" / "check_demo_proof.py"
        check("renders the proof template", gen_proof.exists())
        proof_body = gen_proof.read_text() if gen_proof.exists() else ""
        check("generated proof contains --self-test", "--self-test" in proof_body)
        check("generated proof is fully rendered (no {{var}})", "{{" not in proof_body)

        # 3) writes a content-addressed generation receipt
        receipt_file = tmp / ".agent" / "template-generation" / f"{rec['receipt_id']}-proof.self_test.json"
        check("writes a generation receipt", receipt_file.exists(), str(receipt_file))
        check("receipt id is content-addressed (gen- prefix)", rec["receipt_id"].startswith("gen-"))

        # 4) refuses overwrite without --force; allows with --force
        try:
            generate("proof.self_test", proof_vars, repo=tmp, write_receipt=False)
            check("refuses overwrite without --force", False, "did not raise")
        except GenerationError as e:
            check("refuses overwrite without --force", "without --force" in str(e))
        rec_force = generate("proof.self_test", proof_vars, repo=tmp, force=True, write_receipt=False)
        check("--force allows overwrite (same deterministic id)", rec_force["receipt_id"] == rec["receipt_id"])

        # 5) renders the docs template with the required headings
        generate("docs.section_page",
                 {"area": "runtime", "section": "demo-section", "title": "Demo Section", "owner": "scripts/x.py"},
                 repo=tmp)
        page = tmp / "docs" / "runtime" / "demo-section.md"
        check("renders the docs template", page.exists())
        required = ["Purpose", "Owner", "Inputs", "Outputs", "Contracts", "Ports", "Adapters",
                    "Registry entries", "Proofs", "Commands", "Limitations", "Opportunities", "Next steps"]
        body = page.read_text() if page.exists() else ""
        check("docs template carries all required headings",
              all(f"## {h}" in body for h in required),
              str([h for h in required if f"## {h}" not in body]))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"{'PASS' if not fails else 'FAIL'} check_template_generation ({len(fails)} failing)")
    return 0 if not fails else 1


def _main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Proof: the template generator renders conformant scaffolds.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
