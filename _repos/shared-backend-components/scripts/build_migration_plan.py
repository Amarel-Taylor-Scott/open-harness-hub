#!/usr/bin/env python3
"""scripts/build_migration_plan — turn the surface/project registry into a COMPLETE, safe monorepo→multirepo
migration plan + the per-project package manifests, so splitting each component is one command and nobody
has to reverse-engineer the layout (important as the team grows).

Best-practice approach (no broken working tree):
- Each project's code stays in the monorepo and WORKS until split; extraction uses `git subtree split
  --prefix=<code_path>` which produces a branch with that subtree's full history, ready to push to a new
  repo. No pre-move, no broken imports.
- Every repo installs the shared **aidoneright-devkit** (standards + contracts + gates) rather than copying.
- Per-project manifests (pyproject.toml / package.json) declare dependencies explicitly.

Emits: _repos/dev-rules-context/MIGRATION-PLAN.md + migration_plan.json, and a starter manifest per project.
The project list + code paths come from the registry (single source), never hand-typed here.
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
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
# Post-_repos-migration this module physically lives at _repos/shared-backend-components/scripts/, so REPO is
# `shared-backend-components` and the repos root is its PARENT (`_repos/`), not `REPO/_repos`. This mirrors
# exactly what check_org_freshness's in-memory regenerator sets (bmp.REPOS = repo_root.parent), so a standalone
# `--write` produces byte-identical output to what the org-freshness gate expects.
REPOS = REPO.parent
REGISTRY = REPOS / "dev-rules-context" / "contracts" / "surface-registry.json"
PLAN_MD = REPOS / "dev-rules-context" / "MIGRATION-PLAN.md"
PLAN_JSON = _resource("data") / "dev-intel" / "migration" / "migration_plan.json"
SHARED_PACKAGE = "aidoneright-devkit"   # the one package every repo installs (standards + contracts + gates)


def load_registry() -> dict:
    return json.loads(REGISTRY.read_text())


def collect_projects(reg: dict) -> list[dict]:
    """Flatten the two-level registry (surface → projects) into a list of deployable repos with their code
    path, kind, and dependencies (the shared devkit + any sibling backend it consumes)."""
    out = []
    for surface, spec in reg["surfaces"].items():
        projects = spec.get("projects")
        if projects:
            for pname, p in projects.items():
                out.append({
                    "project": pname, "surface": surface, "kind": p.get("kind"),
                    "repo": p.get("repo"), "code_path": p.get("code_path"),
                    "depends_on_projects": p.get("consumes_projects", []),
                    "depends_on_shared": [SHARED_PACKAGE],
                    "extractable": bool(p.get("code_path") and (_resource(str(p.get("code_path")).split(" ")[0])).exists()),
                })
        else:
            # a surface with no sub-projects is itself one repo (its context/tools).
            out.append({"project": surface, "surface": surface, "kind": spec.get("kind"),
                        "repo": spec.get("repo"), "code_path": f"_repos/{surface}",
                        "depends_on_projects": [], "depends_on_shared": [SHARED_PACKAGE],
                        "extractable": (REPOS / surface).exists()})
    return out


def extraction_commands(proj: dict) -> list[str]:
    """The safe git-subtree extraction for one project — a branch with that subtree's history, push-ready."""
    cp = str(proj.get("code_path") or "").split(" ")[0]
    if not proj["extractable"] or not cp:
        return [f"# {proj['project']}: code_path {proj.get('code_path')!r} not yet a clean subdir — extract/create it first"]
    branch = f"split/{proj['repo']}"
    return [
        f"git subtree split --prefix={cp} -b {branch}      # history-preserving extract of {cp}",
        f"# create empty GitHub repo {proj['repo']} on the new org account, then:",
        f"git push git@github.com:<org>/{proj['repo']}.git {branch}:main",
    ]


def build_plan() -> dict:
    reg = load_registry()
    projects = collect_projects(reg)
    for p in projects:
        p["extraction"] = extraction_commands(p)
    # order: shared devkit first, then substrate/microservices, then backends, then frontends/clients.
    rank = {"rules_and_context": 0, "substrate": 1, "microservice": 1, "open_spec": 2, "backend": 3,
            "dev_tool": 3, "meta_tool": 3, "context": 3, "product_runtime": 3, "product_applied": 3,
            "frontend": 4, "client": 4, "parent_brand": 5}
    projects.sort(key=lambda p: (rank.get(p.get("kind", ""), 3), p["project"]))
    return {"shared_package": SHARED_PACKAGE, "repo_count": len(projects), "projects": projects}


