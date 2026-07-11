#!/usr/bin/env python3
"""Build the candidate semantic-ABI/search-design registry for a very large primitive corpus.

This module is a *design registry*, not evidence that the corpus is populated.  It makes the
large semantic surface requested for primitive discovery machine-readable without proposing a
single extremely wide database table:

* ``hot_columns`` are the deliberately small, latency-sensitive primitive row;
* ``normalized_feature_dictionary`` is generated from semantic facets x evidence properties and
  belongs in a normalized feature table/document (or is derived at ingest/query time);
* ``description_view_specs`` are grounded sentence-generation/indexing specifications, not
  already-generated descriptions;
* ``blocker_variables`` are derived candidate-generation/filter features, not independent source
  claims or hundreds of manually maintained columns;
* embedding spaces remain separate and are fused by rank, never averaged across incompatible
  models.

Everything emitted here is ``candidate=true`` and ``serves_truth=false``.  Promotion requires
population, measured retrieval experiments, security review, and scale benchmarks.

CLI::

    python3 scripts/primitive_semantic_abi_registry.py --summary
    python3 scripts/primitive_semantic_abi_registry.py --emit /tmp/semantic-abi-registry.json
    python3 scripts/primitive_semantic_abi_registry.py --self-test
"""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from itertools import product
from pathlib import Path
from typing import Any, Iterable


BOUNDARY: dict[str, bool] = {"candidate": True, "serves_truth": False}
REGISTRY_ID = "registry/primitive-semantic-abi-candidate"
SCHEMA_VERSION = "0.1.0"

# This is a requested design floor, not a measured corpus count or benchmark claim.
DESIGN_TARGET_PRIMITIVE_FLOOR = 50_000_000
# Requirement from the owner.  Counts are always computed from the registries below.
MINIMUM_GENERATED_SPEC_COUNT = 300

# Prefixes are candidate blocking parameters.  Production values must be tuned on a held-out
# retrieval benchmark instead of being treated as universally optimal.
SHORT_HASH_PREFIX_BITS = 16
LONG_HASH_PREFIX_BITS = 32

POPULATION_STATUS = "design-specifications-only-not-populated-across-corpus"
SCALE_STATUS = "designed-for-target-scale-not-yet-benchmarked-at-target-scale"


def _candidate(**values: Any) -> dict[str, Any]:
    """Attach the immutable candidate boundary to one emitted record."""
    return {**values, **BOUNDARY}


# Primary papers/specifications are design references only.  A citation is not corpus evidence.
# IDs intentionally avoid version tokens; versions remain in paper titles/metadata where needed.
SOURCE_DEFINITIONS: tuple[tuple[str, str, str, str, str], ...] = (
    (
        "paper/diskann",
        "DiskANN: Fast Accurate Billion-point Nearest Neighbor Search on a Single Node",
        "https://www.microsoft.com/en-us/research/?p=634449",
        "ann-index",
        "SSD-aware graph ANN candidate for large dense-vector collections",
    ),
    (
        "paper/spann",
        "SPANN: Highly-efficient Billion-scale Approximate Nearest Neighbor Search",
        "https://arxiv.org/abs/2111.08566",
        "ann-index",
        "memory-disk hybrid ANN candidate",
    ),
    (
        "paper/faiss",
        "Billion-scale similarity search with GPUs",
        "https://arxiv.org/abs/1702.08734",
        "ann-index",
        "vector quantization and GPU ANN design reference",
    ),
    (
        "paper/hierarchical-navigable-small-world",
        "Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs",
        "https://arxiv.org/abs/1603.09320",
        "ann-index",
        "in-memory graph ANN design reference",
    ),
    (
        "paper/scann",
        "Accelerating Large-Scale Inference with Anisotropic Vector Quantization",
        "https://proceedings.mlr.press/v119/guo20h.html",
        "ann-index",
        "quantized maximum-inner-product retrieval design reference",
    ),
    (
        "paper/splade-efficient-sparse-retrieval",
        "SPLADE v2: Sparse Lexical and Expansion Model for Information Retrieval",
        "https://arxiv.org/abs/2109.10086",
        "sparse-retrieval",
        "learned sparse retrieval channel",
    ),
    (
        "paper/colbert-effective-efficient-retrieval",
        "ColBERTv2: Effective and Efficient Retrieval via Lightweight Late Interaction",
        "https://arxiv.org/abs/2112.01488",
        "late-interaction",
        "multi-vector late-interaction retrieval channel",
    ),
    (
        "paper/plaid",
        "PLAID: An Efficient Engine for Late Interaction Retrieval",
        "https://arxiv.org/abs/2205.09707",
        "late-interaction",
        "candidate engine for late-interaction indexes",
    ),
    (
        "paper/e5-text-embeddings",
        "Text Embeddings by Weakly-Supervised Contrastive Pre-training",
        "https://arxiv.org/abs/2212.03533",
        "embedding-model",
        "general intent and behavior dense-vector candidate",
    ),
    (
        "paper/bge-multilingual-multifunctionality-multigranularity",
        "BGE M3-Embedding: Multi-Lingual, Multi-Functionality, Multi-Granularity Text Embeddings",
        "https://arxiv.org/abs/2402.03216",
        "embedding-model",
        "multilingual dense, sparse, and multi-vector candidate",
    ),
    (
        "paper/jina-task-adaptive-embeddings",
        "jina-embeddings-v3: Multilingual Embeddings With Task LoRA",
        "https://arxiv.org/abs/2409.10173",
        "embedding-model",
        "task-adaptive multilingual dense-vector candidate",
    ),
    (
        "paper/graphcodebert",
        "GraphCodeBERT: Pre-training Code Representations with Data Flow",
        "https://arxiv.org/abs/2009.08366",
        "code-embedding",
        "source plus data-flow representation candidate",
    ),
    (
        "paper/unixcoder",
        "UniXcoder: Unified Cross-Modal Pre-training for Code Representation",
        "https://arxiv.org/abs/2203.03850",
        "code-embedding",
        "cross-modal code representation candidate",
    ),
    (
        "paper/codet-five-plus",
        "CodeT5+: Open Code Large Language Models for Code Understanding and Generation",
        "https://arxiv.org/abs/2305.07922",
        "code-embedding",
        "code understanding representation candidate",
    ),
    (
        "paper/codexembed",
        "CodeXEmbed: A Generalist Embedding Model Family for Multilingual and Multi-task Code Retrieval",
        "https://arxiv.org/abs/2411.12644",
        "code-embedding",
        "multilingual code retrieval candidate",
    ),
    (
        "paper/autoblock",
        "AutoBlock: A Hands-off Blocking Framework for Entity Matching",
        "https://arxiv.org/abs/1912.03417",
        "blocking",
        "learned blocker candidate and evaluation reference",
    ),
    (
        "paper/shallowblocker",
        "ShallowBlocker: Improving Set Similarity Joins for Blocking",
        "https://arxiv.org/abs/2312.15835",
        "blocking",
        "high-recall set-similarity blocking reference",
    ),
    (
        "spec/wasm-interface-type",
        "WebAssembly Component Model: WIT",
        "https://component-model.bytecodealliance.org/design/wit.html",
        "interface-contract",
        "typed import/export interface foundation",
    ),
    (
        "spec/oci-distribution",
        "Open Container Initiative Distribution Specification",
        "https://github.com/opencontainers/distribution-spec",
        "artifact-distribution",
        "content-addressed artifact distribution reference",
    ),
    (
        "spec/slsa-provenance",
        "SLSA Provenance",
        "https://slsa.dev/spec/v1.1/provenance",
        "provenance",
        "build provenance contract reference",
    ),
    (
        "spec/sigstore",
        "Sigstore Documentation",
        "https://docs.sigstore.dev/",
        "artifact-trust",
        "artifact signing and verification reference",
    ),
    (
        "spec/cue",
        "CUE Language Specification",
        "https://cuelang.org/docs/reference/spec/",
        "constraint-language",
        "typed constraint and policy validation reference",
    ),
    (
        "spec/model-context-protocol",
        "Model Context Protocol Specification",
        "https://modelcontextprotocol.io/specification/2025-06-18",
        "agent-integration",
        "compact meta-tool control plane reference",
    ),
)


