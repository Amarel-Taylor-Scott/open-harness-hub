#!/usr/bin/env python3
"""Backs `processor/memory-agentic-hierarchy` (process_kind ``memory.agentic``).

Letta/MemGPT-style **working / long-term memory hierarchy**: on a
long-running task the context window is a budgeted working set, and this
processor decides — deterministically — which items page OUT to the
long-term store and which stored items page IN, so the agent stays inside
its token budget without ever losing a fact.

Paging policy (every weight a named constant):

  * **pinned items never page out.** If the pinned items alone exceed the
    budget the call raises ``ValueError`` — an impossible budget must be
    surfaced, never "solved" by silently dropping a pin.
  * unpinned working items are scored by relevance (caller-provided) blended
    with recency over an *injected* clock, and the lowest scores evict first.
  * eviction is a MOVE, not a delete: a paged-out item lands in the store
    with its full body plus ``paged_out_at`` (the lossless law — nothing
    vanishes; every input id ends the run in the working set or the store).
  * remaining budget pages IN the most relevant store items above
    ``PAGE_IN_MIN_RELEVANCE``.

Token counts use a **deterministic whitespace + punctuation tokenizer** (runs
of word characters vs. individual punctuation marks — the same proxy used by
``scripts.processors.compression.structural_compress``); it is NOT model BPE
and the envelope says so.

Runtime contract (matches the manifest): ``process_kind = memory.agentic``;
**deterministic** (injected time, stable ordering); **idempotent** (re-running
on the resulting state is a no-op); **side_effects = write** — but ONLY via
the explicitly injected ``store`` dict; **on_error = raise**.

Public API:
    from scripts.processors.memory.memory_agentic_hierarchy import run
    out = run(context=working_items, store=long_term, budget_tokens=2048, now=t)
    # -> {"paged": {"working_set": [...], "page_out": [...], "page_in": [...]}}

CLI / self-test:
    python3 scripts/processors/memory/memory_agentic_hierarchy.py
    python3 -m scripts.processors.memory.memory_agentic_hierarchy
"""
from __future__ import annotations

import json
import math
import re
from typing import Any

# ── Configuration constants (single source of truth; No-Magic-Values) ────────

#: Default working-set budget in proxy tokens. Sized for a few thousand words
#: of working context; callers pass their real window budget.
DEFAULT_BUDGET_TOKENS = 2048

#: Page score blend: relevance dominates (the agent keeps what the task
#: needs), recency breaks ties. Sums to 1.0 so scores stay in [0, 1].
RELEVANCE_WEIGHT = 0.7
RECENCY_WEIGHT = 0.3

#: Recency half-life for working items: 30 minutes (in seconds) — working-set
#: churn happens on task timescales, not the 7-day store half-life.
RECENCY_HALF_LIFE_SECONDS = 30 * 60.0

#: A stored item needs at least this relevance to be paged back in; below it,
#: pulling it in would spend budget on noise.
PAGE_IN_MIN_RELEVANCE = 0.5

#: Neutral relevance for items that do not declare one (mid-scale: neither
#: protected nor first to evict).
DEFAULT_RELEVANCE = 0.5

#: Tokenizer: a run of word characters is one token; each non-space, non-word
#: character is its own token. Deterministic proxy, NOT model BPE.
_TOKEN_RE = re.compile(r"\w+|[^\w\s]")

#: Score rounding (decimal places) so envelopes are stable across platforms.
SCORE_DECIMALS = 6


def _tokens(item: dict[str, Any]) -> int:
    return len(_TOKEN_RE.findall(str(item.get("text", ""))))


def _page_score(item: dict[str, Any], now: float) -> float:
    relevance = float(item.get("relevance", DEFAULT_RELEVANCE))
    age = max(0.0, float(now) - float(item.get("last_used_at", 0.0)))
    recency = math.pow(2.0, -age / RECENCY_HALF_LIFE_SECONDS)
    return round(RELEVANCE_WEIGHT * relevance + RECENCY_WEIGHT * recency, SCORE_DECIMALS)


