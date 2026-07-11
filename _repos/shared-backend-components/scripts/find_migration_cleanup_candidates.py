#!/usr/bin/env python3
"""scripts/find_migration_cleanup_candidates — surface old-context / orphaned-file cleanup CANDIDATES for the
new-GitHub-account migration, conservatively and by confidence.

It REPORTS, it does not act. Every candidate is an ARCHIVE candidate (move-never-delete law) for owner
review — nothing is deleted here. Categories, most-confident first:
  - empty            : 0-byte tracked files (safe to archive).
  - backup_temp      : .bak/.old/.orig/.tmp/~ names (safe to archive).
  - superseded_marked: header markers (superseded-by / DEPRECATED / do-not-use) — hand to archive_legacy_docs.py.
  - duplicate_content: byte-identical files (keep one, archive the rest — review which is canonical).
  - orphan_scratch   : files under scratch/notes/old dirs that nothing references (review).

Offline, deterministic, `--self-test`-able. Pairs with the reorg + the archival law.
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
import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = _resource("data") / "dev-intel" / "migration_cleanup" / "cleanup_candidates.json"

BACKUP_RE = re.compile(r"\.(bak|old|orig|tmp|swp)$|~$", re.I)
SUPERSEDED_RE = re.compile(r"superseded[- ]by|deprecated|do[- ]not[- ]use|do not use", re.I)
# dirs where an unreferenced file is likely genuinely orphaned scratch (conservative allowlist).
SCRATCH_DIRS = (".research-notes/", "scratch/", "tmp/", "old/", "notes/")
# never flag these as orphans (entry points / conventionally-unreferenced).
KEEP_BASENAMES = {"README.md", "AGENTS.md", "CLAUDE.md", "__init__.py", "index.md", "conftest.py",
                  "setup.py", "main.py", "MEMORY.md", "_manifest.jsonl", "_STATUS.md"}
SKIP_PREFIXES = ("node_modules/", ".git/", "archive/legacy/", "site/", "dist/", "_reference/")
# a superseded/deprecated marker, if present, sits in the doc HEADER — scan only the first bytes, not the body.
HEADER_SCAN_BYTES = 600


def tracked() -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True)
    return [f for f in out.stdout.splitlines() if f and not f.startswith(SKIP_PREFIXES)]


def find_candidates() -> dict:
    files = tracked()
    empty, backup, superseded, orphan_scratch = [], [], [], []
    by_hash: dict[str, list[str]] = defaultdict(list)
    for rel in files:
        p = _resource(rel)
        try:
            data = p.read_bytes()
        except Exception:  # noqa: BLE001
            continue
        if len(data) == 0:
            # __init__.py (package marker), *.log (transient), .gitkeep are LEGITIMATELY empty — not orphans.
            if not (Path(rel).name in ("__init__.py", ".gitkeep") or rel.endswith(".log")):
                empty.append(rel)
            continue
        if BACKUP_RE.search(rel):
            backup.append(rel)
        by_hash[hashlib.sha256(data).hexdigest()].append(rel)
        if rel.endswith(".md") and SUPERSEDED_RE.search(data[:HEADER_SCAN_BYTES].decode("utf-8", "ignore")):
            superseded.append(rel)
        if rel.startswith(SCRATCH_DIRS) and Path(rel).name not in KEEP_BASENAMES:
            orphan_scratch.append(rel)
    duplicates = {h: fs for h, fs in by_hash.items() if len(fs) > 1}
    return {
        "record_type": "migration_cleanup_candidates",
        "note": "ARCHIVE candidates for review — move-never-delete; nothing here is deleted automatically.",
        "empty": sorted(empty),
        "backup_temp": sorted(backup),
        "superseded_marked": sorted(superseded),
        "duplicate_content_groups": [sorted(fs) for fs in duplicates.values()],
        "orphan_scratch": sorted(orphan_scratch),
        "counts": {"empty": len(empty), "backup_temp": len(backup), "superseded_marked": len(superseded),
                   "duplicate_groups": len(duplicates), "orphan_scratch": len(orphan_scratch)},
    }


def self_test() -> int:
    checks = [
        ("backup pattern matches", bool(BACKUP_RE.search("x.bak")) and bool(BACKUP_RE.search("y.py~"))),
        ("normal file not backup", not BACKUP_RE.search("scripts/x.py")),
        ("superseded marker matches", bool(SUPERSEDED_RE.search("This doc is SUPERSEDED-BY foo"))),
        ("keep-basename protected", "README.md" in KEEP_BASENAMES),
        ("archive skipped", "archive/legacy/x.md".startswith(SKIP_PREFIXES)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - find_migration_cleanup_candidates:\n  " + "\n  ".join(failed)); return 1
    print("PASS - find_migration_cleanup_candidates: conservative candidate finder (empty / backup / "
          "superseded-marked / duplicate / orphan-scratch); REPORTS archive candidates, never deletes.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Surface migration cleanup candidates (report-only).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--write", action="store_true", help="write the full candidate report to disk")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    cand = find_candidates()
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(cand, indent=2))
    print("migration cleanup candidates (archive, don't delete):")
    for k, v in cand["counts"].items():
        print(f"  {k:18} {v}")
    if args.write:
        print(f"report -> {OUT.relative_to(REPO)}")
    print("next: superseded_marked -> scripts/archive_legacy_docs.py --apply ; others -> owner review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
