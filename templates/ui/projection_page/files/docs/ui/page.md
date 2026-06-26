# {{title}} page

> GENERATED STUB (standard.docs_page) — fill every section before promotion.

## Purpose
Render {{title}} by projecting `{{api_endpoint}}` — the page computes no truth.

## Owner
{{owner}} — `web/baltor/{{page}}.html`.

## Inputs
A fetch to `{{api_endpoint}}` (a registered projection route).

## Outputs
Rendered panels; held-out items shown separately from served truth.

## Contracts
Consumes the contract returned by `{{api_endpoint}}`.

## Ports
n/a (browser fetch only).

## Adapters
n/a.

## Registry entries
- `architecture/section_maturity_matrix.json` `ui_pages += web/baltor/{{page}}.html`

## Proofs
`scripts/check_{{page}}_ui.py --self-test`

## Commands
```
python3 scripts/check_{{page}}_ui.py --self-test
```

## Limitations
Stub: the render mapping is a TODO; the projection-only and no-secret guards already hold.

## Opportunities
Add per-field panels matching the projected contract.

## Next steps
Map the contract fields into panels, make the proof pass, register the ui page.
