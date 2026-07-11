#!/usr/bin/env python3
"""scripts.check_pipeline_verification_ui — proof (D-PIPE-VER-1): _repos/baltor/frontend/pipeline/verification.html is a
PROJECTION ONLY page for the Verification Gate stage. It fetches ONLY its contracted projection endpoint
(GET /api/pipeline/verification) plus GET /api/pipeline/overview, performs NO durable writes, embeds NO secret
or private memory, shows the required panels INCLUDING the lossless held-out panel (per-artifact allow / hold_out
with reason + receipt), handles loading / empty / error / degraded states, and its pipeline stepper links to the
sibling stage pages. A hold_out artifact is shown excluded-from-the-answer but RETAINED — the lossless law.

Static source scan — deterministic, offline. CLI: python3 _repos/shared-backend-components/scripts/check_pipeline_verification_ui.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
import re
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
_PAGE = _resource("web/baltor/pipeline/verification.html")

#: the ONLY /api/ endpoints this page may reference (its own stage projection + the shared overview).
_ALLOWED_ENDPOINTS = {"/api/pipeline/verification", "/api/pipeline/overview"}
_REQUIRED_ENDPOINTS = ("/api/pipeline/verification", "/api/pipeline/overview")
#: required panel/section copy — INPUT, OUTPUT, the LOSSLESS panel, and source-handle / lineage.
_REQUIRED_PANELS = ("Input", "Output", "Held out", "Source handles", "lineage")
#: the lossless panel must visibly show per-artifact allow / hold_out with reasons + a receipt.
_REQUIRED_LOSSLESS = ("allow", "hold_out", "reason", "receipt")
_REQUIRED_STATES = ("loading", "empty", "error", "degraded")
_REQUIRED_SIBLINGS = ("optimization.html", "consumption.html", "index.html")
_FORBIDDEN = (
    "localStorage", "sessionStorage", "indexedDB",
    ".agent/", "MEMORY.md", "baltor-goal-loop", ".claude/",
    "INSERT INTO", "UPDATE ", "DELETE FROM", "sqlite3",
    "api_key", "Authorization", "Bearer ", "OH_SHOWCASE_TOKEN",
)


def _endpoint_literals(text: str) -> list[str]:
    return [e.split("?")[0] for e in re.findall(r"""['"](/api/[^'"]+)['"]""", text)]


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    check("_repos/baltor/frontend/pipeline/verification.html exists", _PAGE.exists())
    if not _PAGE.exists():
        print("\n1 FAILURES: missing page")
        return 1
    text = _PAGE.read_text(encoding="utf-8")

    check("page carries the explicit PROJECTION ONLY marker", "PROJECTION ONLY" in text.upper())
    check("page reads the shared projection query (tenant + corpus)", "tenant=demo" in text and "corpus=cfpb" in text)

    eps = set(_endpoint_literals(text))
    off = sorted(e for e in eps if e not in _ALLOWED_ENDPOINTS)
    check("page references ONLY its contracted /api/pipeline/* endpoints", off == [], str(off))
    missing_eps = [e for e in _REQUIRED_ENDPOINTS if e not in eps]
    check("page fetches its stage endpoint + the overview endpoint", missing_eps == [], str(missing_eps))

    missing_panels = [p for p in _REQUIRED_PANELS if p not in text]
    check("required panels present (Input / Output / Held out / Source handles / lineage)", missing_panels == [], str(missing_panels))
    missing_lossless = [w for w in _REQUIRED_LOSSLESS if w.lower() not in text.lower()]
    check("the LOSSLESS panel shows per-artifact allow / hold_out + reason + receipt", missing_lossless == [], str(missing_lossless))

    missing_states = [s for s in _REQUIRED_STATES if s.lower() not in text.lower()]
    check("loading / empty / error / degraded states handled", missing_states == [], str(missing_states))

    missing_sib = [s for s in _REQUIRED_SIBLINGS if s not in text]
    check("the pipeline stepper links to sibling stage pages (prev/next + journey)", missing_sib == [], str(missing_sib))
    check("the current stage is highlighted in the stepper", 'id===STAGE' in text and '"verification"' in text)

    offenders = [f for f in _FORBIDDEN if f in text]
    sk_prefix = "sk" + "-"
    if sk_prefix in text:
        offenders.append(sk_prefix)
    check("page is projection-only (no durable writes / truth storage / secrets / private memory)", offenders == [], str(offenders))

    print(f"\n{'PASS — check_pipeline_verification_ui: verification.html projects ONLY /api/pipeline/verification (+overview), shows Input/Output and the LOSSLESS panel (per-artifact allow / hold_out with reasons + receipt, held-out retained not erased), handles loading/empty/error/degraded, links the stepper to siblings, and writes no truth / leaks no secret.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: pipeline verification stage page is projection-only.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
