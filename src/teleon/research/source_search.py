"""src.teleon.research.source_search — specialized, DETERMINISTIC source searchers for tool discovery.

Dogfooding the descent: searching PyPI or GitHub for packages is a BOUNDED task — both expose structured endpoints — so
the cheapest tier is a specialized source adapter that hits the API/HTML directly (no LLM, no browser). The LLM-driven
browser (src.teleon.research.browser_port) is only the UNBOUNDED fallback for sources with no structured access. This is
"multiple versions of search, some focused on PyPI, some on GitHub" expressed as the descent's cheap tier.

  - PyPISearch    PyPI HTML search -> package names -> per-project JSON API for license/summary (deterministic parse)
  - GitHubSearch  GitHub REST repository search (keyless; honors OH_GITHUB_TOKEN for higher rate) -> JSON

Network-gated (OH_INFERENCE_ALLOW_NETWORK) + graceful: offline/blocked -> SourceSearchUnavailable (the caller falls back;
self-tests stay deterministic via offline fixtures). Discovery is NOT trust: every ToolHit is a CANDIDATE carrying its raw
license string for the governance layer to classify (src/openhubforai/licenses) + dedupe + verify before anything is
vendored. serves_truth=false. Teleon layer — never imports src.baltor.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_PYPI_SEARCH = "https://pypi.org/search/?q="
_PYPI_JSON = "https://pypi.org/pypi/{name}/json"
_GH_SEARCH = "https://api.github.com/search/repositories"
_UA = "OpenHarnessHub-Teleon/0.1 (tool-discovery)"
#: package-snippet name/description in the PyPI search HTML (deterministic; raises Unavailable if the markup changes)
_PYPI_NAME_RE = re.compile(r'class="package-snippet__name">([^<]+)</span>')
_PYPI_DESC_RE = re.compile(r'class="package-snippet__description">([^<]*)</p>')


class SourceSearchUnavailable(RuntimeError):
    """Raised when a source searcher cannot run (network off / endpoint blocked) — caller falls back."""


@dataclass
class ToolHit:
    """One discovered candidate tool. CANDIDATE only — license is the RAW string from the source, classified downstream."""
    source: str           # "pypi" | "github"
    name: str
    url: str
    description: str = ""
    license: str | None = None
    popularity: int | None = None   # stars (github) / None (pypi search has no count)
    extra: dict = field(default_factory=dict)

    @property
    def key(self) -> str:
        return f"{self.source}:{self.name}".lower()


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


def _get(url: str, *, headers: dict | None = None, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": _UA, **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


class SourceSearchPort:
    """Agnostic search plane: a future source (npm, crates.io, HF Hub) drops in as another subclass — zero caller change."""
    source = "abstract"

    def search(self, query: str, *, limit: int = 10) -> list[ToolHit]:  # pragma: no cover - interface
        raise NotImplementedError


class PyPISearch(SourceSearchPort):
    """PyPI: keyless KEYWORD search was removed by PyPI (XML-RPC search disabled; the HTML page is JS/challenge-gated), so
    .search() honestly raises Unavailable — we do NOT fabricate or screen-scrape a challenge page. The per-project JSON
    API works, so .describe(name) is the DETERMINISTIC enrichment (real license/summary) used to confirm + classify a
    candidate name (e.g. one surfaced by GitHubSearch). For real PyPI keyword search, set OH_LIBRARIESIO_KEY (LibrariesIo)."""
    source = "pypi"

    def search(self, query: str, *, limit: int = 10, enrich: bool = True) -> list[ToolHit]:
        if not network_allowed():
            raise SourceSearchUnavailable("network not allowed (OH_INFERENCE_ALLOW_NETWORK)")
        try:
            html = _get(_PYPI_SEARCH + urllib.parse.quote(query))
        except Exception as e:  # noqa: BLE001
            raise SourceSearchUnavailable(f"pypi search failed: {e}") from e
        names = _PYPI_NAME_RE.findall(html)[:limit]
        descs = _PYPI_DESC_RE.findall(html)
        if not names:
            raise SourceSearchUnavailable(
                "PyPI removed keyless keyword search (XML-RPC disabled; HTML is challenge-gated). "
                "Use PyPISearch.describe(name) for JSON-API enrichment, or set OH_LIBRARIESIO_KEY for keyword search.")
        hits = []
        for i, name in enumerate(names):
            desc = (descs[i].strip() if i < len(descs) else "")
            lic = None
            if enrich:
                lic, summ = self._enrich(name)
                desc = summ or desc
            hits.append(ToolHit("pypi", name.strip(), f"https://pypi.org/project/{name.strip()}/", desc, lic))
        return hits

    def describe(self, name: str) -> ToolHit | None:
        """Deterministic per-project lookup via the JSON API. Returns a ToolHit with real license/summary, or None if the
        package does not exist / is unreachable (honest — never invents a package)."""
        if not network_allowed():
            raise SourceSearchUnavailable("network not allowed (OH_INFERENCE_ALLOW_NETWORK)")
        lic, summ = self._enrich(name)
        if lic is None and not summ:
            return None
        return ToolHit("pypi", name, f"https://pypi.org/project/{name}/", summ, lic)

    def _enrich(self, name: str) -> tuple[str | None, str]:
        """Per-project JSON API: license (info.license or a 'License ::' classifier) + summary. Best-effort."""
        try:
            info = json.loads(_get(_PYPI_JSON.format(name=urllib.parse.quote(name)))).get("info", {})
        except Exception:  # noqa: BLE001
            return None, ""
        lic = (info.get("license") or "").strip()
        if not lic or len(lic) > 60:  # long license = the full text was dumped into the field; prefer the classifier
            for c in info.get("classifiers", []):
                if c.startswith("License ::"):
                    lic = c.split("::")[-1].strip()
                    break
        return (lic or None), (info.get("summary") or "").strip()


class GitHubSearch(SourceSearchPort):
    source = "github"

    def search(self, query: str, *, limit: int = 10, language: str | None = "python") -> list[ToolHit]:
        if not network_allowed():
            raise SourceSearchUnavailable("network not allowed (OH_INFERENCE_ALLOW_NETWORK)")
        q = query + (f" language:{language}" if language else "")
        url = f"{_GH_SEARCH}?q={urllib.parse.quote(q)}&sort=stars&order=desc&per_page={max(1, min(limit, 50))}"
        headers = {"Accept": "application/vnd.github+json"}
        tok = _env("OH_GITHUB_TOKEN")
        if tok:
            headers["Authorization"] = f"Bearer {tok}"
        try:
            data = json.loads(_get(url, headers=headers))
        except Exception as e:  # noqa: BLE001
            raise SourceSearchUnavailable(f"github search failed: {e}") from e
        hits = []
        for it in data.get("items", [])[:limit]:
            lic = (it.get("license") or {}).get("spdx_id")
            hits.append(ToolHit("github", it.get("full_name", ""), it.get("html_url", ""),
                                (it.get("description") or "").strip(), None if lic in (None, "NOASSERTION") else lic,
                                it.get("stargazers_count"), {"language": it.get("language")}))
        return hits


#: WIRED rungs we actually try here (climb in order); the rest of the ladder is cataloged in
#: architecture/browser_escalation_ladder.json (undetected_driver / vision_coordinate / proxy — governed, not wired).
_WIRED_BROWSER_RUNGS = ("headless", "headed")
_BLOCK_WORDS = ("challenge", "captcha", "are you a robot", "access denied", "verify you are human")


def _looks_blocked(r: dict) -> str:
    title = (r.get("title") or "").lower()
    if any(w in title for w in _BLOCK_WORDS):
        return f"bot wall ('{r.get('title')}')"
    if not (r.get("links") or (r.get("text") or "").strip()):
        return "rendered empty (likely a stub/challenge)"
    return ""


def search_via_browser(search_url: str, *, timeout: int = 60) -> dict:
    """ESCALATION: render a source's search PAGE with the LLM-directed browser as a user would — the rung ABOVE the
    deterministic API. A production tool NEVER gives up at rung 1: this CLIMBS every WIRED rung (headless real-UA +
    stealth-lite, then headed) and only raises after EXHAUSTING them, naming the next cataloged rung (undetected driver /
    vision-coordinate, governed). Returns the first rung whose page isn't bot-walled/empty. Never fabricates."""
    from src.teleon.research.browser_port import PlaywrightBrowser
    bp, trace = PlaywrightBrowser(), []
    for mode in _WIRED_BROWSER_RUNGS:
        r = bp.render(search_url, timeout=timeout, mode=mode)
        if r.get("error"):
            trace.append(f"{mode}: error {r['error']}")
            continue
        blocked = _looks_blocked(r)
        if blocked:
            trace.append(f"{mode}: {blocked}")
            continue
        return r  # a rung that worked
    raise SourceSearchUnavailable(
        "exhausted wired browser rungs [" + "; ".join(trace) + "] — next cataloged rungs: undetected_driver "
        "(undetected_chromedriver/nodriver/patchright) -> vision_coordinate (screenshot+grounding) -> residential_proxy; "
        "all GOVERNED (robots/ToS) + not wired. See architecture/browser_escalation_ladder.json")