# The only fields proposed as one latency-sensitive row.  The physical type is a portable
# hint; the authoritative type belongs in the eventual database schema.
HOT_COLUMN_DEFINITIONS: tuple[tuple[str, str, str, str], ...] = (
    ("primitive-id", "text", "primary", "Immutable primitive identity"),
    ("tenant-id", "text", "partition", "Workspace or organization isolation key"),
    ("registry-tier", "enum", "filter", "Workspace, organization, vendor, public, or untrusted tier"),
    ("capability-namespace", "text", "route", "Stable semantic namespace"),
    ("capability-family", "text", "route", "Coarse family used before expensive retrieval"),
    ("capability-operation", "text", "route", "Canonical operation or behavior class"),
    ("capability-kind", "enum", "filter", "Operation, adapter, recipe, service, component, or tool"),
    ("title", "text", "display", "Compact human label"),
    ("purpose-sketch", "text", "lexical", "One grounded sentence for progressive disclosure"),
    ("input-edge-sketch", "text", "lexical", "Compact principal input edge"),
    ("output-edge-sketch", "text", "lexical", "Compact principal output edge"),
    ("input-type-signature", "text", "filter", "Canonical principal input type signature"),
    ("output-type-signature", "text", "filter", "Canonical principal output type signature"),
    ("error-type-signature", "text", "filter", "Canonical error-channel type signature"),
    ("effect-bitmap", "bitmap", "filter", "Declared effect classes for hard filtering"),
    ("policy-bitmap", "bitmap", "filter", "Precomputed policy partitions; never replaces full policy evaluation"),
    ("data-classification-bitmap", "bitmap", "filter", "Input/output privacy and data-classification classes"),
    ("region-bitmap", "bitmap", "filter", "Permitted or required execution regions"),
    ("language", "text", "filter", "Implementation language"),
    ("runtime", "text", "filter", "Runtime family and compatibility class"),
    ("framework", "text", "filter", "Framework family and compatibility class"),
    ("package-coordinate", "text", "lookup", "Operational package or implementation bundle"),
    ("implementation-form", "enum", "filter", "Library, internal source, AST transform, Wasm, service, MCP, or recipe"),
    ("artifact-digest", "digest", "lookup", "Content identity of materialized artifact"),
    ("implementation-digest", "digest", "lookup", "Content identity of implementation binding"),
    ("source-digest", "digest", "lookup", "Content identity of source evidence"),
    ("source-uri", "uri", "lookup", "Evidence-backed source locator"),
    ("body-object-key", "text", "lookup", "Cold object-store key for source, traces, and detailed evidence"),
    ("recipe-graph-digest", "digest", "lookup", "Content identity of a composite graph"),
    ("dependency-closure-digest", "digest", "filter", "Pinned dependency-closure identity"),
    ("workspace-compatibility-key", "digest", "filter", "Derived coarse repository compatibility key"),
    ("license-expression", "text", "filter", "SPDX-compatible license expression"),
    ("publisher-id", "text", "filter", "Publisher or owning organization identity"),
    ("trust-tier", "enum", "filter", "Execution-policy trust tier"),
    ("signature-status", "enum", "filter", "Artifact signature verification state"),
    ("provenance-status", "enum", "filter", "Build provenance verification state"),
    ("verification-status", "enum", "filter", "Candidate, checked, verified, revoked, or expired state"),
    ("verification-receipt-id", "text", "lookup", "Latest governed verification receipt"),
    ("evidence-strength-bucket", "enum", "rank", "Calibrated evidence tier, not a truth declaration"),
    ("evidence-count", "integer", "rank", "Number of non-duplicate attached evidence records"),
    ("contract-suite-status", "enum", "filter", "Latest compatible contract-suite result"),
    ("hidden-oracle-status", "enum", "filter", "Latest compatible hidden-oracle result"),
    ("compatibility-suite-id", "text", "lookup", "Compatibility suite used by the binding"),
    ("idempotency-class", "enum", "filter", "Idempotency and deduplication semantics"),
    ("retry-safety-class", "enum", "filter", "Retry policy and indeterminate-outcome semantics"),
    ("execution-mode", "enum", "filter", "Synchronous, asynchronous, streaming, or batch mode"),
    ("determinism-class", "enum", "filter", "Deterministic, seeded, bounded-nondeterministic, or probabilistic"),
    ("latency-class", "enum", "rank", "Evidence-backed latency envelope class"),
    ("resource-class", "enum", "rank", "Coarse CPU, memory, storage, or accelerator envelope"),
    ("adapter-cost-class", "enum", "rank", "Estimated verified adapter burden"),
    ("residual-code-class", "enum", "rank", "Estimated unresolved novelty burden"),
    ("description-coverage-bitmap", "bitmap", "filter", "Which grounded description views exist"),
    ("embedding-coverage-bitmap", "bitmap", "filter", "Which independent embedding channels exist"),
    ("blocker-coverage-bitmap", "bitmap", "filter", "Which blocker variables were successfully derived"),
    ("feature-dictionary-version", "semver", "lookup", "Version of normalized semantic feature derivation"),
    ("search-document-version", "semver", "lookup", "Version of search-document projection"),
    ("candidate", "boolean", "filter", "Candidate boundary; enrichment never promotes"),
    ("serves-truth", "boolean", "filter", "Must remain false for this design registry"),
    ("deprecated-at", "timestamp", "filter", "Deprecation timestamp when applicable"),
    ("revoked-at", "timestamp", "filter", "Revocation timestamp when applicable"),
    ("created-at", "timestamp", "sort", "Original governed creation time"),
    ("updated-at", "timestamp", "sort", "Latest source-backed update time"),
)


