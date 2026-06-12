#!/usr/bin/env python3
"""Backs `processor/memory-recall` (process_kind ``memory.recall``).

Recall the memories relevant to the current turn: rank an injected memory
store by a weighted blend of **semantic** match (deterministic bag-of-words
cosine between the query and the memory text + tags) and **recency**
(exponential half-life decay over an *injected* clock — never the wall
clock). The manifest marks the process_kind non-deterministic because
production deployments may swap in a learned embedder behind the same
``run()`` contract; this implementation is strictly deterministic, which is
allowed (stricter, never looser).

Governance rules carried from the memory package (tested):

  * **Tenant scoping** — a ``scope: tenant_private`` memory belonging to
    another tenant is NEVER recalled, and every such exclusion is counted in
    ``filtered_by_tenant`` (reported, not silent).
  * **Honest emptiness** — an empty or fully-filtered store returns an empty
    result set, never fabricated memories.

Runtime contract (matches the manifest):

  * ``process_kind = memory.recall`` — CPU, no model, no network.
  * **idempotent** / deterministic here: same query + store + now →
    byte-identical results.
  * **side_effects = read**: ``run()`` never mutates the store.
  * **on_error = raise**: invalid arguments raise ``TypeError``/``ValueError``.

Public API:
    from scripts.processors.memory.memory_recall import run
    out = run(query="where do we deploy?", store=memories, now=t)
    # -> {"memories": {"results": [{"id", "text", "score", ...}], ...}}

CLI / self-test:
    python3 scripts/processors/memory/memory_recall.py
    python3 -m scripts.processors.memory.memory_recall
"""
from __future__ import annotations

import json
import math
import re
from typing import Any

# ── Configuration constants (single source of truth; No-Magic-Values) ────────

#: Blend weights: semantic match dominates (a relevant old memory beats an
#: irrelevant new one) but recency breaks ties between equal matches. They
#: sum to 1.0 so combined scores stay in [0, 1].
SEMANTIC_WEIGHT = 0.8
RECENCY_WEIGHT = 0.2

#: Recency half-life: a memory's recency score halves every 7 days (in
#: seconds). Conversational/project memories age on this order; tune per
#: deployment.
RECENCY_HALF_LIFE_SECONDS = 7 * 24 * 3600.0

#: Default number of memories returned.
DEFAULT_TOP_K = 5

#: Scope value marking a memory as private to its tenant.
TENANT_PRIVATE_SCOPE = "tenant_private"

#: English function words excluded from term vectors (shared rationale with
#: the cache lane: similarity should track content words, not glue).
STOPWORDS = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how",
    "in", "is", "it", "of", "on", "or", "that", "the", "this", "to", "was",
    "what", "when", "where", "which", "who", "why", "will", "with", "do", "we",
})

#: Tokenizer: runs of letters/digits, lowercased. The single tokenization site.
_TOKEN_RE = re.compile(r"[a-z0-9]+")

#: Score rounding (decimal places) so envelopes are stable across platforms.
SCORE_DECIMALS = 6


def _vector(text: str) -> dict[str, int]:
    vec: dict[str, int] = {}
    for tok in _TOKEN_RE.findall(text.lower()):
        if tok not in STOPWORDS:
            vec[tok] = vec.get(tok, 0) + 1
    return vec