class PyPIBrowserSearch(SourceSearchPort):
    """PyPI escalation: render pypi.org/search as a user (Playwright) + parse /project/ links. (PyPI currently serves a
    'Client Challenge' to headless browsers -> honest-unavailable -> the stealth rung; works for non-walled sources.)"""
    source = "pypi"

    def search(self, query: str, *, limit: int = 10) -> list[ToolHit]:
        if not network_allowed():
            raise SourceSearchUnavailable("network not allowed (OH_INFERENCE_ALLOW_NETWORK)")
        r = search_via_browser(_PYPI_SEARCH + urllib.parse.quote(query))  # raises on challenge (honest)
        names, seen = [], set()
        for l in r.get("links") or []:
            href = l.get("href", "")
            if "/project/" in href:
                n = href.split("/project/")[1].strip("/").split("/")[0]
                if n and n not in seen:
                    seen.add(n)
                    names.append(n)
        if not names:
            raise SourceSearchUnavailable("browser rendered the page but found no /project/ links")
        return [ToolHit("pypi", n, f"https://pypi.org/project/{n}/", "", None) for n in names[:limit]]


_SOURCES = {"pypi": PyPISearch, "github": GitHubSearch}
#: the browser-render escalation version per source (the rung above the deterministic API)
_ESCALATION = {"pypi": PyPIBrowserSearch}


