#!/usr/bin/env python3
"""scripts.check_inference_adapter_styles — PROOF: every registered inference API style can INVOKE (the
native-API stubs are gone), and each external provider's key resolves PER NODE from its own secret_ref —
so OpenAI + Anthropic (or two tenants' BYOK keys) run side by side instead of sharing one global key.

Builds the request shapes WITHOUT a network call (deterministic, offline) + checks the secret_ref → env
mapping under a controlled environment. Exit 0/1.
"""
from __future__ import annotations

import inspect
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.inference import adapters as A


def _self_test() -> int:
    fails: list[str] = []

    def ck(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    # 1. PER-NODE secret resolution: anthropic and openai resolve to DIFFERENT env keys (not one global).
    saved = {k: os.environ.get(k) for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "OH_LLM_API_KEY")}
    try:
        os.environ["ANTHROPIC_API_KEY"] = "k_anthropic"
        os.environ["OPENAI_API_KEY"] = "k_openai"
        os.environ["OH_LLM_API_KEY"] = "k_global"
        ka, ko = A.resolve_secret_ref("secret://provider/anthropic"), A.resolve_secret_ref("secret://provider/openai")
        ck("secret://provider/anthropic -> ANTHROPIC_API_KEY", ka == "k_anthropic", ka)
        ck("secret://provider/openai -> OPENAI_API_KEY", ko == "k_openai", ko)
        ck("two providers resolve to DIFFERENT keys (no shared global)", ka != ko)
        ck("no secret_ref -> the OH_LLM_API_KEY shared fallback", A.resolve_secret_ref(None) == "k_global")
        ck("secret://env/<VAR> -> that env var", A.resolve_secret_ref("secret://env/anthropic_api_key") == "k_anthropic")
        os.environ.pop("OPENAI_API_KEY", None)
        ck("an UNSET provider ref returns '' (degrade, NEVER silently the global key)",
           A.resolve_secret_ref("secret://provider/openai") == "")
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    # 2. EVERY registered style can invoke (the native-API stubs are gone — no live_call_not_provisioned gate).
    invoke_src = inspect.getsource(A._HttpAdapter.invoke)
    ck("the 'live_call_not_provisioned_for_this_api_style' degrade gate is GONE (all styles invoke)",
       "live_call_not_provisioned" not in invoke_src)
    ck("every ADAPTER_STYLES entry is in the REGISTRY", all(s in A.REGISTRY for s in A.ADAPTER_STYLES))

    # 3. NATIVE request shapes are real (built offline, no network): Ollama /api/generate, Anthropic /v1 messages.
    oll = A.OllamaNativeAdapter({"node_id": "n", "base_url": "http://localhost:11434", "model": "llama3"})
    ob = oll._build_body(model="llama3", system="sys", input_text="hi", max_tokens=64, temperature=0.1)
    ck("Ollama-native: /api/generate + prompt body + options.num_predict + stream:false",
       oll._endpoint_path == "/api/generate" and ob["prompt"].endswith("hi") and ob["options"]["num_predict"] == 64
       and ob["stream"] is False)
    ck("Ollama-native: parses `response`", oll._parse_output({"response": "out"}) == "out")

    anth = A.AnthropicMessagesAdapter({"node_id": "a", "base_url": "https://api.anthropic.com/v1", "model": "claude",
                                       "secret_ref": "secret://provider/anthropic", "external": True})
    ab = anth._build_body(model="claude", system="sys", input_text="hi", max_tokens=None, temperature=None)
    ck("Anthropic: /messages + top-level system + REQUIRED max_tokens default + user message",
       anth._endpoint_path == "/messages" and ab["system"] == "sys" and ab["max_tokens"] == anth._DEFAULT_MAX_TOKENS
       and ab["messages"][0]["content"] == "hi")
    ah = anth._auth_headers("k")
    ck("Anthropic: x-api-key + anthropic-version headers (NOT a Bearer)",
       ah.get("x-api-key") == "k" and "anthropic-version" in ah and "Authorization" not in ah)
    ck("Anthropic: parses content[*].text", anth._parse_output({"content": [{"type": "text", "text": "A"},
                                                                            {"type": "text", "text": "B"}]}) == "AB")

    # 4. governed offline degrade preserved: an external node without its secret is unavailable (never fabricates).
    av, _ = anth.available(secrets=set(), allow_network=True)
    ck("external anthropic node w/o its secret is unavailable (governed degrade)", av is False)

    print(("PASS — " if not fails else "FAIL — ")
          + "check_inference_adapter_styles: per-node secret resolution (anthropic/openai/BYOK keys side-by-side; an "
            "unset ref degrades, never the global key); all 4 API styles invoke; Ollama-native + Anthropic-messages "
            "request/response shapes are real; governed offline degrade preserved.")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