def run(
    *,
    context: list[dict[str, Any]],
    store: dict[str, Any],
    budget_tokens: int = DEFAULT_BUDGET_TOKENS,
    now: float = 0.0,
) -> dict[str, Any]:
    """Page items between ``context`` (working set) and ``store`` to fit the budget.

    ``store`` is the long-term side: a dict carrying ``{"items": {id: item}}``
    (the key is created if missing; the dict OBJECT is the one mutated —
    side_effects=write happens only here). Returns ``{"paged": {...}}`` per
    the manifest's single output.
    """
    if not isinstance(context, list):
        raise TypeError(f"context must be a list of item dicts, got {type(context).__name__}")
    if not isinstance(store, dict):
        raise TypeError(f"store must be a dict, got {type(store).__name__}")
    if not isinstance(budget_tokens, int) or budget_tokens < 1:
        raise ValueError(f"budget_tokens must be a positive int, got {budget_tokens!r}")
    for item in context:
        if not isinstance(item, dict) or "id" not in item or "text" not in item:
            raise ValueError("every context item needs at least id and text")
    store_items: dict[str, dict[str, Any]] = store.setdefault("items", {})

    pinned = [i for i in context if i.get("pinned")]
    unpinned = [i for i in context if not i.get("pinned")]
    pinned_tokens = sum(_tokens(i) for i in pinned)
    if pinned_tokens > budget_tokens:
        raise ValueError(
            f"pinned items need {pinned_tokens} tokens but the budget is "
            f"{budget_tokens} — an impossible budget is an error, pins are never dropped")

    # Evict lowest-score unpinned items until the working set fits.
    # Sort: score asc, then id asc — the deterministic eviction order.
    by_evict_order = sorted(unpinned, key=lambda i: (_page_score(i, now), str(i["id"])))
    working = list(pinned) + [i for i in unpinned]
    used = pinned_tokens + sum(_tokens(i) for i in unpinned)
    page_out: list[str] = []
    for victim in by_evict_order:
        if used <= budget_tokens:
            break
        working = [i for i in working if i["id"] != victim["id"]]
        used -= _tokens(victim)
        stored = dict(victim)
        stored["paged_out_at"] = float(now)
        store_items[str(victim["id"])] = stored  # MOVE, never delete
        page_out.append(str(victim["id"]))

    # Page IN the most relevant stored items that fit the remaining budget.
    # Sort: relevance desc, then id asc — the deterministic admission order.
    working_ids = {str(i["id"]) for i in working}
    page_in: list[str] = []
    candidates = sorted(
        (it for iid, it in store_items.items()
         if iid not in working_ids
         and float(it.get("relevance", DEFAULT_RELEVANCE)) >= PAGE_IN_MIN_RELEVANCE),
        key=lambda it: (-float(it.get("relevance", DEFAULT_RELEVANCE)), str(it["id"])))
    for cand in candidates:
        cost = _tokens(cand)
        if used + cost > budget_tokens:
            continue
        admitted = {k: v for k, v in cand.items() if k != "paged_out_at"}
        admitted["last_used_at"] = float(now)
        working.append(admitted)
        working_ids.add(str(cand["id"]))
        used += cost
        del store_items[str(cand["id"])]  # the MOVE back — it lives in working now
        page_in.append(str(cand["id"]))

    working_order = sorted(str(i["id"]) for i in working)
    return {"paged": {
        "working_set": working_order,
        "page_out": page_out,
        "page_in": page_in,
        "tokens_used": used,
        "budget_tokens": budget_tokens,
        "pinned_kept": sorted(str(i["id"]) for i in pinned),
        "store_size_after": len(store_items),
        "tokenizer": "deterministic word/punct proxy (not model BPE)",
    }}


