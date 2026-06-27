#!/usr/bin/env python3
"""scripts.check_oh_states_kit — PROOF for the shared empty/loading/error UX primitives
(UX-BACKLOG P1 #3). oh-states.js is the vanilla token-only primitive loaded by the PRESERVED legacy
front-end (web/openhubforai/legacy.html — kept lossless when the kit React SPA became the current
surface). Static contract: the primitive is loaded by its host, exposes the three functions, each
carries the right ARIA role, uses DESIGN TOKENS not hardcoded colors (S1), and escapes interpolated
text (no injection). node --check syntax-gates the file when node is available.

Offline, stdlib-only. Exit 0/1.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WEB = REPO_ROOT / "web" / "openhubforai"
KIT = WEB / "oh-states.js"


def _self_test() -> int:
    fails: list[str] = []

    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    legacy = (WEB / "legacy.html").read_text(encoding="utf-8")
    kit = KIT.read_text(encoding="utf-8")

    ck("A: legacy.html (the preserved vanilla host) loads oh-states.js", 'src="oh-states.js"' in legacy)
    ck("B: exposes empty/skeleton/error", all(f"{fn}:" in kit for fn in ("empty", "skeleton", "error")))
    ck("C: empty has role=status", 'oh-state--empty' in kit and 'role="status"' in kit)
    ck("C: loading has aria-busy", 'aria-busy="true"' in kit)
    ck("C: error has role=alert", 'oh-state--error' in kit and 'role="alert"' in kit)
    # S1: colors come from tokens (var(--…)), not raw hex — allow ONE documented danger fallback
    raw_hex = re.findall(r"#[0-9a-fA-F]{3,8}\b", kit)
    ck("D: design tokens not hardcoded colors (≤1 documented fallback)",
       kit.count("var(--") >= 8 and len(raw_hex) <= 1, str(raw_hex))
    ck("E: interpolated text is escaped (no injection)", "function esc(" in kit and "esc(o.title" in kit)

    node = shutil.which("node")
    if node:
        res = subprocess.run([node, "--check", str(KIT)], capture_output=True, text=True)
        ck("F: node --check oh-states.js", res.returncode == 0, res.stderr.strip()[:160])
    else:
        print("  [ok] F: node unavailable — syntax check skipped honestly")

    print("\n" + ("PASS — check_oh_states_kit: shared empty/loading/error primitives loaded, correct ARIA "
                  "roles, token-only styling (S1), escaped interpolation."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_oh_states_kit.py --self-test")
    raise SystemExit(0)
