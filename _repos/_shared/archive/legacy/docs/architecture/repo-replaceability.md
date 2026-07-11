# Repo Replaceability (C35)

The goal: **any external repo behind a capability can be swapped without touching domain code** — because
domain code depends on a capability slot's I/O contract, not on the vendor. This doc is the operational side of
the [External Capability Catalog](external-capability-catalog.md).

## Why replaceability is a first-class concern

External repos decay: they get archived (Kuzu, Oct 2025), relicense to something incompatible (AGPL/SSPL),
pivot away from the capability (Marqo → ecommerce), or turn out to be hallucinated upstream-list entries
(Synapse AI). When that happens we must be able to **swap the adapter and keep the slot's contract + proofs
green** — not rewrite the pipeline.

## The swap runbook (per slot)

`architecture/repo_replacement_matrix.json` records, for every slot:

```
wired  →  primary candidate  →  fallback/stub  →  contract tests  →  swap_steps
```

To replace a provider:

1. **License-gate** the candidate (the matrix flags AGPL/SSPL slots that need a decision first).
2. Implement the adapter under an **approved adapter path** (`src/baltor/adapters/**`, or the LLM gateways for
   model providers). This is the *only* place a provider SDK may be imported
   (`check_no_direct_external_imports`).
3. Add the provider package to its adapter card's `import_module` so it's cataloged
   (`check_no_uncataloged_github_repos` will otherwise fail on the first import).
4. Keep the slot's **I/O contract** identical (the `schemas/examples/*.json` example must still hold).
5. Flip the slot's `adapter_id` to the new adapter. The stub stays in the catalog as the always-available
   fallback that keeps the demo offline/no-pip.
6. Re-run the slot's `contract_proofs` + the flywheel.

## Health → action

`architecture/repo_health_policy.json` turns repo decay into governed transitions:

| Signal | Action |
|---|---|
| `last_commit_age_days` > 365 | `at_risk` |
| open critical security advisory | `at_risk` |
| relicense to restrictive | `quarantine` |
| repository archived | `quarantine` |
| capability pivot | `decayed` |
| provenance unverifiable | `quarantine` |

**Invariant (enforced):** an `active`/`candidate` slot may never be wired to a `decayed`/`archived` adapter,
and a flagged/quarantined provider may never be an adopted (primary/fallback/stub) adapter — only a record in
`quarantined_providers`, a `foil`, or a `reference`.

## Today's reality: stdlib-only, every slot stubbed

Nothing external is imported yet. Every adoptable slot is wired to an in-repo stub
(`parser.stub@v1`, `vector.deterministic_local@v1`, `durable.sqlite_store@v1`, `eval.flywheel@v1`, …). The
catalog is the **pre-registration** layer: the first real dependency cannot land without a card + contract +
fallback + license + health. That is what keeps "swap a repo" cheap and "add a repo" governed.
