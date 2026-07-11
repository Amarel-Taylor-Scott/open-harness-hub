#!/usr/bin/env python3
"""tools/generate_repo_edges — the edge-graph-generator: turn the surface-registry into per-repo EDGE
DIGESTS + the global repo dependency graph.

The point: a Claude Code session working in repo X should load X's OWN context (its blackbox) plus a small
EDGES digest — the published interfaces of the repos X depends on and the ones that depend on X — and NOTHING
of their internals. This tool generates exactly that from the single source of truth
(contracts/surface-registry.json + each surface's published `exposes`), so cross-repo awareness stays in sync
without any repo reading through another.

Per surface S it emits:
  - <out>/<S>.edges.json  : machine digest {depends_on:[{surface,exposes,role}], consumed_by:[...], forbidden:[...]}
  - <out>/<S>.EDGES.md    : the compact agent-facing brief a session drops into repo S reads
And globally:
  - <out>/graph.json      : nodes + directed edges (may_depend_on)
  - <out>/GRAPH.md        : the dependency graph as a mermaid diagram + adjacency list

Offline, deterministic, `--self-test`-able. Reads contracts only, never any repo's source.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _resolve_registry() -> Path:
    """Robust registry lookup — works whether this tool lives in edge-graph-generator/ (registry is in the
    sibling dev-rules-context/) or inside dev-rules-context/tools/. No hardcoded path that breaks on move."""
    for c in (HERE.parent / "dev-rules-context" / "contracts" / "surface-registry.json",
              HERE.parent / "contracts" / "surface-registry.json",
              HERE / "contracts" / "surface-registry.json"):
        if c.exists():
            return c
    return HERE.parent / "dev-rules-context" / "contracts" / "surface-registry.json"


DEFAULT_REGISTRY = _resolve_registry()

# Display-only truncation lengths for human/agent-facing role summaries. The FULL text always lives in the
# registry (single source) — these only bound what is echoed into a digest, so drift here is cosmetic.
ROLE_SUMMARY_CHARS = 120   # a neighbor's role, shown inline in this repo's depends_on entry
ROLE_BRIEF_CHARS = 200     # this repo's own role, shown at the top of its EDGES.md
# mermaid node ids cannot contain hyphens; surface ids may. This is the documented substitution.
_MERMAID_HYPHEN = "-"
_MERMAID_SUB = "_"

# ---- AIDONERIGHT-UNIVERSE: the self-contained per-repo "whole org + how to interface" file ----
# EDGES.md (above) is the terse neighbor digest. The UNIVERSE file is its SUPERSET: every surface in the org,
# each capability's one-line meaning INLINED from the registry's capability_catalog (so the file stands alone
# with only this repo open), and — the part EDGES.md lacks — HOW to interface with each surface, derived from
# its kind. Same single source (the registry); a second generated VIEW, never hand-maintained (multi-path law:
# a new output path, the existing EDGES.md output is untouched and stays byte-identical).
UNIVERSE_FILENAME = "AIDONERIGHT-UNIVERSE.md"
SEAM_ENV_TMPL = "OH_SEAM_{S}_BASE"
# kind -> (interface-mode label, how-to-interface sentence). The TRUE distinction a single-repo agent needs:
# you do not call a library over HTTP, you do not import a product's source, you do not "run" a context repo —
# each kind is reached its own way. `<surface>`/`<SURFACE>` are interpolated to the concrete surface key.
KIND_INTERFACE = {
    "rules_and_context":   ("inherit",  "Inherited standards + shared context — present in every repo, read as law; not a running service."),
    "substrate":           ("seam",     "Call the substrate registry seam same-origin at `/registry/` (cloud base `OH_SEAM_REGISTRY_BASE`, a local port in dev)."),
    "open_spec":           ("spec",     "Consume the open CapabilityTask spec + conformance tests; its backend also answers a same-origin seam."),
    "product_runtime":     ("seam",     "Call its HTTP seam same-origin (`/api/<surface>/…`); cloud base `OH_SEAM_<SURFACE>_BASE`, a local port in dev."),
    "product_applied":     ("seam",     "Call its HTTP seam same-origin (`/api/<surface>/…`); cloud base `OH_SEAM_<SURFACE>_BASE`, a local port in dev."),
    "product_usage_layer": ("seam",     "Call its HTTP seam same-origin (`/api/<surface>/…`); cloud base `OH_SEAM_<SURFACE>_BASE`, a local port in dev."),
    "dev_tool":            ("port",     "Consume as a capability behind a stable port (a library/adapter) — no HTTP seam; you invoke the port, never its host."),
    "context":             ("read",     "Read as grounding context/memory — never imported as code, never a running service."),
    "parent_brand":        ("site",     "The portfolio site; it references other surfaces' PUBLIC interfaces for display/routing only."),
    "meta_tool":           ("generate", "Consume its GENERATED output (this very file, EDGES.md, the dependency graph) — never its source."),
}
# kind -> the org layer topic (matches the GitHub repo `layer-*` topics), so the universe map is self-describing.
KIND_LAYER = {
    "rules_and_context": "devkit", "substrate": "substrate", "open_spec": "product",
    "product_runtime": "product", "product_applied": "product", "product_usage_layer": "product",
    "parent_brand": "product", "dev_tool": "library", "meta_tool": "library", "context": "business",
}


def _seam(spec: dict) -> str | None:
    """The same-origin HTTP seam a surface answers on, or None if it isn't reached over HTTP. Derived from the
    registry's `exposes` (first path-like entry) with the documented substrate convention — never hand-typed."""
    for e in spec.get("exposes", []):
        if isinstance(e, str) and e.startswith("/"):
            return e.rstrip("/") + "/"
    return "/registry/" if spec.get("kind") == "substrate" else None


