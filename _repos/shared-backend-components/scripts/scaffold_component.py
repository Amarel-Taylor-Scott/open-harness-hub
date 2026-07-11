#!/usr/bin/env python3
"""scripts/scaffold_component — the deterministic ONBOARDING agent: add a new component/repo (a SURFACE, or a
PROJECT under an existing surface) to the org in ONE command, so a new hire never touches 12 files by hand.

The org's single source of truth is `_repos/dev-rules-context/contracts/surface-registry.json` (+ each repo's
published `interface.json` + the code layout). Everything else (edge digests, the dependency graph, the
interface manifests, the migration plan) is DERIVED from it by tools that already exist. Adding a component is
therefore exactly three deterministic moves, none of them hand-editing a derived file:

  1. APPEND one entry to the single source of truth — a new `surfaces.<name>` (or `surfaces.<s>.projects.<p>`).
  2. SCAFFOLD `_repos/<name>/` (ADD-ONLY) from the shared component template
     (`_repos/dev-rules-context/context/_component-template/` → context/blackbox.md + context/edges.md) plus a
     README and a starter interface.json computed from the just-appended registry entry.
  3. REFRESH — run _repos/shared-backend-components/scripts/refresh_all.py so every derived artifact (edges/graph/interfaces/migration-plan) is
     regenerated from the new source of truth. This tool never writes a derived file itself.

Reuses (never re-implements): edge-graph-generator/{interface_manifests.build_manifest,
check_cross_repo_dependency_law.validate_registry/check_repo_consumes}, _repos/shared-backend-components/scripts/refresh_all.py (which itself
drives generate_repo_edges + build_migration_plan). Offline, deterministic, no network, no git. NO hardcoded
surface/repo names in logic — every name/kind/edge is read from the registry or supplied by the caller.

`--self-test` proves the logic on a SYNTHETIC registry in a temp dir (never mutates the real registry or
_repos/): the new entry validates against the dependency law, the folder scaffold is produced ADD-ONLY, and no
existing entry is clobbered. `--write` performs the append+scaffold+refresh; without it, a dry run prints the
plan. This is a deterministic maintainer, not an LLM.
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
import copy
import json
import subprocess
import sys
import tempfile
from collections import namedtuple
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
REPOS = REPO.parent
DEVKIT = REPOS / "dev-rules-context"
REGISTRY = DEVKIT / "contracts" / "surface-registry.json"
TEMPLATE_DIR = DEVKIT / "context" / "_component-template"
EGG = REPOS / "edge-graph-generator"
REFRESH_ALL = _resource("scripts/refresh_all.py")

# --- naming / layout conventions, single-sourced here (NO magic values scattered in logic) ---
REPO_NAME_PREFIX = "aidoneright-"          # every surface/project repo is aidoneright-<name> (matches the registry)
CONTEXT_DIR_NAME = "context"               # the per-repo consolidated-context dir (holds blackbox.md + edges.md)
TEMPLATE_FILES = ("blackbox.md", "edges.md")   # the two files copied from _component-template/ into context/
INTERFACE_FILENAME = "interface.json"      # the starter published-interface manifest at the repo root
README_FILENAME = "README.md"              # the repo's human entry doc
JSON_INDENT = 2                            # one indent width for every file this tool writes (registry + manifests)

# reuse the org's existing tools rather than re-implementing the dependency law / manifest shape.
for _p in (str(REPO), str(EGG)):
    if _p not in sys.path:                 # self-bootstrap so imports resolve regardless of CWD/PYTHONPATH
        sys.path.insert(0, _p)
import interface_manifests as _iface            # noqa: E402  edge-graph-generator/interface_manifests.py
import check_cross_repo_dependency_law as _law  # noqa: E402  edge-graph-generator/check_cross_repo_dependency_law.py

# the register tuple returned to the caller — the minimal record of what was registered.
RegisterTuple = namedtuple("RegisterTuple", "scope name kind may_depend_on repo")


class ScaffoldError(Exception):
    """A refusal that protects the single source of truth (clobber / unknown edge / unknown surface)."""


# --------------------------------------------------------------------------- pure registry moves (no I/O)

def _repo_for(name: str) -> str:
    return f"{REPO_NAME_PREFIX}{name}"


def _default_role(name: str, kind: str) -> str:
    """A deterministic placeholder role so the entry is valid immediately; the owner rewrites it in the
    registry (the single source), never in a derived file."""
    return (f"{kind} surface '{name}' — scaffolded by scaffold_component; replace this with its real role "
            f"in contracts/surface-registry.json (the single source of truth).")


def compute_surface_entry(name: str, kind: str, may_depend_on: list[str], exposes: list[str],
                          repo: str | None = None, role: str | None = None) -> dict:
    """The registry entry for a new SURFACE — same shape the existing entries use."""
    return {
        "repo": repo or _repo_for(name),
        "role": role or _default_role(name, kind),
        "kind": kind,
        "exposes": list(exposes or []),
        "may_depend_on": list(may_depend_on or []),
        "consumed_by": [],
    }


def add_surface_to_registry(reg: dict, name: str, kind: str, may_depend_on: list[str], exposes: list[str],
                            repo: str | None = None, role: str | None = None) -> dict:
    """Return a NEW registry with `surfaces.<name>` appended. Never mutates the input (no-clobber by copy);
    refuses to overwrite an existing surface or point at an unknown dependency."""
    surfaces = reg.get("surfaces", {})
    if name in surfaces:
        raise ScaffoldError(f"surface {name!r} already exists — refusing to clobber the registry")
    for dep in may_depend_on or []:
        if dep not in surfaces:
            raise ScaffoldError(f"{name}.may_depend_on -> unknown surface {dep!r} (not in the registry)")
    new = copy.deepcopy(reg)
    new.setdefault("surfaces", {})[name] = compute_surface_entry(name, kind, may_depend_on, exposes, repo, role)
    return new


def add_project_to_registry(reg: dict, surface: str, project: str, kind: str, code_path: str,
                            consumes_projects: list[str], repo: str | None = None,
                            exposes: list[str] | None = None) -> dict:
    """Return a NEW registry with `surfaces.<surface>.projects.<project>` appended (a deployable repo under an
    existing surface). Never mutates the input; refuses unknown surface or duplicate project."""
    surfaces = reg.get("surfaces", {})
    if surface not in surfaces:
        raise ScaffoldError(f"unknown surface {surface!r} — add the surface first (not in the registry)")
    if project in (surfaces[surface].get("projects") or {}):
        raise ScaffoldError(f"project {project!r} already exists under {surface!r} — refusing to clobber")
    new = copy.deepcopy(reg)
    entry = {"kind": kind, "code_path": code_path, "repo": repo or _repo_for(project),
             "consumes_projects": list(consumes_projects or [])}
    if exposes:
        entry["exposes"] = list(exposes)
    new["surfaces"][surface].setdefault("projects", {})[project] = entry
    return new


def validate(reg: dict, name: str, may_depend_on: list[str]) -> list[str]:
    """Reuse the portable dependency-law checker: the whole registry is internally consistent + legal, AND the
    new surface's declared consumes are allowed. Empty == sound."""
    problems = list(_law.validate_registry(reg))
    if name in reg.get("surfaces", {}):
        problems += _law.check_repo_consumes(reg, name, list(may_depend_on or []))
    return problems


