> **EDITOR'S NOTE (captured 2026-06-06 from the owner).** Canonical spec for the internal **Shared Template
> Registry** (future public surface: OpenTemplatesHub.io — NOT launched). Executed INCREMENTALLY. **DONE +
> proven (flywheel 339):** the canonical 14-section object shell (`templates/schema-objects/canonical_object_shell.json`)
> + 15 schema mixins (`templates/schema-objects/mixins/`); numeric code tables
> (`architecture/template_{status,visibility,edge_type}_codes.json`); registry + schema-object index
> (`architecture/{template_registry,schema_object_templates}.json`); contracts
> `schemas/templates/{TemplateArtifact,SchemaObjectTemplate}.v1` (registered); safe instantiator
> `src/teleon/templates/instantiator.py` (CANDIDATE-only, no overwrite/traversal/secret); proof
> `scripts/check_shared_template_registry.py`; doc `docs/templates/shared-template-registry.md`. Reuses the
> existing `templates/` tree + `scripts/{check_template_catalog,generate_from_template}` (not reinvented).
> **QUEUED:** remaining contracts (TemplateGraph/Instantiation/Compatibility/Evaluation/Visibility/Provenance);
> the category template FILES (infrastructure k8s/cloud-fn/venv/local-emulators · inference-preference · data-
> resource · api/ui · purpose-task); the template graph + rubrics; `/api/templates/*` + `/templates` UI; the
> template redteam (writes-outside-dir · raw-secret · real-cloud · schema-no-version/provenance · display-string
> control · k8s-no-atomic-claim · cloud-fn-no-emulator · api-writes-truth · generated-active-without-harness ·
> template-treated-as-proof · registry-as-runtime — all fail safe).

# /workflows /shared-template-registry-and-schema-object-templates

Build an internal shared template registry (NOT a public OpenTemplatesHub yet). Categories: schema-object
templates · infrastructure/runtime · API/UI · inference-preference · data-resource · PurposeTask · receipts ·
validation rubrics · redteam. Reuse existing templates; do not replace working worker templates; do not merge
into OpenHarnessHub; templates are not a runtime; generated outputs are candidates until validated.

## SHARED TEMPLATE REGISTRY CLAUSE (carry forward)
Templates are not only infrastructure starters. The shared template system also includes standardized schema
object templates, schema mixins, canonical object shells, I/O-contract templates, command/event/error envelope
templates, inference-preference templates, data-resource templates, API/UI templates, worker/runtime templates,
and PurposeTask templates. Internal Shared Template Registry for now; OpenTemplatesHub.io is a possible future
public surface. Templates generate STARTING SHAPES; harnesses prove generated outputs work; generated outputs
are CANDIDATE until validated, redteamed, registered, and promoted.

## Canonical object shell (14 sections — the reusable shape)
identity · scope · contracts · payload_or_ref · provenance · lineage · policy · security · visibility ·
lifecycle · status · telemetry · relationships · receipts. Reusable across ContextArtifact/SkillArtifact/
ToolArtifact/HarnessArtifact/TemplateArtifact/PurposeTask/WorkerApp/DataResource/ModelInvocationReceipt.

*(Full PART 1–18 detail is in the owner's message + the proven core above; build the QUEUED items next.)*