# Each facet supplies one semantic subject.  Properties below turn it into a normalized,
# evidence-aware feature dictionary.  This is intentionally *not* a SQL-column declaration.
ABI_FACET_DEFINITIONS: tuple[tuple[str, str, str, str], ...] = (
    ("identity", "identity", "identifier", "Primitive and capability identity"),
    ("namespace", "identity.namespace", "identifier", "Capability namespace"),
    ("family", "identity.family", "identifier", "Capability family"),
    ("operation", "identity.operation", "identifier", "Canonical behavior or operation"),
    ("kind", "identity.kind", "enum", "Operation, adapter, recipe, tool, service, or component kind"),
    ("implementation-form", "implementation.form", "enum", "How the implementation is materialized"),
    ("implementation-binding", "implementation.binding", "identifier", "Concrete implementation selection"),
    ("package-bundle", "implementation.bundle", "identifier", "Operational package containing virtual capabilities"),
    ("input-port", "interface.input", "type", "Input port types and refinements"),
    ("output-port", "interface.output", "type", "Output port types and refinements"),
    ("error-port", "interface.error", "type", "Typed error channel and failure meaning"),
    ("configuration-port", "interface.configuration", "type", "Configuration inputs"),
    ("state-port", "interface.state", "type", "State read and transition contract"),
    ("control-port", "interface.control", "type", "Control, approval, and cancellation inputs"),
    ("input-cardinality", "interface.input_cardinality", "enum", "Single, optional, collection, map, or stream input"),
    ("output-cardinality", "interface.output_cardinality", "enum", "Single, optional, collection, map, or stream output"),
    ("nullability", "interface.nullability", "enum", "Missing and null semantics"),
    ("serialization", "interface.serialization", "set", "Accepted and emitted serialization formats"),
    ("protocol", "interface.protocol", "enum", "Protocol and state-machine contract"),
    ("precondition", "contract.precondition", "constraint", "Conditions required before invocation"),
    ("postcondition", "contract.postcondition", "constraint", "Guaranteed state after successful invocation"),
    ("invariant", "contract.invariant", "constraint", "Properties preserved across invocation"),
    ("failure-condition", "contract.failure", "constraint", "Conditions that produce each typed error"),
    ("effect", "effects.summary", "set", "Declared side-effect classes"),
    ("network-effect", "effects.network", "policy", "Network destinations and operations"),
    ("filesystem-effect", "effects.filesystem", "policy", "Filesystem scopes and operations"),
    ("database-effect", "effects.database", "policy", "Database resources and operation classes"),
    ("secret-effect", "effects.secret", "policy", "Secret identities and exposure rules"),
    ("subprocess-effect", "effects.subprocess", "policy", "Permitted child process behavior"),
    ("logging-effect", "effects.logging", "policy", "Logging permissions and forbidden data"),
    ("model-provider-effect", "effects.model_provider", "policy", "Data sent to probabilistic model providers"),
    ("randomness", "behavior.randomness", "enum", "Randomness source, seeding, and reproducibility"),
    ("time", "behavior.time", "enum", "Clock dependence and time semantics"),
    ("idempotency", "behavior.idempotency", "enum", "Idempotency key and replay semantics"),
    ("retry", "behavior.retry", "enum", "Retry safety and indeterminate outcomes"),
    ("transaction", "behavior.transaction", "enum", "Transaction participation and boundary"),
    ("ordering", "behavior.ordering", "enum", "Ordering guarantees"),
    ("consistency", "behavior.consistency", "enum", "Consistency and visibility guarantees"),
    ("concurrency", "behavior.concurrency", "enum", "Concurrency safety and isolation"),
    ("execution-mode", "behavior.execution_mode", "enum", "Sync, async, stream, or batch execution"),
    ("backpressure", "behavior.backpressure", "enum", "Streaming pressure and buffering semantics"),
    ("ownership", "behavior.ownership", "enum", "Resource and value ownership semantics"),
    ("lifecycle", "behavior.lifecycle", "enum", "Creation, reuse, close, and cleanup protocol"),
    ("cancellation", "behavior.cancellation", "enum", "Cancellation propagation and safe points"),
    ("timeout", "behavior.timeout", "range", "Timeout requirements and default semantics"),
    ("latency", "operations.latency", "range", "Measured latency envelope"),
    ("throughput", "operations.throughput", "range", "Measured throughput envelope"),
    ("cpu", "operations.cpu", "range", "CPU resource envelope"),
    ("memory", "operations.memory", "range", "Memory resource envelope"),
    ("storage", "operations.storage", "range", "Storage resource envelope"),
    ("batch-size", "operations.batch_size", "range", "Supported and efficient batch ranges"),
    ("data-classification", "security.data_classification", "policy", "Data sensitivity and taint classes"),
    ("authentication", "security.authentication", "policy", "Required caller authentication"),
    ("authorization", "security.authorization", "policy", "Required scopes, roles, or decisions"),
    ("tenant-isolation", "security.tenant_isolation", "policy", "Tenant boundary contract"),
    ("region", "security.region", "policy", "Data residency and execution region rules"),
    ("compliance", "security.compliance", "set", "Applicable compliance profiles"),
    ("human-approval", "security.human_approval", "policy", "Human approval gates"),
    ("license", "supply_chain.license", "policy", "License and redistribution terms"),
    ("publisher", "supply_chain.publisher", "identifier", "Publisher identity"),
    ("artifact-signature", "supply_chain.signature", "evidence", "Artifact signature and verification"),
    ("build-provenance", "supply_chain.provenance", "evidence", "Build provenance and builder identity"),
    ("dependency-closure", "supply_chain.dependencies", "graph", "Pinned dependency graph"),
    ("vulnerability", "supply_chain.vulnerability", "evidence", "Vulnerability scan and incident state"),
    ("contract-test", "evidence.contract_test", "evidence", "Executable contract-test evidence"),
    ("property-test", "evidence.property_test", "evidence", "Property-test evidence"),
    ("integration-test", "evidence.integration_test", "evidence", "Repository integration evidence"),
    ("hidden-oracle", "evidence.hidden_oracle", "evidence", "Hidden-oracle evidence"),
    ("execution-trace", "evidence.execution_trace", "evidence", "Behavioral trace evidence"),
    ("compatibility-suite", "compatibility.suite", "identifier", "Compatibility suite identity"),
    ("language", "compatibility.language", "enum", "Implementation language and language version range"),
    ("runtime", "compatibility.runtime", "enum", "Runtime compatibility"),
    ("framework", "compatibility.framework", "enum", "Framework compatibility"),
    ("operating-system", "compatibility.operating_system", "enum", "Operating-system compatibility"),
    ("architecture", "compatibility.architecture", "enum", "CPU and machine architecture compatibility"),
    ("deployment-target", "compatibility.deployment_target", "enum", "Deployment environment compatibility"),
    ("toolchain", "compatibility.toolchain", "enum", "Compiler, generator, and toolchain compatibility"),
    ("composition-before", "composition.before", "graph", "Valid predecessor capabilities"),
    ("composition-after", "composition.after", "graph", "Valid successor capabilities"),
    ("adapter", "composition.adapter", "graph", "Known verified adapters"),
    ("recipe-membership", "composition.recipe", "graph", "Composite recipe membership and role"),
    ("deprecation", "lifecycle.deprecation", "enum", "Deprecation state and reason"),
    ("migration", "lifecycle.migration", "graph", "Replacement and migration path"),
    ("revocation", "lifecycle.revocation", "evidence", "Revocation status and evidence"),
)


ABI_PROPERTY_DEFINITIONS: tuple[tuple[str, str, str, str], ...] = (
    ("canonical-value", "value", "stored-normalized", "Canonical value or structured payload"),
    ("normalized-value", "normalized", "derived-on-ingest", "Search-normalized representation"),
    ("schema-reference", "schema_ref", "stored-normalized", "Schema or ontology reference"),
    ("requiredness", "requiredness", "stored-normalized", "Required, optional, conditional, or forbidden state"),
    ("constraint-expression", "constraint", "stored-normalized", "Machine-checkable constraint expression"),
    ("default-semantics", "default_semantics", "stored-normalized", "Meaning of absence and declared default"),
    ("evidence-references", "evidence_refs", "stored-normalized", "Supporting evidence locators"),
    ("verification-status", "verification_status", "derived-from-receipts", "Verification state for this facet only"),
    ("provenance-reference", "provenance_ref", "stored-normalized", "Generator, source, and derivation lineage"),
    ("freshness-state", "freshness", "derived-from-source-state", "Fresh, stale, expired, revoked, or unknown"),
)


# A view is a request for one grounded full sentence.  The Cartesian product is deliberate:
# facets answer different questions, registers change vocabulary, and frames cover positive,
# query-shaped, and negative retrieval.  They are specifications until an evidence-backed job
# materializes them.
DESCRIPTION_FACET_DEFINITIONS: tuple[tuple[str, str, tuple[str, ...], str], ...] = (
    ("does", "What does the primitive do from start to finish?", ("purpose-sketch", "contract.postcondition"), "intent"),
    ("user-goal", "What user or agent outcome does this primitive satisfy?", ("purpose-sketch",), "intent"),
    ("problem", "What recurring problem does the primitive solve?", ("purpose-sketch", "evidence.execution_trace"), "intent"),
    ("solution", "How does the primitive solve that problem without implementation trivia?", ("contract.postcondition",), "behavior"),
    ("input", "What inputs, configuration, and state does it consume?", ("interface.input", "interface.configuration", "interface.state"), "interface"),
    ("output", "What values, errors, and new state can it produce?", ("interface.output", "interface.error", "interface.state"), "interface"),
    ("transform", "What semantic transformation connects its inputs to outputs?", ("interface.input", "interface.output", "contract.postcondition"), "behavior"),
    ("precondition", "What must be true before it can run?", ("contract.precondition",), "behavior"),
    ("postcondition", "What is guaranteed after successful completion?", ("contract.postcondition",), "behavior"),
    ("invariant", "What property remains true across execution?", ("contract.invariant",), "behavior"),
    ("use-when", "When should a developer select this primitive?", ("purpose-sketch", "contract.precondition"), "intent"),
    ("not-when", "When is this primitive the wrong choice?", ("contract.precondition", "contract.failure"), "negative"),
    ("failure", "Under what conditions does it fail and with which typed errors?", ("contract.failure", "interface.error"), "failure"),
    ("failure-symptom", "What developer-observed symptom should retrieve this primitive?", ("contract.failure", "evidence.execution_trace"), "failure"),
    ("edge-case", "Which boundary cases materially change behavior?", ("contract.constraint", "evidence.property_test"), "failure"),
    ("retry", "How should callers handle retries and indeterminate outcomes?", ("behavior.retry", "behavior.idempotency"), "behavior"),
    ("idempotency", "What makes repeated invocation safe or unsafe?", ("behavior.idempotency",), "behavior"),
    ("transaction", "How does the primitive participate in transaction boundaries?", ("behavior.transaction",), "composition"),
    ("ordering", "What ordering and consistency does it preserve or require?", ("behavior.ordering", "behavior.consistency"), "behavior"),
    ("effects", "Which external effects can it perform?", ("effects.summary",), "policy"),
    ("security", "Which authentication, authorization, secret, and approval rules apply?", ("security.authentication", "security.authorization", "effects.secret", "security.human_approval"), "policy"),
    ("privacy", "How does data classification, tenancy, and region constrain use?", ("security.data_classification", "security.tenant_isolation", "security.region"), "policy"),
    ("performance", "What measured latency and throughput envelope applies?", ("operations.latency", "operations.throughput"), "operations"),
    ("resource", "What CPU, memory, storage, and batch resources are required?", ("operations.cpu", "operations.memory", "operations.storage", "operations.batch_size"), "operations"),
    ("compatibility", "Which language, runtime, framework, and deployment contexts are compatible?", ("compatibility.language", "compatibility.runtime", "compatibility.framework", "compatibility.deployment_target"), "compatibility"),
    ("prerequisite", "Which capabilities, resources, and policies must already exist?", ("composition.before", "contract.precondition"), "composition"),
    ("composition-before", "Which primitives normally precede this one and why?", ("composition.before",), "composition"),
    ("composition-after", "Which primitives normally consume its outputs and why?", ("composition.after",), "composition"),
    ("adapter", "Which verified adapters can bridge incompatible ports or protocols?", ("composition.adapter",), "composition"),
    ("near-miss", "Which similar capability should not be confused with this one?", ("contract.precondition", "composition.recipe"), "negative"),
    ("alternative", "Which compatible alternatives exist and what contract difference matters?", ("compatibility.suite", "composition.adapter"), "negative"),
    ("migration", "How should a caller move from a deprecated or incompatible binding?", ("lifecycle.migration", "lifecycle.deprecation"), "compatibility"),
    ("evidence", "What executable evidence supports the declared behavior?", ("evidence.contract_test", "evidence.property_test", "evidence.integration_test", "evidence.hidden_oracle"), "evidence"),
    ("test", "What observable contract should a test assert?", ("evidence.contract_test", "contract.postcondition"), "evidence"),
    ("observability", "Which traces, metrics, and safe logs reveal success or failure?", ("evidence.execution_trace", "effects.logging"), "operations"),
    ("residual-gap", "Which requested behavior remains unresolved by this primitive?", ("contract.postcondition", "composition.recipe"), "negative"),
)


