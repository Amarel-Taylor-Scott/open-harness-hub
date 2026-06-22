"""src.teleon.dag.real_steps — REAL infrastructure adapters for DAG nodes (no stand-ins).

The example pipelines use deterministic offline fns; THESE call actual infrastructure so a demo runs end-to-end on
real services:
  - real_llm        a real model via the Ollama Cloud lane (.env OH_LLM_*), reusing the proven OpenAI-compatible call.
  - real_search     real GROUNDED sources from FREE, no-key APIs: Wikipedia REST + the US Federal Register (GPO) — both
                    return citable source URLs (provenance). Registered in architecture/search_provider_registry.json.
  - real_text       real text extraction from a real file (PDF/scan need pypdf/tesseract — absent here — so text/markdown
                    is the real acquire path; the cost model + cascade are identical).

Network-gated (OH_INFERENCE_ALLOW_NETWORK) + graceful: when offline/unavailable each adapter raises RealStepUnavailable
so a caller can fall back to the offline stand-in (the --self-test path stays deterministic). serves_truth=false (model
output is a candidate; the cited sources carry provenance). Teleon-layer — never imports src.baltor.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
#: cheap + frontier REAL model ids on the Ollama lane (provider-specific ids; the registry's logical ids differ —
#: a known mapping gap tracked for single-sourcing). Cheap = small/fast; frontier = the strong reviewer model.
REAL_CHEAP_MODEL = "gemma4:31b"
REAL_FRONTIER_MODEL = "glm-5.2"
_WIKI_SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/"
_WIKI_SEARCH = "https://en.wikipedia.org/w/api.php"
_FEDREG = "https://www.federalregister.gov/api/v1/documents.json"


class RealStepUnavailable(RuntimeError):
    """Raised when a real adapter cannot run (no key, network off) — caller may fall back to the offline stand-in."""


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


def llm_available() -> bool:
    return bool(_env("OH_LLM_API_KEY")) and bool(_env("OH_LLM_BASE_URL")) and network_allowed()


def _get_json(url: str, *, timeout: int = 25) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "OpenHarnessHub-Teleon/0.1 (real_steps)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


# ── real model ───────────────────────────────────────────────────────────────────────────────────
def real_llm(prompt: str, *, system: str = "You are a precise extraction/synthesis engine.", model: str | None = None,
             max_tokens: int = 1200, timeout: int = 240) -> dict:
    """A REAL model call via the Ollama lane (reuses the proven OpenAI-compatible client). Returns {text, model,
    usage, cost_estimate, serves_truth:false}. Raises RealStepUnavailable if the lane isn't configured."""
    if not llm_available():
        raise RealStepUnavailable("Ollama lane not configured (OH_LLM_API_KEY / OH_INFERENCE_ALLOW_NETWORK)")
    from scripts._llm_client import resolve_provider, chat
    prov = resolve_provider("ollama")
    mdl = model or REAL_CHEAP_MODEL
    res = chat(mdl, system, prompt, prov, max_tokens=max_tokens, timeout=timeout)
    if res["error"]:
        raise RealStepUnavailable(f"real_llm error: {res['error'][:160]}")
    usage = res.get("usage", {}) or {}
    # rough cost estimate from output tokens at a cheap-lane rate (the lane itself is near-zero marginal cost)
    cost = round(usage.get("completion_tokens", 0) * 0.0000002, 6)
    return {"text": res["text"], "model": mdl, "usage": usage, "cost_estimate": cost, "serves_truth": False}


# ── real Cloudflare Workers AI (BYO key; the customer's edge LLMs) ─────────────────────────────────
_CF_AI_BASE = "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1"
_CF_DEFAULT_MODEL = "@cf/meta/llama-3.3-70b-instruct"


def _cf_token() -> str:
    t = _env("CLOUDFLARE_API_TOKEN")
    return "" if t.startswith("replace-with") else t


def _cf_account() -> str:
    a = _env("CLOUDFLARE_ACCOUNT_ID")
    return "" if a.startswith("replace-with") else a


def cloudflare_ai_available() -> bool:
    return bool(_cf_token()) and bool(_cf_account()) and network_allowed()


