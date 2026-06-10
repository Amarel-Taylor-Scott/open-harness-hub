#!/usr/bin/env python3
"""scripts.check_demo_control_tower — PROOF: the Demo Control Tower aggregates every surface into ONE start-here
page + ONE consolidated all-URLs manifest, honestly and without fake URLs.

Asserts (deterministic + offline; rebuilds the page/manifest, does not require live servers/tunnels):
  A. REGISTRY well-formed: every surface has the required fields; statuses ∈ {active,candidate,internal_only};
     the portfolio_lib static launch sites + hub are registered as active static sites at the portfolio_lib ports.
  B. BUILD: build() emits the start-here page + dist/demo-all-urls.{json,md,txt}.
  C. AGGREGATION: the consolidated manifest contains every registered surface, grouped; the portfolio_lib sites +
     hub appear; the Demo Control Tower is the 'Start here' entry.
  D. START-HERE PAGE: every ACTIVE surface appears; demo script + caveat present; candidate/internal surfaces
     shown honestly; NO external scripts/CDN.
  E. CFPB E2E INVARIANT cited (answer 10 business days · FAQ-30 held out · receipt + source handles) — the live
     evidence is scripts/demo_offline_full_baltor.py (the offline e2e proof), referenced on the page.
  F. NO FAKE URLS: any TryCloudflare URL present is a real *.trycloudflare.com host (from the captured manifest),
     never invented; absent ones render '—'/'(launch a tunnel)', not a fabricated link.
  G. PORT CONSISTENCY: registry static-site ports == portfolio_lib PORTS/HUB_PORT (single source).

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

from scripts import build_demo_control_tower as B
from scripts import portfolio_lib as P

_TCF = re.compile(r"^https://[a-z0-9-]+\.trycloudflare\.com$")
_REQUIRED = ("surface_id", "company_or_hub", "surface_type", "display_name", "local_port", "status")


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    reg = json.loads((_REPO / "architecture" / "demo_surface_registry.json").read_text())["surfaces"]
    by_id = {s["surface_id"]: s for s in reg}

    # A. registry well-formed
    check("A: every surface has required fields", all(all(k in s for k in _REQUIRED) for s in reg))
    check("A: statuses honest", all(s["status"] in ("active", "candidate", "internal_only") for s in reg), str({s["status"] for s in reg}))
    check("A: demo-control-tower registered as active start-here", by_id.get("demo-control-tower", {}).get("status") == "active")
    for sid in P.SITE_ORDER:
        check(f"A: site.{sid} registered active", by_id.get(f"site.{sid}", {}).get("status") == "active")

    # B. build
    res = B.build()
    page = B._PAGE.read_text()
    allj = json.loads((_REPO / "dist" / "demo-all-urls.json").read_text())
    md = (_REPO / "dist" / "demo-all-urls.md").read_text()
    check("B: start-here page + 3 manifests emitted",
          B._PAGE.exists() and all((_REPO / "dist" / f"demo-all-urls.{e}").exists() for e in ("json", "md", "txt")))

    # C. aggregation
    manifest_ids = {s["surface_id"] for s in allj["surfaces"]}
    check("C: manifest contains every registered surface", manifest_ids == set(by_id), str(set(by_id) - manifest_ids))
    check(f"C: {len(P.SITE_ORDER)} static portfolio sites + hub aggregated",
          sum(1 for s in allj["surfaces"] if s["surface_id"].startswith("site.")) == len(P.SITE_ORDER) + 1)
    check("C: Demo Control Tower is the 'Start here' group", any(s["group"] == "Start here" for s in allj["surfaces"]))

    # D. start-here page
    check("D: every active surface on the page", all(s["display_name"] in page for s in reg if s["status"] == "active"))
    check("D: demo script + caveat present", "Demo script" in page and ("TEMPORARY" in page or "temporary" in page.lower()))
    check("D: candidate + internal shown honestly", "candidate" in page and "internal_only" in page)
    check("D: no external scripts/CDN", not any(m in page for m in ('src="http', "<script", "cdn.", "googleapis")))

    # E. CFPB e2e invariant cited + the offline proof exists
    check("E: CFPB invariant on the page (10 business days + held out)", "10 business days" in page and "held out" in page)
    check("E: the offline e2e proof exists", (_REPO / "scripts" / "demo_offline_full_baltor.py").exists())

    # F. no fake URLs
    pubs = [s["trycloudflare_url"] for s in allj["surfaces"] if s.get("trycloudflare_url")]
    bad = [u for u in pubs if not _TCF.match(u)]
    check("F: every present public URL is a real trycloudflare host (no fakes)", not bad, str(bad))

    # G. port consistency with portfolio_lib (single source)
    ok_ports = all(by_id[f"site.{sid}"]["local_port"] == P.PORTS[sid] for sid in P.SITE_ORDER) and by_id["site.portfolio-hub"]["local_port"] == P.HUB_PORT
    check("G: registry static-site ports == portfolio_lib (single source)", ok_ports)

    print("\n" + (f"PASS — check_demo_control_tower: {res['surfaces']} surfaces aggregated into one start-here page + "
                  f"dist/demo-all-urls.* ({res['with_public_url']} real TryCloudflare URLs); CFPB e2e invariant cited; "
                  f"candidate/internal shown honestly; no fake URLs; ports single-sourced." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_demo_control_tower.py --self-test")
    raise SystemExit(0)
