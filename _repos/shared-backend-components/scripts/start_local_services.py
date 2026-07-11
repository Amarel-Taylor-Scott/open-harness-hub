#!/usr/bin/env python3
"""scripts.start_local_services — start every active_local service group from the registry
(_repos/shared-backend-components/architecture/local_service_registry.json). Idempotent: a group that already answers health is left
alone. held/planned services are reported, never started, never faked. Writes the honest URL map."""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
# Resolve the SUBSTRATE root via the scripts/_repo_paths.py sentinel — NOT `.aidoneright-root` (MONOREPO root,
# no `scripts/` package), which breaks `from scripts.*` on a bare `python3 _repos/.../scripts/<f>.py` launch.
_sbc = next((_p for _p in Path(__file__).resolve().parents if (_p / "scripts" / "_repo_paths.py").exists()), Path(__file__).resolve().parents[1])
if str(_sbc) not in sys.path:
    sys.path.insert(0, str(_sbc))
from scripts._repo_paths import install as _install  # noqa: E402
_install()  # prepend all code roots so `from scripts.*` (and `from src.*`) resolve on a bare launch

from scripts.local_services_lib import groups, group_health, load_registry, start_group, write_url_map  # noqa: E402


def main() -> int:
    registry = load_registry()
    failed: list[str] = []
    for group, members in groups(registry).items():
        statuses = {m["status"] for m in members}
        if "active_local" not in statuses:
            print(f"  [held] {group}: {members[0].get('held_reason', 'not active')[:100]}")
            continue
        result = start_group(group, members)
        health = group_health(members)
        print(f"  [{result}] {group}: " + ", ".join(f"{k}={'up' if v else 'DOWN'}" for k, v in health.items()))
        if result == "failed" or (result != "no_start_command" and not any(health.values())):
            failed.append(group)
    path = write_url_map(registry)
    print(f"url map: {path}")
    if failed:
        print(f"FAILED groups: {failed}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
