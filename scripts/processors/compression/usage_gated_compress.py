#!/usr/bin/env python3
"""Backs `processor/usage-gated-compress` (process_kind ``compress.usage_gated``).

Prediction-error-gated context retention — the Friston move applied to context
serving. A transformer is stateless: it re-pays the full prefill cost of every
context item on every turn, even items it has already absorbed and could
predict. The brain does the opposite — it carries a learned generative model
and spends expensive bits only where prediction FAILS (Raichle's "dark
energy"; Friston's free-energy principle). This planner brings that to the
compression phase: it keeps a **usage prior** learned from past turns and
spends token fidelity only on the context that is surprising or
demonstrably load-bearing, compressing hard on the predictable, re-read-as-
ritual remainder.

How it differs from the prior art (both model-INTERNAL, single-pass):
  * H2O (arXiv 2306.14048) gates the KV cache by attention scores — decoding-
    phase, and by its own admission does NOT reduce prefill. This gates
    PREFILL (the re-read cost) and needs no model internals.
  * LLMLingua / LongLLMLingua score one prompt by a small model's perplexity,
    stateless across turns. This is model-EXTERNAL and CROSS-TURN: the signal
    is demonstrated usage history, not a forward pass.

The three signals (per context item, accumulated across turns):
  * utility    = cited / served      — bottom-up "this actually mattered".
  * volatility = changed / served    — the source's own prediction-error rate
                                       (a file that keeps changing must be
                                       re-read; a frozen one can be predicted).
  * recency    = decay since last cited.
A NEW item (no prior) is treated as maximally surprising and kept FULL —
novelty is high free energy; the brain never compresses what it hasn't seen.

Tiers, assigned greedily under a token budget (highest priority first):
  FULL (verbatim) → SUMMARY (a hard-compressed gist, handle kept) →
  HANDLE_ONLY (dropped to a ``ctx://`` source handle + one-line gist).
LOSSLESS LAW: a HANDLE_ONLY item is NEVER deleted — it is returned in
``paged_out`` with its handle, rehydratable. When a later turn references a
paged-out item, that is a PREDICTION MISS: ``observe()`` records the
citation, utility jumps, and the next plan keeps it FULL. That feedback loop
IS the learning — the prior tunes itself to reduce future free energy, exactly
like the brain refining its generative model.

Runtime contract:
  * ``process_kind = compress.usage_gated`` — CPU planning, no model, no network.
  * **deterministic**: same items + prior + budget + now → byte-identical plan.
  * **side_effects = none**: ``run()`` is a pure planner; ``observe()`` returns
    a NEW prior (never mutates the one it is handed).
  * **on_error = raise**.

Token counts use the deterministic word/punct proxy shared across this package
(NOT model BPE; stated in the plan).

Public API:
    from scripts.processors.compression.usage_gated_compress import run, observe, empty_prior
    prior = empty_prior()
    plan = run(items=[...], prior=prior, token_budget=2000, now_turn=5)["plan"]
    prior = observe(prior, served_ids=[...], cited_ids=[...], changed_ids=[...], now_turn=5)

CLI / self-test:
    python3 scripts/processors/compression/usage_gated_compress.py
    python3 -m scripts.processors.compression.usage_gated_compress
"""
from __future__ import annotations

import json
import math
import re
from typing import Any

# ── Configuration constants (single source of truth; No-Magic-Values) ─────────

#: Priority blend. Utility dominates (a cited item is proven load-bearing);
#: volatility is next (a changing source can't be predicted, so re-read it);
#: recency breaks ties. They sum to 1.0 so priority stays in [0, 1].
W_UTILITY = 0.55
W_VOLATILITY = 0.30
W_RECENCY = 0.15

#: Recency half-life in TURNS: a citation's recency weight halves every 8
#: turns. Conversation-scale, not wall-clock.
RECENCY_HALF_LIFE_TURNS = 8.0

#: Cold-start priority for an item with NO usage history — novelty is high
#: free energy, so an unseen item outranks all but proven-critical items and
#: is kept FULL until usage shows it is predictable. Just below a perfect
#: utility score so a repeatedly-cited item still wins.
COLD_START_PRIORITY = 0.9