def _selftest() -> None:
    minute = 60.0
    now = 1_000 * minute
    sys_prompt = {"id": "sys", "text": "persona and rules " * 10, "pinned": True}
    hot = {"id": "hot", "text": "current subtask state " * 10,
           "relevance": 0.9, "last_used_at": now - 1 * minute}
    warm = {"id": "warm", "text": "useful reference table " * 10,
            "relevance": 0.6, "last_used_at": now - 20 * minute}
    cold = {"id": "cold", "text": "stale exploratory notes " * 10,
            "relevance": 0.1, "last_used_at": now - 300 * minute}
    context = [sys_prompt, hot, warm, cold]
    total = sum(len(_TOKEN_RE.findall(i["text"])) for i in context)

    # Budget forces one eviction: the lowest-score item (cold) goes, the pin stays.
    store: dict[str, Any] = {}
    budget = total - 1
    out = run(context=context, store=store, budget_tokens=budget, now=now)["paged"]
    assert out["page_out"] == ["cold"]
    assert "sys" in out["working_set"] and out["pinned_kept"] == ["sys"]
    assert out["tokens_used"] <= budget
    # Lossless: the evicted item is IN the store with its body + paged_out_at.
    assert store["items"]["cold"]["text"] == cold["text"]
    assert store["items"]["cold"]["paged_out_at"] == now
    # Every input id is accounted for: working or store.
    assert set(out["working_set"]) | set(store["items"]) >= {"sys", "hot", "warm", "cold"}

    # Pinned survives even at relevance 0 while unpinned strong items evict.
    s2: dict[str, Any] = {}
    pin0 = {"id": "pin0", "text": "must keep " * 5, "pinned": True, "relevance": 0.0}
    big = {"id": "big", "text": "evictable " * 50, "relevance": 0.95, "last_used_at": now}
    tight = len(_TOKEN_RE.findall(pin0["text"])) + 1
    o2 = run(context=[pin0, big], store=s2, budget_tokens=tight, now=now)["paged"]
    assert "pin0" in o2["working_set"] and o2["page_out"] == ["big"]

    # Impossible pinned budget raises (never silently drops a pin).
    raised = False
    try:
        run(context=[pin0], store={}, budget_tokens=1, now=now)
    except ValueError:
        raised = True
    assert raised, "pinned items over budget must raise ValueError"

    # Page-in: relevant stored items return when budget allows; weak ones stay.
    s3: dict[str, Any] = {"items": {
        "rel": {"id": "rel", "text": "highly relevant stored fact", "relevance": 0.9},
        "weak": {"id": "weak", "text": "barely related trivia", "relevance": 0.2},
    }}
    o3 = run(context=[sys_prompt], store=s3, budget_tokens=DEFAULT_BUDGET_TOKENS, now=now)["paged"]
    assert o3["page_in"] == ["rel"] and "rel" in o3["working_set"]
    assert "weak" in s3["items"] and "rel" not in s3["items"]

    # Idempotent: re-running on the resulting state is a no-op.
    ctx2 = [i for i in context if str(i["id"]) in out["working_set"]]
    again = run(context=ctx2, store=store, budget_tokens=budget, now=now)["paged"]
    assert again["page_out"] == [] and again["page_in"] == []
    assert again["working_set"] == out["working_set"]

    # Deterministic byte-identical repeat (fresh equal inputs).
    sA: dict[str, Any] = {}
    sB: dict[str, Any] = {}
    a = json.dumps(run(context=context, store=sA, budget_tokens=budget, now=now), sort_keys=True)
    b = json.dumps(run(context=context, store=sB, budget_tokens=budget, now=now), sort_keys=True)
    assert a == b and sA == sB

    # on_error=raise.
    raised = False
    try:
        run(context=[{"id": "x"}], store={}, budget_tokens=10, now=now)
    except ValueError:
        raised = True
    assert raised, "item without text must raise ValueError"
    raised = False
    try:
        run(context=[], store={}, budget_tokens=0, now=now)
    except ValueError:
        raised = True
    assert raised, "non-positive budget must raise ValueError"

    print(
        "PASS — memory_agentic_hierarchy: budgeted page-out/page-in (relevance"
        "+recency, deterministic order), pins never dropped (impossible budget "
        "raises), evictions MOVE to the store (lossless, every id accounted), "
        "no-op on settled state, byte-identical repeats verified"
    )


if __name__ == "__main__":
    _selftest()
