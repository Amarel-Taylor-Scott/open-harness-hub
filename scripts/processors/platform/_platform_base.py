#!/usr/bin/env python3
"""Shared helpers for the platform-action processors (one definition each).

Every ``scripts.processors.platform.*`` ``run()`` is a deterministic *planner*
for a platform write: it returns a content-addressed description of the row /
artifact / index entry that would be persisted, without touching live infra.
The hashing, id derivation, and plan-row envelope are defined here exactly once
so the nine action modules stay thin and cannot drift (docs/codex/no-magic-values.md).
"""
from __future__ import annotations

import json
from typing import Any

# Reuse the established canonical sha256-over-canonical-JSON hash rather than
# defining a second hashing convention (single source of truth lives in the db
# CDC planner). ``canonical_hash`` returns a ``sha256:<hex>`` string.
from scripts.db.component_cdc_plan import canonical_hash

# Length of the short, hash-derived id suffix. Never truncation-only of an
# external value — the suffix is taken from a full content hash, so distinct
# payloads cannot collapse onto the same id (docs/codex ID/hash discipline).
ID_SUFFIX_LEN = 16


def content_hash(value: Any) -> str:
    """Stable ``sha256:<hex>`` over a JSON-serializable value."""
    return canonical_hash(value)


def content_address(prefix: str, value: Any) -> str:
    """A deterministic ``<prefix>/<16-hex>`` content-addressed id for ``value``."""
    digest = canonical_hash(value).split(":", 1)[1]
    return f"{prefix}/{digest[:ID_SUFFIX_LEN]}"


def plan_row(
    *,
    action: str,
    target: str,
    payload: Any,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the deterministic plan envelope shared by all platform writes.

    Fields:
      * ``action``  — the manifest ``process_kind`` (what write this represents).
      * ``target``  — logical destination (table/store/index/widget name).
      * ``content_hash`` — hash of the payload (idempotency / change detection).
      * ``planned`` — always True; this is a plan, not an applied write. Honest
        signal that no live infra was contacted.
    Callers add their own content-addressed id and any action-specific keys.
    """
    row: dict[str, Any] = {
        "action": action,
        "target": target,
        "content_hash": content_hash(payload),
        "planned": True,
    }
    if extra:
        row.update(extra)
    return row


def require(value: Any, name: str) -> Any:
    """Validate a required input is present (manifests declare ``on_error: raise``)."""
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"required input {name!r} is missing or empty")
    return value


def as_rows(value: Any) -> list[Any]:
    """Normalize a single object or a list into a list (rows-shaped inputs)."""
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def json_compact(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def selftest_run(run: Any, inputs: dict[str, Any], expected_keys: tuple[str, ...]) -> int:
    """Shared --self-test body for a platform action ``run``.

    Asserts: ``run(**inputs)`` returns the declared output keys, is deterministic
    across two calls, and that each returned plan envelope is content-addressed
    and honestly flagged ``planned: True``. Prints a one-line PASS and returns 0.
    """
    out1 = run(**inputs)
    out2 = run(**inputs)
    assert isinstance(out1, dict) and out1, f"empty result: {out1!r}"
    assert set(out1) == set(expected_keys), f"keys {sorted(out1)} != {sorted(expected_keys)}"
    assert out1 == out2, "non-deterministic result across two identical calls"
    for key, value in out1.items():
        assert isinstance(value, dict), f"{key} not a plan dict"
        assert "content_hash" in value and value["content_hash"].startswith("sha256:"), (key, value)
        assert value.get("planned") is True, f"{key} not flagged planned"
    print(json_compact({"ok": True, "keys": sorted(out1)}))
    return 0