#: Pinned items are always FULL regardless of budget (system prompt, the
#: live task) — if pins alone exceed budget the call raises (an impossible
#: budget is surfaced, never silently dropped).
#: Retention tiers (single definition; callers/tests read these).
TIER_FULL = "full"
TIER_SUMMARY = "summary"
TIER_HANDLE_ONLY = "handle_only"

#: Estimated retained-token fraction per tier (the planner does not itself
#: rewrite text — structural_compress / llmlingua_compress do — it estimates
#: the budget each tier costs so the plan fits). SUMMARY ~ a 5x compression;
#: HANDLE_ONLY ~ a short handle + gist line.
TIER_KEEP_FRACTION = {TIER_FULL: 1.0, TIER_SUMMARY: 0.2}
HANDLE_ONLY_TOKENS = 24  # a ctx:// handle + a one-line gist

#: Tokenizer: a run of word chars is one token; each punctuation mark its own.
#: Deterministic proxy, NOT model BPE (stated in every plan).
_TOKEN_RE = re.compile(r"\w+|[^\w\s]")
TOKENIZER_NOTE = "deterministic word/punct proxy (not model BPE)"
SCORE_DECIMALS = 6


def empty_prior() -> dict[str, Any]:
    """A fresh usage prior — the learned generative model before any turns."""
    return {"schema": "usage-prior.v1", "items": {}}


def _count_tokens(text: str) -> int:
    return len(_TOKEN_RE.findall(text))


def _stats(prior: dict[str, Any], item_id: str) -> dict[str, int]:
    return prior.get("items", {}).get(item_id, {})


def _priority(stats: dict[str, int], now_turn: int,
              weights: dict[str, float] | None = None) -> tuple[float, dict[str, float]]:
    """The Friston gate: spend fidelity where prediction fails or use is proven.

    ``weights`` (utility/volatility/recency, e.g. from ``cohort_policy_selector``) overrides
    the module defaults so the gate follows the tenant's cohort curve; None = the defaults."""
    w_u = (weights or {}).get("utility", W_UTILITY)
    w_v = (weights or {}).get("volatility", W_VOLATILITY)
    w_r = (weights or {}).get("recency", W_RECENCY)
    served = int(stats.get("served", 0))
    if served == 0:
        # Unseen → maximally surprising → keep. (Novelty is high free energy.)
        return COLD_START_PRIORITY, {"utility": 0.0, "volatility": 0.0,
                                     "recency": 0.0, "cold_start": 1.0}
    utility = stats.get("cited", 0) / served
    volatility = stats.get("changed", 0) / served
    last_cited = stats.get("last_cited_turn")
    if last_cited is None:
        recency = 0.0
    else:
        age = max(0, int(now_turn) - int(last_cited))
        recency = math.pow(2.0, -age / RECENCY_HALF_LIFE_TURNS)
    priority = w_u * utility + w_v * volatility + w_r * recency
    return round(priority, SCORE_DECIMALS), {
        "utility": round(utility, SCORE_DECIMALS),
        "volatility": round(volatility, SCORE_DECIMALS),
        "recency": round(recency, SCORE_DECIMALS), "cold_start": 0.0}


