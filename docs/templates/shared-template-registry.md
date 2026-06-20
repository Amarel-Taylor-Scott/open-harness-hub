# Shared Template Registry (internal) — canonical object shell + schema mixins

**Status:** core built + proven (`scripts/check_shared_template_registry.py`, flywheel-registered). **Internal
only** — `OpenTemplatesHub.io` is a *possible future* public surface, NOT launched. Reuses the existing
`templates/` tree + `scripts/{check_template_catalog,generate_from_template,scaffold_pipeline_from_task}` — this
adds the canonical schema-object shell those lacked, not a second template framework.

> **SHARED TEMPLATE REGISTRY CLAUSE.** Templates are not only infrastructure starters. The shared template
> system also includes standardized **schema object templates**, **schema mixins**, **canonical object shells**,
> I/O-contract templates, command/event/error envelope templates, inference-preference templates, data-resource
> templates, API/UI templates, worker/runtime templates, and PurposeTask templates. **Templates generate
> starting shapes; harnesses prove generated outputs work; generated outputs are CANDIDATE until validated,
> redteamed, registered, and promoted.**

## The canonical object shell (the centrepiece)
`templates/schema-objects/canonical_object_shell.json` — every major artifact composes from one 14-section
shell so no object invents its own status/visibility/provenance/receipt shape:

```
identity · scope · contracts · payload_or_ref · provenance · lineage · policy · security ·
visibility · lifecycle · status · telemetry · relationships · receipts
```

Composed from **15 standardized mixins** (`templates/schema-objects/mixins/`): identity, scope, tenant_project,
provenance, lineage, policy, security, visibility, lifecycle, status, telemetry, relationships, receipts,
source_handles, content_hash. Runtime branches on **numeric codes** (`status_code`, `visibility_code`,
edge-types — `architecture/template_{status,visibility,edge_type}_codes.json`), never display labels.

Reusable across: `ContextArtifact · SkillArtifact · ToolArtifact · HarnessArtifact · TemplateArtifact ·
PurposeTask · WorkerApp · DataResource · ModelInvocationReceipt` (`architecture/schema_object_templates.json`).

## Boundary (template vs the rest)
- **Shared Template Registry** = reusable **starting shapes**.
- OpenContextHub = context · OpenSkillsHub = know-how · OpenToolsHub = execution · **OpenHarnessHub = proof**.
- A schema object template lives in **templates**; a test for that schema lives in **harnesses**; a tool that
  validates schemas lives in **tools**; a skill teaching schema design lives in **skills**; a context artifact
  using the schema lives in **context**.

## Contracts + instantiator
- `schemas/templates/{TemplateArtifact,SchemaObjectTemplate}.v1` (registered in `contract_registry.json`).
- `src/teleon/templates/instantiator.py` (Teleon-owned — scaffolding is a runtime concern; dependency-law
  clean): `compose_object_shell()` builds a shell object (default **candidate** status, internal visibility,
  computed `content_hash`, `security.secret_refs` only — **no raw keys**); `instantiate_schema_object()` renders
  a CANDIDATE instance + a `TemplateInstantiationReceipt` to a target dir, **refusing overwrite + path
  traversal**, marking `is_active=False, is_truth=False`.

## Built vs queued
**Built + proven:** the canonical shell, 15 mixins, numeric code tables, the registry + schema-object-template
index, the 2 contracts, the safe instantiator, and the proof. **Queued** (`prompts/shared-template-registry.md`):
the remaining template contracts (TemplateGraph/Instantiation/Compatibility/Evaluation/Visibility/Provenance),
the full template-category template files (infrastructure/inference/resources/api/ui/purpose-tasks), the template
graph + rubrics, the `/api/templates/*` + `/templates` UI, and the template redteam.
