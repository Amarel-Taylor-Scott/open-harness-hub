# Repository organization — the AI Done Right org

GitHub is **flat**: repos are all top-level, no folders or subgroups. We don't fight that — we make the flat
org navigable, multi-dimensional, and **reproducible from one manifest**. This is the standard for how the
org is structured and how to add to it.

## The single source

Everything below is described once in [`contracts/repo_org_manifest.json`](contracts/repo_org_manifest.json)
and applied by [`tools/apply_repo_org.py`](tools/apply_repo_org.py) — never hand-clicked in the GitHub UI.
Edit the manifest, run `--write`; `--check` reports drift; `--self-test` is offline.

## Naming

`aidoneright-<full-word-name>` — the org prefix + the surface/tool name, no abbreviations (the naming law).
The prefix makes the repos sort into visual clusters in the flat list.

## Categorization — three orthogonal property axes (better than one folder tree)

A folder forces one hierarchy; typed **custom properties** let you slice the same repos many ways. Filter the
repo list with `props.<axis>:<value>` (e.g. `props.layer:product`, `props.layer:library props.domain:ingestion`).

| Axis | Values | What it answers |
|---|---|---|
| `layer` | substrate · product · library · devkit · business · infra · meta | Where in the architecture it sits |
| `domain` | platform · runtime · governance · ecosystem · usage · brand · ingestion · integration · context · business · meta | What functional area it serves |
| `visibility-plan` | private · open-later · public | Intended visibility (all private today) |

Topics (`layer-*`) mirror `layer` for users who prefer the topic filter.

## Access — nested teams

GitHub Teams *do* nest (the one real hierarchy). `engineering` is the parent; child teams grant access to
their layer's repos: `products`, `libraries`, `platform` (substrate + devkit + infra + meta), `business`.
A repo joins a team automatically by its `layer` — defined in the manifest, applied by the tool.

## Cross-repo views

Use an org **Project (v2)** board for roadmap/status across repos (the "view across the tree" flat repos lack).

## Adding a new repo (the easy path)

1. **Scaffold from the template.** `aidoneright-dev-rules-context` is a GitHub *template repository* — click
   "Use this template" (or `gh repo create AIDoneRight/aidoneright-<name> --template AIDoneRight/aidoneright-dev-rules-context --private`). It comes with the `CLAUDE.md` template, the standards, and the shared-context structure.
2. **Register it.** Add the repo + its `layer`/`domain`/`visibility-plan` to `repo_org_manifest.json`, and add
   it as a surface in `contracts/surface-registry.json` if it participates in the edge graph.
3. **Apply structure.** `python3 tools/apply_repo_org.py --write` (properties + teams). 
4. **Vendor shared context.** `python3 tools/sync_shared_context.py --write` (rules/skills/agents into `.aidoneright/`).
5. **Regenerate edges.** `python3 ../edge-graph-generator/generate_repo_edges.py --write --propagate` (the repo's
   `AIDONERIGHT-UNIVERSE.md` + everyone's neighbour digests).

## The tools (all `--self-test`'d, offline, deterministic)

| Tool | Repo | Job |
|---|---|---|
| `apply_repo_org.py` | dev-rules-context | Org structure (properties, teams, template) from the manifest |
| `sync_shared_context.py` | dev-rules-context | Vendor rules/skills/agents into every repo's `.aidoneright/`, drift-gated |
| `generate_repo_edges.py` | edge-graph-generator | Generate `AIDONERIGHT-UNIVERSE.md` + `EDGES.md` from the surface registry |

Single source, generated projections, drift gates — the same law the whole org runs on. GitLab's subgroups
would give literal URL nesting; we get multi-axis categorization + nested teams + reproducibility instead,
and keep the GitHub ecosystem.