def run(*, items: list[dict[str, Any]], prior: dict[str, Any] | None = None,
        token_budget: int, now_turn: int = 0,
        weights: dict[str, float] | None = None) -> dict[str, Any]:
    """Plan per-item fidelity tiers under ``token_budget`` using the usage prior.

    Each item: ``{"id", "text", optional "pinned": bool, optional "handle"}``.
    ``weights`` (utility/volatility/recency) overrides the default gate blend — pass the
    ``cohort_policy_selector`` policy's weights to follow the tenant's cohort curve.
    Returns ``{"plan": {...}}`` — tiers, the lossless ``paged_out`` list, and the estimated
    re-read saving (the Friston payoff).
    """
    if not isinstance(items, list):
        raise TypeError("items must be a list of id/text dicts")
    if not isinstance(token_budget, int) or token_budget < 1:
        raise ValueError(f"token_budget must be a positive int, got {token_budget!r}")
    prior = prior if prior is not None else empty_prior()
    rows: list[dict[str, Any]] = []
    for i, it in enumerate(items):
        if not isinstance(it, dict) or "id" not in it or "text" not in it:
            raise ValueError(f"items[{i}] needs id and text")
        full_tokens = _count_tokens(str(it["text"]))
        priority, breakdown = _priority(_stats(prior, str(it["id"])), now_turn, weights)
        rows.append({"id": str(it["id"]), "pinned": bool(it.get("pinned")),
                     "handle": it.get("handle") or f"ctx://{it['id']}",
                     "full_tokens": full_tokens, "priority": priority,
                     "priority_breakdown": breakdown, "text": str(it["text"])})

    pinned_tokens = sum(r["full_tokens"] for r in rows if r["pinned"])
    if pinned_tokens > token_budget:
        raise ValueError(f"pinned items need {pinned_tokens} tokens but the budget is "
                         f"{token_budget} — an impossible budget is an error, pins are never dropped")

    # Highest priority first; id as the deterministic tie-break. Pins float to
    # the top so they are assigned (and kept FULL) before any pressure.
    rows.sort(key=lambda r: (0 if r["pinned"] else 1, -r["priority"], r["id"]))

    used = 0
    full_reread = 0  # tokens that a naive (keep-everything) prefill would re-read
    tiers: dict[str, list[str]] = {TIER_FULL: [], TIER_SUMMARY: [], TIER_HANDLE_ONLY: []}
    plan_items: list[dict[str, Any]] = []
    paged_out: list[dict[str, Any]] = []
    for r in rows:
        full_reread += r["full_tokens"]
        full_cost = r["full_tokens"]
        summary_cost = max(1, math.ceil(r["full_tokens"] * TIER_KEEP_FRACTION[TIER_SUMMARY]))
        if r["pinned"] or used + full_cost <= token_budget:
            tier, cost = TIER_FULL, full_cost
        elif used + summary_cost <= token_budget:
            tier, cost = TIER_SUMMARY, summary_cost
        else:
            tier, cost = TIER_HANDLE_ONLY, HANDLE_ONLY_TOKENS
        # If even the handle would overflow, it still pages out (handle is the
        # floor — the item is preserved by reference, never silently lost).
        if tier == TIER_HANDLE_ONLY:
            paged_out.append({"id": r["id"], "handle": r["handle"],
                              "gist": _gist(r["text"])})
        else:
            used += cost
        tiers[tier].append(r["id"])
        plan_items.append({"id": r["id"], "tier": tier, "priority": r["priority"],
                           "priority_breakdown": r["priority_breakdown"],
                           "est_tokens": cost, "full_tokens": r["full_tokens"],
                           "reason": _reason(r, tier)})

    kept = used
    return {"plan": {
        "items": sorted(plan_items, key=lambda p: p["id"]),
        "tiers": {k: sorted(v) for k, v in tiers.items()},
        "paged_out": sorted(paged_out, key=lambda p: p["id"]),
        "tokens_kept": kept,
        "tokens_budget": token_budget,
        "naive_reread_tokens": full_reread,
        "predicted_reread_savings": full_reread - kept,
        "predicted_savings_fraction": round((full_reread - kept) / full_reread, SCORE_DECIMALS) if full_reread else 0.0,
        "now_turn": now_turn,
        "tokenizer": TOKENIZER_NOTE,
        "policy": "prediction-error-gated (Friston): keep surprising + load-bearing, compress the predictable",
    }}


def _gist(text: str, max_chars: int = 80) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= max_chars else flat[:max_chars - 1] + "…"


def _reason(row: dict[str, Any], tier: str) -> str:
    if row["pinned"]:
        return "pinned — always full"
    b = row["priority_breakdown"]
    if b.get("cold_start"):
        return "unseen (novelty = high surprise) — kept full"
    if tier == TIER_FULL:
        return f"high priority (utility={b['utility']}, volatility={b['volatility']})"
    if tier == TIER_SUMMARY:
        return f"mid priority — compressed (utility={b['utility']})"
    return f"predictable / re-read-as-ritual (utility={b['utility']}) — paged to handle"


