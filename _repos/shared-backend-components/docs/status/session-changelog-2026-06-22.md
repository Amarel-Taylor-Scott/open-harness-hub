# Session changelog — 2026-06-22 (registries, the capability compiler, governance)

Consolidated record of this session's adjustments + improvements. Each is committed, proof-gated, and saved to agent
memory. Proof suite: **599 registered checks, all green** (`python3 scripts/flywheel_proof_modules.py`). serves_truth=false
on every new artifact; dependency-law + plane-separation hold throughout.

## Capability model & the descent
- **12 inefficient-pipeline archetypes** + an **IF-THEN optimization heuristic library** (`57e0268a`) — the cognition→deterministic KB seed.
- **Agnostic tool PLANES** grew to **30** (added rules_engine, workflow_orchestration, data_extraction, validation, field_parsing, fuzzy_matching, classical_ml, constraint_solver, parsing_grammar, templating, diff_compare, caching, social_scrape, entity_enrichment, stance_nli, time_series).
- **Capability LADDERS** — 18 cost-ordered, deterministic-first descents (web_browsing, document_extraction/classification, entity_enrichment, social_media_scraping, search, ocr, retrieval, asr, mt, entity_resolution, contact_lookup, meeting_notes, contract_clause, brand_monitoring, lead_research, public_statement_tracking, …).
- **Browser escalation ladder** (`9666c9b3`, `d2f15c1f`) — http→headless→headed→stealth/undetected→vision; the tool now CLIMBS (never gives up) + honest at exhaustion.
- **Profile-then-shortcut** (`d5168c9a`) — classify a PDF cheaply → skip the rungs that don't apply.
- **Micro-steps** (`e609b1b2`) — rungs decompose into 32 atomic components typed by the 7 primitives + a generator for more.

## The capability compiler (synthesis)
- **intent → outline → DAG → 5W1H verify → alternatives** (`44e64779`), with a **versioned decision tree + backtracking** (winners/losers kept lossless, honest no-solution).
- **Disciplined templated prompts** (`c5c57b4c`) — enumerate-before-commit, deterministic-before-model, test-before-descend, troubleshoot-before-backtrack, **track-data-every-step**; a troubleshooting ladder; and **escape strategies** (sprout / reframe / try-something-new) when a tree dead-ends.

## Registries (tools, ML, components)
- **Deterministic-replacement tool registry**: 100 → **245 curated** real tools, license-classified (single-source).
- **ML model-type registry** (`c7328cd8`) — 25 model types over 10 ML tasks + the time_series plane.
- **MASSIVE staged layer + harvester** (`7eb226b3`) — scrapes GitHub at scale into JSONL (content-hash dedupe, license/plane classify, resumable, rate-limit-honest). **403 staged** real tools so far.
- **Promotion boundary** (`52ef2cd5`) — staged → promoted (permissive + URL + core-plane + popularity + dedupe), **66 promoted**, `vetted:false`.
- **Scheduled harvest flywheel** (`52ef2cd5`) — grows the registry unattended.
- **Component search index** (`c6b02e0b`) — all **439 components** labelled text+keywords+vector; `search()` + `compose()` (per-rung candidates).

## Governance & infrastructure
- **Credential PLANE** (`d2f15c1f`) + **key-ownership** (byo / platform-within-limits) (`112cb3c2`) + the runtime **KEY HOLDER** (`914384d7`, redaction-safe).
- **Access-policy authorization** (`a13908f7`) + **wired into the key holder + the descent** (`e33fec29`) — deny-by-default; a principal only resolves/sees what they're entitled to; restricted (evasion/social/PII), plan-gated, internal tiers.
- **Storage tiers** (`c6b02e0b`) — config stays JSON/git; operational JSONL → SQLite-local / **Postgres+pgvector**-cloud via the record_store port (round-trip parity proven).
- **Discovery pipeline** (`914384d7`) — GitHub + governed Facebook → ideas (tool/plugin/capability), candidate-only.
- **Adjacent verticals** (`b8871750`) — insurance-free adjudication verticals + an in-code no-insurance guardrail.

## Memory (the durable record of decisions)
13 new topic memories written this session (capability-synthesis-compiler, massive-registry-layers-and-harvester,
access-policy-authorization, credential-plane-reachability, escalate-before-concluding-unavailable, public-statement-
tracking-stance, ml-model-type-registry, input-profiler-shortcut, registry-storage-tiers-and-component-search, …) + this
changelog.
