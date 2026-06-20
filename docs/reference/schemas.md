# JSON Schemas

Every manifest validates against a Draft-2020-12 JSON Schema in
`schemas/`. The common envelope `$defs` are reused by every type-specific
schema.

| Schema | Type |
|---|---|
| `_common.schema.json` | Shared $defs (envelope, logicPath, modelTarget, packContract, …). |
| `harness.schema.json` | Harness. |
| `pipeline.schema.json` | Pipeline. |
| `benchmark.schema.json` | Benchmark. |
| `rule-pack.schema.json` | Rule pack. |
| `knowledge-pack.schema.json` | Knowledge pack. |
| `logic-pack.schema.json` | Logic pack. |
| `tool.schema.json` | Tool. |
| `persona.schema.json` | Persona. |
| `adapter.schema.json` | Model adapter. |
| `rubric.schema.json` | Rubric. |
| `dataset.schema.json` | Dataset. |

Validate every manifest with:

```bash
python scripts/validate.py
```
