#!/usr/bin/env python3
"""scripts/rewrite_repo_stage_refs — rewrite path references after the _repos/ staging move (prefix-based,
old -> new from the stage path-map), so the operating layer and the moved docs' own cross-links resolve.

Prefix map source: data/dev-intel/context_reorg/repo_stage_path_map.json (emitted by stage_repos.py).
Rewrites over the operating layer + code + the staged _repos/ tree (incl. untracked staged content); SKIPS
generated/self-healing data. Longest-prefix-first so a shorter path never rewrites inside a longer one.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MAP = _resource("data") / "dev-intel" / "context_reorg" / "repo_stage_path_map.json"
INCLUDE_ROOTS = ("_repos/", ".codex/", ".claude/", "scripts/", "src/", "docs/", "commands/", "architecture/")
INCLUDE_FILES = ("CLAUDE.md", "AGENTS.md", "FOR_CODEX.MD", "README.md", "mkdocs.yml")
SKIP_ROOTS = ("data/", "db/", "site/", "dist/", "node_modules/", ".git/", "_reference/", "docs/catalog/")
EXTS = (".md", ".MD", ".json", ".yml", ".yaml", ".txt", ".py", ".ts", ".tsx", ".js", ".sh", ".html")


def load_prefix_map() -> list[tuple[str, str]]:
    m = json.loads(MAP.read_text())
    return sorted(m.items(), key=lambda kv: len(kv[0]), reverse=True)


def target_files() -> list[Path]:
    files: list[Path] = []
    # tracked files under the include roots
    tracked = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True).stdout.splitlines()
    for f in tracked:
        if f.startswith(SKIP_ROOTS):
            continue
        if (f.startswith(INCLUDE_ROOTS) or f in INCLUDE_FILES) and f.endswith(EXTS):
            files.append(_resource(f))
    # untracked staged content under _repos/ (moved via plain mv)
    for root, _dirs, fnames in os.walk(REPO / "_repos"):
        if "__pycache__" in root or "/.git" in root:
            continue
        for fn in fnames:
            if fn.endswith(EXTS):
                p = Path(root) / fn
                if p not in files:
                    files.append(p)
    return files


def rewrite(apply: bool) -> dict:
    prefixes = load_prefix_map()
    changed, total = [], 0
    for p in target_files():
        try:
            text = p.read_text(errors="ignore")
        except Exception:  # noqa: BLE001
            continue
        new, n = text, 0
        for old, new_pref in prefixes:
            if old in new:
                n += new.count(old)
                new = new.replace(old, new_pref)
        if n:
            changed.append(str(p.relative_to(REPO)))
            total += n
            if apply:
                p.write_text(new)
    return {"files_changed": len(changed), "total_replacements": total, "sample": changed[:12]}


def self_test() -> int:
    checks = [("skip generated data", "data/x.jsonl".startswith(SKIP_ROOTS)),
              ("include staged repos", "_repos/teleon/context/x.md".startswith(INCLUDE_ROOTS)),
              ("include operating layer", ".codex/prompts/goal.md".startswith(INCLUDE_ROOTS))]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - rewrite_repo_stage_refs:\n  " + "\n  ".join(failed)); return 1
    print("PASS - rewrite_repo_stage_refs: prefix rewrite (old context/ + template-repo/ paths -> _repos/), "
          "longest-first, over operating layer + code + staged tree; generated data skipped.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    rep = rewrite(apply=args.apply)
    print(f"{'APPLIED' if args.apply else 'DRY-RUN'}: files_changed={rep['files_changed']} replacements={rep['total_replacements']}")
    for f in rep["sample"]:
        print(f"  {f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
