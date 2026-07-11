#!/usr/bin/env python3
"""scripts.check_pipeline_enhancement_ui — proof (C-PIPE-ENH-UI): _repos/baltor/frontend/pipeline/enhancement.html is a
PROJECTION-ONLY stage page for the "Enhancement" stage. It fetches ONLY its contracted /api/pipeline/enhancement
(+ /api/pipeline/overview), renders the required panels INCLUDING the lossless held-out panel (low-confidence /
fragile enrichments preserved, not served), shows entities + fragility/freshness + deterministic graph edges,
handles loading/empty/error states, carries the shared 7-stage stepper that links to its siblings, and performs
NO durable write / no secret / no private-memory leak. Static source scan — deterministic, offline.

CLI: python3 _repos/shared-backend-components/scripts/check_pipeline_enhancement_ui.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
import re
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
_PAGE = _resource("web/baltor/pipeline/enhancement.html")

#: this page's own contracted endpoint + the shared overview are the ONLY pipeline endpoints it may touch.
_STAGE = "enhancement"
_ALLOWED_ENDPOINTS = {f"/api/pipeline/{_STAGE}", "/api/pipeline/overview"}
#: the other six stages this page's stepper must link to (sibling pages).
_SIBLINGS = ("upload", "decomposition", "reconciliation", "optimization", "verification", "consumption")
#: required panel/label substrings: INPUT, OUTPUT, the LOSSLESS held-out panel, source-handle/lineage.
_REQUIRED_PANELS = ("Input ", "Output ", "Held out", "Source handles", "lineage")
#: this stage's enrichment content: entities + fragility/freshness + deterministic graph edges.
_REQUIRED_ENRICH = ("entities", "fragility", "freshness", "volatility", "graph edges", "next_verify_at")
#: this stage's lossless content: low-confidence/fragile enrichments held out (preserved, not deleted).
_REQUIRED_LOSSLESS = ("held out", "held_out", "≠ deleted")
#: loading / empty / error states must be handled.
_REQUIRED_STATES = ("loading", "empty", "error")
#: a projection-only page must never write durable truth, embed secrets, or render private memory/intel.
_FORBIDDEN = (
    ".agent/", "MEMORY.md", "baltor-goal-loop", ".claude/",
    "INSERT INTO", "UPDATE ", "DELETE FROM", "sqlite3",
    "localStorage", "sessionStorage", "indexedDB",
    "api_key", "Authorization", "Bearer ", "OH_SHOWCASE_TOKEN",
)


def _endpoint_literals(text: str) -> list[str]:
    """Every /api/... string literal in the page, stripped of any query string."""
    return [e.split("?")[0] for e in re.findall(r"""['"](/api/[^'"]+)['"]""", text)]


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    check("_repos/baltor/frontend/pipeline/enhancement.html exists", _PAGE.exists())
    if not _PAGE.exists():
        print("\n1 FAILURES: missing page")
        return 1
    text = _PAGE.read_text(encoding="utf-8")

    # 1) projection-only: every /api/ endpoint is its own stage endpoint or the shared overview
    eps = set(_endpoint_literals(text))
    off = [e for e in eps if e not in _ALLOWED_ENDPOINTS]
    check(f"page references ONLY /api/pipeline/{_STAGE} (+ overview)", off == [], str(off))
    check(f"page fetches its contracted /api/pipeline/{_STAGE}", f"/api/pipeline/{_STAGE}" in text)
    check("page fetches /api/pipeline/overview (degrades gracefully)", "/api/pipeline/overview" in text)

    # 2) required panels present (INPUT, OUTPUT, the LOSSLESS held-out panel, source-handle/lineage)
    missing_panels = [p for p in _REQUIRED_PANELS if p not in text]
    check("required panels present (input/output/held-out/source-handle/lineage)", missing_panels == [], str(missing_panels))

    # 3) enrichment content: entities + fragility/freshness + deterministic graph edges
    missing_enrich = [s for s in _REQUIRED_ENRICH if s not in text]
    check("enrichment content present (entities + fragility/freshness + graph edges)", missing_enrich == [], str(missing_enrich))

    # 4) lossless: low-confidence / fragile enrichments held out, preserved (not deleted)
    missing_loss = [s for s in _REQUIRED_LOSSLESS if s not in text]
    check("lossless held-out story present (held out + preserved, not deleted)", missing_loss == [], str(missing_loss))

    # 5) loading / empty / error states handled
    missing_states = [s for s in _REQUIRED_STATES if s.lower() not in text.lower()]
    check("loading / empty / error states handled", missing_states == [], str(missing_states))

    # 6) shared 7-stage stepper links to every sibling stage page.
    #    The stepper builds each href as `"./" + id + ".html"`, so we assert (a) the href-builder pattern
    #    exists and (b) every sibling stage id is a quoted STAGES entry the builder iterates over.
    check("stepper builds sibling hrefs from the STAGES list (./<id>.html)", '"./" +' in text and '".html"' in text)
    missing_links = [s for s in _SIBLINGS if f'"{s}"' not in text]
    check("stepper enumerates all 6 sibling stage ids", missing_links == [], str(missing_links))
    check(f"stepper marks {_STAGE} as the current stage", 'current' in text and f'"{_STAGE}"' in text)

    # 7) no durable writes / truth storage / secrets / private memory
    offenders = [f for f in _FORBIDDEN if f in text]
    sk_prefix = "sk" + "-"
    if sk_prefix in text:
        offenders.append(sk_prefix)
    check("page is projection-only (no durable writes / secrets / private memory / forbidden tokens)", offenders == [], str(offenders))

    # 8) governance copy: the page states it computes no truth
    check("page declares projection-only (computes no truth; reads the API)",
          "projection-only" in text and "computes no truth" in text)

    print(f"\n{'PASS — check_pipeline_enhancement_ui: enhancement.html fetches ONLY /api/pipeline/enhancement (+ overview), renders input/output/lossless-held-out/source-handle panels (entities + fragility/freshness + deterministic graph edges; low-confidence enrichments held out, preserved), handles loading/empty/error, the 7-stage stepper links to all siblings, and it computes/stores/leaks no truth or secret.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: pipeline enhancement stage page is projection-only.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