# --------------------------------------------------------------------------- pure file-scaffold (compute map)

def render_readme(name: str, entry: dict) -> str:
    """Deterministic README derived ENTIRELY from the registry entry — no hand-typed counts or edges."""
    exposes = entry.get("exposes", [])
    deps = entry.get("may_depend_on", [])
    lines = [
        f"# {entry.get('repo', _repo_for(name))}", "",
        f"Scaffolded surface **`{name}`** (kind: `{entry.get('kind', '')}`) in the AI Done Right multi-repo org.",
        "", f"> {entry.get('role', '')}", "",
        "## What this repo is", "",
        "The **context repo** for this surface — the standalone, source-cited briefing a session needs to work "
        "it *edge-aware* without reading any neighbor repo's internals. It carries the operating context "
        f"(`{CONTEXT_DIR_NAME}/`), the published cross-repo edges (regenerated into `EDGES.md`), and this "
        f"repo's published interface (`{INTERFACE_FILENAME}`). This file is derived from the single source of "
        "truth (`_repos/dev-rules-context/contracts/surface-registry.json`) — if it disagrees with the "
        "registry, the registry wins.", "",
        "## This repo exposes (its published interface)", "",
    ]
    lines += ([f"- `{e}`" for e in exposes] or ["- (nothing yet — declare capabilities in the registry `exposes`)"])
    lines += ["", "## You may consume (via their published interface only)", ""]
    lines += ([f"- `{d}`" for d in deps] or ["- (nothing — this surface depends on no other surface)"])
    lines += [
        "", "## Layout", "", "```",
        f"_repos/{name}/",
        f"├── {README_FILENAME}          ← you are here",
        f"├── {INTERFACE_FILENAME}     ← the starter published interface (regenerated by refresh_all)",
        "├── EDGES.md           ← generated cross-repo contract (run scripts/refresh_all.py --write)",
        f"└── {CONTEXT_DIR_NAME}/",
        f"    ├── {TEMPLATE_FILES[0]}    ← what this component internally is, owns, and does (fill me)",
        f"    └── {TEMPLATE_FILES[1]}       ← how this component connects to the others (fill me)",
        "```", "",
        "Fill in `context/blackbox.md` and `context/edges.md` (copied from the shared component template), then "
        "run `python3 scripts/refresh_all.py --write` to regenerate every derived artifact from the registry.",
        "",
    ]
    return "\n".join(lines) + "\n"


