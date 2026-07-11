"""scripts/_repo_paths — the ONE place that knows where code lives after the _repos/ migration.

As product/backend code moves into `_repos/<repo>/backend/`, its import root must be on `sys.path` for the
existing `src.<x>` / package imports to keep resolving (no import rewrites — `src` is a namespace package
that spans the repo root + every backend root). This module computes those roots so the proof runner, a
root `conftest.py`, and any dev/CI entrypoint all agree — a single source of truth for the path, per
NO-MAGIC-VALUES. Deterministic (sorted); no side effects on import beyond exposing the functions.
"""
from __future__ import annotations

import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
_REPOS = REPO / "_repos"

# Markers that identify the repo root, so repo_root() finds it by WALKING UP rather than by a fixed
# parents[N] depth — a module that moves deeper still resolves the true root (the fix for the coupling that
# breaks on a file move). `.aidoneright-root` is the explicit sentinel; `.git` is the fallback.
_ROOT_MARKERS = (".aidoneright-root", ".git")
_root_cache: "Path | None" = None


def repo_root() -> Path:
    """The repository root, found by walking up from THIS module to a marker. Depth-independent: unlike
    `Path(__file__).resolve().parents[N]`, this stays correct when a consuming module is relocated. Use
    `from scripts._repo_paths import repo_root; REPO = repo_root()` in place of a hardcoded parents[N] root."""
    global _root_cache
    if _root_cache is None:
        here = Path(__file__).resolve()
        _root_cache = next((c for c in (here.parent, *here.parents)
                            if any((c / m).exists() for m in _ROOT_MARKERS)), REPO)
    return _root_cache


def code_roots() -> list[str]:
    """All import roots, most-specific-last, deduped + deterministic: the repo root (unmoved code) + every
    `_repos/*/backend` (moved backends) + `_repos/shared-backend-components` (if the shared tooling moved there)."""
    root = repo_root()                      # walk-up to the marker — CORRECT even though this file moved deeper
    repos = root / "_repos"                 # into _repos/shared-backend-components/scripts (parents[1] would be wrong)
    roots: list[str] = [str(root)]
    if repos.is_dir():
        for backend in sorted(repos.glob("*/backend")):   # _repos/<x>/backend so `import src.<x>` resolves
            if backend.is_dir():
                roots.append(str(backend))
        sbc = repos / "shared-backend-components"
        if sbc.is_dir():                    # substrate repo: holds importable top-level packages relocated
            roots.append(str(sbc))          # from root (local_emulators, db, services, scripts, …) so
            #                                 `import scripts.x` / `import local_emulators` resolve symlink-free.
    seen: set[str] = set()
    return [r for r in roots if not (r in seen or seen.add(r))]


def pythonpath(base: str | None = ".") -> str:
    """A PYTHONPATH string for subprocesses: the code roots, plus an optional base (default '.')."""
    parts = code_roots()
    if base and base not in parts:
        parts.append(base)
    return os.pathsep.join(parts)


def install(into_sys_path: bool = True) -> list[str]:
    """Prepend the code roots to sys.path (for in-process use, e.g. from conftest). Returns the roots added."""
    roots = code_roots()
    if into_sys_path:
        import sys
        for r in reversed(roots):
            if r not in sys.path:
                sys.path.insert(0, r)
    return roots


def self_test() -> int:
    roots = code_roots()
    ok = (str(REPO) in roots) and roots == list(dict.fromkeys(roots))  # repo root present + deduped
    pp = pythonpath()
    ok = ok and str(REPO) in pp
    # regression: a dot-headed rel resolves under its OWN name — lstrip("./") strips chars, not a prefix,
    # and used to mangle ".agent" -> "<root>/agent" (an unapproved top-level dir)
    ok = ok and resource(".agent").name == ".agent" and resource("./architecture") == resource("architecture")
    print("PASS - _repo_paths: single-source code-root computation (repo root + _repos/*/backend), "
          f"deduped + deterministic ({len(roots)} root(s)); dot-head rel paths resolve unmangled."
          if ok else "FAIL - _repo_paths")
    return 0 if ok else 1


_moved_cache: "dict[str, Path] | None" = None