def real_cloudflare_ai(prompt: str, *, system: str = "You are a precise extraction/synthesis engine.",
                       model: str = _CF_DEFAULT_MODEL, max_tokens: int = 800, timeout: int = 240,
                       token: str | None = None, account_id: str | None = None) -> dict:
    """A REAL LLM call on the customer's Cloudflare Workers AI (OpenAI-compatible endpoint). BYO: uses the customer
    token/account (from .env or passed in). Raises RealStepUnavailable if not configured. Runs on THEIR account."""
    tok, acct = token or _cf_token(), account_id or _cf_account()
    if not (tok and acct and network_allowed()):
        raise RealStepUnavailable("Cloudflare Workers AI not configured (CLOUDFLARE_API_TOKEN / CLOUDFLARE_ACCOUNT_ID / OH_INFERENCE_ALLOW_NETWORK)")
    from scripts._llm_client import chat
    prov = {"base_url": _CF_AI_BASE.format(account_id=acct), "key": tok, "headers": {}}
    res = chat(model, system, prompt, prov, max_tokens=max_tokens, timeout=timeout)
    if res["error"]:
        raise RealStepUnavailable(f"cloudflare_ai error: {res['error'][:200]}")
    return {"text": res["text"], "model": f"cloudflare:{model}", "usage": res.get("usage", {}),
            "cost_estimate": 0.0, "ran_on": "cloudflare_workers_ai", "billed_to": "customer_account", "serves_truth": False}


# ── real grounded search (free, no-key, returns source URLs) ───────────────────────────────────────
def real_wikipedia(query: str, *, limit: int = 3) -> list[dict]:
    """Real Wikipedia grounding: search → top page summaries with citable URLs. serves_truth=false (a source)."""
    if not network_allowed():
        raise RealStepUnavailable("network not allowed")
    params = urllib.parse.urlencode({"action": "query", "list": "search", "srsearch": query,
                                     "format": "json", "srlimit": limit})
    hits = _get_json(f"{_WIKI_SEARCH}?{params}").get("query", {}).get("search", [])
    out = []
    for h in hits[:limit]:
        title = h.get("title", "")
        try:
            s = _get_json(_WIKI_SUMMARY + urllib.parse.quote(title.replace(" ", "_")))
            out.append({"title": title, "snip": (s.get("extract") or "")[:400],
                        "url": s.get("content_urls", {}).get("desktop", {}).get("page", ""), "source": "wikipedia"})
        except Exception:
            continue
    return out


def real_federal_register(query: str, *, limit: int = 3) -> list[dict]:
    """Real US Federal Register grounding (signed GPO source-of-record). On-thesis for the compliance wedge."""
    if not network_allowed():
        raise RealStepUnavailable("network not allowed")
    params = urllib.parse.urlencode({"per_page": limit, "order": "newest", "conditions[term]": query})
    res = _get_json(f"{_FEDREG}?{params}").get("results", [])
    return [{"title": (r.get("title") or "")[:200], "snip": (r.get("abstract") or r.get("title") or "")[:400],
             "url": r.get("html_url", ""), "source": "federal_register",
             "published": r.get("publication_date", "")} for r in res[:limit]]


#: wired grounded-source adapters (handler per provider_id). A new ACTIVE registry provider becomes selectable by adding
#: its adapter here — the SELECTION is registry-driven, not a hardcoded default.
_WIRED_SEARCH = {"wikipedia": real_wikipedia, "federal_register": real_federal_register}
_SEARCH_REGISTRY = _REPO / "architecture" / "search_provider_registry.json"


def _active_search_providers() -> list[dict]:
    return [p for p in json.loads(_SEARCH_REGISTRY.read_text(encoding="utf-8"))["providers"] if p.get("status") == "active"]


def default_search_provider() -> str:
    """The cheapest ACTIVE registry provider that has a wired adapter (registry-driven; not the hardcoded 'wikipedia')."""
    for p in sorted(_active_search_providers(), key=lambda p: (p.get("cost_per_query_usd", 9.9), -p.get("quality_rank", 0))):
        if p["provider_id"] in _WIRED_SEARCH:
            return p["provider_id"]
    return next(iter(_WIRED_SEARCH))


def real_search(query: str, *, provider: str | None = None, limit: int = 3) -> list[dict]:
    """Dispatch to a real grounded provider SELECTED from architecture/search_provider_registry.json. provider=None ->
    the cheapest active WIRED provider; an unknown/unwired provider raises honestly (no silent hardcoded fallback)."""
    provider = provider or default_search_provider()
    if provider not in _WIRED_SEARCH:
        raise ValueError(f"search provider {provider!r} not wired; active registry providers: "
                         f"{[p['provider_id'] for p in _active_search_providers()]}; wired: {sorted(_WIRED_SEARCH)}")
    return _WIRED_SEARCH[provider](query, limit=limit)


# ── real text acquire ──────────────────────────────────────────────────────────────────────────────
def real_text(path: str | Path) -> str:
    """Real text-layer extraction from a real file (PDF/scan need pypdf/tesseract — absent — so text/markdown is the
    real acquire path here)."""
    p = Path(path)
    if not p.exists():
        raise RealStepUnavailable(f"no such document: {p}")
    if p.suffix.lower() in (".pdf", ".png", ".jpg", ".jpeg", ".tiff"):
        raise RealStepUnavailable(f"{p.suffix} needs pypdf/tesseract (not installed); use a text/markdown doc")
    return p.read_text(encoding="utf-8", errors="replace")
