"""Shared infrastructure for knowledge-tree walkers.

Every new walker (USC, Wikidata, NIST, etc.) gets:
  - RateLimiter        — monotonic-clock spacing between requests
  - on-disk cache      — sha256(url + body) keyed; ~/.cache/oh-hub/{kind}/
  - fetch_json         — GET → JSON with retry + cache + User-Agent
  - fetch_text         — GET → text (for XML/HTML walkers)
  - fetch_post_json    — POST → JSON (for SPARQL etc.)
  - WalkStats          — uniform stats object every walker fills in

The existing `wikipedia_category_walker.py` was written before this base
existed; it remains self-contained. New walkers should import from here.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

USER_AGENT = (
    "OpenHubForAIWalker/0.1 "
    "(+https://github.com/Amarel-Taylor-Scott/openhubforai; issues via repo)"
)

DEFAULT_RATE_LIMIT_PER_SEC = 1.0
CACHE_ROOT = Path.home() / ".cache" / "oh-hub"


class RateLimiter:
    def __init__(self, requests_per_second: float):
        self.interval = 1.0 / max(requests_per_second, 0.01)
        self._last_call = 0.0

    def wait(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_call
        if elapsed < self.interval:
            time.sleep(self.interval - elapsed)
        self._last_call = time.monotonic()


def _cache_path(kind: str, key: str) -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:32]
    return _resource(kind) / f"{digest}.cache"


def fetch_text(
    url: str,
    rate_limiter: RateLimiter,
    cache_kind: str,
    *,
    use_cache: bool = True,
    headers: dict[str, str] | None = None,
    timeout: float = 30.0,
    max_attempts: int = 4,
) -> str:
    """GET a URL, return body as text. Cached on disk by URL hash."""
    cache = _cache_path(cache_kind, url)
    if use_cache and cache.exists():
        return cache.read_text(encoding="utf-8")

    req_headers = {"User-Agent": USER_AGENT, **(headers or {})}
    last_err: Exception | None = None
    for attempt in range(max_attempts):
        rate_limiter.wait()
        req = urllib.request.Request(url, headers=req_headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read().decode("utf-8", errors="replace")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            last_err = e
            time.sleep(min(30, 2 ** attempt))
            continue
        if use_cache:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(body, encoding="utf-8")
        return body
    raise RuntimeError(f"failed to fetch {url}: {last_err}")


def fetch_json(
    url: str,
    rate_limiter: RateLimiter,
    cache_kind: str,
    *,
    use_cache: bool = True,
    headers: dict[str, str] | None = None,
) -> dict:
    text = fetch_text(
        url,
        rate_limiter,
        cache_kind,
        use_cache=use_cache,
        headers={"Accept": "application/json", **(headers or {})},
    )
    return json.loads(text)


def fetch_post_json(
    url: str,
    body: str,
    rate_limiter: RateLimiter,
    cache_kind: str,
    *,
    use_cache: bool = True,
    headers: dict[str, str] | None = None,
    timeout: float = 60.0,
    max_attempts: int = 4,
) -> dict:
    """POST body → JSON. Cache key includes the body so different queries cache distinctly."""
    cache_key = url + "\n" + body
    cache = _cache_path(cache_kind, cache_key)
    if use_cache and cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))

    req_headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
        **(headers or {}),
    }
    last_err: Exception | None = None
    for attempt in range(max_attempts):
        rate_limiter.wait()
        req = urllib.request.Request(url, data=body.encode("utf-8"), headers=req_headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            last_err = e
            time.sleep(min(30, 2 ** attempt))
            continue
        if use_cache:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return data
    raise RuntimeError(f"failed to POST {url}: {last_err}")


@dataclass
class WalkStats:
    """Uniform stats object every walker fills in."""

    walker_kind: str
    nodes_emitted: int = 0
    nodes_skipped: int = 0
    duration_s: float = 0.0
    stopped_reason: str = "completed"
    warnings: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "walker_kind": self.walker_kind,
            "nodes_emitted": self.nodes_emitted,
            "nodes_skipped": self.nodes_skipped,
            "duration_s": round(self.duration_s, 2),
            "stopped_reason": self.stopped_reason,
            "warnings": list(self.warnings),
            **self.extra,
        }


def percent_encode(s: str) -> str:
    """For SPARQL / query-string parts. Quotes everything except unreserved chars."""
    return urllib.parse.quote(s, safe="")
