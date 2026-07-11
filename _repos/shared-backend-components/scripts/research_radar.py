"""scripts.research_radar (DEVELOPMENT tool — not a product module) — proactive OUTWARD research via FREE no-key APIs (GitHub / Hacker News / PyPI).

Scan the external landscape — competitors, similar products, repos, packages, news, product-market gaps — in the
context-layer / agent-runtime space, recorded as governed CANDIDATES (discovery != trust; intake never auto-active;
claims UNVERIFIED-until-reproduced). Sources are free + no-key: GitHub repo search, Hacker News (Algolia), PyPI JSON
(package vetting). Config: _repos/shared-backend-components/architecture/research_radar.json. Feeds the GitHub Signal Flywheel +
_repos/shared-backend-components/architecture/intelligence_source_registry.json. Pure data in; offline-degrading; Teleon-layer; serves_truth=false.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_CONFIG = _resource("architecture") / "research_radar.json"
LEDGER = _resource("data") / "dev-intel" / "research-radar.jsonl"
SOURCES = ("github", "hackernews", "pypi")


def load_config() -> dict:
    return json.loads(_CONFIG.read_text(encoding="utf-8"))


def _env(var: str) -> str:
    f = _REPO / ".env"
    if not f.exists():
        return ""
    for ln in f.read_text(encoding="utf-8").splitlines():
        if ln.startswith(f"{var}="):
            return ln.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def network_allowed() -> bool:
    return _env("OH_INFERENCE_ALLOW_NETWORK") in ("1", "true", "True", "yes")


class RadarUnavailable(RuntimeError):
    """Raised when a source can't be reached (network off / rate-limited); the loop records + continues."""


def _get_json(url: str, *, headers: dict | None = None, timeout: int = 20) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "OpenHubForAI-research-radar/0.1", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def github_repos(query: str, *, n: int = 5) -> list[dict]:
    if not network_allowed():
        raise RadarUnavailable("network not allowed")
    headers = {"Accept": "application/vnd.github+json"}
    tok = _env("GITHUB_TOKEN")
    if tok:
        headers["Authorization"] = f"Bearer {tok}"   # higher rate limit when supplied (optional)
    q = urllib.parse.quote(query)
    d = _get_json(f"https://api.github.com/search/repositories?q={q}&sort=stars&order=desc&per_page={n}", headers=headers)
    return [{"source": "github", "title": r["full_name"], "url": r["html_url"], "stars": r.get("stargazers_count", 0),
             "snippet": (r.get("description") or "")[:200], "license": (r.get("license") or {}).get("spdx_id"),
             "updated": r.get("pushed_at", "")} for r in d.get("items", [])[:n]]


def hn_news(query: str, *, n: int = 5) -> list[dict]:
    if not network_allowed():
        raise RadarUnavailable("network not allowed")
    q = urllib.parse.quote(query)
    d = _get_json(f"https://hn.algolia.com/api/v1/search?query={q}&tags=story&hitsPerPage={n}")
    return [{"source": "hackernews", "title": (h.get("title") or "")[:200], "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
             "points": h.get("points", 0), "snippet": (h.get("story_text") or "")[:200], "updated": h.get("created_at", "")}
            for h in d.get("hits", [])[:n]]


def pypi_pkg(name: str) -> dict:
    """Vet a specific package (free PyPI JSON). Returns {} if not found."""
    if not network_allowed():
        raise RadarUnavailable("network not allowed")
    try:
        d = _get_json(f"https://pypi.org/pypi/{urllib.parse.quote(name)}/json")
    except Exception:
        return {}
    i = d.get("info", {})
    return {"source": "pypi", "title": name, "url": i.get("project_url") or f"https://pypi.org/project/{name}/",
            "version": i.get("version"), "snippet": (i.get("summary") or "")[:200], "license": i.get("license")}


def research(query: str, source: str = "github", *, n: int = 5, record_raw: bool = True) -> list[dict]:
    """Run one query against one free source; record raw hits as candidates. Returns the hits (empty if unavailable)."""
    fn = {"github": github_repos, "hackernews": hn_news}.get(source)
    if fn is None:
        return []
    try:
        hits = fn(query, n=n)
    except RadarUnavailable:
        return []
    except Exception:  # noqa: BLE001 — rate-limit / transient: record nothing, the loop continues
        return []
    if record_raw and hits:
        record([{**h, "query": query, "status": "candidate", "serves_truth": False} for h in hits])
    return hits


def record(items: list[dict]) -> int:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it, sort_keys=True) + "\n")
    return sum(1 for _ in LEDGER.read_text(encoding="utf-8").splitlines() if _.strip()) if LEDGER.exists() else 0


def radar_targets() -> list[dict]:
    """topics x sources -> research targets for the loop."""
    cfg = load_config()
    out = []
    for topic in cfg.get("topics", []):
        for src in cfg.get("sources", SOURCES):
            out.append({"id": f"research:{src}:{topic}", "kind": "research", "ref": f"{src}::{topic}"})
    return out


def format_results(query: str, source: str, hits: list[dict]) -> str:
    if not hits:
        return f"RESEARCH {source} :: {query}\n(no results — offline or rate-limited)"
    lines = [f"RESEARCH {source} :: {query} ({len(hits)} hits)"]
    for h in hits:
        meta = f"{h.get('stars','')}★" if source == "github" else (f"{h.get('points','')}pts" if source == "hackernews" else "")
        lines.append(f"  - {h['title']} {meta} | {h.get('url','')}\n    {h.get('snippet','')}")
    return "\n".join(lines)
