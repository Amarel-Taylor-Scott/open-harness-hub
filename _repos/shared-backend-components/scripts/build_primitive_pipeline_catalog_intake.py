#!/usr/bin/env python3
"""Intake the owner-provided primitive/pipeline catalog into the factory lanes.

Source: ``primitive_pipeline_catalog_8000.md`` (owner-provided, repo root) — an
8,000-row / 24-column Markdown table of candidate primitive-group pipelines
(200 pipeline families x 20 industries x 2 runtime shapes).

This builder is the single source for four intake outputs (never hand-edit
them; rerun with ``--write``):

1. Lossless staged rows — every catalog row preserved as JSONL (raw layer).
2. Deterministic candidate cards — one deduped ``primitive_group`` card per
   unique (edge contract x pipeline family), in the exact shape
   ``_repos/shared-backend-components/scripts/verify_primitive_candidates.py`` verifies, written under the
   factory ``batch_runs`` layout so the standard verification loop consumes
   them. Zero model tokens: this lane is a deterministic parser.
3. Ollama lane shards — ``primitive_factory_shard`` rows so the GLM / Kimi /
   Gemma writers generate NEW member primitives and adjacent variants for the
   catalog families (not restatements).
4. Fable ultracode workflow briefs — shard briefs for Claude Fable workflow
   agents covering catalog decompositions plus the new place/facility/
   open-data/geospatial, entity-resolution, similarity/indexing, visual/math,
   rendering, algorithm, guardrail, and company-surface lanes.

All emitted rows stay ``candidate=true`` / ``serves_truth=false``; verification
never promotes truth.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    PRIMITIVE_CANDIDATE_OUTPUT_CONTRACT,
    PRIMITIVE_CANDIDATE_PROMPT_EXAMPLE_ROW,
    PRIMITIVE_FACTORY_BATCH_RUNS_DIR,
    REPO_ROOT,
)
from scripts.verify_primitive_candidates import ALLOWED_KINDS, GROUP_MIN_HIDDEN_EDGES, REQUIRED_FIELDS  # noqa: E402

CATALOG_SOURCE_PATH = "primitive_pipeline_catalog_8000.md"
INTAKE_ROOT_DIR = "data/dev-intel/primitive_factory/catalog_intake"
CATALOG_SHARDS_ROOT_DIR = "data/dev-intel/primitive_factory/daily_shards_catalog8k"
# Lane suffixes: <date-prefix>-c8kdet = deterministic parser lane,
# <date-prefix>-c8k1 = Ollama shard lane, <date-prefix>-uc02 = Fable workflow lane.
DETERMINISTIC_LANE_SUFFIX = "-c8kdet"
SHARD_LANE_SUFFIX = "-c8k1"
FABLE_LANE_SUFFIX = "-uc02"

CATALOG_COLUMNS = (
    "row_id",
    "primitive_group_id",
    "category",
    "pipeline_family",
    "industry",
    "use_case",
    "input_edge",
    "input_data_formats",
    "input_structure",
    "schema_or_standard",
    "start_to_finish_route",
    "output_edge",
    "output_formats",
    "runtime_shape",
    "known_implementations",
    "source_refs",
    "effects",
    "guardrails",
    "proof_requirements",
    "cache_key",
    "variation_dimensions",
    "evidence_level",
    "candidate",
    "serves_truth",
)

# Mirrors high_leverage_requirements.edge_description_min_chars in the live
# 20k factory shards so all lanes share one usefulness bar.
EDGE_DESCRIPTION_MIN_CHARS = 240
# Rank-hint only: rough output tokens a coding model avoids per hidden route
# step by reusing a compiled group instead of regenerating the pipeline.
STEP_SAVED_OUTPUT_TOKENS = 400
# Families per Ollama shard: keeps each shard prompt small enough for the
# 65536-token direct Ollama lanes while still giving variation room.
FAMILIES_PER_SHARD = 4
SHARD_RAW_CANDIDATE_TARGET = 100
SHARD_USEFUL_CANDIDATE_TARGET = 25
# Verifier-shape paragraph shared by every generation lane (adapted from the
# live daily_shards_20k writer prompts so all lanes pass the same gate).
VERIFIER_SHAPE_SPEC = (
    "Each row must pass this deterministic verifier shape exactly: kind is either primitive or "
    "primitive_group, never primitive-group; contract is a JSON object, never a string, with at least "
    "summary, input, output, and errors keys; edge_contract is a JSON object with input_edge_description, "
    "output_edge_description, preconditions, postconditions, failure_modes, and composition_notes; "
    "descriptions should explain what a downstream coding model needs to compile/link this primitive "
    "without seeing implementation internals; input_edge_description and output_edge_description should "
    f"each be at least {EDGE_DESCRIPTION_MIN_CHARS} characters when the route is non-trivial; "
    "edge_contract.composition_notes should contain concrete wiring guidance, adapter choices, idempotency "
    "or receipt handling, and what tests must run before reuse; blackbox is a concise string, not a "
    "boolean; effects is a non-empty array of objects with type and description; source_refs is a "
    "non-empty array of objects with label and url where url starts with https://; mutators is a "
    "non-empty array of strings or objects; proof_requirements is an array with at least two concrete "
    "tests; promotion_blockers is a non-empty array; dedupe_key is stable and edge-shaped. For "
    "kind=primitive_group, group_contract is required as an object with visible_input exactly equal to "
    "input_edge, visible_output exactly equal to output_edge, and hidden_member_edges containing at "
    f"least {GROUP_MIN_HIDDEN_EDGES} internal member edges; prefer at least 5 hidden member edges for "
    "high-leverage groups. Add reuse_profile as an object with reuse_class, estimated_saved_output_tokens, "
    "reusable_build_tasks, implementation_surfaces, compile_strategy, and linking_instructions. "
    "reuse_class should be one of multistep_coding_group, long_edge_contract, workflow_route_group, "
    "adapter_mutator_chain unless the row is deliberately atomic. Every row needs primitive_id, kind, "
    "title, input_edge, output_edge, input_edge_description, output_edge_description, edge_contract, "
    "contract, group_contract when applicable, blackbox, effects, source_refs, mutators, "
    "proof_requirements, promotion_blockers, reuse_profile, dedupe_key, candidate=true, serves_truth=false."
)

# Fable workflow briefs for lanes the catalog does NOT cover; seed refs are
# official public docs (the verifier requires public https source refs).
NEW_LANE_BRIEFS: tuple[dict[str, Any], ...] = (
    {
        "slug": "place-clinic-facility-discovery",
        "title": "Clinic and health-facility discovery, resolution, and coverage",
        "topics": [
            "HRSA health center ingestion", "NPPES provider identity resolution",
            "CMS provider data catalog adapters", "OSM healthcare feature extraction",
            "official-vs-open coverage comparison", "facility dedupe and conflict reports",
            "directory-only privacy boundary (no patient-level data)",
        ],
        "seed_source_refs": [
            {"label": "hrsa_data", "url": "https://data.hrsa.gov/"},
            {"label": "nppes_npi_registry", "url": "https://npiregistry.cms.hhs.gov/"},
            {"label": "cms_provider_data_catalog", "url": "https://data.cms.gov/provider-data/"},
            {"label": "osm_healthcare_key", "url": "https://wiki.openstreetmap.org/wiki/Key:healthcare"},
            {"label": "healthsites", "url": "https://healthsites.io/"},
        ],
        "base_edges": [
            "AreaOfInterest+ClinicSearchPolicy+SourcePreference -> ClinicCandidateSet+SourceEvidenceBundle",
            "HRSARecords+NPPESRecords+OSMHealthcareFeatures+MatchPolicy -> ResolvedClinicRegistry+ConflictReport+EvidenceBundle",
        ],
    },
    {
        "slug": "place-training-workforce-discovery",
        "title": "Training-provider and workforce-program discovery and gap analysis",
        "topics": [
            "CareerOneStop training provider adapters", "College Scorecard program adapters",
            "IPEDS postsecondary ingestion", "WIOA/ETPL eligibility surfaces",
            "occupation demand joins", "training desert / workforce gap reports",
        ],
        "seed_source_refs": [
            {"label": "careeronestop_api", "url": "https://www.careeronestop.org/Developers/WebAPI/web-api.aspx"},
            {"label": "college_scorecard_api", "url": "https://collegescorecard.ed.gov/data/api-documentation/"},
            {"label": "nces_ipeds", "url": "https://nces.ed.gov/ipeds/use-the-data"},
            {"label": "onet_web_services", "url": "https://services.onetcenter.org/"},
        ],
        "base_edges": [
            "OccupationOrSkill+AreaOfInterest+TrainingPolicy -> TrainingProgramCandidateSet+EvidenceBundle",
            "TrainingProgramSet+OccupationDemandDataset+RegionPolicy -> WorkforceTrainingGapReport+MapArtifacts",
        ],
    },
    {
        "slug": "place-open-data-portal-harvest",
        "title": "Open-government data portal discovery, harvest, and typed ingestion",
        "topics": [
            "CKAN package/resource harvest", "Socrata SODA ingestion",
            "ArcGIS FeatureServer layer ingestion", "OGC API Records catalog discovery",
            "dataset schema fingerprinting", "portal change monitoring", "license/attribution receipts",
        ],
        "seed_source_refs": [
            {"label": "ckan_api", "url": "https://docs.ckan.org/en/latest/api/"},
            {"label": "socrata_soda", "url": "https://dev.socrata.com/"},
            {"label": "arcgis_feature_service", "url": "https://developers.arcgis.com/rest/services-reference/enterprise/feature-service/"},
            {"label": "ogc_api_records", "url": "https://ogcapi.ogc.org/records/"},
            {"label": "data_gov", "url": "https://data.gov/developers/apis/"},
        ],
        "base_edges": [
            "PortalTarget+DirectedQuestion+DatasetHarvestPolicy -> DatasetCandidateSet+CatalogEvidenceReceipt",
            "DatasetResourceURL+IngestionPolicy+SchemaPolicy -> TypedDatasetArtifact+SchemaFingerprint+QualityReceipt",
        ],
    },
    {
        "slug": "geospatial-analysis-routes",
        "title": "Geospatial analysis: joins, isochrones, catchments, site selection",
        "topics": [
            "point-to-boundary spatial joins", "isochrone/service-area computation",
            "access-gap and catchment reports", "H3/S2 grid aggregation",
            "geocode policy gates (usage-policy compliant)", "ranked site selection with tradeoff reports",
            "map artifact generation with attribution receipts",
        ],
        "seed_source_refs": [
            {"label": "geopandas", "url": "https://geopandas.org/en/stable/"},
            {"label": "postgis", "url": "https://postgis.net/documentation/"},
            {"label": "osmnx", "url": "https://osmnx.readthedocs.io/en/stable/"},
            {"label": "osrm", "url": "https://project-osrm.org/"},
            {"label": "openrouteservice", "url": "https://openrouteservice.org/"},
            {"label": "h3", "url": "https://h3geo.org/"},
            {"label": "nominatim_usage_policy", "url": "https://operations.osmfoundation.org/policies/nominatim/"},
            {"label": "overture_docs", "url": "https://docs.overturemaps.org/"},
        ],
        "base_edges": [
            "FacilitySet+PopulationGeography+TravelPolicy -> AccessGapReport+ServiceAreaArtifacts",
            "CandidateSiteSet+DemandLayerSet+ConstraintPolicy+ScoringWeights -> RankedSiteList+TradeoffReport+EvidenceBundle",
        ],
    },
    {
        "slug": "entity-resolution-record-linkage",
        "title": "Entity resolution and record linkage routes",
        "topics": [
            "blocking rule generation/analysis", "comparison vectors and Fellegi-Sunter scoring",
            "threshold tuning and match explanation", "cluster-to-canonical-entity assignment",
            "clerical review packets", "leaf/block record processing", "false merge/split review",
        ],
        "seed_source_refs": [
            {"label": "splink_docs", "url": "https://moj-analytical-services.github.io/splink/index.html"},
            {"label": "splink_blocking", "url": "https://moj-analytical-services.github.io/splink/topic_guides/blocking/blocking_rules.html"},
            {"label": "bigquery_entity_resolution", "url": "https://docs.cloud.google.com/bigquery/docs/entity-resolution-intro"},
        ],
        "base_edges": [
            "RawRecordTable+BlockingRules+ComparisonSettings+ThresholdPolicy -> ClusteredEntityTable+MatchWeights+DiagnosticsReceipt",
            "LinkGraph+ClusterPolicy -> ConnectedComponents+CanonicalEntities+ExplainabilityPacket",
        ],
    },
    {
        "slug": "distance-similarity-indexing",
        "title": "Distance metrics, LSH/MinHash, and approximate nearest-neighbor indexing",
        "topics": [
            "distance primitive family (L1/L2/cosine/jaccard/levenshtein/haversine)",
            "MinHash/SimHash signatures and LSH indexes", "KDTree/BallTree leaf tuning",
            "HNSW/Faiss/PQ index selection", "blocking key generation", "recall@k and pair-reduction receipts",
        ],
        "seed_source_refs": [
            {"label": "datasketch_lsh", "url": "https://ekzhu.com/datasketch/lsh.html"},
            {"label": "sklearn_neighbors", "url": "https://scikit-learn.org/stable/modules/neighbors.html"},
            {"label": "faiss", "url": "https://faiss.ai/"},
        ],
        "base_edges": [
            "RecordBatch+ShingleOrEmbeddingPolicy -> SignatureSet+IndexBuildReceipt",
            "QuerySet+IndexRef+SearchPolicy -> CandidatePairSet+RecallLatencyReceipt",
        ],
    },
    {
        "slug": "math-formula-visualization",
        "title": "Math, formula, and animation visualization routes",
        "topics": [
            "formula-to-Manim scenes", "formula-to-three.js surfaces", "symbol ledger consistency",
            "parametric/vector-field/phase-portrait renders", "render smoke tests and visual diff receipts",
        ],
        "seed_source_refs": [
            {"label": "manim_docs", "url": "https://docs.manim.community/en/stable/"},
            {"label": "threejs_docs", "url": "https://threejs.org/docs/"},
            {"label": "nist_dlmf", "url": "https://dlmf.nist.gov/"},
        ],
        "base_edges": [
            "FormulaSpec+RenderPolicy -> ManimSceneArtifact+RenderSmokeReceipt",
            "EquationSet+SymbolLedgerPolicy -> ConsistencyReport+VisualSequenceArtifact",
        ],
    },
    {
        "slug": "rendering-game-graphics",
        "title": "Rendering, web-game, and ray-tracing systems routes",
        "topics": [
            "scene graph + camera + asset loading groups", "shader compile validation",
            "frame/draw-call/memory budget receipts", "BVH build/traverse and sampling primitives",
            "canvas non-blank and visual regression receipts",
        ],
        "seed_source_refs": [
            {"label": "raytracing_one_weekend", "url": "https://raytracing.github.io/"},
            {"label": "pbrt_book", "url": "https://pbr-book.org/4ed/contents"},
            {"label": "phaser_docs", "url": "https://docs.phaser.io/"},
            {"label": "webgpu_mdn", "url": "https://developer.mozilla.org/en-US/docs/Web/API/WebGPU_API"},
        ],
        "base_edges": [
            "SceneSpec+AssetManifest+RenderBudget -> RenderedFrameSet+FrameBudgetReceipt",
            "MeshSet+BvhPolicy -> BvhIndex+TraversalBenchmarkReceipt",
        ],
    },
    {
        "slug": "classical-algorithms-contracts",
        "title": "Classical algorithm and data-structure primitive contracts",
        "topics": [
            "sort/search/heap/union-find/graph traversal contracts", "segment/Fenwick tree groups",
            "property-based and cross-implementation proof receipts", "complexity receipts",
            "license-safe concept extraction (no protected text)",
        ],
        "seed_source_refs": [
            {"label": "cp_algorithms", "url": "https://cp-algorithms.com/"},
            {"label": "mit_ocw_6006", "url": "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-spring-2020/"},
        ],
        "base_edges": [
            "WeightedGraph+SourceNode+TargetNode+PathPolicy -> Path+CostReceipt",
            "SequenceBatch+OrderPolicy -> OrderedSequence+ComplexityReceipt",
        ],
    },
    {
        "slug": "guardrail-primitive-runtime",
        "title": "Cloud-agnostic guardrail primitives for prompts, RAG, tools, and outputs",
        "topics": [
            "prompt injection/jailbreak gates", "PII/secret redaction with receipts",
            "RAG source allowlist + citation-required gates", "tool-call schema/allowlist/approval gates",
            "decision receipt emitters", "provider adapters (Bedrock/Model Armor/Content Safety) behind ports",
        ],
        "seed_source_refs": [
            {"label": "bedrock_guardrails", "url": "https://docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html"},
            {"label": "gcp_model_armor", "url": "https://cloud.google.com/security-command-center/docs/model-armor-overview"},
            {"label": "azure_content_safety", "url": "https://learn.microsoft.com/en-us/azure/ai-services/content-safety/overview"},
            {"label": "open_policy_agent", "url": "https://www.openpolicyagent.org/docs/latest/"},
            {"label": "cedar_policy", "url": "https://docs.cedarpolicy.com/"},
        ],
        "base_edges": [
            "ProposedToolCall+UserContext+ToolPolicySet -> ToolCallDecision+GuardrailDecisionReceipt",
            "UserQuestion+RetrievedContextBundle+RagPolicySet -> SafeContextBundle+RagGuardrailReceipt",
        ],
    },
    {
        "slug": "company-surface-interrogation",
        "title": "Public-company surface interrogation primitives",
        "topics": [
            "SEC EDGAR submissions/companyfacts adapters", "XBRL metric panel extraction",
            "LEI/FIGI/NAICS identity joins", "company website structured-data extraction",
            "careers/job-posting skill demand extraction", "filing citation receipts",
        ],
        "seed_source_refs": [
            {"label": "sec_edgar_apis", "url": "https://www.sec.gov/search-filings/edgar-application-programming-interfaces"},
            {"label": "gleif_api", "url": "https://www.gleif.org/en/lei-data/gleif-api"},
            {"label": "openfigi_api", "url": "https://www.openfigi.com/api"},
            {"label": "census_naics", "url": "https://www.census.gov/naics/"},
            {"label": "schema_org_product", "url": "https://schema.org/Product"},
        ],
        "base_edges": [
            "CompanyCIK+XbrlConceptPolicy+PeriodPolicy -> FinancialMetricPanel+SourceBackedReceipt",
            "CompanyWebsitePage+SchemaOrgExtractionPolicy -> StructuredEntityCandidateSet+SourceSpanReceipt",
        ],
    },
)


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _today_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path)


def _sha(value: Any, *, n: int = 16) -> str:
    data = value if isinstance(value, str) else json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:n]


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return re.sub(r"-{2,}", "-", slug) or "family"


def _split_semicolon(value: str) -> list[str]:
    return [part.strip() for part in value.split(";") if part.strip()]


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def parse_catalog_rows(text: str) -> list[dict[str, str]]:
    """Parse the 24-column catalog table into row dicts (raw layer)."""
    rows: list[dict[str, str]] = []
    header_seen = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells:
            continue
        if cells[0] == "row_id":
            assert tuple(cell.strip() for cell in cells) == CATALOG_COLUMNS, (
                f"catalog header drifted: {cells[:6]}..."
            )
            header_seen = True
            continue
        if not re.fullmatch(r"\d{5}", cells[0] or ""):
            continue
        assert header_seen, "catalog data row appeared before the table header"
        assert len(cells) == len(CATALOG_COLUMNS), (
            f"row {cells[0]}: expected {len(CATALOG_COLUMNS)} columns, got {len(cells)}"
        )
        rows.append(dict(zip(CATALOG_COLUMNS, cells)))
    return rows


def _parse_source_refs(value: str) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for pair in _split_semicolon(value):
        label, _, url = pair.partition(":")
        label, url = label.strip(), url.strip()
        if url.startswith(("https://", "http://")):
            refs.append({"label": _slug(label), "url": url})
    return refs


def _hidden_member_edges(input_edge: str, route_steps: list[str], output_edge: str) -> list[str]:
    edges: list[str] = []
    previous = input_edge.split("+")[0].strip() or "InputEnvelope"
    for index, step in enumerate(route_steps):
        artifact = "".join(word.capitalize() for word in re.findall(r"[a-zA-Z0-9]+", step)) or f"Stage{index + 1}"
        artifact = f"{artifact}Artifact"
        edges.append(f"{previous} -> {artifact}")
        previous = artifact
    edges.append(f"{previous} -> {output_edge.split('+')[0].strip() or 'OutputArtifact'}")
    return edges


def build_deterministic_cards(rows: list[dict[str, str]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Dedupe catalog rows into unique family cards (derived layer, lossless)."""
    families: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for row in rows:
        key = _sha(
            "::".join((row["input_edge"].lower(), row["output_edge"].lower(), row["category"].lower(), row["pipeline_family"].lower()))
        )
        family = families.get(key)
        if family is None:
            family = {
                "key": key,
                "category": row["category"],
                "pipeline_family": row["pipeline_family"],
                "input_edge": row["input_edge"],
                "output_edge": row["output_edge"],
                "input_data_formats": row["input_data_formats"],
                "input_structure": row["input_structure"],
                "output_formats": row["output_formats"],
                "route_steps": _split_semicolon(row["start_to_finish_route"]),
                "cache_key": row["cache_key"],
                "evidence_level": row["evidence_level"],
                "industries": [],
                "runtime_shapes": [],
                "use_cases": [],
                "schemas": [],
                "implementations": [],
                "source_refs": {},
                "effects": [],
                "guardrails": [],
                "proof_requirements": [],
                "catalog_row_ids": [],
            }
            families[key] = family
            order.append(key)
        for field, column in (
            ("industries", "industry"),
            ("runtime_shapes", "runtime_shape"),
        ):
            if row[column] and row[column] not in family[field]:
                family[field].append(row[column])
        if row["use_case"] and row["use_case"] not in family["use_cases"]:
            family["use_cases"].append(row["use_case"])
        for field, column in (
            ("schemas", "schema_or_standard"),
            ("implementations", "known_implementations"),
            ("effects", "effects"),
            ("guardrails", "guardrails"),
            ("proof_requirements", "proof_requirements"),
        ):
            for item in _split_semicolon(row[column]):
                if item not in family[field]:
                    family[field].append(item)
        for ref in _parse_source_refs(row["source_refs"]):
            family["source_refs"].setdefault(ref["label"], ref["url"])
        family["catalog_row_ids"].append(row["row_id"])

    cards: list[dict[str, Any]] = []
    family_summaries: list[dict[str, Any]] = []
    for index, key in enumerate(order, start=1):
        family = families[key]
        family_slug = _slug(family["pipeline_family"])[:60]
        hidden_edges = _hidden_member_edges(family["input_edge"], family["route_steps"], family["output_edge"])
        kind = "primitive_group" if len(hidden_edges) >= GROUP_MIN_HIDDEN_EDGES else "primitive"
        industries_text = ", ".join(family["industries"][:20])
        input_description = (
            f"{family['input_edge']} — {family['use_cases'][0] if family['use_cases'] else family['pipeline_family']}. "
            f"Accepts {family['input_data_formats']} shaped as {family['input_structure']}, described by "
            f"{'; '.join(family['schemas'][:6])}. The same visible edge serves these industries via variation "
            f"overlays instead of per-industry forks: {industries_text}. Policy input selects schema mapping, "
            f"validation strictness, and runtime shape ({', '.join(family['runtime_shapes'])})."
        )
        output_description = (
            f"{family['output_edge']} — emits {family['output_formats']} plus a typed receipt recording row counts, "
            f"schema fingerprint, policy hash, and source lineage. Downstream consumers can rely on the receipt for "
            f"idempotent retries and audit. Proof obligations for this family: {'; '.join(family['proof_requirements'][:6])}. "
            f"Guardrails: {'; '.join(family['guardrails'][:5])}."
        )
        composition_notes = (
            f"Compile as a deterministic route: {' -> '.join(step for step in family['route_steps'][:8])}. "
            f"Cache key: {family['cache_key']}. Known implementation surfaces: {'; '.join(family['implementations'][:8])}. "
            f"Bind the runtime shape ({', '.join(family['runtime_shapes'])}) via a wrapper mutator, keep receipts "
            f"append-only, and run the family proof tests before reuse."
        )
        source_refs = [{"label": label, "url": url} for label, url in sorted(family["source_refs"].items())]
        card: dict[str, Any] = {
            "record_type": "primitive_candidate",
            "primitive_id": f"prim:c8k:{family_slug}:{index:03d}",
            "extracted_candidate_id": f"c8k:{family_slug}:{index:03d}",
            "kind": kind,
            "primitive_kind": f"pipeline.{_slug(family['category']).replace('-', '_')}",
            "title": f"{family['pipeline_family']} route group",
            "input_edge": family["input_edge"],
            "output_edge": family["output_edge"],
            "input_edge_description": input_description,
            "output_edge_description": output_description,
            "blackbox": (
                f"{family['pipeline_family']}: {family['input_edge']} -> {family['output_edge']}; deterministic "
                f"start-to-finish route ({len(family['route_steps'])} hidden steps) reused across "
                f"{len(family['industries'])} industries and {len(family['runtime_shapes'])} runtime shapes."
            ),
            "contract": {
                "summary": (
                    f"Deterministically runs the {family['pipeline_family']} route under an explicit policy and "
                    f"emits typed artifacts plus receipts; industry and runtime are variation overlays."
                ),
                "input": {
                    part.strip(): f"{part.strip()} component of the visible input edge ({family['input_data_formats']}; {family['input_structure']})"
                    for part in family["input_edge"].split("+")
                },
                "output": {
                    part.strip(): f"{part.strip()} component of the visible output edge ({family['output_formats']})"
                    for part in family["output_edge"].split("+")
                },
                "errors": ["SchemaValidationError", "SourceUnavailableError", "ContractViolationError"],
                "transformation_logic": [f"step {i + 1}: {step}" for i, step in enumerate(family["route_steps"])],
            },
            "edge_contract": {
                "input_edge_description": input_description,
                "output_edge_description": output_description,
                "preconditions": family["guardrails"][:6] or ["explicit policy provided"],
                "postconditions": ["typed output artifact emitted", "receipt with lineage and policy hash emitted"],
                "failure_modes": ["schema drift between source and policy", "silent row drops", "stale source snapshot"],
                "composition_notes": composition_notes,
            },
            "group_contract": {
                "visible_input": family["input_edge"],
                "visible_output": family["output_edge"],
                "hidden_member_edges": hidden_edges,
            } if kind == "primitive_group" else {},
            "features": family["guardrails"][:6],
            "reuse_profile": {
                "reuse_class": "workflow_route_group",
                "estimated_saved_output_tokens": len(family["route_steps"]) * STEP_SAVED_OUTPUT_TOKENS,
                "reusable_build_tasks": family["use_cases"][:3],
                "implementation_surfaces": family["implementations"][:8],
                "compile_strategy": "deterministic_template_fill",
                "linking_instructions": composition_notes,
                "reuse_frequency": "high",
                "typical_consumers": family["industries"][:10],
            },
            "effects": [
                {"type": effect, "description": f"{effect} declared by the catalog route contract."}
                for effect in family["effects"]
            ] or [{"type": "cpu_compute", "description": "pure transformation declared by the catalog route contract."}],
            "source_refs": source_refs,
            "mutators": ["runtime_shape_wrapper", "schema_overlay_binding", "output_wrapper"],
            "proof_requirements": sorted(set(family["proof_requirements"] + ["candidate_boundary_gate"])),
            "promotion_blockers": ["review_required", "implementation_evidence_required"],
            "promotion_status": "candidate",
            "dedupe_key": (
                f"{family['input_edge'].lower()}->{family['output_edge'].lower()}::{_slug(family['pipeline_family'])}"
            ),
            "variation_profile": {
                "industries": family["industries"],
                "runtime_shapes": family["runtime_shapes"],
                "catalog_row_ids": family["catalog_row_ids"],
                "evidence_level": family["evidence_level"],
            },
            "source_provider": "deterministic-catalog-intake",
            "source_model": "deterministic-parser",
            "candidate": True,
            "serves_truth": False,
        }
        if not card["group_contract"]:
            card.pop("group_contract")
        assert card["kind"] in ALLOWED_KINDS
        assert not source_refs or all(ref["url"].startswith(("https://", "http://")) for ref in source_refs)
        missing = [field for field in REQUIRED_FIELDS if field not in card or card[field] in ("", [], {})]
        assert not missing or missing == ["candidate", "serves_truth"], f"card missing {missing}"
        assert len(input_description) >= EDGE_DESCRIPTION_MIN_CHARS, f"input description too short for {family_slug}"
        assert len(output_description) >= EDGE_DESCRIPTION_MIN_CHARS, f"output description too short for {family_slug}"
        cards.append(card)
        family_summaries.append(
            {
                "family_key": key,
                "pipeline_family": family["pipeline_family"],
                "category": family["category"],
                "input_edge": family["input_edge"],
                "output_edge": family["output_edge"],
                "primitive_id": card["primitive_id"],
                "industry_count": len(family["industries"]),
                "runtime_shapes": family["runtime_shapes"],
                "catalog_row_count": len(family["catalog_row_ids"]),
                "source_refs": source_refs,
                "candidate": True,
                "serves_truth": False,
            }
        )
    return cards, family_summaries


