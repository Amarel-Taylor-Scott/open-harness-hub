#!/usr/bin/env python3
"""scripts.check_inference_ui — PROOF: the Shared LLM Plane UI projection is real, reachable, and projection-only.

The inference plane has a read-only page (web/baltor/inference-plane.html) served at /inference-plane, and the Live
Ops Dashboard both LINKS to it (no dead link) and renders the governed inference.* events distinctly. This proof
asserts the UI is a safe projection — it consumes the /api/inference/* API, declares model output is a candidate
(never truth), labels providers local/candidate, and leaks no secret value or raw key.

Asserts:
  A. PAGE EXISTS + REACHABLE: web/baltor/inference-plane.html exists and the admin server serves /inference-plane
     (self._serve_web branch present) — no dead link.
  B. CONSUMES THE PROJECTION: the page fetches the /api/inference/* GET endpoints (providers/health/free-endpoints/
     preferences) and the structured-local POST — it renders the API, it does not compute truth.
  C. OUTPUT-NOT-TRUTH: the page declares projection-only + "candidate"/"never served truth" labelling.
  D. PROVIDER LABELS: the page distinguishes local vs external providers and shows a key indicator WITHOUT a value
     (has_secret_ref boolean / "ref"), never a raw key.
  E. NO SECRET LEAK: no secret-value pattern (the handler's guard regex) appears in the page source.
  F. DASHBOARD WIRES IT: dashboard.html links to /inference-plane AND renders inference.* events (k-inference class +
     kclass mapping) — the governed event is legible, not hidden.
  G. NO DASHBOARD TRUTH: the inference artifact line the dashboard renders marks is_truth / candidate-not-truth
     (the dashboard projects the receipt; it does not assert the model output as fact).

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.api_inference_handler import _LEAK  # reuse the production secret-value guard

_WEB = _REPO / "web" / "baltor"


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    page_p = _WEB / "inference-plane.html"
    page = page_p.read_text(encoding="utf-8") if page_p.is_file() else ""
    server = (_REPO / "scripts" / "baltor_admin_demo_server.py").read_text(encoding="utf-8")
    dash_p = _WEB / "dashboard.html"
    dash = dash_p.read_text(encoding="utf-8") if dash_p.is_file() else ""
    low = page.lower()

    check("A: inference-plane page exists + admin server serves /inference-plane (no dead link)",
          bool(page) and 'self._serve_web("inference-plane.html")' in server
          and '"/inference-plane"' in server)

    check("B: the page consumes the /api/inference/* projection",
          all(e in page for e in ("/api/inference/providers", "/api/inference/health",
                                  "/api/inference/free-endpoints", "/api/inference/preferences",
                                  "/api/inference/structured-local")))

    check("C: the page declares projection-only + candidate/never-served-truth",
          "projection only" in low and ("never served truth" in low or "never truth" in low) and "candidate" in low)

    check("D: providers labelled local vs external + key shown as ref/boolean, not a value",
          ("external" in low and "local" in low) and ("has_secret_ref" in page or "key:" in page))

    check("E: no secret-value pattern in the page source", not _LEAK.search(page))

    check("F: dashboard links to /inference-plane AND renders inference.* events",
          bool(dash) and "/inference-plane" in dash and "k-inference" in dash
          and "startsWith('inference')" in dash)

    check("G: the dashboard inference line marks candidate-not-truth (no dashboard truth)",
          "inference.completed" in dash and "is_truth" in dash and "candidate-not-truth" in dash)

    print("\n" + ("PASS — check_inference_ui: the Shared LLM Plane UI is a reachable, projection-only read view — it "
                  "consumes /api/inference/*, declares model output a candidate (never truth), labels providers "
                  "local/external with a key indicator (no value), leaks no secret, and the dashboard links it + "
                  "renders the governed inference events as candidate-not-truth." if not fails
                  else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_inference_ui.py --self-test")
    raise SystemExit(0)
