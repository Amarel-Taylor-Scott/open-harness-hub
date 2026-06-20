"""src/baltor/workers/execution_dispatch.py — RE-EXPORT SHIM (lossless extraction → Teleon, 2026-06-08). Canonical home: src.teleon.workers.*. Baltor → Teleon allowed; Teleon never imports Baltor."""
from __future__ import annotations

from src.teleon.workers.execution_dispatch import (  # noqa: F401
    SHARD_BUCKET, _executor_for_backend, dispatch_capability, dispatch_owned_shards)
__all__ = ["dispatch_capability", "dispatch_owned_shards", "SHARD_BUCKET"]