def build_ollama_shards(family_summaries: list[dict[str, Any]], run_date: str) -> list[dict[str, Any]]:
    """Emit primitive_factory_shard rows so GLM/Kimi/Gemma writers expand the catalog families."""
    shards: list[dict[str, Any]] = []
    by_category: dict[str, list[dict[str, Any]]] = {}
    for summary in family_summaries:
        by_category.setdefault(summary["category"], []).append(summary)
    groups: list[tuple[str, list[dict[str, Any]]]] = []
    for category in sorted(by_category):
        members = by_category[category]
        for start in range(0, len(members), FAMILIES_PER_SHARD):
            groups.append((category, members[start : start + FAMILIES_PER_SHARD]))
    for shard_index, (category, members) in enumerate(groups, start=1):
        lane_id = f"catalog8k-{_slug(category)}"
        base_groups = [
            {
                "primitive_id": member["primitive_id"],
                "title": f"{member['pipeline_family']} route group",
                "input_edge": member["input_edge"],
                "output_edge": member["output_edge"],
            }
            for member in members
        ]
        ref_map: dict[str, str] = {}
        for member in members:
            for ref in member["source_refs"]:
                ref_map.setdefault(ref["label"], ref["url"])
        source_refs = [
            {"id": label, "title": label.replace("-", " "), "url": url} for label, url in sorted(ref_map.items())
        ][:10]
        base_lines = "; ".join(
            f"{group['primitive_id']}:{group['input_edge']}->{group['output_edge']}" for group in base_groups
        )
        source_lines = "; ".join(f"{ref['id']}={ref['url']}" for ref in source_refs)
        writer_prompt = (
            PRIMITIVE_CANDIDATE_OUTPUT_CONTRACT
            + "Generate source-backed primitive or primitive-group candidates as JSONL only. Start the response "
            "with a JSON object. Do not include markdown, prose, or analysis. Keep candidate=true and "
            f"serves_truth=false. Emit at least {SHARD_USEFUL_CANDIDATE_TARGET} useful rows for this shard; do "
            f"not emit more than {SHARD_RAW_CANDIDATE_TARGET} rows. Prefer compact primitive-group rows when a "
            "visible edge can hide 3+ member edges. These catalog pipeline families already exist as base "
            "groups — do NOT restate them; instead emit their hidden MEMBER primitives, deterministic mutators, "
            "schema/industry overlay variants, repair and receipt primitives, and adjacent routes the families "
            f"imply. Lane: {lane_id}. Sources: {source_lines}. Base groups: {base_lines}. {VERIFIER_SHAPE_SPEC} "
            + PRIMITIVE_CANDIDATE_PROMPT_EXAMPLE_ROW
        )
        reviewer_prompt = (
            "Review candidate primitive/group JSONL for missing source refs, weak visible edges, missing hidden "
            "member edges, missing proof requirements, duplicate edge shapes, and violations of this lane "
            "rejection policy: Reject records missing official source refs, visible input/output edges, or "
            "candidate=true/serves_truth=false boundary."
        )
        shard_id_body = f"pfs:{run_date.replace('-', '')}:{lane_id}:{shard_index:04d}"
        shards.append(
            {
                "record_type": "primitive_factory_shard",
                "run_date": run_date,
                "lane_id": lane_id,
                "lane_title": f"Catalog 8k {category} family expansion",
                "shard_id": f"{shard_id_body}:{_sha(shard_id_body, n=10)}",
                "shard_index": shard_index,
                "shard_count": len(groups),
                "status": "planned",
                "base_group_ids": [group["primitive_id"] for group in base_groups],
                "base_groups": base_groups,
                "source_ref_ids": [ref["id"] for ref in source_refs],
                "source_refs": source_refs,
                "candidate_writer_prompt": writer_prompt,
                "contract_reviewer_prompt": reviewer_prompt,
                "acceptance_criteria": [
                    "emit_jsonl_only",
                    "source_ref_resolution",
                    "visible_edge_contract",
                    "long_edge_descriptions_for_nontrivial_routes",
                    "reuse_profile_attached",
                    "high_leverage_primitive_groups_preferred",
                    "proof_plan_attached",
                    "dedupe_key_attached",
                    "candidate_true_serves_truth_false",
                ],
                "artifact_outputs": ["candidate_cards.jsonl", "proof_plans.jsonl", "review_findings.jsonl", "rejected.jsonl"],
                "auxiliary_model_roles": {"openwebui_gemma_candidate_writer": "gemma-4-coding"},
                "model_roles": {
                    "codex_orchestrator": "codex",
                    "deterministic_validator": "jsonl_schema_and_candidate_boundary_checks",
                    "glm_contract_reviewer": "glm-5.2",
                    "kimi_candidate_writer": "kimi-k2.7-code",
                },
                "deterministic_validators": [
                    "source_ref_resolution",
                    "json_schema_validation",
                    "dedupe_key_generation",
                    "candidate_boundary_gate",
                ],
                "high_leverage_requirements": {
                    "candidate": True,
                    "edge_description_min_chars": EDGE_DESCRIPTION_MIN_CHARS,
                    "preferred_group_min_hidden_edges": 5,
                    "reuse_classes": [
                        "multistep_coding_group",
                        "long_edge_contract",
                        "workflow_route_group",
                        "adapter_mutator_chain",
                    ],
                    "serves_truth": False,
                },
                "minimum_group_ratio": 0.75,
                "output_mix": {"primitive_candidate": 0.15, "primitive_group_candidate": 0.85},
                "proof_gates": [
                    "source_evidence_gate",
                    "contract_schema_gate",
                    "deterministic_factory_gate",
                    "fixture_or_property_test_gate",
                    "candidate_boundary_gate",
                ],
                "usefulness_gates": [
                    "source_ref_resolution",
                    "visible_edge_contract",
                    "hidden_member_edge_or_single_step_contract",
                    "proof_plan_attached",
                    "dedupe_key_attached",
                    "candidate_boundary_gate",
                ],
                "dedupe_namespace": _sha(f"{run_date}:{lane_id}"),
                "raw_candidate_target": SHARD_RAW_CANDIDATE_TARGET,
                "useful_candidate_target": SHARD_USEFUL_CANDIDATE_TARGET,
                "target_candidate_level": "L3_source_backed",
                "candidate": True,
                "serves_truth": False,
            }
        )
    return shards


