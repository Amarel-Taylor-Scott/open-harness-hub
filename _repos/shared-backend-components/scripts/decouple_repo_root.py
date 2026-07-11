#!/usr/bin/env python3
"""scripts/decouple_repo_root — replace the depth-coupled repo-root computation
`Path(__file__).resolve().parents[D]` (D == the file's directory depth, so it points at the repo root) with
a self-contained, depth-INDEPENDENT walk-up to the `.aidoneright-root` marker.

Why SELF-CONTAINED (an inline expression, not an import): many files compute the root precisely to bootstrap
`sys.path` before `import scripts.X` — importing a helper there would be circular. The inline walk-up needs
only `Path` (already imported wherever `Path(__file__)` is used), so it works everywhere, including bootstrap.

Why SAFE: at the file's current location the walk-up returns the identical path as `parents[D]` (the nearest
ancestor holding the marker IS the repo root), so behavior is unchanged NOW; and it stays correct after the
file moves into a per-repo folder (unlike a fixed `parents[D]`). Precise: only `parents[<D>]` with D == the
file's dir depth is touched; any other `parents[N]` (a genuine local reference) is left alone. Idempotent.

`--dry-run` lists changes; `--apply` writes; `--paths <files…>` scopes to a subsystem for verified batches;
`--self-test` proves the depth math + rewrite offline.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MARKER = ".aidoneright-root"


def dir_depth(rel_path: str) -> int:
    """Directory segments above the file = the parents[] index that equals the repo root.
    'scripts/x.py' -> 1 ; 'src/teleon/a/y.py' -> 3."""
    return len(Path(rel_path).parts) - 1


def _root_pattern(depth: int) -> re.Pattern:
    return re.compile(rf"Path\(__file__\)(?:\.resolve\(\))?\.parents\[{depth}\]")


def _replacement(depth: int) -> str:
    # self-contained walk-up to the marker, with the original parents[depth] as a safe fallback.
    return (f'next((_ar for _ar in Path(__file__).resolve().parents if (_ar / "{MARKER}").exists()), '
            f'Path(__file__).resolve().parents[{depth}])')


def process(rel_path: str, apply: bool) -> int:
    p = _resource(rel_path)
    try:
        text = p.read_text(encoding="utf-8")
    except Exception:  # noqa: BLE001
        return 0
    depth = dir_depth(rel_path)
    pat = _root_pattern(depth)
    if MARKER in text or not pat.search(text):   # already decoupled or nothing to do
        return 0
    n = len(pat.findall(text))
    new = pat.sub(_replacement(depth), text)
    if apply and new != text:
        p.write_text(new, encoding="utf-8")
    return n


def candidates(paths: list[str] | None) -> list[str]:
    if paths:
        return [p for p in paths if p.endswith(".py")]
    out = subprocess.run(["git", "ls-files", "*.py"], cwd=REPO, capture_output=True, text=True, check=True)
    skip = ("_repos/", "node_modules/", ".venv/", "site/", "dist/", "templates/")  # templates render code-as-strings; depth is placeholder-relative
    return [f for f in out.stdout.splitlines()
            if f and not f.startswith(skip) and f != "scripts/decouple_repo_root.py"]


def run(paths: list[str] | None, apply: bool) -> dict:
    files = candidates(paths)
    changed = []
    for f in files:
        n = process(f, apply)
        if n:
            changed.append({"file": f, "occurrences": n, "depth": dir_depth(f)})
    return {"scanned": len(files), "changed": changed, "total_occurrences": sum(c["occurrences"] for c in changed)}


def self_test() -> int:
    checks = [
        ("depth of scripts/x.py is 1", dir_depth("scripts/x.py") == 1),
        ("depth of src/teleon/a/y.py is 3", dir_depth("src/teleon/a/y.py") == 3),
        ("pattern matches parents[1] with resolve", bool(_root_pattern(1).search("Path(__file__).resolve().parents[1]"))),
        ("pattern matches no-resolve form", bool(_root_pattern(2).search("Path(__file__).parents[2]"))),
        ("pattern does NOT match a different index", not _root_pattern(1).search("Path(__file__).resolve().parents[3]")),
        ("replacement walks up to the marker", MARKER in _replacement(1) and "parents" in _replacement(1)),
        ("rewrite is behavior-preserving text-wise",
         _root_pattern(1).sub(_replacement(1), "REPO = Path(__file__).resolve().parents[1]").startswith("REPO = next((")),
        ("replacement is valid python (compiles)", _compiles(f"from pathlib import Path\nREPO = {_replacement(2)}\n")),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - decouple_repo_root:\n  " + "\n  ".join(failed)); return 1
    print("PASS - decouple_repo_root: replaces the depth-coupled parents[D] repo-root idiom with a self-"
          "contained walk-up to the marker (no import, so bootstrap files are safe); same value now, move-safe later.")
    return 0


def _compiles(src: str) -> bool:
    try:
        compile(src, "<t>", "exec"); return True
    except SyntaxError:
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Decouple the repo-root computation from file depth (safe walk-up).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--paths", nargs="*")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    rep = run(args.paths, args.apply)
    print(f"{'APPLIED' if args.apply else 'DRY-RUN'}: {len(rep['changed'])}/{rep['scanned']} files, "
          f"{rep['total_occurrences']} repo-root sites -> marker walk-up")
    for c in rep["changed"][:12]:
        print(f"  {c['file']} (depth {c['depth']}, x{c['occurrences']})")
    if len(rep["changed"]) > 12:
        print(f"  … +{len(rep['changed'])-12} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
