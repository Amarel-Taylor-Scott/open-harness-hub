#!/usr/bin/env python3
"""verify_tunnels.py — the "not done until all sites are live" GATE.

For every brand surface declared in ``services/registry.yaml`` (a product with a ``web_root``), check
that its public trycloudflare URL is FULLY FUNCTIONAL:

  1. the URL exists (``dist/showcase-tunnel-url-<id>.txt`` was written by the orchestrator),
  2. ``GET <url>/api/health`` returns HTTP 200 with ``{"status": ...}`` (the shared backend answers),
  3. ``GET <url>/`` returns 200 and contains the product's BRAND string (the *right* site is served,
     not a stale/another product's folder).

Prints a status table and exits ``0`` only when EVERY site passes; otherwise exits ``1``. This is the
condition the goal loop blocks on (``docs/codex/three-sites-live-goal.md`` /
``.claude/commands/sites-live.md``). Pure stdlib + PyYAML (already a repo dependency); no writes.

    python3 -m scripts.showcase.verify_tunnels            # check, table, exit code
    python3 -m scripts.showcase.verify_tunnels --json     # machine-readable, still sets exit code
    python3 -m scripts.showcase.verify_tunnels --quiet    # exit code only
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "services" / "registry.yaml"
DIST = ROOT / "dist"
TIMEOUT = 12  # seconds per request; tunnels add real latency, so be generous

# fallback if the registry can't be read — the three known brand surfaces
_FALLBACK = [
    {"id": "harness-hub", "brand": "OpenHubForAI"},
    {"id": "baltor", "brand": "Baltor"},
    {"id": "context-is-everything", "brand": "Context is Everything"},
]


def _sites() -> list[dict]:
    """The brand surfaces to check = registry products that serve a web_root."""
    try:
        import yaml  # repo dependency

        reg = yaml.safe_load(REGISTRY.read_text())
        out = [
            {"id": p["id"], "brand": p.get("brand", p["id"])}
            for p in (reg.get("products") or [])
            if p.get("web_root")
        ]
        return out or _FALLBACK
    except Exception:
        return _FALLBACK


def _get(url: str, want_text: bool = False):
    """Return (status_code, body_or_None). Never raises — network errors → (None, None)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ohh-verify-tunnels/1"})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:  # noqa: S310 (trusted, our own tunnel)
            body = r.read().decode("utf-8", "replace") if want_text else None
            return r.status, body
    except Exception:
        return None, None


def check(site: dict) -> dict:
    slug, brand = site["id"], site["brand"]
    urlfile = DIST / f"showcase-tunnel-url-{slug}.txt"
    base = urlfile.read_text().strip() if urlfile.exists() else ""
    res = {"id": slug, "brand": brand, "url": base, "has_url": bool(base),
           "health": False, "brand_served": False, "ok": False}
    if not base:
        return res
    hcode, _ = _get(f"{base}/api/health")
    res["health"] = hcode == 200
    rcode, html = _get(f"{base}/", want_text=True)
    res["brand_served"] = rcode == 200 and html is not None and brand in html
    res["ok"] = res["health"] and res["brand_served"]
    return res


def main(argv: list[str]) -> int:
    as_json = "--json" in argv
    quiet = "--quiet" in argv
    results = [check(s) for s in _sites()]
    all_ok = bool(results) and all(r["ok"] for r in results)

    if as_json:
        print(json.dumps({"all_ok": all_ok, "sites": results}, indent=2))
    elif not quiet:
        print("  site                    health  brand   public URL")
        print("  " + "-" * 78)
        for r in results:
            mark = "●LIVE" if r["ok"] else "○DOWN"
            h = "ok " if r["health"] else "-- "
            b = "ok " if r["brand_served"] else "-- "
            url = (r["url"] or "(no url yet)")
            print(f"  {mark} {r['id']:<20} {h:<6} {b:<6} {url}")
        print("  " + "-" * 78)
        print(f"  {'ALL LIVE ✓' if all_ok else 'NOT ALL LIVE ✗'}  "
              f"({sum(r['ok'] for r in results)}/{len(results)} sites fully functional)")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