def select_source_search(source: str = "auto") -> list[SourceSearchPort]:
    """'pypi' / 'github' -> that one; 'auto' (or 'all') -> both (the descent runs the cheapest reachable, falls back)."""
    if source in ("auto", "all"):
        return [PyPISearch(), GitHubSearch()]
    if source not in _SOURCES:
        raise ValueError(f"unknown source {source!r}; known: {sorted(_SOURCES)} or 'auto'")
    return [_SOURCES[source]()]


def discover(query: str, *, source: str = "auto", limit: int = 10, escalate: bool = False) -> list[ToolHit]:
    """Run the selected source searcher(s), merge + dedupe by (source,name). The DESCENT: a source's deterministic API
    is the cheap tier; with escalate=True, an API that's unavailable ESCALATES to the browser-render tier for that
    source (climb the ladder, don't give up). Honest: if every tier of every reachable source is unavailable, raises
    SourceSearchUnavailable with the full escalation trace — never fabricates."""
    seen, out, errs = set(), [], []
    def take(hits):
        for h in hits:
            if h.name and h.key not in seen:
                seen.add(h.key)
                out.append(h)
    for s in select_source_search(source):
        try:
            take(s.search(query, limit=limit))
        except SourceSearchUnavailable as e:
            errs.append(f"{s.source}:api {e}")
            if escalate and s.source in _ESCALATION:
                try:
                    take(_ESCALATION[s.source]().search(query, limit=limit))
                    errs.append(f"{s.source}:escalated->browser ok")
                except SourceSearchUnavailable as e2:
                    errs.append(f"{s.source}:browser {e2}")
    if not out and errs:
        raise SourceSearchUnavailable("; ".join(errs))
    return out


if __name__ == "__main__":  # quick live probe: python3 -m src.teleon.research.source_search "ocr"
    import sys
    q = sys.argv[1] if len(sys.argv) > 1 else "ocr"
    src = sys.argv[2] if len(sys.argv) > 2 else "auto"
    try:
        for h in discover(q, source=src, limit=8):
            print(f"  [{h.source:6s}] {h.name:40s} {h.license or '?':14s} {('★' + str(h.popularity)) if h.popularity else ''}  {h.description[:60]}")
    except SourceSearchUnavailable as e:
        print(f"  UNAVAILABLE (honest): {e}")