def _interface(spec: dict) -> dict:
    """The (mode, how-to, seam, seam_env) an agent uses to interface with this surface — derived from its kind."""
    key = spec.get("_key", "")
    mode, how = KIND_INTERFACE.get(spec.get("kind", ""), ("consume", "Consume via its published interface only."))
    how = how.replace("<surface>", key).replace("<SURFACE>", key.upper().replace(_MERMAID_HYPHEN, _MERMAID_SUB))
    seam = _seam(spec)
    return {"mode": mode, "how": how, "seam": seam,
            "seam_env": SEAM_ENV_TMPL.format(S=key.upper().replace(_MERMAID_HYPHEN, _MERMAID_SUB)) if seam else None}


def _exposes_with_summaries(reg: dict, spec: dict) -> list[dict]:
    """Each exposed capability id paired with its one-line meaning from the registry's capability_catalog, so the
    generated file is self-contained (no lookup back into the registry needed to understand a capability)."""
    cat = reg.get("capability_catalog", {})
    return [{"id": c, "summary": cat.get(c, "")} for c in spec.get("exposes", [])]


def _short(text: str, n: int) -> str:
    """Truncate to <= n chars on a WORD boundary with an ellipsis — a clean cell in the universe table (never
    a mid-word cut). The full role always lives in the registry + this file's per-neighbor section."""
    t = " ".join(text.split())
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0].rstrip(",;:.") + "…"


