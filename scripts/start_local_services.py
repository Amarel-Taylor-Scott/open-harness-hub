#!/usr/bin/env python3
"""scripts.start_local_services — start every active_local service group from the registry
(architecture/local_service_registry.json). Idempotent: a group that already answers health is left
alone. held/planned services are reported, never started, never faked. Writes the honest URL map."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

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
