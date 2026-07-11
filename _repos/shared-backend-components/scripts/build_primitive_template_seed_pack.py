#!/usr/bin/env python3
"""Build the primitive template seed pack — the 50,000-template goal's first deterministic rung.

Templates are NOT a hand-generated population. The owner law (recorded in the
variation-dimension atlas manifest) is that templates RESOLVE from dimensions
and materialize on demand. This pack therefore stores the small deterministic
generator inputs — ~25 edge-shape archetypes (data in this builder), the 60
primitive kind families (read from
``_repos/shared-backend-components/catalog/knowledge-packs/data/aidevexplorer-primitive-kind-families/``), and a
curated archetype-by-family compatibility matrix — and derives >=1,000
template candidate rows by composing them. Incoherent archetype/family pairs
are SKIPPED (never a blind cartesian product) and every skip is logged as an
auditable row plus counts in the manifest.

Every template row carries: typed slots with contracts, ``{Slot}`` placeholder
visible edges, ``variation_dimension_refs`` that point at REAL dimension ids
read from
``_repos/shared-backend-components/catalog/knowledge-packs/data/primitive-variation-dimension-atlas/``,
resolver-rule references (materialize-on-demand), proof requirements, known
failure modes, a source search plan, and the candidate boundary
(``candidate=true`` / ``serves_truth=false``). Nothing here is a measured or
promoted primitive; every row is a seed for later instantiation + proof.

Deterministic and offline: the only date in the pack is ``generated_at`` in
the manifest (``--date``, default 2026-07-02); no network, no wall clock in
row bodies. Paired checker: ``scripts/check_primitive_template_seed_pack.py``
(hand-edited pack files go red there).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import REPO_ROOT  # noqa: E402

PACK_DIR = _resource("catalog/knowledge-packs/data/primitive-template-seeds")
KIND_FAMILIES_PATH = (
    _resource("catalog/knowledge-packs/data/aidevexplorer-primitive-kind-families/families.jsonl")
)
DIMENSION_ATLAS_DIR = _resource("catalog/knowledge-packs/data/primitive-variation-dimension-atlas")
DIMENSIONS_PATH = DIMENSION_ATLAS_DIR / "primitive_variation_dimensions_250.jsonl"
RESOLVER_RULES_PATH = DIMENSION_ATLAS_DIR / "variation_resolver_rules.jsonl"
ATLAS_MANIFEST_PATH = DIMENSION_ATLAS_DIR / "manifest.json"

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
PACK_ID = "primitive-template-seeds"
PACK_VERSION = "0.1.0"  # version lives in metadata, never in ids or file names
DEFAULT_GENERATED_AT = "2026-07-02"  # date lives ONLY in the manifest
#: The first deterministic rung toward the 50,000-template goal.
MINIMUM_TEMPLATE_ROWS = 1000
SOURCE_FAMILY = "primitive_template_edge_archetype_composition"
SOURCE_STATUS = "derived_template_seed_composed_from_local_candidate_packs"
EVIDENCE_STATUS = "derived_seed_needs_instantiation_and_proof_receipts"
#: Every template resolves through these atlas resolver rules (materialize on demand).
RESOLVER_RULE_REFS: list[str] = [
    "rule:materialize_hot_or_proof_backed",
    "rule:smallest_context_first",
]
MATERIALIZATION_POLICY = "resolve_from_dimensions_on_demand"
#: Closed slot-type vocabulary (checker-enforced).
SLOT_TYPES: tuple[str, ...] = (
    "artifact", "budget", "entity", "operation", "policy", "resource", "schema", "subject",
)
#: Closed source-search surface vocabulary (offline HANDLES to search later, never fetched here).
SEARCH_SURFACES: tuple[str, ...] = (
    "github_code_search",
    "package_registries",
    "official_documentation",
    "standards_specifications",
    "public_benchmark_corpora",
    "open_data_portals",
    "workflow_template_libraries",
)
#: The dimension family every row keys an identity dimension from.
IDENTITY_DIMENSION_FAMILY = "fam:primitive_identity_granularity"
PLACEHOLDER_PATTERN = re.compile(r"\{([A-Za-z]+)\}")
#: Kind-family domains where every facet is presentational; data-shaped
#: archetypes skip families whose domains ALL fall in this set.
PRESENTATION_DOMAINS: list[str] = [
    "assets", "design_system", "diagramming", "frontend", "genai", "media",
    "reporting", "visualization",
]
#: Pure in-process computations: nothing long-lived to probe, shape, or roll back.
PURE_COMPUTE_KINDS: list[str] = [
    "algorithm.fuzzy_match", "algorithm.graph", "algorithm.near_duplicate",
    "algorithm.optimization", "algorithm.sort", "algorithm.vector_search",
]

DATA_SHAPED_SKIP_REASON = (
    "data-shaped archetype: every domain facet of this kind family is presentational, "
    "so a record/batch contract does not bind coherently"
)


def _slot(name: str, slot_type: str, hint: str) -> dict[str, str]:
    return {"name": name, "type": slot_type, "hint": hint}


def _compat_exclude(reason: str, domains: list[str] | None = None,
                    kinds: list[str] | None = None) -> dict[str, Any]:
    """Coherent unless EVERY family domain is excluded, or the kind is excluded by name."""
    return {"mode": "exclude", "domains": sorted(domains or []),
            "kinds": sorted(kinds or []), "skip_reason": reason}


def _compat_include(reason: str, domains: list[str]) -> dict[str, Any]:
    """Coherent only when the family shares at least one included domain."""
    return {"mode": "include", "domains": sorted(domains), "kinds": [], "skip_reason": reason}


# ── ~25 edge-shape archetypes (curated data, the generator's first input) ──
ARCHETYPES: list[dict[str, Any]] = [
    {
        "archetype_id": "arch:prepared_entity_import",
        "title": "Prepared, policy-gated entity batch import",
        "visible_edge": "Raw{Entity}Batch+{ImportPolicy}+Existing{Entity}Index -> Prepared{Entity}Import+ImportReceipt",
        "slots": [
            _slot("Entity", "entity", "typed record family drawn from the base kind's input edge"),
            _slot("ImportPolicy", "policy", "dedupe scope, conflict resolution, quarantine thresholds"),
        ],
        "slot_contracts": {
            "Entity": "typed record family with a stable primary key and declared schema_version metadata",
            "ImportPolicy": "declares dedupe scope, conflict-resolution order, and quarantine thresholds; versioned in metadata",
        },
        "mutators": ["field_rename", "output_wrapper", "retry_wrapper"],
        "proof_requirements": ["slot_fixture_test", "import_idempotency_test", "receipt_shape_test"],
        "failure_modes": [
            "second apply silently duplicates rows because the existing index was stale",
            "conflict resolution drops the newer record without a receipt",
            "quarantine threshold unversioned, so reruns route different rows",
        ],
        "dimension_families": ["fam:data_types_schema_semantics", "fam:data_layout_storage_modeling",
                               "fam:industry_domain_business_context"],
        "instantiation_templates": [
            "prepare a governed {kind} import for: {task}",
            "re-run the same {kind} import batch and prove the second apply is a no-op for: {task}",
        ],
        "search_terms": ["governed batch import pipeline", "idempotent upsert import receipt"],
        "search_surfaces": ["github_code_search", "package_registries", "official_documentation"],
        "compatibility": _compat_exclude(DATA_SHAPED_SKIP_REASON, domains=PRESENTATION_DOMAINS),
    },
    {
        "archetype_id": "arch:evidence_backed_answer",
        "title": "Evidence-backed answer over a governed corpus",
        "visible_edge": "{Entity}Query+{SourcePolicy}+{CorpusHandle} -> EvidenceBackedAnswer+SourceBundle",
        "slots": [
            _slot("Entity", "entity", "the question's subject record family"),
            _slot("SourcePolicy", "policy", "allowed sources, freshness window, citation requirements"),
            _slot("CorpusHandle", "resource", "handle to the governed corpus or index queried"),
        ],
        "slot_contracts": {
            "Entity": "typed subject family the query is grounded in; never free text alone",
            "SourcePolicy": "declares allowed source tiers, freshness window, and mandatory citation shape",
            "CorpusHandle": "resolvable handle to a governed corpus/index; never an inline document dump",
        },
        "mutators": ["filter_predicate", "output_wrapper"],
        "proof_requirements": ["citation_support_test", "source_handle_resolution_test", "slot_fixture_test"],
        "failure_modes": [
            "answer cites a source that does not support the claim",
            "corpus handle resolves to a stale snapshot without a freshness warning",
            "held-out or rejected evidence is silently dropped instead of carried as a warning",
        ],
        "dimension_families": ["fam:ml_ai_rag_benchmark", "fam:web_browsing_source_surfaces",
                               "fam:response_format_user_output"],
        "instantiation_templates": [
            "answer a {kind} question with a source bundle for: {task}",
            "prove every claim in a {kind} answer resolves to a supporting span for: {task}",
        ],
        "search_terms": ["retrieval augmented answer citations", "grounded question answering receipt"],
        "search_surfaces": ["github_code_search", "public_benchmark_corpora", "official_documentation"],
        "compatibility": _compat_exclude(DATA_SHAPED_SKIP_REASON, domains=PRESENTATION_DOMAINS),
    },
    {
        "archetype_id": "arch:rendered_artifact_budget",
        "title": "Budget-gated artifact rendering with receipts",
        "visible_edge": "{Artifact}+{RenderBudget} -> Rendered{Artifact}+BudgetReceipt",
        "slots": [
            _slot("Artifact", "artifact", "the renderable artifact family (page, chart, scene, media)"),
            _slot("RenderBudget", "budget", "wall-time, memory, and output-size envelope"),
        ],
        "slot_contracts": {
            "Artifact": "typed renderable artifact with declared output format expectations",
            "RenderBudget": "hard envelope: wall-time, memory, output size; overruns fail loud with a receipt",
        },
        "mutators": ["output_wrapper", "cache_wrapper"],
        "proof_requirements": ["render_smoke_test", "budget_overrun_test", "receipt_shape_test"],
        "failure_modes": [
            "render succeeds locally but the budget receipt omits peak memory",
            "budget overrun degrades quality silently instead of failing loud",
            "cached render served after the artifact's inputs changed",
        ],
        "dimension_families": ["fam:ui_visualization_media_artifact_design",
                               "fam:response_format_user_output", "fam:variation_control_lattice"],
        "instantiation_templates": [
            "render a {kind} artifact inside a declared budget for: {task}",
            "prove a {kind} render overrun fails loud with a budget receipt for: {task}",
        ],
        "search_terms": ["render budget receipt", "deterministic artifact rendering pipeline"],
        "search_surfaces": ["github_code_search", "official_documentation", "workflow_template_libraries"],
        "compatibility": _compat_include(
            "rendering archetype: only presentational kind families produce renderable artifacts",
            domains=PRESENTATION_DOMAINS),
    },
    {
        "archetype_id": "arch:policy_gated_action",
        "title": "Guardrail-gated action decision",
        "visible_edge": "{Action}Request+{GuardrailPolicy} -> Gated{Action}Decision+PolicyReceipt",
        "slots": [
            _slot("Action", "operation", "the effectful operation family being gated"),
            _slot("GuardrailPolicy", "policy", "deny-by-default rules, approval tiers, blast-radius limits"),
        ],
        "slot_contracts": {
            "Action": "declared operation family with enumerated side effects",
            "GuardrailPolicy": "deny-by-default; every allow carries a rule id and an approval tier",
        },
        "mutators": ["filter_predicate", "output_wrapper"],
        "proof_requirements": ["deny_by_default_test", "policy_receipt_test", "slot_fixture_test"],
        "failure_modes": [
            "gate evaluates after the side effect instead of before",
            "policy exception path bypasses the receipt",
            "approval tier mapping drifts from the org policy source",
        ],
        "dimension_families": ["fam:legal_compliance_security_governance",
                               "fam:industry_domain_business_context", "fam:variation_control_lattice"],
        "instantiation_templates": [
            "gate a {kind} action behind a guardrail policy for: {task}",
            "prove a denied {kind} action leaves no side effect for: {task}",
        ],
        "search_terms": ["policy as code action gate", "guardrail approval receipt"],
        "search_surfaces": ["github_code_search", "standards_specifications", "official_documentation"],
        "compatibility": _compat_exclude(
            "universal mechanism: every kind family executes actions that can be policy-gated"),
    },
    {
        "archetype_id": "arch:idempotent_replay",
        "title": "Idempotent execution with a replay ledger",
        "visible_edge": "{Operation}Request+{IdempotencyPolicy}+ReplayLedger -> Executed{Operation}Result+ReplayReceipt",
        "slots": [
            _slot("Operation", "operation", "the retryable operation family"),
            _slot("IdempotencyPolicy", "policy", "key derivation, dedupe window, replay semantics"),
        ],
        "slot_contracts": {
            "Operation": "operation family whose full mutating parameter set feeds the idempotency key",
            "IdempotencyPolicy": "declares key derivation, dedupe window, and replay-equality semantics",
        },
        "mutators": ["retry_wrapper", "output_wrapper"],
        "proof_requirements": ["idempotency_key_coverage_test", "double_apply_test", "receipt_shape_test"],
        "failure_modes": [
            "idempotency key omits a mutating parameter, so distinct requests collide",
            "replay ledger truncation window shorter than the retry window",
            "second apply returns success but a different result body",
        ],
        "dimension_families": ["fam:core_computer_logic", "fam:api_web_event_integration",
                               "fam:architecture_system_design_pattern"],
        "instantiation_templates": [
            "execute a {kind} request idempotently for: {task}",
            "prove a replayed {kind} request short-circuits via the ledger for: {task}",
        ],
        "search_terms": ["idempotency key replay ledger", "exactly once effect deduplication"],
        "search_surfaces": ["github_code_search", "official_documentation", "standards_specifications"],
        "compatibility": _compat_exclude(
            "sampled generative kinds do not contract replay-equality of outputs",
            kinds=["genai.image_generation", "genai.video_generation"]),
    },
    {
        "archetype_id": "arch:drift_detection",
        "title": "Baseline-versus-observed drift detection",
        "visible_edge": "Observed{Surface}Snapshot+Baseline{Surface}Snapshot+{DriftPolicy} -> {Surface}DriftFindings+DriftReceipt",
        "slots": [
            _slot("Surface", "subject", "the observed surface family (schema, config, metric, contract)"),
            _slot("DriftPolicy", "policy", "tolerances, ignore rules, severity mapping"),
        ],
        "slot_contracts": {
            "Surface": "snapshot-comparable surface with a canonical serialization",
            "DriftPolicy": "declares tolerances and ignore rules; every ignore carries a rationale",
        },
        "mutators": ["filter_predicate", "output_wrapper"],
        "proof_requirements": ["known_drift_fixture_test", "no_drift_noop_test", "receipt_shape_test"],
        "failure_modes": [
            "canonicalization differences reported as drift (false positives)",
            "ignore rules grow until real drift is invisible",
            "baseline snapshot updated without a receipt, hiding the drift window",
        ],
        "dimension_families": ["fam:devops_observability_runtime_ops",
                               "fam:data_types_schema_semantics", "fam:variation_control_lattice"],
        "instantiation_templates": [
            "detect drift on a {kind} surface against its baseline for: {task}",
            "prove an identical {kind} snapshot pair yields zero findings for: {task}",
        ],
        "search_terms": ["schema drift detection baseline", "configuration drift receipt"],
        "search_surfaces": ["github_code_search", "official_documentation", "package_registries"],
        "compatibility": _compat_exclude(
            "universal mechanism: every kind family exposes a snapshot-comparable surface"),
    },
    {
        "archetype_id": "arch:quarantine_review_routing",
        "title": "Risk-routed acceptance with quarantine and review tickets",
        "visible_edge": "{Record}Batch+{RiskPolicy} -> Accepted{Record}Set+Quarantined{Record}Set+ReviewRoutingReceipt",
        "slots": [
            _slot("Record", "entity", "the candidate record family being risk-routed"),
            _slot("RiskPolicy", "policy", "risk tiers, quarantine triggers, reviewer routing"),
        ],
        "slot_contracts": {
            "Record": "candidate record family; quarantined items are preserved, never deleted",
            "RiskPolicy": "declares risk tiers, quarantine triggers, and the reviewer queue each tier routes to",
        },
        "mutators": ["filter_predicate", "output_wrapper", "map_sequence"],
        "proof_requirements": ["partition_completeness_test", "quarantine_preservation_test", "receipt_shape_test"],
        "failure_modes": [
            "accepted + quarantined sets do not partition the input batch",
            "quarantine treated as deletion, losing the raw layer",
            "review tickets created without a routing target, so they rot",
        ],
        "dimension_families": ["fam:legal_compliance_security_governance",
                               "fam:job_role_seniority_workforce", "fam:industry_domain_business_context"],
        "instantiation_templates": [
            "risk-route a {kind} batch into accept/quarantine for: {task}",
            "prove every quarantined {kind} row keeps its raw record and reason for: {task}",
        ],
        "search_terms": ["review queue quarantine routing", "risk tier record triage"],
        "search_surfaces": ["github_code_search", "workflow_template_libraries", "official_documentation"],
        "compatibility": _compat_exclude(
            "universal mechanism: every kind family emits candidate outputs that can be risk-routed"),
    },
    {
        "archetype_id": "arch:normalization_canonicalization",
        "title": "Raw-to-canonical normalization with receipts",
        "visible_edge": "Raw{Entity}Set+{NormalizationPolicy} -> Canonical{Entity}Set+NormalizationReceipt",
        "slots": [
            _slot("Entity", "entity", "the record family being canonicalized"),
            _slot("NormalizationPolicy", "policy", "canonical forms, locale rules, unit conversions"),
        ],
        "slot_contracts": {
            "Entity": "record family with declared raw and canonical schemas; raw layer preserved",
            "NormalizationPolicy": "declares canonical forms, locale/unit rules, and unknown-value handling",
        },
        "mutators": ["field_rename", "map_sequence", "output_wrapper"],
        "proof_requirements": ["canonical_form_fixture_test", "raw_layer_preservation_test", "unicode_test"],
        "failure_modes": [
            "normalization is lossy and the raw value is discarded",
            "locale-dependent rules applied with a hardcoded locale",
            "two distinct raw values collapse to one canonical value without a merge receipt",
        ],
        "dimension_families": ["fam:data_types_schema_semantics", "fam:common_schema_interchange",
                               "fam:region_geography_localization_jurisdiction"],
        "instantiation_templates": [
            "canonicalize a raw {kind} set for: {task}",
            "prove {kind} normalization keeps the raw layer and lineage for: {task}",
        ],
        "search_terms": ["data normalization canonical form", "locale aware field canonicalization"],
        "search_surfaces": ["github_code_search", "standards_specifications", "package_registries"],
        "compatibility": _compat_exclude(DATA_SHAPED_SKIP_REASON, domains=PRESENTATION_DOMAINS),
    },
    {
        "archetype_id": "arch:dedupe_clustering",
        "title": "Blocked similarity dedupe into clusters",
        "visible_edge": "{Entity}Batch+{BlockingPolicy}+{SimilarityPolicy} -> {Entity}ClusterSet+DedupeReceipt",
        "slots": [
            _slot("Entity", "entity", "the record family being deduplicated"),
            _slot("BlockingPolicy", "policy", "blocking keys that bound the candidate pair space"),
            _slot("SimilarityPolicy", "policy", "comparison features, weights, and thresholds"),
        ],
        "slot_contracts": {
            "Entity": "record family with comparable fields; cluster members keep lineage to raw rows",
            "BlockingPolicy": "declares blocking keys and the expected pair-space bound",
            "SimilarityPolicy": "declares comparison features, weights, thresholds; thresholds versioned in metadata",
        },
        "mutators": ["field_rename", "map_sequence", "output_wrapper"],
        "proof_requirements": ["known_pair_fixture_test", "threshold_boundary_test", "cluster_lineage_test"],
        "failure_modes": [
            "loose blocking keys cause a quadratic pair blowup",
            "threshold tuned on one population misfires on another",
            "cluster merge loses the losing records' lineage",
        ],
        "dimension_families": ["fam:algorithms_data_structures",
                               "fam:embedding_affinity_search_materialization",
                               "fam:data_types_schema_semantics"],
        "instantiation_templates": [
            "dedupe a {kind} batch into clusters for: {task}",
            "prove {kind} dedupe keeps every merged row's lineage for: {task}",
        ],
        "search_terms": ["record linkage blocking keys", "fuzzy dedupe cluster threshold"],
        "search_surfaces": ["github_code_search", "package_registries", "public_benchmark_corpora"],
        "compatibility": _compat_exclude(DATA_SHAPED_SKIP_REASON, domains=PRESENTATION_DOMAINS),
    },
    {
        "archetype_id": "arch:cost_budget_gate",
        "title": "Cost-budget gate over a workload plan",
        "visible_edge": "{Workload}Plan+{CostBudget} -> Approved{Workload}Plan+BudgetGateReceipt",
        "slots": [
            _slot("Workload", "operation", "the plannable workload family"),
            _slot("CostBudget", "budget", "spend, token, and compute envelopes with escalation rules"),
        ],
        "slot_contracts": {
            "Workload": "workload family whose plan enumerates billable steps before execution",
            "CostBudget": "declares spend/token/compute envelopes and who approves an overage",
        },
        "mutators": ["filter_predicate", "output_wrapper"],
        "proof_requirements": ["budget_rejection_test", "estimate_versus_actual_receipt_test", "slot_fixture_test"],
        "failure_modes": [
            "estimate model drifts from actual cost with no reconciliation receipt",
            "budget gate approves a plan whose steps are re-estimated after approval",
            "overage escalation路 routes to a queue nobody owns",
        ],
        "dimension_families": ["fam:devops_observability_runtime_ops",
                               "fam:architecture_system_design_pattern", "fam:variation_control_lattice"],
        "instantiation_templates": [
            "gate a {kind} workload plan behind a cost budget for: {task}",
            "prove an over-budget {kind} plan is rejected with a receipt for: {task}",
        ],
        "search_terms": ["cost budget gate workload plan", "spend envelope approval receipt"],
        "search_surfaces": ["github_code_search", "official_documentation", "workflow_template_libraries"],
        "compatibility": _compat_exclude(
            "universal mechanism: every kind family consumes budgetable compute"),
    },
    {
        "archetype_id": "arch:schema_mapping",
        "title": "Source-to-target schema field mapping",
        "visible_edge": "Source{Schema}Contract+Target{Schema}Contract+{MappingPolicy} -> {Schema}FieldMap+MappingReceipt",
        "slots": [
            _slot("Schema", "schema", "the schema family being mapped between contracts"),
            _slot("MappingPolicy", "policy", "coercion rules, unmapped-field handling, collision rules"),
        ],
        "slot_contracts": {
            "Schema": "declared source and target contracts with field types and semantics",
            "MappingPolicy": "declares coercions, unmapped-field handling, and collision resolution; no silent drops",
        },
        "mutators": ["field_rename", "map_sequence", "output_wrapper"],
        "proof_requirements": ["roundtrip_fixture_test", "unmapped_field_receipt_test", "slot_fixture_test"],
        "failure_modes": [
            "unmapped fields silently dropped instead of receipted",
            "type coercion loses precision without a warning",
            "field names match but semantics differ (semantic false positive)",
        ],
        "dimension_families": ["fam:common_schema_interchange", "fam:data_types_schema_semantics",
                               "fam:file_message_artifact_formats"],
        "instantiation_templates": [
            "map a {kind} source contract onto a target contract for: {task}",
            "prove every unmapped {kind} field appears in the mapping receipt for: {task}",
        ],
        "search_terms": ["schema mapping field coercion", "contract to contract field map"],
        "search_surfaces": ["github_code_search", "standards_specifications", "package_registries"],
        "compatibility": _compat_exclude(DATA_SHAPED_SKIP_REASON, domains=PRESENTATION_DOMAINS),
    },
    {
        "archetype_id": "arch:provenance_stamping",
        "title": "Provenance and lineage stamping over artifact batches",
        "visible_edge": "{Artifact}Batch+{ProvenancePolicy} -> Provenanced{Artifact}Batch+LineageReceipt",
        "slots": [
            _slot("Artifact", "artifact", "the artifact family receiving provenance stamps"),
            _slot("ProvenancePolicy", "policy", "required lineage fields, source handles, license capture"),
        ],
        "slot_contracts": {
            "Artifact": "artifact family whose body hash is stable under formatting-only changes",
            "ProvenancePolicy": "declares required lineage fields, source handles, and license capture rules",
        },
        "mutators": ["output_wrapper", "map_sequence"],
        "proof_requirements": ["lineage_completeness_test", "content_hash_stability_test", "receipt_shape_test"],
        "failure_modes": [
            "formatting-only change creates a false new version",
            "license metadata missing upstream and stamped as unknown-silently",
            "tenant-private lineage leaks into a global artifact",
        ],
        "dimension_families": ["fam:legal_compliance_security_governance",
                               "fam:source_mining_benchmarks_public_corpora",
                               "fam:file_message_artifact_formats"],
        "instantiation_templates": [
            "stamp provenance onto a {kind} batch for: {task}",
            "prove a formatting-only {kind} change keeps its content identity for: {task}",
        ],
        "search_terms": ["artifact provenance lineage stamp", "content hash identity receipt"],
        "search_surfaces": ["github_code_search", "standards_specifications", "official_documentation"],
        "compatibility": _compat_exclude(
            "universal mechanism: every kind family emits artifacts that need lineage"),
    },
    {
        "archetype_id": "arch:incremental_sync",
        "title": "Delta-based incremental synchronization",
        "visible_edge": "{Source}Delta+{SyncPolicy}+TargetStateIndex -> Applied{Source}Delta+SyncReceipt",
        "slots": [
            _slot("Source", "subject", "the upstream system family emitting deltas"),
            _slot("SyncPolicy", "policy", "ordering, conflict, tombstone, and backfill rules"),
        ],
        "slot_contracts": {
            "Source": "upstream family with a monotonic delta cursor or change feed",
            "SyncPolicy": "declares ordering guarantees, conflict resolution, tombstone handling, and backfill triggers",
        },
        "mutators": ["retry_wrapper", "output_wrapper", "map_sequence"],
        "proof_requirements": ["cursor_monotonicity_test", "tombstone_propagation_test", "receipt_shape_test"],
        "failure_modes": [
            "deletes upstream never tombstone downstream, so ghosts accumulate",
            "cursor resets replay old deltas as new",
            "conflict resolution differs between backfill and steady state",
        ],
        "dimension_families": ["fam:api_web_event_integration", "fam:data_layout_storage_modeling",
                               "fam:sql_database_query_engine"],
        "instantiation_templates": [
            "apply a {kind} delta stream incrementally for: {task}",
            "prove a {kind} delete propagates as a tombstone for: {task}",
        ],
        "search_terms": ["change data capture incremental sync", "delta cursor tombstone"],
        "search_surfaces": ["github_code_search", "official_documentation", "package_registries"],
        "compatibility": _compat_exclude(DATA_SHAPED_SKIP_REASON, domains=PRESENTATION_DOMAINS),
    },
    {
        "archetype_id": "arch:contract_fixture_generation",
        "title": "Contract-derived fixture set generation",
        "visible_edge": "{Component}Contract+{FixturePolicy} -> {Component}FixtureSet+FixtureReceipt",
        "slots": [
            _slot("Component", "subject", "the component family whose contract seeds fixtures"),
            _slot("FixturePolicy", "policy", "coverage targets, edge-case classes, synthetic-data rules"),
        ],
        "slot_contracts": {
            "Component": "component family with a declared io contract to derive fixtures from",
            "FixturePolicy": "declares coverage targets, edge-case classes, and synthetic-only data rules (no real PII)",
        },
        "mutators": ["map_sequence", "output_wrapper"],
        "proof_requirements": ["fixture_contract_conformance_test", "edge_case_coverage_test", "synthetic_only_gate"],
        "failure_modes": [
            "fixtures mirror the happy path and miss declared error paths",
            "synthetic data accidentally embeds realistic personal identifiers",
            "fixtures age out as the contract evolves with no staleness receipt",
        ],
        "dimension_families": ["fam:data_types_schema_semantics", "fam:language_runtime_stack",
                               "fam:variation_control_lattice"],
        "instantiation_templates": [
            "generate a contract-derived fixture set for a {kind} for: {task}",
            "prove {kind} fixtures cover every declared error path for: {task}",
        ],
        "search_terms": ["contract test fixture generation", "schema derived synthetic fixtures"],
        "search_surfaces": ["github_code_search", "package_registries", "official_documentation"],
        "compatibility": _compat_exclude(
            "universal mechanism: every kind family has a contract fixtures can be derived from"),
    },
    {
        "archetype_id": "arch:dry_run_preview",
        "title": "Dry-run preview diff before a mutation",
        "visible_edge": "{Mutation}Plan+{PreviewPolicy} -> {Mutation}PreviewDiff+DryRunReceipt",
        "slots": [
            _slot("Mutation", "operation", "the effectful mutation family being previewed"),
            _slot("PreviewPolicy", "policy", "diff granularity, redaction, and divergence tolerances"),
        ],
        "slot_contracts": {
            "Mutation": "mutation family whose plan can be evaluated without applying effects",
            "PreviewPolicy": "declares diff granularity, redaction rules, and allowed preview-versus-apply divergence",
        },
        "mutators": ["output_wrapper", "filter_predicate"],
        "proof_requirements": ["no_side_effect_during_preview_test", "preview_apply_divergence_test", "receipt_shape_test"],
        "failure_modes": [
            "preview path shares code with apply and mutates state",
            "dry-run diverges from real execution on permission checks",
            "diff omits cascading effects (triggers, hooks, downstream jobs)",
        ],
        "dimension_families": ["fam:devops_observability_runtime_ops", "fam:core_computer_logic",
                               "fam:architecture_system_design_pattern"],
        "instantiation_templates": [
            "preview a {kind} mutation as a dry-run diff for: {task}",
            "prove a {kind} dry-run leaves target state untouched for: {task}",
        ],
        "search_terms": ["dry run plan preview diff", "no-op preview receipt"],
        "search_surfaces": ["github_code_search", "official_documentation", "workflow_template_libraries"],
        "compatibility": _compat_exclude(
            "pure computations have no side effects to preview; running them IS the preview",
            kinds=PURE_COMPUTE_KINDS),
    },
    {
        "archetype_id": "arch:rollback_compensation",
        "title": "Compensation plan from a failed operation receipt",
        "visible_edge": "Failed{Operation}Receipt+{CompensationPolicy} -> {Operation}CompensationPlan+RollbackReceipt",
        "slots": [
            _slot("Operation", "operation", "the effectful operation family being compensated"),
            _slot("CompensationPolicy", "policy", "undo mappings, non-compensatable effect handling"),
        ],
        "slot_contracts": {
            "Operation": "operation family whose effects enumerate a compensating action or an explicit non-compensatable flag",
            "CompensationPolicy": "declares undo mappings and how non-compensatable effects escalate to review",
        },
        "mutators": ["retry_wrapper", "output_wrapper"],
        "proof_requirements": ["compensation_coverage_test", "non_compensatable_escalation_test", "receipt_shape_test"],
        "failure_modes": [
            "compensation plan assumes state that later steps already changed",
            "non-compensatable effects silently marked as rolled back",
            "rollback receipt written before the compensation actually ran",
        ],
        "dimension_families": ["fam:architecture_system_design_pattern", "fam:api_web_event_integration",
                               "fam:devops_observability_runtime_ops"],
        "instantiation_templates": [
            "build a compensation plan from a failed {kind} receipt for: {task}",
            "prove a non-compensatable {kind} effect escalates to review for: {task}",
        ],
        "search_terms": ["saga compensation rollback plan", "failed operation undo receipt"],
        "search_surfaces": ["github_code_search", "official_documentation", "standards_specifications"],
        "compatibility": _compat_exclude(
            "pure computations mutate nothing; there is no effect to compensate",
            kinds=PURE_COMPUTE_KINDS),
    },
    {
        "archetype_id": "arch:rate_quota_shaping",
        "title": "Quota-policy request stream shaping",
        "visible_edge": "{Request}Stream+{QuotaPolicy} -> Shaped{Request}Stream+QuotaReceipt",
        "slots": [
            _slot("Request", "operation", "the callable request family being shaped"),
            _slot("QuotaPolicy", "policy", "rate limits, burst rules, fairness tiers, backpressure"),
        ],
        "slot_contracts": {
            "Request": "request family with a stable principal/tenant key for fairness accounting",
            "QuotaPolicy": "declares rate limits, burst allowances, fairness tiers, and backpressure signals",
        },
        "mutators": ["retry_wrapper", "filter_predicate", "output_wrapper"],
        "proof_requirements": ["limit_boundary_test", "fairness_tier_test", "receipt_shape_test"],
        "failure_modes": [
            "burst allowance resets on process restart, doubling effective quota",
            "shaping drops requests instead of queueing with backpressure receipts",
            "per-tenant fairness key missing, so one tenant starves the rest",
        ],
        "dimension_families": ["fam:api_web_event_integration", "fam:devops_observability_runtime_ops",
                               "fam:variation_control_lattice"],
        "instantiation_templates": [
            "shape a {kind} request stream under a quota policy for: {task}",
            "prove a {kind} burst beyond quota is queued with receipts for: {task}",
        ],
        "search_terms": ["rate limiting token bucket fairness", "quota shaping backpressure"],
        "search_surfaces": ["github_code_search", "official_documentation", "package_registries"],
        "compatibility": _compat_exclude(
            "no request stream or callable quota surface on pure computations or static artifacts",
            kinds=PURE_COMPUTE_KINDS + ["test.fixture", "ui.component", "viz.chart", "viz.graph_network"]),
    },
    {
        "archetype_id": "arch:extraction_structuring",
        "title": "Schema-guided extraction into structured tables",
        "visible_edge": "{Document}Batch+{ExtractionSchema}+{ExtractionPolicy} -> Structured{Document}Table+ExtractionReceipt",
        "slots": [
            _slot("Document", "artifact", "the semi-structured document family being extracted"),
            _slot("ExtractionSchema", "schema", "target field schema with types and span requirements"),
            _slot("ExtractionPolicy", "policy", "confidence thresholds, span citation, quarantine rules"),
        ],
        "slot_contracts": {
            "Document": "document family with resolvable source handles for every extracted span",
            "ExtractionSchema": "target schema declaring field types and whether a source span is mandatory",
            "ExtractionPolicy": "declares confidence thresholds and routes low-confidence fields to quarantine",
        },
        "mutators": ["field_rename", "map_sequence", "output_wrapper"],
        "proof_requirements": ["span_support_test", "low_confidence_quarantine_test", "slot_fixture_test"],
        "failure_modes": [
            "extracted value has no supporting span after re-render",
            "confidence calibrated on one document layout misfires on another",
            "quarantined fields dropped from the receipt instead of preserved",
        ],
        "dimension_families": ["fam:file_message_artifact_formats", "fam:web_browsing_source_surfaces",
                               "fam:geospatial_open_data_public_services"],
        "instantiation_templates": [
            "extract a structured table from a {kind} batch for: {task}",
            "prove every extracted {kind} field cites a supporting span for: {task}",
        ],
        "search_terms": ["document field extraction spans", "schema guided structuring receipt"],
        "search_surfaces": ["github_code_search", "public_benchmark_corpora", "open_data_portals"],
        "compatibility": _compat_exclude(DATA_SHAPED_SKIP_REASON, domains=PRESENTATION_DOMAINS),
    },
    {
        "archetype_id": "arch:embedding_index_refresh",
        "title": "Delta-driven vector index refresh",
        "visible_edge": "{Corpus}Delta+{EmbeddingPolicy}+ExistingVectorIndex -> Refreshed{Corpus}VectorIndex+IndexRefreshReceipt",
        "slots": [
            _slot("Corpus", "resource", "the corpus family whose delta drives the refresh"),
            _slot("EmbeddingPolicy", "policy", "model handle, dimension, chunking, re-embed triggers"),
        ],
        "slot_contracts": {
            "Corpus": "corpus family with stable document identities across refreshes",
            "EmbeddingPolicy": "declares the embedding model handle, dimension (single-sourced), chunking, and re-embed triggers",
        },
        "mutators": ["map_sequence", "cache_wrapper", "output_wrapper"],
        "proof_requirements": ["no_placeholder_embedding_gate", "delta_only_recompute_test", "receipt_shape_test"],
        "failure_modes": [
            "placeholder embeddings promoted into the live index",
            "model or dimension change without a full re-embed receipt",
            "deleted documents remain searchable in the index",
        ],
        "dimension_families": ["fam:embedding_affinity_search_materialization", "fam:ml_ai_rag_benchmark",
                               "fam:data_layout_storage_modeling"],
        "instantiation_templates": [
            "refresh a {kind} vector index from a corpus delta for: {task}",
            "prove a deleted {kind} document leaves the index for: {task}",
        ],
        "search_terms": ["incremental vector index refresh", "embedding delta recompute"],
        "search_surfaces": ["github_code_search", "package_registries", "official_documentation"],
        "compatibility": _compat_exclude(DATA_SHAPED_SKIP_REASON, domains=PRESENTATION_DOMAINS),
    },
    {
        "archetype_id": "arch:ranking_selection",
        "title": "Policy-ranked candidate selection",
        "visible_edge": "{Candidate}Set+{RankingPolicy} -> Ranked{Candidate}List+SelectionReceipt",
        "slots": [
            _slot("Candidate", "entity", "the candidate family being ranked"),
            _slot("RankingPolicy", "policy", "features, weights, tie-breaks, and abstention rules"),
        ],
        "slot_contracts": {
            "Candidate": "candidate family with comparable feature fields; losers keep lineage",
            "RankingPolicy": "declares features, weights, deterministic tie-breaks, and when to abstain",
        },
        "mutators": ["filter_predicate", "map_sequence", "output_wrapper"],
        "proof_requirements": ["deterministic_ordering_test", "tie_break_fixture_test", "receipt_shape_test"],
        "failure_modes": [
            "unstable sort makes reruns disagree on equal scores",
            "ranking score treated as truth instead of a ranking aid",
            "winner promoted without lineage to the losing candidates",
        ],
        "dimension_families": ["fam:algorithms_data_structures",
                               "fam:embedding_affinity_search_materialization",
                               "fam:response_format_user_output"],
        "instantiation_templates": [
            "rank a {kind} candidate set under a declared policy for: {task}",
            "prove equal-scored {kind} candidates order deterministically for: {task}",
        ],
        "search_terms": ["candidate ranking policy weights", "deterministic tie break selection"],
        "search_surfaces": ["github_code_search", "public_benchmark_corpora", "package_registries"],
        "compatibility": _compat_exclude(DATA_SHAPED_SKIP_REASON, domains=PRESENTATION_DOMAINS),
    },
    {
        "archetype_id": "arch:health_probe_watchdog",
        "title": "Probe-policy health report over live targets",
        "visible_edge": "{Service}ProbeTargetSet+{ProbePolicy} -> {Service}HealthReport+ProbeReceipt",
        "slots": [
            _slot("Service", "subject", "the long-lived surface family being probed"),
            _slot("ProbePolicy", "policy", "probe cadence, timeout budget, flap suppression"),
        ],
        "slot_contracts": {
            "Service": "long-lived surface with a declared liveness/readiness contract",
            "ProbePolicy": "declares cadence, timeout budget, flap suppression, and escalation thresholds",
        },
        "mutators": ["retry_wrapper", "output_wrapper"],
        "proof_requirements": ["timeout_budget_test", "flap_suppression_test", "receipt_shape_test"],
        "failure_modes": [
            "probe traffic itself degrades the probed service",
            "flap suppression hides a real sustained outage",
            "health report aggregates away the one failing target",
        ],
        "dimension_families": ["fam:devops_observability_runtime_ops", "fam:api_web_event_integration",
                               "fam:architecture_system_design_pattern"],
        "instantiation_templates": [
            "probe a {kind} target set under a probe policy for: {task}",
            "prove a flapping {kind} target is suppressed but receipted for: {task}",
        ],
        "search_terms": ["health check probe watchdog", "liveness readiness flap suppression"],
        "search_surfaces": ["github_code_search", "official_documentation", "package_registries"],
        "compatibility": _compat_exclude(
            "no long-lived surface to probe on pure computations or static artifacts",
            kinds=PURE_COMPUTE_KINDS + ["test.fixture", "viz.chart", "viz.graph_network"]),
    },
    {
        "archetype_id": "arch:notification_escalation",
        "title": "Audience-routed notification with escalation",
        "visible_edge": "{Event}Finding+{EscalationPolicy}+AudienceDirectory -> Routed{Event}Notification+EscalationReceipt",
        "slots": [
            _slot("Event", "subject", "the finding/event family being routed"),
            _slot("EscalationPolicy", "policy", "severity mapping, audience tiers, quiet hours, dedupe"),
        ],
        "slot_contracts": {
            "Event": "finding family with severity and an owning surface",
            "EscalationPolicy": "declares severity-to-audience mapping, escalation timers, and notification dedupe keys",
        },
        "mutators": ["filter_predicate", "output_wrapper"],
        "proof_requirements": ["routing_receipt_test", "escalation_timer_test", "dedupe_window_test"],
        "failure_modes": [
            "notification noise trains the audience to ignore real escalations",
            "escalation timer resets on every duplicate finding",
            "audience directory staleness routes to a departed owner",
        ],
        "dimension_families": ["fam:job_role_seniority_workforce", "fam:devops_observability_runtime_ops",
                               "fam:response_format_user_output"],
        "instantiation_templates": [
            "route a {kind} finding to the right audience for: {task}",
            "prove duplicate {kind} findings collapse into one escalation for: {task}",
        ],
        "search_terms": ["alert routing escalation policy", "notification dedupe audience"],
        "search_surfaces": ["github_code_search", "workflow_template_libraries", "official_documentation"],
        "compatibility": _compat_exclude(
            "universal mechanism: every kind family emits findings worth routing"),
    },
    {
        "archetype_id": "arch:access_scope_review",
        "title": "Scoped access grant with review receipts",
        "visible_edge": "{Principal}AccessRequest+{ScopePolicy} -> Scoped{Principal}Grant+AccessReviewReceipt",
        "slots": [
            _slot("Principal", "subject", "the requesting principal family (user, service, agent)"),
            _slot("ScopePolicy", "policy", "least-privilege scopes, expiry, review cadence"),
        ],
        "slot_contracts": {
            "Principal": "principal family with a stable identity and an auditable request context",
            "ScopePolicy": "deny-by-default least privilege; every grant carries expiry and review cadence",
        },
        "mutators": ["filter_predicate", "output_wrapper"],
        "proof_requirements": ["least_privilege_test", "expiry_enforcement_test", "receipt_shape_test"],
        "failure_modes": [
            "grants accumulate without expiry (privilege creep)",
            "service principals exempted from review cadence",
            "scope wildcard approved because the reviewer could not enumerate it",
        ],
        "dimension_families": ["fam:legal_compliance_security_governance",
                               "fam:job_role_seniority_workforce", "fam:industry_domain_business_context"],
        "instantiation_templates": [
            "grant scoped access to a {kind} surface for: {task}",
            "prove an expired {kind} grant stops working with a receipt for: {task}",
        ],
        "search_terms": ["least privilege scoped grant", "access review expiry receipt"],
        "search_surfaces": ["github_code_search", "standards_specifications", "official_documentation"],
        "compatibility": _compat_exclude(
            "pure in-process computations expose no principal-facing scope surface",
            kinds=PURE_COMPUTE_KINDS),
    },
    {
        "archetype_id": "arch:golden_regression_replay",
        "title": "Recorded-corpus regression replay against a candidate build",
        "visible_edge": "Recorded{Interaction}Corpus+Candidate{Component}Build+{ReplayPolicy} -> {Component}RegressionFindings+ReplayReceipt",
        "slots": [
            _slot("Interaction", "subject", "the recorded interaction family replayed"),
            _slot("Component", "subject", "the component family under regression test"),
            _slot("ReplayPolicy", "policy", "comparison tolerances, masking, corpus sampling"),
        ],
        "slot_contracts": {
            "Interaction": "recorded interaction family with stable identities and redacted payloads",
            "Component": "candidate build addressable side-by-side with the champion build",
            "ReplayPolicy": "declares comparison tolerances, masked volatile fields, and corpus sampling rules",
        },
        "mutators": ["map_sequence", "output_wrapper"],
        "proof_requirements": ["replay_determinism_test", "masking_coverage_test", "receipt_shape_test"],
        "failure_modes": [
            "replay corpus unrepresentative of rare branches",
            "volatile fields unmasked, so every run flags false regressions",
            "candidate build reads live state during replay, poisoning the comparison",
        ],
        "dimension_families": ["fam:public_repo_package_codebase", "fam:ml_ai_rag_benchmark",
                               "fam:variation_control_lattice"],
        "instantiation_templates": [
            "replay a recorded corpus against a candidate {kind} build for: {task}",
            "prove a masked volatile field never flags a {kind} regression for: {task}",
        ],
        "search_terms": ["golden regression replay corpus", "record and replay comparison"],
        "search_surfaces": ["github_code_search", "public_benchmark_corpora", "official_documentation"],
        "compatibility": _compat_exclude(
            "universal mechanism: every kind family's behavior can be recorded and replayed"),
    },
    {
        "archetype_id": "arch:capacity_forecast_planning",
        "title": "History-driven capacity forecast plan",
        "visible_edge": "{Workload}History+{ForecastPolicy} -> {Workload}CapacityPlan+ForecastReceipt",
        "slots": [
            _slot("Workload", "operation", "the measurable workload family being forecast"),
            _slot("ForecastPolicy", "policy", "horizon, seasonality assumptions, safety margins"),
        ],
        "slot_contracts": {
            "Workload": "workload family with a measured history series and declared units",
            "ForecastPolicy": "declares horizon, seasonality assumptions, safety margins, and forecast-versus-actual review cadence",
        },
        "mutators": ["map_sequence", "output_wrapper", "cache_wrapper"],
        "proof_requirements": ["backtest_fixture_test", "safety_margin_test", "receipt_shape_test"],
        "failure_modes": [
            "forecast never reconciled against actuals, so error compounds",
            "seasonality assumption baked in for one region only",
            "capacity plan units drift from the workload's measured units",
        ],
        "dimension_families": ["fam:algorithms_data_structures", "fam:devops_observability_runtime_ops",
                               "fam:industry_domain_business_context"],
        "instantiation_templates": [
            "forecast {kind} capacity from workload history for: {task}",
            "prove a {kind} forecast is backtested against held-out history for: {task}",
        ],
        "search_terms": ["capacity planning workload forecast", "backtested demand forecast"],
        "search_surfaces": ["github_code_search", "package_registries", "open_data_portals"],
        "compatibility": _compat_exclude(DATA_SHAPED_SKIP_REASON, domains=PRESENTATION_DOMAINS),
    },
]


# ── Input loaders (local candidate packs; offline, deterministic) ──────────
def load_kind_families() -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in
            KIND_FAMILIES_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    return sorted(rows, key=lambda row: str(row["primitive_kind"]))


def load_dimensions_by_family() -> dict[str, list[str]]:
    dims: dict[str, list[tuple[int, str]]] = {}
    for line in DIMENSIONS_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        dims.setdefault(str(row["family_id"]), []).append(
            (int(row["dimension_index"]), str(row["dimension_id"])))
    return {family: [dim_id for _, dim_id in sorted(pairs)] for family, pairs in dims.items()}


def load_resolver_rule_ids() -> set[str]:
    return {str(json.loads(line)["rule_id"]) for line in
            RESOLVER_RULES_PATH.read_text(encoding="utf-8").splitlines() if line.strip()}


def load_atlas_manifest() -> dict[str, Any]:
    return json.loads(ATLAS_MANIFEST_PATH.read_text(encoding="utf-8"))


# ── Deterministic derivation ───────────────────────────────────────────────
def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _pick_dimension(dims_by_family: dict[str, list[str]], family_id: str, key: str) -> str:
    """Stable spread over a dimension family: same key always picks the same dimension."""
    dims = dims_by_family[family_id]
    return dims[int(_sha(f"{key}|{family_id}")[:8], 16) % len(dims)]


def pair_is_coherent(archetype: dict[str, Any], family: dict[str, Any]) -> bool:
    compat = archetype["compatibility"]
    kind = str(family["primitive_kind"])
    domains = set(family["domains"])
    if compat["mode"] == "include":
        return bool(domains & set(compat["domains"])) or kind in set(compat["kinds"])
    if kind in set(compat["kinds"]):
        return False
    return bool(domains - set(compat["domains"]))


def _archetype_key(archetype: dict[str, Any]) -> str:
    return str(archetype["archetype_id"]).split(":", 1)[1]


def _archetype_rows() -> list[dict[str, Any]]:
    rows = []
    for archetype in ARCHETYPES:
        rows.append({"record_type": "primitive_template_edge_archetype", **BOUNDARY, **archetype})
    return rows


def _template_row(archetype: dict[str, Any], family: dict[str, Any],
                  dims_by_family: dict[str, list[str]]) -> dict[str, Any]:
    kind = str(family["primitive_kind"])
    key = _archetype_key(archetype)
    dedupe_key = _sha(f"{archetype['archetype_id']}|{kind}|{archetype['visible_edge']}")[:16]
    template_id = f"tmpl:seed:{key}.{kind}:{dedupe_key[:8]}"
    tasks = [str(task) for task in family["example_tasks"]] or [family["title"]]
    picked_tasks = [tasks[0], tasks[-1]]
    example_instantiations = []
    for template, task in zip(archetype["instantiation_templates"], picked_tasks):
        example_instantiations.append(template.replace("{kind}", kind).replace("{task}", task))
    dimension_refs = [_pick_dimension(dims_by_family, IDENTITY_DIMENSION_FAMILY, template_id)]
    dimension_refs += [_pick_dimension(dims_by_family, fam, template_id)
                       for fam in archetype["dimension_families"]]
    failure_modes = list(archetype["failure_modes"])
    failure_modes += [pitfall for pitfall in family.get("common_pitfalls", [])
                      if pitfall not in failure_modes]
    return {
        "record_type": "primitive_template_candidate",
        **BOUNDARY,
        "template_id": template_id,
        "dedupe_key": dedupe_key,
        "title": f"{archetype['title']} — {family['title']}",
        "archetype_ref": archetype["archetype_id"],
        "base_kind": kind,
        "base_family_ref": str(family["id"]),
        "base_family_title": str(family["title"]),
        "base_kind_edge_context": {
            "input_edge": str(family["input_edge"]),
            "output_edge": str(family["output_edge"]),
        },
        "domains": sorted(str(domain) for domain in family["domains"]),
        "runtime_targets": sorted(str(target) for target in family.get("runtime_targets", [])),
        "visible_edge": archetype["visible_edge"],
        "slots": [dict(slot) for slot in archetype["slots"]],
        "slot_contracts": dict(archetype["slot_contracts"]),
        "mutators": sorted(set(archetype["mutators"]) | set(family.get("adapter_mutators", []))),
        "proof_requirements": sorted(set(archetype["proof_requirements"])
                                     | set(family.get("proof_requirements", []))
                                     | {"candidate_boundary_gate"}),
        "known_failure_modes": failure_modes,
        "variation_dimension_refs": dimension_refs,
        "variation_dimension_atlas": DIMENSION_ATLAS_DIR.relative_to(REPO_ROOT).as_posix(),
        "resolver_rule_refs": list(RESOLVER_RULE_REFS),
        "materialization_policy": MATERIALIZATION_POLICY,
        "example_instantiations": example_instantiations,
        "source_search_plan": {
            "queries": [f"{kind} {term}" for term in archetype["search_terms"]],
            "surfaces": list(archetype["search_surfaces"]),
            "acceptance_criteria": "a real implementation of this edge shape for the base kind, "
                                   "with a visible contract and license",
            "license_gate": "record license and terms before intake; unknown license stays candidate-only",
            "candidate_only": True,
        },
        "source_refs": [
            KIND_FAMILIES_PATH.relative_to(REPO_ROOT).as_posix(),
            DIMENSIONS_PATH.relative_to(REPO_ROOT).as_posix(),
        ],
        "source_evidence_status": EVIDENCE_STATUS,
    }


def _skip_row(archetype: dict[str, Any], family: dict[str, Any]) -> dict[str, Any]:
    kind = str(family["primitive_kind"])
    return {
        "record_type": "primitive_template_compatibility_skip",
        **BOUNDARY,
        "skip_id": f"skip:{_archetype_key(archetype)}.{kind}",
        "archetype_ref": archetype["archetype_id"],
        "base_kind": kind,
        "base_family_ref": str(family["id"]),
        "skip_reason": archetype["compatibility"]["skip_reason"],
    }


def build_pack() -> dict[str, Any]:
    """Return {filename: rows} for every non-manifest pack file. Deterministic, offline."""
    families = load_kind_families()
    dims_by_family = load_dimensions_by_family()
    templates: list[dict[str, Any]] = []
    skips: list[dict[str, Any]] = []
    for archetype in ARCHETYPES:
        for family in families:
            if pair_is_coherent(archetype, family):
                templates.append(_template_row(archetype, family, dims_by_family))
            else:
                skips.append(_skip_row(archetype, family))
    return {
        "edge_shape_archetypes.jsonl": _archetype_rows(),
        "template_candidates.jsonl": templates,
        "compatibility_skips.jsonl": skips,
    }


def _canonical_bytes(pack: dict[str, Any]) -> bytes:
    parts: list[str] = []
    for name in sorted(pack):
        parts.extend(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in pack[name])
    return ("\n".join(parts) + "\n").encode("utf-8")


def _input_fingerprints() -> dict[str, str]:
    fingerprints: dict[str, str] = {}
    for path in (KIND_FAMILIES_PATH, DIMENSIONS_PATH, RESOLVER_RULES_PATH, ATLAS_MANIFEST_PATH):
        fingerprints[path.relative_to(REPO_ROOT).as_posix()] = hashlib.sha256(
            path.read_bytes()).hexdigest()
    return fingerprints


def build_manifest(pack: dict[str, Any], generated_at: str = DEFAULT_GENERATED_AT) -> dict[str, Any]:
    row_counts = {name: len(rows) for name, rows in pack.items()}
    skip_counts_by_archetype: dict[str, int] = {a["archetype_id"]: 0 for a in ARCHETYPES}
    for skip in pack["compatibility_skips.jsonl"]:
        skip_counts_by_archetype[skip["archetype_ref"]] += 1
    kind_family_count = len({row["base_kind"] for row in pack["template_candidates.jsonl"]}
                            | {row["base_kind"] for row in pack["compatibility_skips.jsonl"]})
    return {
        "record_type": "primitive_template_seed_pack_manifest",
        "pack_id": PACK_ID,
        **BOUNDARY,
        "version": PACK_VERSION,
        "generator": "scripts/build_primitive_template_seed_pack.py",
        "generated_at": generated_at,
        "source_family": SOURCE_FAMILY,
        "source_status": SOURCE_STATUS,
        "evidence_status": EVIDENCE_STATUS,
        "boundary": "candidate=true; serves_truth=false; every template is a seed for later "
                    "instantiation + proof, never a promoted primitive",
        "materialization_rule": str(load_atlas_manifest()["materialization_rule"]),
        "files": {name.rsplit(".", 1)[0]: name for name in sorted(pack)},
        "file_count": len(pack),
        "row_counts": row_counts,
        "total_rows": sum(row_counts.values()),
        "content_sha256": hashlib.sha256(_canonical_bytes(pack)).hexdigest(),
        "archetype_count": len(ARCHETYPES),
        "kind_family_count": kind_family_count,
        "coherent_pair_count": len(pack["template_candidates.jsonl"]),
        "skipped_pair_count": len(pack["compatibility_skips.jsonl"]),
        "skip_counts_by_archetype": skip_counts_by_archetype,
        "minimum_template_rows": MINIMUM_TEMPLATE_ROWS,
        "input_fingerprints": _input_fingerprints(),
        "reuses": [
            KIND_FAMILIES_PATH.parent.relative_to(REPO_ROOT).as_posix(),
            DIMENSION_ATLAS_DIR.relative_to(REPO_ROOT).as_posix(),
        ],
    }


def write_pack(generated_at: str = DEFAULT_GENERATED_AT) -> dict[str, Any]:
    pack = build_pack()
    manifest = build_manifest(pack, generated_at)
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    for name, rows in pack.items():
        with (PACK_DIR / name).open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    (PACK_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


# ── Self test (in-memory; the checker re-verifies the pack ON DISK) ────────
def self_test() -> int:
    families = load_kind_families()
    dims_by_family = load_dimensions_by_family()
    resolver_rule_ids = load_resolver_rule_ids()
    domain_universe = {str(domain) for family in families for domain in family["domains"]}
    kind_universe = {str(family["primitive_kind"]) for family in families}
    all_dimension_ids = {dim for dims in dims_by_family.values() for dim in dims}

    assert len(ARCHETYPES) == 25, "the seed pack encodes ~25 edge-shape archetypes"
    assert set(RESOLVER_RULE_REFS) <= resolver_rule_ids, "resolver rule refs must exist in the atlas"
    for archetype in ARCHETYPES:
        aid = archetype["archetype_id"]
        slot_names = {slot["name"] for slot in archetype["slots"]}
        placeholders = set(PLACEHOLDER_PATTERN.findall(archetype["visible_edge"]))
        assert placeholders, f"{aid}: visible_edge must carry {{Slot}} placeholders"
        assert placeholders == slot_names, f"{aid}: placeholders {placeholders} != slots {slot_names}"
        assert set(archetype["slot_contracts"]) == slot_names, f"{aid}: slot_contracts must cover slots"
        assert " -> " in archetype["visible_edge"], f"{aid}: visible_edge needs input -> output"
        for slot in archetype["slots"]:
            assert slot["type"] in SLOT_TYPES, f"{aid}: unknown slot type {slot['type']!r}"
        assert len(archetype["failure_modes"]) >= 3, f"{aid}: needs >=3 known failure modes"
        assert archetype["proof_requirements"], f"{aid}: needs proof requirements"
        assert len(archetype["instantiation_templates"]) == 2, f"{aid}: needs 2 instantiation templates"
        for template in archetype["instantiation_templates"]:
            assert "{kind}" in template and "{task}" in template, f"{aid}: template placeholders"
        assert set(archetype["search_surfaces"]) <= set(SEARCH_SURFACES), f"{aid}: unknown search surface"
        for fam in archetype["dimension_families"]:
            assert fam in dims_by_family, f"{aid}: unknown atlas dimension family {fam!r}"
        compat = archetype["compatibility"]
        assert compat["mode"] in ("include", "exclude"), f"{aid}: bad compatibility mode"
        assert compat["skip_reason"], f"{aid}: compatibility needs a skip_reason"
        assert set(compat["domains"]) <= domain_universe, f"{aid}: unknown compatibility domain"
        assert set(compat["kinds"]) <= kind_universe, f"{aid}: unknown compatibility kind"

    pack = build_pack()
    manifest = build_manifest(pack)
    templates = pack["template_candidates.jsonl"]
    skips = pack["compatibility_skips.jsonl"]

    for name, rows in pack.items():
        for row in rows:
            assert row.get("candidate") is True and row.get("serves_truth") is False, \
                f"{name}: truth boundary violated"

    assert len(templates) >= MINIMUM_TEMPLATE_ROWS, \
        f"first rung needs >= {MINIMUM_TEMPLATE_ROWS} template rows, got {len(templates)}"
    assert len(templates) + len(skips) == len(ARCHETYPES) * len(families), \
        "coherent + skipped pairs must cover the full archetype x family grid"

    template_ids = [row["template_id"] for row in templates]
    assert len(template_ids) == len(set(template_ids)), "template_id must be unique"
    dedupe_keys = [row["dedupe_key"] for row in templates]
    assert len(dedupe_keys) == len(set(dedupe_keys)), "dedupe_key must be unique"

    covered_archetypes = {row["archetype_ref"] for row in templates}
    assert covered_archetypes == {a["archetype_id"] for a in ARCHETYPES}, \
        "every archetype must yield at least one template"
    covered_kinds = {row["base_kind"] for row in templates}
    assert covered_kinds == kind_universe, "every kind family must appear in at least one template"

    family_by_kind = {str(family["primitive_kind"]): family for family in families}
    for row in templates:
        assert set(row["variation_dimension_refs"]) <= all_dimension_ids, \
            f"{row['template_id']}: dimension ref does not resolve in the atlas"
        assert row["base_family_ref"] == str(family_by_kind[row["base_kind"]]["id"])
        assert "candidate_boundary_gate" in row["proof_requirements"]
        assert row["example_instantiations"] and row["known_failure_modes"]
        assert row["source_search_plan"]["queries"] and row["source_search_plan"]["surfaces"]
    for row in skips:
        assert row["skip_reason"], "every skip carries its curation reason"

    assert manifest["total_rows"] == sum(len(rows) for rows in pack.values())
    assert manifest["coherent_pair_count"] == len(templates)
    assert manifest["skipped_pair_count"] == len(skips)
    assert manifest["kind_family_count"] == len(families)
    assert sum(manifest["skip_counts_by_archetype"].values()) == len(skips)
    print(json.dumps({"pack_id": PACK_ID, "template_rows": len(templates),
                      "skipped_pairs": len(skips), "archetypes": len(ARCHETYPES),
                      "kind_families": len(families), "self_test": "ok"},
                     indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true",
                        help="validate the generated pack without writing")
    parser.add_argument("--write", action="store_true", help="write the pack + manifest to disk")
    parser.add_argument("--date", default=DEFAULT_GENERATED_AT,
                        help="generated_at date recorded ONLY in the manifest (YYYY-MM-DD)")
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    manifest = write_pack(generated_at=args.date)
    print(json.dumps({"pack_id": manifest["pack_id"], "files": manifest["file_count"],
                      "total_rows": manifest["total_rows"],
                      "template_rows": manifest["row_counts"]["template_candidates.jsonl"],
                      "skipped_pairs": manifest["skipped_pair_count"],
                      "content_sha256": manifest["content_sha256"]}, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
