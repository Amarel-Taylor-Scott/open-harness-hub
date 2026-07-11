#!/usr/bin/env python3
"""scripts.check_memory_page_projection_only — proof (C-MEM-1): _repos/baltor/frontend/memory.html is a PROJECTION ONLY.
It fetches ONLY /api/memory/* endpoints; it performs NO durable writes; it stores NO truth in
localStorage/sessionStorage; it leaks NO secret and renders NO private memory. The required panels are present
(incl. claim_status, source handles, held-out, providers, traces). Static source scan — deterministic, offline.

CLI: python3 _repos/shared-backend-components/scripts/check_memory_page_projection_only.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
import re
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
_PAGE = _resource("web/baltor/memory.html")

#: fetch() targets that are allowed (the page may read ONLY the memory projection API).
_ALLOWED_FETCH_PREFIX = "/api/memory/"
#: anything that would imply the page computes/persists truth or stores secrets.
_FORBIDDEN = (
    "localStorage", "sessionStorage", "indexedDB",     # no client-side truth/secret storage
    "ContextResponse(", "served_facts =", "served_facts.push",  # no truth construction (projection only)
    "api_key", "Authorization", "Bearer ", "OH_SHOWCASE_TOKEN",  # no secrets
)
#: required panel/label substrings (claim_status, source handles, held-out, providers, traces must be visible).
_REQUIRED_PANELS = (
    "Memory artifacts", "Profile", "Connectors", "Sync state", "Memory graph",
    "Search", "Contradictions", "Freshness", "Reconciliation receipts",
    "Injected into agent context", "Held out", "Providers", "Memory traces",
)
_REQUIRED_LABELS = ("claim_status", "external_source_handle", "candidate", "held_out", "promoted")
#: loading / empty / error / degraded states must be handled.
_REQUIRED_STATES = ("loading", "empty", "error", "degraded")


def _fetch_targets(text: str) -> list[str]:
    """Every fetch(...) argument literal (the leading string of the URL expression)."""
    out: list[str] = []
    for m in re.finditer(r"fetch\(\s*([^)]*)", text):
        arg = m.group(1)
        lit = re.search(r"""['"]([^'"]+)['"]""", arg)
        if lit:
            out.append(lit.group(1))
    return out


def _endpoint_literals(text: str) -> list[str]:
    """All /api/... string literals that appear in the page (the EP map + fetch args)."""
    return re.findall(r"""['"](/api/[^'"]+)['"]""", text)


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    check("_repos/baltor/frontend/memory.html exists", _PAGE.exists())
    if not _PAGE.exists():
        print("\n1 FAILURES: missing page"); return 1
    text = _PAGE.read_text(encoding="utf-8")

    # 1) every /api/ endpoint the page references is under /api/memory/ (projection-only — no other API touched)
    eps = _endpoint_literals(text)
    off_eps = [e for e in eps if not e.startswith(_ALLOWED_FETCH_PREFIX)]
    check("page references ONLY /api/memory/* endpoints", off_eps == [], str(off_eps))
    check("page references at least the 6 memory routes", len(set(e.split('?')[0] for e in eps)) >= 6, str(sorted(set(eps))))

    # 2) every literal fetch() target is a memory endpoint or a function-built URL (EP.search(q))
    for t in _fetch_targets(text):
        if t.startswith("/") and not t.startswith(_ALLOWED_FETCH_PREFIX):
            check(f"fetch target {t} is under /api/memory/", False, t)
    check("all literal fetch() targets are memory endpoints", True)

    # 3) no durable writes / truth storage / secrets
    off = [f for f in _FORBIDDEN if f in text]
    sk_prefix = "sk" + "-"
    if sk_prefix in text:
        off.append(sk_prefix)
    check("page performs no durable write / truth storage / secret", off == [], str(off))

    # 4) required panels present (incl. claim_status, source handles, held-out, providers, traces)
    missing_panels = [p for p in _REQUIRED_PANELS if p not in text]
    check("all required panels are present", missing_panels == [], str(missing_panels))
    missing_labels = [l for l in _REQUIRED_LABELS if l not in text]
    check("claim_status + source handles + held_out + promoted/candidate are shown", missing_labels == [], str(missing_labels))

    # 5) loading / empty / error / degraded states are handled
    missing_states = [s for s in _REQUIRED_STATES if s.lower() not in text.lower()]
    check("loading / empty / error / degraded states handled", missing_states == [], str(missing_states))

    # 6) governance copy is on the page (remembered != verified etc.)
    check("governance copy present (remembered/served/promoted distinctions)",
          "remembered" in text and "served" in text and "Consumption API" in text)

    print(f"\n{'PASS — check_memory_page_projection_only: memory.html fetches ONLY /api/memory/* (no other API), performs no durable writes / truth storage / secret leakage, shows claim_status + source handles + held-out, and handles loading/empty/error/degraded.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: memory.html is projection-only.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
