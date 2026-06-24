# Registry federation & the registry ontology (owner vision, 2026-06-23)

> The endgame is not workflow automation. It is **the canonical machine-readable knowledge
> graph of all executable capability** — a federation of registries, each behind one universal
> interface (the "Bloomberg Terminal of computation"). This doc records that frame and the
> **sequencing law** that keeps it honest. The machine-readable source is
> `architecture/registry_ontology.json` — read it, don't restate it.

## Three layers, three files (each with its own anti-drift check)

| Layer | File | What it answers | Check |
|---|---|---|---|
| Brand / release policy | `architecture/candidate_open_hubs.json` | which Open*Hubs exist / are candidates, and when they open (owner-gated) | `check_candidate_open_hubs.py` |
| System-facing hub map | `architecture/hub_profiles.json` | for each of the 28 hubs, the **types** of rules / context / modules pullable from it | `check_hub_profiles.py` |
| Registry-of-registries | `architecture/registry_ontology.json` | the ~35 load-bearing **knowledge registries** beneath the hubs, each → real backing module + status | `check_registry_ontology.py` |

A hub exposes one or more registries (OpenToolsHub exposes the component + transformation registries; OpenRoutingHub exposes the model + provider + cost registries). The ontology is the **finer** layer.

## The headline: the federation is largely already built

The owner proposed 35 registries (capability, component, model, provider, prompt, failure,
transformation, equivalence, …, agent-behavior, semantic-ontology, observability). Grounded
against disk: **32 of 35 already have a real backing module** (`10 live + 22 partial`); only
**3 are true gaps** (`agent_behavior`, `semantic_ontology`, `observability`). The repo already
carries ~180 `architecture/*.json` registries + 48 `src/teleon/` modules + 45 `schemas/` dirs.

So the work is **not** "build 35 catalogs." It is:

1. **Declare ONE universal interface** — the `Registry<T>` verbs (search/lookup/benchmark/score/
   health/relationships/history/mutate/simulate/explain) + the `RegistryObject` base shape. Every
   verb already has a backing primitive in-repo (named in the ontology); what's missing is a single
   declared contract all ~180 registries conform to. This is the highest-leverage move — it turns
   the existing sprawl into one governed pattern (the `makeHub(config)` idea, generalized).
2. **Fill the ~6 highest-leverage gaps**, flywheel-first (see below).

## Sequencing law (the honest constraint — `registry_ontology.json#sequencing_law`)

Warrant: capability-gap framework + the multi-model board verdict ("ship one live capability to a
real buyer") + the universal-compiler memory ("win one vertical first; don't build
discovery-at-scale / formal-IR yet").

- **Schema-all-now, fill-gap-first.** Declaring the ontology is cheap and makes the scale legible.
  *Filling* a registry is expensive and only pays when the descent/compiler **prunes** on it.
- **A registry nothing reads is dead weight.** Stand one up when a real pipeline needs it, proven
  on the **starter vertical** (HealthLynked provider directory) — not speculatively.
- **Moat = the flywheel** that fills + scores these registries from real runs, **not** the registry
  count. 35 empty catalogs is not a moat.
- **Universal interface before more registries.**
- **First gaps to close** (owner-flagged moat): `failure` (7), `equivalence` (11),
  `semantic_ontology` (20); then `cost_prediction` forecasting (15) and `agent_behavior` (14) when
  agents-as-customers lands.

## Owner-gated (not decided here)

- The `*.aidoneright.com` subdomain federation is **recorded as proposed only** — each needs owner
  domain/trademark clearance (same gate as the Open*Hub `.io` sites). Never claimed.
- This work does **not** change the family brand count (`products.js` drives that, computed by
  `check_ai_done_right_surface_family.py`). Adding registries is orthogonal to the 22-hub surface.
- Note: `products.js` and the policy files now both use `OpenEnvironmentHub` — the `OpenEnvHub`
  abbreviation is retired (owner directive 2026-06-24: no abbreviations in names). The public brand
  surface (`products.js`, computed by `check_ai_done_right_surface_family.py`) is a curated SUBSET of
  the full federation (`architecture/registry_ontology.json`, 103 registries); the newest candidates
  aren't on the public brand surface yet, so the public family count differs from the federation
  registry count. Both are COMPUTED from their sources — never hand-typed.
