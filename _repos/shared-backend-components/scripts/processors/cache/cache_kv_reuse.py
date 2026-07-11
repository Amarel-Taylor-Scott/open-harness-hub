#!/usr/bin/env python3
"""Backs `processor/cache-kv-reuse` (process_kind ``cache.kv_reuse``).

LMCache-style **KV-cache reuse planner** for self-hosted inference: when a new
prompt shares a prefix with one already run through the model, the attention
KV tensors for that prefix can be loaded instead of recomputed — LMCache
reports up to ~7× faster time-to-first-token on long shared prefixes. This
module does NOT hold GPU tensors; it is the deterministic *planning* half:
given a prompt prefix and a registry of previously-cached prefixes, find the
longest reusable token prefix for the same model and emit a reuse plan the
serving layer can act on.

Token counts use a **deterministic whitespace + punctuation tokenizer** (runs
of word characters vs. individual punctuation marks — the same proxy used by
``scripts.processors.compression.structural_compress``). It is a proxy for
the model's real tokenizer, chosen because it is dependency-free and stable
across runs; reuse fractions it reports track real-tokenizer fractions
closely, but it is NOT the serving tokenizer and the plan says so.

Hard rules (tested):

  * **KV is model-specific** — an entry only matches a request with the SAME
    ``model_id``; tensors from one model are garbage to another.
  * **Prefix means prefix** — reuse counts only a CONTIGUOUS token match from
    position 0, on whole-token boundaries (never half a token).

Runtime contract (matches the manifest):

  * ``process_kind = cache.kv_reuse`` — CPU planning, no model, no network.
  * **deterministic** / **idempotent**: same inputs → byte-identical plan.
  * **side_effects = read**: ``run()`` only READS the registry; writing is the
    explicit ``register()`` helper.
  * **on_error = raise**: invalid arguments raise ``TypeError``/``ValueError``.

Public API:
    from scripts.processors.cache.cache_kv_reuse import register, run
    register(store, system_plus_tools_text, model_id="llama-3.1-8b", now=t0)
    out = run(prefix=new_prompt_text, store=store, model_id="llama-3.1-8b")
    # -> {"kv": {"reusable": True, "matched_tokens": 812, "reuse_fraction": ...}}

CLI / self-test:
    python3 _repos/shared-backend-components/scripts/processors/cache/cache_kv_reuse.py
    python3 -m scripts.processors.cache.cache_kv_reuse
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, MutableMapping

# ── Configuration constants (single source of truth; No-Magic-Values) ────────

#: Tokenizer: a run of word characters is one token; each non-space,
#: non-word character is its own token. Deterministic proxy, NOT billing/
#: serving-grade BPE (stated in the module docstring and in every plan).
_TOKEN_RE = re.compile(r"\w+|[^\w\s]")

#: TTFT speedup model: linear from 1.0× (no reuse) to MAX_TTFT_SPEEDUP at 100%
#: prefix reuse. The ceiling is LMCache's headline "up to 7× faster
#: time-to-first-token" figure (github.com/LMCache/LMCache); real speedup
#: depends on hardware and prefix length, so this is an ESTIMATE for routing
#: decisions, not a promise.
MAX_TTFT_SPEEDUP = 7.0
MIN_TTFT_SPEEDUP = 1.0  # no reuse → no speedup

#: Entries shorter than this many tokens are not worth registering: loading
#: KV for a trivial prefix costs more than recomputing it.
MIN_REGISTER_TOKENS = 8

#: Hash algorithm + prefix for entry ids (self-describing, future-proof).
HASH_ALGORITHM = "sha256"
ENTRY_ID_PREFIX = "kv:"


def tokenize(text: str) -> list[str]:
    """The single tokenization site for both registration and planning."""
    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__}")
    return _TOKEN_RE.findall(text)


def _entry_id(model_id: str, tokens: list[str]) -> str:
    payload = json.dumps({"model_id": model_id, "tokens": tokens},
                         sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return ENTRY_ID_PREFIX + hashlib.new(HASH_ALGORITHM, payload.encode("utf-8")).hexdigest()


def register(
    store: MutableMapping[str, Any],
    prompt_text: str,
    *,
    model_id: str,
    now: float,
) -> str | None:
    """Record a served prompt's prefix as reusable KV. Explicit, never implicit.

    Returns the entry id, or ``None`` when the prompt is shorter than
    ``MIN_REGISTER_TOKENS`` (registering it would cost more than it saves).
    ``now`` is injected (no wall clock) so registries are replayable.
    """
    if not isinstance(model_id, str) or not model_id:
        raise ValueError("model_id must be a non-empty str")
    tokens = tokenize(prompt_text)
    if len(tokens) < MIN_REGISTER_TOKENS:
        return None
    eid = _entry_id(model_id, tokens)
    store[eid] = {"model_id": model_id, "tokens": tokens, "registered_at": float(now)}
    return eid


def run(
    *,
    prefix: str,
    store: MutableMapping[str, Any] | None = None,
    model_id: str,
) -> dict[str, Any]:
    """Plan KV reuse for ``prefix`` against the injected registry (read-only).

    Returns ``{"kv": {...}}`` per the manifest's single ``kv`` output: the
    LONGEST contiguous whole-token prefix match among same-model entries, with
    an honest ``reusable: False`` plan when nothing matches.
    """
    if not isinstance(model_id, str) or not model_id:
        raise ValueError("model_id must be a non-empty str")
    want = tokenize(prefix)  # raises TypeError on non-str
    total = len(want)
    plan: dict[str, Any] = {
        "reusable": False, "matched_tokens": 0, "total_tokens": total,
        "reuse_fraction": 0.0, "cache_entry_id": None,
        "estimated_ttft_speedup": MIN_TTFT_SPEEDUP, "model_id": model_id,
        "tokenizer": "deterministic word/punct proxy (not serving BPE)",
    }
    if store is None or total == 0:
        return {"kv": plan}
    best_len = 0
    best_id: str | None = None
    for eid in sorted(store):  # sorted: deterministic tie-breaks
        entry = store[eid]
        if entry.get("model_id") != model_id:
            continue  # KV is model-specific — never cross models
        have = entry["tokens"]
        n = 0
        for a, b in zip(want, have):
            if a != b:
                break
            n += 1
        if n > best_len:
            best_len, best_id = n, eid
    if best_len > 0 and best_id is not None:
        fraction = best_len / total
        plan.update(
            reusable=True, matched_tokens=best_len,
            reuse_fraction=round(fraction, 6), cache_entry_id=best_id,
            estimated_ttft_speedup=round(
                MIN_TTFT_SPEEDUP + (MAX_TTFT_SPEEDUP - MIN_TTFT_SPEEDUP) * fraction, 3),
        )
    return {"kv": plan}


def _selftest() -> None:
    store: dict[str, Any] = {}
    system = ("You are a compliance assistant. Always cite the governing source. "
              "Tools: sanctions_lookup(name), ownership_graph(entity).")
    eid = register(store, system, model_id="llama-3.1-8b", now=100.0)
    assert eid is not None and eid in store

    # A prompt extending the registered prefix reuses ALL registered tokens.
    prompt = system + " User: screen Novaya Commerce LLC against the SDN list."
    plan = run(prefix=prompt, store=store, model_id="llama-3.1-8b")["kv"]
    assert plan["reusable"] is True and plan["cache_entry_id"] == eid
    assert plan["matched_tokens"] == len(tokenize(system))
    assert 0.0 < plan["reuse_fraction"] < 1.0
    assert MIN_TTFT_SPEEDUP < plan["estimated_ttft_speedup"] <= MAX_TTFT_SPEEDUP

    # KV is model-specific: the same text under another model never matches.
    other = run(prefix=prompt, store=store, model_id="qwen-2.5-7b")["kv"]
    assert other["reusable"] is False and other["matched_tokens"] == 0
    assert other["estimated_ttft_speedup"] == MIN_TTFT_SPEEDUP

    # Prefix means prefix: a mid-string overlap (different first token) is no match.
    mid = "IMPORTANT " + system
    assert run(prefix=mid, store=store, model_id="llama-3.1-8b")["kv"]["matched_tokens"] == 0

    # Whole-token boundaries: a prompt diverging INSIDE a word stops at the
    # last fully-matching token, never half a token.
    diverge = system.replace("ownership_graph", "ownership_tree")
    dplan = run(prefix=diverge, store=store, model_id="llama-3.1-8b")["kv"]
    assert 0 < dplan["matched_tokens"] < len(tokenize(system))

    # Longest match wins among multiple entries.
    longer = system + " User: screen"
    eid2 = register(store, longer, model_id="llama-3.1-8b", now=101.0)
    plan2 = run(prefix=prompt, store=store, model_id="llama-3.1-8b")["kv"]
    assert plan2["cache_entry_id"] == eid2
    assert plan2["matched_tokens"] == len(tokenize(longer))

    # Trivially short prompts are not registered (honest None).
    assert register(store, "hi there", model_id="llama-3.1-8b", now=102.0) is None

    # Deterministic + idempotent: byte-identical repeat; read-only run().
    a = json.dumps(run(prefix=prompt, store=store, model_id="llama-3.1-8b"), sort_keys=True)
    b = json.dumps(run(prefix=prompt, store=store, model_id="llama-3.1-8b"), sort_keys=True)
    assert a == b
    before = dict(store)
    run(prefix="unrelated text entirely", store=store, model_id="llama-3.1-8b")
    assert store == before

    # on_error=raise: bad types raise.
    raised = False
    try:
        run(prefix=42, store=store, model_id="llama-3.1-8b")  # type: ignore[arg-type]
    except TypeError:
        raised = True
    assert raised, "non-str prefix must raise TypeError"
    raised = False
    try:
        run(prefix="x", store=store, model_id="")
    except ValueError:
        raised = True
    assert raised, "empty model_id must raise ValueError"

    print(
        "PASS — cache_kv_reuse: longest contiguous whole-token prefix planning, "
        "model-scoped entries (no cross-model KV), honest no-reuse plans, "
        f"linear TTFT estimate capped at {MAX_TTFT_SPEEDUP}x (LMCache figure), "
        "deterministic + read-only run() verified"
    )


if __name__ == "__main__":
    _selftest()