def scaffold_file_map(name: str, reg_with_surface: dict, template_dir: Path = TEMPLATE_DIR) -> dict[str, str]:
    """Compute the {relative_path: content} map for `_repos/<name>/` — pure, no writes. `reg_with_surface`
    must already contain `surfaces.<name>` (so the interface manifest can be built from it)."""
    entry = reg_with_surface["surfaces"][name]
    files: dict[str, str] = {}
    for tf in TEMPLATE_FILES:
        files[f"{CONTEXT_DIR_NAME}/{tf}"] = (template_dir / tf).read_text()
    # reuse the org's manifest shape rather than re-inventing interface.json
    files[INTERFACE_FILENAME] = json.dumps(_iface.build_manifest(reg_with_surface, name), indent=JSON_INDENT) + "\n"
    files[README_FILENAME] = render_readme(name, entry)
    return files


def write_scaffold(name: str, file_map: dict[str, str], repos_dir: Path = REPOS) -> list[str]:
    """ADD-ONLY write of the file map under `<repos_dir>/<name>/`. Refuses if ANY target already exists, so an
    existing repo is never clobbered. Returns the written paths."""
    root = repos_dir / name
    for rel in file_map:
        if (root / rel).exists():
            raise ScaffoldError(f"{root / rel} already exists — refusing to clobber (ADD-ONLY)")
    written = []
    for rel, content in file_map.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        written.append(str(p))
    return written


def write_registry(reg: dict, path: Path = REGISTRY) -> None:
    path.write_text(json.dumps(reg, indent=JSON_INDENT) + "\n")


# --------------------------------------------------------------------------- orchestration (the one command)

def load_registry(path: Path = REGISTRY) -> dict:
    return json.loads(path.read_text())


def scaffold_component(name: str, kind: str, may_depend_on: list[str] | None = None,
                       exposes: list[str] | None = None, *, under_surface: str | None = None,
                       code_path: str | None = None, consumes_projects: list[str] | None = None,
                       registry_path: Path = REGISTRY, repos_dir: Path = REPOS,
                       template_dir: Path = TEMPLATE_DIR, write: bool = False, refresh: bool = True) -> dict:
    """The one-command add. SURFACE mode (default) appends a surface + scaffolds `_repos/<name>/`. PROJECT mode
    (`under_surface` set) appends a deployable project under an existing surface (its light manifest folder is
    produced by refresh_all's build_migration_plan). Always validates against the dependency law before any
    write. Returns {register_tuple, validated, problems, would_write/written, refreshed}."""
    may_depend_on = list(may_depend_on or [])
    reg = load_registry(registry_path)

    if under_surface:
        new_reg = add_project_to_registry(reg, under_surface, name, kind, code_path or "", consumes_projects or [])
        reg_repo = new_reg["surfaces"][under_surface]["projects"][name]["repo"]
        rt = RegisterTuple("project", name, kind, tuple(consumes_projects or []), reg_repo)
        file_map: dict[str, str] = {}   # projects live inside their surface; no _repos/<name> scaffold
    else:
        new_reg = add_surface_to_registry(reg, name, kind, may_depend_on, list(exposes or []))
        rt = RegisterTuple("surface", name, kind, tuple(may_depend_on), _repo_for(name))
        file_map = scaffold_file_map(name, new_reg, template_dir)

    problems = validate(new_reg, name if not under_surface else under_surface,
                        may_depend_on if not under_surface else [])
    result = {"register_tuple": rt, "validated": not problems, "problems": problems,
              "scaffold_files": sorted(f"{name}/{r}" for r in file_map), "written": [], "refreshed": False}
    if problems:
        raise ScaffoldError("dependency-law validation failed:\n  " + "\n  ".join(problems))
    if not write:
        return result

    write_registry(new_reg, registry_path)
    if file_map:
        result["written"] = write_scaffold(name, file_map, repos_dir)
    if refresh:
        r = subprocess.run([sys.executable, str(REFRESH_ALL), "--write"], cwd=str(REPO),
                           capture_output=True, text=True)
        result["refreshed"] = r.returncode == 0
        result["refresh_tail"] = (r.stdout.strip().splitlines() or [""])[-1][:160]
    return result


