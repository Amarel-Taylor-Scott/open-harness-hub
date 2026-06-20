# {{title}} adapter

> GENERATED STUB (standard.docs_page.v1) — fill every section before promotion.

## Purpose
Front the {{capability}} provider behind the structural {{port_name}} so processors stay SDK-free.

## Owner
{{owner}} — `scripts/adapters/{{adapter_name}}.py`.

## Inputs
Calls through the {{port_name}} method surface (see `scripts/runtime/ports.py`).

## Outputs
Whatever {{port_name}} returns; secrets resolved by ref, never returned.

## Contracts
Satisfies {{port_name}} (runtime_checkable Protocol). Capability `{{capability}}`.

## Ports
{{port_name}} — the swap point (in-memory test adapter vs this production adapter).

## Adapters
`{{adapter_name}}Adapter`.

## Registry entries
- `architecture/external_capability_catalog.json += {{capability}} ({{adapter_name}})`

## Proofs
`scripts/check_{{adapter_name}}_adapter.py --self-test`

## Commands
```
python3 scripts/check_{{adapter_name}}_adapter.py --self-test
```

## Limitations
Stub: the {{port_name}} methods raise NotImplementedError; the no-key-literal + secret-by-ref contract holds.

## Opportunities
Provide an in-memory adapter alongside for fast offline tests.

## Next steps
Implement {{port_name}}, make the proof pass, register the capability.