def universe_digest(reg: dict, surface: str) -> dict:
    """The full, self-contained universe VIEW from `surface`'s point of view: identity + how others reach it, the
    surfaces it may consume (with their capabilities' meanings + how to interface), who consumes it, forbidden
    edges, and a compact map of EVERY surface. All from the single-source registry."""
    surfaces = reg.get("surfaces", {})
    spec = dict(surfaces[surface]); spec["_key"] = surface
    forbidden = {(e["from"], e["to"]): e.get("why", "") for e in reg.get("forbidden_edges", [])}
    consume = []
    for dep in spec.get("may_depend_on", []):
        d = dict(surfaces.get(dep, {})); d["_key"] = dep
        consume.append({"surface": dep, "repo": d.get("repo"), "kind": d.get("kind", ""),
                        "role": d.get("role", ""), "interface": _interface(d),
                        "exposes": _exposes_with_summaries(reg, d)})
    consumers = sorted({n for n, s in surfaces.items() if surface in s.get("may_depend_on", [])}
                       | set(spec.get("consumed_by", [])))
    universe = []
    for n in sorted(surfaces):
        s = dict(surfaces[n]); s["_key"] = n
        iface = _interface(s)
        universe.append({"surface": n, "repo": s.get("repo"), "kind": s.get("kind", ""),
                         "layer": KIND_LAYER.get(s.get("kind", ""), "—"),
                         "interface_mode": iface["mode"], "seam": iface["seam"],
                         "role_short": _short(s.get("role", ""), ROLE_SUMMARY_CHARS)})
    return {
        "record_type": "repo_universe", "surface": surface, "repo": spec.get("repo"),
        "kind": spec.get("kind", ""), "layer": KIND_LAYER.get(spec.get("kind", ""), "—"),
        "role": spec.get("role", ""), "interface": _interface(spec),
        "exposes": _exposes_with_summaries(reg, spec),
        "consume": consume,
        "consumed_by": [{"surface": c, "repo": surfaces.get(c, {}).get("repo")} for c in consumers],
        "forbidden_from_me": [{"to": to, "why": why} for (frm, to), why in forbidden.items() if frm == surface],
        "universe": universe,
        "law": reg.get("law", ""), "consumption_rule": reg.get("consumption_rule", ""),
        "rule": "Consume a neighbor ONLY via its published interface listed here — never read/import its source.",
    }


def render_universe_md(dig: dict) -> str:
    S = dig["surface"]
    L = [f"# AIDONERIGHT-UNIVERSE — how `{S}` interfaces with the rest of the AI Done Right org", "",
         "> Generated from `contracts/surface-registry.json` by the edge-graph-generator — **single source, do",
         "> not hand-edit** (regenerate after any registry change). **Self-contained:** with only this repo open,",
         "> it tells you every surface in the org, what each exposes, and HOW to reach it.", "",
         f"> _{dig['rule']}_", ""]
    itf = dig["interface"]
    L += [f"## This repo — `{S}` (`{dig.get('repo','')}`)",
          f"- **Layer:** {dig['layer']} · **Kind:** {dig['kind']}",
          f"- **Role:** {dig['role']}",
          f"- **How others interface with you:** {itf['how']}"
          + (f" Seam: `{itf['seam']}`." if itf['seam'] else "")]
    if dig["exposes"]:
        L += ["", "**What you expose** (your published interface — keep it stable):"]
        L += [f"- `{e['id']}`" + (f" — {e['summary']}" if e['summary'] else "") for e in dig["exposes"]]
    L += ["", "## What you may consume — and exactly how"]
    if dig["consume"]:
        for c in dig["consume"]:
            ci = c["interface"]
            L += ["", f"### `{c['surface']}` (`{c.get('repo','')}`) — {c['kind']}",
                  f"- **How to interface:** {ci['how']}" + (f" Seam: `{ci['seam']}`." if ci['seam'] else ""),
                  f"- **Its role:** {c['role']}"]
            if c["exposes"]:
                L.append("- **You may use:**")
                L += [f"    - `{e['id']}`" + (f" — {e['summary']}" if e['summary'] else "") for e in c["exposes"]]
    else:
        L.append("- (nothing — this repo consumes no other surface)")
    L += ["", "## Who consumes you (keep your interface stable for them)"]
    L += ([f"- `{c['surface']}` (`{c.get('repo','')}`)" for c in dig["consumed_by"]]
          or ["- (no downstream consumers yet)"])
    if dig["forbidden_from_me"]:
        L += ["", "## Forbidden edges (the boundary law — never do these)"]
        L += [f"- **→ {f['to']}** — {f['why']}" for f in dig["forbidden_from_me"]]
    L += ["", "## The whole universe (every surface — what it is, how to reach it)", "",
          "| Surface | Repo | Layer | Interface | One-line role |", "|---|---|---|---|---|"]
    for u in dig["universe"]:
        seam = f"seam `{u['seam']}`" if u["seam"] else u["interface_mode"]
        me = " **← you**" if u["surface"] == S else ""
        role_cell = u["role_short"].replace("|", "\\|")   # escape table-breaking pipes (out of the f-string)
        L.append(f"| `{u['surface']}`{me} | {u.get('repo','')} | {u['layer']} | {seam} | {role_cell} |")
    L += ["", "## How interfacing works (the rules that keep it safe)",
          f"- **Consumption rule:** {dig['consumption_rule']}",
          f"- **Dependency law:** {dig['law']}",
          "- **Seams are same-origin:** call `/api/<surface>/…` (or `/registry/` for the substrate), never a",
          "  hardcoded host; the cloud base is `OH_SEAM_<SURFACE>_BASE`, a local port in dev.",
          "- **Libraries and context are not seams:** a `dev_tool` is invoked behind a port; a `context` repo is",
          "  read as grounding — neither is called over HTTP nor imported as source.", ""]
    return "\n".join(L) + "\n"


