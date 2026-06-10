#!/usr/bin/env python3
"""scripts.stop_local_services — stop registry-managed service groups via each service's own
stop_command when declared, else the exact recorded pid (.agent/local-services/<group>.pid).
Never a broad pkill. held/planned services have nothing to stop and are skipped."""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.local_services_lib import groups, load_registry, stop_group, write_url_map  # noqa: E402


def main() -> int:
    registry = load_registry()
    for group, members in groups(registry).items():
        if not any(m.get("status") == "active_local" for m in members):
            continue
        print(f"  [{stop_group(group, members)}] {group}")
    write_url_map(registry)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