def project_manifest(proj: dict) -> tuple[str, str]:
    """Return (filename, content) for the project's package manifest — pyproject.toml for python, package.json
    for a frontend/client. Declares the shared devkit + sibling deps so the component is self-describing."""
    deps = proj["depends_on_shared"] + proj["depends_on_projects"]
    if proj.get("kind") in ("frontend", "client"):
        pkg = {"name": proj["repo"], "private": True, "version": "0.1.0",
               "description": f"{proj['surface']} {proj['kind']}",
               "dependencies": {d: "workspace:*" for d in deps}}
        return "package.json", json.dumps(pkg, indent=2) + "\n"
    toml = (f'[project]\nname = "{proj["repo"]}"\nversion = "0.1.0"\n'
            f'description = "{proj["surface"]} {proj.get("kind","")}"\nrequires-python = ">=3.11"\n'
            f'dependencies = [\n' + "".join(f'  "{d}",\n' for d in deps) + ']\n\n'
            f'# code_path in the monorepo (extract via git subtree at split): {proj.get("code_path")}\n')
    return "pyproject.toml", toml


def write_manifests(plan: dict) -> int:
    n = 0
    for p in plan["projects"]:
        folder = REPOS / p["project"]
        if not folder.is_dir():
            # nested project (e.g. teleon-backend) has no folder yet — create a light one under its surface.
            folder = REPOS / p["surface"] / "projects" / p["project"]
            folder.mkdir(parents=True, exist_ok=True)
        fname, content = project_manifest(p)
        path = folder / fname
        if not path.exists():
            path.write_text(content); n += 1
    return n


def render_md(plan: dict) -> str:
    lines = ["# Migration plan — monorepo → managed multi-repo", "",
             f"{plan['repo_count']} repos. Every repo installs the shared **`{plan['shared_package']}`** "
             "(standards + contracts + gates) instead of copying them. Splitting is history-preserving "
             "(`git subtree split`) so the working monorepo never breaks — do it repo-by-repo, in order.", "",
             "## Order + commands", ""]
    for p in plan["projects"]:
        lines.append(f"### {p['repo']}  ({p['surface']} · {p.get('kind','')})")
        lines.append(f"- code: `{p.get('code_path')}`  ·  depends on: {', '.join(p['depends_on_shared'] + p['depends_on_projects'])}")
        lines.append("```bash")
        lines += p["extraction"]
        lines.append("```")
        lines.append("")
    lines += ["## After each extract", "1. In the new repo, `pip install -e` (or workspace-link) the shared "
              f"`{plan['shared_package']}`.", "2. Run the inherited gates (`run_proofs`) — green before you push.",
              "3. Rewrite any `src.<x>` imports to the package name; leave a compat shim during transition.", ""]
    return "\n".join(lines) + "\n"


def self_test() -> int:
    reg = {"surfaces": {
        "dev-rules-context": {"repo": "r", "kind": "rules_and_context", "may_depend_on": []},
        "teleon": {"repo": "t", "kind": "product_runtime", "may_depend_on": ["dev-rules-context"],
                   "projects": {"teleon-backend": {"kind": "backend", "code_path": "src/teleon", "repo": "aidoneright-teleon-backend", "consumes_projects": []},
                                "teleon-frontend": {"kind": "frontend", "code_path": "web/teleon", "repo": "aidoneright-teleon-frontend", "consumes_projects": ["teleon-backend"]}}},
    }}
    projs = collect_projects(reg)
    checks = [
        ("two-level flatten yields nested projects", {p["project"] for p in projs} == {"dev-rules-context", "teleon-backend", "teleon-frontend"}),
        ("frontend depends on its backend", any(p["project"] == "teleon-frontend" and "teleon-backend" in p["depends_on_projects"] for p in projs)),
        ("every project depends on the shared devkit", all(SHARED_PACKAGE in p["depends_on_shared"] for p in projs)),
        ("frontend manifest is package.json", project_manifest(next(p for p in projs if p["kind"] == "frontend"))[0] == "package.json"),
        ("backend manifest is pyproject.toml", project_manifest(next(p for p in projs if p["kind"] == "backend"))[0] == "pyproject.toml"),
        ("extraction uses git subtree split", any("subtree split" in c for c in extraction_commands({"project": "x", "repo": "r", "code_path": "src/teleon", "extractable": True}))),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - build_migration_plan:\n  " + "\n  ".join(failed)); return 1
    print("PASS - build_migration_plan: two-level surface→project flatten; per-project manifests (pyproject/"
          "package.json) declare the shared devkit + sibling deps; history-preserving git-subtree extraction order.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Build the monorepo→multirepo migration plan + manifests.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--write", action="store_true", help="write MIGRATION-PLAN.md + json + per-project manifests")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    plan = build_plan()
    manifests = 0
    if args.write:
        PLAN_MD.write_text(render_md(plan))
        PLAN_JSON.parent.mkdir(parents=True, exist_ok=True)
        PLAN_JSON.write_text(json.dumps(plan, indent=2))
        manifests = write_manifests(plan)
    print(f"{plan['repo_count']} repos planned; shared package = {plan['shared_package']}; "
          f"{sum(1 for p in plan['projects'] if p['extractable'])} extractable now")
    if args.write:
        print(f"  wrote MIGRATION-PLAN.md + {manifests} project manifests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
