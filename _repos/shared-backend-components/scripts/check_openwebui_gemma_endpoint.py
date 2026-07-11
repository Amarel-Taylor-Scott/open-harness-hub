#!/usr/bin/env python3
"""Check the Open WebUI Gemma coding endpoint configuration.

Offline mode validates provider wiring only. Live mode performs one direct
bearer-token chat call and writes no credentials.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    OPENWEBUI_CHAT_COMPLETIONS_PATH,
    OPENWEBUI_DEFAULT_MODEL,
    OPENWEBUI_TOKEN_ENV,
)
from scripts._llm_client import PROVIDERS, chat, resolve_provider  # noqa: E402
from scripts.openwebui_cdp_client import cdp_chat, redacted_plan  # noqa: E402


def self_test(*, live: bool, prompt: str, mode: str, cdp_url: str, max_tokens: int, timeout: int) -> dict:
    provider = resolve_provider("openwebui")
    configured = PROVIDERS["openwebui"]
    result: dict = {}
    if configured.get("chat_path") != OPENWEBUI_CHAT_COMPLETIONS_PATH:
        raise AssertionError("Open WebUI provider must use /api/chat/completions")
    if OPENWEBUI_DEFAULT_MODEL not in configured.get("models", []):
        raise AssertionError("Open WebUI provider must expose the configured Gemma coding model")
    if not provider.get("base_url"):
        raise AssertionError("Open WebUI provider must resolve a base URL")

    if live:
        if mode == "direct" and not provider.get("key"):
            raise AssertionError(f"--live requires {OPENWEBUI_TOKEN_ENV}")
        if mode == "cdp":
            normalized = cdp_chat(
                prompt,
                system="Return exactly what the user asks for. No prose.",
                model=OPENWEBUI_DEFAULT_MODEL,
                base_url=str(provider.get("base_url") or ""),
                cdp_url=cdp_url or None,
                max_tokens=max_tokens,
                timeout=timeout,
            )
            result = {
                "text": normalized.get("assistant_content") or "",
                "usage": normalized.get("usage") or {},
                "finish_reason": normalized.get("finish_reason"),
                "http_status": normalized.get("http_status"),
            }
        else:
            result = chat(
                OPENWEBUI_DEFAULT_MODEL,
                "Return exactly what the user asks for. No prose.",
                prompt,
                provider,
                max_tokens=max_tokens,
                timeout=timeout,
            )
            if result.get("error"):
                raise AssertionError(str(result["error"]))
        if prompt.split(":", 1)[-1].strip() not in str(result.get("text") or ""):
            raise AssertionError("live response did not contain the expected sentinel")

    return {
        "record_type": "openwebui_gemma_endpoint_check",
        "provider": "openwebui",
        "mode": mode,
        "base_url_configured": bool(provider.get("base_url")),
        "chat_path": configured.get("chat_path"),
        "model": OPENWEBUI_DEFAULT_MODEL,
        "token_configured": bool(provider.get("key")),
        "cdp_plan": redacted_plan(mode="cdp", cdp_url=cdp_url) if mode == "cdp" else {},
        "live": live,
        "assistant_content": result.get("text", "") if live else "",
        "usage": result.get("usage", {}) if live else {},
        "candidate": True,
        "serves_truth": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--mode", choices=["direct", "cdp"], default="direct")
    parser.add_argument("--cdp-url", default="")
    parser.add_argument("--prompt", default="Print exactly: Open WebUI integration OK")
    parser.add_argument("--max-tokens", type=int, default=64)
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args(argv)
    try:
        result = self_test(
            live=args.live,
            prompt=args.prompt,
            mode=args.mode,
            cdp_url=args.cdp_url,
            max_tokens=args.max_tokens,
            timeout=args.timeout,
        )
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
