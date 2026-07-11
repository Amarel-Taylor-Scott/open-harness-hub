#!/usr/bin/env python3
"""Backs ``processor/cache-write``. Canonical wiring: the manifest
``_repos/shared-backend-components/catalog/processors/platform/cache-write.yaml`` (process_kind
``cache.write_response``). This planner builds a deterministic cache entry keyed
by the content hash of ``key`` with an optional TTL; it does not write to a live
cache (the manifest is the contract).
"""
from __future__ import annotations

from typing import Any

from scripts.processors.platform._platform_base import (
    content_address,
    content_hash,
    plan_row,
    selftest_run,
)

PROCESS_KIND = "cache.write_response"


def run(key: Any, result: Any, ttl: Any = None) -> dict[str, Any]:
    """Plan a cache write of ``result`` under ``key`` (optional ``ttl``). Returns ``{cached}``."""
    cache_key = content_address("cache", key)
    ttl_seconds = None
    if isinstance(ttl, dict):
        ttl_seconds = ttl.get("seconds")
    elif isinstance(ttl, (int, float)):
        ttl_seconds = ttl
    cached = plan_row(
        action=PROCESS_KIND,
        target=cache_key,
        payload=result,
        extra={
            "cache_key": cache_key,
            "key_hash": content_hash(key),
            "result_hash": content_hash(result),
            "ttl_seconds": ttl_seconds,
        },
    )
    return {"cached": cached}


def _self_test() -> int:
    result = run(key={"q": "hello"}, result={"answer": 42}, ttl={"seconds": 60})
    assert result["cached"]["ttl_seconds"] == 60, result
    assert result["cached"]["cache_key"].startswith("cache/"), result
    # Same key -> same cache_key regardless of result.
    a = run(key={"q": "x"}, result={"a": 1})
    b = run(key={"q": "x"}, result={"a": 2})
    assert a["cached"]["cache_key"] == b["cached"]["cache_key"], (a, b)
    return selftest_run(run, {"key": {"q": "x"}, "result": {"a": 1}}, ("cached",))


if __name__ == "__main__":
    raise SystemExit(_self_test())