def load_registry(path: Path) -> dict:
    return json.loads(path.read_text())


def edge_digest(reg: dict, surface: str) -> dict:
    surfaces = reg.get("surfaces", {})
    spec = surfaces[surface]
    forbidden = {(e["from"], e["to"]): e.get("why", "") for e in reg.get("forbidden_edges", [])}
    depends_on = []
    for dep in spec.get("may_depend_on", []):
        d = surfaces.get(dep, {})
        depends_on.append({"surface": dep, "repo": d.get("repo"), "exposes": d.get("exposes", []),
                           "role": d.get("role", "")[:ROLE_SUMMARY_CHARS]})
    # who consumes me = anyone whose may_depend_on includes me (authoritative) unioned with my consumed_by hint.
    consumers = sorted({n for n, s in surfaces.items() if surface in s.get("may_depend_on", [])}
                       | set(spec.get("consumed_by", [])))
    forbidden_from_me = [{"to": to, "why": why} for (frm, to), why in forbidden.items() if frm == surface]
    return {
        "record_type": "repo_edge_digest",
        "surface": surface, "repo": spec.get("repo"), "role": spec.get("role", ""),
        "exposes": spec.get("exposes", []),
        "depends_on": depends_on,          # what I may consume (their PUBLISHED edges, not internals)
        "consumed_by": consumers,          # who depends on me (keep my interface stable for them)
        "forbidden_from_me": forbidden_from_me,
        "rule": "Consume a neighbor ONLY via its exposed interface listed here — never read/import its source.",
    }


def render_edges_md(dig: dict) -> str:
    lines = [f"# Edges for `{dig['surface']}` ({dig.get('repo','')})", "",
             "> Generated by the edge-graph-generator from `contracts/surface-registry.json`. This is the ONLY",
             "> cross-repo context a session in this repo needs — the neighbors' **published edges**, not their",
             "> internals. Work inside this repo's own context (its blackbox) + this file.", "",
             f"**This repo's role:** {dig['role'][:ROLE_BRIEF_CHARS]}", "",
             f"**This repo exposes:** {', '.join(dig['exposes']) or '—'}", "",
             "## You may consume (via their published interface only)"]
    if dig["depends_on"]:
        for d in dig["depends_on"]:
            lines.append(f"- **{d['surface']}** (`{d.get('repo','')}`) — exposes: {', '.join(d['exposes']) or '—'}")
    else:
        lines.append("- (nothing — this repo depends on no other surface)")
    lines += ["", "## Who consumes you (keep these interfaces stable)",
              "- " + (", ".join(dig["consumed_by"]) or "(no downstream consumers yet)"), ""]
    if dig["forbidden_from_me"]:
        lines += ["## Forbidden (never depend on these — the boundary law)"]
        for f in dig["forbidden_from_me"]:
            lines.append(f"- **{f['to']}** — {f['why']}")
        lines.append("")
    lines.append("_" + dig["rule"] + "_")
    return "\n".join(lines) + "\n"


