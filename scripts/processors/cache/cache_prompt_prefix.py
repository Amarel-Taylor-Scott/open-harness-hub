#!/usr/bin/env python3
"""Backs `processor/cache-prompt-prefix` (process_kind ``cache.prompt_prefix``).

**Provider prompt-cache marker**: split a prompt into its STABLE prefix
(system/persona messages + tool schemas + anything explicitly pinned) and its
VOLATILE suffix (the conversation turns), and emit the cache hint each
provider needs — an Anthropic ``cache_control`` breakpoint on the last stable
block (~90% read discount on cached tokens), and an OpenAI eligibility flag
(automatic prefix caching applies from 1,024 prefix tokens). This is the
"turn on first — free" optimization: no quality trade-off, pure cost/latency.

Token counts use a **deterministic whitespace + punctuation tokenizer** (runs
of word characters vs. individual punctuation marks — the same proxy used by
``scripts.processors.compression.structural_compress``). It is a proxy for
provider tokenizers, chosen because it is dependency-free and stable across
runs; eligibility near the 1,024-token boundary should be re-checked with the
provider's own counter, and the hint says so.

Runtime contract (matches the manifest):

  * ``process_kind = cache.prompt_prefix`` — CPU, no model, no network.
  * **deterministic** / **idempotent**: same prompt → byte-identical hint.
  * **side_effects = read**: pure function of its arguments.
  * **on_error = raise**: invalid arguments raise ``TypeError``/``ValueError``.

Public API:
    from scripts.processors.cache.cache_prompt_prefix import run
    out = run(prompt=[{"role": "system", "content": "..."},
                      {"role": "user", "content": "..."}],
              tools=[{"name": "search", "description": "..."}])
    # -> {"cache_hint": {"stable_prefix_tokens": ..., "providers": {...}}}

CLI / self-test:
    python3 scripts/processors/cache/cache_prompt_prefix.py
    python3 -m scripts.processors.cache.cache_prompt_prefix
"""
from __future__ import annotations

import json
import re
from typing import Any

# ── Configuration constants (single source of truth; No-Magic-Values) ────────

#: Tokenizer: a run of word characters is one token; each non-space, non-word
#: character is its own token. Deterministic proxy, NOT provider BPE.
_TOKEN_RE = re.compile(r"\w+|[^\w\s]")

#: OpenAI prompt caching activates automatically once the prompt prefix
#: reaches this many tokens (platform.openai.com/docs/guides/prompt-caching).
OPENAI_MIN_PREFIX_TOKENS = 1024

#: Anthropic prompt caching: cached-prefix reads are billed at ~10% of the
#: base input rate — a ~90% discount (docs.anthropic.com, prompt caching).
ANTHROPIC_READ_DISCOUNT = 0.9

#: Roles whose messages are stable by position when they LEAD the prompt.
STABLE_ROLES = frozenset({"system", "developer"})

#: A message may pin itself into the stable prefix explicitly.
STABLE_MARK_KEY = "cache"
STABLE_MARK_VALUE = "stable"


def _count_tokens(text: str) -> int:
    """The single token-counting site (deterministic proxy)."""
    return len(_TOKEN_RE.findall(text))


