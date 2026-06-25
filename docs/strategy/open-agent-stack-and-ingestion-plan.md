# The Open Agent Stack + Recursive-Cognition Substrate — grounded build plan

> Synthesis of the owner's 2026-06-25 vision (messages on universal tool wrappers, rehydration/doctor/kickstart,
> the Open\* Format family, and seed-source ingestion). **Warrant: clear, detailed owner intent.** This is the
> marching-orders map the `./build` loop and contributors work from. serves_truth=false (a plan/candidate).
> Core principle: *no task ever completes — every result creates new questions; the system never stops thinking,
> but it stops **cheaply and deterministically** wherever it can (the Teleon descent).*

## The discipline first: most of this already exists
Per the Foundational Law (*"check it doesn't already exist; don't rebuild it"*), the vision maps onto existing
assets. We **connect and fill gaps**, we do not greenfield a parallel system.

### Recursive-substrate layers → existing assets → gap
| Owner layer | Already in repo | Real gap to build |
|---|---|---|
| Universal tool wrapper | `src/teleon/components/` (uniform `Component.invoke`), agnostic ports (`browser_port`, `ocr_port`, `inference/adapters`) | a thin **probe/diagnostic envelope** exposing `health/state/history/confidence/intervention hooks` on top of existing ports |
| Supervisor | `src/baltor/workers/` (`fleet_supervisor`, `supervisor_watch/ledger/metrics`, `control_plane`) | extend to watch **tasks/tools**, not just workers; inject questions on stall |
| Doctor | `src/baltor/workers/failure_taxonomy`, `provider_circuit_breaker`, `determinism/fallback_router` | a `diagnose()` that maps a failure → recovery rungs |
| Rehydration / Kickstart | `escalate-before-unavailable` ladders (`capability_ladders.json`), `acquisition_strategies.json` | **`search_exhaustion_ladder.json` (BUILT)** + a `next_rung()` injector |
| Multi-search infra | `search_provider_registry.json`, `intelligence_source_registry.json`, `external_api_registry.json` | wire the keyed rungs (RapidAPI/Brave/Tavily/Serp) + browser/archive/community rungs |
| Content pipeline | `src/teleon/registry/populate.py` (signal→record→enrich→stage), `ingest/bulk_registry` | the **interrogation stage** (ask the question bank against content) |
| Registry interrogation | `kaggle_mining_questions.json` (question bank) | a **general object-interrogation engine** (the confirmed gap) over `universal_object_schema.json` |
| Recursive expansion | `proposal_backlog.py`, `research_queue.py`, the `./build` loop | wire "every record spawns subtasks" into the backlog |
| Self-awareness / adversarial | `multi_model_improvement_loop.py` (defer-to panel), `change-verification-contract` | a `why_did_i_stop()` checklist gated on the exhaustion ladder |

### Open\* Format family → seven primitives / CTS → home
The owner's Open Agent Stack is a **registry family** (not 14 new codebases). Each format is a schema +
records, living under `architecture/` / `schemas/`, governed like every other registry.
| Format | Maps to | Seed/home |
|---|---|---|
| OKF (Knowledge) | Knowledge Corpus primitive | external (Google) — ingested as a `standard_spec` seed |
| **OCF** (Capability) | **Action** primitive + the open CapabilityTask spec (CTS) | `universal_object_schema.json` (capabilities/inputs/outputs/limits/alternatives) |
| **OLF** (Logic) | **If-Statement** primitive | reasoning-chain object_type + `reasoning_strategies` registry |
| **OKSF** (Kickstart) | Loop primitive | **`search_exhaustion_ladder.json` (BUILT)** + retry/decompose strategies |
| **ORF** (Recovery) | Stop/End + Loop | `failure_taxonomy` + `provider_fallback` + the ladder |
| **OSF** (Search) | Input primitive | `search_provider_registry` + `search_exhaustion_ladder` |
| **ORGF** (Registry) | all primitives | `registry_ontology.json` (the 96-registry federation) |
| **OIF** (Interrogation) | meta | the object-interrogation engine (gap) + `universal_object_schema` meta-rule |
| **OSVF** (Supervisor) | meta | `src/baltor/workers/` supervisor family |
| OEF/OMF/OTF/OWF/OAF/OCSF | various | later — file as proposals, don't pre-build |

## The ingestion pipeline (what the seed corpus flows through)
`seed_sources.jsonl` → fetch via `search_exhaustion_ladder` rung → **normalize to `universal_object_schema`** →
recursive interrogation (question bank) → standardize into an Open\* Format record → store in the right registry
(`registry_ontology`) → enrich (metadata/embeddings/variations via `registry/enrich.py`) → spawn subtasks for
every `open_question` / `adjacent_tool` / `missing_metadata` → recurse. Governed: public-only, candidate until
verified, promotion boundary, lossless.

## Phased build order (for `./build` + contributors)
1. **Rehydration/Kickstart injector** — a `next_rung()` over `search_exhaustion_ladder.json` + a stall detector,
   wired into the supervisor. (Antidote to "gave up too soon." Keyless.) ← do first.
2. **General object-interrogation engine** — generate the thousands of spintax questions over
   `universal_object_schema` objects + code-graph symbols + registry records → `interrogation_candidates.jsonl`.
3. **Seed ingestion run** — fetch the keyless seeds (github/HN/arxiv/rss), normalize, interrogate, populate
   registries. (Live keys for RapidAPI/Brave/Tavily extend coverage — owner to provide.)
4. **Universal tool envelope** — wrap existing ports with probe/diagnostic/intervention hooks for the supervisor.
5. **Open\* Format schemas** — formalize OCF/OLF/OKSF/ORF as `schemas/*.schema.json` from the universal schema.

## Inputs needed from the owner (unblock the live data layer)
- The **RapidAPI services + keys** (plug into `external_api_registry` + ladder rung 12; stored in `.env`, never
  committed).
- The **~10 social sites / pages / groups** to scrape (added to `seed_sources.jsonl` with governance tags).
- **Priority**: which phase (1–5) to run first.
