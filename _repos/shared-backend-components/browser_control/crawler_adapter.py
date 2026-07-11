#!/usr/bin/env python3
"""browser_control.crawler_adapter — the multi-page crawl primitive (sitemap · robots · rate-limited BFS).

The orchestration lane of the zoo: given seed URLs it discovers more (sitemap.xml + same-host links) and
walks them breadth-first under a politeness budget. READ-ONLY research crawling only — it never submits a
form, never activates a side-effect control, never bypasses a login/captcha.

REUSE-FIRST: the crawl engine IS the shipped harness — ``scripts.primitive_browser_control_harness.crawl``
(robots-gated, rate-limited, no-raw-body ``CapturedArtifact`` rows) driven by a ``StaticBackend`` (urllib or
an injected fetcher), the harness ``RateLimiter`` (per-domain throttle, injected clock), and the harness
robots policy via ``browser_control.safety.robots_gate``. Nothing re-implements fetching, robots parsing, the
throttle, or extraction. The only logic added is a stdlib ``sitemap.xml`` parser (incl. sitemap-index) and a
compact per-page projection over the harness rows. ``scrapy`` (Python) and ``crawlee`` (Node) are optional
higher-scale engines whose PRESENCE is reported but which are not required. Nothing raises.

    python3 browser_control/ingestion_self_test.py --self-test   # offline (injected fetch), mutation-gated
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install  # noqa: E402

_install()

import importlib.util  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402
import time  # noqa: E402
import urllib.parse  # noqa: E402
import urllib.request  # noqa: E402
import xml.etree.ElementTree as ET  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

from scripts.primitive_browser_control_harness import (  # noqa: E402  single source — the crawl engine + throttle
    BOUNDARY,
    RateLimiter,
    StaticBackend,
    _UA,
    crawl as _harness_crawl,
)

from browser_control import safety  # noqa: E402  single-source robots policy

_DEFAULT_MIN_INTERVAL_S = 2.0
_MAX_SITEMAP_URLS = 5000


def _import_ok(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except Exception:  # noqa: BLE001
        return False


def _node_module_present(module: str) -> bool:
    if not shutil.which("node"):
        return False
    try:
        out = subprocess.run(["node", "-e", f"try{{require.resolve('{module}');console.log('y')}}catch(e){{}}"],
                             capture_output=True, text=True, timeout=8)
        return "y" in (out.stdout or "")
    except Exception:  # noqa: BLE001
        return False


class CrawlerAdapter:
    """Read-only crawler: sitemap/robots discovery + a robots-gated, rate-limited BFS over the harness engine.
    Fully offline with an injected ``fetch``; live via urllib otherwise. Every result is candidate-only; the
    disallowed and the rate-limited pages are reported, never fetched. Nothing raises."""

    name = "crawler"

    def __init__(self, *, fetch: Optional[Callable[[str], Optional[str]]] = None,
                 robots_fetch: Optional[Callable[[str], Optional[str]]] = None, ua: Optional[str] = None,
                 min_interval: float = _DEFAULT_MIN_INTERVAL_S,
                 clock: Optional[Callable[[], float]] = None) -> None:
        self._fetch = fetch                       # inject for offline/deterministic crawl; None → live urllib
        self._robots_fetch = robots_fetch
        self._ua = ua or _UA
        self._min_interval = float(min_interval)
        self._clock = clock or time.monotonic

    # ── introspection ────────────────────────────────────────────────────────────────────────────────────────
    def available_engines(self) -> dict[str, bool]:
        return {"stdlib_bfs": True, "scrapy": _import_ok("scrapy"), "crawlee_node": _node_module_present("crawlee")}

    def capabilities(self) -> dict[str, Any]:
        return {"adapter": self.name, "read_only": True,
                "methods": ["fetch_robots", "robots_allows", "fetch_sitemap", "crawl"],
                "engines_available": self.available_engines(), "min_interval_s": self._min_interval, **BOUNDARY}

    # ── discovery (read-only) ────────────────────────────────────────────────────────────────────────────────
    def robots_allows(self, url: str) -> bool:
        """True iff robots.txt permits our UA to fetch ``url`` (delegates to the harness policy)."""
        return safety.robots_gate(url, fetch=self._robots_fetch, ua=self._ua)

    def fetch_robots(self, base_url: str) -> dict[str, Any]:
        robots_url = self._origin(base_url) + "/robots.txt"
        body = self._raw(robots_url)
        return {"supported": True, "adapter": self.name, "url": robots_url,
                "robots_txt": (body or "")[:8000], "n_bytes": len(body or ""), "found": bool(body), **BOUNDARY}

    def fetch_sitemap(self, base_url: str) -> dict[str, Any]:
        sitemap_url = self._origin(base_url) + "/sitemap.xml"
        body = self._raw(sitemap_url)
        if not body:
            return {"supported": True, "adapter": self.name, "url": sitemap_url, "urls": [], "n_urls": 0,
                    "is_index": False, "found": False, **BOUNDARY}
        urls, is_index = self._parse_sitemap(body)
        return {"supported": True, "adapter": self.name, "url": sitemap_url, "urls": urls[:_MAX_SITEMAP_URLS],
                "n_urls": len(urls[:_MAX_SITEMAP_URLS]), "is_index": is_index, "found": True, **BOUNDARY}

    # ── crawl (read-only BFS over the harness engine) ────────────────────────────────────────────────────────
    def crawl(self, seeds: list[str], *, max_pages: int = 10, min_interval: Optional[float] = None,
              follow_links: bool = True) -> dict[str, Any]:
        """Robots-gated, rate-limited, read-only BFS from ``seeds``. Returns a compact per-page projection plus
        the URLs skipped for robots / rate-limit — the harness never stores a raw body or a secret."""
        interval = self._min_interval if min_interval is None else float(min_interval)
        backend = StaticBackend(fetch=self._fetch, ua=self._ua) if self._fetch else StaticBackend(ua=self._ua)
        try:
            rows = _harness_crawl(list(seeds), backend=backend, clock=self._clock, max_pages=int(max_pages),
                                  robots_fetch=self._robots_fetch, min_interval=interval, follow_links=follow_links)
        except Exception as exc:  # noqa: BLE001 — a crawl failure is structured, never raised
            return {"supported": True, "ok": False, "adapter": self.name, "pages": [], "n_pages": 0,
                    "reason": f"{type(exc).__name__}: {exc}"[:200], **BOUNDARY}
        pages, skipped_robots, skipped_rate = [], [], []
        for r in rows:
            if r.get("reason") == "robots_disallow":
                skipped_robots.append(r.get("url"))
            elif r.get("reason") == "rate_limited_domain":
                skipped_rate.append(r.get("url"))
            ex = r.get("extracted") or {}
            pages.append({"url": r.get("url"), "captured": bool(r.get("captured")),
                          "reason": r.get("reason"), "trust_tier": r.get("trust_tier"),
                          "n_links": ex.get("n_links", 0), "login_wall": ex.get("login_wall", False),
                          "n_forms": ex.get("n_forms", 0)})
        n_captured = sum(1 for p in pages if p["captured"])
        return {"supported": True, "ok": True, "adapter": self.name, "n_pages": len(pages),
                "n_captured": n_captured, "pages": pages, "skipped_robots": skipped_robots,
                "skipped_rate_limited": skipped_rate, "hit_page_cap": len(pages) >= int(max_pages), **BOUNDARY}

    # ── helpers ──────────────────────────────────────────────────────────────────────────────────────────────
    def _origin(self, url: str) -> str:
        p = urllib.parse.urlparse(url if "://" in url else "http://" + url)
        return f"{p.scheme}://{p.netloc}"

    def _raw(self, url: str) -> Optional[str]:
        """Read-only GET of a discovery resource — injected fetch if provided, else stdlib urllib. Never raises."""
        if self._fetch is not None:
            try:
                return self._fetch(url)
            except Exception:  # noqa: BLE001
                return None
        try:
            req = urllib.request.Request(url, headers={"User-Agent": self._ua})
            with urllib.request.urlopen(req, timeout=15) as resp:  # noqa: S310
                return resp.read().decode("utf-8", "ignore")
        except Exception:  # noqa: BLE001
            return None

    def _parse_sitemap(self, body: str) -> tuple[list[str], bool]:
        """Parse sitemap.xml (or a sitemap index) → list of <loc> URLs. Namespace-agnostic; bounded; never raises."""
        try:
            root = ET.fromstring(body)
        except Exception:  # noqa: BLE001 — malformed XML → no urls, never crash
            return [], False
        locs = [(el.text or "").strip() for el in root.iter()
                if el.tag.rsplit("}", 1)[-1] == "loc" and (el.text or "").strip()]
        is_index = root.tag.rsplit("}", 1)[-1] == "sitemapindex"
        seen, out = set(), []
        for u in locs:
            if u not in seen and u.startswith(("http://", "https://")):
                seen.add(u)
                out.append(u)
        return out, is_index


# expose the harness throttle so callers reading THIS module import the rate limiter from one place
__all__ = ["CrawlerAdapter", "RateLimiter"]