def build_fable_briefs(family_summaries: list[dict[str, Any]], run_date: str) -> list[dict[str, Any]]:
    """Briefs for Claude Fable ultracode workflow agents: catalog decompositions + new lanes."""
    briefs: list[dict[str, Any]] = []
    by_category: dict[str, list[dict[str, Any]]] = {}
    for summary in family_summaries:
        by_category.setdefault(summary["category"], []).append(summary)
    for category in sorted(by_category):
        members = sorted(by_category[category], key=lambda item: -item["industry_count"])[:6]
        ref_map: dict[str, str] = {}
        for member in members:
            for ref in member["source_refs"]:
                ref_map.setdefault(ref["label"], ref["url"])
        briefs.append(
            {
                "brief_id": f"ucb:{run_date}:catalog-{_slug(category)}",
                "slug": f"catalog-{_slug(category)}",
                "title": f"Decompose catalog {category} families into member primitives",
                "lane": "catalog_decomposition",
                "topics": [
                    f"{member['pipeline_family']} ({member['input_edge']} -> {member['output_edge']})"
                    for member in members
                ],
                "seed_source_refs": [
                    {"label": label, "url": url} for label, url in sorted(ref_map.items())
                ][:10],
                "base_edges": [f"{member['input_edge']} -> {member['output_edge']}" for member in members],
                "target_rows": 30,
                "notes": (
                    "Emit hidden MEMBER primitives, deterministic mutators, receipt/repair primitives, and "
                    "high-value overlay variants for these existing base groups; do not restate the base groups."
                ),
                "candidate": True,
                "serves_truth": False,
            }
        )
    for lane in NEW_LANE_BRIEFS:
        briefs.append(
            {
                "brief_id": f"ucb:{run_date}:{lane['slug']}",
                "slug": lane["slug"],
                "title": lane["title"],
                "lane": "new_topic_lane",
                "topics": lane["topics"],
                "seed_source_refs": lane["seed_source_refs"],
                "base_edges": lane["base_edges"],
                "target_rows": 30,
                "notes": (
                    "New lane not covered by the catalog: emit primitive and primitive_group candidates with "
                    "public official source refs, receipts-first proof plans, and privacy/usage-policy gates "
                    "where relevant."
                ),
                "candidate": True,
                "serves_truth": False,
            }
        )
    return briefs


