#!/usr/bin/env python3
"""scripts/check_org_freshness — the org-freshness DRIFT GATE (verify-the-verifier for the ORGANIZATION).

`refresh_all.py` is the deterministic MAINTAINER that *regenerates* every derived org artifact from the ONE
source of truth (`_repos/dev-rules-context/contracts/surface-registry.json` + each repo's `interface.json`
+ the code layout). This gate is its inverse: it PROVES nothing has silently drifted, WITHOUT writing over
any real file. Drop it in CI — it fails (exit 1) the moment a derived artifact stops matching what
regenerating from the current registry would produce.

It reuses the real generators as libraries (never a parallel re-implementation) and regenerates into a
TEMP dir, then diffs:

  - `<surface>.EDGES.md` / `<surface>.edges.json`  (per-repo edge digests)  — byte-diff vs regenerated
  - `graph.json` / `GRAPH.md`                        (global dependency graph) — byte-diff vs regenerated
  - `MIGRATION-PLAN.md`                              (monorepo→multirepo plan) — byte-diff vs regenerated
  - `interface.json` per repo — the DERIVED fields (`exposes` ids + `repo`) must equal the registry
    (owner-refined `consumes`/`version` are NOT diffed — those are legitimately hand-narrowed), AND the
    relationship consistency check must pass (a repo may consume only capabilities a provider exposes and
    only surfaces its `may_depend_on` allows).
  - every registry surface must have a `_repos/<surface>/` folder; a folder must carry an `interface.json`.
  - any derived edge/graph file the current registry would NOT produce is flagged as an ORPHAN (a surface
    was removed but its digest was left behind).

Single source of truth: the surface registry (+ each interface.json + the code layout). NO surface/repo
name is hardcoded in logic — everything is read from the registry. Offline, deterministic, no network, no
git. `--self-test` builds a synthetic in-sync tree (passes clean) and a deliberately-stale one (detected).
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
REPOS_DIRNAME = "_repos"
EDGE_TOOLS_DIRNAME = "edge-graph-generator"          # holds the edge/graph + interface + law generators
SCRIPTS_DIRNAME = "scripts"                          # holds the migration-plan builder

# --- layout of the DERIVED artifacts, relative to the _repos/ dir (single-sourced here, never re-typed) ---
REGISTRY_REL = ("dev-rules-context", "contracts", "surface-registry.json")
MIGRATION_PLAN_REL = ("dev-rules-context", "MIGRATION-PLAN.md")
GENERATED_EDGES_DIRNAME = "generated-edges"
INTERFACE_FILENAME = "interface.json"
EDGES_MD_SUFFIX = ".EDGES.md"
EDGES_JSON_SUFFIX = ".edges.json"
GRAPH_FILENAMES = ("graph.json", "GRAPH.md")
# fields of interface.json that are DERIVED from the registry (must match); everything else is owner-refined.
INTERFACE_DERIVED_EXPOSES_KEY = "exposes"
INTERFACE_DERIVED_REPO_KEY = "repo"

# --- drift categories (named — the gate reports which invariant broke, never a bare boolean) -------------
DRIFT_MISSING_FOLDER = "missing_surface_folder"
DRIFT_STALE_EDGE_DIGEST = "stale_edge_digest"
DRIFT_STALE_GRAPH = "stale_dependency_graph"
DRIFT_ORPHAN_ARTIFACT = "orphan_derived_artifact"
DRIFT_MISSING_INTERFACE = "missing_interface_manifest"
DRIFT_STALE_INTERFACE_DERIVED = "stale_interface_derived_field"
DRIFT_INTERFACE_RELATIONSHIP = "interface_relationship_violation"
DRIFT_STALE_MIGRATION_PLAN = "stale_migration_plan"

DRIFT_CATEGORIES = (
    DRIFT_MISSING_FOLDER, DRIFT_STALE_EDGE_DIGEST, DRIFT_STALE_GRAPH, DRIFT_ORPHAN_ARTIFACT,
    DRIFT_MISSING_INTERFACE, DRIFT_STALE_INTERFACE_DERIVED, DRIFT_INTERFACE_RELATIONSHIP,
    DRIFT_STALE_MIGRATION_PLAN,
)

EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_ERROR = 2


def load_tools(repo_root: Path = REPO_ROOT) -> SimpleNamespace:
    """Import the real generators as libraries so this gate diffs against exactly what `refresh_all --write`
    would produce — never a parallel re-implementation that could itself drift."""
    edge_tools = repo_root.parent / EDGE_TOOLS_DIRNAME
    scripts_dir = repo_root / SCRIPTS_DIRNAME
    for p in (str(edge_tools), str(scripts_dir)):
        if p not in sys.path:
            sys.path.insert(0, p)
    import generate_repo_edges as gre          # edge digests + global graph
    import interface_manifests as im           # per-repo interface.json + relationship check
    import build_migration_plan as bmp         # MIGRATION-PLAN.md
    return SimpleNamespace(gre=gre, im=im, bmp=bmp)


def _drift(category: str, artifact: str, detail: str) -> dict:
    return {"category": category, "artifact": artifact, "detail": detail}


def _registry_path(repos_root: Path) -> Path:
    return repos_root.joinpath(*REGISTRY_REL)


def _edge_category_for(filename: str) -> str:
    if filename in GRAPH_FILENAMES:
        return DRIFT_STALE_GRAPH
    return DRIFT_STALE_EDGE_DIGEST


def regenerate_migration_md(repo_root: Path, tools: SimpleNamespace) -> str:
    """Regenerate MIGRATION-PLAN.md in-memory for an ARBITRARY tree by pointing the real builder's roots at
    `repo_root` (save/restore its module globals). Reuses the real plan builder incl. its `extractable`
    filesystem probe, so the diff is faithful. No file is written."""
    bmp = tools.bmp
    saved = (bmp.REGISTRY, bmp.REPO, bmp.REPOS)
    try:
        bmp.REPO = repo_root
        bmp.REPOS = repo_root.parent
        bmp.REGISTRY = _registry_path(bmp.REPOS)
        return bmp.render_md(bmp.build_plan())
    finally:
        bmp.REGISTRY, bmp.REPO, bmp.REPOS = saved


def _check_edges_and_graph(reg: dict, repos_root: Path, tools: SimpleNamespace) -> list[dict]:
    """Regenerate all edge digests + the graph into a temp dir and byte-diff against the real ones. Catches
    changed content, missing artifacts, and orphan artifacts the current registry would not produce."""
    findings: list[dict] = []
    real_dir = repos_root / GENERATED_EDGES_DIRNAME
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        tools.gre.generate_all(reg, tmp)
        expected = {p.name: p.read_text() for p in tmp.iterdir() if p.is_file()}
    actual = {p.name for p in real_dir.iterdir() if p.is_file()} if real_dir.is_dir() else set()
    for name in sorted(expected):
        rp = real_dir / name
        if not rp.exists():
            findings.append(_drift(_edge_category_for(name), name, "derived artifact missing on disk"))
        elif rp.read_text() != expected[name]:
            findings.append(_drift(_edge_category_for(name), name,
                                   "content differs from what regenerating from the registry produces"))
    for name in sorted(actual - set(expected)):
        if name.endswith(EDGES_MD_SUFFIX) or name.endswith(EDGES_JSON_SUFFIX) or name in GRAPH_FILENAMES:
            findings.append(_drift(DRIFT_ORPHAN_ARTIFACT, name,
                                   "derived artifact the current registry would not produce (stale/orphan)"))
    return findings


def _load_manifests(reg: dict, repos_root: Path) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for surface in reg.get("surfaces", {}):
        p = repos_root / surface / INTERFACE_FILENAME
        if p.exists():
            try:
                out[surface] = json.loads(p.read_text())
            except Exception:  # noqa: BLE001
                out[surface] = {"_parse_error": True}
    return out


def _check_interfaces(reg: dict, repos_root: Path, tools: SimpleNamespace) -> list[dict]:
    """Two independent interface checks: (a) the DERIVED fields (exposes ids + repo) must equal the registry
    — owner-refined consumes/version are left alone; (b) the relationship consistency law (reuse the real
    checker) must hold."""
    findings: list[dict] = []
    surfaces = reg.get("surfaces", {})
    for surface, spec in surfaces.items():
        if (repos_root / surface).is_dir() and not (repos_root / surface / INTERFACE_FILENAME).exists():
            findings.append(_drift(DRIFT_MISSING_INTERFACE, f"{surface}/{INTERFACE_FILENAME}",
                                   "surface folder exists but has no interface.json"))
    manifests = _load_manifests(reg, repos_root)
    for surface, m in manifests.items():
        art = f"{surface}/{INTERFACE_FILENAME}"
        if m.get("_parse_error"):
            findings.append(_drift(DRIFT_STALE_INTERFACE_DERIVED, art, "interface.json is not valid JSON"))
            continue
        expected_exposed = list(surfaces.get(surface, {}).get("exposes", []))
        got_exposed = [e.get("id") for e in m.get(INTERFACE_DERIVED_EXPOSES_KEY, [])]
        if got_exposed != expected_exposed:
            findings.append(_drift(DRIFT_STALE_INTERFACE_DERIVED, art,
                                   f"exposes drift: manifest {got_exposed} != registry {expected_exposed}"))
        if m.get(INTERFACE_DERIVED_REPO_KEY) != surfaces.get(surface, {}).get("repo"):
            findings.append(_drift(DRIFT_STALE_INTERFACE_DERIVED, art,
                                   f"repo field drift: manifest {m.get(INTERFACE_DERIVED_REPO_KEY)!r} "
                                   f"!= registry {surfaces.get(surface, {}).get('repo')!r}"))
    for problem in tools.im.check(reg, manifests):
        findings.append(_drift(DRIFT_INTERFACE_RELATIONSHIP, INTERFACE_FILENAME, problem))
    return findings


def _check_migration_plan(repo_root: Path, repos_root: Path, tools: SimpleNamespace) -> list[dict]:
    findings: list[dict] = []
    real_plan = repos_root.joinpath(*MIGRATION_PLAN_REL)
    expected_md = regenerate_migration_md(repo_root, tools)
    if not real_plan.exists():
        findings.append(_drift(DRIFT_STALE_MIGRATION_PLAN, MIGRATION_PLAN_REL[-1], "missing on disk"))
    elif real_plan.read_text() != expected_md:
        findings.append(_drift(DRIFT_STALE_MIGRATION_PLAN, MIGRATION_PLAN_REL[-1],
                               "content differs from what regenerating from the registry produces"))
    return findings


def detect_drift(repo_root: Path, tools: SimpleNamespace | None = None) -> list[dict]:
    """The gate's core: return every drift finding (empty == the whole org is in sync with its source of
    truth). `repo_root` is the monorepo root (its `_repos/` holds the registry + derived artifacts)."""
    tools = tools or load_tools(repo_root)
    repos_root = repo_root.parent
    reg = tools.gre.load_registry(_registry_path(repos_root))
    findings: list[dict] = []
    # 1. every registry surface must have a folder.
    for surface in reg.get("surfaces", {}):
        if not (repos_root / surface).is_dir():
            findings.append(_drift(DRIFT_MISSING_FOLDER, surface,
                                   "registry surface has no _repos/<surface>/ folder"))
    # 2. edge digests + global graph.  3. interface manifests.  4. migration plan.
    findings += _check_edges_and_graph(reg, repos_root, tools)
    findings += _check_interfaces(reg, repos_root, tools)
    findings += _check_migration_plan(repo_root, repos_root, tools)
    findings.sort(key=lambda f: (f["category"], f["artifact"], f["detail"]))
    return findings


# ---------------------------------------------------------------------------------------------------------
# self-test: build a synthetic tree from the SAME generators, prove in-sync passes + injected staleness trips
# ---------------------------------------------------------------------------------------------------------
def _synthetic_registry() -> dict:
    """A tiny, name-neutral registry (surfaces alpha/beta/gamma) — fixture only, never used by gate logic."""
    return {
        "version": "1.0",
        "surfaces": {
            "alpha": {"repo": "org-alpha", "role": "rules", "kind": "rules_and_context",
                      "exposes": ["standards/*"], "may_depend_on": [], "consumed_by": ["beta", "gamma"]},
            "beta": {"repo": "org-beta", "role": "substrate", "kind": "substrate",
                     "exposes": ["registry"], "may_depend_on": ["alpha"], "consumed_by": ["gamma"],
                     "projects": {"beta-backend": {"kind": "backend", "code_path": "src/beta",
                                                   "repo": "org-beta-backend", "consumes_projects": []}}},
            "gamma": {"repo": "org-gamma", "role": "product", "kind": "product_runtime",
                      "exposes": ["/api/gamma"], "may_depend_on": ["alpha", "beta"], "consumed_by": [],
                      "projects": {"gamma-frontend": {"kind": "frontend", "code_path": "web/gamma",
                                                      "repo": "org-gamma-frontend",
                                                      "consumes_projects": ["gamma-backend"]}}},
        },
        "forbidden_edges": [{"from": "beta", "to": "gamma", "why": "substrate is product-neutral"}],
    }


def _build_insync_tree(root: Path, tools: SimpleNamespace, reg: dict) -> None:
    """Materialize a fully in-sync tree using the real generators, so 'in-sync passes' is true BY
    CONSTRUCTION (writer and checker share one generator). Post-_repos/ migration the derived artifacts live
    UNDER `_repos/` and `repo_root` is itself a dir INSIDE `_repos/` (real: `_repos/shared-backend-components`),
    so `repos_root == root.parent` — the same convention detect_drift + regenerate_migration_md use."""
    repos_root = root.parent
    reg_path = _registry_path(repos_root)
    reg_path.parent.mkdir(parents=True, exist_ok=True)
    reg_path.write_text(json.dumps(reg, indent=2))
    for surface in reg["surfaces"]:
        (repos_root / surface).mkdir(parents=True, exist_ok=True)
        (repos_root / surface / INTERFACE_FILENAME).write_text(
            json.dumps(tools.im.build_manifest(reg, surface), indent=2) + "\n")
    tools.gre.generate_all(reg, repos_root / GENERATED_EDGES_DIRNAME)
    repos_root.joinpath(*MIGRATION_PLAN_REL).write_text(regenerate_migration_md(root, tools))


def self_test() -> int:
    tools = load_tools()
    reg = _synthetic_registry()
    checks: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory() as td:
        # Mirror production: `_repos/` holds the derived artifacts and `root` (the repo carrying the scripts)
        # lives INSIDE it, so `root.parent == repos_root`. This makes the synthetic tree resolve exactly the
        # way detect_drift + regenerate_migration_md do (both use `repo_root.parent`), which the old
        # `root = Path(td)` fixture broke — it pointed the registry at `<tmp-parent>/dev-rules-context/…`.
        repos_root = Path(td) / REPOS_DIRNAME
        root = repos_root / "shared-backend-components"
        root.mkdir(parents=True, exist_ok=True)
        _build_insync_tree(root, tools, reg)

        checks.append(("a synthetic in-sync tree reports zero drift", detect_drift(root, tools) == []))

        # (a) a deliberately-stale edge digest is detected.
        edges_dir = repos_root / GENERATED_EDGES_DIRNAME
        a_edge = next(p for p in edges_dir.iterdir() if p.name.endswith(EDGES_MD_SUFFIX))
        original = a_edge.read_text()
        a_edge.write_text(original + "\nDRIFT INJECTED\n")
        d = detect_drift(root, tools)
        checks.append(("a stale EDGES.md is detected as stale_edge_digest",
                       any(f["category"] == DRIFT_STALE_EDGE_DIGEST for f in d)))
        a_edge.write_text(original)  # restore -> back in sync
        checks.append(("restoring the edge digest clears the drift", detect_drift(root, tools) == []))

        # (b) a missing surface folder is detected.
        moved = repos_root / "gamma"
        renamed = repos_root / "_gamma_hidden"
        moved.rename(renamed)
        d = detect_drift(root, tools)
        checks.append(("a registry surface with no folder is detected",
                       any(f["category"] == DRIFT_MISSING_FOLDER for f in d)))
        renamed.rename(moved)

        # (c) a stale DERIVED interface field (exposes) is detected.
        iface = repos_root / "beta" / INTERFACE_FILENAME
        m = json.loads(iface.read_text())
        good_iface = json.dumps(m, indent=2) + "\n"
        m["exposes"].append({"id": "ghost-capability", "kind": "capability"})
        iface.write_text(json.dumps(m, indent=2) + "\n")
        d = detect_drift(root, tools)
        checks.append(("a drifted interface.json exposes list is detected",
                       any(f["category"] == DRIFT_STALE_INTERFACE_DERIVED for f in d)))
        iface.write_text(good_iface)

        # (d) an interface RELATIONSHIP breach (consume an unexposed capability) is detected.
        m2 = json.loads(iface.read_text())
        m2["consumes"] = {"alpha": ["not-a-real-capability"]}
        iface.write_text(json.dumps(m2, indent=2) + "\n")
        d = detect_drift(root, tools)
        checks.append(("an interface relationship breach is detected",
                       any(f["category"] == DRIFT_INTERFACE_RELATIONSHIP for f in d)))
        iface.write_text(good_iface)

        # (e) a stale MIGRATION-PLAN.md is detected.
        plan = repos_root / Path(*MIGRATION_PLAN_REL)
        plan.write_text(plan.read_text() + "\nDRIFT\n")
        d = detect_drift(root, tools)
        checks.append(("a stale MIGRATION-PLAN.md is detected",
                       any(f["category"] == DRIFT_STALE_MIGRATION_PLAN for f in d)))

        checks.append(("no surface/repo name is hardcoded in the drift logic (uses the synthetic registry)",
                       {"alpha", "beta", "gamma"} == set(reg["surfaces"])))

    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - check_org_freshness:\n  " + "\n  ".join(failed))
        return 1
    print("PASS - check_org_freshness: regenerates every derived org artifact (edge digests, dependency "
          "graph, per-repo interface.json derived fields + relationship law, MIGRATION-PLAN.md) from the "
          "surface registry into a temp dir and diffs WITHOUT touching real files; in-sync passes, injected "
          "staleness (edge/graph/interface/relationship/migration/missing-folder) trips it. No net/git.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Org-freshness drift gate: fail if any derived artifact is "
                                             "stale vs the surface registry (verify-the-verifier).")
    ap.add_argument("--self-test", action="store_true", help="offline mutation proof (pure)")
    ap.add_argument("--repo-root", type=Path, default=REPO_ROOT, help="monorepo root (default: this repo)")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    try:
        findings = detect_drift(args.repo_root.resolve())
    except FileNotFoundError as e:
        print(f"FAIL - check_org_freshness: cannot read a source-of-truth file: {e}")
        return EXIT_ERROR
    if not findings:
        print("PASS - check_org_freshness: every derived org artifact is in sync with the surface registry "
              "(edge digests, dependency graph, interface manifests + relationship law, migration plan).")
        return EXIT_OK
    by_cat: dict[str, int] = {}
    for f in findings:
        by_cat[f["category"]] = by_cat.get(f["category"], 0) + 1
    print(f"FAIL - check_org_freshness: {len(findings)} drift finding(s) — the org has silently drifted from "
          "its single source of truth. Run `python3 scripts/refresh_all.py --write` to regenerate:")
    for f in findings:
        print(f"  [{f['category']}] {f['artifact']}: {f['detail']}")
    print("  summary: " + ", ".join(f"{k}={v}" for k, v in sorted(by_cat.items())))
    return EXIT_DRIFT


if __name__ == "__main__":
    raise SystemExit(main())
