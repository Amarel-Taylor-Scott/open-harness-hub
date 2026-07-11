# Open Primitive Edge Interchange (OPEI) — feasibility and layered-architecture report

> **Provenance:** owner-forwarded verbatim on 2026-07-11 (produced in the owner's external research session);
> seed handle `owner-opei-open-primitive-edge-standard-verdict-2026-07-11` in
> `data/research-queue/seed_sources.jsonl`. Claims and citations are NOT yet verified in-repo; treat as a
> candidate design input for `scripts/open_primitive_format.py` (OPF v0 → v0.2) and the strategy doc
> `docs/strategy/open-primitive-format-and-agentic-edge-landscape-2026-07-10.md`. Load-bearing rules to adopt:
> typed Measure (never a generic weight) · embedding identity = full pipeline lineage (new lineage = new
> identity, never overwrite) · similarity = computed/virtual edges · search = logical stage DAG + per-engine
> compilation reports + search receipts · eight edge namespaces kept distinct · "standard" only after
> independent producers/consumers + governance.

## Executive verdict (owner-forwarded summary)

No broadly adopted format combines: typed directional provenance-bearing edges; executable primitive identity;
typed ports without flattening native type systems; semantic/structural/effect/evidence/runtime edge
namespaces; multiple dense/sparse/multivector embeddings per subject with generation lineage; portable hybrid
search recipes; scoped typed weights; compatibility assessments + adapters; and scalable physical projections
at 20M–100M components. "Open Knowledge Format" as a literal Google spec could not be verified — nearest
precedents are Google Data Commons / MCF and MLCommons Croissant, neither of which covers executable
primitives or compatibility. Recommendation: a LAYERED profile suite (OPE-Core · OPE-Primitive ·
OPE-Assessment · OPE-Representation · OPE-Search-Experimental · OPE-Evidence) over existing standards
(RDF 1.2 / JSON-LD / GraphAr / Arrow / in-toto / OpenLineage), never a clean-sheet universal super-schema.
Graph facts + supported contracts = portable semantic records; embeddings, neighbors, ANN indexes, learned
weights, rankings = derived, immutable, versioned projections.

Key sizing facts: 100M subjects × 768-dim float32 = 307.2 GB per embedding family (eight ≈ 2.46 TB) → vectors
live OUTSIDE graph documents as content-addressed references. 50M subjects × 100 materialized neighbors = 5B
rapidly-stale edges → similarity stays computed/virtual.

Readiness: implement an experimental 0.1 working draft + validators + round trips + conformance NOW; the word
"standard" is earned later (two independent producers AND consumers, neutral governance, IP policy first).

Phases (target ~180 days): 0 spec boundary (identities, 8 edge namespaces, Measure, JSON Schema/JSON-LD/RDF
mapping, positive+negative examples) → 1 primitive+assessment pilot (MCP/OpenAPI import, PROVED/DISPROVED/
INDETERMINATE reason codes, adapters, Python validator) → 2 vector projection profile (EmbeddingProfile vs
EmbeddingArtifact; three existing embedding families exported to Arrow/Parquet + two engines; tuned variants
coexist, never mutate) → 3 logical search recipes (exact-math kernel: cosine/dot/L2/RRF/min-max/z-score/
MaxSim with canonical test vectors; compile one recipe to two engines; compilation-loss reports; search
receipts; ACL before retrieval) → 4 bulk graph + public draft (GraphAr/Parquet snapshot, JSON-LD/RDF subset,
round-trip fidelity, recruit independents, stabilize only demonstrated layers).

Owner retains the full pasted report text in the external session Library
(`OPEN_EDGE_PRIMITIVE_GRAPH_STANDARD_FEASIBILITY_2026-07-11.md`); this repo copy preserves the verdict,
architecture, rules, risks, and phase plan needed to act. The complete coverage matrices and source index are
summarized in the seed row; re-request the full text from the owner if a section below proves insufficient.

## Edge namespaces (keep distinct — never one generic edge)

Distribution (packagedIn/dependsOn) · Static code (defines/calls/flowsTo — extracted facts, NOT contracts) ·
Capability (implements/accepts/emits/requires/mayEffect — supported contract) · Compatibility
(structurallySatisfies/semanticallySatisfies/convertibleBy/conflictsWith — profile-scoped assessment) ·
Retrieval (similarUnder/candidateUnder — derived, model/recipe-scoped) · Execution (consumed/produced/
failedWith — runtime observation) · Evidence (declaredBy/testedBy/attestedBy/contradictedBy) · Policy
(allowedUnder/deniedUnder/admittedBy/revokedBy — local protected decision).

## Typed Measure (replaces every generic weight)

kind=Measure · measureType URI · value · range · preferenceDirection · calibration · subject ref · profile ref
· generatedAt. Confidence, similarity, latency/token/money cost, failure probability, learned coefficients,
policy risk are DIFFERENT measure types — never arithmetically combined until a named recipe defines
normalization, calibration, units, missing-value behavior, and direction.

## Assessment contract

assess(producer, consumer, direction, adapter, matcher profile, domain profile, evidence, environment, time)
→ PROVED | DISPROVED | INDETERMINATE, with contract digests, reason codes, unresolved facts, validity
interval. Consumer-local admission, PlanLock, and execution receipts stay protected and local — never global
registry truth.

## Canonicalization

RFC 8785 (JCS) for exact normative JSON digests; RDF Dataset Canonicalization 1.0 for serialization-invariant
RDF digests. Never interchangeable; every digest names its algorithm and scope.
