#!/usr/bin/env python3
"""scripts.check_current_state_freshness — PROOF: the orientation doc docs/CURRENT-STATE.md cannot silently ROT.

CURRENT-STATE.md is the doc the multi-day loop reads first. Two ways it rots: (1) a hand-typed flywheel/proof COUNT
that drifts from reality (the canonical no-magic-values bug — a number that describes the repo must be computed/looked
up, never frozen in prose), and (2) it names a file/flag that no longer exists (a dangling source handle). This proof
forbids both — so the doc stays an honest map.

Asserts:
  A. EXISTS: docs/CURRENT-STATE.md is present and non-trivial.
  B. NO FROZEN COUNT (no-magic-values): the doc contains NO `GREEN <n>/<n>` or `<n>/<n> proofs` frozen flywheel count —
     it must reference the live signal instead, so the number cannot drift.
  C. POINTS TO THE LIVE SIGNAL: the doc tells the reader where the real count lives (mentions `baltor_flywheel`).
  D. NO DANGLING HANDLES (anti-rot): every concrete repo path the doc cites in backticks (scripts/…, docs/…,
     architecture/…, web/…, src/…, schemas/…, prompts/…, .agent/…, catalog/…, dist/…, fixtures/…, rubrics/…) resolves
     to a real file or directory on disk. A doc that names a deleted file is rotted.
  E. DETERMINISM: pure read; two scans agree.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DOC = _REPO / "docs" / "CURRENT-STATE.md"

#: a frozen flywheel proof-count typed into prose (the rot we forbid)
_FROZEN_COUNT = re.compile(r"GREEN\s+\d+\s*/\s*\d+|\b\d+\s*/\s*\d+\s+(?:deterministic\s+)?proofs?\b", re.I)
#: a frozen running-surface PORT (drifts as processes restart — reference the URL aggregator instead)
_FROZEN_PORT = re.compile(r":\d{4}\b")
#: concrete repo paths cited in backticks (no spaces, no glob '*', under a known top-level dir)
_TOPS = ("scripts", "docs", "architecture", "web", "websites", "src", "schemas", "prompts",
         "catalog", "dist", "fixtures", "rubrics", ".agent", "data", "configs")
_PATH = re.compile(r"`(" + "|".join(re.escape(t) for t in _TOPS) + r")/([\w./@-]+)`")


def _cited_paths(text: str) -> list[str]:
    out = []
    for m in _PATH.finditer(text):
        p = (m.group(1) + "/" + m.group(2)).rstrip(".,);:")
        if "*" not in p and p not in out:
            out.append(p)
    return out


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    text = _DOC.read_text(encoding="utf-8") if _DOC.is_file() else ""
    check("A: docs/CURRENT-STATE.md exists + non-trivial", len(text) > 400)

    frozen = _FROZEN_COUNT.findall(text)
    check("B: no frozen flywheel proof-count typed into prose (reference the live signal instead)",
          not frozen, f"frozen count(s): {frozen[:3]}")

    check("C: points the reader to the live flywheel signal", "baltor_flywheel" in text)

    ports = _FROZEN_PORT.findall(text)
    check("C2: no frozen running-surface port (drifts — reference dist/cloudflare-urls.md instead)",
          not ports, f"frozen port(s): {ports[:4]}")

    cited = _cited_paths(text)
    missing = [p for p in cited if not (_REPO / p).exists()]
    check(f"D: every cited repo path resolves ({len(cited)} cited, no dangling handles)", not missing, f"missing: {missing[:5]}")

    check("E: deterministic (re-scan agrees)", _cited_paths(text) == cited and _FROZEN_COUNT.findall(text) == frozen)

    print("\n" + ("PASS — check_current_state_freshness: CURRENT-STATE.md carries no frozen proof-count (no-magic-values), "
                  "points to the live flywheel signal, and every repo path it cites resolves (no dangling handles) — "
                  "the orientation doc cannot silently rot." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_current_state_freshness.py --self-test")
    raise SystemExit(0)
