# aidoneright-edge-graph-generator

A META DEV TOOL in the **AI Done Right** multi-repo org. It reads the single source of truth — the surface
registry + each repo's published interface — and **generates** the repo-to-repo edge context and dependency
graph. The point: a session working in repo X loads X's own context plus a small **EDGES digest** (the
published interfaces of the repos X depends on and the ones that depend on X) and **nothing of their
internals**. Every repo stays **edge-aware, not everything-aware**, and the awareness stays in sync without
any repo reading through another.

It reads **contracts only, never any repo's source**.

## What this repo is

It exposes, as its published interface:

- **per-repo-edge-digest** — for each surface S: `<out>/S.EDGES.md` (the agent-facing brief) +
  `<out>/S.edges.json` (the machine digest: `depends_on`, `consumed_by`, `forbidden`).
- **repo-dependency-graph** — `<out>/graph.json` (nodes + directed `may_depend_on` edges) and
  `<out>/GRAPH.md` (a mermaid diagram + adjacency list).
- **surface-registry-validator** — checks the registry itself (unknown edges, forbidden-vs-allowed
  contradictions, cycles).
- **interface-manifest-validator** — checks each repo's declared `consumes` against the registry: every
  consumed capability is one the provider actually exposes, and every consumed provider is allowed by the
  dependency law.

## The three scripts

All three are offline, deterministic, and `--self-test`-able. `generate_repo_edges.py` and
`check_cross_repo_dependency_law.py` default their registry path to a sibling `contracts/` directory, so
**from this repo you must pass the registry path explicitly** to the shared source of truth in
`../dev-rules-context/contracts/surface-registry.json`; `interface_manifests.py` resolves that shared
registry directly (no `--registry` flag).

### `generate_repo_edges.py` — generate the digests + graph

```bash
# prove it (mutation/determinism self-test)
python3 generate_repo_edges.py --self-test

# generate every surface's EDGES digest + the global graph from the shared registry
python3 generate_repo_edges.py \
  --registry ../dev-rules-context/contracts/surface-registry.json \
  --out ../generated-edges --write
```

Writes `<S>.EDGES.md` + `<S>.edges.json` per surface, plus `graph.json` + `GRAPH.md`. Each repo's committed
`EDGES.md` is this generator's output for that surface — regenerate after any registry change so no digest
goes stale.

### `check_cross_repo_dependency_law.py` — enforce the boundary

```bash
# prove it (self-test)
python3 check_cross_repo_dependency_law.py --self-test

# validate the whole registry (unknown edges, forbidden-vs-allowed contradictions, cycles)
python3 check_cross_repo_dependency_law.py \
  --registry ../dev-rules-context/contracts/surface-registry.json

# validate one repo's declared consumes (forbidden / undeclared cross-repo dependency)
python3 check_cross_repo_dependency_law.py \
  --registry ../dev-rules-context/contracts/surface-registry.json \
  --surface scraping --consumes api-endpoint-wrappers dev-rules-context
```

The dependency law it enforces (from the registry): direction is preserved across repos — Baltor → Teleon →
OpenHubForAI, never the reverse; every surface may consume the substrate and inherit `dev-rules-context`; a
surface references another **only** through its published `interface.json`, never its source. This checker
is what makes the boundary a proof, not prose — wire it into each repo's CI.

### `interface_manifests.py` — generate + check the interface manifests

Makes every repo's `interface.json` first-class, versioned, and consistency-checked (the
`interface-manifest-validator` capability). It resolves the shared registry directly — no `--registry` flag.

```bash
# prove it (mutation/determinism self-test)
python3 interface_manifests.py --self-test

# write a starter interface.json for any surface missing one (never clobbers an owner-refined manifest)
python3 interface_manifests.py --generate

# check every manifest: valid shape + semver, every consumed capability is one the provider EXPOSES,
# and every consumed provider is in the surface's may_depend_on (agrees with the dependency law)
python3 interface_manifests.py --check
```

## How it fits

Dependency direction is fixed by `../dev-rules-context/contracts/surface-registry.json`:

- **This repo may consume:** `dev-rules-context` only — specifically `contracts/surface-registry.json` and
  each surface's published interface. Contracts only, never any repo's source.
- **This repo is consumed by:** every surface — `aidoneright`, `teleon`, `baltor`, `aidevobserver`,
  `shared-backend-components`, `openhubforai`, `api-endpoint-wrappers`, `scraping`, `context-injection`,
  `business-context`. Its output (each repo's `EDGES.md`) is what makes "edge-aware, not everything-aware"
  real, so keep the digest/graph format and the checker stable and byte-deterministic.

## Layout

- `CLAUDE.md` — the agent operating manual (filled from the org template; inherits the 8 standards).
- `EDGES.md` — this repo's own cross-repo contract (itself a product of this generator).
- `generate_repo_edges.py` — the digest + graph generator.
- `check_cross_repo_dependency_law.py` — the portable boundary checker.
- `interface_manifests.py` — generate + check each repo's versioned `interface.json` (the interface-manifest-validator).
- `context/` — per-component context, added as the tool grows.
- `README.md` — this file.

Inherited standards, the shared glossary/config, and the portable checkers live in the sibling
`../dev-rules-context/` repo — this repo does not re-declare them. The registry this tool reads is the
single source of truth in that sibling repo.

## How to work in it

1. Read `../dev-rules-context/standards/README.md`, then `CLAUDE.md`, then `EDGES.md`.
2. The registry is the single source of truth — never hand-maintain an edge, count, or `exposes` list the
   generator can compute from it. A registry change lives in `dev-rules-context`, not here.
3. After any registry change, regenerate every repo's `EDGES.md` (`generate_repo_edges.py ... --write`) so
   no digest goes stale.
4. Every new output field or invariant ships a `--self-test` mutation gate and stays byte-deterministic.
5. Carry a warrant for every change — the whole org consumes this tool's output, so a format change is high
   blast radius.
