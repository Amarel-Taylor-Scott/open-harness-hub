# CFPB Artifact Graph Demo (C32)

The `/integrate` page is the polished, guided CFPB demo. `/cfpb-artifact-graph` is the **builder-grade,
inspectable** demo: it shows CFPB ingestion decomposed into a **versioned artifact graph** — not a single
"5 records → context pack" headline. Context objects are **one layer**, not the terminal output.

The whole flow is deterministic and offline (no model, no network, no paid API, no `pip`). The ledger is
the **source of truth**; the page and the API response are projections.

## Flow

```
CFPB records
  → source artifact graph (source_record / source_field / source_block / sentence)
  → context objects + decomposition (atomic_fact / narrative_allegation / entity_mention / emotion_signal / conclusion)
  → stored in ONE artifact ledger (content-hashed, lineaged, source-handled, governed)
  → vectorized retrieval units (deterministic local provider)
  → deterministic graph edges (rules first)
  → conflict detection (deterministic detectors)
  → reconciliation (authority/freshness/scope precedence) + receipt
  → final reconciled context pack
```

Modules: `scripts/artifact_graph/{artifact_ledger,cfpb_artifacts,vector_store,graph_builder,conflict_detector,reconciliation}.py`
+ orchestrator `scripts/cfpb_artifact_graph_demo.py`. API `POST /api/demo/cfpb-artifact-graph`; page `web/baltor/cfpb-artifact-graph.html`.

## Artifact types

One `artifacts` table (not one table per type yet) holds every decomposed object with full lineage
(`tenant_id, source_id, source_version, artifact_type, schema_version, text, payload_json, content_hash,
parent_artifact_id, source_handles_json, pipeline_id, pipeline_version, processor_id, processor_version,
run_id, claim_status, promotion_eligible, model_dependent, created_at, superseded_by`). Sibling tables:
`artifact_edges`, `artifact_vectors`, `conflicts`, `reconciliations`.

Governance is fixed at construction and never blurred by similarity:

| type | claim_status | promotion_eligible |
|---|---|---|
| `atomic_fact` (structured field) | `fact` | **true** |
| `narrative_allegation` | `unverified_allegation` | false |
| `conclusion` | `derived_conclusion` | false (until signed off) |
| `emotion_signal` | `model_interpretation` | false (model_dependent) |

## Vector provider seam

`VectorProvider` is pluggable. `DeterministicLocalVectorProvider` (`provider=deterministic_local`,
`model=hashed_lexical`, `version=v1`, 64-dim L2-normalised hashed bag-of-words) proves the lifecycle
**artifact → vector → nearest-neighbour → graph neighbourhood → context pack → receipt** with no network.
Every vector row records provider/model/version/dimensions. Search filters by `tenant_id` and by
`artifact_type`, so a semantically-similar allegation is never returned as a fact. Later swap (same
interface): sentence-transformers / OpenAI / Cohere / Gemini embeddings over **pgvector** (vectors next to
relational data, HNSW/IVFFlat), **Qdrant** (payload filtering), or **LanceDB** (embedded/local-first).

## Deterministic graph

Edges are built from rules first (`graph_builder.py`): `CONTAINS, HAS_FIELD, HAS_SENTENCE, YIELDS_FACT,
YIELDS_ALLEGATION, MENTIONS, SAME_COMPLAINT_AS, SAME_COMPANY_AS, SAME_PRODUCT_AS, SAME_ISSUE_AS,
SUPPORTED_BY` (+ `INCLUDED_IN_PACK / HELD_OUT_FROM_PACK / RECEIPT_ATTESTS` after reconciliation). Each
`edge_id` is a deterministic hash of `(tenant_id, from, edge_type, to, run_id)` and carries
`evidence_json`, so the edge set is **byte-identical across runs**. The edge TABLE is the source of truth;
project into NetworkX for graph algorithms, or later into Neo4j (GraphRAG) / RDF (RDFLib + SHACL).

## LLM candidate layer

LLMs do not write truth — they PROPOSE. Any LLM output is stored as a separate `edge_source='llm'` (or a
`candidate_*` artifact) with `claim_status='model_suggestion'`, `model_dependent=true`,
`promotion_eligible=false`, `requires_verification=true`, plus `processor_id@version`, `prompt_hash`,
`model_id`, and evidence spans. Deterministic validators (both artifacts current? same tenant? same
topic/timeframe? cited spans real? higher authority? derived from each other?) gate any promotion. The
demo runs deterministically; the panel is a documented placeholder. (LangExtract maps extractions back to
exact character offsets; spaCy provides local linguistic features — both fit the evidence-first design.)

## Conflict detection + reconciliation

Deterministic detectors (`conflict_detector.py`): deadline/numeric mismatch on the same topic
(**Reg E "10 business days" vs FAQ "30 days"**), same complaint_id + field + different current value, same
source_handle + different content_hash, and a governance check (a promotable artifact `SUPPORTED_BY` an
unverified allegation). Each conflict cites both artifacts + evidence and starts `open`.

Reconciliation precedence (`reconciliation.py`): exact regulation/source-of-law > FAQ/summary; newer
source_version > older (same authority); structured-field fact > narrative allegation; human-signed > LLM
suggestion (documented hook, no UI yet); unresolved → **held out** of the promoted pack. Each decision
emits a receipt (`decision, winning_artifact_id, held_out_artifact_ids, reason, evidence, human_review_required`).
For the demo: Reg E (rank 100) beats FAQ (rank 10) → `resolved_by_authority`, FAQ "30 days" held out, the
final pack serves "10 business days".

## Proofs

`scripts/check_cfpb_artifact_ledger.py` · `check_cfpb_vectorization.py` · `check_cfpb_deterministic_graph.py`
· `check_cfpb_conflict_detection.py` · `check_cfpb_reconciliation.py` · `check_cfpb_artifact_graph_demo.py`
(all registered in the flywheel). Run: `PYTHONPATH=. python3 scripts/cfpb_artifact_graph_demo.py --self-test`.

## Why the ledger, not the page

The dashboard can lie or go stale; the ledger cannot. Every count, conflict, and reconciliation on the
page is read back from SQLite. Local SQLite maps later to Postgres (artifacts/edges as long + JSONB tables),
object store (large payloads), and pgvector/Qdrant/LanceDB (vectors) **without changing these contracts** —
because identity is content-hash + lineage, not row position.
