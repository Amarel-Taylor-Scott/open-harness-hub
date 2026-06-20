#!/usr/bin/env python3
"""scripts.build_portfolio_sites — render the static portfolio launch sites (+ optional hub) from the single source
(scripts/portfolio_lib.py) into dist/portfolio-public/<site>/index.html. Local CSS only; no external CDN/JS/secrets.

Reuses websites/<site>/ content when present (writes an editable content.md mirror on first build). Idempotent +
deterministic. --self-test builds and asserts all outputs exist, carry their required phrases, and contain no
external script/CDN reference.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import portfolio_lib as P

_WEB = P.REPO / "websites"
_BUILD_MANIFEST = P.REPO / "dist" / "portfolio-sites-build.json"
_EXTERNAL_MARKERS = ('src="http', "src='http", 'href="http', "href='http", "cdn.", "<script", "googleapis",
                     "analytics", "gtag(")


def _ensure_website_source(site_id: str, s: dict) -> None:
    d = _WEB / site_id
    d.mkdir(parents=True, exist_ok=True)
    md = d / "content.md"
    if not md.exists():  # reuse if present; only generate when absent
        md.write_text(
            f"# {s['title']}\n\n> {s['one_liner']}\n\n**Kind:** {s['kind']}\n\n**Audience:** {s['audience']}\n\n"
            f"## What it is\n" + "".join(f"- {x}\n" for x in s["what_it_is"]) +
            f"\n## What it is not\n" + "".join(f"- {x}\n" for x in s["what_it_is_not"]) +
            f"\n## Owns\n" + "".join(f"- {x}\n" for x in s["owns"]) +
            f"\n## Does not own\n" + "".join(f"- {x}\n" for x in s["not_owns"]) +
            f"\n## Relationship\n{s['relationship']}\n\n*Canonical source: scripts/portfolio_lib.py (edit there; "
            f"this mirror is for human review).*\n", encoding="utf-8")


def build_all() -> dict:
    results: dict = {"sites": {}, "external_script_refs": 0, "schema_version": "portfolio-sites-build.v1"}
    for site_id in P.SITE_ORDER:
        s = P.SITES[site_id]
        _ensure_website_source(site_id, s)
        out = P.dist_path(site_id)
        out.parent.mkdir(parents=True, exist_ok=True)
        htmltext = P.render_site(site_id)
        out.write_text(htmltext, encoding="utf-8")
        ext = sum(htmltext.count(m) for m in _EXTERNAL_MARKERS)
        results["external_script_refs"] += ext
        results["sites"][site_id] = {"path": str(out.relative_to(P.REPO)), "bytes": len(htmltext),
                                     "title": s["title"], "external_refs": ext}
    for legacy_id, target_id in P.LEGACY_SITE_REDIRECTS.items():
        out = P.dist_path(legacy_id)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<meta http-equiv="refresh" content="0; url=../{target_id}/index.html">
<title>AI Done Right — moved</title>
</head><body>
<p>This local preview moved to <a href="../{target_id}/index.html">AI Done Right</a>.</p>
</body></html>
""", encoding="utf-8")
        results.setdefault("legacy_redirects", {})[legacy_id] = str(out.relative_to(P.REPO))
    # optional portfolio hub
    hub_html = P.render_hub()
    hub = P.DIST / "portfolio" / "index.html"
    hub.parent.mkdir(parents=True, exist_ok=True)
    hub.write_text(hub_html, encoding="utf-8")
    root_hub = P.DIST / "index.html"
    root_hub.write_text(hub_html, encoding="utf-8")
    results["hub"] = {"path": str(hub.relative_to(P.REPO)), "root_path": str(root_hub.relative_to(P.REPO))}
    # standards-interoperability page, generated from architecture/standards_interop_manifest.json (its own
    # source of truth). Kept out of the per-site renderer; never block the site build on it.
    try:
        from scripts.check_standards_interop_manifest import write_pages as _write_interop
        results["interop_pages"] = _write_interop()
    except Exception as e:  # pragma: no cover
        results["interop_pages_error"] = str(e)
    _BUILD_MANIFEST.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    res = build_all()
    check(f"build emitted {len(P.SITE_ORDER)} sites + hub",
          len(res["sites"]) == len(P.SITE_ORDER) and "hub" in res, str(list(res["sites"])))
    check("ZERO external script/CDN references across all sites", res["external_script_refs"] == 0,
          str(res["external_script_refs"]))
    for site_id in P.SITE_ORDER:
        out = P.dist_path(site_id)
        check(f"{site_id}: index.html exists", out.exists())
        htmltext = out.read_text(encoding="utf-8")
        missing = [p for p in P.SITES[site_id]["required_phrases"] if p not in htmltext]
        check(f"{site_id}: all required phrases present", not missing, f"missing {missing[:2]}")
        check(f"{site_id}: has viewport + local <style>", "viewport" in htmltext and "<style>" in htmltext)
        check(f"{site_id}: no visible TODO", "TODO" not in htmltext)

    print("\n" + (f"PASS — build_portfolio_sites: {len(P.SITE_ORDER)} sites + hub rendered from the single source, all required "
                  "phrases present, viewport + local CSS, no external scripts, no visible TODO."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    res = build_all()
    print(f"built {len(res['sites'])} sites + hub → {P.DIST.relative_to(P.REPO)}/ (external refs: {res['external_script_refs']})")
    raise SystemExit(0)