def run_intake(*, date_prefix: str, write: bool) -> dict[str, Any]:
    catalog_path = _resource(CATALOG_SOURCE_PATH)
    assert catalog_path.exists(), f"missing catalog source: {catalog_path}"
    text = catalog_path.read_text(encoding="utf-8")
    rows = parse_catalog_rows(text)
    assert rows, "no catalog rows parsed"
    cards, family_summaries = build_deterministic_cards(rows)
    shard_run_date = f"{date_prefix}{SHARD_LANE_SUFFIX}"
    deterministic_run_date = f"{date_prefix}{DETERMINISTIC_LANE_SUFFIX}"
    fable_run_date = f"{date_prefix}{FABLE_LANE_SUFFIX}"
    shards = build_ollama_shards(family_summaries, shard_run_date)
    briefs = build_fable_briefs(family_summaries, fable_run_date)

    intake_dir = _resource(INTAKE_ROOT_DIR) / shard_run_date
    batch_dir = _resource(PRIMITIVE_FACTORY_BATCH_RUNS_DIR) / deterministic_run_date / "catalog_deterministic" / "extracted"
    shards_dir = _resource(CATALOG_SHARDS_ROOT_DIR) / shard_run_date
    manifest = {
        "record_type": "primitive_pipeline_catalog_intake_manifest",
        "created_at": _now(),
        "source_path": CATALOG_SOURCE_PATH,
        "source_content_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "catalog_row_count": len(rows),
        "unique_family_count": len(cards),
        "category_counts": {
            category: sum(1 for summary in family_summaries if summary["category"] == category)
            for category in sorted({summary["category"] for summary in family_summaries})
        },
        "industry_count": len({row["industry"] for row in rows}),
        "runtime_shape_count": len({row["runtime_shape"] for row in rows}),
        "deterministic_lane": {
            "run_date": deterministic_run_date,
            "cards_path": _rel(batch_dir / "extracted_candidates.jsonl"),
            "card_count": len(cards),
        },
        "ollama_lane": {
            "run_date": shard_run_date,
            "shards_path": _rel(shards_dir / "shards.jsonl"),
            "shard_count": len(shards),
        },
        "fable_lane": {
            "run_date": fable_run_date,
            "briefs_path": _rel(intake_dir / "fable_briefs.json"),
            "brief_count": len(briefs),
        },
        "staged_rows_path": _rel(intake_dir / "catalog_rows_staged.jsonl"),
        "lossless_note": "Raw catalog rows are preserved verbatim in the staged JSONL; cards are a derived, deduped layer.",
        "candidate": True,
        "serves_truth": False,
    }
    if write:
        _write_jsonl(intake_dir / "catalog_rows_staged.jsonl", rows)
        _write_jsonl(batch_dir / "extracted_candidates.jsonl", cards)
        _write_jsonl(shards_dir / "shards.jsonl", shards)
        _write_json(
            shards_dir / "manifest.json",
            {
                "record_type": "primitive_factory_catalog_shards_manifest",
                "created_at": _now(),
                "run_date": shard_run_date,
                "shard_count": len(shards),
                "source_manifest": _rel(intake_dir / "manifest.json"),
                "candidate": True,
                "serves_truth": False,
            },
        )
        _write_json(intake_dir / "fable_briefs.json", {"record_type": "fable_ultracode_briefs", "run_date": fable_run_date, "briefs": briefs, "candidate": True, "serves_truth": False})
        _write_json(intake_dir / "manifest.json", manifest)
    return manifest


