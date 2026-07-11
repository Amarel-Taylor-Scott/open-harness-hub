#!/usr/bin/env python3
"""Backs `processor/cache-exact` (process_kind ``cache.exact_hash``).

Exact-hash response cache: a request is keyed by the canonical JSON of its
identity — ``(task, components, inputs)`` — hashed with SHA-256, and an
identical run returns the stored response instantly at zero model cost.
"Identical" means *semantically identical JSON*, not byte-identical text:
key order and whitespace never matter, value changes always do (the ID/hash
discipline in `CLAUDE.md` — formatting changes must not create false
versions; content changes must always be detectable).

Runtime contract (matches the manifest + the runtime-routing doc
``_repos/shared-backend-components/context/architecture/component-execution-and-runtime-routing.md``):

  * ``process_kind = cache.exact_hash`` — CPU, no model, no network.
  * **deterministic**: same key object → same cache key string, byte-identical
    result envelope. No clocks (time is *injected* for TTL checks), no RNG,
    no environment reads.
  * **idempotent**: looking up the same key twice returns the same envelope.
  * **side_effects = read**: ``run()`` only READS the store it is handed.
    Writing is a separate explicit ``put()`` (never implicit on lookup).
  * **on_error = raise**: invalid arguments raise ``TypeError`` /
    ``ValueError``; we never silently swallow.

The store is INJECTED (any ``MutableMapping`` — a plain dict locally, a
Redis/SQLite adapter in cloud) so this module stays pure stdlib and the same
code runs everywhere; the processor never owns a global cache.

Public API:
    from scripts.processors.cache.cache_exact import cache_key, put, run
    key = {"task": "summarize", "components": ["processor/x@1"], "inputs": {...}}
    put(store, key, {"text": "..."}, now=t0)
    out = run(key=key, store=store, now=t1)
    # -> {"hit": {"hit": True, "value": {...}, "cache_key": "sha256:...",
    #             "age_seconds": t1 - t0, "expired": False}}

CLI / self-test:
    python3 _repos/shared-backend-components/scripts/processors/cache/cache_exact.py
    python3 -m scripts.processors.cache.cache_exact
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, MutableMapping

# ── Configuration constants (single source of truth; No-Magic-Values) ────────

#: Hash algorithm + prefix for cache keys. The prefix makes keys self-describing
#: so a store can hold keys minted by future algorithms side by side.
HASH_ALGORITHM = "sha256"
CACHE_KEY_PREFIX = f"{HASH_ALGORITHM}:"

#: Identity fields a key object MAY carry. Unknown fields are rejected (raise)
#: rather than silently ignored — a typo'd field must never produce a key that
#: aliases a different request.
KEY_FIELDS = frozenset({"task", "components", "inputs"})

#: TTL sentinel: entries default to "never expires" (the exact cache is for
#: deterministic / frozen runs; freshness-bearing facts belong behind CDC,
#: not in a response cache).
NO_TTL: float | None = None


def _canonical(obj: Any) -> str:
    """Canonical JSON: sorted keys, no insignificant whitespace, UTF-8 kept raw.

    This is the single place key text is produced — formatting can never make
    two identical requests hash apart.
    """
    try:
        return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"cache key must be JSON-serializable: {exc}") from exc


def cache_key(key: dict[str, Any]) -> str:
    """Mint the deterministic cache key string for a request-identity object."""
    if not isinstance(key, dict):
        raise TypeError(f"key must be a dict, got {type(key).__name__}")
    unknown = set(key) - KEY_FIELDS
    if unknown:
        raise ValueError(f"unknown key fields {sorted(unknown)}; allowed: {sorted(KEY_FIELDS)}")
    digest = hashlib.new(HASH_ALGORITHM, _canonical(key).encode("utf-8")).hexdigest()
    return f"{CACHE_KEY_PREFIX}{digest}"


def put(
    store: MutableMapping[str, Any],
    key: dict[str, Any],
    value: Any,
    *,
    now: float,
    ttl_seconds: float | None = NO_TTL,
) -> str:
    """Write ``value`` under ``key``'s hash. Explicit, never implicit in ``run()``.

    ``now`` is injected (no wall clock) so writes are replayable; ``ttl_seconds``
    of ``NO_TTL`` means the entry never expires.
    """
    ck = cache_key(key)
    store[ck] = {"value": value, "stored_at": float(now), "ttl_seconds": ttl_seconds}
    return ck


def run(
    *,
    key: dict[str, Any],
    store: MutableMapping[str, Any] | None = None,
    now: float = 0.0,
) -> dict[str, Any]:
    """Look up the exact-hash entry for ``key`` in the injected ``store`` (read-only).

    Returns ``{"hit": {...}}`` per the manifest's single ``hit`` output: a miss
    is an HONEST ``hit: False`` envelope (never a fabricated value), and an
    expired entry reports ``expired: True`` and does not serve its value.
    """
    ck = cache_key(key)
    envelope: dict[str, Any] = {
        "hit": False,
        "value": None,
        "cache_key": ck,
        "age_seconds": None,
        "expired": False,
    }
    if store is None:
        return {"hit": envelope}
    entry = store.get(ck)
    if entry is None:
        return {"hit": envelope}
    age = float(now) - float(entry["stored_at"])
    ttl = entry.get("ttl_seconds", NO_TTL)
    if ttl is not None and age > ttl:
        envelope.update(age_seconds=age, expired=True)
        return {"hit": envelope}
    envelope.update(hit=True, value=entry["value"], age_seconds=age)
    return {"hit": envelope}


def _selftest() -> None:
    store: dict[str, Any] = {}
    key = {"task": "summarize", "components": ["processor/structural-compress@0.1.0"],
           "inputs": {"doc": "alpha", "max_tokens": 100}}

    # Miss before any write; the miss is honest (no value fabricated).
    miss = run(key=key, store=store)["hit"]
    assert miss["hit"] is False and miss["value"] is None

    # Put then hit; value round-trips; age uses injected time only.
    ck = put(store, key, {"text": "compressed alpha"}, now=1_000.0)
    hit = run(key=key, store=store, now=1_007.5)["hit"]
    assert hit["hit"] is True and hit["value"] == {"text": "compressed alpha"}
    assert hit["cache_key"] == ck and hit["age_seconds"] == 7.5

    # Formatting never matters: key order / dict order changes hash identically.
    reordered = {"inputs": {"max_tokens": 100, "doc": "alpha"},
                 "components": ["processor/structural-compress@0.1.0"], "task": "summarize"}
    assert cache_key(reordered) == ck.replace(CACHE_KEY_PREFIX, CACHE_KEY_PREFIX)
    assert run(key=reordered, store=store, now=1_007.5)["hit"]["hit"] is True

    # Content always matters: any value change is a different key (no aliasing).
    changed = {"task": "summarize", "components": ["processor/structural-compress@0.1.0"],
               "inputs": {"doc": "alpha", "max_tokens": 101}}
    assert cache_key(changed) != ck
    assert run(key=changed, store=store)["hit"]["hit"] is False

    # Determinism: same key → byte-identical envelope JSON across calls.
    a = json.dumps(run(key=key, store=store, now=2_000.0), sort_keys=True)
    b = json.dumps(run(key=key, store=store, now=2_000.0), sort_keys=True)
    assert a == b

    # TTL: an expired entry reports expired and does NOT serve its value.
    ttl_key = {"task": "volatile", "components": [], "inputs": {}}
    put(store, ttl_key, "stale", now=0.0, ttl_seconds=10.0)
    fresh = run(key=ttl_key, store=store, now=5.0)["hit"]
    stale = run(key=ttl_key, store=store, now=11.0)["hit"]
    assert fresh["hit"] is True and stale["hit"] is False and stale["expired"] is True

    # run() never writes: a miss leaves the store untouched (side_effects=read).
    before = dict(store)
    run(key={"task": "absent", "components": [], "inputs": {}}, store=store)
    assert store == before

    # on_error=raise: unknown fields and unserializable keys raise, never alias.
    raised = False
    try:
        cache_key({"task": "x", "extra": 1})
    except ValueError:
        raised = True
    assert raised, "unknown key field must raise ValueError"
    raised = False
    try:
        cache_key({"task": object()})  # type: ignore[dict-item]
    except TypeError:
        raised = True
    assert raised, "unserializable key must raise TypeError"

    print(
        "PASS — cache_exact: canonical-JSON SHA-256 keying (format-insensitive, "
        "content-sensitive), honest miss, injected-time TTL, read-only run(), "
        "deterministic envelopes, on_error=raise verified"
    )


if __name__ == "__main__":
    _selftest()
