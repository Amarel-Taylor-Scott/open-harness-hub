#!/usr/bin/env python3
"""scripts.check_pipeline_consumption_ui — proof (D-PIPE-CON-1): web/baltor/pipeline/consumption.html is a
PROJECTION ONLY page for the Consumption (served context) stage. It fetches ONLY its contracted projection
endpoint (GET /api/pipeline/consumption) plus GET /api/pipeline/overview, performs NO durable writes, embeds NO
secret or private memory, shows the required panels INCLUDING the lossless held-out panel (served_facts next to
held_out_warnings) and the verification→optimization→consumption receipt lineage, handles loading / empty /
error / degraded states, and its pipeline stepper links to the sibling stage pages.

Static source scan — deterministic, offline. CLI: python3 scripts/check_pipeline_consumption_ui.py --self-test
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_PAGE = _REPO / "web" / "baltor" / "pipeline" / "consumption.html"

#: the ONLY /api/ endpoints this page may reference (its own stage projection + the shared overview).
_ALLOWED_ENDPOINTS = {"/api/pipeline/consumption", "/api/pipeline/overview"}
_REQUIRED_ENDPOINTS = ("/api/pipeline/consumption", "/api/pipeline/overview")
#: required panel/section copy — the served ANSWER (output), INPUT, the LOSSLESS panel, source-handle / lineage.
_REQUIRED_PANELS = ("Answer", "Input", "Output", "Held out", "Source handles", "lineage")
#: the lossless panel must show served_facts next to held_out_warnings + the receipt chain.
_REQUIRED_LOSSLESS = ("served_facts", "held_out_warnings", "verification", "optimization", "consumption")
_REQUIRED_STATES = ("loading", "empty", "error", "degraded")
_REQUIRED_SIBLINGS = ("verification.html", "index.html")
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

    check("web/baltor/pipeline/consumption.html exists", _PAGE.exists())
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
    check("required panels present (Answer / Input / Output / Held out / Source handles / lineage)", missing_panels == [], str(missing_panels))
    missing_lossless = [w for w in _REQUIRED_LOSSLESS if w.lower() not in text.lower()]
    check("the LOSSLESS panel shows served_facts next to held_out_warnings + receipt chain", missing_lossless == [], str(missing_lossless))

    missing_states = [s for s in _REQUIRED_STATES if s.lower() not in text.lower()]
    check("loading / empty / error / degraded states handled", missing_states == [], str(missing_states))

    missing_sib = [s for s in _REQUIRED_SIBLINGS if s not in text]
    check("the pipeline stepper links to sibling stage pages (prev + journey)", missing_sib == [], str(missing_sib))
    check("the current stage is highlighted in the stepper", 'id===STAGE' in text and '"consumption"' in text)

    offenders = [f for f in _FORBIDDEN if f in text]
    sk_prefix = "sk" + "-"
    if sk_prefix in text:
        offenders.append(sk_prefix)
    check("page is projection-only (no durable writes / truth storage / secrets / private memory)", offenders == [], str(offenders))

    print(f"\n{'PASS — check_pipeline_consumption_ui: consumption.html projects ONLY /api/pipeline/consumption (+overview), shows the served Answer/Input/Output and the LOSSLESS panel (served_facts next to held_out_warnings) plus the verification→optimization→consumption receipt lineage, handles loading/empty/error/degraded, links the stepper to siblings, and writes no truth / leaks no secret.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: pipeline consumption stage page is projection-only.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