def _moved_map() -> "dict[str, Path]":
    """Map of top-level dir NAME -> its real location after the _repos/ migration. AUTHORITATIVE source is the
    manifest `_repos/_moved_dirs.json` (name -> repo-relative _repos path), maintained as dirs are moved — so
    ONLY dirs that were actually relocated FROM the repo root are mapped (never an incidental `_repos/*/context`
    subdir). Lets code find a relocated resource dir WITHOUT a compat symlink at the old root path, so the
    symlink can be deleted and the dir truly leaves the root. Falls back to a scoped glob if the manifest is
    absent (fresh clone before first move)."""
    global _moved_cache
    if _moved_cache is None:
        import json
        root = repo_root()
        m: dict[str, Path] = {}
        manifest = root / "_repos" / "_moved_dirs.json"
        if manifest.is_file():
            try:
                for name, rel in json.loads(manifest.read_text()).items():
                    p = root / rel
                    if p.exists():
                        m[name] = p
            except Exception:  # noqa: BLE001 — corrupt manifest never breaks resolution
                m = {}
        _moved_cache = m
    return _moved_cache


# web/<brand> moved into each surface's own repo as <brand>/frontend; context-is-everything was renamed aidoneright.
_WEB_TO_FRONTEND = {"context-is-everything": "aidoneright"}
# src/<x> product backends moved under _repos/<x>/backend/src/<x> (the canonical_code_path inverse). These are the
# surfaces whose backend code was relocated; a src path for any other head falls through to the manifest/root logic.
_BACKEND_SURFACES = ("teleon", "baltor", "openhubforai", "aidevobserver", "aidoneright")


def resource(rel: str) -> Path:
    """Resolve a repo-relative resource path to its REAL location, whether its top-level dir still lives at the
    repo root or has been relocated under `_repos/<owner>/`. THE universal root-relative→real resolver: use it in
    place of `repo_root() / "<path>"` for ANY moved path — a data/config/doc dir, a `web/<brand>` frontend, or a
    `src/<x>` backend — so a data-driven path read from a registry resolves with no root symlink:
        VOCAB_DIR = resource("vocabularies")             # -> _repos/shared-backend-components/vocabularies
        open(resource("architecture/x.json"))            # data-driven config paths resolve
        resource("web/baltor/index.html")                # -> _repos/baltor/frontend/index.html
        resource("src/teleon/registry/port.py")          # -> _repos/teleon/backend/src/teleon/registry/port.py
    Falls back to `repo_root()/<rel>` for a head that never moved, and still works if a transitional symlink is
    present. Idempotent + cheap (the _repos scan is cached)."""
    # strip "./" PREFIXES (never lstrip("./"), which strips CHARACTERS and mangles dot-heads: ".agent" -> "agent",
    # sending runtime state to an unapproved top-level dir — found live via check_file_layout_policy)
    rel = str(rel).replace("\\", "/")
    while rel.startswith("./"):
        rel = rel[2:]
    rel = rel.lstrip("/")
    head, _, tail = rel.partition("/")
    root = repo_root()
    if head == "web" and tail:                                   # web/<brand>[/rest] -> _repos/<repo>/frontend[/rest]
        brand, _, rest = tail.partition("/")
        base = root / "_repos" / _WEB_TO_FRONTEND.get(brand, brand) / "frontend"
        return base / rest if rest else base
    if head == "src" and tail:                                   # src/<x>[/rest] -> _repos/<x>/backend/src/<x>[/rest]
        sub, _, rest = tail.partition("/")
        if sub in _BACKEND_SURFACES:
            base = root / "_repos" / sub / "backend" / "src" / sub
            return base / rest if rest else base
    base = _moved_map().get(head)
    if base is None:
        base = root / head
    return base / tail if tail else base


def canonical_code_path(rel_path: str) -> str:
    """Normalize a code path for STABLE ids/names across the _repos/ relocation: a backend staged under
    _repos/<x>/backend/src/<x>/... is canonically src/<x>/... (so names, graph node ids, and migration
    baselines do not change when the file physically moves). Idempotent; leaves non-staged paths alone."""
    p = rel_path.replace(chr(92), "/").split("/")
    if len(p) >= 3 and p[0] == "_repos" and p[2] == "backend":
        return "/".join(p[3:])
    return rel_path


# the __main__ block lives at file END so self_test() can reference every def above (it once sat mid-file,
# before resource() existed, and a self-test touching resource() died with NameError at bare launch)
if __name__ == "__main__":
    import sys
    sys.exit(self_test() if "--self-test" in sys.argv else (print(pythonpath()) or 0))
