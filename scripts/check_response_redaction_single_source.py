#!/usr/bin/env python3
"""scripts.check_response_redaction_single_source — PROOF: the API handlers' secret-redaction
allow-list is SINGLE-SOURCED in scripts/security/response_redaction.py, never re-declared per handler.

Seven api_*_handler.py files each used to define their own ``_SECRET_MARKERS`` tuple, and the copies
DRIFTED — some lacked ``Bearer `` (would pass a raw bearer token), some lacked ``.claude/``. A redaction
allow-list that disagrees with itself is a security hole AND the canonical no-magic-values bug. This
gate fails if any api_*_handler.py re-declares the tuple instead of importing the single source.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_HANDLERS = sorted((_REPO / "scripts").glob("api_*_handler.py"))
_REDECLARE = re.compile(r"^_SECRET_MARKERS\s*=\s*\(", re.M)  # a literal re-declaration (not `import ... as`)
_CANONICAL_IMPORT = "from scripts.security.response_redaction import"


def _self_test() -> int:
    from scripts.security.response_redaction import SECRET_MARKERS

    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # 1. the canonical allow-list carries every security-critical token (the superset)
    for marker in ("OH_SHOWCASE_TOKEN", "sk-", "api_key", "Authorization", "Bearer ", "MEMORY.md", ".agent/", ".claude/"):
        ck(f"canonical SECRET_MARKERS includes {marker!r}", marker in SECRET_MARKERS)

    # 2. no api_*_handler RE-DECLARES its own _SECRET_MARKERS tuple (must import the single source)
    redeclarers = [h.name for h in _HANDLERS if _REDECLARE.search(h.read_text(encoding="utf-8"))]
    ck("no api_*_handler re-declares _SECRET_MARKERS (single-sourced, no drift)", not redeclarers, str(redeclarers))

    # 3. every handler that USES _SECRET_MARKERS imports it from the canonical module
    not_importing = [h.name for h in _HANDLERS
                     if "_SECRET_MARKERS" in (txt := h.read_text(encoding="utf-8")) and _CANONICAL_IMPORT not in txt]
    ck("every handler using _SECRET_MARKERS imports the canonical module", not not_importing, str(not_importing))

    print(("PASS — " if not fails else "FAIL — ")
          + f"response-redaction allow-list single-sourced across {len(_HANDLERS)} api_*_handler.py files "
            f"({len(SECRET_MARKERS)} canonical markers; no per-handler drift).")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
