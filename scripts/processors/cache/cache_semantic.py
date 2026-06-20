#!/usr/bin/env python3
"""Backs `processor/cache-semantic` (process_kind ``cache.semantic``).

GPTCache-style **semantic response cache**: a paraphrase of a previously
answered query hits the same entry, so repeated questions stop costing model
calls. Similarity here is a *deterministic* bag-of-words cosine over
term-frequency vectors (lowercased, punctuation-split, stopwords removed) —
pure stdlib, no embedding model — so the same inputs always produce the same
hit decision. The manifest marks the process_kind non-deterministic because
production deployments may swap in a learned embedder behind the same
``run()`` contract; this implementation is strictly deterministic, which is
allowed (stricter, never looser).

Safety rules carried from the manifest description (both are tested):

  * **NEVER serve a personalized entry.** An entry written with
    ``personalized=True`` is excluded from matching even at similarity 1.0 —
    a cached "your refund is on card ending 4242" must never reach another
    user. Skips are *reported*, not silent.
  * **Tenant scoping.** An entry written with a ``tenant_id`` only matches a
    query carrying the SAME ``tenant_id`` — no cross-tenant leak.

Runtime contract (matches the manifest):

  * ``process_kind = cache.semantic`` — CPU, no model, no network.
  * **idempotent**: the same lookup twice returns the same envelope.
  * **side_effects = read**: ``run()`` only READS the store; writing is the
    explicit ``put()`` helper.
  * **on_error = raise**: invalid arguments raise ``TypeError`` /
    ``ValueError``.

Public API:
    from scripts.processors.cache.cache_semantic import put, run
    put(store, "What is the capital of France?", {"text": "Paris"})
    out = run(query="capital city of France?", store=store)
    # -> {"hit": {"hit": True, "value": {"text": "Paris"}, "similarity": ...}}

CLI / self-test:
    python3 scripts/processors/cache/cache_semantic.py
    python3 -m scripts.processors.cache.cache_semantic
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any, MutableMapping

# ── Configuration constants (single source of truth; No-Magic-Values) ────────

#: Minimum cosine similarity for a paraphrase to count as a hit. 0.55 keeps
#: genuine rephrasings ("what is the capital of France" / "capital city of
#: France?") while rejecting merely-overlapping topics; tune per corpus.
DEFAULT_SIMILARITY_THRESHOLD = 0.55

#: English function words excluded from the term vector so similarity tracks
#: content words, not glue. Frozen so callers/tests can read (never re-type) it.
STOPWORDS = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how",
    "in", "is", "it", "of", "on", "or", "that", "the", "this", "to", "was",
    "what", "when", "where", "which", "who", "why", "will", "with",
})

#: Tokenizer: runs of letters/digits, lowercased. One definition, used for
#: both stored queries and lookups, so the two sides can never drift.
_TOKEN_RE = re.compile(r"[a-z0-9]+")

#: Hash algorithm + prefix for entry keys (self-describing, future-proof).
HASH_ALGORITHM = "sha256"
ENTRY_KEY_PREFIX = f"{HASH_ALGORITHM}:"


def _vector(text: str) -> dict[str, int]:
    """Term-frequency vector of content words. The single tokenization site."""
    if not isinstance(text, str):
        raise TypeError(f"query text must be str, got {type(text).__name__}")
    vec: dict[str, int] = {}
    for tok in _TOKEN_RE.findall(text.lower()):
        if tok not in STOPWORDS:
            vec[tok] = vec.get(tok, 0) + 1
    return vec


def _cosine(a: dict[str, int], b: dict[str, int]) -> float:
    """Cosine similarity of two TF vectors; 0.0 when either is empty."""
    if not a or not b:
        return 0.0
    dot = sum(n * b.get(t, 0) for t, n in a.items())
    if dot == 0:
        return 0.0
    norm = math.sqrt(sum(n * n for n in a.values())) * math.sqrt(sum(n * n for n in b.values()))
    return dot / norm


def entry_key(query: str, tenant_id: str | None) -> str:
    """Deterministic store key for a cached query (tenant-scoped identity)."""
    payload = json.dumps({"query": query, "tenant_id": tenant_id},
                         sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return ENTRY_KEY_PREFIX + hashlib.new(HASH_ALGORITHM, payload.encode("utf-8")).hexdigest()


def put(
    store: MutableMapping[str, Any],
    query: str,
    value: Any,
    *,
    personalized: bool = False,
    tenant_id: str | None = None,
) -> str:
    """Write a response under its query. Explicit — never implicit in ``run()``.

    ``personalized=True`` marks the entry as user-specific: it stays in the
    store (it may serve the SAME user via exact tooling later) but the
    semantic matcher will never return it.
    """
    key = entry_key(query, tenant_id)
    store[key] = {
        "query": query,
        "value": value,
        "personalized": bool(personalized),
        "tenant_id": tenant_id,
        "vector": _vector(query),
    }
    return key


def run(
    *,
    query: str,
    store: MutableMapping[str, Any] | None = None,
    threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """Find the best semantically-matching cached entry for ``query`` (read-only).

    Returns ``{"hit": {...}}`` per the manifest's single ``hit`` output. A miss
    is an HONEST ``hit: False`` (never a fabricated value); personalized and
    cross-tenant candidates are excluded and counted, never served.
    """
    if not isinstance(threshold, (int, float)) or not 0.0 <= float(threshold) <= 1.0:
        raise ValueError(f"threshold must be in [0, 1], got {threshold!r}")
    qvec = _vector(query)  # raises TypeError on non-str
    envelope: dict[str, Any] = {
        "hit": False, "value": None, "matched_query": None, "similarity": 0.0,
        "cache_key": None, "skipped_personalized": 0, "skipped_tenant": 0,
    }
    if store is None:
        return {"hit": envelope}
    best_key: str | None = None
    best_sim = 0.0
    best_entry: dict[str, Any] | None = None
    for key in sorted(store):  # sorted: deterministic tie-breaks
        entry = store[key]
        sim = _cosine(qvec, entry["vector"])
        if sim < float(threshold):
            continue
        if entry.get("personalized"):
            envelope["skipped_personalized"] += 1
            continue
        if entry.get("tenant_id") is not None and entry.get("tenant_id") != tenant_id:
            envelope["skipped_tenant"] += 1
            continue
        if sim > best_sim:
            best_key, best_sim, best_entry = key, sim, entry
    if best_entry is not None:
        envelope.update(hit=True, value=best_entry["value"], matched_query=best_entry["query"],
                        similarity=round(best_sim, 6), cache_key=best_key)
    return {"hit": envelope}


def _selftest() -> None:
    store: dict[str, Any] = {}
    put(store, "What is the capital of France?", {"text": "Paris"})
    put(store, "How do I rotate Postgres credentials?", {"text": "ALTER ROLE ..."})

    # A paraphrase hits the right entry with its similarity reported.
    hit = run(query="capital city of France?", store=store)["hit"]
    assert hit["hit"] is True and hit["value"] == {"text": "Paris"}
    assert hit["matched_query"] == "What is the capital of France?"
    assert hit["similarity"] >= DEFAULT_SIMILARITY_THRESHOLD

    # An unrelated query is an honest miss.
    miss = run(query="train a segmentation model on CT scans", store=store)["hit"]
    assert miss["hit"] is False and miss["value"] is None

    # NEVER serve personalized — even an EXACT duplicate query stays excluded
    # and the skip is reported.
    put(store, "Where is my refund?", {"text": "Card ending 4242, Friday"}, personalized=True)
    p = run(query="Where is my refund?", store=store)["hit"]
    assert p["hit"] is False and p["skipped_personalized"] == 1

    # Tenant scoping: acme's entry never leaks to globex or to no-tenant.
    put(store, "What is our internal deploy region?", {"text": "us-east-1"}, tenant_id="acme")
    same = run(query="What is our internal deploy region?", store=store, tenant_id="acme")["hit"]
    other = run(query="What is our internal deploy region?", store=store, tenant_id="globex")["hit"]
    none = run(query="What is our internal deploy region?", store=store)["hit"]
    assert same["hit"] is True and same["value"] == {"text": "us-east-1"}
    assert other["hit"] is False and other["skipped_tenant"] == 1
    assert none["hit"] is False and none["skipped_tenant"] == 1

    # Idempotent + deterministic: identical lookups are byte-identical.
    a = json.dumps(run(query="capital city of France?", store=store), sort_keys=True)
    b = json.dumps(run(query="capital city of France?", store=store), sort_keys=True)
    assert a == b

    # run() never writes (side_effects=read).
    before = dict(store)
    run(query="anything at all", store=store)
    assert store == before

    # on_error=raise: bad threshold and non-str query raise.
    raised = False
    try:
        run(query="x", store=store, threshold=1.5)
    except ValueError:
        raised = True
    assert raised, "out-of-range threshold must raise ValueError"
    raised = False
    try:
        run(query=123, store=store)  # type: ignore[arg-type]
    except TypeError:
        raised = True
    assert raised, "non-str query must raise TypeError"

    print(
        "PASS — cache_semantic: paraphrase hits via deterministic TF-cosine, "
        "honest misses, personalized entries never served (reported skips), "
        "tenant scoping enforced, read-only run(), byte-identical repeats, "
        "on_error=raise verified"
    )


if __name__ == "__main__":
    _selftest()