SELF_TEST_TABLE = """
| row_id | primitive_group_id | category | pipeline_family | industry | use_case | input_edge | input_data_formats | input_structure | schema_or_standard | start_to_finish_route | output_edge | output_formats | runtime_shape | known_implementations | source_refs | effects | guardrails | proof_requirements | cache_key | variation_dimensions | evidence_level | candidate | serves_truth |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 00001 | grp:test.family.a@candidate:aa | data_engineering | Test ingest family | Healthcare | Load records into analytics tables for testing operators with realistic long descriptions | RawFileBatch+SchemaPolicy | CSV/JSONL | wide_table | JSON Schema; FHIR | discover files; infer schema; validate required fields; load staging; publish table; emit receipt | ValidatedTable+LoadReceipt | warehouse_table | airflow.dag | pandas; dbt | pandas:https://pandas.pydata.org/docs/; dbt:https://docs.getdbt.com/ | file_read; database_write | no silent row drops; source hash required | schema_fixture_test; row_count_check | source_hash+schema_hash | industry=Healthcare | plausible_candidate | true | false |
| 00002 | grp:test.family.a.spark@candidate:bb | data_engineering | Test ingest family | Financial Services | Load records into analytics tables for testing operators with realistic long descriptions | RawFileBatch+SchemaPolicy | CSV/JSONL | wide_table | JSON Schema; XBRL | discover files; infer schema; validate required fields; load staging; publish table; emit receipt | ValidatedTable+LoadReceipt | warehouse_table | spark_job | Spark | spark:https://spark.apache.org/docs/latest/ | file_read; database_write | no silent row drops | schema_fixture_test | source_hash+schema_hash | industry=Financial Services | plausible_candidate | true | false |
"""