def observe(prior: dict[str, Any], *, served_ids: list[str],
            cited_ids: list[str] | None = None, changed_ids: list[str] | None = None,
            now_turn: int) -> dict[str, Any]:
    """Fold one turn's outcome into a NEW prior (the learning loop).

    ``served_ids`` were placed in context this turn; ``cited_ids`` were actually
    referenced in the output (a paged-out id appearing here is a PREDICTION
    MISS — its utility jumps so the next plan keeps it full); ``changed_ids``
    had content differing from the prior serving (source prediction error).
    The input prior is never mutated.
    """
    cited = set(cited_ids or [])
    changed = set(changed_ids or [])
    out = {"schema": prior.get("schema", "usage-prior.v1"),
           "items": {k: dict(v) for k, v in prior.get("items", {}).items()}}
    for sid in served_ids:
        st = out["items"].setdefault(sid, {"served": 0, "cited": 0, "changed": 0,
                                           "last_cited_turn": None})
        st["served"] += 1
        if sid in cited:
            st["cited"] += 1
            st["last_cited_turn"] = int(now_turn)
        if sid in changed:
            st["changed"] += 1
    # A citation of an id that was NOT served (rehydrated from a handle on a
    # prediction miss) still counts — record it so the gate learns to keep it.
    for cid in cited - set(served_ids):
        st = out["items"].setdefault(cid, {"served": 0, "cited": 0, "changed": 0,
                                           "last_cited_turn": None})
        st["served"] += 1
        st["cited"] += 1
        st["last_cited_turn"] = int(now_turn)
    return out


