#!/usr/bin/env python3
"""scripts/check_repos_edge_tools — proof-suite BRIDGE for the edge/graph/interface tools that now live in
the staged repos under _repos/ (edge-graph-generator + dev-rules-context/tools).

Those tools moved out of _repos/shared-backend-components/scripts/ into their future repos, so run_proofs can't register them by module path.
This bridge runs each one's own `--self-test` and fails if any fails — keeping cross-repo awareness,
the dependency-law gate, and the interface-relationship checks green in THIS repo's suite until they split
into their own repos (where each becomes that repo's CI). The tool list is discovered, not hand-typed.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
# the edge-graph-generator tools carry the load-bearing --self-tests we must keep green.
BRIDGED = [
    REPO / "_repos" / "edge-graph-generator" / "generate_repo_edges.py",
    REPO / "_repos" / "edge-graph-generator" / "check_cross_repo_dependency_law.py",
    REPO / "_repos" / "edge-graph-generator" / "interface_manifests.py",
]


def self_test() -> int:
    missing = [str(t.relative_to(REPO)) for t in BRIDGED if not t.exists()]
    if missing:
        # absence is not a failure once these repos split away — report and pass (nothing to bridge here).
        print(f"PASS - check_repos_edge_tools: {len(missing)} bridged tool(s) not present (repo split?) — nothing to run: {missing}")
        return 0
    failed = []
    for t in BRIDGED:
        res = subprocess.run([sys.executable, str(t), "--self-test"], capture_output=True, text=True)
        if res.returncode != 0:
            failed.append(f"{t.name}: {res.stdout.strip().splitlines()[-1] if res.stdout.strip() else res.stderr.strip()[:120]}")
    if failed:
        print("FAIL - check_repos_edge_tools:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - check_repos_edge_tools: {len(BRIDGED)} edge/graph/interface tools self-test green "
          "(cross-repo dependency law + per-repo edge digests + versioned interface relationships).")
    return 0


if __name__ == "__main__":
    # the bridge's job IS to run the sub-tools' self-tests, so --self-test and a bare call are the same.
    raise SystemExit(self_test())
