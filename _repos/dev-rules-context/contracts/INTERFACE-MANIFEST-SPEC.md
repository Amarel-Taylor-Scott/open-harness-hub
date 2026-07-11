# Interface Manifest Spec — separate components, with flexible relationships

Each repo publishes one `interface.json` at its root: the **versioned contract** other repos bind to. This
is how the components stay *separate* (each owns its interface) while their *relationships* stay explicit,
versioned, and **checked** — a repo may consume only what a provider actually exposes, and only a provider
its dependency law allows. Generated + enforced by `edge-graph-generator/interface_manifests.py`.

Design goal: **most flexible as possible** — adding, swapping, or versioning a component is a data change
(a registry row + an interface field), never a code rewrite. Nothing about a relationship is hardcoded in
logic; every checker reads the manifests.

## Shape

```jsonc
{
  "surface": "teleon",                       // matches the registry key (single source)
  "repo": "aidoneright-teleon",
  "interface_version": "0.1.0",              // semver; version lives HERE, never in a name/id
  "exposes": [
    { "id": "/api/teleon", "kind": "api",        "stability": "stable",       "summary": "…" },
    { "id": "PurposeTask", "kind": "type",       "stability": "stable",       "summary": "…" },
    { "id": "runtime-selector", "kind": "capability", "stability": "experimental", "summary": "…" }
  ],
  "consumes": {
    // FLEXIBLE per relationship — pick the least-binding form that is still correct:
    "shared-backend-components": ["registry", "primitives"],          // simple list (whole-version)
    "openhubforai": { "capabilities": ["capabilitytask-spec"], "version": ">=0.1" },  // version RANGE
    "context-injection": { "capabilities": ["prompt-composer"], "optional": true }    // OPTIONAL: degrade, don't fail
  }
}
```

- **`exposes[].kind`** ∈ `api · type · capability · spec · event`. **`stability`** ∈
  `declared · experimental · stable · deprecated` — lets an interface evolve without breaking consumers.
- **`consumes[provider]`** is flexible: a plain **list** of capability ids, or an **object** with
  `capabilities`, an optional `version` **constraint** (exact `1.2.3`, range `>=1.0` / `^1.2` / `~1.2.0`,
  or any `*`), and an optional `optional: true` (a missing optional capability **degrades**, it does not
  break the relationship).

## The two consistency laws (checked)

1. **Consume ⊆ expose** — every consumed capability id is one the provider's `interface.json` actually
   `exposes`. You cannot depend on something that isn't published. (An `optional` consume is exempt — it is
   allowed to be absent.)
2. **Provider ∈ may_depend_on** — every consumed provider is in the surface's `may_depend_on` in
   `surface-registry.json`. The interface layer can never contradict the dependency law.

## Where flexibility lives (so you are never locked in)

- **Add a component** → a registry row + its `interface.json`. No consumer changes until it opts in.
- **Swap a provider** → point a `consumes` entry at a different surface that exposes the same capability id;
  a capability can be published by more than one provider (a provider *portfolio* with fallback).
- **Version an interface** → bump `interface_version`; consumers pin a **range**, not an exact build, so a
  compatible bump needs no consumer change.
- **Make a dependency soft** → `optional: true` — the relationship degrades gracefully when absent.
- **Change the delivery mechanism** (submodule / package / generated stubs) → an infra choice; the contract
  (`interface.json`) is identical regardless.

Regenerate + prove after any change:
```
python3 edge-graph-generator/interface_manifests.py --generate   # starter manifests for new surfaces
python3 edge-graph-generator/interface_manifests.py --check      # relationships sound?
python3 edge-graph-generator/generate_repo_edges.py --write       # refresh every EDGES.md + the graph
python3 edge-graph-generator/check_cross_repo_dependency_law.py    # the boundary law
```