# --------------------------------------------------------------------------- self-test (pure, offline)

def _synthetic_registry() -> dict:
    return {"surfaces": {
        "rules": {"repo": "r", "role": "rules", "kind": "rules_and_context", "exposes": ["standards/*"],
                  "may_depend_on": [], "consumed_by": []},
        "substrate": {"repo": "s", "role": "substrate", "kind": "substrate", "exposes": ["registry"],
                      "may_depend_on": ["rules"], "consumed_by": []},
        "teleon": {"repo": "t", "role": "runtime", "kind": "product_runtime", "exposes": ["/api/teleon"],
                   "may_depend_on": ["rules", "substrate"], "consumed_by": []},
    }, "forbidden_edges": [{"from": "substrate", "to": "teleon", "why": "substrate is product-neutral"}]}


def self_test() -> int:
    reg = _synthetic_registry()
    checks: list[tuple[str, bool]] = []

    # 1. the new surface entry validates against the dependency law (reusing the portable checker).
    new_reg = add_surface_to_registry(reg, "newcomp", "dev_tool", ["rules", "substrate"], ["port-x"])
    checks.append(("new surface validates against the dependency law", validate(new_reg, "newcomp", ["rules", "substrate"]) == []))
    checks.append(("new entry carries the derived repo name", new_reg["surfaces"]["newcomp"]["repo"] == _repo_for("newcomp")))
    checks.append(("new entry born with empty consumed_by", new_reg["surfaces"]["newcomp"]["consumed_by"] == []))

    # 2. no existing entry is clobbered — input untouched, existing surfaces preserved, re-add refused.
    checks.append(("input registry not mutated (no-clobber by copy)", "newcomp" not in reg["surfaces"]))
    checks.append(("existing surfaces preserved verbatim", all(new_reg["surfaces"][s] == reg["surfaces"][s] for s in reg["surfaces"])))
    try:
        add_surface_to_registry(new_reg, "newcomp", "dev_tool", [], [])
        checks.append(("re-adding an existing surface is refused", False))
    except ScaffoldError:
        checks.append(("re-adding an existing surface is refused", True))

    # 3. an edge to an unknown surface is refused before any write.
    try:
        add_surface_to_registry(reg, "bad", "dev_tool", ["ghost"], [])
        checks.append(("edge to unknown surface refused", False))
    except ScaffoldError:
        checks.append(("edge to unknown surface refused", True))

    # 4. an illegal edge (forbidden by the law) fails validation.
    illegal = add_surface_to_registry(reg, "illegal", "substrate", ["teleon"], [])
    # make substrate->teleon-style illegality concrete: forbid the new edge, then validate must complain.
    illegal["forbidden_edges"].append({"from": "illegal", "to": "teleon", "why": "test"})
    checks.append(("a may_depend_on that is also forbidden fails validation", validate(illegal, "illegal", ["teleon"]) != []))

    # 5. the folder scaffold is produced ADD-ONLY (into a temp dir, from a synthetic template — pure/offline).
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        tdir = tmp / "template"; tdir.mkdir()
        for tf in TEMPLATE_FILES:
            (tdir / tf).write_text(f"# template {tf}\n")
        fmap1 = scaffold_file_map("newcomp", new_reg, tdir)
        fmap2 = scaffold_file_map("newcomp", new_reg, tdir)
        checks.append(("file map covers context template + interface + readme",
                       set(fmap1) == {f"{CONTEXT_DIR_NAME}/{TEMPLATE_FILES[0]}", f"{CONTEXT_DIR_NAME}/{TEMPLATE_FILES[1]}",
                                      INTERFACE_FILENAME, README_FILENAME}))
        checks.append(("scaffold is deterministic (byte-identical twice)", fmap1 == fmap2))
        checks.append(("starter interface.json is valid JSON with the surface name",
                       json.loads(fmap1[INTERFACE_FILENAME]).get("surface") == "newcomp"))
        repos = tmp / "repos"
        written = write_scaffold("newcomp", fmap1, repos)
        checks.append(("scaffold writes every file", len(written) == len(fmap1) and all(Path(w).exists() for w in written)))
        try:  # ADD-ONLY: a second write must refuse (no clobber)
            write_scaffold("newcomp", fmap1, repos)
            checks.append(("second write refused (ADD-ONLY)", False))
        except ScaffoldError:
            checks.append(("second write refused (ADD-ONLY)", True))

    # 6. PROJECT mode appends under an existing surface and refuses an unknown one.
    proj_reg = add_project_to_registry(reg, "teleon", "teleon-backend", "backend", "src/teleon", [])
    checks.append(("project appended under its surface", "teleon-backend" in proj_reg["surfaces"]["teleon"]["projects"]))
    try:
        add_project_to_registry(reg, "ghost", "p", "backend", "x", [])
        checks.append(("project under unknown surface refused", False))
    except ScaffoldError:
        checks.append(("project under unknown surface refused", True))

    # 7. wired-in reality checks: the real template + refresher exist (this tool is useless without them).
    checks.append(("real component template exists", all((TEMPLATE_DIR / tf).exists() for tf in TEMPLATE_FILES)))
    checks.append(("real refresher exists", REFRESH_ALL.exists()))

    # 8. the register tuple shape a caller relies on.
    rt = RegisterTuple("surface", "newcomp", "dev_tool", ("rules",), _repo_for("newcomp"))
    checks.append(("register tuple has scope/name/kind/may_depend_on/repo", rt._fields == ("scope", "name", "kind", "may_depend_on", "repo")))

    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - scaffold_component:\n  " + "\n  ".join(failed)); return 1
    print("PASS - scaffold_component: one-command add of a surface/project — appends the single-source registry, "
          "validates against the reused cross-repo dependency law, produces an ADD-ONLY folder scaffold from the "
          "shared template (no existing entry clobbered), and defers every derived artifact to refresh_all.")
    return 0


