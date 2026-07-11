"""AIDevObserver runtime settings.

This is the single source for observer hot-path thresholds that affect
product behavior. Protocol constants and self-test fixtures may still live in
their owning modules, but review/search/capture limits should route through
this file so tuning does not become a grep-and-guess exercise.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from scripts._config import (
    AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_CARDS_PATH,
    AIDEVEXPLORER_PRIMITIVE_KIND_CARDS_PATH,
    AIDEVEXPLORER_RUNTIME_SHAPE_PRIMITIVE_CARDS_PATH,
    AIDEVOBSERVER_CURATED_PRIMITIVE_GROUPS_PATH,
    AIDEVOBSERVER_IMPLEMENTED_CODE_PRIMITIVES_PATH,
    AIDEVOBSERVER_SOURCE_BACKED_GROUP_CARDS_PATH,
    AIDEVOBSERVER_SOURCE_BACKED_GROUP_PROMOTION_GATES_PATH,
    AIDEVOBSERVER_SOURCE_BACKED_GROUP_PROOF_BUNDLES_PATH,
    PRIMITIVE_QUALITY_ARTIFACT_FILES,
    PRIMITIVE_QUALITY_CLASS_HIGH_VALUE,
    PRIMITIVE_QUALITY_CLASS_HOLD,
    PRIMITIVE_QUALITY_CLASS_NOISE,
    PRIMITIVE_QUALITY_CLASS_SURFACEABLE,
    PRIMITIVE_QUALITY_DIRNAME,
    PRIMITIVE_QUALITY_HIGH_VALUE_MIN_SCORE,
    PRIMITIVE_QUALITY_SURFACEABLE_MIN_SCORE,
    PRIMITIVE_REGISTRY_OPERATIONAL_CSV_DIR,
    REPO_ROOT,
)


DEFAULT_SURFACEABLE_PRIMITIVES_PATH = (
    f".agent/primitive-registry/{PRIMITIVE_QUALITY_DIRNAME}/"
    f"{PRIMITIVE_QUALITY_ARTIFACT_FILES['surfaceable']}"
)
DEFAULT_OPERATIONAL_PRIMITIVE_QUALITY_CSV_PATH = str(
    (PRIMITIVE_REGISTRY_OPERATIONAL_CSV_DIR / "primitive_quality_assessment.csv").relative_to(REPO_ROOT)
)
DEFAULT_OPERATIONAL_REGISTRY_RECORD_CSV_PATH = str(
    (PRIMITIVE_REGISTRY_OPERATIONAL_CSV_DIR / "registry_record.csv").relative_to(REPO_ROOT)
)
DEFAULT_OPERATIONAL_PRIMITIVE_BLOCKING_KEY_CSV_PATH = str(
    (PRIMITIVE_REGISTRY_OPERATIONAL_CSV_DIR / "primitive_blocking_key.csv").relative_to(REPO_ROOT)
)
EDGE_FOUNDRY_PRIMITIVES_ENABLED_ENV = "OH_OBSERVER_EDGE_FOUNDRY_PRIMITIVES_ENABLED"
EDGE_FOUNDRY_PRIMITIVES_PATH_ENV = "OH_OBSERVER_EDGE_FOUNDRY_PRIMITIVES_PATH"
CURATED_PRIMITIVE_GROUPS_PATH_ENV = "OH_OBSERVER_CURATED_PRIMITIVE_GROUPS_PATH"
RUNTIME_SHAPE_PRIMITIVE_CARDS_PATH_ENV = "OH_OBSERVER_RUNTIME_SHAPE_PRIMITIVE_CARDS_PATH"
PRIMITIVE_KIND_CARDS_PATH_ENV = "OH_OBSERVER_PRIMITIVE_KIND_CARDS_PATH"
BENCHMARK_DECOMPOSITION_CARDS_PATH_ENV = "OH_OBSERVER_BENCHMARK_DECOMPOSITION_CARDS_PATH"
SOURCE_BACKED_GROUP_CARDS_PATH_ENV = "OH_OBSERVER_SOURCE_BACKED_GROUP_CARDS_PATH"
SOURCE_BACKED_GROUP_PROOF_BUNDLES_PATH_ENV = "OH_OBSERVER_SOURCE_BACKED_GROUP_PROOF_BUNDLES_PATH"
SOURCE_BACKED_GROUP_PROMOTION_GATES_PATH_ENV = "OH_OBSERVER_SOURCE_BACKED_GROUP_PROMOTION_GATES_PATH"
IMPLEMENTED_CODE_PRIMITIVES_PATH_ENV = "OH_OBSERVER_IMPLEMENTED_CODE_PRIMITIVES_PATH"
VERIFIED_FACTORY_CARDS_PATH_ENV = "OH_OBSERVER_VERIFIED_FACTORY_CARDS_PATH"
DEFAULT_EDGE_FOUNDRY_PRIMITIVES_PATH = (
    "data/dev-intel/aidevobserver_edge_foundry/primitive_edge_cards.jsonl"
)
DEFAULT_CURATED_PRIMITIVE_GROUPS_PATH = AIDEVOBSERVER_CURATED_PRIMITIVE_GROUPS_PATH
DEFAULT_RUNTIME_SHAPE_PRIMITIVE_CARDS_PATH = AIDEVEXPLORER_RUNTIME_SHAPE_PRIMITIVE_CARDS_PATH
DEFAULT_PRIMITIVE_KIND_CARDS_PATH = AIDEVEXPLORER_PRIMITIVE_KIND_CARDS_PATH
DEFAULT_BENCHMARK_DECOMPOSITION_CARDS_PATH = AIDEVEXPLORER_BENCHMARK_DECOMPOSITION_CARDS_PATH
DEFAULT_SOURCE_BACKED_GROUP_CARDS_PATH = AIDEVOBSERVER_SOURCE_BACKED_GROUP_CARDS_PATH
DEFAULT_SOURCE_BACKED_GROUP_PROOF_BUNDLES_PATH = AIDEVOBSERVER_SOURCE_BACKED_GROUP_PROOF_BUNDLES_PATH
DEFAULT_SOURCE_BACKED_GROUP_PROMOTION_GATES_PATH = AIDEVOBSERVER_SOURCE_BACKED_GROUP_PROMOTION_GATES_PATH
DEFAULT_IMPLEMENTED_CODE_PRIMITIVES_PATH = AIDEVOBSERVER_IMPLEMENTED_CODE_PRIMITIVES_PATH
#: verified factory primitives bridged into the searchable registry by
#: _repos/shared-backend-components/scripts/load_verified_candidates_into_registry.py (closes the verified_candidates/* -> registry gap).
DEFAULT_VERIFIED_FACTORY_CARDS_PATH = (
    "data/dev-intel/aidevobserver_edge_foundry/verified_factory_primitive_cards.jsonl"
)


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass(frozen=True, slots=True)
class ObserverRouterSettings:
    """Thresholds for route_session review/live scoring."""

    live_budget: int = field(default_factory=lambda: _env_int("OH_OBSERVER_LIVE_BUDGET", 3))
    chars_per_token: int = field(default_factory=lambda: _env_int("OH_OBSERVER_CHARS_PER_TOKEN", 4))
    oversized_tokens: int = field(default_factory=lambda: _env_int("OH_OBSERVER_OVERSIZED_TOKENS", 8000))
    duplicate_prefix_chars: int = field(default_factory=lambda: _env_int("OH_OBSERVER_DUP_PREFIX_CHARS", 200))
    duplicate_min_tokens: int = field(default_factory=lambda: _env_int("OH_OBSERVER_DUP_MIN_TOKENS", 200))
    reinvention_confidence: float = field(default_factory=lambda: _env_float("OH_OBSERVER_CONF_REINVENTION", 0.8))
    oversized_confidence: float = field(default_factory=lambda: _env_float("OH_OBSERVER_CONF_OVERSIZED", 0.55))
    duplicate_confidence: float = field(default_factory=lambda: _env_float("OH_OBSERVER_CONF_DUPLICATE", 0.7))
    stack_confidence: float = field(default_factory=lambda: _env_float("OH_OBSERVER_CONF_STACK", 0.82))
    ml_competition_confidence: float = field(default_factory=lambda: _env_float("OH_OBSERVER_CONF_ML_COMPETITION", 0.84))
    manual_context_waste_confidence: float = field(default_factory=lambda: _env_float("OH_OBSERVER_CONF_MANUAL_CONTEXT_WASTE", 0.68))
    shortcut_repeat: int = field(default_factory=lambda: _env_int("OH_OBSERVER_SHORTCUT_REPEAT", 4))
    per_type_floor: float = field(default_factory=lambda: _env_float("OH_OBSERVER_PER_TYPE_FLOOR", 0.5))


@dataclass(frozen=True, slots=True)
class ObserverCaptureSettings:
    """Transcript capture truncation limits."""

    tool_input_head_chars: int = field(default_factory=lambda: _env_int("OH_OBSERVER_TOOL_INPUT_HEAD_CHARS", 240))
    tool_result_multiplier: int = field(default_factory=lambda: _env_int("OH_OBSERVER_TOOL_RESULT_MULTIPLIER", 8))


@dataclass(frozen=True, slots=True)
class ObserverHookSettings:
    """Live hook context limits."""

    transcript_tail_events: int = field(default_factory=lambda: _env_int("OH_OBSERVER_HOOK_TRANSCRIPT_TAIL", 12))
    max_synthesized_content_chars: int = field(default_factory=lambda: _env_int("OH_OBSERVER_HOOK_MAX_CONTENT_CHARS", 2000))


@dataclass(frozen=True, slots=True)
class ObserverLocalRegistrySettings:
    """Local source-ref connector limits and scoring knobs."""

    max_indexed_files: int = field(default_factory=lambda: _env_int("OH_OBSERVER_LOCAL_MAX_INDEXED_FILES", 20000))
    max_doc_chars: int = field(default_factory=lambda: _env_int("OH_OBSERVER_LOCAL_MAX_DOC_CHARS", 4000))
    max_snippet_chars: int = field(default_factory=lambda: _env_int("OH_OBSERVER_LOCAL_MAX_SNIPPET_CHARS", 360))
    max_search_results: int = field(default_factory=lambda: _env_int("OH_OBSERVER_LOCAL_MAX_SEARCH_RESULTS", 10))
    max_primitive_candidates: int = field(default_factory=lambda: _env_int("OH_OBSERVER_LOCAL_MAX_PRIMITIVE_CANDIDATES", 20000))
    min_search_score: int = field(default_factory=lambda: _env_int("OH_OBSERVER_LOCAL_MIN_SEARCH_SCORE", 2))
    record_id_slug_chars: int = field(default_factory=lambda: _env_int("OH_OBSERVER_LOCAL_RECORD_ID_SLUG_CHARS", 120))
    hash_digest_chars: int = field(default_factory=lambda: _env_int("OH_OBSERVER_LOCAL_HASH_DIGEST_CHARS", 24))
    annotation_chars: int = field(default_factory=lambda: _env_int("OH_OBSERVER_LOCAL_ANNOTATION_CHARS", 120))
    exact_name_score_boost: int = field(default_factory=lambda: _env_int("OH_OBSERVER_LOCAL_EXACT_NAME_SCORE_BOOST", 3))
    path_score_boost: int = field(default_factory=lambda: _env_int("OH_OBSERVER_LOCAL_PATH_SCORE_BOOST", 2))
    callable_parse_score_boost: int = field(default_factory=lambda: _env_int("OH_OBSERVER_LOCAL_CALLABLE_PARSE_SCORE_BOOST", 2))
    constant_score_boost: int = field(default_factory=lambda: _env_int("OH_OBSERVER_LOCAL_CONSTANT_SCORE_BOOST", 3))
    command_score_boost: int = field(default_factory=lambda: _env_int("OH_OBSERVER_LOCAL_COMMAND_SCORE_BOOST", 3))
    edge_exact_score_boost: int = field(default_factory=lambda: _env_int("OH_OBSERVER_LOCAL_EDGE_EXACT_SCORE_BOOST", 8))
    edge_mutation_score_boost: int = field(default_factory=lambda: _env_int("OH_OBSERVER_LOCAL_EDGE_MUTATION_SCORE_BOOST", 5))
    edge_query_mutation_score_boost: int = field(default_factory=lambda: _env_int("OH_OBSERVER_LOCAL_EDGE_QUERY_MUTATION_SCORE_BOOST", 2))
    default_kind_priority: int = field(default_factory=lambda: _env_int("OH_OBSERVER_LOCAL_DEFAULT_KIND_PRIORITY", 99))
    index_cache_ttl_seconds: int = field(default_factory=lambda: _env_int("OH_OBSERVER_LOCAL_INDEX_CACHE_TTL_SECONDS", 30))
    index_cache_max_roots: int = field(default_factory=lambda: _env_int("OH_OBSERVER_LOCAL_INDEX_CACHE_MAX_ROOTS", 8))


@dataclass(frozen=True, slots=True)
class ObserverGlobalPrimitiveSettings:
    """Global primitive quality-file search settings.

    This searches only quality-promoted candidate cards, never raw broad
    symbol-level rows. It is safe for public demos because it reads generated
    registry artifacts rather than machine-local project paths.
    """

    enabled: int = field(default_factory=lambda: _env_int("OH_OBSERVER_GLOBAL_PRIMITIVES_ENABLED", 1))
    surfaceable_path: str = field(default_factory=lambda: os.environ.get(
        "OH_OBSERVER_SURFACEABLE_PRIMITIVES_PATH",
        DEFAULT_SURFACEABLE_PRIMITIVES_PATH,
    ))
    default_limit: int = field(default_factory=lambda: _env_int("OH_OBSERVER_GLOBAL_PRIMITIVE_DEFAULT_LIMIT", 8))
    review_hit_limit: int = field(default_factory=lambda: _env_int("OH_OBSERVER_GLOBAL_PRIMITIVE_REVIEW_HIT_LIMIT", 3))
    min_score: int = field(default_factory=lambda: _env_int("OH_OBSERVER_GLOBAL_PRIMITIVE_MIN_SCORE", 3))
    exact_term_score: int = field(default_factory=lambda: _env_int("OH_OBSERVER_GLOBAL_PRIMITIVE_EXACT_TERM_SCORE", 4))
    identifier_score: int = field(default_factory=lambda: _env_int("OH_OBSERVER_GLOBAL_PRIMITIVE_IDENTIFIER_SCORE", 3))
    domain_score: int = field(default_factory=lambda: _env_int("OH_OBSERVER_GLOBAL_PRIMITIVE_DOMAIN_SCORE", 2))
    edge_score: int = field(default_factory=lambda: _env_int("OH_OBSERVER_GLOBAL_PRIMITIVE_EDGE_SCORE", 3))
    proof_intent_boost: int = field(default_factory=lambda: _env_int("OH_OBSERVER_GLOBAL_PRIMITIVE_PROOF_INTENT_BOOST", 30))
    operational_enabled: int = field(default_factory=lambda: _env_int("OH_OBSERVER_OPERATIONAL_PRIMITIVES_ENABLED", 1))
    operational_quality_csv_path: str = field(default_factory=lambda: os.environ.get(
        "OH_OBSERVER_OPERATIONAL_PRIMITIVE_QUALITY_CSV_PATH",
        DEFAULT_OPERATIONAL_PRIMITIVE_QUALITY_CSV_PATH,
    ))
    operational_registry_record_csv_path: str = field(default_factory=lambda: os.environ.get(
        "OH_OBSERVER_OPERATIONAL_REGISTRY_RECORD_CSV_PATH",
        DEFAULT_OPERATIONAL_REGISTRY_RECORD_CSV_PATH,
    ))
    operational_blocking_key_csv_path: str = field(default_factory=lambda: os.environ.get(
        "OH_OBSERVER_OPERATIONAL_PRIMITIVE_BLOCKING_KEY_CSV_PATH",
        DEFAULT_OPERATIONAL_PRIMITIVE_BLOCKING_KEY_CSV_PATH,
    ))
    operational_min_quality_score: int = field(default_factory=lambda: _env_int(
        "OH_OBSERVER_OPERATIONAL_PRIMITIVE_MIN_QUALITY_SCORE",
        PRIMITIVE_QUALITY_HIGH_VALUE_MIN_SCORE,
    ))
    operational_surfaceable_quality_class: str = PRIMITIVE_QUALITY_CLASS_SURFACEABLE
    operational_high_value_quality_class: str = PRIMITIVE_QUALITY_CLASS_HIGH_VALUE
    operational_noise_quality_class: str = PRIMITIVE_QUALITY_CLASS_NOISE
    operational_hold_quality_class: str = PRIMITIVE_QUALITY_CLASS_HOLD
    operational_surfaceable_boost: int = field(default_factory=lambda: _env_int(
        "OH_OBSERVER_OPERATIONAL_PRIMITIVE_SURFACEABLE_BOOST",
        PRIMITIVE_QUALITY_SURFACEABLE_MIN_SCORE // 4,
    ))
    operational_high_value_boost: int = field(default_factory=lambda: _env_int(
        "OH_OBSERVER_OPERATIONAL_PRIMITIVE_HIGH_VALUE_BOOST",
        PRIMITIVE_QUALITY_HIGH_VALUE_MIN_SCORE // 5,
    ))
    operational_per_key_candidate_limit: int = field(default_factory=lambda: _env_int(
        "OH_OBSERVER_OPERATIONAL_PRIMITIVE_PER_KEY_LIMIT",
        80,
    ))
    operational_candidate_pool_limit: int = field(default_factory=lambda: _env_int(
        "OH_OBSERVER_OPERATIONAL_PRIMITIVE_CANDIDATE_POOL_LIMIT",
        360,
    ))
    edge_foundry_enabled: int = field(default_factory=lambda: _env_int(EDGE_FOUNDRY_PRIMITIVES_ENABLED_ENV, 1))
    edge_foundry_path: str = field(default_factory=lambda: os.environ.get(
        EDGE_FOUNDRY_PRIMITIVES_PATH_ENV,
        DEFAULT_EDGE_FOUNDRY_PRIMITIVES_PATH,
    ))
    curated_groups_path: str = field(default_factory=lambda: os.environ.get(
        CURATED_PRIMITIVE_GROUPS_PATH_ENV,
        DEFAULT_CURATED_PRIMITIVE_GROUPS_PATH,
    ))
    runtime_shape_cards_path: str = field(default_factory=lambda: os.environ.get(
        RUNTIME_SHAPE_PRIMITIVE_CARDS_PATH_ENV,
        DEFAULT_RUNTIME_SHAPE_PRIMITIVE_CARDS_PATH,
    ))
    primitive_kind_cards_path: str = field(default_factory=lambda: os.environ.get(
        PRIMITIVE_KIND_CARDS_PATH_ENV,
        DEFAULT_PRIMITIVE_KIND_CARDS_PATH,
    ))
    benchmark_decomposition_cards_path: str = field(default_factory=lambda: os.environ.get(
        BENCHMARK_DECOMPOSITION_CARDS_PATH_ENV,
        DEFAULT_BENCHMARK_DECOMPOSITION_CARDS_PATH,
    ))
    source_backed_group_cards_path: str = field(default_factory=lambda: os.environ.get(
        SOURCE_BACKED_GROUP_CARDS_PATH_ENV,
        DEFAULT_SOURCE_BACKED_GROUP_CARDS_PATH,
    ))
    source_backed_group_proof_bundles_path: str = field(default_factory=lambda: os.environ.get(
        SOURCE_BACKED_GROUP_PROOF_BUNDLES_PATH_ENV,
        DEFAULT_SOURCE_BACKED_GROUP_PROOF_BUNDLES_PATH,
    ))
    source_backed_group_promotion_gates_path: str = field(default_factory=lambda: os.environ.get(
        SOURCE_BACKED_GROUP_PROMOTION_GATES_PATH_ENV,
        DEFAULT_SOURCE_BACKED_GROUP_PROMOTION_GATES_PATH,
    ))
    implemented_code_primitives_path: str = field(default_factory=lambda: os.environ.get(
        IMPLEMENTED_CODE_PRIMITIVES_PATH_ENV,
        DEFAULT_IMPLEMENTED_CODE_PRIMITIVES_PATH,
    ))
    verified_factory_cards_path: str = field(default_factory=lambda: os.environ.get(
        VERIFIED_FACTORY_CARDS_PATH_ENV,
        DEFAULT_VERIFIED_FACTORY_CARDS_PATH,
    ))


@dataclass(frozen=True, slots=True)
class ObserverServiceSettings:
    """HTTP service and review-enrichment limits."""

    max_body_bytes: int = field(default_factory=lambda: _env_int("OH_OBSERVER_MAX_BODY_BYTES", 4 * 1024 * 1024))
    safe_id_max_chars: int = field(default_factory=lambda: _env_int("OH_OBSERVER_SAFE_ID_MAX_CHARS", 128))
    session_id_max_chars: int = field(default_factory=lambda: _env_int("OH_OBSERVER_SESSION_ID_MAX_CHARS", 96))
    digest_chars: int = field(default_factory=lambda: _env_int("OH_OBSERVER_DIGEST_CHARS", 16))
    local_registry_default_limit: int = field(default_factory=lambda: _env_int("OH_OBSERVER_LOCAL_REGISTRY_DEFAULT_LIMIT", 8))
    local_review_hit_limit: int = field(default_factory=lambda: _env_int("OH_OBSERVER_LOCAL_REVIEW_HIT_LIMIT", 3))
    outcome_memory_files: int = field(default_factory=lambda: _env_int("OH_OBSERVER_OUTCOME_MEMORY_FILES", 500))
    outcome_memory_deltas: dict[str, int] = field(default_factory=lambda: {
        "accepted": _env_int("OH_OBSERVER_OUTCOME_ACCEPTED_DELTA", 2),
        "reused": _env_int("OH_OBSERVER_OUTCOME_REUSED_DELTA", 4),
        "dismissed": _env_int("OH_OBSERVER_OUTCOME_DISMISSED_DELTA", -4),
        "ignored": _env_int("OH_OBSERVER_OUTCOME_IGNORED_DELTA", -1),
    })


@dataclass(frozen=True, slots=True)
class ObserverSessionStoreSettings:
    """Local outcome/session-store truncation limits."""

    content_id_digest_chars: int = field(default_factory=lambda: _env_int("OH_OBSERVER_SESSION_DIGEST_CHARS", 16))
    event_payload_chars: int = field(default_factory=lambda: _env_int("OH_OBSERVER_SESSION_EVENT_PAYLOAD_CHARS", 2000))
    recent_files: int = field(default_factory=lambda: _env_int("OH_OBSERVER_SESSION_RECENT_FILES", 500))


@dataclass(frozen=True, slots=True)
class ObserverSavingsSettings:
    """Transparent token-savings estimate defaults.

    These are intentionally estimates, not billing claims. Findings carry a
    `basis` field so UI/reports can distinguish observed-token estimates from
    heuristic reuse estimates.
    """

    reuse_route_tokens_avoided: int = field(default_factory=lambda: _env_int("OH_OBSERVER_REUSE_ROUTE_TOKENS_AVOIDED", 10000))
    reuse_route_model_calls_avoided: int = field(default_factory=lambda: _env_int("OH_OBSERVER_REUSE_ROUTE_MODEL_CALLS_AVOIDED", 3))
    ml_baseline_tokens_avoided: int = field(default_factory=lambda: _env_int("OH_OBSERVER_ML_BASELINE_TOKENS_AVOIDED", 12000))
    dependency_stack_tokens_avoided: int = field(default_factory=lambda: _env_int("OH_OBSERVER_DEP_STACK_TOKENS_AVOIDED", 6000))
    product_overlap_tokens_avoided: int = field(default_factory=lambda: _env_int("OH_OBSERVER_PRODUCT_OVERLAP_TOKENS_AVOIDED", 4000))
    manual_context_tokens_avoided: int = field(default_factory=lambda: _env_int("OH_OBSERVER_MANUAL_CONTEXT_TOKENS_AVOIDED", 2500))
    compact_context_target_tokens: int = field(default_factory=lambda: _env_int("OH_OBSERVER_COMPACT_CONTEXT_TARGET_TOKENS", 800))
    duplicate_context_target_tokens: int = field(default_factory=lambda: _env_int("OH_OBSERVER_DUPLICATE_CONTEXT_TARGET_TOKENS", 100))
    shortcut_tokens_per_manual_step: int = field(default_factory=lambda: _env_int("OH_OBSERVER_SHORTCUT_TOKENS_PER_MANUAL_STEP", 500))


ROUTER_SETTINGS = ObserverRouterSettings()
CAPTURE_SETTINGS = ObserverCaptureSettings()
HOOK_SETTINGS = ObserverHookSettings()
LOCAL_REGISTRY_SETTINGS = ObserverLocalRegistrySettings()
GLOBAL_PRIMITIVE_SETTINGS = ObserverGlobalPrimitiveSettings()
SERVICE_SETTINGS = ObserverServiceSettings()
SESSION_STORE_SETTINGS = ObserverSessionStoreSettings()
SAVINGS_SETTINGS = ObserverSavingsSettings()