DESCRIPTION_REGISTER_DEFINITIONS: tuple[tuple[str, str], ...] = (
    ("plain", "Use clear developer language and expand specialized terminology."),
    ("technical", "Use exact types, protocols, effects, and failure semantics."),
    ("semantic", "State intent and behavioral distinctions independently of a particular implementation."),
)


DESCRIPTION_FRAME_DEFINITIONS: tuple[tuple[str, str], ...] = (
    ("canonical-statement", "Write one declarative sentence that answers the facet question."),
    ("developer-query", "Write one realistic complete-sentence request that this primitive should retrieve for."),
    ("negative-contrast", "Write one complete sentence distinguishing a confusable but incompatible case."),
)


# Blocking dimensions are source signals.  Each compatible transform below produces a derived
# variable.  Hard constraints are enforced after retrieval as well; a probabilistic blocker must
# never authorize execution.
BLOCKER_DIMENSION_DEFINITIONS: tuple[tuple[str, str, str, bool, str], ...] = (
    ("capability-namespace", "identity.namespace", "identifier", False, "Coarse capability namespace"),
    ("capability-family", "identity.family", "identifier", False, "Capability family"),
    ("capability-operation", "identity.operation", "identifier", False, "Canonical operation"),
    ("capability-kind", "identity.kind", "enum", False, "Primitive or implementation kind"),
    ("domain", "identity.domain", "identifier", False, "Domain or bounded context"),
    ("industry", "identity.industry", "set", False, "Open industry tags"),
    ("task-intent", "descriptions.intent", "text", False, "Normalized task-intent terms"),
    ("recipe-role", "composition.recipe.role", "enum", False, "Role inside a composite recipe"),
    ("input-types", "interface.input.types", "type", True, "Input type and refinement signatures"),
    ("output-types", "interface.output.types", "type", True, "Output type and refinement signatures"),
    ("error-types", "interface.error.types", "type", False, "Typed error signatures"),
    ("configuration-types", "interface.configuration.types", "type", False, "Configuration type signatures"),
    ("state-types", "interface.state.types", "type", False, "State type signatures"),
    ("input-cardinality", "interface.input_cardinality", "enum", True, "Input cardinality class"),
    ("output-cardinality", "interface.output_cardinality", "enum", True, "Output cardinality class"),
    ("nullability", "interface.nullability", "enum", True, "Missing and null semantics"),
    ("execution-mode", "behavior.execution_mode", "enum", True, "Sync, async, stream, or batch"),
    ("streaming-mode", "behavior.backpressure", "enum", True, "Streaming and backpressure class"),
    ("serialization", "interface.serialization", "set", True, "Serialization formats"),
    ("protocol", "interface.protocol", "enum", True, "Protocol or state-machine family"),
    ("idempotency", "behavior.idempotency", "enum", True, "Idempotency class"),
    ("retry-safety", "behavior.retry", "enum", True, "Retry safety class"),
    ("transaction", "behavior.transaction", "enum", True, "Transaction participation class"),
    ("ordering", "behavior.ordering", "enum", False, "Ordering guarantee"),
    ("consistency", "behavior.consistency", "enum", False, "Consistency model"),
    ("determinism", "behavior.randomness", "enum", False, "Determinism and randomness class"),
    ("cancellation", "behavior.cancellation", "enum", False, "Cancellation semantics"),
    ("timeout", "behavior.timeout", "numeric", False, "Timeout range"),
    ("network-destinations", "effects.network", "policy", True, "Allowed network destinations"),
    ("filesystem-scopes", "effects.filesystem", "policy", True, "Filesystem scopes"),
    ("database-resources", "effects.database", "policy", True, "Database tables and operation classes"),
    ("secret-identities", "effects.secret", "policy", True, "Required secret identities"),
    ("subprocess-permissions", "effects.subprocess", "policy", True, "Subprocess permission classes"),
    ("logging-classifications", "effects.logging", "policy", True, "Allowed and forbidden log data"),
    ("model-provider-exposure", "effects.model_provider", "policy", True, "Data exposed to model providers"),
    ("data-classifications", "security.data_classification", "policy", True, "Input and output data classifications"),
    ("authentication", "security.authentication", "policy", True, "Caller authentication class"),
    ("authorization-scopes", "security.authorization", "policy", True, "Required scopes and roles"),
    ("tenant-isolation", "security.tenant_isolation", "policy", True, "Tenant isolation class"),
    ("region", "security.region", "policy", True, "Residency and execution region"),
    ("compliance", "security.compliance", "set", True, "Compliance profiles"),
    ("human-approval", "security.human_approval", "boolean", True, "Human approval requirement"),
    ("language", "compatibility.language", "enum", True, "Implementation language"),
    ("language-version", "compatibility.language.version", "semver", True, "Language version range"),
    ("runtime", "compatibility.runtime", "enum", True, "Runtime family"),
    ("runtime-version", "compatibility.runtime.version", "semver", True, "Runtime version range"),
    ("framework", "compatibility.framework", "enum", True, "Framework family"),
    ("framework-version", "compatibility.framework.version", "semver", True, "Framework version range"),
    ("package-manager", "compatibility.package_manager", "enum", False, "Package-manager family"),
    ("abi-version", "compatibility.abi", "semver", True, "Mechanical ABI compatibility range"),
    ("operating-system", "compatibility.operating_system", "enum", True, "Operating-system family"),
    ("architecture", "compatibility.architecture", "enum", True, "Machine architecture"),
    ("deployment-target", "compatibility.deployment_target", "enum", True, "Deployment target"),
    ("accelerator", "compatibility.accelerator", "enum", False, "Required accelerator class"),
    ("toolchain", "compatibility.toolchain", "enum", True, "Compiler and generator family"),
    ("dependency-closure", "supply_chain.dependencies", "digest", False, "Pinned dependency-closure digest"),
    ("license", "supply_chain.license", "policy", True, "License-policy partition"),
    ("trust-tier", "supply_chain.trust", "enum", True, "Registry trust tier"),
    ("publisher", "supply_chain.publisher", "identifier", True, "Publisher identity"),
    ("artifact-digest", "supply_chain.artifact_digest", "digest", False, "Artifact content digest"),
    ("signature-status", "supply_chain.signature", "enum", True, "Artifact signature state"),
    ("provenance-builder", "supply_chain.provenance.builder", "identifier", True, "Provenance builder identity"),
    ("vulnerability-status", "supply_chain.vulnerability", "enum", True, "Vulnerability and revocation state"),
    ("verification-status", "evidence.verification_status", "enum", True, "Verification status"),
    ("contract-suite", "evidence.contract_test.suite", "identifier", False, "Contract-suite identity"),
    ("compatibility-suite", "compatibility.suite", "identifier", False, "Compatibility-suite identity"),
    ("deprecation-status", "lifecycle.deprecation", "enum", True, "Deprecation state"),
    ("latency", "operations.latency", "numeric", False, "Latency envelope"),
    ("memory", "operations.memory", "numeric", False, "Memory envelope"),
    ("cpu", "operations.cpu", "numeric", False, "CPU envelope"),
    ("storage", "operations.storage", "numeric", False, "Storage envelope"),
    ("batch-size", "operations.batch_size", "numeric", False, "Batch-size range"),
    ("concurrency", "behavior.concurrency", "numeric", False, "Supported concurrency range"),
    ("predecessor-families", "composition.before", "graph", False, "Compatible predecessor families"),
    ("successor-families", "composition.after", "graph", False, "Compatible successor families"),
    ("adapter-families", "composition.adapter", "graph", False, "Available adapter families"),
    ("graph-neighborhood", "composition.neighborhood", "graph", False, "Local capability graph neighborhood"),
    ("workspace-lock", "workspace.lock_digest", "digest", True, "Exact workspace primitive lock identity"),
    ("repository-convention", "workspace.convention", "enum", False, "Repository convention class"),
    ("existing-dependencies", "workspace.dependencies", "set", False, "Already installed dependency families"),
    ("feature-flags", "workspace.feature_flags", "set", False, "Applicable workspace feature flags"),
)


