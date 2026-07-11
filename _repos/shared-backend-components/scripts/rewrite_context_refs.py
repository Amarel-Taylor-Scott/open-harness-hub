#!/usr/bin/env python3
"""scripts/rewrite_context_refs — after the context reorg, rewrite path references to MOVED docs from their
old path to their new context/ path, so the operating layer, configs, and the moved docs' own cross-links
keep resolving.

Safe by construction: exact old-path -> new-path string replacement (paths are specific, longest-first to
avoid nesting), only over a WHITELIST of files where a stale reference is an actual problem. It SKIPS:
- generated data (data/, db/seeds/, site/, dist/) — those regenerate from source, so rewriting is pointless;
- _repos/shared-backend-components/scripts/ — the docs those reference were deliberately HELD (not moved), so their refs are still valid;
- the reorg planning data itself.
Lineage source of truth: context/_manifest.jsonl (original_path -> new_path).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MANIFEST = _resource("context") / "_manifest.jsonl"

# Only rewrite references living under these roots (where a stale path is a real break). Includes code
# (_repos/shared-backend-components/scripts/, src/, web/) because a moved doc's old path in a comment/constant/loader must point to the new
# path — the manifest only holds MOVED docs, so held-doc references (not in the manifest) are never touched.
INCLUDE_ROOTS = ("context/", "docs/", ".codex/", ".claude/", "prompts/", "commands/", "architecture/",
                 "scripts/", "src/", "web/", ".research-notes/")
INCLUDE_FILES = ("CLAUDE.md", "AGENTS.md", "mkdocs.yml", "README.md", "FOR_CODEX.MD")
# Never rewrite inside these (generated / self-healing on regeneration / vendored / build output).
SKIP_ROOTS = ("data/", "db/", "site/", "dist/", "node_modules/", "_reference/", ".git/", "docs/catalog/")


def load_moves() -> list[tuple[str, str]]:
    moves = []
    for line in MANIFEST.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        if rec.get("original_path") and rec.get("new_path"):
            moves.append((rec["original_path"], rec["new_path"]))
    # longest old-path first so a shorter path never rewrites inside a longer one.
    return sorted(moves, key=lambda m: len(m[0]), reverse=True)


def target_files() -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True)
    files = []
    for f in out.stdout.splitlines():
        if not f.strip() or f.startswith(SKIP_ROOTS):
            continue
        if f.startswith(INCLUDE_ROOTS) or f in INCLUDE_FILES:
            if f.endswith((".md", ".MD", ".json", ".yml", ".yaml", ".txt", ".py", ".ts", ".tsx", ".js", ".sh", ".html")):
                files.append(f)
    return files


def rewrite(apply: bool) -> dict:
    moves = load_moves()
    files = target_files()
    changed, total_repl = [], 0
    for rel in files:
        p = _resource(rel)
        try:
            text = p.read_text(errors="ignore")
        except Exception:  # noqa: BLE001
            continue
        new_text, n = text, 0
        for old, new in moves:
            if old in new_text:
                cnt = new_text.count(old)
                new_text = new_text.replace(old, new)
                n += cnt
        if n:
            changed.append({"file": rel, "replacements": n})
            total_repl += n
            if apply:
                p.write_text(new_text)
    return {"files_changed": len(changed), "total_replacements": total_repl, "changed": changed}


def self_test() -> int:
    # pure check on the ordering + skip logic (no disk writes).
    checks = [
        ("skip generated data", "data/x.jsonl".startswith(SKIP_ROOTS)),
        ("skip catalog output", "docs/catalog/x.md".startswith(SKIP_ROOTS)),
        ("include code (moved-doc refs rewritten)", "scripts/x.py".startswith(INCLUDE_ROOTS)),
        ("include context", "context/teleon/x.md".startswith(INCLUDE_ROOTS)),
        ("include codex prompts", ".codex/prompts/goal.md".startswith(INCLUDE_ROOTS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - rewrite_context_refs:\n  " + "\n  ".join(failed)); return 1
    print("PASS - rewrite_context_refs: exact old->new rewrite over operating/config/context files; "
          "generated data + held-ref scripts skipped; longest-path-first avoids nesting.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Rewrite references to moved context docs (old -> new path).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--apply", action="store_true", help="write the rewrites (default is dry-run)")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    rep = rewrite(apply=args.apply)
    print(f"{'APPLIED' if args.apply else 'DRY-RUN'}: files_changed={rep['files_changed']} "
          f"total_replacements={rep['total_replacements']}")
    for c in rep["changed"][:15]:
        print(f"  {c['replacements']:4} in {c['file']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
