#!/usr/bin/env python3
"""scripts/migrate_dir_to_repo — SAFELY relocate a top-level directory into its owning per-repo folder
under `_repos/<owner>/` while keeping the working monorepo green, per the _repos/ migration.

The move is a git-history-preserving `git mv` PLUS a compat **symlink** left at the old top-level path, so
every existing reference keeps resolving with ZERO rewrites:
  - literal `"schemas/x.json"` opened relative to the repo root  -> root symlink -> new home
  - `_resource("schemas") / "x.json"` Path-parts refs                -> root symlink -> new home
  - `import scripts.X` / `src.<x>` packages                      -> unaffected (namespace path roots)

The ONE hazard a naive `git mv` introduces is **relative bridge symlinks living inside the moved dir**
(left by the earlier docs->_repos context reorg): a `../_repos/...` target that was correct at depth-1
becomes wrong at the new depth. This tool REPAIRS every such symlink by recomputing its target relative to
the symlink's NEW location (fully general via os.path.relpath — not a fixed `../_repos/ -> ../../` string
sub), so no bridge is left dangling. That exact breakage (the North Star prompt) is what motivated this.

Only DATA / CONFIG / DOC dirs are safe to move this way. A dir that is a Python PACKAGE whose modules compute
their own root via `Path(__file__).resolve().parents[N]` must NOT move (the symlink's `.resolve()` follows to
the deeper real path and the root computation breaks) — the tool refuses those (`--check-safe`).

  --plan                 print the owner mapping (which dir -> which _repos/<owner>) without moving
  --move <dir> <owner>   git mv <dir> -> _repos/<owner>/<dir>, add the compat symlink, repair bridges
  --repair <dir>         re-repair bridge symlinks under an already-moved dir (idempotent)
  --check-safe <dir>     report whether <dir> is safe to move (no self-rooting .py packages)
  --self-test            offline proof of the relpath repair + safety classifier
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()),
             Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_REPOS = _REPO / "_repos"


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=_REPO, capture_output=True, text=True)


def repair_bridges(moved_real: Path) -> list[tuple[str, str, str]]:
    """Repair every relative symlink under `moved_real` whose target no longer resolves, by recomputing it
    relative to the symlink's current location. The pre-move location is inferred from the target text: the
    symlink used to sit at `_REPO/<name>/...`; we resolve the old target against THAT, then relpath from the
    new parent. Returns (link, old_target, new_target) for each repair. Idempotent (skips resolving links)."""
    name = moved_real.relative_to(_REPOS).parts[-1]           # e.g. 'prompts'
    old_dir = _REPO / name                                     # where the dir used to live (now the symlink)
    repairs: list[tuple[str, str, str]] = []
    for link in sorted(moved_real.rglob("*")):
        if not link.is_symlink() or link.exists():            # skip non-links + still-valid links
            continue
        old_target = os.readlink(link)
        if os.path.isabs(old_target):
            continue                                          # absolute links don't break on move
        # the link's path as it was BEFORE the move, to resolve the old relative target against:
        old_link_loc = old_dir / link.relative_to(moved_real)
        abs_target = Path(os.path.normpath(old_link_loc.parent / old_target))
        if not abs_target.exists():
            continue                                          # genuinely missing target — leave for inspection
        new_target = os.path.relpath(abs_target, link.parent)
        os.remove(link)
        os.symlink(new_target, link)
        repairs.append((str(link.relative_to(_REPO)), old_target, new_target))
    return repairs


_JS_EXT = {".mjs", ".js", ".cjs", ".ts", ".mts", ".cts", ".jsx", ".tsx"}


def is_safe_to_move(dir_name: str) -> tuple[bool, str]:
    """A dir is UNSAFE to move if it contains files that resolve repo paths RELATIVE TO THEIR OWN LOCATION,
    because moving them behind a symlink makes the resolver follow to the deeper real path:
      - Python: `Path(__file__).resolve().parents[N]` / `os.path.dirname(...abspath(__file__))` (`.resolve()`
        follows the symlink), and
      - JS/TS: parent-relative imports/reads `'../…'` (Node/bundlers resolve the realpath, so `../web` from a
        moved `e2e/` file points into `_repos/…/web`, not the repo root — this is exactly what broke the events
        beacon probe).
    Data/config/doc dirs with neither are safe."""
    base = _REPO / dir_name
    if not base.is_dir():
        return False, f"{dir_name}: not a directory"
    py_selfroot, js_relparent = [], []
    for p in base.rglob("*"):
        if not p.is_file() or any(seg in {"__pycache__", ".venv", "node_modules"} for seg in p.parts):
            continue
        if p.suffix == ".py":
            t = p.read_text(encoding="utf-8", errors="ignore")
            if ".resolve().parents[" in t or "os.path.dirname(os.path.dirname" in t:
                py_selfroot.append(str(p.relative_to(_REPO)))
        elif p.suffix in _JS_EXT:
            t = p.read_text(encoding="utf-8", errors="ignore")
            # JS self-roots via the file's OWN location (Node resolves the realpath, so these follow the
            # symlink to the deeper home): `import.meta.url` / `__dirname` (repo-root-from-file, e.g. the beacon
            # probe's `dirname(dirname(fileURLToPath(import.meta.url)))`), or a parent-relative `'../` ref.
            if "import.meta.url" in t or "__dirname" in t or re.search(r"""['"]\.\./""", t):
                js_relparent.append(str(p.relative_to(_REPO)))
    if py_selfroot:
        return False, f"{dir_name}: {len(py_selfroot)} self-rooting .py module(s) — move would break .resolve() (e.g. {py_selfroot[0]})"
    if js_relparent:
        return False, f"{dir_name}: {len(js_relparent)} JS/TS file(s) with parent-relative imports — move would break realpath resolution (e.g. {js_relparent[0]})"
    return True, f"{dir_name}: safe (data/config/doc dir, no self-rooting .py or parent-relative JS)"


def move(dir_name: str, owner: str) -> int:
    src = _REPO / dir_name
    if src.is_symlink():
        print(f"  {dir_name}: already a symlink -> {os.readlink(src)} (already moved); repairing bridges only")
        return 0 if _repair_only(dir_name) == 0 else 1
    ok, why = is_safe_to_move(dir_name)
    if not ok:
        print(f"  REFUSED — {why}"); return 2
    dest_dir = _REPOS / owner
    if not dest_dir.is_dir():
        print(f"  REFUSED — owner repo {dest_dir.relative_to(_REPO)} does not exist"); return 2
    dest = dest_dir / dir_name
    r = _git("mv", dir_name, str(dest.relative_to(_REPO)))
    if r.returncode != 0:
        print(f"  git mv FAILED: {r.stderr.strip()}"); return 1
    rel = os.path.relpath(dest, _REPO)
    os.symlink(rel, src)                                       # compat symlink at the old top-level path
    repairs = repair_bridges(dest)
    print(f"  {dir_name} -> {rel}  (compat symlink added; {len(repairs)} bridge symlink(s) repaired)")
    return 0


def _repair_only(dir_name: str) -> int:
    link = _REPO / dir_name
    if not link.is_symlink():
        print(f"  {dir_name}: not a symlink — nothing to repair"); return 0
    real = (link.parent / os.readlink(link)).resolve()
    repairs = repair_bridges(real)
    print(f"  {dir_name}: {len(repairs)} bridge symlink(s) repaired")
    return 0


# --- owner mapping: DATA/CONFIG/DOC dirs -> the per-repo folder that owns them ------------------------------
# CODE packages (scripts, local_emulators) are deliberately absent — they self-root and must stay at root.
OWNER_MAP = {
    # shared substrate: config contracts + backend infra owned by the shared-backend-components repo
    "architecture": "shared-backend-components", "schemas": "shared-backend-components",
    "vocabularies": "shared-backend-components", "rubrics": "shared-backend-components",
    "db": "shared-backend-components", "pipelines": "shared-backend-components",
    "services": "shared-backend-components", "deploy": "shared-backend-components",
    "fly": "shared-backend-components", "infra": "shared-backend-components",
    "local_emulators": "shared-backend-components",
    # dev tooling + rules owned by the devkit repo
    "prompts": "dev-rules-context", "hooks": "dev-rules-context", "mcp": "dev-rules-context",
    "commands": "dev-rules-context", "code-templates": "dev-rules-context",
    "workflows": "dev-rules-context",
    "editor": "dev-rules-context", "skills": "dev-rules-context",
    # NOTE: `templates/` (self-rooting rendered .py) and `e2e/` (Node probes with `../web`,`../dist`
    # parent-relative imports that break under realpath resolution) are intentionally ABSENT — the tool
    # refuses both; and `_repos/shared-backend-components/scripts/`/product `src/`/`web/` stay at root (they self-root en masse).
}


def _self_test() -> int:
    import tempfile
    fails: list[str] = []

    def ck(name: str, ok: bool) -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
        if not ok:
            fails.append(name)

    # relpath repair math: a link that was at root/D/a.md -> ../_repos/x/y.md, moved to _repos/OWN/D/a.md,
    # must repoint to ../../x/y.md (both resolve to _repos/x/y.md).
    old = os.path.normpath(Path("/r/D") / "../_repos/x/y.md")
    ck("old relative target resolves under repo root", old == os.path.normpath("/r/_repos/x/y.md"))
    new = os.path.relpath("/r/_repos/x/y.md", "/r/_repos/OWN/D")
    ck("recomputed target from new depth-3 location is ../../x/y.md", new == "../../x/y.md")

    # safety classifier flags a self-rooting .py, passes a pure-data dir
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        (base / ".aidoneright-root").write_text("")
        (base / "cfg").mkdir(); (base / "cfg" / "a.json").write_text("{}")
        (base / "pkg").mkdir(); (base / "pkg" / "m.py").write_text("import x\nR = Path(__file__).resolve().parents[1]\n")
        global _REPO
        _saved = _REPO; _REPO = base
        try:
            ck("pure-data dir classified SAFE", is_safe_to_move("cfg")[0] is True)
            ck("self-rooting .py dir classified UNSAFE", is_safe_to_move("pkg")[0] is False)
        finally:
            _REPO = _saved

    ck("owner map excludes the self-rooting/unsafe dirs (scripts, e2e, templates)",
       not ({"scripts", "e2e", "templates"} & set(OWNER_MAP)))
    print("\n" + ("PASS — migrate_dir_to_repo: relpath bridge-repair + self-rooting safety classifier proven."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="Safely relocate a top-level dir into its _repos/<owner> home.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--move", nargs=2, metavar=("DIR", "OWNER"))
    ap.add_argument("--repair", metavar="DIR")
    ap.add_argument("--check-safe", metavar="DIR")
    a = ap.parse_args()
    if a.self_test:
        return _self_test()
    if a.plan:
        print("owner mapping (data/config/doc dirs -> _repos/<owner>):")
        for d, o in sorted(OWNER_MAP.items()):
            here = _REPO / d
            state = "moved" if here.is_symlink() else ("at-root" if here.is_dir() else "absent")
            print(f"  {d:<16} -> {o:<26} [{state}]")
        return 0
    if a.check_safe:
        ok, why = is_safe_to_move(a.check_safe); print(f"  {why}"); return 0 if ok else 1
    if a.repair:
        return _repair_only(a.repair)
    if a.move:
        return move(a.move[0], a.move[1])
    ap.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(main())
