"""Provider-neutral chat/LLM route for Open Harness Hub — local now, cloud later.

The text-generation sibling of ``scripts/embeddings.py``: ONE resolver, env-
driven, so builder polish / explanations / labeling run on a **local Gemma via
Ollama** today and a hosted model later with **no code change**. It is optional
and never the source of truth — if no model is reachable, ``complete()`` returns
``None`` and callers fall back to deterministic output.

Talks the OpenAI-compatible ``/chat/completions`` shape, which Ollama, vLLM,
LM Studio, OpenAI, Azure, Together, etc. all speak. Stdlib-only (``urllib``).

Environment:

  ===============  ========================================================
  OH_LLM_BACKEND   auto | http-openai | none           (default: auto)
  OH_LLM_BASE_URL  default http://localhost:11434/v1    (Ollama OpenAI-compat)
  OH_LLM_API_KEY   bearer token (optional for local servers)
  OH_LLM_MODEL     default "gemma2"  (any local/hosted chat model, e.g. Gemma 4)
  ===============  ========================================================
"""
from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass

DEFAULT_BASE_URL = "http://localhost:11434/v1"   # Ollama's OpenAI-compatible API
DEFAULT_MODEL = "gemma2"                          # swap to your local Gemma tag
_HEALTH_TIMEOUT_S = 2
_COMPLETE_TIMEOUT_S = 120


@dataclass
class ChatRoute:
    name: str            # http-openai | none
    model_id: str
    base_url: str | None
    api_key: str | None

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def health(self) -> bool:
        """Quick reachability probe (GET {base}/models). Never raises."""
        if self.name == "none" or not self.base_url:
            return False
        try:
            req = urllib.request.Request(self.base_url.rstrip("/") + "/models", headers=self._headers())
            with urllib.request.urlopen(req, timeout=_HEALTH_TIMEOUT_S) as resp:
                return resp.status == 200
        except Exception:
            return False

    def complete(self, system: str, user: str, *, max_tokens: int = 600,
                 temperature: float = 0.2) -> str | None:
        """Return assistant text, or None on any failure (caller falls back)."""
        if self.name == "none" or not self.base_url:
            return None
        payload = json.dumps({
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }).encode("utf-8")
        url = self.base_url.rstrip("/") + "/chat/completions"
        try:
            req = urllib.request.Request(url, data=payload, headers=self._headers(), method="POST")
            with urllib.request.urlopen(req, timeout=_COMPLETE_TIMEOUT_S) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
        except Exception:
            return None

    def summary(self) -> dict:
        return {"backend": self.name, "model": self.model_id, "base_url": self.base_url}


def resolve_route(model: str | None = None, backend: str | None = None) -> ChatRoute:
    backend = backend or os.environ.get("OH_LLM_BACKEND") or "auto"
    if backend == "none":
        return ChatRoute("none", model or "none", None, None)
    base_url = os.environ.get("OH_LLM_BASE_URL") or DEFAULT_BASE_URL
    api_key = os.environ.get("OH_LLM_API_KEY")
    model_id = model or os.environ.get("OH_LLM_MODEL") or DEFAULT_MODEL
    return ChatRoute("http-openai", model_id, base_url, api_key)


if __name__ == "__main__":
    r = resolve_route()
    print(json.dumps({**r.summary(), "reachable": r.health()}, indent=2))
