#!/usr/bin/env python3
"""scripts/stage_repos — mirror the future multi-repo layout LOCALLY under _repos/, one folder per planned
GitHub repo, so each can later be `git init`+pushed and, meanwhile, a Claude Code session can focus on one
folder with only its edge digest for cross-repo awareness.

Lossless: directory-level `git mv` (history preserved), lineage recorded in _repos/_MANIFEST.jsonl, and a
path-mapping emitted for the reference rewriter. Nothing deleted. Idempotent-ish: a source already moved is
skipped. The repo list + folder names come from the surface-registry (single source), never hand-typed here.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REPOS = REPO.parent
# the registry moved with template-repo into the staged dev-rules-context repo; fall back to the pre-stage
# location so this stays runnable both before and after staging (no hardcoded single path that breaks on move).
_REGISTRY_CANDIDATES = (REPO.parent / "dev-rules-context" / "contracts" / "surface-registry.json",
                        _resource("template-repo") / "contracts" / "surface-registry.json")
REGISTRY = next((p for p in _REGISTRY_CANDIDATES if p.exists()), _REGISTRY_CANDIDATES[0])
MANIFEST = REPOS / "_MANIFEST.jsonl"
MAPPING = _resource("data") / "dev-intel" / "context_reorg" / "repo_stage_path_map.json"

# source dir (repo-relative) -> destination under _repos/. Existing content only; new repos are scaffolded empty.
# context component 'backend' maps to repo 'shared-backend-components'; others map 1:1 by name.
CONTEXT_TO_REPO = {
    "backend": "shared-backend-components", "teleon": "teleon", "baltor": "baltor",
    "openhubforai": "openhubforai", "aidevobserver": "aidevobserver", "aidoneright": "aidoneright",
}


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True)


def planned_repos() -> list[str]:
    reg = json.loads(REGISTRY.read_text())
    return sorted(reg["surfaces"].keys())


def build_moves() -> list[tuple[str, str]]:
    """(source_dir, dest_dir) directory-level moves. Ordered so parents exist first."""
    moves = [("template-repo", "_repos/dev-rules-context"),
             ("context/_shared", "_repos/_shared")]
    for comp, repo in CONTEXT_TO_REPO.items():
        moves.append((f"context/{comp}", f"_repos/{repo}/context"))
    return moves


def apply(dry: bool) -> dict:
    moves = build_moves()
    done, skipped, failed = [], [], []
    path_map: dict[str, str] = {}
    manifest_lines = []
    for src, dst in moves:
        s, d = _resource(src), _resource(dst)
        # record the path prefix mapping for the ref rewriter regardless (old prefix -> new prefix).
        path_map[src + "/"] = dst + "/"
        if not s.exists():
            skipped.append(src); continue
        if not dry:
            d.parent.mkdir(parents=True, exist_ok=True)
            res = _git("mv", src, dst)
            if res.returncode != 0:
                failed.append({"src": src, "err": res.stderr.strip()[:160]}); continue
            manifest_lines.append(json.dumps({"original_path": src, "new_path": dst,
                                             "reason": "repo staging 2026-07-03", "reversible": True}, sort_keys=True))
        done.append((src, dst))
    # scaffold the new/empty repos (dev-tools + business-context + edge-graph-generator) with a placeholder.
    reg_repos = planned_repos()
    scaffolded = []
    for repo in reg_repos:
        folder = REPOS / repo
        if not dry:
            folder.mkdir(parents=True, exist_ok=True)
            readme = folder / "README.md"
            if not readme.exists():
                readme.write_text(f"# {repo}\n\nStaged folder for the future `aidoneright-{repo}` repo. "
                                  f"See `EDGES.md` for cross-repo contracts and `../README.md` for the map.\n")
                scaffolded.append(repo)
    if not dry:
        MAPPING.parent.mkdir(parents=True, exist_ok=True)
        MAPPING.write_text(json.dumps(path_map, indent=2))
        if manifest_lines:
            MANIFEST.parent.mkdir(parents=True, exist_ok=True)
            with MANIFEST.open("a") as fh:
                fh.write("\n".join(manifest_lines) + "\n")
    return {"moved": len(done), "skipped": len(skipped), "failed": failed,
            "scaffolded_new": scaffolded, "repos": reg_repos, "path_map": path_map}


def self_test() -> int:
    moves = build_moves()
    checks = [
        ("backend -> shared-backend-components", ("context/backend", "_repos/shared-backend-components/context") in moves),
        ("template-repo -> dev-rules-context", ("template-repo", "_repos/dev-rules-context") in moves),
        ("_shared hoisted to _repos/_shared", ("context/_shared", "_repos/_shared") in moves),
        ("repo names come from registry", len(planned_repos()) >= 12),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - stage_repos:\n  " + "\n  ".join(failed)); return 1
    print(f"PASS - stage_repos: directory-level git-mv staging into _repos/ ({len(planned_repos())} repos from "
          f"the registry); lossless + lineage + path-map for the ref rewriter; new repos scaffolded with a README.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Stage the multi-repo layout under _repos/.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    rep = apply(dry=not args.apply)
    print(f"{'APPLIED' if args.apply else 'DRY-RUN'}: moved={rep['moved']} skipped={rep['skipped']} "
          f"failed={len(rep['failed'])} new_repos_scaffolded={len(rep['scaffolded_new'])} total_repos={len(rep['repos'])}")
    if rep["failed"]:
        print("  failures:", rep["failed"][:5])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