def _cosine(a: dict[str, int], b: dict[str, int]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(n * b.get(t, 0) for t, n in a.items())
    if dot == 0:
        return 0.0
    norm = math.sqrt(sum(n * n for n in a.values())) * math.sqrt(sum(n * n for n in b.values()))
    return dot / norm


def _recency(created_at: float, now: float) -> float:
    """Exponential half-life decay; future timestamps clamp to 1.0 (no bonus)."""
    age = max(0.0, float(now) - float(created_at))
    return math.pow(2.0, -age / RECENCY_HALF_LIFE_SECONDS)


def run(
    *,
    query: str,
    store: list[dict[str, Any]] | dict[str, dict[str, Any]],
    now: float,
    top_k: int = DEFAULT_TOP_K,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """Rank the injected store against ``query`` (read-only) and return the top hits.

    Returns ``{"memories": {...}}`` per the manifest's single output:
    ``results`` (ranked), ``considered`` (entries scored), and
    ``filtered_by_tenant`` (private entries of other tenants — excluded and
    counted, never served).
    """
    if not isinstance(query, str):
        raise TypeError(f"query must be str, got {type(query).__name__}")
    if not isinstance(top_k, int) or top_k < 1:
        raise ValueError(f"top_k must be a positive int, got {top_k!r}")
    entries = list(store.values()) if isinstance(store, dict) else list(store)
    qvec = _vector(query)

    filtered_by_tenant = 0
    scored: list[dict[str, Any]] = []
    for mem in entries:
        if not isinstance(mem, dict) or "id" not in mem or "text" not in mem:
            raise ValueError("every memory needs at least id and text")
        if (mem.get("scope") == TENANT_PRIVATE_SCOPE
                and mem.get("tenant_id") is not None
                and mem.get("tenant_id") != tenant_id):
            filtered_by_tenant += 1
            continue
        tags = mem.get("tags") or []
        sem = _cosine(qvec, _vector(mem["text"] + " " + " ".join(str(t) for t in tags)))
        rec = _recency(mem.get("created_at", 0.0), now)
        scored.append({
            "id": mem["id"],
            "text": mem["text"],
            "score": round(SEMANTIC_WEIGHT * sem + RECENCY_WEIGHT * rec, SCORE_DECIMALS),
            "semantic_score": round(sem, SCORE_DECIMALS),
            "recency_score": round(rec, SCORE_DECIMALS),
            "created_at": mem.get("created_at", 0.0),
        })
    # Deterministic order: score desc, then id asc as the stable tie-break.
    scored.sort(key=lambda r: (-r["score"], str(r["id"])))
    return {"memories": {
        "results": scored[:top_k],
        "considered": len(scored),
        "filtered_by_tenant": filtered_by_tenant,
    }}


def _selftest() -> None:
    day = 24 * 3600.0
    now = 100 * day
    store = [
        {"id": "m1", "text": "We deploy Teleon and Baltor to the Fly.io iad region",
         "created_at": now - 30 * day, "tags": ["hosting"]},
        {"id": "m2", "text": "The owner prefers dark roast coffee", "created_at": now - 1 * day},
        {"id": "m3", "text": "Deploy region decisions live in the hosting matrix doc",
         "created_at": now - 2 * day, "tags": ["hosting", "deploy"]},
        {"id": "m4", "text": "Acme's private billing account id is 9981",
         "created_at": now - 1 * day, "scope": "tenant_private", "tenant_id": "acme"},
    ]

    # Semantic dominates: a 30-day-old on-topic memory outranks a fresh
    # off-topic one for a deploy query.
    out = run(query="where do we deploy the services?", store=store, now=now)["memories"]
    ids = [r["id"] for r in out["results"]]
    assert ids.index("m1") < ids.index("m2") or "m2" not in ids
    assert out["results"][0]["id"] in {"m1", "m3"}

    # Tenant privacy: m4 is excluded for no-tenant and for the wrong tenant —
    # excluded AND counted; visible to its own tenant.
    assert "m4" not in ids and out["filtered_by_tenant"] == 1
    wrong = run(query="billing account id", store=store, now=now, tenant_id="globex")["memories"]
    assert all(r["id"] != "m4" for r in wrong["results"]) and wrong["filtered_by_tenant"] == 1
    own = run(query="billing account id", store=store, now=now, tenant_id="acme")["memories"]
    assert any(r["id"] == "m4" for r in own["results"]) and own["filtered_by_tenant"] == 0

    # Recency breaks ties between semantically equal memories.
    twins = [
        {"id": "old", "text": "standup is at nine", "created_at": now - 50 * day},
        {"id": "new", "text": "standup is at nine", "created_at": now - 1 * day},
    ]
    tie = run(query="when is standup", store=twins, now=now)["memories"]["results"]
    assert tie[0]["id"] == "new" and tie[0]["score"] > tie[1]["score"]

    # top_k respected; dict-shaped stores accepted.
    k1 = run(query="deploy", store={m["id"]: m for m in store}, now=now, top_k=1)["memories"]
    assert len(k1["results"]) == 1

    # Honest emptiness + read-only store.
    empty = run(query="anything", store=[], now=now)["memories"]
    assert empty["results"] == [] and empty["considered"] == 0
    snapshot = json.dumps(store, sort_keys=True)
    run(query="deploy", store=store, now=now)
    assert json.dumps(store, sort_keys=True) == snapshot

    # Deterministic byte-identical repeat.
    a = json.dumps(run(query="deploy", store=store, now=now), sort_keys=True)
    b = json.dumps(run(query="deploy", store=store, now=now), sort_keys=True)
    assert a == b

    # on_error=raise.
    raised = False
    try:
        run(query=42, store=store, now=now)  # type: ignore[arg-type]
    except TypeError:
        raised = True
    assert raised, "non-str query must raise TypeError"
    raised = False
    try:
        run(query="x", store=store, now=now, top_k=0)
    except ValueError:
        raised = True
    assert raised, "non-positive top_k must raise ValueError"

    print(
        "PASS — memory_recall: semantic+recency blend (semantic-dominant, "
        "recency tie-break, 7-day half-life on injected time), tenant_private "
        "never leaks (counted skips), honest empty results, top_k, read-only, "
        "deterministic verified"
    )


if __name__ == "__main__":
    _selftest()
