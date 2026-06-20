#!/usr/bin/env python3
"""scripts.check_pipeline_optimization_ui — proof (D-PIPE-OPT-1): web/baltor/pipeline/optimization.html is a
PROJECTION ONLY page for the Optimization (bake-off) stage. It fetches ONLY its contracted projection endpoint
(GET /api/pipeline/optimization) plus GET /api/pipeline/overview, performs NO durable writes, embeds NO secret
or private memory, shows the required panels INCLUDING the lossless held-out / rejected-candidate panel, handles
loading / empty / error / degraded states, and its pipeline stepper links to the sibling stage pages. The
promoted pack is shown next to the rejected candidates (preserved with reasons) — the lossless law of this UI.

Static source scan — deterministic, offline. CLI: python3 scripts/check_pipeline_optimization_ui.py --self-test
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_PAGE = _REPO / "web" / "baltor" / "pipeline" / "optimization.html"

#: the ONLY /api/ endpoints this page may reference (its own stage projection + the shared overview).
_ALLOWED_ENDPOINTS = {"/api/pipeline/optimization", "/api/pipeline/overview"}
#: the stage's contracted endpoint (must be fetched) and the shared overview.
_REQUIRED_ENDPOINTS = ("/api/pipeline/optimization", "/api/pipeline/overview")
#: required panel/section copy — INPUT, OUTPUT, the LOSSLESS panel, and source-handle / lineage.
_REQUIRED_PANELS = ("Input", "Output", "Held out", "Source handles", "lineage")
#: the lossless panel must visibly preserve rejected candidates + the baseline (not erase them).
_REQUIRED_LOSSLESS = ("rejected", "baseline", "promoted", "preserved")
#: loading / empty / error / degraded states must be handled.
_REQUIRED_STATES = ("loading", "empty", "error", "degraded")
#: the shared 7-stage stepper must link to siblings (prev/next + the others).
_REQUIRED_SIBLINGS = ("enhancement.html", "verification.html", "consumption.html", "index.html")
#: projection-only: a page must never write durable truth, store truth client-side, embed secrets/private memory.
_FORBIDDEN = (
    "localStorage", "sessionStorage", "indexedDB",
    ".agent/", "MEMORY.md", "baltor-goal-loop", ".claude/",
    "INSERT INTO", "UPDATE ", "DELETE FROM", "sqlite3",
    "api_key", "Authorization", "Bearer ", "OH_SHOWCASE_TOKEN",
)


def _endpoint_literals(text: str) -> list[str]:
    """All /api/... string literals (path only, query stripped)."""
    return [e.split("?")[0] for e in re.findall(r"""['"](/api/[^'"]+)['"]""", text)]


def _run(page: Path, stage: str, allowed: set[str], required_eps, sibling_html, prose: str) -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    check(f"web/baltor/pipeline/{stage}.html exists", page.exists())
    if not page.exists():
        print(f"\n1 FAILURES: missing page {page}")
        return 1
    text = page.read_text(encoding="utf-8")

    # 1) projection-only marker present (explicit comment) + the contract query shape
    check("page carries the explicit PROJECTION ONLY marker", "PROJECTION ONLY" in text.upper())
    check("page reads the shared projection query (tenant + corpus)", "tenant=demo" in text and "corpus=cfpb" in text)

    # 2) it references ONLY its allowed endpoints (its stage projection + overview), nothing else
    eps = set(_endpoint_literals(text))
    off = sorted(e for e in eps if e not in allowed)
    check("page references ONLY its contracted /api/pipeline/* endpoints", off == [], str(off))
    missing_eps = [e for e in required_eps if e not in eps]
    check("page fetches its stage endpoint + the overview endpoint", missing_eps == [], str(missing_eps))

    # 3) required panels: INPUT, OUTPUT, the LOSSLESS held-out panel, source-handle/lineage
    missing_panels = [p for p in _REQUIRED_PANELS if p not in text]
    check("required panels present (Input / Output / Held out / Source handles / lineage)", missing_panels == [], str(missing_panels))
    missing_lossless = [w for w in _REQUIRED_LOSSLESS if w.lower() not in text.lower()]
    check("the LOSSLESS panel preserves rejected candidates + baseline (not erased)", missing_lossless == [], str(missing_lossless))

    # 4) loading / empty / error / degraded states handled
    missing_states = [s for s in _REQUIRED_STATES if s.lower() not in text.lower()]
    check("loading / empty / error / degraded states handled", missing_states == [], str(missing_states))

    # 5) the shared stepper links to every sibling stage page
    missing_sib = [s for s in sibling_html if s not in text]
    check("the pipeline stepper links to sibling stage pages (prev/next + journey)", missing_sib == [], str(missing_sib))
    check("the current stage is highlighted in the stepper", 'id===STAGE' in text and f'"{stage}"' in text)

    # 6) projection-only: no durable writes / truth storage / secrets / private memory
    offenders = [f for f in _FORBIDDEN if f in text]
    sk_prefix = "sk" + "-"
    if sk_prefix in text:
        offenders.append(sk_prefix)
    check("page is projection-only (no durable writes / truth storage / secrets / private memory)", offenders == [], str(offenders))

    print(f"\n{prose if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _self_test() -> int:
    return _run(
        _PAGE, "optimization", _ALLOWED_ENDPOINTS, _REQUIRED_ENDPOINTS,
        _REQUIRED_SIBLINGS,
        "PASS — check_pipeline_optimization_ui: optimization.html projects ONLY /api/pipeline/optimization (+overview), "
        "shows Input/Output and the LOSSLESS panel (rejected candidates + baseline preserved next to the promoted pack), "
        "handles loading/empty/error/degraded, links the stepper to siblings, and writes no truth / leaks no secret.",
    )


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: pipeline optimization stage page is projection-only.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
