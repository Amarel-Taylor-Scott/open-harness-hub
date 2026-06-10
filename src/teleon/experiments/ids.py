"""src/teleon/experiments/ids — canonical, deterministic id + hash helpers for the parallel-path engine.

ID And Hash Discipline (CLAUDE.md): never truncation-only. Every generated id carries a stable
sha256-derived suffix so daily runs do not collapse during dedupe/index merge. Canonical bytes are the
single source of identity: a value's hash is over its canonical JSON (sorted keys, no insignificant
whitespace), so a formatting change never creates a false new identity but a content change is detectable.

Canonical TELEON home (experiments layer); pure + deterministic (hashlib only); imports nothing internal —
never Baltor. Baltor re-exports this via a shim at src/baltor/experiments/ids.py.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

#: length of the hex suffix appended to generated ids — wide enough that daily batches don't collide,
#: short enough to stay readable. NOT truncation-of-the-only-signal: it is a hash suffix on a typed prefix.
ID_HASH_SUFFIX_LEN = 16


def canonical_bytes(value: Any) -> bytes:
    """The canonical JSON bytes of ``value`` — sorted keys, compact separators, UTF-8.

    Two values that are equal as data hash identically regardless of key order or whitespace; a content
    change changes the bytes (and thus the hash). This is the single definition of "canonical bytes" used
    for input_snapshot_hash and every content hash in the engine.
    """
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_hex(value: Any) -> str:
    """Full sha256 hex digest of ``value``'s canonical bytes (e.g. input_snapshot_hash)."""
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def canonical_id(prefix: str, *parts: str) -> str:
    """A stable id ``"{prefix}-{hash16}"`` where the hash is over the canonical bytes of ``parts``.

    The prefix is human-readable; the suffix is a content hash (never truncation-only), so the same inputs
    always yield the same id and different inputs (almost surely) yield a different one.
    """
    digest = hashlib.sha256(canonical_bytes(list(parts))).hexdigest()[:ID_HASH_SUFFIX_LEN]
    return f"{prefix}-{digest}"