# Each transform declares the kinds it can safely consume.  ``all`` means canonical JSON
# normalization is defined for any value kind.  The resulting variables are deterministic
# candidates; recall/precision must be measured before production use.
BLOCKER_TRANSFORM_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "id": "is-present",
        "kinds": ("all",),
        "index_family": "bitmap",
        "parameter": None,
        "description": "Presence bit; useful for routing incomplete records without treating missing as mismatch",
    },
    {
        "id": "canonical-exact",
        "kinds": ("all",),
        "index_family": "inverted",
        "parameter": None,
        "description": "Exact match over canonical JSON representation",
    },
    {
        "id": "stable-hash-prefix-short",
        "kinds": ("all",),
        "index_family": "hash",
        "parameter": {"prefix_bits": SHORT_HASH_PREFIX_BITS},
        "description": "Short stable hash prefix for coarse shard routing",
    },
    {
        "id": "stable-hash-prefix-long",
        "kinds": ("all",),
        "index_family": "hash",
        "parameter": {"prefix_bits": LONG_HASH_PREFIX_BITS},
        "description": "Long stable hash prefix for narrower candidate buckets",
    },
    {
        "id": "coarse-class",
        "kinds": ("all",),
        "index_family": "bitmap",
        "parameter": {"mapping": "dimension-owned-coarsener"},
        "description": "Dimension-specific compatibility class",
    },
    {
        "id": "workspace-policy-partition",
        "kinds": ("all",),
        "index_family": "bitmap",
        "parameter": {"mapping": "workspace-policy-compiler"},
        "description": "Allowed, forbidden, conditional, or unknown partition for the active workspace policy",
    },
    {
        "id": "prefix-bucket",
        "kinds": ("identifier", "text", "type", "semver", "digest"),
        "index_family": "trie",
        "parameter": {"length": "benchmark-selected"},
        "description": "Normalized leading-token or digest prefix bucket",
    },
    {
        "id": "set-any-signature",
        "kinds": ("set", "type", "policy", "graph"),
        "index_family": "inverted",
        "parameter": {"semantics": "at-least-one-canonical-member"},
        "description": "Candidate bucket for any overlapping canonical member",
    },
    {
        "id": "set-all-signature",
        "kinds": ("set", "type", "policy", "graph"),
        "index_family": "inverted",
        "parameter": {"semantics": "all-required-members"},
        "description": "Candidate bucket requiring the query's canonical member set",
    },
    {
        "id": "minhash-band",
        "kinds": ("set", "text", "graph"),
        "index_family": "lsh",
        "parameter": {"bands": "benchmark-selected"},
        "description": "Approximate Jaccard candidate bucket; never a deterministic compatibility decision",
    },
    {
        "id": "range-bucket",
        "kinds": ("numeric", "semver"),
        "index_family": "range",
        "parameter": {"boundaries": "evidence-distribution-derived"},
        "description": "Overlapping numeric or version range bucket",
    },
    {
        "id": "compatibility-class",
        "kinds": ("identifier", "enum", "type", "semver", "policy", "graph"),
        "index_family": "bitmap",
        "parameter": {"resolver": "dimension-specific-compatibility-resolver"},
        "description": "Resolver-produced compatibility class rather than string equality",
    },
    {
        "id": "major-version",
        "kinds": ("semver",),
        "index_family": "bitmap",
        "parameter": {"component": "major"},
        "description": "Coarse semantic-version compatibility candidate bucket",
    },
    {
        "id": "graph-neighborhood-signature",
        "kinds": ("graph",),
        "index_family": "graph",
        "parameter": {"radius": "request-budget-derived"},
        "description": "Stable signature of a bounded typed graph neighborhood",
    },
)


EMBEDDING_MODEL_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "id": "embedding-model/e5",
        "name": "E5 text embedding family",
        "modalities": ("natural-language",),
        "source_ids": ("paper/e5-text-embeddings",),
        "vector_shape": "model-native",
    },
    {
        "id": "embedding-model/bge-multifunction",
        "name": "BGE multilingual multifunction embedding family",
        "modalities": ("natural-language", "sparse", "multi-vector"),
        "source_ids": ("paper/bge-multilingual-multifunctionality-multigranularity",),
        "vector_shape": "model-native",
    },
    {
        "id": "embedding-model/jina-task-adaptive",
        "name": "Jina task-adaptive multilingual embedding family",
        "modalities": ("natural-language",),
        "source_ids": ("paper/jina-task-adaptive-embeddings",),
        "vector_shape": "model-native-or-matryoshka-selected",
    },
    {
        "id": "embedding-model/graphcodebert",
        "name": "GraphCodeBERT code and data-flow representation",
        "modalities": ("source-code", "data-flow"),
        "source_ids": ("paper/graphcodebert",),
        "vector_shape": "model-native",
    },
    {
        "id": "embedding-model/unixcoder",
        "name": "UniXcoder cross-modal code representation",
        "modalities": ("source-code", "natural-language"),
        "source_ids": ("paper/unixcoder",),
        "vector_shape": "model-native",
    },
    {
        "id": "embedding-model/codet-five-plus",
        "name": "CodeT5+ code representation",
        "modalities": ("source-code", "natural-language"),
        "source_ids": ("paper/codet-five-plus",),
        "vector_shape": "model-native",
    },
    {
        "id": "embedding-model/codexembed",
        "name": "CodeXEmbed multilingual code retrieval family",
        "modalities": ("source-code", "natural-language"),
        "source_ids": ("paper/codexembed",),
        "vector_shape": "model-native",
    },
    {
        "id": "embedding-model/splade",
        "name": "SPLADE learned sparse representation",
        "modalities": ("natural-language", "sparse"),
        "source_ids": ("paper/splade-efficient-sparse-retrieval",),
        "vector_shape": "sparse-vocabulary-native",
    },
    {
        "id": "embedding-model/colbert",
        "name": "ColBERT late-interaction representation",
        "modalities": ("natural-language", "multi-vector"),
        "source_ids": ("paper/colbert-effective-efficient-retrieval", "paper/plaid"),
        "vector_shape": "token-multi-vector-native",
    },
    {
        "id": "embedding-model/deterministic-symbolic",
        "name": "Deterministic typed, policy, and graph fingerprints",
        "modalities": ("type", "policy", "graph", "execution-trace"),
        "source_ids": (),
        "vector_shape": "feature-dictionary-native",
    },
)


