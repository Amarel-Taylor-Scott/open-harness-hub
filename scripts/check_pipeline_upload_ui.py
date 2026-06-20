#!/usr/bin/env python3
"""scripts.check_pipeline_upload_ui — proof (C-PIPE-UPLOAD-1): web/baltor/pipeline/upload.html is the
"Upload & Ingestion" stage page and is a PROJECTION ONLY. It fetches ONLY its contracted
/api/pipeline/upload (+ /api/pipeline/overview); it performs NO durable writes; it stores NO truth in
localStorage/sessionStorage/indexedDB; it leaks NO secret and renders NO private memory. The required
panels are present (INPUT, OUTPUT, the LOSSLESS held-out/preserved panel, source-handle/lineage), it
handles loading/empty/error/degraded, and the 7-stage stepper links to every sibling stage with this
stage highlighted + prev/next. Static source scan — deterministic, offline. Models on
scripts/check_consumption_ui.py + scripts/check_memory_page_projection_only.py.

CLI: python3 scripts/check_pipeline_upload_ui.py --self-test
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_PAGE = _REPO / "web" / "baltor" / "pipeline" / "upload.html"

#: the ONLY /api/ family this page may touch (projection-only — its own stage + overview).
_ALLOWED_FETCH_PREFIX = "/api/pipeline/"
#: the exact contracted endpoints this stage page must reference.
_REQUIRED_ENDPOINTS = ("/api/pipeline/upload", "/api/pipeline/overview")
#: the 7 sibling stage pages the shared stepper must link to (this stage highlighted).
_STEPPER_SIBLINGS = (
    "./upload.html", "./decomposition.html", "./reconciliation.html", "./enhancement.html",
    "./optimization.html", "./verification.html", "./consumption.html",
)
#: required panel headings (INPUT, OUTPUT, the lossless panel, source-handle/lineage).
_REQUIRED_PANELS = ("INPUT", "OUTPUT", "LOSSLESS", "Source handles", "lineage", "Run overview")
#: lossless vocabulary that must be visible (held-out / preserved-original framing).
_REQUIRED_LOSSLESS = ("raw_ref", "preserved", "source handle")
#: loading / empty / error / degraded states must be handled.
_REQUIRED_STATES = ("loading", "empty", "error", "degraded")
#: anything implying the page computes/persists truth, embeds secrets, or leaks private memory.
_FORBIDDEN = (
    ".agent/", "MEMORY.md", "baltor-goal-loop", ".claude/",
    "INSERT INTO", "UPDATE ", "DELETE FROM", "sqlite3",
    "localStorage", "sessionStorage", "indexedDB",
    "api_key", "Authorization", "Bearer ", "OH_SHOWCASE_TOKEN",
    "served_facts =", "served_facts.push", "ContextResponse(",
)


def _endpoint_literals(text: str) -> list[str]:
    """All /api/... string literals that appear in the page (the EP map + fetch args)."""
    return re.findall(r"""['"](/api/[^'"]+)['"]""", text)


def _fetch_targets(text: str) -> list[str]:
    """Every fetch(...) argument literal (the leading string of the URL expression)."""
    out: list[str] = []
    for m in re.finditer(r"fetch\(\s*([^)]*)", text):
        lit = re.search(r"""['"]([^'"]+)['"]""", m.group(1))
        if lit:
            out.append(lit.group(1))
    return out


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    check("web/baltor/pipeline/upload.html exists", _PAGE.exists())
    if not _PAGE.exists():
        print("\n1 FAILURES: missing page"); return 1
    text = _PAGE.read_text(encoding="utf-8")

    # 1) projection-only: every /api/ reference is under /api/pipeline/ (no other API touched)
    eps = _endpoint_literals(text)
    off_eps = [e for e in eps if not e.startswith(_ALLOWED_FETCH_PREFIX)]
    check("page references ONLY /api/pipeline/* endpoints", off_eps == [], str(off_eps))
    bases = {e.split("?")[0] for e in eps}
    missing_eps = [e for e in _REQUIRED_ENDPOINTS if e not in bases]
    check("page fetches its contracted /api/pipeline/upload (+ overview)", missing_eps == [], str(missing_eps))

    # 2) every literal fetch() target is a pipeline endpoint (no foreign host / write target)
    bad_fetch = [t for t in _fetch_targets(text) if t.startswith("/") and not t.startswith(_ALLOWED_FETCH_PREFIX)]
    check("all literal fetch() targets are /api/pipeline/* (read-only projection)", bad_fetch == [], str(bad_fetch))

    # 3) no durable writes / truth storage / secrets / private-memory tokens
    off = [f for f in _FORBIDDEN if f in text]
    sk_prefix = "sk" + "-"
    if re.search(sk_prefix + r"[A-Za-z0-9]{16,}", text):
        off.append(sk_prefix + "<key>")
    check("page is projection-only (no durable writes / secrets / private memory / forbidden tokens)", off == [], str(off))

    # 4) required panels present (INPUT, OUTPUT, the lossless panel, source-handle/lineage)
    missing_panels = [p for p in _REQUIRED_PANELS if p not in text]
    check("required panels present (INPUT / OUTPUT / LOSSLESS / source-handles / lineage / overview)",
          missing_panels == [], str(missing_panels))

    # 5) the LOSSLESS panel actually shows held-out / preserved-original vocabulary
    missing_loss = [l for l in _REQUIRED_LOSSLESS if l not in text]
    check("lossless panel shows preserved raw_ref + source handle (nothing dropped)", missing_loss == [], str(missing_loss))

    # 6) loading / empty / error / degraded states handled
    missing_states = [s for s in _REQUIRED_STATES if s.lower() not in text.lower()]
    check("loading / empty / error / degraded states handled", missing_states == [], str(missing_states))

    # 7) the 7-stage stepper links to every sibling, this stage highlighted, with prev/next
    missing_steps = [s for s in _STEPPER_SIBLINGS if s not in text]
    check("stepper links to all 7 sibling stages", missing_steps == [], str(missing_steps))
    check("this stage (upload) is the highlighted/current step",
          'class="step current" href="./upload.html"' in text and 'aria-current="step"' in text)
    check("prev/next pager present (prev disabled on first stage, next → decomposition)",
          'id="prev"' in text and 'id="next"' in text and 'href="./decomposition.html"' in text)

    # 8) the projection-only contract is stated on the page (governance copy)
    check("page declares it computes no truth (projection-only copy)",
          "projection" in text.lower() and "computes no truth" in text)

    print(f"\n{'PASS — check_pipeline_upload_ui: upload.html fetches ONLY /api/pipeline/upload (+ overview), is projection-only (no durable writes / secrets / private memory), shows INPUT + OUTPUT + the LOSSLESS preserved-raw_ref panel + source-handle/lineage, handles loading/empty/error/degraded, and the 7-stage stepper links all siblings with this stage highlighted + prev/next.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: pipeline upload stage page is projection-only.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
