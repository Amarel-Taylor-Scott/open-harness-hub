# {{title}} source adapter

> GENERATED STUB (standard.docs_page.v1) — fill every section before promotion.

## Purpose
Governed ingestion of {{title}} ({{source_type}}) into the standard artifact chain so it flows through the
existing engine without a bespoke path.

## Owner
{{owner}} — `scripts/ingest/{{source_family}}.py`.

## Inputs
A {{source_type}} payload via `{{source_family}}Adapter.ingest(payload, tenant_id, source_id, scope, authority)`.

## Outputs
`source_record` -> `source_field` -> `atomic_fact` (structured, promotion-eligible) / `narrative_allegation`
(free-text, held-out). All content-addressed.

## Contracts
Consumes a FetchRequest-style input; emits the registered artifact_types. source_type `{{source_type}}`.

## Ports
SourceAdapter (structural): `source_type`, `parser_provider`, `ingest(...)`.

## Adapters
`{{source_family}}Adapter` (parser_provider `{{parser_provider}}`).

## Registry entries
- `architecture/contract_registry.json#source_types += {{source_type}}`
- `architecture/section_maturity_matrix.json` section `{{source_family}}` (category ingestion)

## Proofs
`scripts/check_{{source_family}}_adapter.py --self-test`

## Commands
```
python3 scripts/check_{{source_family}}_adapter.py --self-test
python3 scripts/validate.py scripts/ingest/{{source_family}}.py
```

## Limitations
Stub: `ingest` raises NotImplementedError until implemented; the proof FAILS by design until then.

## Opportunities
Wire {{source_family}} into the golden path once the adapter passes.

## Next steps
Implement `ingest`, make the proof pass, register source_type, add the section_maturity entry.
