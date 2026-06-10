#!/usr/bin/env python3
"""scripts.check_{{proof_name}} — proof: {{title}} (subject: {{subject_module}}).

GENERATED from proof.self_test.v1 (standard.proof_script.v1). This is the canonical proof scaffold: a
deterministic, OFFLINE --self-test that prints [ok]/[FAIL] lines, a PASS/FAIL summary, and exits 0/1. The
harness-mechanics block below is real and passes (content-addressing is deterministic; the temp dir is
created and cleaned up). Add your subject assertions against {{subject_module}} where marked.

CLI: python3 scripts/check_{{proof_name}}.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from pathlib import Path


def _hash(obj) -> str:
    # content-addressed (NOT wall-clock) so the same body always yields the same id
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:16]


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    tmp = Path(tempfile.mkdtemp(prefix="check_{{proof_name}}_"))
    try:
        # ── harness mechanics (real): determinism + a clean temp dir ──
        body = {"subject": "{{subject_module}}", "n": 1}
        check("content id is deterministic (no wall-clock)", _hash(body) == _hash(dict(body)))
        f = tmp / "artifact.json"
        f.write_text(json.dumps(body, sort_keys=True))
        check("temp-dir write round-trips", json.loads(f.read_text()) == body)

        # ── subject assertions (TODO): assert the real {{subject_module}} contract here ──
        # Example shape: from {{subject_module}} import <fn>; out = <fn>(...); check("...", out == expected)
        check("subject placeholder for {{title}} present", True,
              "TODO: replace with real {{subject_module}} assertions")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"{'PASS' if not fails else 'FAIL'} check_{{proof_name}} ({len(fails)} failing)")
    return 0 if not fails else 1


def _main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Proof: {{title}}.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
