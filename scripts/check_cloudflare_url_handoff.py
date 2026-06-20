#!/usr/bin/env python3
"""scripts.check_cloudflare_url_handoff — PROOF (consolidated): the Cloudflare URL handoff inventory + handoff
Markdown + one-by-one review checklist + review state + rubric scorecard are well-formed, honest, and contain no
fake URLs.

Deterministic + offline: rebuilds the inventory WITHOUT live HTTP (do_verify=False) and validates the rendered
artifacts (the live verification is done by cloudflare_handoff.py --run). Asserts:
  A. inventory built; every surface has local and/or cloudflare URL or is honestly missing/candidate.
  B. NO FAKE URLs: every cloudflare_url is a real *.trycloudflare.com host (or absent).
  C. handoff MD (dist/cloudflare-urls.md): status section, grouped tables, caveats (temporary/not-production).
  D. review checklist: one '## Review NN' section per reviewable URL; the Baltor specifics include
     '10 business days' + 'held out' + receipt + source handles.
  E. review state (.agent/cloudflare-url-review-state.json): total_reviews == reviewable; each review has order/
     surface/urls/status.
  F. rubric scorecard (md+json) present with the 9 rubrics; screenshot availability honestly 'partial'
     (Playwright unavailable).
  G. review CLI exists + self-tests.
  H. all required output files exist.

Exit 0/1.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts import cloudflare_handoff as H

_TCF = re.compile(r"^https://[a-z0-9-]+\.trycloudflare\.com")
_DIST = _REPO / "dist"
_NOW = "2026-06-06T00:00:00Z"


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    # rebuild deterministically (no network) into a TEMP dir so the flywheel proof NEVER clobbers the live
    # verified deliverable in dist/ (that is produced by `cloudflare_handoff.py --run`).
    import tempfile
    tmp = Path(tempfile.mkdtemp(prefix="cf-handoff-proof-"))
    _orig_dist, _orig_state = H._DIST, H._STATE
    H._DIST, H._STATE = tmp, tmp / "review-state.json"
    try:
        H.run(_NOW, do_verify=False)
        inv = json.loads((tmp / "cloudflare-url-inventory.json").read_text())
        globals()["_DIST"] = tmp  # the rest of this proof validates the temp render
        globals()["_STATE_FILE"] = tmp / "review-state.json"
    finally:
        H._DIST, H._STATE = _orig_dist, _orig_state
    surfaces = inv["surfaces"]
    reviewable = [s for s in surfaces if s.get("review_order")]

    # A
    check("A: inventory has surfaces", len(surfaces) >= 8)
    check("A: each surface has a URL or is missing/candidate",
          all(s["local_url"] or s["cloudflare_url"] or s["health_status"] in ("missing", "candidate") for s in surfaces))

    # B no fake URLs
    bad = [s["cloudflare_url"] for s in surfaces if s["cloudflare_url"] and not _TCF.match(s["cloudflare_url"])]
    check("B: no fake cloudflare URLs (real *.trycloudflare.com only)", not bad, str(bad))

    # C handoff MD
    urls_md = (_DIST / "cloudflare-urls.md").read_text()
    check("C: handoff MD has status + caveats", "## Status" in urls_md and "## Caveats" in urls_md and "not production hosting" in urls_md)
    check("C: handoff MD groups Start Here + Portfolio", "## Start Here" in urls_md and "## Portfolio websites" in urls_md)

    # D checklist one-section-per-URL + CFPB specifics
    ck = (_DIST / "cloudflare-url-review-checklist.md").read_text()
    n_sections = ck.count("## Review ")
    check("D: one '## Review NN' per reviewable URL", n_sections == len(reviewable), f"{n_sections} vs {len(reviewable)}")
    check("D: Baltor CFPB specifics present (10 business days, held out, receipt, source handles)",
          "10 business days" in ck and "held out" in ck and "Receipt" in ck and "Source handles" in ck)

    # E review state (from the temp render — non-destructive)
    st = json.loads(globals()["_STATE_FILE"].read_text())
    check("E: state total_reviews == reviewable", st["total_reviews"] == len(reviewable))
    check("E: each review has order/surface/urls/status",
          all(all(k in r for k in ("review_order", "surface_id", "cloudflare_url", "local_url", "status")) for r in st["reviews"]))

    # F rubric scorecard
    sc = json.loads((_DIST / "cloudflare-url-rubric-scorecard.json").read_text())
    check("F: scorecard has 9 rubrics", len(sc["rubrics"]) == 9, str(len(sc["rubrics"])))
    check("F: screenshot availability honestly 'partial'", sc["rubrics"]["screenshot_availability"] == "partial")
    check("F: scorecard md present", (_DIST / "cloudflare-url-rubric-scorecard.md").exists())

    # G review CLI
    check("G: one-by-one review CLI exists", (_REPO / "scripts" / "review_cloudflare_urls_one_by_one.py").exists())

    # H required outputs
    for f in ("cloudflare-url-inventory.json", "cloudflare-urls.md", "cloudflare-url-review-checklist.md",
              "cloudflare-url-rubric-scorecard.md", "cloudflare-url-review-progress.md"):
        check(f"H: dist/{f} exists", (_DIST / f).exists())

    print("\n" + ("PASS — check_cloudflare_url_handoff: inventory + handoff MD + one-by-one checklist + review state "
                  "+ rubric scorecard are well-formed; no fake URLs; CFPB specifics present; screenshots honestly "
                  "partial; review CLI present." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_cloudflare_url_handoff.py --self-test")
    raise SystemExit(0)