EMBEDDING_CHANNEL_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "id": "embedding-channel/intent-dense",
        "view_families": ("intent",),
        "model_ids": ("embedding-model/e5", "embedding-model/bge-multifunction", "embedding-model/jina-task-adaptive"),
        "index": "ann-dense",
    },
    {
        "id": "embedding-channel/behavior-dense",
        "view_families": ("behavior",),
        "model_ids": ("embedding-model/e5", "embedding-model/bge-multifunction"),
        "index": "ann-dense",
    },
    {
        "id": "embedding-channel/interface-dense",
        "view_families": ("interface",),
        "model_ids": ("embedding-model/bge-multifunction", "embedding-model/jina-task-adaptive"),
        "index": "ann-dense",
    },
    {
        "id": "embedding-channel/failure-dense",
        "view_families": ("failure", "negative"),
        "model_ids": ("embedding-model/e5", "embedding-model/bge-multifunction"),
        "index": "ann-dense",
    },
    {
        "id": "embedding-channel/composition-dense",
        "view_families": ("composition", "compatibility"),
        "model_ids": ("embedding-model/bge-multifunction", "embedding-model/jina-task-adaptive"),
        "index": "ann-dense",
    },
    {
        "id": "embedding-channel/policy-dense",
        "view_families": ("policy",),
        "model_ids": ("embedding-model/e5",),
        "index": "ann-dense-advisory-only",
    },
    {
        "id": "embedding-channel/code-dense",
        "view_families": ("source-code",),
        "model_ids": ("embedding-model/graphcodebert", "embedding-model/unixcoder", "embedding-model/codet-five-plus", "embedding-model/codexembed"),
        "index": "ann-dense",
    },
    {
        "id": "embedding-channel/learned-sparse",
        "view_families": ("intent", "behavior", "failure", "composition"),
        "model_ids": ("embedding-model/splade", "embedding-model/bge-multifunction"),
        "index": "inverted-sparse",
    },
    {
        "id": "embedding-channel/lexical-sparse",
        "view_families": ("all-grounded-text",),
        "model_ids": (),
        "index": "bm25-inverted",
    },
    {
        "id": "embedding-channel/late-interaction",
        "view_families": ("intent", "behavior", "failure"),
        "model_ids": ("embedding-model/colbert", "embedding-model/bge-multifunction"),
        "index": "multi-vector-late-interaction",
    },
    {
        "id": "embedding-channel/type-symbolic",
        "view_families": ("interface",),
        "model_ids": ("embedding-model/deterministic-symbolic",),
        "index": "typed-inverted-and-graph",
    },
    {
        "id": "embedding-channel/graph-symbolic",
        "view_families": ("composition",),
        "model_ids": ("embedding-model/deterministic-symbolic",),
        "index": "typed-graph",
    },
    {
        "id": "embedding-channel/trace-symbolic",
        "view_families": ("execution-trace",),
        "model_ids": ("embedding-model/deterministic-symbolic",),
        "index": "behavioral-fingerprint",
    },
)


ANN_INDEX_PROFILE_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "id": "ann-profile/disk-graph",
        "algorithm_candidates": ("DiskANN", "SPANN"),
        "source_ids": ("paper/diskann", "paper/spann"),
        "fit": "large dense spaces whose full graph should not reside in memory",
    },
    {
        "id": "ann-profile/memory-graph",
        "algorithm_candidates": ("HNSW",),
        "source_ids": ("paper/hierarchical-navigable-small-world",),
        "fit": "hot partitions that fit the measured memory budget",
    },
    {
        "id": "ann-profile/quantized",
        "algorithm_candidates": ("Faiss IVF/PQ", "ScaNN"),
        "source_ids": ("paper/faiss", "paper/scann"),
        "fit": "quantized dense-vector candidates selected by recall, latency, and cost benchmarks",
    },
)


RETRIEVAL_STAGE_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "id": "retrieval-stage/workspace-policy",
        "order": 0,
        "reads": ("hot-columns", "workspace-profile"),
        "purpose": "Apply tenant, trust, license, data, effect, region, and revocation hard constraints",
        "acceptance": "deterministic-policy-check",
    },
    {
        "id": "retrieval-stage/family-route",
        "order": 1,
        "reads": ("hot-columns", "blocker-variables"),
        "purpose": "Route to capability, language, runtime, and framework partitions",
        "acceptance": "high-recall-candidate-routing",
    },
    {
        "id": "retrieval-stage/hybrid-candidates",
        "order": 2,
        "reads": ("lexical-sparse", "learned-sparse", "independent-dense-spaces", "typed-index"),
        "purpose": "Retrieve candidates independently from sparse, dense, type, and graph channels",
        "acceptance": "rank-fusion-with-channel-provenance",
    },
    {
        "id": "retrieval-stage/rerank",
        "order": 3,
        "reads": ("selected-description-views", "late-interaction", "workspace-profile"),
        "purpose": "Rerank a bounded candidate set with negative contrasts and workspace fit",
        "acceptance": "calibrated-reranker-score-not-truth",
    },
    {
        "id": "retrieval-stage/graph-solve",
        "order": 4,
        "reads": ("semantic-abi", "adapter-graph", "recipe-graph"),
        "purpose": "Find a low-cost typed, effect-aware subgraph and expose residual gaps",
        "acceptance": "bounded-search-candidate-plan",
    },
    {
        "id": "retrieval-stage/deterministic-acceptance",
        "order": 5,
        "reads": ("exact-implementations", "policies", "locks", "tests", "provenance"),
        "purpose": "Reject incompatible plans and emit a reproducible binding only after deterministic checks",
        "acceptance": "types-effects-policy-lock-and-tests",
    },
)


RETRIEVAL_PROFILE_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "id": "retrieval-profile/hybrid-semantic-linker",
        "channels": tuple(row["id"] for row in EMBEDDING_CHANNEL_DEFINITIONS),
        "stages": tuple(row["id"] for row in RETRIEVAL_STAGE_DEFINITIONS),
        "fusion": "calibrated-rank-fusion-over-separate-spaces",
        "expansion": "progressive-disclosure-under-request-token-budget",
    },
    {
        "id": "retrieval-profile/private-workspace",
        "channels": (
            "embedding-channel/lexical-sparse",
            "embedding-channel/type-symbolic",
            "embedding-channel/graph-symbolic",
            "embedding-channel/trace-symbolic",
        ),
        "stages": tuple(row["id"] for row in RETRIEVAL_STAGE_DEFINITIONS),
        "fusion": "local-rank-fusion",
        "expansion": "source-remains-local; only capability requirements may leave the workspace",
    },
    {
        "id": "retrieval-profile/low-context-agent",
        "channels": (
            "embedding-channel/intent-dense",
            "embedding-channel/lexical-sparse",
            "embedding-channel/type-symbolic",
        ),
        "stages": tuple(row["id"] for row in RETRIEVAL_STAGE_DEFINITIONS),
        "fusion": "rank-fusion-plus-deterministic-compatibility",
        "expansion": "sketch-then-contract-then-evidence-then-implementation",
    },
)


def _sources() -> list[dict[str, Any]]:
    return [
        _candidate(
            id=source_id,
            title=title,
            url=url,
            category=category,
            design_use=design_use,
            evidence_role="design-reference-not-primitive-proof",
        )
        for source_id, title, url, category, design_use in SOURCE_DEFINITIONS
    ]


def _hot_columns() -> list[dict[str, Any]]:
    return [
        _candidate(
            id=f"hot-column/{name}",
            name=name.replace("-", "_"),
            logical_type=logical_type,
            index_role=index_role,
            purpose=purpose,
            storage="primitive-hot-row",
            population_status=POPULATION_STATUS,
        )
        for name, logical_type, index_role, purpose in HOT_COLUMN_DEFINITIONS
    ]