def build_graph(reg: dict) -> dict:
    surfaces = reg.get("surfaces", {})
    nodes = [{"id": n, "kind": s.get("kind", ""), "repo": s.get("repo")} for n, s in surfaces.items()]
    edges = [{"from": n, "to": dep} for n, s in surfaces.items() for dep in s.get("may_depend_on", [])]
    return {"record_type": "repo_dependency_graph", "nodes": nodes, "edges": edges,
            "surface_count": len(nodes), "edge_count": len(edges)}


def render_graph_md(graph: dict) -> str:
    lines = ["# Repo-to-repo dependency graph", "",
             f"{graph['surface_count']} surfaces, {graph['edge_count']} dependency edges. Direction: `A --> B`",
             "means A may consume B's published interface.", "", "```mermaid", "graph TD"]
    for e in graph["edges"]:
        lines.append(f"  {e['from'].replace(_MERMAID_HYPHEN, _MERMAID_SUB)} --> "
                     f"{e['to'].replace(_MERMAID_HYPHEN, _MERMAID_SUB)}")
    lines += ["```", "", "## Adjacency (who each repo may consume)"]
    adj: dict[str, list[str]] = {}
    for e in graph["edges"]:
        adj.setdefault(e["from"], []).append(e["to"])
    for n in sorted({node["id"] for node in graph["nodes"]}):
        lines.append(f"- **{n}** → {', '.join(sorted(adj.get(n, []))) or '(none)'}")
    return "\n".join(lines) + "\n"


def generate_all(reg: dict, outdir: Path) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    written = []
    for surface in reg.get("surfaces", {}):
        dig = edge_digest(reg, surface)
        (outdir / f"{surface}.edges.json").write_text(json.dumps(dig, indent=2))
        (outdir / f"{surface}.EDGES.md").write_text(render_edges_md(dig))
        udig = universe_digest(reg, surface)
        (outdir / f"{surface}.universe.json").write_text(json.dumps(udig, indent=2))
        (outdir / f"{surface}.{UNIVERSE_FILENAME}").write_text(render_universe_md(udig))
        written.append(surface)
    graph = build_graph(reg)
    (outdir / "graph.json").write_text(json.dumps(graph, indent=2))
    (outdir / "GRAPH.md").write_text(render_graph_md(graph))
    return {"surfaces": written, "graph": graph}


def propagate_to_repos(reg: dict, outdir: Path, repos_root: Path) -> list[str]:
    """Copy each surface's freshly-generated `<S>.EDGES.md` into its repo folder as `<repos_root>/<S>/EDGES.md`
    — the per-repo digest a session actually opens. The surface key IS the folder name; only folders that exist
    are written (skip-missing keeps this safe in a partial mirror). This is the mechanism behind the operating
    rule 'regenerate every repo's EDGES.md after a registry change so no digest goes stale' — single source
    (the registry) → every repo's edge brief, no hand-maintained second copy. Mirror-only: at split time each
    repo is standalone and this is a no-op (no siblings), so it stays off by default."""
    propagated = []
    for surface in reg.get("surfaces", {}):
        dest = repos_root / surface
        src = outdir / f"{surface}.EDGES.md"
        usrc = outdir / f"{surface}.{UNIVERSE_FILENAME}"
        if dest.is_dir() and src.is_file():
            (dest / "EDGES.md").write_text(src.read_text())
            if usrc.is_file():                                  # the self-contained whole-org view
                (dest / UNIVERSE_FILENAME).write_text(usrc.read_text())
            propagated.append(surface)
    return propagated


