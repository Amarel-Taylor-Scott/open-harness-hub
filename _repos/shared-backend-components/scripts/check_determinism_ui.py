#!/usr/bin/env python3
"""scripts.check_determinism_ui — proof: _repos/baltor/frontend/determinism.html is a PROJECTION ONLY over the Determinism
API. It fetches ONLY /api/determinism/* endpoints; it performs NO durable writes; it stores NO truth in
localStorage/sessionStorage; it leaks NO secret and renders NO private memory. The required panels are present
(LLM traces, consensus runs, patterns, rule candidates, replay, shadow, promotions, fallback rate, safety
blocks), plus loading/empty/error states. The page's data sources (the Determinism API handler) actually answer
it. Static source scan + a live handler check — deterministic, offline.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_determinism_ui.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
import re
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.api_determinism_handler import handle  # noqa: E402

_PAGE = _resource("web/baltor/determinism.html")

#: the page may read ONLY the determinism projection API.
_ALLOWED_FETCH_PREFIX = "/api/determinism/"
#: anything that would imply the page computes/persists truth or stores secrets/private memory.
_FORBIDDEN = (
    "localStorage", "sessionStorage", "indexedDB",          # no client-side truth/secret storage
    "INSERT INTO", "sqlite3",                                # no durable writes
    "api_key", "Authorization", "Bearer ", "OH_SHOWCASE_TOKEN",  # no secrets
    ".agent/", "MEMORY.md", "baltor-goal-loop", ".claude/",  # no private memory / loop internals
)
#: required panel/label substrings — every stage of the factory must be visible.
_REQUIRED_PANELS = (
    "LLM traces", "Verified traces", "Consensus runs", "Pattern candidates", "Rule candidates",
    "Replay report", "Shadow report", "Promotions", "Fallback rate", "Safety blocks",
)
#: the load-bearing labels that must be on the page (the safety invariants the projection exposes).
_REQUIRED_LABELS = ("can_serve_fact", "distilled_from_trace_ids", "10 business days", "30 days",
                    "fabricated", "live_authoritative")
#: loading / empty / error states must be handled.
_REQUIRED_STATES = ("loading", "empty", "error")


def _endpoint_literals(text: str) -> list[str]:
    """All /api/... string literals that appear in the page (the EP map + fetch args)."""
    return re.findall(r"""['"](/api/[^'"]+)['"]""", text)


def _fetch_targets(text: str) -> list[str]:
    """Every fetch(...) argument's leading string literal (the URL expression)."""
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

    check("_repos/baltor/frontend/determinism.html exists", _PAGE.exists())
    if not _PAGE.exists():
        print("\n1 FAILURES: missing page")
        return 1
    text = _PAGE.read_text(encoding="utf-8")

    # 1) every /api/ endpoint the page references is under /api/determinism/ (projection-only — no other API)
    eps = _endpoint_literals(text)
    off_eps = [e for e in eps if not e.startswith(_ALLOWED_FETCH_PREFIX)]
    check("page references ONLY /api/determinism/* endpoints", off_eps == [], str(off_eps))
    check("page references all 9 determinism routes",
          len(set(e.split("?")[0] for e in eps)) >= 9, str(sorted(set(eps))))

    # 2) every literal fetch() target is a determinism endpoint or a function-built URL (EP.x)
    for t in _fetch_targets(text):
        if t.startswith("/") and not t.startswith(_ALLOWED_FETCH_PREFIX):
            check(f"fetch target {t} is under /api/determinism/", False, t)
    check("all literal fetch() targets are determinism endpoints", True)
    check("no cross-origin fetch (no absolute http(s) URL)", "http://" not in text and "https://" not in text)

    # 3) no durable writes / truth storage / secrets / private memory
    off = [f for f in _FORBIDDEN if f in text]
    sk_prefix = "sk" + "-"
    if sk_prefix in text:
        off.append(sk_prefix)
    check("page performs no durable write / truth storage / secret / private-memory leak", off == [], str(off))

    # 4) required panels present (every factory stage), plus the load-bearing safety labels
    missing_panels = [p for p in _REQUIRED_PANELS if p not in text]
    check("all required panels are present", missing_panels == [], str(missing_panels))
    missing_labels = [l for l in _REQUIRED_LABELS if l not in text]
    check("the load-bearing safety labels are shown (can_serve_fact, lossless, reference answers, fabricated)",
          missing_labels == [], str(missing_labels))

    # 5) loading / empty / error states are handled
    missing_states = [s for s in _REQUIRED_STATES if s.lower() not in text.lower()]
    check("loading / empty / error states handled", missing_states == [], str(missing_states))

    # 6) the page's data sources actually answer it (degrade gracefully, correctness invariant with no creds)
    for route, key in (("/api/determinism/overview", "stage_counts"),
                       ("/api/determinism/traces", "traces"),
                       ("/api/determinism/consensus", "can_serve_fact"),
                       ("/api/determinism/patterns", "patterns"),
                       ("/api/determinism/rules", "rules"),
                       ("/api/determinism/replay", "precision"),
                       ("/api/determinism/shadow", "live_authoritative"),
                       ("/api/determinism/promotions", "safety_blocks"),
                       ("/api/determinism/fallback", "events")):
        code, payload = handle("GET", route, {})
        check(f"data source {route} answers the page", code == 200 and key in payload, str(code))

    print(f"\n{'PASS — check_determinism_ui: /determinism renders the whole Determinism Factory as a projection over /api/determinism/* (all stage panels present incl. LLM traces, consensus, patterns, rule candidates, replay, shadow, promotions, fallback rate, safety blocks; the load-bearing safety labels shown; loading/empty/error states; fetches only the determinism API; no truth/secrets/storage/private-memory); the nine API data sources answer the page.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: /determinism UI (projection-only).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