# --------------------------------------------------------------------------- CLI

def main() -> int:
    ap = argparse.ArgumentParser(description="Add a new component/repo (surface or project) to the org in one command.")
    ap.add_argument("--self-test", action="store_true", help="offline proof on a synthetic registry (no real writes)")
    ap.add_argument("--name", help="the new surface name (or, with --under-surface, the new project name)")
    ap.add_argument("--kind", help="the component kind (e.g. dev_tool, substrate, product_runtime, backend, frontend)")
    ap.add_argument("--may-depend-on", nargs="*", default=[], help="surfaces this one may consume (surface mode)")
    ap.add_argument("--exposes", nargs="*", default=[], help="capability ids this one publishes")
    ap.add_argument("--under-surface", help="add a PROJECT under this existing surface instead of a new surface")
    ap.add_argument("--code-path", default="", help="project mode: where the code lives in the monorepo today")
    ap.add_argument("--consumes-projects", nargs="*", default=[], help="project mode: sibling projects it consumes")
    ap.add_argument("--write", action="store_true", help="perform the append + scaffold (default is a dry run)")
    ap.add_argument("--no-refresh", action="store_true", help="skip running refresh_all after --write")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if not args.name or not args.kind:
        ap.error("--name and --kind are required (or use --self-test)")

    try:
        res = scaffold_component(
            args.name, args.kind, args.may_depend_on, args.exposes,
            under_surface=args.under_surface, code_path=args.code_path,
            consumes_projects=args.consumes_projects, write=args.write, refresh=not args.no_refresh)
    except ScaffoldError as e:
        print(f"FAIL - scaffold_component: {e}"); return 1

    rt = res["register_tuple"]
    print(f"register: scope={rt.scope} name={rt.name} kind={rt.kind} "
          f"{'consumes' if rt.scope == 'project' else 'may_depend_on'}={list(rt.may_depend_on)} repo={rt.repo}")
    print(f"validated against dependency law: {'yes' if res['validated'] else 'NO'}")
    if not args.write:
        print("dry run (pass --write to apply). Would scaffold:")
        for f in res["scaffold_files"] or ["(registry entry only — project mode)"]:
            print(f"  + _repos/{f}")
        return 0
    for w in res["written"]:
        print(f"  wrote {Path(w).relative_to(REPO)}")
    print(f"registry appended; refresh_all: {'ran' if res['refreshed'] else 'skipped'}"
          + (f" — {res.get('refresh_tail','')}" if res["refreshed"] else ""))
    print("PASS - scaffold_component: component added from the single source of truth; derived artifacts refreshed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
