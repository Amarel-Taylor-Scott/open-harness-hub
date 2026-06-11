#!/usr/bin/env python3
"""Backs ``processor/persist-object-store``. Canonical wiring: the manifest
``catalog/processors/platform/persist-object-store.yaml`` (process_kind
``platform.object_store``). This planner derives a content-addressed object URI
for an artifact; it does not upload anything (the manifest is the contract).
"""
from __future__ import annotations

from typing import Any

from scripts.processors.platform._platform_base import (
    content_hash,
    plan_row,
    require,
    selftest_run,
)

PROCESS_KIND = "platform.object_store"

# Logical content-addressed scheme; the real bucket/endpoint is supplied at
# apply time, never hard-coded into a planner.
OBJECT_URI_SCHEME = "cas"


def run(artifact: Any) -> dict[str, Any]:
    """Plan storage of ``artifact`` at a content-addressed URI. Returns ``{uri}``."""
    require(artifact, "artifact")
    digest = content_hash(artifact).split(":", 1)[1]
    uri = f"{OBJECT_URI_SCHEME}://{digest}"
    plan = plan_row(
        action=PROCESS_KIND,
        target=uri,
        payload=artifact,
        extra={"uri": uri, "scheme": OBJECT_URI_SCHEME},
    )
    return {"uri": plan}


def _self_test() -> int:
    a = run(artifact={"bundle": "report-bytes"})
    b = run(artifact={"bundle": "report-bytes"})
    assert a == b and a["uri"]["uri"].startswith(f"{OBJECT_URI_SCHEME}://"), a
    # Different artifacts get different URIs (content-addressed).
    c = run(artifact={"bundle": "other"})
    assert c["uri"]["uri"] != a["uri"]["uri"], (a, c)
    return selftest_run(run, {"artifact": {"bundle": "x"}}, ("uri",))


if __name__ == "__main__":
    raise SystemExit(_self_test())