def _selftest() -> None:
    # Three items: a hot file (cited a lot), a churning config (changes a lot,
    # rarely cited), and a frozen vendored lib (served forever, never cited).
    items = [
        {"id": "hot.py", "text": "def core(): " + "logic ; " * 60, "handle": "ctx://hot.py"},
        {"id": "config.yaml", "text": "settings: " + "k: v ; " * 60},
        {"id": "vendor.js", "text": "minified vendor blob " * 60},
        {"id": "system", "text": "You are the assistant.", "pinned": True},
    ]
    # Build a prior over ~12 past turns reflecting that history.
    prior = empty_prior()
    for turn in range(1, 13):
        prior = observe(prior, served_ids=["hot.py", "config.yaml", "vendor.js"],
                        cited_ids=["hot.py"],                       # only hot.py gets used
                        changed_ids=["config.yaml"] if turn % 2 == 0 else [],  # config churns
                        now_turn=turn)

    # Budget computed from the module's own token math: room for the pin (full)
    # + hot.py (full) + config.yaml (summary), but NOT vendor.js (forcing the
    # lowest-priority item to page out to a handle).
    tok = {it["id"]: _count_tokens(it["text"]) for it in items}
    config_summary = math.ceil(tok["config.yaml"] * TIER_KEEP_FRACTION[TIER_SUMMARY])
    budget = tok["system"] + tok["hot.py"] + config_summary
    plan = run(items=items, prior=prior, token_budget=budget, now_turn=13)["plan"]
    tier = {p["id"]: p["tier"] for p in plan["items"]}

    # The pin is always full.
    assert tier["system"] == TIER_FULL
    # The proven-load-bearing file is kept at the highest available fidelity…
    assert tier["hot.py"] == TIER_FULL
    # …while the never-cited frozen blob is the first paged to a handle.
    assert tier["vendor.js"] == TIER_HANDLE_ONLY
    assert any(p["id"] == "vendor.js" for p in plan["paged_out"])
    # The churning config outranks the frozen blob (volatility = must re-read).
    pr = {p["id"]: p["priority"] for p in plan["items"]}
    assert pr["config.yaml"] > pr["vendor.js"]

    # LOSSLESS: every paged-out item carries a rehydratable handle + gist;
    # nothing is deleted (tiers ∪ paged_out == all ids).
    all_ids = {it["id"] for it in items}
    placed = set(plan["tiers"][TIER_FULL]) | set(plan["tiers"][TIER_SUMMARY]) | set(plan["tiers"][TIER_HANDLE_ONLY])
    assert placed == all_ids
    assert all(p["handle"].startswith("ctx://") and p["gist"] for p in plan["paged_out"])

    # The Friston payoff is reported and real (we serve fewer tokens than a
    # naive keep-everything prefill would re-read).
    assert plan["predicted_reread_savings"] > 0
    assert 0 < plan["predicted_savings_fraction"] < 1
    assert plan["tokens_kept"] <= budget

    # COLD START: an unseen item is treated as surprising and kept full even
    # though it has zero usage history.
    fresh = run(items=[{"id": "system", "text": "sys", "pinned": True},
                       {"id": "brand_new.py", "text": "x " * 200}],
                prior=prior, token_budget=10_000, now_turn=13)["plan"]
    nb = next(p for p in fresh["items"] if p["id"] == "brand_new.py")
    assert nb["tier"] == TIER_FULL and nb["priority"] == COLD_START_PRIORITY
    assert "novelty" in nb["reason"]

    # THE LEARNING LOOP: a prediction MISS (vendor.js gets cited after being
    # paged out) raises its utility, and the next plan keeps it full.
    learned = observe(prior, served_ids=["hot.py", "config.yaml"],
                      cited_ids=["vendor.js"], now_turn=13)  # cited though not served = miss
    relearned = run(items=items, prior=learned, token_budget=budget, now_turn=14)["plan"]
    assert {p["id"]: p["priority"] for p in relearned["items"]}["vendor.js"] > pr["vendor.js"]

    # observe() never mutates the prior it is handed (pure).
    snapshot = json.dumps(prior, sort_keys=True)
    observe(prior, served_ids=["hot.py"], cited_ids=["hot.py"], now_turn=20)
    assert json.dumps(prior, sort_keys=True) == snapshot

    # COHORT WEIGHTS bite: a high-utility item (cited, never changed) outranks a
    # high-volatility item under the defaults, but volatility-heavy cohort weights
    # (the 'iterating' curve) flip that — the gate follows the tenant's curve.
    wp = empty_prior()
    for t in range(1, 9):
        wp = observe(wp, served_ids=["proven", "churning"], cited_ids=["proven"],
                     changed_ids=["churning"], now_turn=t)
    wi = [{"id": "proven", "text": "x " * 20}, {"id": "churning", "text": "y " * 20}]
    pr_default = {p["id"]: p["priority"] for p in
                  run(items=wi, prior=wp, token_budget=10_000, now_turn=9)["plan"]["items"]}
    pr_volatile = {p["id"]: p["priority"] for p in
                   run(items=wi, prior=wp, token_budget=10_000, now_turn=9,
                       weights={"utility": 0.1, "volatility": 0.8, "recency": 0.1})["plan"]["items"]}
    assert pr_default["proven"] > pr_default["churning"]      # default: utility wins
    assert pr_volatile["churning"] > pr_volatile["proven"]    # volatility-heavy: churn wins

    # Determinism + read-only run() + impossible-pin-budget raise + bad args.
    a = json.dumps(run(items=items, prior=prior, token_budget=budget, now_turn=13), sort_keys=True)
    b = json.dumps(run(items=items, prior=prior, token_budget=budget, now_turn=13), sort_keys=True)
    assert a == b
    raised = False
    try:
        run(items=[{"id": "system", "text": "x " * 100, "pinned": True}], prior=prior, token_budget=5)
    except ValueError:
        raised = True
    assert raised, "pins over budget must raise"
    raised = False
    try:
        run(items=[{"id": "x"}], prior=prior, token_budget=10)
    except ValueError:
        raised = True
    assert raised

    print(
        "PASS — usage_gated_compress: prediction-error gate (utility+volatility+recency, "
        "cold-start=keep), budgeted FULL/SUMMARY/HANDLE_ONLY tiers, lossless paged_out "
        "(rehydratable), prediction-miss learning loop, pure observe(), reported re-read "
        "savings, deterministic verified"
    )


if __name__ == "__main__":
    _selftest()
