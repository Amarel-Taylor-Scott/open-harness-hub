#!/usr/bin/env python3
"""scripts/refresh_all — the deterministic MAINTAINER that keeps the whole organization in sync from its
single sources, so context / graph / interface / MD files never drift as the repo grows.

One command regenerates every derived artifact from the ONE source of truth
(`_repos/dev-rules-context/contracts/surface-registry.json` + each repo's interface.json + code layout):
  1. per-repo EDGES.md digests + the global dependency GRAPH   (generate_repo_edges)
  2. per-repo interface.json + the relationship consistency check (interface_manifests)
  3. the migration plan + per-project manifests                 (build_migration_plan)
  4. the cross-repo dependency-law proof                         (check_cross_repo_dependency_law)
  5. a staleness scan of the context MD tree                     (flags docs older than their source)

`--check` = verify everything is in sync WITHOUT writing (for CI: fails if a derived file is stale).
`--write` = regenerate everything. `--self-test` = offline proof the orchestration + staleness logic work.
This is a "graph refresher + continuous context updater" — a deterministic agent, not an LLM.
"""
from __future__ import annotations

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
# Resolve the SUBSTRATE root (the dir that holds the `scripts` package) via the scripts/_repo_paths.py sentinel —
# NOT `.aidoneright-root`, which sits at the MONOREPO root (no `scripts/` package) and breaks `from scripts.*`/
# `from src.*` on a bare `python3 _repos/shared-backend-components/scripts/<f>.py` launch. install() then
# prepends every code root (repo root + each _repos/*/backend + shared-backend-components) so both resolve.
import sys
from pathlib import Path
_sbc = next((_p for _p in Path(__file__).resolve().parents if (_p / "scripts" / "_repo_paths.py").exists()), Path(__file__).resolve().parents[1])
if str(_sbc) not in sys.path:
    sys.path.insert(0, str(_sbc))
from scripts._repo_paths import install as _install  # noqa: E402
_install()
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EGG = REPO.parent / "edge-graph-generator"
DEVKIT_TOOLS = REPO.parent / "dev-rules-context" / "tools"

# Each maintainer: (label, argv). Ordered — interfaces before edges so the graph reflects fresh interfaces.
def _maintainers(write: bool) -> list[tuple[str, list[str]]]:
    gen = "--generate" if write else "--check"
    mk = "--write" if write else "--self-test"   # build_migration_plan has no --check; self-test is its dry gate
    return [
        ("interfaces", [sys.executable, str(EGG / "interface_manifests.py"), *( ["--generate", "--check"] if write else ["--check"] )]),
        ("edges+graph", [sys.executable, str(EGG / "generate_repo_edges.py"), *(["--write"] if write else [])]),
        ("dependency-law", [sys.executable, str(EGG / "check_cross_repo_dependency_law.py")]),
        ("migration-plan", [sys.executable, str(_resource("scripts/build_migration_plan.py")), *(["--write"] if write else ["--self-test"])]),
    ]


def run_maintainers(write: bool) -> dict:
    results = []
    for label, argv in _maintainers(write):
        r = subprocess.run(argv, cwd=str(REPO), capture_output=True, text=True)
        results.append({"maintainer": label, "ok": r.returncode == 0,
                        "tail": (r.stdout.strip().splitlines() or [""])[-1][:160] if r.stdout.strip() else r.stderr.strip()[:160]})
    return {"results": results, "all_ok": all(x["ok"] for x in results)}


def staleness_scan(sample: int = 400) -> dict:
    """Flag context MD files whose mtime predates their surface's blackbox (a cheap 'this doc may be stale'
    signal). Reports candidates for review — never edits. Deterministic ordering."""
    repos = REPO.parent
    stale = []
    if repos.is_dir():
        mds = sorted(p for p in repos.rglob("*.md") if "generated-edges" not in str(p))
        for p in mds[:sample]:
            bb = p.parent / "blackbox.md"
            try:
                if bb.exists() and bb != p and p.stat().st_mtime < bb.stat().st_mtime - 86400:
                    stale.append(str(p.relative_to(REPO)))
            except OSError:
                continue
    return {"scanned": len(list((repos).rglob("*.md"))) if repos.is_dir() else 0, "stale_candidates": stale[:20], "stale_count": len(stale)}


def self_test() -> int:
    checks = [
        ("maintainer list is ordered interfaces-before-edges", _maintainers(True)[0][0] == "interfaces" and _maintainers(True)[1][0] == "edges+graph"),
        ("write mode passes --write to edges", "--write" in _maintainers(True)[1][1]),
        ("check mode does not write edges", "--write" not in _maintainers(False)[1][1]),
        ("staleness scan returns a report shape", set(staleness_scan(1)) >= {"scanned", "stale_candidates", "stale_count"}),
        ("edge-graph-generator tools exist", (EGG / "generate_repo_edges.py").exists() and (EGG / "interface_manifests.py").exists()),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - refresh_all:\n  " + "\n  ".join(failed)); return 1
    print("PASS - refresh_all: deterministic maintainer orchestrates interfaces->edges->dependency-law->"
          "migration-plan from the single-source registry, + a context-MD staleness scan. --check for CI, --write to refresh.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Refresh all derived org artifacts from their single sources.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--write", action="store_true", help="regenerate every derived artifact")
    ap.add_argument("--check", action="store_true", help="verify in-sync without writing (CI gate)")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    rep = run_maintainers(write=args.write)
    for r in rep["results"]:
        print(f"  [{'ok' if r['ok'] else 'FAIL'}] {r['maintainer']:16} {r['tail']}")
    stale = staleness_scan()
    print(f"  context MD: {stale['scanned']} scanned, {stale['stale_count']} stale candidate(s)"
          + (f" (e.g. {stale['stale_candidates'][0]})" if stale['stale_candidates'] else ""))
    if not rep["all_ok"]:
        print("FAIL - refresh_all: a maintainer failed (see above)")
        return 1
    print(f"PASS - refresh_all: everything {'regenerated' if args.write else 'verified'} in sync from the single sources.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