def _message_text(msg: dict[str, Any]) -> str:
    content = msg.get("content", "")
    if not isinstance(content, str):
        content = json.dumps(content, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return content


def run(*, prompt: str | list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Mark the stable prefix of ``prompt`` and emit per-provider cache hints.

    ``prompt`` is either a raw string (no structure → nothing is provably
    stable, and the hint honestly says to structure the prompt) or a list of
    message dicts (``{"role": ..., "content": ...}``). Tool schemas, when
    passed, are part of the stable prefix — providers serialize them ahead of
    the conversation.

    Returns ``{"cache_hint": {...}}`` per the manifest's single output.
    """
    if tools is not None and not isinstance(tools, list):
        raise TypeError(f"tools must be a list of schema dicts or None, got {type(tools).__name__}")
    tools_tokens = sum(
        _count_tokens(json.dumps(t, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
        for t in (tools or []))

    if isinstance(prompt, str):
        # Unstructured text: we cannot prove any of it is stable.
        stable_tokens, volatile_tokens, breakpoint_index = 0, _count_tokens(prompt), 0
        stable_blocks: list[int] = []
    elif isinstance(prompt, list):
        # The stable prefix is the LEADING run of system/developer/pinned
        # messages; the first conversational turn ends it (prefix caching is
        # positional — a stable block AFTER a volatile one cannot cache).
        breakpoint_index = 0
        for msg in prompt:
            if not isinstance(msg, dict):
                raise TypeError("prompt messages must be dicts with role/content")
            is_stable = (msg.get("role") in STABLE_ROLES
                         or msg.get(STABLE_MARK_KEY) == STABLE_MARK_VALUE)
            if not is_stable:
                break
            breakpoint_index += 1
        stable_blocks = list(range(breakpoint_index))
        stable_tokens = sum(_count_tokens(_message_text(m)) for m in prompt[:breakpoint_index])
        volatile_tokens = sum(_count_tokens(_message_text(m)) for m in prompt[breakpoint_index:])
    else:
        raise TypeError(f"prompt must be str or list of message dicts, got {type(prompt).__name__}")

    stable_total = stable_tokens + tools_tokens
    openai_eligible = stable_total >= OPENAI_MIN_PREFIX_TOKENS
    if stable_total == 0:
        recommendation = ("no stable prefix found — move persona/system text and tool "
                          "schemas into leading system messages so providers can cache them")
    elif not openai_eligible:
        recommendation = (f"stable prefix is {stable_total} proxy tokens; Anthropic cache_control "
                          f"applies now, OpenAI automatic caching needs >= {OPENAI_MIN_PREFIX_TOKENS} "
                          "(re-check near the boundary with the provider tokenizer)")
    else:
        recommendation = "stable prefix is cacheable on both providers — enable cache_control and keep the prefix byte-stable"

    hint: dict[str, Any] = {
        "stable_prefix_tokens": stable_total,
        "volatile_suffix_tokens": volatile_tokens,
        "breakpoint_index": breakpoint_index,
        "tools_tokens": tools_tokens,
        "providers": {
            "anthropic": {
                "mechanism": "cache_control",
                "breakpoints": stable_blocks,
                "estimated_read_discount": ANTHROPIC_READ_DISCOUNT,
            },
            "openai": {
                "mechanism": "automatic_prefix",
                "eligible": openai_eligible,
                "min_prefix_tokens": OPENAI_MIN_PREFIX_TOKENS,
            },
        },
        "tokenizer": "deterministic word/punct proxy (not provider BPE)",
        "recommendation": recommendation,
    }
    return {"cache_hint": hint}


def _selftest() -> None:
    system_text = "You are the compliance copilot. Cite the governing source for every claim. " * 40
    tools = [{"name": "sanctions_lookup", "description": "Screen a name against the SDN list",
              "parameters": {"type": "object", "properties": {"name": {"type": "string"}}}}]
    msgs = [
        {"role": "system", "content": system_text},
        {"role": "user", "content": "Screen Novaya Commerce LLC."},
        {"role": "assistant", "content": "Checking the SDN list now."},
    ]

    out = run(prompt=msgs, tools=tools)["cache_hint"]
    assert out["breakpoint_index"] == 1  # the system message, then conversation starts
    assert out["stable_prefix_tokens"] > 0 and out["volatile_suffix_tokens"] > 0
    assert out["tools_tokens"] > 0
    assert out["providers"]["anthropic"]["breakpoints"] == [0]
    assert out["providers"]["anthropic"]["estimated_read_discount"] == ANTHROPIC_READ_DISCOUNT

    # OpenAI eligibility flips exactly at the documented 1,024-token floor.
    assert out["providers"]["openai"]["eligible"] is (
        out["stable_prefix_tokens"] >= OPENAI_MIN_PREFIX_TOKENS)

    # An explicitly pinned leading block joins the stable prefix.
    pinned = [{"role": "system", "content": "persona"},
              {"cache": "stable", "role": "user", "content": "Glossary: SDN = Specially Designated Nationals."},
              {"role": "user", "content": "fresh question"}]
    p = run(prompt=pinned)["cache_hint"]
    assert p["breakpoint_index"] == 2 and p["providers"]["anthropic"]["breakpoints"] == [0, 1]

    # Stability is positional: a system message AFTER a user turn is volatile.
    trailing = [{"role": "user", "content": "hi"}, {"role": "system", "content": system_text}]
    t = run(prompt=trailing)["cache_hint"]
    assert t["breakpoint_index"] == 0 and t["stable_prefix_tokens"] == 0

    # Editing only the volatile suffix never changes the stable-prefix result.
    msgs2 = [msgs[0], {"role": "user", "content": "Screen Meridian Capital Ventures instead."}]
    out2 = run(prompt=msgs2, tools=tools)["cache_hint"]
    assert out2["stable_prefix_tokens"] == out["stable_prefix_tokens"]
    assert out2["breakpoint_index"] == out["breakpoint_index"]

    # A raw string prompt is honestly all-volatile with guidance.
    s = run(prompt="just one big unstructured prompt string")["cache_hint"]
    assert s["stable_prefix_tokens"] == 0 and s["providers"]["openai"]["eligible"] is False
    assert "no stable prefix" in s["recommendation"]

    # Deterministic + idempotent: byte-identical repeats.
    a = json.dumps(run(prompt=msgs, tools=tools), sort_keys=True)
    b = json.dumps(run(prompt=msgs, tools=tools), sort_keys=True)
    assert a == b

    # on_error=raise: malformed inputs raise.
    raised = False
    try:
        run(prompt=42)  # type: ignore[arg-type]
    except TypeError:
        raised = True
    assert raised, "non-str/list prompt must raise TypeError"
    raised = False
    try:
        run(prompt=["not a dict"])  # type: ignore[list-item]
    except TypeError:
        raised = True
    assert raised, "non-dict message must raise TypeError"

    print(
        "PASS — cache_prompt_prefix: leading-stable-block detection (system + "
        "pinned + tool schemas), positional stability, Anthropic cache_control "
        f"breakpoints (~{int(ANTHROPIC_READ_DISCOUNT * 100)}% read discount), OpenAI "
        f">={OPENAI_MIN_PREFIX_TOKENS}-token eligibility, honest unstructured-prompt "
        "guidance, deterministic verified"
    )


if __name__ == "__main__":
    _selftest()
