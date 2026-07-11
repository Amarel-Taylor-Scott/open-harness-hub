#!/usr/bin/env python3
"""browser_control.search_adapter — the search-API lane (SCAFFOLD; available_with_credentials, no fake keys).

Often the cheapest way to "find pages about X" is a search API, not a crawl. This adapter is the SEAM for the
common providers — Tavily, Exa, SerpAPI, Brave Search, Bing Web Search — behind one ``search(query)`` surface.

It ships as a governed SCAFFOLD: with NO key present it returns a structured
``status="available_with_credentials"`` result (naming the env var to set) and NEVER calls out and NEVER
fabricates results. Key presence is detected by ENV name only — a key value is never read into a record or
logged. The real REST call is implemented behind a key-present guard for when an operator supplies one, but
this repo carries no keys, so that path is unexercised by the offline test (which asserts the keyless
behavior). Nothing raises.

    python3 browser_control/ingestion_self_test.py --self-test   # offline, mutation-gated (keyless behavior)
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
import json  # noqa: E402
import os  # noqa: E402
import urllib.parse  # noqa: E402
import urllib.request  # noqa: E402
from typing import Any, Optional  # noqa: E402

from scripts.primitive_browser_control_harness import BOUNDARY  # noqa: E402

#: provider -> {env var that holds the key, optional python package, whether a REST-only path exists}
PROVIDERS: dict[str, dict[str, Any]] = {
    "tavily":  {"env": "TAVILY_API_KEY",  "package": "tavily",  "rest": True,
                "endpoint": "https://api.tavily.com/search"},
    "exa":     {"env": "EXA_API_KEY",     "package": "exa_py",  "rest": True,
                "endpoint": "https://api.exa.ai/search"},
    "serpapi": {"env": "SERPAPI_API_KEY", "package": "serpapi", "rest": True,
                "endpoint": "https://serpapi.com/search"},
    "brave":   {"env": "BRAVE_API_KEY",   "package": None,      "rest": True,
                "endpoint": "https://api.search.brave.com/res/v1/web/search"},
    "bing":    {"env": "BING_API_KEY",    "package": None,      "rest": True,
                "endpoint": "https://api.bing.microsoft.com/v7.0/search"},
}


def _import_ok(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except Exception:  # noqa: BLE001
        return False


def _key_present(env_var: str) -> bool:
    """Presence ONLY — the value is never read out of the environment into any record."""
    return bool(os.environ.get(env_var))


class SearchAdapter:
    """Search-API seam over Tavily/Exa/SerpAPI/Brave/Bing. Keyless → ``available_with_credentials`` (never calls
    out, never fabricates results). Every result is structured + candidate-only; nothing raises."""

    name = "search"

    def __init__(self, *, provider: str = "auto", max_results: int = 5, timeout: float = 15.0) -> None:
        self._provider = provider
        self._max_results = int(max_results)
        self._timeout = float(timeout)

    # ── introspection ────────────────────────────────────────────────────────────────────────────────────────
    def providers(self) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for name, spec in PROVIDERS.items():
            key = _key_present(spec["env"])
            pkg = spec["package"]
            pkg_present = _import_ok(pkg) if pkg else True     # REST-only providers need no package
            if key and pkg_present:
                status = "available"
            elif pkg and not pkg_present and not spec.get("rest"):
                status = "missing_package"
            else:
                status = "available_with_credentials"
            out.append({"provider": name, "env_var": spec["env"], "key_present": key, "package": pkg,
                        "package_present": pkg_present, "rest_available": bool(spec.get("rest")), "status": status})
        return out

    def capabilities(self) -> dict[str, Any]:
        provs = self.providers()
        return {"adapter": self.name, "read_only": True, "methods": ["search", "providers"],
                "providers": provs, "any_key_present": any(p["key_present"] for p in provs), **BOUNDARY}

    def _resolve_provider(self, requested: Optional[str]) -> str:
        want = requested or self._provider
        if want and want != "auto":
            return want
        return next((p["provider"] for p in self.providers() if p["key_present"]), "tavily")

    # ── the one command ──────────────────────────────────────────────────────────────────────────────────────
    def search(self, query: str, *, provider: Optional[str] = None,
               max_results: Optional[int] = None) -> dict[str, Any]:
        """Web search via the resolved provider. With no key set → structured ``available_with_credentials``
        (names the env var; never calls out, never fabricates). With a key present → the real REST call."""
        prov = self._resolve_provider(provider)
        spec = PROVIDERS.get(prov)
        if spec is None:
            return {"supported": False, "adapter": self.name, "reason": f"unknown provider {prov!r}; "
                    f"known: {sorted(PROVIDERS)}", **BOUNDARY}
        k = min(int(max_results or self._max_results), 20)
        if not _key_present(spec["env"]):
            return {"supported": True, "ok": False, "adapter": self.name, "provider": prov,
                    "status": "available_with_credentials", "results": [], "n_results": 0,
                    "reason": f"no API key for {prov}; set {spec['env']} to enable "
                              "(env presence-only — the value is never read into a record)", **BOUNDARY}
        try:
            results = self._rest_search(prov, spec, query, k)
            return {"supported": True, "ok": True, "adapter": self.name, "provider": prov, "status": "available",
                    "results": results[:k], "n_results": len(results[:k]), **BOUNDARY}
        except Exception as exc:  # noqa: BLE001 — a live failure is structured, never raised
            return {"supported": True, "ok": False, "adapter": self.name, "provider": prov, "status": "error",
                    "results": [], "n_results": 0, "reason": f"{type(exc).__name__}: {exc}"[:200], **BOUNDARY}

    # ── real REST call (behind a key-present guard; unexercised where no key is set) ──────────────────────────
    def _rest_search(self, prov: str, spec: dict, query: str, k: int) -> list[dict[str, Any]]:
        key = os.environ.get(spec["env"], "")                 # read only at call time, only when present; never stored
        endpoint = spec["endpoint"]
        if prov == "brave":
            url = endpoint + "?" + urllib.parse.urlencode({"q": query, "count": k})
            req = urllib.request.Request(url, headers={"X-Subscription-Token": key, "Accept": "application/json"})
        elif prov == "bing":
            url = endpoint + "?" + urllib.parse.urlencode({"q": query, "count": k})
            req = urllib.request.Request(url, headers={"Ocp-Apim-Subscription-Key": key})
        elif prov == "tavily":
            body = json.dumps({"api_key": key, "query": query, "max_results": k}).encode()
            req = urllib.request.Request(endpoint, data=body, headers={"Content-Type": "application/json"},
                                         method="POST")
        elif prov == "exa":
            body = json.dumps({"query": query, "numResults": k}).encode()
            req = urllib.request.Request(endpoint, data=body,
                                         headers={"Content-Type": "application/json", "x-api-key": key},
                                         method="POST")
        else:  # serpapi
            url = endpoint + "?" + urllib.parse.urlencode({"q": query, "api_key": key, "num": k})
            req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:  # noqa: S310
            data = json.loads(resp.read().decode("utf-8", "ignore"))
        return self._normalize(prov, data)

    def _normalize(self, prov: str, data: dict) -> list[dict[str, Any]]:
        """Map each provider's response shape to a common {title,url,snippet} row (no raw payload stored)."""
        rows: list[dict[str, Any]] = []
        raw = (data.get("results") or data.get("web", {}).get("results") or data.get("webPages", {}).get("value")
               or data.get("organic_results") or [])
        for r in raw:
            rows.append({"title": r.get("title") or r.get("name") or "",
                         "url": r.get("url") or r.get("link") or "",
                         "snippet": (r.get("content") or r.get("snippet") or r.get("description") or "")[:400]})
        return rows


__all__ = ["SearchAdapter", "PROVIDERS"]
