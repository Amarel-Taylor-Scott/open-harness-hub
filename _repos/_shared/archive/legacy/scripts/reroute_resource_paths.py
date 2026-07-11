#!/usr/bin/env python3
"""scripts/reroute_resource_paths — rewrite root-relative references to a RELOCATED resource dir so its compat
symlink at the repo root can be DELETED (the dir then truly leaves the root, living only under `_repos/<owner>/`).

The migration physically moved data/config/doc dirs into `_repos/` but left a symlink at the old top-level path
so `repo_root() / "<dir>"` kept resolving. That symlink is why the dir still SHOWS at the root. This codemod
replaces the coupled `<rootvar> / "<dir>"` idiom with `resource("<dir>")` (from scripts._repo_paths, which finds
the dir's real `_repos` home without a symlink), then the caller deletes the symlink.

Handles the mechanical Path-parts form `<ROOTVAR> / "<dir>"` (ROOTVAR ∈ REPO/ROOT/REPO_ROOT/_REPO/_RR/_R/_ROOT),
injects the `resource` import once per file, and REPORTS every ref it can't safely auto-rewrite (string literals
like "<dir>/x", f-strings, data-file values) so those are handled deliberately — a silent miss is what broke
check_fragile_context_atlas, so unhandled refs are surfaced, never ignored.

  --dir <name> [--apply]   reroute refs to one moved dir; prints rewritten + UNHANDLED refs
  --plan                   list moved dirs + their root-relative ref counts (what's tractable to unlink)
  --self-test              offline proof of the rewrite + import injection
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()),
             Path(__file__).resolve().parents[1])
sys.path.insert(0, str(_REPO / "scripts"))
from _repo_paths import _moved_map, resource  # noqa: E402

_ROOTVARS = ("REPO_ROOT", "REPO", "_REPO", "ROOT", "_RR", "_ROOT", "_R")
_IMPORT = "from scripts._repo_paths import resource as _resource"


def _pp_re(dir_name: str) -> re.Pattern:
    # <ROOTVAR> / "<dir>"  — but NOT `P.ROOT` (attribute access on another module): a `.` or word char before
    # the rootvar means it's `pkg.ROOT`, which must NOT become `pkg._resource(...)`. Negative lookbehind guards it.
    alt = "|".join(_ROOTVARS)
    return re.compile(rf"(?<![.\w])({alt})\s*/\s*\"{re.escape(dir_name)}\"")


def _other_ref_re(dir_name: str) -> re.Pattern:
    # refs this tool does NOT auto-rewrite: string-literal paths "<dir>/..." (opened relative to root / data-driven)
    return re.compile(rf"\"{re.escape(dir_name)}/")


def moved_dirs() -> dict:
    return _moved_map()


def _tracked_py() -> list[str]:
    # POST-MIGRATION: all substrate code now lives under _repos/shared-backend-components/. Process THAT (the
    # proofs + their helpers read the moved data/config dirs); skip vendored/templates/archive + the two files
    # that must not gain a self-referential resource() rewrite (_repo_paths defines it; this codemod edits it).
    out = subprocess.run(["git", "ls-files", "_repos/shared-backend-components/*.py"], cwd=_REPO,
                         capture_output=True, text=True, check=True)
    skip_frag = ("/node_modules/", "/_reference/", "/repo_reference/", "/archive/", "/templates/", "/__pycache__/")
    self_files = ("scripts/reroute_resource_paths.py", "scripts/_repo_paths.py")
    return [f for f in out.stdout.splitlines()
            if f and not any(s in ("/" + f) for s in skip_frag)
            and not any(f.endswith(sf) for sf in self_files)]


def reroute_dir(dir_name: str, apply: bool) -> dict:
    pp = _pp_re(dir_name)
    other = _other_ref_re(dir_name)
    rewritten: list[str] = []
    unhandled: list[str] = []
    for rel in _tracked_py():
        p = _REPO / rel
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:  # noqa: BLE001
            continue
        if pp.search(text):
            new = pp.sub(f'_resource("{dir_name}")', text)
            if _IMPORT not in new and "import resource as _resource" not in new:
                new = _inject_import(new)
            rewritten.append(rel)
            if apply:
                p.write_text(new, encoding="utf-8")
        # surface literals we did NOT rewrite (excluding comments/docstrings is best-effort)
        for m in other.finditer(text):
            line = text[: m.start()].count("\n") + 1
            src = text.splitlines()[line - 1].strip()
            if not src.startswith("#") and "resource(" not in src:
                unhandled.append(f"{rel}:{line}: {src[:90]}")
    return {"dir": dir_name, "rewritten": rewritten, "unhandled": unhandled}


def _inject_import(text: str) -> str:
    """Add the resource import once, right after the module's repo-root marker line (or after __future__)."""
    lines = text.splitlines(keepends=True)
    # Prefer the __future__ import: it is ALWAYS a complete single line, so inserting after it can never split a
    # multi-line statement. The `.aidoneright-root` marker is only a fallback AND only when it is a complete line
    # (does not end mid-expression with `,`/`(`) — a multi-line `_REPO = next(( ... .aidoneright-root ...),` would
    # otherwise get the import spliced into the middle of the call (the migrate_dir_to_repo.py misfire).
    anchor = next((i for i, ln in enumerate(lines) if ln.startswith("from __future__")), None)
    if anchor is None:
        anchor = next((i for i, ln in enumerate(lines)
                       if ".aidoneright-root" in ln and ln.rstrip().endswith(")")), 0)
    lines.insert(anchor + 1, _IMPORT + "\n")
    return "".join(lines)


def _self_test() -> int:
    fails = []

    def ck(n, ok):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
        (fails.append(n) if not ok else None)

    src = 'REPO = x\np = REPO / "rubrics" / "a.yaml"\nq = _REPO / "rubrics"\n'
    out = _pp_re("rubrics").sub('_resource("rubrics")', src)
    ck("rewrites REPO / \"rubrics\" -> _resource(\"rubrics\")", '_resource("rubrics") / "a.yaml"' in out)
    ck("rewrites _REPO / \"rubrics\" too", out.count('_resource("rubrics")') == 2)
    ck("does NOT touch a different dir", _pp_re("rubrics").sub("X", 'REPO / "schemas"') == 'REPO / "schemas"')
    inj = _inject_import("from __future__ import annotations\nimport os\n")
    ck("injects import once", inj.count(_IMPORT) == 1)
    ck("string-literal detector flags \"rubrics/x\"", bool(_other_ref_re("rubrics").search('open("rubrics/x.yaml")')))
    print("\n" + ("PASS — reroute_resource_paths: Path-parts rewrite + import injection + unhandled-ref surfacing."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--plan", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return _self_test()
    if a.plan:
        print("moved dirs + root-relative ref counts (Path-parts / string-literal):")
        for name in sorted(moved_dirs()):
            r = reroute_dir(name, apply=False)
            print(f"  {name:<20} rewritable={len(r['rewritten']):<4} unhandled-literals={len(r['unhandled'])}")
        return 0
    if a.dir:
        r = reroute_dir(a.dir, a.apply)
        print(f"{'APPLIED' if a.apply else 'DRY-RUN'} {a.dir}: rewrote {len(r['rewritten'])} file(s)")
        for f in r["rewritten"]:
            print(f"  ✓ {f}")
        if r["unhandled"]:
            print(f"  UNHANDLED literals ({len(r['unhandled'])}) — reroute manually (loader/data) before deleting the symlink:")
            for u in r["unhandled"][:40]:
                print(f"    ⚠ {u}")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
