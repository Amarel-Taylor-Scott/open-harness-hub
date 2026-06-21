"""scripts._llm_client — SHARED OpenAI-compatible LLM client (used by BOTH planes; depends on neither plane's tools).

The PRODUCT runtime (src/teleon/dag/real_steps) and the DEVELOPMENT tools (external_review / panel_review /
multi_model_improvement_loop) both need to call a model. Putting the client HERE (shared infra, like scripts/_jsonl_store)
means product never imports a dev tool and dev never owns product runtime. Provider lanes (Ollama Cloud default,
OpenRouter) + a reasoning-model-aware chat(). Keys are read from .env, never logged. serves_truth=false (a model call
returns a candidate, never truth). Offline-safe (no key -> error surfaced, not raised into the loop).
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

#: provider lanes (all OpenAI-compatible). base_url ends in /v1; the call hits {base_url}/chat/completions.
PROVIDERS = {
    "ollama": {"base_url_var": "OH_LLM_BASE_URL", "key_var": "OH_LLM_API_KEY",
               "models": ["glm-5.2", "kimi-k2.7-code"], "headers": {}},
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "key_var": "OPENROUTER_API_KEY",
                   "models": ["z-ai/glm-5.2", "moonshotai/kimi-k2.7-code"],
                   "headers": {"HTTP-Referer": "https://aidoneright.dev", "X-Title": "OpenHarnessHub"}},
}
DEFAULT_PROVIDER = "ollama"


def _env(var: str) -> str:
    f = REPO / ".env"
    if not f.exists():
        return ""
    for ln in f.read_text(encoding="utf-8").splitlines():
        if ln.startswith(f"{var}="):
            return ln.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def resolve_provider(name: str) -> dict:
    if name not in PROVIDERS:
        raise SystemExit(f"unknown provider {name!r}; have: {list(PROVIDERS)}")
    p = dict(PROVIDERS[name])
    p["base_url"] = p.get("base_url") or _env(p["base_url_var"])
    p["key"] = _env(p["key_var"])
    p["name"] = name
    return p


def chat(model: str, system: str, user: str, provider: dict, *, max_tokens: int = 8000, timeout: int = 300) -> dict:
    """One OpenAI-compatible chat call. Captures reasoning-model output (kimi puts text in `reasoning`, content empty).
    Returns {model, text, usage, finish_reason, error}. serves_truth=false."""
    url = provider["base_url"].rstrip("/") + "/chat/completions"
    body = json.dumps({"model": model, "messages": [{"role": "system", "content": system},
                                                    {"role": "user", "content": user}],
                       "temperature": 0.3, "max_tokens": max_tokens, "stream": False}).encode()
    headers = {"Authorization": f"Bearer {provider['key']}", "Content-Type": "application/json", **provider.get("headers", {})}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=headers), timeout=timeout) as r:
            d = json.loads(r.read().decode())
        choice = d["choices"][0]
        msg = choice.get("message", {})
        text = msg.get("content") or msg.get("reasoning") or msg.get("reasoning_content") or ""
        return {"model": model, "text": text, "usage": d.get("usage", {}), "finish_reason": choice.get("finish_reason"), "error": None}
    except Exception as e:  # noqa: BLE001 — surface provider/network errors; callers decide
        detail = ""
        if hasattr(e, "read"):
            try:
                detail = e.read().decode()[:500]
            except Exception:
                pass
        return {"model": model, "text": "", "usage": {}, "error": f"{type(e).__name__}: {e} {detail}"}


__all__ = ["PROVIDERS", "DEFAULT_PROVIDER", "resolve_provider", "chat"]