def _normalized_features() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for (facet_id, path, value_kind, facet_purpose), (
        property_id,
        suffix,
        materialization,
        property_purpose,
    ) in product(ABI_FACET_DEFINITIONS, ABI_PROPERTY_DEFINITIONS):
        rows.append(
            _candidate(
                id=f"semantic-feature/{facet_id}/{property_id}",
                feature_path=f"{path}.{suffix}",
                facet=facet_id,
                property=property_id,
                value_kind=value_kind,
                purpose=f"{property_purpose} for {facet_purpose.lower()}",
                storage="normalized-feature-dictionary",
                materialization=materialization,
                population_status=POPULATION_STATUS,
            )
        )
    return rows


def _description_views() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for (facet_id, question, evidence_fields, embedding_family), (
        register_id,
        register_instruction,
    ), (frame_id, frame_instruction) in product(
        DESCRIPTION_FACET_DEFINITIONS,
        DESCRIPTION_REGISTER_DEFINITIONS,
        DESCRIPTION_FRAME_DEFINITIONS,
    ):
        rows.append(
            _candidate(
                id=f"description-view/{facet_id}/{register_id}/{frame_id}",
                facet=facet_id,
                register=register_id,
                frame=frame_id,
                question=question,
                instruction=f"{frame_instruction} {register_instruction}",
                grounding_fields=list(evidence_fields),
                grounding_policy="every-claim-must-resolve-to-source-or-executable-evidence",
                sentence_contract="one-complete-sentence",
                embedding_family=embedding_family,
                storage="description-view-store-not-hot-row",
                population_status="unpopulated-view-specification",
            )
        )
    return rows


def _transform_applies(value_kind: str, transform: dict[str, Any]) -> bool:
    kinds = set(transform["kinds"])
    return "all" in kinds or value_kind in kinds


def _blocker_variables() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for (dimension_id, source_path, value_kind, hard_constraint, purpose), transform in product(
        BLOCKER_DIMENSION_DEFINITIONS,
        BLOCKER_TRANSFORM_DEFINITIONS,
    ):
        if not _transform_applies(value_kind, transform):
            continue
        # Equality is not compatibility for refinements, version ranges, policy sets, authorization scopes,
        # destinations, or most other semantic-ABI dimensions.  Only an explicitly pinned workspace lock has
        # safe exact-identity semantics.  A workspace-policy partition may reject only when the policy compiler
        # has produced an explicit forbidden class; every other transform remains recall-oriented until the
        # full compatibility solver runs.
        exact_identity_hard_filter = (
            hard_constraint
            and dimension_id == "workspace-lock"
            and transform["id"] == "canonical-exact"
        )
        explicit_policy_hard_filter = (
            hard_constraint and transform["id"] == "workspace-policy-partition"
        )
        constraint_role = (
            "hard-exact-identity-filter"
            if exact_identity_hard_filter
            else "hard-explicit-policy-filter"
            if explicit_policy_hard_filter
            else "candidate-generation-only"
        )
        rows.append(
            _candidate(
                id=f"blocker-variable/{dimension_id}/{transform['id']}",
                dimension=dimension_id,
                source_path=source_path,
                value_kind=value_kind,
                transform=transform["id"],
                parameters=transform["parameter"],
                index_family=transform["index_family"],
                purpose=f"{transform['description']} for {purpose.lower()}",
                constraint_role=constraint_role,
                missing_value_behavior=(
                    "reject-only-when-the-workspace-policy-explicitly-requires-this-dimension"
                    if hard_constraint
                    else "do-not-block"
                ),
                acceptance_policy=(
                    "reject-only-an-explicit-forbidden-policy-partition-then-recheck-the-full-semantic-abi"
                    if explicit_policy_hard_filter
                    else "recheck-against-full-semantic-abi-and-policy-after-retrieval"
                ),
                storage="derived-blocker-feature-store",
                population_status=POPULATION_STATUS,
            )
        )
    return rows


def _embedding_models() -> list[dict[str, Any]]:
    return [
        _candidate(
            **definition,
            storage="model-registry",
            adoption_status="candidate-requires-license-quality-latency-and-cost-evaluation",
        )
        for definition in EMBEDDING_MODEL_DEFINITIONS
    ]


def _embedding_channels() -> list[dict[str, Any]]:
    return [
        _candidate(
            **definition,
            vector_space_id=f"vector-space/{definition['id'].split('/', 1)[1]}",
            cross_model_rule="never-average-vectors-from-incompatible-model-spaces",
            fusion_rule="retain-channel-and-model-provenance-then-fuse-ranked-results",
            population_status=POPULATION_STATUS,
        )
        for definition in EMBEDDING_CHANNEL_DEFINITIONS
    ]


def _ann_profiles() -> list[dict[str, Any]]:
    return [
        _candidate(
            **definition,
            scale_target_floor=DESIGN_TARGET_PRIMITIVE_FLOOR,
            scale_status=SCALE_STATUS,
            selection_gate="held-out-recall-latency-memory-build-time-update-and-cost-benchmark",
        )
        for definition in ANN_INDEX_PROFILE_DEFINITIONS
    ]


def _retrieval_stages() -> list[dict[str, Any]]:
    return [_candidate(**definition) for definition in RETRIEVAL_STAGE_DEFINITIONS]


def _retrieval_profiles() -> list[dict[str, Any]]:
    return [
        _candidate(
            **definition,
            scale_target_floor=DESIGN_TARGET_PRIMITIVE_FLOOR,
            scale_status=SCALE_STATUS,
            candidate_budget="derived-from-request-latency-token-and-recall-policy",
            execution_rule="retrieval-is-probabilistic-acceptance-is-deterministic",
        )
        for definition in RETRIEVAL_PROFILE_DEFINITIONS
    ]


def _count_manifest(registry: dict[str, Any]) -> dict[str, int]:
    storage = registry["storage_contract"]
    retrieval = registry["retrieval_design"]
    hot = len(storage["hot_columns"])
    normalized = len(storage["normalized_feature_dictionary"])
    return {
        "hot_columns": hot,
        "normalized_semantic_features": normalized,
        "semantic_abi_fields_total": hot + normalized,
        "description_view_specs": len(storage["description_view_specs"]),
        "blocker_variables": len(storage["blocker_variables"]),
        "embedding_models": len(retrieval["embedding_models"]),
        "embedding_channels": len(retrieval["embedding_channels"]),
        "ann_index_profiles": len(retrieval["ann_index_profiles"]),
        "retrieval_stages": len(retrieval["stages"]),
        "retrieval_profiles": len(retrieval["profiles"]),
        "primary_sources": len(registry["research_sources"]),
    }


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def build_registry() -> dict[str, Any]:
    """Build the deterministic candidate registry entirely from the canonical definitions above."""
    registry: dict[str, Any] = _candidate(
        id=REGISTRY_ID,
        schema_version=SCHEMA_VERSION,
        population_status=POPULATION_STATUS,
        claim_boundary={
            "populated_corpus": False,
            "measured_at_target_scale": False,
            "retrieval_quality_proven": False,
            "production_schema_approved": False,
            "meaning": "This artifact enumerates candidate specifications only.",
        },
        scale_design=_candidate(
            id="scale-design/primitive-semantic-linker",
            primitive_floor=DESIGN_TARGET_PRIMITIVE_FLOOR,
            status=SCALE_STATUS,
            storage_separation={
                "hot_metadata": "partitioned relational or columnar row",
                "normalized_features": "normalized feature table or document projection",
                "descriptions": "cold view store with only benchmark-selected hot views indexed",
                "dense_vectors": "one physical index per model and semantic channel",
                "sparse_vectors": "inverted indexes",
                "bodies_and_evidence": "content-addressed object storage",
                "graph": "typed adjacency and recipe/adapter projections",
            },
            sharding_keys=(
                "tenant-and-registry-tier",
                "trust-and-policy-partition",
                "capability-family",
                "language-runtime-framework",
                "embedding-model-and-channel",
            ),
            physical_shard_rule="derive-from-measured-recall-latency-memory-update-and-cost-envelopes",
        ),
        storage_contract=_candidate(
            id="storage-contract/primitive-semantic-abi",
            hot_columns=_hot_columns(),
            normalized_feature_dictionary=_normalized_features(),
            description_view_specs=_description_views(),
            blocker_variables=_blocker_variables(),
            separation_rule=(
                "Only hot_columns are proposed as physical columns on the latency-sensitive primitive row; "
                "all other entries are normalized, derived, or cold specifications."
            ),
        ),
        retrieval_design=_candidate(
            id="retrieval-design/primitive-semantic-linker",
            embedding_models=_embedding_models(),
            embedding_channels=_embedding_channels(),
            ann_index_profiles=_ann_profiles(),
            stages=_retrieval_stages(),
            profiles=_retrieval_profiles(),
            fusion_rule="calibrated-rank-fusion-or-learned-reranking-with-channel-provenance",
            acceptance_rule="exact-types-effects-policy-lock-provenance-and-tests",
        ),
        research_sources=_sources(),
    )
    registry["counts"] = _candidate(id="manifest/computed-counts", **_count_manifest(registry))
    # Freeze tuples and any other Python-only containers into their exact JSON representation so
    # callers receive the same object that ``--emit`` persists.
    registry = json.loads(_canonical_bytes(registry))
    payload_digest = hashlib.sha256(_canonical_bytes(registry)).hexdigest()
    registry["integrity"] = _candidate(
        id="integrity/registry-content",
        algorithm="sha256",
        digest=payload_digest,
        coverage="canonical-json-before-integrity-field",
    )
    return registry


