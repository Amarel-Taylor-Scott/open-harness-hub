# External Capability Catalog (C35)

Baltor's governed runtime is **stdlib-only** today — deterministic vector, stub LLM, SQLite. It imports zero
external repos. But the product depends on a long list of best-of-breed external capabilities (parsing,
retrieval, claim-graph memory, durable workflow, sandboxing, …). The **External Capability Catalog** is how we
pre-register those capabilities **behind ports** so the first real dependency cannot land without a card, an
I/O contract, a fallback, a license, and a health status.

> Baltor domain code depends on a **capability slot**, never on a vendor. Backend repos are swappable infra.

## The three manifests

| File | Purpose |
|---|---|
| `architecture/external_capability_catalog.json` | The catalog. One entry per capability slot; each carries the currently-wired adapter (a working stub), a candidate primary external repo, fallbacks, an I/O contract, contract proofs, license, and health. |
| `architecture/repo_health_policy.json` | When is an external repo still safe to adopt/keep? Health/adoption enums, monitored signals + thresholds, quarantine triggers, review cadence, invariants. |
| `architecture/repo_replacement_matrix.json` | Per slot: wired adapter → primary candidate → fallback/stub → contract tests → documented swap steps. This is the "the upstream repo died, now what" runbook, made into a failing check. |

The single in-code reader is `src/baltor/runtime/registry/capability_registry.py`
(`class CapabilityRegistry`, the declared owner in `architecture/runtime_ownership.json`).

## Builds ON the verified seed — no second source of truth

The catalog **mirrors** `data/backend-tools.yaml` (the web-verified tool seed). Its 13 capability keys
(`parser_manager`, `repo_codegraph`, `skills_manager`, `scraping_manager`, `api_manager`, `api_catalog`,
`mcp_gateway`, `durable_workflow_engine`, `claim_graph_memory`, `graph_db_substrate`, `hybrid_retrieval`,
`observability_evals`, `sandboxed_execution`) each become a slot, and the `flagged:` do-not-reintroduce block
is mirrored into `quarantined_providers`. The 13 keys and the flagged names are **read** from the YAML at proof
time (no PyYAML on this host — regex extraction), and drift between the YAML and the catalog is a failing
proof. Five further slots are earned from the self-evolving-agent research
(`research/external-tools/self-evolving-coding-agents.md`): `eval_harness`, `code_review`, `skill_memory`
(adoptable), plus `agent_runtime` (**foil** — never our runtime) and `self_improvement_research` (**reference**).

## A catalog entry

```json
{
  "capability_slot": "parser_manager",
  "adapter_id": "parser.stub@v1",          // currently WIRED (stdlib stub)
  "input_schema": "RawDocument",
  "output_schema": "DocumentTree",
  "fallback_adapters": ["parser.unstructured@v1"],
  "contract_proofs": ["check_capability_contract_examples", "check_provider_replacement_matrix"],
  "contract_example": "schemas/examples/parser_manager.example.json",
  "status": "candidate", "license": "MIT", "health_status": "healthy",
  "adapters": [ { "adapter_id": "parser.stub@v1", "role": "stub", "import_module": null, ... },
                { "adapter_id": "parser.docling@v1", "role": "primary", "import_module": "docling", ... } ]
}
```

Every **adoptable** slot (`active`/`candidate`) ships a **working stub** so the system runs with zero external
deps, plus a candidate primary and a fallback. `foil`/`reference` slots are records, never wired, and every
foil/reference adapter card must carry `do_not_adopt_as_runtime: true`.

## Status vocabulary

`active` (a working in-repo adapter is wired) · `candidate` (stub wired, real provider pre-registered) ·
`experimental` · `deprecated` · `quarantined` · `replaced` · `foil` (comparison only) · `reference` (validates
a pattern). Health: `healthy` · `watch` · `at_risk` · `decayed` · `archived` · `unverified`.

## Enforcement proofs (registered in the flywheel)

- `check_external_capability_catalog` — structure, 13-key coverage, self-evolving slots, foil notes, registry-owned.
- `check_repo_health_policy` — policy well-formed; every adapter health governed; **no active slot wired to a decayed/archived repo**.
- `check_provider_replacement_matrix` — matrix == catalog slots; every adoptable slot has primary + fallback/stub + a contract test.
- `check_no_uncataloged_github_repos` — AST import scan of the governed runtime; any 3rd-party import must be cataloged (stdlib-only today ⇒ passes; the first uncataloged `import docling` fails the build).
- `check_no_direct_external_imports` — a provider SDK may only be imported inside an approved adapter path (`src/baltor/adapters`, the LLM gateways).
- `check_capability_contract_examples` — every slot has an I/O contract; referenced examples in `schemas/examples/` are valid and grounded in real slots+adapters.
- `check_flagged_tools_not_reintroduced` — flagged seed names never appear as an adopted adapter; `quarantined_providers` mirrors the seed.

See `repo-replaceability.md` for the swap runbook and `archive/legacy/docs/adr/0004-external-capability-catalog-and-repo-replaceability.md`.