def self_test() -> None:
    rows = parse_catalog_rows(SELF_TEST_TABLE)
    assert len(rows) == 2, f"expected 2 synthetic rows, got {len(rows)}"
    cards, summaries = build_deterministic_cards(rows)
    assert len(cards) == 1, "same edge+family must dedupe to one card"
    card = cards[0]
    assert card["kind"] == "primitive_group"
    assert len(card["group_contract"]["hidden_member_edges"]) >= GROUP_MIN_HIDDEN_EDGES
    assert card["variation_profile"]["industries"] == ["Healthcare", "Financial Services"]
    assert card["variation_profile"]["runtime_shapes"] == ["airflow.dag", "spark_job"]
    assert all(ref["url"].startswith("https://") for ref in card["source_refs"])
    missing = [field for field in REQUIRED_FIELDS if field not in card]
    assert not missing, f"missing required fields: {missing}"
    assert card["candidate"] is True and card["serves_truth"] is False
    shards = build_ollama_shards(summaries, "2000-01-01-c8k1")
    assert len(shards) == 1
    shard = shards[0]
    for key in ("candidate_writer_prompt", "base_groups", "source_refs", "dedupe_namespace", "shard_id"):
        assert shard.get(key), f"shard missing {key}"
    assert "do NOT restate" in shard["candidate_writer_prompt"]
    briefs = build_fable_briefs(summaries, "2000-01-01-uc02")
    assert len(briefs) == 1 + len(NEW_LANE_BRIEFS)
    assert all(brief["seed_source_refs"] for brief in briefs)
    real_catalog = _resource(CATALOG_SOURCE_PATH)
    if real_catalog.exists():
        real_rows = parse_catalog_rows(real_catalog.read_text(encoding="utf-8"))
        assert len(real_rows) >= 1000, f"real catalog unexpectedly small: {len(real_rows)} rows"
        real_cards, real_summaries = build_deterministic_cards(real_rows)
        assert real_cards, "real catalog produced no cards"
        assert all(card["candidate"] is True and card["serves_truth"] is False for card in real_cards)
        group_count = sum(1 for card in real_cards if card["kind"] == "primitive_group")
        assert group_count >= len(real_cards) // 2, "expected mostly primitive_group cards"
        assert build_ollama_shards(real_summaries, "2000-01-01-c8k1"), "real catalog produced no shards"
    print(
        "OK: primitive pipeline catalog intake self-test passed "
        f"(parse, dedupe, verifier-shape cards, shards, {1 + len(NEW_LANE_BRIEFS)} synthetic briefs)."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date-prefix", default=_today_utc(), help="Factory day label, e.g. 2026-07-01.")
    parser.add_argument("--write", action="store_true", help="Write staged rows, cards, shards, and briefs.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    manifest = run_intake(date_prefix=args.date_prefix, write=args.write)
    print(json.dumps(manifest, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