def summary(registry: dict[str, Any] | None = None) -> dict[str, Any]:
    registry = registry or build_registry()
    return {
        "id": registry["id"],
        **BOUNDARY,
        "population_status": registry["population_status"],
        "scale_target_floor": registry["scale_design"]["primitive_floor"],
        "scale_status": registry["scale_design"]["status"],
        "counts": {key: value for key, value in registry["counts"].items() if key not in {"id", *BOUNDARY}},
        "digest": registry["integrity"]["digest"],
    }


def _all_ids(records: Iterable[dict[str, Any]]) -> list[str]:
    return [str(record["id"]) for record in records]


def _assert_unique(records: Iterable[dict[str, Any]], label: str) -> None:
    ids = _all_ids(records)
    if len(ids) != len(set(ids)):
        raise AssertionError(f"duplicate ids in {label}")


def _assert_candidate_records(records: Iterable[dict[str, Any]], label: str) -> None:
    for record in records:
        if record.get("candidate") is not True or record.get("serves_truth") is not False:
            raise AssertionError(f"non-candidate record in {label}: {record.get('id')}")


def _write_registry(path: Path, registry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def run_self_test() -> dict[str, Any]:
    """Offline proof of determinism, count floors, boundaries, references, and storage separation."""
    first = build_registry()
    second = build_registry()
    if _canonical_bytes(first) != _canonical_bytes(second):
        raise AssertionError("registry build is not deterministic")

    storage = first["storage_contract"]
    retrieval = first["retrieval_design"]
    counts = first["counts"]
    if counts["semantic_abi_fields_total"] < MINIMUM_GENERATED_SPEC_COUNT:
        raise AssertionError("semantic ABI field count below requested floor")
    if counts["description_view_specs"] < MINIMUM_GENERATED_SPEC_COUNT:
        raise AssertionError("description view count below requested floor")
    if counts["blocker_variables"] < MINIMUM_GENERATED_SPEC_COUNT:
        raise AssertionError("blocker variable count below requested floor")
    if first["scale_design"]["primitive_floor"] < DESIGN_TARGET_PRIMITIVE_FLOOR:
        raise AssertionError("scale target below requested design floor")

    record_groups: dict[str, list[dict[str, Any]]] = {
        "hot columns": storage["hot_columns"],
        "normalized features": storage["normalized_feature_dictionary"],
        "description views": storage["description_view_specs"],
        "blocker variables": storage["blocker_variables"],
        "embedding models": retrieval["embedding_models"],
        "embedding channels": retrieval["embedding_channels"],
        "ann profiles": retrieval["ann_index_profiles"],
        "retrieval stages": retrieval["stages"],
        "retrieval profiles": retrieval["profiles"],
        "research sources": first["research_sources"],
    }
    for label, records in record_groups.items():
        _assert_unique(records, label)
        _assert_candidate_records(records, label)

    hot_names = {row["name"] for row in storage["hot_columns"]}
    normalized_paths = {row["feature_path"] for row in storage["normalized_feature_dictionary"]}
    if hot_names & normalized_paths:
        raise AssertionError("hot and normalized feature namespaces overlap")
    if {row["storage"] for row in storage["hot_columns"]} != {"primitive-hot-row"}:
        raise AssertionError("a hot column escaped the hot row")
    if {row["storage"] for row in storage["normalized_feature_dictionary"]} != {
        "normalized-feature-dictionary"
    }:
        raise AssertionError("a normalized semantic feature was mislabeled as a hot column")
    if any(row["population_status"] != "unpopulated-view-specification" for row in storage["description_view_specs"]):
        raise AssertionError("description specification falsely claims population")
    unsafe_exact_hard = [
        row
        for row in storage["blocker_variables"]
        if row["transform"] == "canonical-exact"
        and row["constraint_role"].startswith("hard-")
        and row["dimension"] != "workspace-lock"
    ]
    if unsafe_exact_hard:
        raise AssertionError(
            "canonical equality was mislabeled as compatibility for: "
            + ", ".join(row["dimension"] for row in unsafe_exact_hard[:5])
        )
    policy_hard = [
        row for row in storage["blocker_variables"]
        if row["constraint_role"] == "hard-explicit-policy-filter"
    ]
    if not policy_hard or any("explicit-forbidden" not in row["acceptance_policy"] for row in policy_hard):
        raise AssertionError("hard policy blockers must reject only explicit forbidden partitions")

    source_ids = set(_all_ids(first["research_sources"]))
    model_ids = set(_all_ids(retrieval["embedding_models"]))
    channel_ids = set(_all_ids(retrieval["embedding_channels"]))
    stage_ids = set(_all_ids(retrieval["stages"]))
    for model in retrieval["embedding_models"]:
        if not set(model["source_ids"]) <= source_ids:
            raise AssertionError(f"unknown model source reference: {model['id']}")
    for channel in retrieval["embedding_channels"]:
        if not set(channel["model_ids"]) <= model_ids:
            raise AssertionError(f"unknown embedding model reference: {channel['id']}")
        if channel["cross_model_rule"] != "never-average-vectors-from-incompatible-model-spaces":
            raise AssertionError(f"unsafe cross-model fusion rule: {channel['id']}")
    for profile in retrieval["profiles"]:
        if not set(profile["channels"]) <= channel_ids or not set(profile["stages"]) <= stage_ids:
            raise AssertionError(f"unknown retrieval profile reference: {profile['id']}")
    for ann_profile in retrieval["ann_index_profiles"]:
        if not set(ann_profile["source_ids"]) <= source_ids:
            raise AssertionError(f"unknown ANN source reference: {ann_profile['id']}")
    if any(not str(row["url"]).startswith("https://") for row in first["research_sources"]):
        raise AssertionError("research sources must use HTTPS primary-source URLs")
    if first.get("candidate") is not True or first.get("serves_truth") is not False:
        raise AssertionError("registry boundary changed")
    if first["claim_boundary"]["populated_corpus"] is not False:
        raise AssertionError("registry falsely claims a populated corpus")

    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "registry.json"
        _write_registry(output, first)
        round_trip = json.loads(output.read_text(encoding="utf-8"))
        if round_trip != first:
            raise AssertionError("emitted registry failed JSON round trip")

    return {
        "status": "PASS",
        **BOUNDARY,
        "counts": {key: value for key, value in counts.items() if key not in {"id", *BOUNDARY}},
        "population_status": first["population_status"],
        "digest": first["integrity"]["digest"],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit", metavar="PATH", help="Write the complete machine-readable registry JSON")
    parser.add_argument("--summary", action="store_true", help="Print computed counts and claim boundaries")
    parser.add_argument("--self-test", action="store_true", help="Run the deterministic offline proof")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    emitted_or_printed = False
    if args.self_test:
        print(json.dumps(run_self_test(), indent=2, sort_keys=True))
        emitted_or_printed = True

    registry: dict[str, Any] | None = None
    if args.emit:
        registry = build_registry()
        if args.emit == "-":
            print(json.dumps(registry, indent=2, sort_keys=True, ensure_ascii=False))
        else:
            output = Path(args.emit).expanduser().resolve()
            _write_registry(output, registry)
            print(json.dumps({"status": "emitted", "path": str(output), **summary(registry)}, indent=2, sort_keys=True))
        emitted_or_printed = True

    if args.summary or not emitted_or_printed:
        print(json.dumps(summary(registry), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
