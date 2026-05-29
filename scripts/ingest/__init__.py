"""Open Harness Hub — corpus-ingestion tools.

Feed official / government sources into the governed corpus, and watch them for updates
(change-data-capture). These build ON TOP of `scripts.foundry` (no reinvention): the
fetchers + CDC live in `scripts.foundry.scrapers`, the row families in
`scripts.foundry.stage_load`, persistence in `scripts.foundry.store`, the job broker in
`scripts.foundry.queues`. This package adds the runnable, containerizable surface:

- `scripts.ingest.feed`      — fetch a registered source → parse → emit corpus rows → store
- `scripts.ingest.freshness` — poll registered sites, detect change (CDC), enqueue re-ingest
- `scripts.ingest.health`    — quick reachability + parseability check per source
- `scripts.ingest.run`       — the freshness→feed loop (wired by the workflow's verify phase)

Local→cloud is env-only (sqlite/sqlite-queue local → postgres/redis cloud); see `.env.example`.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.foundry.scrapers import DEFAULT_REGISTRY

__all__ = ["load_registry", "REGISTRY_PATH"]

REGISTRY_PATH = DEFAULT_REGISTRY  # data/source-registry.jsonl (single source of truth)


def load_registry(path: str | Path | None = None) -> list[dict]:
    """Read the gap-keyword → authoritative-source registry. THE single way to load sources
    (mirrors scrapers._refresh / worker._default_foundry); '#' lines are comments."""
    p = Path(path or REGISTRY_PATH)
    if not p.exists():
        return []
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.startswith("#")]