def self_test() -> int:
    reg = {"surfaces": {
        "rules": {"repo": "r", "role": "rules", "kind": "rules", "exposes": ["standards"], "may_depend_on": []},
        "substrate": {"repo": "s", "role": "substrate", "kind": "substrate", "exposes": ["registry"], "may_depend_on": ["rules"]},
        "teleon": {"repo": "t", "role": "runtime", "kind": "product_runtime", "exposes": ["/api/teleon"], "may_depend_on": ["rules", "substrate"]},
        "baltor": {"repo": "b", "role": "applied", "kind": "product_applied", "exposes": ["/api/baltor"], "may_depend_on": ["rules", "substrate", "teleon"], "consumed_by": []},
    }, "forbidden_edges": [{"from": "teleon", "to": "baltor", "why": "infra not product-specific"}]}
    checks = []
    dig = edge_digest(reg, "baltor")
    checks.append(("baltor depends_on lists teleon+substrate+rules", {d["surface"] for d in dig["depends_on"]} == {"teleon", "substrate", "rules"}))
    checks.append(("baltor digest carries teleon's exposes, not internals", any(d["surface"] == "teleon" and d["exposes"] == ["/api/teleon"] for d in dig["depends_on"])))
    tdig = edge_digest(reg, "teleon")
    checks.append(("teleon consumed_by includes baltor (derived)", "baltor" in tdig["consumed_by"]))
    checks.append(("teleon forbidden_from_me lists baltor", any(f["to"] == "baltor" for f in tdig["forbidden_from_me"])))
    g = build_graph(reg)
    checks.append(("graph has baltor->teleon edge", {"from": "baltor", "to": "teleon"} in g["edges"]))
    checks.append(("edges md renders + names the rule", "published interface" in render_edges_md(dig)))
    checks.append(("graph md renders mermaid", "```mermaid" in render_graph_md(g)))
    # --- AIDONERIGHT-UNIVERSE: the self-contained whole-org view ---
    reg_u = {**reg, "capability_catalog": {"/api/teleon": "the runtime API", "registry": "the component registry"}}
    ud = universe_digest(reg_u, "baltor")
    checks.append(("universe lists EVERY surface, not just neighbors", {u["surface"] for u in ud["universe"]} == set(reg_u["surfaces"])))
    checks.append(("universe inlines a consumed capability's meaning (self-contained)",
                   any(e["id"] == "/api/teleon" and e["summary"] == "the runtime API"
                       for c in ud["consume"] if c["surface"] == "teleon" for e in c["exposes"])))
    checks.append(("universe derives interface mode from kind (product -> seam)", ud["interface"]["mode"] == "seam"))
    checks.append(("universe derives a seam path from exposes", ud["interface"]["seam"] == "/api/baltor/"))
    subs = next(u for u in ud["universe"] if u["surface"] == "substrate")
    checks.append(("universe gives the substrate its /registry/ seam", subs["seam"] == "/registry/"))
    checks.append(("universe md renders the whole-org table + rules", "The whole universe" in render_universe_md(ud)
                   and "Dependency law" in render_universe_md(ud)))
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - generate_repo_edges:\n  " + "\n  ".join(failed)); return 1
    print("PASS - generate_repo_edges: per-repo edge digests (a repo sees neighbors' EXPOSES, never internals) "
          "+ consumed_by derived from the graph + forbidden edges + the global mermaid dependency graph.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate per-repo edge digests + the repo dependency graph.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    ap.add_argument("--out", type=Path, default=HERE.parent / "generated-edges")
    ap.add_argument("--write", action="store_true", help="write the digests + graph to --out")
    ap.add_argument("--propagate", action="store_true",
                    help="also copy each <S>.EDGES.md into its sibling repo folder <_repos>/<S>/EDGES.md "
                         "(the local monorepo mirror; no-op once repos are split standalone)")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    reg = load_registry(args.registry)
    if args.write:
        res = generate_all(reg, args.out)
        print(f"generated edge digests for {len(res['surfaces'])} surfaces + graph "
              f"({res['graph']['edge_count']} edges) -> {args.out}")
        if args.propagate:
            # repos_root = the dir holding every surface folder = registry's <_repos>/dev-rules-context/contracts → up 2
            repos_root = args.registry.resolve().parents[2]
            prop = propagate_to_repos(reg, args.out, repos_root)
            print(f"propagated EDGES.md into {len(prop)} repo folder(s) under {repos_root}")
    else:
        g = build_graph(reg)
        print(f"{g['surface_count']} surfaces, {g['edge_count']} edges (dry run — pass --write)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
