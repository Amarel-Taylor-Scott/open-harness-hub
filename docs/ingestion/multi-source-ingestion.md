# Multi-Source Ingestion (governed, behind SourceAdapterPort)

**Purpose.** Run *any* source type through the SAME governed path — source artifacts → source_record →
source_field → atomic_fact / narrative_allegation → (existing) ledger → vector → graph → conflict → reconcile
→ verify → optimize → consumption. One port, many adapters; no source becomes truth directly.

**Owner.** `scripts/ingest/source_adapters.py` (`SourceAdapter` Protocol + `normalize(source_type, payload, …)`).
**Registry.** `architecture/contract_registry.json#source_types`. **Parser providers.** cataloged in
`external_capability_catalog.json#parser_manager`.

## Source types + handle formats

| source_type | parser | scope default | source handle format | status |
|---|---|---|---|---|
| `api` | structured_record | global_public | `ctx://public/source/<sid>/record/<rid>#<field>` | active |
| `csv` | csv | tenant_private | `ctx://tenant/<tid>/source/<sid>#row.<n>.col.<col>` | active |
| `json` / `webhook` | json | tenant_private | `ctx://tenant/<tid>/source/<sid>#/json/pointer` | active |
| `pdf` | parser.docling@candidate | — | n/a (parser unavailable) | **candidate** |
| `html` | parser.html@candidate | — | n/a (parser unavailable) | **candidate** |

## Governance (enforced)

- **Structured fields → `atomic_fact`** (`promotion_eligible=true`); **free-text → `narrative_allegation`**
  (`promotion_eligible=false`, one per sentence). No raw source becomes truth.
- Every artifact carries a **source handle + content hash + tenant scope + parent lineage**.
- **Deterministic**: same payload → identical artifacts; a changed field changes only its own artifact hash.
- **Tenant scope preserved**: `tenant_private` CSV/JSON artifacts never carry `global_public` scope.
- Produced facts are **gate-compatible** (a structured fact passes the VerificationGate; an allegation is held out).
- **Honest unavailability**: a `pdf`/`html`/unknown source stores the raw payload as a source artifact and returns
  an **explicit non-consumable reason** (`parser_unavailable …`) — never a faked parse or extracted claim. Real
  parsers (Docling/PyMuPDF/Unstructured) remain cataloged candidates; the correctness invariant does not depend on them.

## Commands

```
PYTHONPATH=. python3 scripts/check_multi_source_ingestion.py --self-test
PYTHONPATH=. python3 -c "from scripts.ingest.source_adapters import normalize; import json; \
  print(json.dumps(normalize('csv','id,amount,note\n1,35,Unfair fee.\n', tenant_id='acme', source_id='x', scope='tenant_private'), indent=2, default=str)[:600])"
```

## Known limitations / next

- `pdf`/`html` are candidate (no local extractor; vendor Docling/PyMuPDF to enable — OPP-unstructured-parser).
- `database` / `email` / `folder` / `unknown-classification` source types are sequenced next, each behind the
  same port + its own proof; wiring each adapter's artifacts into the full `run_*_to_consumption` flow is the
  generic-consumption follow-on (CFPB consumption is already proven end-to-end).
