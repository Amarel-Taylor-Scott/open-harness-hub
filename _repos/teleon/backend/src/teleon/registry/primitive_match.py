"""Hybrid primitive matching for Teleon registry candidates.

This layer answers a more useful question than ordinary search:

    Can this primitive be chained into the requested graph now, after a deterministic adapter, only after
    a generated/non-deterministic edit, or not at all?

The implementation is deterministic and candidate-only. Semantic ranking uses the existing lexical hash
embedding floor from ``registry.enrich``; future learned embeddings can replace that function behind the
same contract. No search hit is promoted as truth here.
"""
from __future__ import annotations

import math
import re
import sys
from collections import Counter
from pathlib import Path

py_const_src_teleon_registry_primitive_match__REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
if str(py_const_src_teleon_registry_primitive_match__REPO) not in sys.path:
    sys.path.insert(0, str(py_const_src_teleon_registry_primitive_match__REPO))

from src.teleon.registry.composition_affinity import (
    py_function_src_teleon_registry_composition_affinity__affinity_boost,
    py_function_src_teleon_registry_composition_affinity__pair_id,
)
from src.teleon.registry.enrich import py_function_src_teleon_registry_enrich__embedding, py_function_src_teleon_registry_enrich__enrich_record


py_const_src_teleon_registry_primitive_match__FIT_EXACT_MATCH = "exact_match"
py_const_src_teleon_registry_primitive_match__FIT_DETERMINISTIC_EDIT_MATCH = "deterministic_edit_match"
py_const_src_teleon_registry_primitive_match__FIT_NONDETERMINISTIC_EDIT_MATCH = "nondeterministic_edit_match"
py_const_src_teleon_registry_primitive_match__FIT_INCOMPATIBLE = "incompatible"

py_const_src_teleon_registry_primitive_match__MUTATION_SCALAR_TO_SEQUENCE = "scalar_to_sequence"
py_const_src_teleon_registry_primitive_match__MUTATION_OUTPUT_FIELD_WRAPPER = "output_field_wrapper"
py_const_src_teleon_registry_primitive_match__MUTATION_FIELD_RENAME_ADAPTER = "field_rename_adapter"
py_const_src_teleon_registry_primitive_match__MUTATION_RETRY_CACHE_RATE_LIMIT_ADAPTER = "retry_cache_rate_limit_adapter"
py_const_src_teleon_registry_primitive_match__MUTATION_MODEL_COST_DOWNSHIFT = "model_cost_downshift"
py_const_src_teleon_registry_primitive_match__MUTATION_BROWSER_TO_DETERMINISTIC_EXTRACTOR = "browser_to_deterministic_extractor"
py_const_src_teleon_registry_primitive_match__MUTATION_LOCAL_API_IMPLEMENTATION_SWAP = "local_api_implementation_swap"
py_const_src_teleon_registry_primitive_match__MUTATION_GENERATED_ADAPTER_CANDIDATE = "generated_adapter_candidate"

py_const_src_teleon_registry_primitive_match__SEARCH_DIMENSIONS = (
    "exact",
    "keyword",
    "label",
    "semantic",
    "input_contract",
    "output_contract",
    "graph_neighborhood",
    "blocking_index",
    "deterministic_mutation",
    "nondeterministic_mutation",
)

py_const_src_teleon_registry_primitive_match__TOKEN_RE = re.compile(r"[a-z0-9]+")
py_const_src_teleon_registry_primitive_match__STOPWORDS = {
    "the", "and", "for", "with", "from", "into", "this", "that", "then", "only", "your",
    "shape", "fields", "field", "string", "integer", "number", "object", "array", "list",
    "dict", "mapping", "path", "scalar", "unknown",
}
py_const_src_teleon_registry_primitive_match__BLOCK_MIN_SCORE = 0.08
py_const_src_teleon_registry_primitive_match__NONDETERMINISTIC_MIN_SIGNAL = 0.22
#: cap on the OPTIONAL learned composition-affinity additive boost. Kept strictly below the smallest
#: fit-class score delta (0.12, nondeterministic) so affinity can nudge ranking between otherwise-tied
#: candidates but can NEVER outweigh a contract-compatibility class on its own (boost-only law).
py_const_src_teleon_registry_primitive_match__AFFINITY_BOOST_CAP = 0.1
py_const_src_teleon_registry_primitive_match__SEMANTIC_BUCKET_COUNT = 8
py_const_src_teleon_registry_primitive_match__BLOCKED_RERANK_MAX_CANDIDATES = 500
py_const_src_teleon_registry_primitive_match__GENERIC_CONTRACT_SHAPES = {"object", "dict", "mapping", "scalar", "unknown", "any"}
py_const_src_teleon_registry_primitive_match__IO_MUTATIONS = {py_const_src_teleon_registry_primitive_match__MUTATION_SCALAR_TO_SEQUENCE, py_const_src_teleon_registry_primitive_match__MUTATION_OUTPUT_FIELD_WRAPPER, py_const_src_teleon_registry_primitive_match__MUTATION_FIELD_RENAME_ADAPTER}
py_const_src_teleon_registry_primitive_match__BLOCK_PROFILE_FIELDS = (
    "exact_keys",
    "keyword_keys",
    "label_keys",
    "input_signature",
    "output_signature",
    "graph_signature",
    "semantic_text",
    "semantic_embedding",
    "mutation_hints",
)
py_const_src_teleon_registry_primitive_match__BLOCKING_INDEX_FIELDS = (
    "candidate_count",
    "profile_fields",
    "inverted",
    "profile_keys",
    "serves_truth",
)
py_const_src_teleon_registry_primitive_match__GRAPH_STATUS_CHAINABLE_AS_IS = "chainable_as_is"
py_const_src_teleon_registry_primitive_match__GRAPH_STATUS_CHAINABLE_WITH_ADAPTERS = "chainable_with_adapter_nodes"
py_const_src_teleon_registry_primitive_match__GRAPH_STATUS_GENERATED_ADAPTER_REQUIRED = "candidate_generated_adapter_required"
py_const_src_teleon_registry_primitive_match__GRAPH_STATUS_NOT_CHAINABLE = "not_chainable"


def py_function_src_teleon_registry_primitive_match__tokens(py_arg_src_teleon_registry_primitive_match__tokens__text: str) -> set[str]:
    return {token for token in py_const_src_teleon_registry_primitive_match__TOKEN_RE.findall(py_arg_src_teleon_registry_primitive_match__tokens__text.lower()) if len(token) >= 2 and token not in py_const_src_teleon_registry_primitive_match__STOPWORDS}


def py_function_src_teleon_registry_primitive_match__as_list(py_arg_src_teleon_registry_primitive_match__as_list__value) -> list:
    if py_arg_src_teleon_registry_primitive_match__as_list__value is None:
        return []
    if isinstance(py_arg_src_teleon_registry_primitive_match__as_list__value, list):
        return py_arg_src_teleon_registry_primitive_match__as_list__value
    if isinstance(py_arg_src_teleon_registry_primitive_match__as_list__value, tuple):
        return list(py_arg_src_teleon_registry_primitive_match__as_list__value)
    if isinstance(py_arg_src_teleon_registry_primitive_match__as_list__value, set):
        return sorted(py_arg_src_teleon_registry_primitive_match__as_list__value)
    return [py_arg_src_teleon_registry_primitive_match__as_list__value]


def py_function_src_teleon_registry_primitive_match__text_blob(py_arg_src_teleon_registry_primitive_match__text_blob__record: dict) -> str:
    py_local_src_teleon_registry_primitive_match__text_blob__parts: list[str] = []
    for py_local_src_teleon_registry_primitive_match__text_blob__key in ("id", "name", "purpose", "problem", "solution", "description", "long_description", "execution_surface"):
        if py_arg_src_teleon_registry_primitive_match__text_blob__record.get(py_local_src_teleon_registry_primitive_match__text_blob__key):
            py_local_src_teleon_registry_primitive_match__text_blob__parts.append(str(py_arg_src_teleon_registry_primitive_match__text_blob__record[py_local_src_teleon_registry_primitive_match__text_blob__key]))
    for py_local_src_teleon_registry_primitive_match__text_blob__key in ("labels", "tags", "keywords", "capabilities", "search_terms"):
        py_local_src_teleon_registry_primitive_match__text_blob__parts.extend(str(v) for v in py_function_src_teleon_registry_primitive_match__as_list(py_arg_src_teleon_registry_primitive_match__text_blob__record.get(py_local_src_teleon_registry_primitive_match__text_blob__key)))
    py_local_src_teleon_registry_primitive_match__text_blob__metadata = py_arg_src_teleon_registry_primitive_match__text_blob__record.get("metadata") or {}
    if isinstance(py_local_src_teleon_registry_primitive_match__text_blob__metadata, dict):
        for py_local_src_teleon_registry_primitive_match__text_blob__key in ("labels", "tags", "keywords", "use_cases"):
            py_local_src_teleon_registry_primitive_match__text_blob__parts.extend(str(v) for v in py_function_src_teleon_registry_primitive_match__as_list(py_local_src_teleon_registry_primitive_match__text_blob__metadata.get(py_local_src_teleon_registry_primitive_match__text_blob__key)))
    for py_local_src_teleon_registry_primitive_match__text_blob__contract_key in ("input_contract", "output_contract"):
        py_local_src_teleon_registry_primitive_match__text_blob__contract = py_arg_src_teleon_registry_primitive_match__text_blob__record.get(py_local_src_teleon_registry_primitive_match__text_blob__contract_key)
        if isinstance(py_local_src_teleon_registry_primitive_match__text_blob__contract, dict):
            py_local_src_teleon_registry_primitive_match__text_blob__parts.append(py_function_src_teleon_registry_primitive_match__flatten_contract_text(py_local_src_teleon_registry_primitive_match__text_blob__contract))
    return " ".join(py_local_src_teleon_registry_primitive_match__text_blob__parts)


def py_function_src_teleon_registry_primitive_match__semantic_text(py_arg_src_teleon_registry_primitive_match__semantic_text__record: dict) -> str:
    """Search text with schema boilerplate removed so generic contracts do not create false matches."""
    return " ".join(sorted(py_function_src_teleon_registry_primitive_match__tokens(py_function_src_teleon_registry_primitive_match__text_blob(py_arg_src_teleon_registry_primitive_match__semantic_text__record))))


def py_function_src_teleon_registry_primitive_match__flatten_contract_text(py_arg_src_teleon_registry_primitive_match__flatten_contract_text__contract: dict) -> str:
    py_local_src_teleon_registry_primitive_match__flatten_contract_text__values: list[str] = []
    for py_local_src_teleon_registry_primitive_match__flatten_contract_text__key, py_local_src_teleon_registry_primitive_match__flatten_contract_text__value in py_arg_src_teleon_registry_primitive_match__flatten_contract_text__contract.items():
        if isinstance(py_local_src_teleon_registry_primitive_match__flatten_contract_text__value, dict):
            py_local_src_teleon_registry_primitive_match__flatten_contract_text__values.append(py_local_src_teleon_registry_primitive_match__flatten_contract_text__key)
            py_local_src_teleon_registry_primitive_match__flatten_contract_text__values.append(py_function_src_teleon_registry_primitive_match__flatten_contract_text(py_local_src_teleon_registry_primitive_match__flatten_contract_text__value))
        elif isinstance(py_local_src_teleon_registry_primitive_match__flatten_contract_text__value, list):
            py_local_src_teleon_registry_primitive_match__flatten_contract_text__values.append(py_local_src_teleon_registry_primitive_match__flatten_contract_text__key)
            py_local_src_teleon_registry_primitive_match__flatten_contract_text__values.extend(py_function_src_teleon_registry_primitive_match__flatten_contract_text(v) if isinstance(v, dict) else str(v) for v in py_local_src_teleon_registry_primitive_match__flatten_contract_text__value)
        else:
            py_local_src_teleon_registry_primitive_match__flatten_contract_text__values.append(str(py_local_src_teleon_registry_primitive_match__flatten_contract_text__key))
            py_local_src_teleon_registry_primitive_match__flatten_contract_text__values.append(str(py_local_src_teleon_registry_primitive_match__flatten_contract_text__value))
    return " ".join(py_local_src_teleon_registry_primitive_match__flatten_contract_text__values)


def py_function_src_teleon_registry_primitive_match__primitive_labels(py_arg_src_teleon_registry_primitive_match__primitive_labels__record: dict) -> set[str]:
    py_local_src_teleon_registry_primitive_match__primitive_labels__labels = set()
    for py_local_src_teleon_registry_primitive_match__primitive_labels__key in ("labels", "tags", "capabilities"):
        py_local_src_teleon_registry_primitive_match__primitive_labels__labels |= {str(v).lower() for v in py_function_src_teleon_registry_primitive_match__as_list(py_arg_src_teleon_registry_primitive_match__primitive_labels__record.get(py_local_src_teleon_registry_primitive_match__primitive_labels__key))}
    py_local_src_teleon_registry_primitive_match__primitive_labels__metadata = py_arg_src_teleon_registry_primitive_match__primitive_labels__record.get("metadata") or {}
    if isinstance(py_local_src_teleon_registry_primitive_match__primitive_labels__metadata, dict):
        for py_local_src_teleon_registry_primitive_match__primitive_labels__key in ("labels", "tags", "keywords", "use_cases"):
            py_local_src_teleon_registry_primitive_match__primitive_labels__labels |= {str(v).lower() for v in py_function_src_teleon_registry_primitive_match__as_list(py_local_src_teleon_registry_primitive_match__primitive_labels__metadata.get(py_local_src_teleon_registry_primitive_match__primitive_labels__key))}
    return py_local_src_teleon_registry_primitive_match__primitive_labels__labels | py_function_src_teleon_registry_primitive_match__tokens(py_function_src_teleon_registry_primitive_match__text_blob({"labels": sorted(py_local_src_teleon_registry_primitive_match__primitive_labels__labels)}))


def py_function_src_teleon_registry_primitive_match__primitive_keywords(py_arg_src_teleon_registry_primitive_match__primitive_keywords__record: dict) -> set[str]:
    py_local_src_teleon_registry_primitive_match__primitive_keywords__enriched = py_function_src_teleon_registry_enrich__enrich_record({"text": py_function_src_teleon_registry_primitive_match__semantic_text(py_arg_src_teleon_registry_primitive_match__primitive_keywords__record)})["_enrichment"]
    return {token for token in py_local_src_teleon_registry_primitive_match__primitive_keywords__enriched["keywords"] if token not in py_const_src_teleon_registry_primitive_match__STOPWORDS} | py_function_src_teleon_registry_primitive_match__tokens(py_function_src_teleon_registry_primitive_match__text_blob(py_arg_src_teleon_registry_primitive_match__primitive_keywords__record))


def py_function_src_teleon_registry_primitive_match__cosine(py_arg_src_teleon_registry_primitive_match__cosine__left: list[float], py_arg_src_teleon_registry_primitive_match__cosine__right: list[float]) -> float:
    py_local_src_teleon_registry_primitive_match__cosine__dot = sum(a * b for a, b in zip(py_arg_src_teleon_registry_primitive_match__cosine__left, py_arg_src_teleon_registry_primitive_match__cosine__right))
    py_local_src_teleon_registry_primitive_match__cosine__left_norm = math.sqrt(sum(a * a for a in py_arg_src_teleon_registry_primitive_match__cosine__left))
    py_local_src_teleon_registry_primitive_match__cosine__right_norm = math.sqrt(sum(b * b for b in py_arg_src_teleon_registry_primitive_match__cosine__right))
    return py_local_src_teleon_registry_primitive_match__cosine__dot / (py_local_src_teleon_registry_primitive_match__cosine__left_norm * py_local_src_teleon_registry_primitive_match__cosine__right_norm) if py_local_src_teleon_registry_primitive_match__cosine__left_norm and py_local_src_teleon_registry_primitive_match__cosine__right_norm else 0.0


def py_function_src_teleon_registry_primitive_match__shape(py_arg_src_teleon_registry_primitive_match__shape__contract: dict | None) -> str:
    if not isinstance(py_arg_src_teleon_registry_primitive_match__shape__contract, dict):
        return "unknown"
    py_local_src_teleon_registry_primitive_match__shape__raw = py_arg_src_teleon_registry_primitive_match__shape__contract.get("shape") or py_arg_src_teleon_registry_primitive_match__shape__contract.get("type") or py_arg_src_teleon_registry_primitive_match__shape__contract.get("kind") or "unknown"
    return str(py_local_src_teleon_registry_primitive_match__shape__raw).lower().replace("-", "_")


def py_function_src_teleon_registry_primitive_match__fields(py_arg_src_teleon_registry_primitive_match__fields__contract: dict | None) -> set[str]:
    if not isinstance(py_arg_src_teleon_registry_primitive_match__fields__contract, dict):
        return set()
    py_local_src_teleon_registry_primitive_match__fields__raw_fields = py_arg_src_teleon_registry_primitive_match__fields__contract.get("fields") or py_arg_src_teleon_registry_primitive_match__fields__contract.get("properties") or {}
    if isinstance(py_local_src_teleon_registry_primitive_match__fields__raw_fields, dict):
        py_local_src_teleon_registry_primitive_match__fields__out = {str(k).lower() for k in py_local_src_teleon_registry_primitive_match__fields__raw_fields}
    else:
        py_local_src_teleon_registry_primitive_match__fields__out = {str(v).lower() for v in py_function_src_teleon_registry_primitive_match__as_list(py_local_src_teleon_registry_primitive_match__fields__raw_fields)}
    for py_local_src_teleon_registry_primitive_match__fields__param in py_function_src_teleon_registry_primitive_match__as_list(py_arg_src_teleon_registry_primitive_match__fields__contract.get("parameters")):
        if isinstance(py_local_src_teleon_registry_primitive_match__fields__param, dict) and py_local_src_teleon_registry_primitive_match__fields__param.get("name"):
            py_local_src_teleon_registry_primitive_match__fields__out.add(str(py_local_src_teleon_registry_primitive_match__fields__param["name"]).lower())
    for py_local_src_teleon_registry_primitive_match__fields__nested_key in ("items_contract", "item_output_contract"):
        if isinstance(py_arg_src_teleon_registry_primitive_match__fields__contract.get(py_local_src_teleon_registry_primitive_match__fields__nested_key), dict):
            py_local_src_teleon_registry_primitive_match__fields__out |= py_function_src_teleon_registry_primitive_match__fields(py_arg_src_teleon_registry_primitive_match__fields__contract[py_local_src_teleon_registry_primitive_match__fields__nested_key])
    return py_local_src_teleon_registry_primitive_match__fields__out


def py_function_src_teleon_registry_primitive_match__graph_neighbors(py_arg_src_teleon_registry_primitive_match__graph_neighbors__record: dict) -> set[str]:
    py_local_src_teleon_registry_primitive_match__graph_neighbors__out = set()
    for py_local_src_teleon_registry_primitive_match__graph_neighbors__edge in py_function_src_teleon_registry_primitive_match__as_list(py_arg_src_teleon_registry_primitive_match__graph_neighbors__record.get("graph_edges")):
        if isinstance(py_local_src_teleon_registry_primitive_match__graph_neighbors__edge, dict):
            for py_local_src_teleon_registry_primitive_match__graph_neighbors__key in ("from", "to", "source", "target", "src", "dst"):
                if py_local_src_teleon_registry_primitive_match__graph_neighbors__edge.get(py_local_src_teleon_registry_primitive_match__graph_neighbors__key):
                    py_local_src_teleon_registry_primitive_match__graph_neighbors__out.add(str(py_local_src_teleon_registry_primitive_match__graph_neighbors__edge[py_local_src_teleon_registry_primitive_match__graph_neighbors__key]).lower())
        elif py_local_src_teleon_registry_primitive_match__graph_neighbors__edge:
            py_local_src_teleon_registry_primitive_match__graph_neighbors__out.add(str(py_local_src_teleon_registry_primitive_match__graph_neighbors__edge).lower())
    return py_local_src_teleon_registry_primitive_match__graph_neighbors__out


def py_function_src_teleon_registry_primitive_match__contract_signature(py_arg_src_teleon_registry_primitive_match__contract_signature__contract: dict | None) -> dict:
    """Cheap, deterministic contract key used for blocking before expensive reranking."""
    return {
        "shape": py_function_src_teleon_registry_primitive_match__shape(py_arg_src_teleon_registry_primitive_match__contract_signature__contract),
        "fields": sorted(py_function_src_teleon_registry_primitive_match__fields(py_arg_src_teleon_registry_primitive_match__contract_signature__contract)),
    }


def py_function_src_teleon_registry_primitive_match__mutation_hints(py_arg_src_teleon_registry_primitive_match__mutation_hints__record: dict) -> list[str]:
    """Primitive-local mutation affordances that can be precomputed in the search index.

    These are not claims that a request needs the mutation. They are cheap blocking hints: a scalar input
    primitive can be batched, a scalar output can be wrapped, an LLM/browser scraper can be considered for
    cheaper or deterministic descent, and hosted/API primitives can be considered for local swaps.
    """
    py_local_src_teleon_registry_primitive_match__mutation_hints__hints: set[str] = set()
    py_local_src_teleon_registry_primitive_match__mutation_hints__input_shape = py_function_src_teleon_registry_primitive_match__shape(py_arg_src_teleon_registry_primitive_match__mutation_hints__record.get("input_contract"))
    py_local_src_teleon_registry_primitive_match__mutation_hints__output_shape = py_function_src_teleon_registry_primitive_match__shape(py_arg_src_teleon_registry_primitive_match__mutation_hints__record.get("output_contract"))
    py_local_src_teleon_registry_primitive_match__mutation_hints__labels = py_function_src_teleon_registry_primitive_match__primitive_labels(py_arg_src_teleon_registry_primitive_match__mutation_hints__record)
    if py_local_src_teleon_registry_primitive_match__mutation_hints__input_shape == "scalar":
        py_local_src_teleon_registry_primitive_match__mutation_hints__hints.add(py_const_src_teleon_registry_primitive_match__MUTATION_SCALAR_TO_SEQUENCE)
    if py_local_src_teleon_registry_primitive_match__mutation_hints__output_shape not in {"object", "dict", "mapping", "unknown", "any"}:
        py_local_src_teleon_registry_primitive_match__mutation_hints__hints.add(py_const_src_teleon_registry_primitive_match__MUTATION_OUTPUT_FIELD_WRAPPER)
    if {"llm", "model", "browser"} & py_local_src_teleon_registry_primitive_match__mutation_hints__labels:
        py_local_src_teleon_registry_primitive_match__mutation_hints__hints.add(py_const_src_teleon_registry_primitive_match__MUTATION_MODEL_COST_DOWNSHIFT)
    if {"llm", "browser", "scrape", "scraper"} & py_local_src_teleon_registry_primitive_match__mutation_hints__labels:
        py_local_src_teleon_registry_primitive_match__mutation_hints__hints.add(py_const_src_teleon_registry_primitive_match__MUTATION_BROWSER_TO_DETERMINISTIC_EXTRACTOR)
    if {"api", "hosted", "third_party", "third-party"} & py_local_src_teleon_registry_primitive_match__mutation_hints__labels:
        py_local_src_teleon_registry_primitive_match__mutation_hints__hints.add(py_const_src_teleon_registry_primitive_match__MUTATION_LOCAL_API_IMPLEMENTATION_SWAP)
    return sorted(py_local_src_teleon_registry_primitive_match__mutation_hints__hints)


def py_function_src_teleon_registry_primitive_match__blocking_profile(py_arg_src_teleon_registry_primitive_match__blocking_profile__record: dict) -> dict:
    """Precomputed hybrid blocking profile for registry rows and vector/search exports.

    The point is efficiency: exact keys, keyword keys, labels/facets, I/O signatures, graph neighbors,
    deterministic lexical semantic text/embedding, and mutation affordances can be stored once and reused by
    search instead of recomputing the whole row every query.
    """
    py_local_src_teleon_registry_primitive_match__blocking_profile__semantic_text = py_function_src_teleon_registry_primitive_match__semantic_text(py_arg_src_teleon_registry_primitive_match__blocking_profile__record)
    return {
        "exact_keys": sorted(
            {
                str(value).lower()
                for value in (
                    py_arg_src_teleon_registry_primitive_match__blocking_profile__record.get("id"),
                    py_arg_src_teleon_registry_primitive_match__blocking_profile__record.get("name"),
                )
                if value
            }
        ),
        "keyword_keys": sorted(py_function_src_teleon_registry_primitive_match__primitive_keywords(py_arg_src_teleon_registry_primitive_match__blocking_profile__record)),
        "label_keys": sorted(py_function_src_teleon_registry_primitive_match__primitive_labels(py_arg_src_teleon_registry_primitive_match__blocking_profile__record)),
        "input_signature": py_function_src_teleon_registry_primitive_match__contract_signature(py_arg_src_teleon_registry_primitive_match__blocking_profile__record.get("input_contract")),
        "output_signature": py_function_src_teleon_registry_primitive_match__contract_signature(py_arg_src_teleon_registry_primitive_match__blocking_profile__record.get("output_contract")),
        "graph_signature": sorted(
            set(str(value).lower() for value in py_function_src_teleon_registry_primitive_match__as_list(py_arg_src_teleon_registry_primitive_match__blocking_profile__record.get("graph_neighbors")))
            | py_function_src_teleon_registry_primitive_match__graph_neighbors(py_arg_src_teleon_registry_primitive_match__blocking_profile__record)
        ),
        "semantic_text": py_local_src_teleon_registry_primitive_match__blocking_profile__semantic_text,
        "semantic_embedding": py_function_src_teleon_registry_enrich__embedding({"text": py_local_src_teleon_registry_primitive_match__blocking_profile__semantic_text}),
        "mutation_hints": py_function_src_teleon_registry_primitive_match__mutation_hints(py_arg_src_teleon_registry_primitive_match__blocking_profile__record),
        "serves_truth": False,
    }


def py_function_src_teleon_registry_primitive_match__semantic_bucket_keys(py_arg_src_teleon_registry_primitive_match__semantic_bucket_keys__embedding: list[float]) -> list[str]:
    """Coarse deterministic semantic buckets used for pre-rerank candidate blocking.

    This is not the final semantic score. It is a cheap lexical-hash LSH-style lane: candidates sharing the
    strongest embedding dimensions are allowed into reranking; exact compatibility still has to be proven by
    classify_candidate().
    """
    py_local_src_teleon_registry_primitive_match__semantic_bucket_keys__ranked_dims = sorted(
        (
            (abs(py_local_src_teleon_registry_primitive_match__semantic_bucket_keys__value), py_local_src_teleon_registry_primitive_match__semantic_bucket_keys__index, "pos" if py_local_src_teleon_registry_primitive_match__semantic_bucket_keys__value >= 0 else "neg")
            for py_local_src_teleon_registry_primitive_match__semantic_bucket_keys__index, py_local_src_teleon_registry_primitive_match__semantic_bucket_keys__value in enumerate(py_arg_src_teleon_registry_primitive_match__semantic_bucket_keys__embedding or [])
            if py_local_src_teleon_registry_primitive_match__semantic_bucket_keys__value
        ),
        reverse=True,
    )
    return [
        f"semantic_bucket:{py_local_src_teleon_registry_primitive_match__semantic_bucket_keys__index}:{py_local_src_teleon_registry_primitive_match__semantic_bucket_keys__sign}"
        for _, py_local_src_teleon_registry_primitive_match__semantic_bucket_keys__index, py_local_src_teleon_registry_primitive_match__semantic_bucket_keys__sign in py_local_src_teleon_registry_primitive_match__semantic_bucket_keys__ranked_dims[:py_const_src_teleon_registry_primitive_match__SEMANTIC_BUCKET_COUNT]
    ]


def py_function_src_teleon_registry_primitive_match__blocking_profile_keys(py_arg_src_teleon_registry_primitive_match__blocking_profile_keys__profile: dict) -> list[str]:
    """Flatten a blocking profile into deterministic inverted-index keys."""
    py_local_src_teleon_registry_primitive_match__blocking_profile_keys__keys: set[str] = set()
    for py_local_src_teleon_registry_primitive_match__blocking_profile_keys__lane, py_local_src_teleon_registry_primitive_match__blocking_profile_keys__field in (
        ("exact", "exact_keys"),
        ("keyword", "keyword_keys"),
        ("label", "label_keys"),
        ("graph", "graph_signature"),
        ("mutation", "mutation_hints"),
    ):
        py_local_src_teleon_registry_primitive_match__blocking_profile_keys__keys |= {
            f"{py_local_src_teleon_registry_primitive_match__blocking_profile_keys__lane}:{str(py_local_src_teleon_registry_primitive_match__blocking_profile_keys__value).lower()}"
            for py_local_src_teleon_registry_primitive_match__blocking_profile_keys__value in py_function_src_teleon_registry_primitive_match__as_list(py_arg_src_teleon_registry_primitive_match__blocking_profile_keys__profile.get(py_local_src_teleon_registry_primitive_match__blocking_profile_keys__field))
            if py_local_src_teleon_registry_primitive_match__blocking_profile_keys__value
        }
    for py_local_src_teleon_registry_primitive_match__blocking_profile_keys__contract_lane, py_local_src_teleon_registry_primitive_match__blocking_profile_keys__signature in (
        ("input", py_arg_src_teleon_registry_primitive_match__blocking_profile_keys__profile.get("input_signature") or {}),
        ("output", py_arg_src_teleon_registry_primitive_match__blocking_profile_keys__profile.get("output_signature") or {}),
    ):
        py_local_src_teleon_registry_primitive_match__blocking_profile_keys__shape = str(py_local_src_teleon_registry_primitive_match__blocking_profile_keys__signature.get("shape") or "")
        if py_local_src_teleon_registry_primitive_match__blocking_profile_keys__shape and py_local_src_teleon_registry_primitive_match__blocking_profile_keys__shape not in py_const_src_teleon_registry_primitive_match__GENERIC_CONTRACT_SHAPES:
            py_local_src_teleon_registry_primitive_match__blocking_profile_keys__keys.add(f"{py_local_src_teleon_registry_primitive_match__blocking_profile_keys__contract_lane}_shape:{py_local_src_teleon_registry_primitive_match__blocking_profile_keys__shape}")
        py_local_src_teleon_registry_primitive_match__blocking_profile_keys__keys |= {
            f"{py_local_src_teleon_registry_primitive_match__blocking_profile_keys__contract_lane}_field:{str(py_local_src_teleon_registry_primitive_match__blocking_profile_keys__field).lower()}"
            for py_local_src_teleon_registry_primitive_match__blocking_profile_keys__field in py_function_src_teleon_registry_primitive_match__as_list(py_local_src_teleon_registry_primitive_match__blocking_profile_keys__signature.get("fields"))
            if py_local_src_teleon_registry_primitive_match__blocking_profile_keys__field
        }
    py_local_src_teleon_registry_primitive_match__blocking_profile_keys__keys |= set(
        py_function_src_teleon_registry_primitive_match__semantic_bucket_keys(
            py_arg_src_teleon_registry_primitive_match__blocking_profile_keys__profile.get("semantic_embedding") or []
        )
    )
    return sorted(py_local_src_teleon_registry_primitive_match__blocking_profile_keys__keys)


def py_function_src_teleon_registry_primitive_match__request_mutation_need_keys(py_arg_src_teleon_registry_primitive_match__request_mutation_need_keys__request: dict) -> list[str]:
    """Mutation-lane keys the request should retrieve even before compatibility reranking."""
    py_local_src_teleon_registry_primitive_match__request_mutation_need_keys__keys: set[str] = set()
    py_local_src_teleon_registry_primitive_match__request_mutation_need_keys__input_shape = py_function_src_teleon_registry_primitive_match__shape(py_arg_src_teleon_registry_primitive_match__request_mutation_need_keys__request.get("input_contract"))
    py_local_src_teleon_registry_primitive_match__request_mutation_need_keys__output_shape = py_function_src_teleon_registry_primitive_match__shape(py_arg_src_teleon_registry_primitive_match__request_mutation_need_keys__request.get("output_contract"))
    py_local_src_teleon_registry_primitive_match__request_mutation_need_keys__output_fields = py_function_src_teleon_registry_primitive_match__fields(py_arg_src_teleon_registry_primitive_match__request_mutation_need_keys__request.get("output_contract"))
    py_local_src_teleon_registry_primitive_match__request_mutation_need_keys__labels = py_function_src_teleon_registry_primitive_match__primitive_labels(py_arg_src_teleon_registry_primitive_match__request_mutation_need_keys__request)
    if py_local_src_teleon_registry_primitive_match__request_mutation_need_keys__input_shape in {"sequence", "array", "list", "scalar_or_sequence"}:
        py_local_src_teleon_registry_primitive_match__request_mutation_need_keys__keys.add(f"mutation:{py_const_src_teleon_registry_primitive_match__MUTATION_SCALAR_TO_SEQUENCE}")
    if py_local_src_teleon_registry_primitive_match__request_mutation_need_keys__output_shape in {"object", "dict", "mapping"} and len(py_local_src_teleon_registry_primitive_match__request_mutation_need_keys__output_fields) == 1:
        py_local_src_teleon_registry_primitive_match__request_mutation_need_keys__keys.add(f"mutation:{py_const_src_teleon_registry_primitive_match__MUTATION_OUTPUT_FIELD_WRAPPER}")
    if py_arg_src_teleon_registry_primitive_match__request_mutation_need_keys__request.get("deterministic_field_map"):
        py_local_src_teleon_registry_primitive_match__request_mutation_need_keys__keys.add(f"mutation:{py_const_src_teleon_registry_primitive_match__MUTATION_FIELD_RENAME_ADAPTER}")
    if {"retry", "cache", "rate_limit", "rate-limit", "timeout", "backoff"} & py_local_src_teleon_registry_primitive_match__request_mutation_need_keys__labels:
        py_local_src_teleon_registry_primitive_match__request_mutation_need_keys__keys.add(f"mutation:{py_const_src_teleon_registry_primitive_match__MUTATION_RETRY_CACHE_RATE_LIMIT_ADAPTER}")
    if {"cheap", "cheaper", "cost"} & py_local_src_teleon_registry_primitive_match__request_mutation_need_keys__labels:
        py_local_src_teleon_registry_primitive_match__request_mutation_need_keys__keys.add(f"mutation:{py_const_src_teleon_registry_primitive_match__MUTATION_MODEL_COST_DOWNSHIFT}")
    if "deterministic" in py_local_src_teleon_registry_primitive_match__request_mutation_need_keys__labels:
        py_local_src_teleon_registry_primitive_match__request_mutation_need_keys__keys.add(f"mutation:{py_const_src_teleon_registry_primitive_match__MUTATION_BROWSER_TO_DETERMINISTIC_EXTRACTOR}")
    if "local" in py_local_src_teleon_registry_primitive_match__request_mutation_need_keys__labels:
        py_local_src_teleon_registry_primitive_match__request_mutation_need_keys__keys.add(f"mutation:{py_const_src_teleon_registry_primitive_match__MUTATION_LOCAL_API_IMPLEMENTATION_SWAP}")
    return sorted(py_local_src_teleon_registry_primitive_match__request_mutation_need_keys__keys)


def py_function_src_teleon_registry_primitive_match__request_blocking_keys(py_arg_src_teleon_registry_primitive_match__request_blocking_keys__request: dict) -> list[str]:
    py_local_src_teleon_registry_primitive_match__request_blocking_keys__query = (
        py_arg_src_teleon_registry_primitive_match__request_blocking_keys__request.get("name")
        or py_arg_src_teleon_registry_primitive_match__request_blocking_keys__request.get("query")
        or py_arg_src_teleon_registry_primitive_match__request_blocking_keys__request.get("intent")
        or py_arg_src_teleon_registry_primitive_match__request_blocking_keys__request.get("id")
        or ""
    )
    py_local_src_teleon_registry_primitive_match__request_blocking_keys__profile = py_function_src_teleon_registry_primitive_match__blocking_profile({
        **py_arg_src_teleon_registry_primitive_match__request_blocking_keys__request,
        "name": py_local_src_teleon_registry_primitive_match__request_blocking_keys__query,
    })
    return sorted(
        set(py_function_src_teleon_registry_primitive_match__blocking_profile_keys(py_local_src_teleon_registry_primitive_match__request_blocking_keys__profile))
        | set(py_function_src_teleon_registry_primitive_match__request_mutation_need_keys(py_arg_src_teleon_registry_primitive_match__request_blocking_keys__request))
    )


def py_function_src_teleon_registry_primitive_match__blocking_index(py_arg_src_teleon_registry_primitive_match__blocking_index__candidates: list[dict]) -> dict:
    """Build a deterministic inverted index over precomputed blocking profiles.

    The index is candidate evidence only. It exists to shrink a million-row primitive registry to a bounded
    rerank set before the compatibility/mutation classifier runs.
    """
    py_local_src_teleon_registry_primitive_match__blocking_index__inverted: dict[str, list[int]] = {}
    py_local_src_teleon_registry_primitive_match__blocking_index__profile_keys: list[dict] = []
    for py_local_src_teleon_registry_primitive_match__blocking_index__index, py_local_src_teleon_registry_primitive_match__blocking_index__candidate in enumerate(py_arg_src_teleon_registry_primitive_match__blocking_index__candidates):
        py_local_src_teleon_registry_primitive_match__blocking_index__profile = py_local_src_teleon_registry_primitive_match__blocking_index__candidate.get("blocking_profile")
        if not isinstance(py_local_src_teleon_registry_primitive_match__blocking_index__profile, dict):
            py_local_src_teleon_registry_primitive_match__blocking_index__profile = py_function_src_teleon_registry_primitive_match__blocking_profile(py_local_src_teleon_registry_primitive_match__blocking_index__candidate)
        py_local_src_teleon_registry_primitive_match__blocking_index__keys = py_function_src_teleon_registry_primitive_match__blocking_profile_keys(py_local_src_teleon_registry_primitive_match__blocking_index__profile)
        py_local_src_teleon_registry_primitive_match__blocking_index__profile_keys.append({
            "candidate_index": py_local_src_teleon_registry_primitive_match__blocking_index__index,
            "primitive_id": py_local_src_teleon_registry_primitive_match__blocking_index__candidate.get("id") or py_local_src_teleon_registry_primitive_match__blocking_index__candidate.get("name"),
            "keys": py_local_src_teleon_registry_primitive_match__blocking_index__keys,
        })
        for py_local_src_teleon_registry_primitive_match__blocking_index__key in py_local_src_teleon_registry_primitive_match__blocking_index__keys:
            py_local_src_teleon_registry_primitive_match__blocking_index__inverted.setdefault(py_local_src_teleon_registry_primitive_match__blocking_index__key, []).append(py_local_src_teleon_registry_primitive_match__blocking_index__index)
    return {
        "candidate_count": len(py_arg_src_teleon_registry_primitive_match__blocking_index__candidates),
        "profile_fields": list(py_const_src_teleon_registry_primitive_match__BLOCK_PROFILE_FIELDS),
        "inverted": {key: py_local_src_teleon_registry_primitive_match__blocking_index__inverted[key] for key in sorted(py_local_src_teleon_registry_primitive_match__blocking_index__inverted)},
        "profile_keys": py_local_src_teleon_registry_primitive_match__blocking_index__profile_keys,
        "serves_truth": False,
    }


def py_function_src_teleon_registry_primitive_match__blocked_candidate_indexes(py_arg_src_teleon_registry_primitive_match__blocked_candidate_indexes__request: dict, py_arg_src_teleon_registry_primitive_match__blocked_candidate_indexes__index: dict, *, py_arg_src_teleon_registry_primitive_match__blocked_candidate_indexes__limit: int = py_const_src_teleon_registry_primitive_match__BLOCKED_RERANK_MAX_CANDIDATES) -> dict:
    py_local_src_teleon_registry_primitive_match__blocked_candidate_indexes__request_keys = py_function_src_teleon_registry_primitive_match__request_blocking_keys(py_arg_src_teleon_registry_primitive_match__blocked_candidate_indexes__request)
    py_inst_src_teleon_registry_primitive_match__blocked_candidate_indexes__counts: Counter[int] = Counter()
    py_local_src_teleon_registry_primitive_match__blocked_candidate_indexes__matched_keys: dict[int, set[str]] = {}
    py_local_src_teleon_registry_primitive_match__blocked_candidate_indexes__inverted = py_arg_src_teleon_registry_primitive_match__blocked_candidate_indexes__index.get("inverted") or {}
    for py_local_src_teleon_registry_primitive_match__blocked_candidate_indexes__key in py_local_src_teleon_registry_primitive_match__blocked_candidate_indexes__request_keys:
        for py_local_src_teleon_registry_primitive_match__blocked_candidate_indexes__candidate_index in py_local_src_teleon_registry_primitive_match__blocked_candidate_indexes__inverted.get(py_local_src_teleon_registry_primitive_match__blocked_candidate_indexes__key, []):
            py_inst_src_teleon_registry_primitive_match__blocked_candidate_indexes__counts[py_local_src_teleon_registry_primitive_match__blocked_candidate_indexes__candidate_index] += 1
            py_local_src_teleon_registry_primitive_match__blocked_candidate_indexes__matched_keys.setdefault(py_local_src_teleon_registry_primitive_match__blocked_candidate_indexes__candidate_index, set()).add(py_local_src_teleon_registry_primitive_match__blocked_candidate_indexes__key)
    py_local_src_teleon_registry_primitive_match__blocked_candidate_indexes__ranked = [
        py_local_src_teleon_registry_primitive_match__blocked_candidate_indexes__candidate_index
        for py_local_src_teleon_registry_primitive_match__blocked_candidate_indexes__candidate_index, _ in sorted(
            py_inst_src_teleon_registry_primitive_match__blocked_candidate_indexes__counts.items(),
            key=lambda py_arg_src_teleon_registry_primitive_match__blocked_candidate_indexes__item: (-py_arg_src_teleon_registry_primitive_match__blocked_candidate_indexes__item[1], py_arg_src_teleon_registry_primitive_match__blocked_candidate_indexes__item[0]),
        )
    ][:py_arg_src_teleon_registry_primitive_match__blocked_candidate_indexes__limit]
    return {
        "request_keys": py_local_src_teleon_registry_primitive_match__blocked_candidate_indexes__request_keys,
        "candidate_indexes": py_local_src_teleon_registry_primitive_match__blocked_candidate_indexes__ranked,
        "candidate_match_counts": {str(key): py_inst_src_teleon_registry_primitive_match__blocked_candidate_indexes__counts[key] for key in py_local_src_teleon_registry_primitive_match__blocked_candidate_indexes__ranked},
        "matched_keys": {str(key): sorted(py_local_src_teleon_registry_primitive_match__blocked_candidate_indexes__matched_keys.get(key, set())) for key in py_local_src_teleon_registry_primitive_match__blocked_candidate_indexes__ranked},
        "serves_truth": False,
    }


def py_function_src_teleon_registry_primitive_match__adapter_plan(py_arg_src_teleon_registry_primitive_match__adapter_plan__mutation_ids: list[str], py_arg_src_teleon_registry_primitive_match__adapter_plan__candidate: dict, py_arg_src_teleon_registry_primitive_match__adapter_plan__request: dict) -> list[dict]:
    """Turn required mutations into explicit graph adapter/candidate nodes.

    Search should not only say "this almost fits"; it should say which node must be inserted and which
    proof/promotion boundary applies. The plan is candidate evidence only.
    """
    py_local_src_teleon_registry_primitive_match__adapter_plan__nodes: list[dict] = []
    py_local_src_teleon_registry_primitive_match__adapter_plan__base_id = str(py_arg_src_teleon_registry_primitive_match__adapter_plan__candidate.get("id") or py_arg_src_teleon_registry_primitive_match__adapter_plan__candidate.get("name") or "primitive")
    py_local_src_teleon_registry_primitive_match__adapter_plan__templates = {
        py_const_src_teleon_registry_primitive_match__MUTATION_SCALAR_TO_SEQUENCE: {
            "lane": "deterministic_adapter",
            "node_kind": "normalize_to_sequence_then_map",
            "proof_required": "wrapper_executes_and_preserves_per_item_contract",
        },
        py_const_src_teleon_registry_primitive_match__MUTATION_OUTPUT_FIELD_WRAPPER: {
            "lane": "deterministic_adapter",
            "node_kind": "wrap_output_field",
            "proof_required": "wrapper_executes_and_output_schema_matches",
        },
        py_const_src_teleon_registry_primitive_match__MUTATION_FIELD_RENAME_ADAPTER: {
            "lane": "deterministic_adapter",
            "node_kind": "explicit_field_rename",
            "proof_required": "explicit_field_map_present_and_schema_matches",
        },
        py_const_src_teleon_registry_primitive_match__MUTATION_RETRY_CACHE_RATE_LIMIT_ADAPTER: {
            "lane": "policy_adapter",
            "node_kind": "retry_cache_rate_limit_policy",
            "proof_required": "policy_wrapper_logs_retries_cache_and_rate_limits",
        },
        py_const_src_teleon_registry_primitive_match__MUTATION_MODEL_COST_DOWNSHIFT: {
            "lane": "deterministic_candidate_optimization",
            "node_kind": "model_provider_downshift_candidate",
            "proof_required": "guardrail_pass_rate_and_latency_cost_receipts",
        },
        py_const_src_teleon_registry_primitive_match__MUTATION_BROWSER_TO_DETERMINISTIC_EXTRACTOR: {
            "lane": "deterministic_candidate_optimization",
            "node_kind": "browser_to_css_xpath_regex_extractor_candidate",
            "proof_required": "observed_structure_stability_and_extraction_accuracy",
        },
        py_const_src_teleon_registry_primitive_match__MUTATION_LOCAL_API_IMPLEMENTATION_SWAP: {
            "lane": "implementation_swap_candidate",
            "node_kind": "local_api_compatible_implementation_candidate",
            "proof_required": "same_io_contract_dependency_license_and_runtime_receipts",
        },
        py_const_src_teleon_registry_primitive_match__MUTATION_GENERATED_ADAPTER_CANDIDATE: {
            "lane": "nondeterministic_generated_candidate",
            "node_kind": "generated_adapter_candidate",
            "proof_required": "owner_or_human_review_plus_deterministic_proofs_before_promotion",
        },
    }
    for py_local_src_teleon_registry_primitive_match__adapter_plan__mutation_id in py_arg_src_teleon_registry_primitive_match__adapter_plan__mutation_ids:
        py_local_src_teleon_registry_primitive_match__adapter_plan__template = py_local_src_teleon_registry_primitive_match__adapter_plan__templates.get(py_local_src_teleon_registry_primitive_match__adapter_plan__mutation_id)
        if not py_local_src_teleon_registry_primitive_match__adapter_plan__template:
            continue
        py_local_src_teleon_registry_primitive_match__adapter_plan__nodes.append({
            "id": f"{py_local_src_teleon_registry_primitive_match__adapter_plan__base_id}::adapter::{py_local_src_teleon_registry_primitive_match__adapter_plan__mutation_id}",
            "mutation": py_local_src_teleon_registry_primitive_match__adapter_plan__mutation_id,
            "lane": py_local_src_teleon_registry_primitive_match__adapter_plan__template["lane"],
            "node_kind": py_local_src_teleon_registry_primitive_match__adapter_plan__template["node_kind"],
            "candidate_input_contract": py_arg_src_teleon_registry_primitive_match__adapter_plan__candidate.get("input_contract"),
            "candidate_output_contract": py_arg_src_teleon_registry_primitive_match__adapter_plan__candidate.get("output_contract"),
            "requested_input_contract": py_arg_src_teleon_registry_primitive_match__adapter_plan__request.get("input_contract"),
            "requested_output_contract": py_arg_src_teleon_registry_primitive_match__adapter_plan__request.get("output_contract"),
            "proof_required": py_local_src_teleon_registry_primitive_match__adapter_plan__template["proof_required"],
            "promotion_required": True,
            "serves_truth": False,
        })
    return py_local_src_teleon_registry_primitive_match__adapter_plan__nodes


def py_function_src_teleon_registry_primitive_match__graph_assembly_status(py_arg_src_teleon_registry_primitive_match__graph_assembly_status__fit_class: str) -> str:
    if py_arg_src_teleon_registry_primitive_match__graph_assembly_status__fit_class == py_const_src_teleon_registry_primitive_match__FIT_EXACT_MATCH:
        return py_const_src_teleon_registry_primitive_match__GRAPH_STATUS_CHAINABLE_AS_IS
    if py_arg_src_teleon_registry_primitive_match__graph_assembly_status__fit_class == py_const_src_teleon_registry_primitive_match__FIT_DETERMINISTIC_EDIT_MATCH:
        return py_const_src_teleon_registry_primitive_match__GRAPH_STATUS_CHAINABLE_WITH_ADAPTERS
    if py_arg_src_teleon_registry_primitive_match__graph_assembly_status__fit_class == py_const_src_teleon_registry_primitive_match__FIT_NONDETERMINISTIC_EDIT_MATCH:
        return py_const_src_teleon_registry_primitive_match__GRAPH_STATUS_GENERATED_ADAPTER_REQUIRED
    return py_const_src_teleon_registry_primitive_match__GRAPH_STATUS_NOT_CHAINABLE


def py_function_src_teleon_registry_primitive_match__direct_contract_compatible(py_arg_src_teleon_registry_primitive_match__direct_contract_compatible__candidate_contract: dict | None, py_arg_src_teleon_registry_primitive_match__direct_contract_compatible__requested_contract: dict | None) -> bool:
    py_local_src_teleon_registry_primitive_match__direct_contract_compatible__requested_shape = py_function_src_teleon_registry_primitive_match__shape(py_arg_src_teleon_registry_primitive_match__direct_contract_compatible__requested_contract)
    py_local_src_teleon_registry_primitive_match__direct_contract_compatible__candidate_shape = py_function_src_teleon_registry_primitive_match__shape(py_arg_src_teleon_registry_primitive_match__direct_contract_compatible__candidate_contract)
    if py_local_src_teleon_registry_primitive_match__direct_contract_compatible__requested_shape in {"unknown", "any"}:
        return True
    if py_local_src_teleon_registry_primitive_match__direct_contract_compatible__candidate_shape == py_local_src_teleon_registry_primitive_match__direct_contract_compatible__requested_shape:
        py_local_src_teleon_registry_primitive_match__direct_contract_compatible__requested_fields = py_function_src_teleon_registry_primitive_match__fields(py_arg_src_teleon_registry_primitive_match__direct_contract_compatible__requested_contract)
        py_local_src_teleon_registry_primitive_match__direct_contract_compatible__candidate_fields = py_function_src_teleon_registry_primitive_match__fields(py_arg_src_teleon_registry_primitive_match__direct_contract_compatible__candidate_contract)
        return not py_local_src_teleon_registry_primitive_match__direct_contract_compatible__requested_fields or py_local_src_teleon_registry_primitive_match__direct_contract_compatible__requested_fields <= py_local_src_teleon_registry_primitive_match__direct_contract_compatible__candidate_fields or not py_local_src_teleon_registry_primitive_match__direct_contract_compatible__candidate_fields
    if py_local_src_teleon_registry_primitive_match__direct_contract_compatible__candidate_shape == "scalar_or_sequence" and py_local_src_teleon_registry_primitive_match__direct_contract_compatible__requested_shape in {"scalar", "sequence", "array", "list"}:
        return True
    if py_local_src_teleon_registry_primitive_match__direct_contract_compatible__candidate_shape in {"object", "dict", "mapping"} and py_local_src_teleon_registry_primitive_match__direct_contract_compatible__requested_shape == "object":
        py_local_src_teleon_registry_primitive_match__direct_contract_compatible__requested_fields = py_function_src_teleon_registry_primitive_match__fields(py_arg_src_teleon_registry_primitive_match__direct_contract_compatible__requested_contract)
        return not py_local_src_teleon_registry_primitive_match__direct_contract_compatible__requested_fields or py_local_src_teleon_registry_primitive_match__direct_contract_compatible__requested_fields <= py_function_src_teleon_registry_primitive_match__fields(py_arg_src_teleon_registry_primitive_match__direct_contract_compatible__candidate_contract)
    return False


def py_function_src_teleon_registry_primitive_match__deterministic_mutations(py_arg_src_teleon_registry_primitive_match__deterministic_mutations__candidate: dict, py_arg_src_teleon_registry_primitive_match__deterministic_mutations__request: dict) -> list[str]:
    py_local_src_teleon_registry_primitive_match__deterministic_mutations__mutations: list[str] = []
    py_local_src_teleon_registry_primitive_match__deterministic_mutations__candidate_input = py_arg_src_teleon_registry_primitive_match__deterministic_mutations__candidate.get("input_contract")
    py_local_src_teleon_registry_primitive_match__deterministic_mutations__candidate_output = py_arg_src_teleon_registry_primitive_match__deterministic_mutations__candidate.get("output_contract")
    py_local_src_teleon_registry_primitive_match__deterministic_mutations__requested_input = py_arg_src_teleon_registry_primitive_match__deterministic_mutations__request.get("input_contract")
    py_local_src_teleon_registry_primitive_match__deterministic_mutations__requested_output = py_arg_src_teleon_registry_primitive_match__deterministic_mutations__request.get("output_contract")
    py_local_src_teleon_registry_primitive_match__deterministic_mutations__requested_input_shape = py_function_src_teleon_registry_primitive_match__shape(py_local_src_teleon_registry_primitive_match__deterministic_mutations__requested_input)
    py_local_src_teleon_registry_primitive_match__deterministic_mutations__candidate_input_shape = py_function_src_teleon_registry_primitive_match__shape(py_local_src_teleon_registry_primitive_match__deterministic_mutations__candidate_input)
    py_local_src_teleon_registry_primitive_match__deterministic_mutations__requested_output_shape = py_function_src_teleon_registry_primitive_match__shape(py_local_src_teleon_registry_primitive_match__deterministic_mutations__requested_output)
    py_local_src_teleon_registry_primitive_match__deterministic_mutations__candidate_output_shape = py_function_src_teleon_registry_primitive_match__shape(py_local_src_teleon_registry_primitive_match__deterministic_mutations__candidate_output)

    if py_local_src_teleon_registry_primitive_match__deterministic_mutations__requested_input_shape in {"sequence", "array", "list", "scalar_or_sequence"} and py_local_src_teleon_registry_primitive_match__deterministic_mutations__candidate_input_shape == "scalar":
        py_local_src_teleon_registry_primitive_match__deterministic_mutations__mutations.append(py_const_src_teleon_registry_primitive_match__MUTATION_SCALAR_TO_SEQUENCE)
    py_local_src_teleon_registry_primitive_match__deterministic_mutations__requested_output_fields = py_function_src_teleon_registry_primitive_match__fields(py_local_src_teleon_registry_primitive_match__deterministic_mutations__requested_output)
    py_local_src_teleon_registry_primitive_match__deterministic_mutations__candidate_output_fields = py_function_src_teleon_registry_primitive_match__fields(py_local_src_teleon_registry_primitive_match__deterministic_mutations__candidate_output)
    if py_local_src_teleon_registry_primitive_match__deterministic_mutations__requested_output_shape in {"object", "dict", "mapping"} and py_local_src_teleon_registry_primitive_match__deterministic_mutations__requested_output_fields:
        if py_local_src_teleon_registry_primitive_match__deterministic_mutations__candidate_output_shape not in {"object", "dict", "mapping"} and len(py_local_src_teleon_registry_primitive_match__deterministic_mutations__requested_output_fields) == 1:
            py_local_src_teleon_registry_primitive_match__deterministic_mutations__mutations.append(py_const_src_teleon_registry_primitive_match__MUTATION_OUTPUT_FIELD_WRAPPER)
        elif (
            py_local_src_teleon_registry_primitive_match__deterministic_mutations__candidate_output_fields
            and len(py_local_src_teleon_registry_primitive_match__deterministic_mutations__candidate_output_fields) == len(py_local_src_teleon_registry_primitive_match__deterministic_mutations__requested_output_fields)
            and py_arg_src_teleon_registry_primitive_match__deterministic_mutations__request.get("deterministic_field_map")
        ):
            if py_local_src_teleon_registry_primitive_match__deterministic_mutations__candidate_output_fields != py_local_src_teleon_registry_primitive_match__deterministic_mutations__requested_output_fields:
                py_local_src_teleon_registry_primitive_match__deterministic_mutations__mutations.append(py_const_src_teleon_registry_primitive_match__MUTATION_FIELD_RENAME_ADAPTER)

    py_local_src_teleon_registry_primitive_match__deterministic_mutations__requested_labels = py_function_src_teleon_registry_primitive_match__primitive_labels(py_arg_src_teleon_registry_primitive_match__deterministic_mutations__request)
    py_local_src_teleon_registry_primitive_match__deterministic_mutations__candidate_labels = py_function_src_teleon_registry_primitive_match__primitive_labels(py_arg_src_teleon_registry_primitive_match__deterministic_mutations__candidate)
    if {"retry", "cache", "rate_limit", "rate-limit", "timeout", "backoff"} & py_local_src_teleon_registry_primitive_match__deterministic_mutations__requested_labels and not (
        {"retry", "cache", "rate_limit", "rate-limit", "timeout", "backoff"} & py_local_src_teleon_registry_primitive_match__deterministic_mutations__candidate_labels
    ):
        py_local_src_teleon_registry_primitive_match__deterministic_mutations__mutations.append(py_const_src_teleon_registry_primitive_match__MUTATION_RETRY_CACHE_RATE_LIMIT_ADAPTER)
    if "cheap" in py_local_src_teleon_registry_primitive_match__deterministic_mutations__requested_labels or "cheaper" in py_local_src_teleon_registry_primitive_match__deterministic_mutations__requested_labels or "cost" in py_local_src_teleon_registry_primitive_match__deterministic_mutations__requested_labels:
        if {"llm", "model", "browser"} & py_local_src_teleon_registry_primitive_match__deterministic_mutations__candidate_labels:
            py_local_src_teleon_registry_primitive_match__deterministic_mutations__mutations.append(py_const_src_teleon_registry_primitive_match__MUTATION_MODEL_COST_DOWNSHIFT)
    if "deterministic" in py_local_src_teleon_registry_primitive_match__deterministic_mutations__requested_labels and {"llm", "browser"} & py_local_src_teleon_registry_primitive_match__deterministic_mutations__candidate_labels:
        py_local_src_teleon_registry_primitive_match__deterministic_mutations__mutations.append(py_const_src_teleon_registry_primitive_match__MUTATION_BROWSER_TO_DETERMINISTIC_EXTRACTOR)
    if "local" in py_local_src_teleon_registry_primitive_match__deterministic_mutations__requested_labels and {"api", "hosted", "third_party"} & py_local_src_teleon_registry_primitive_match__deterministic_mutations__candidate_labels:
        py_local_src_teleon_registry_primitive_match__deterministic_mutations__mutations.append(py_const_src_teleon_registry_primitive_match__MUTATION_LOCAL_API_IMPLEMENTATION_SWAP)
    return sorted(set(py_local_src_teleon_registry_primitive_match__deterministic_mutations__mutations))


def py_function_src_teleon_registry_primitive_match__compatibility(py_arg_src_teleon_registry_primitive_match__compatibility__candidate: dict, py_arg_src_teleon_registry_primitive_match__compatibility__request: dict) -> dict:
    py_local_src_teleon_registry_primitive_match__compatibility__input_direct = py_function_src_teleon_registry_primitive_match__direct_contract_compatible(py_arg_src_teleon_registry_primitive_match__compatibility__candidate.get("input_contract"), py_arg_src_teleon_registry_primitive_match__compatibility__request.get("input_contract"))
    py_local_src_teleon_registry_primitive_match__compatibility__output_direct = py_function_src_teleon_registry_primitive_match__direct_contract_compatible(py_arg_src_teleon_registry_primitive_match__compatibility__candidate.get("output_contract"), py_arg_src_teleon_registry_primitive_match__compatibility__request.get("output_contract"))
    py_local_src_teleon_registry_primitive_match__compatibility__mutations = py_function_src_teleon_registry_primitive_match__deterministic_mutations(py_arg_src_teleon_registry_primitive_match__compatibility__candidate, py_arg_src_teleon_registry_primitive_match__compatibility__request)
    py_local_src_teleon_registry_primitive_match__compatibility__io_mutations = sorted(set(py_local_src_teleon_registry_primitive_match__compatibility__mutations) & py_const_src_teleon_registry_primitive_match__IO_MUTATIONS)
    if py_local_src_teleon_registry_primitive_match__compatibility__input_direct and py_local_src_teleon_registry_primitive_match__compatibility__output_direct and not py_local_src_teleon_registry_primitive_match__compatibility__mutations:
        py_local_src_teleon_registry_primitive_match__compatibility__fit_class = py_const_src_teleon_registry_primitive_match__FIT_EXACT_MATCH
    elif (py_local_src_teleon_registry_primitive_match__compatibility__input_direct or py_const_src_teleon_registry_primitive_match__MUTATION_SCALAR_TO_SEQUENCE in py_local_src_teleon_registry_primitive_match__compatibility__io_mutations) and (py_local_src_teleon_registry_primitive_match__compatibility__output_direct or py_local_src_teleon_registry_primitive_match__compatibility__io_mutations):
        py_local_src_teleon_registry_primitive_match__compatibility__fit_class = py_const_src_teleon_registry_primitive_match__FIT_DETERMINISTIC_EDIT_MATCH
    else:
        py_local_src_teleon_registry_primitive_match__compatibility__fit_class = py_const_src_teleon_registry_primitive_match__FIT_INCOMPATIBLE
    return {
        "fit_class": py_local_src_teleon_registry_primitive_match__compatibility__fit_class,
        "input_direct": py_local_src_teleon_registry_primitive_match__compatibility__input_direct,
        "output_direct": py_local_src_teleon_registry_primitive_match__compatibility__output_direct,
        "required_mutations": py_local_src_teleon_registry_primitive_match__compatibility__mutations,
    }


def py_function_src_teleon_registry_primitive_match__blocking_evidence(py_arg_src_teleon_registry_primitive_match__blocking_evidence__candidate: dict, py_arg_src_teleon_registry_primitive_match__blocking_evidence__request: dict) -> dict:
    py_local_src_teleon_registry_primitive_match__blocking_evidence__query_text = str(py_arg_src_teleon_registry_primitive_match__blocking_evidence__request.get("intent") or py_arg_src_teleon_registry_primitive_match__blocking_evidence__request.get("query") or "")
    py_local_src_teleon_registry_primitive_match__blocking_evidence__request_tokens = py_function_src_teleon_registry_primitive_match__tokens(py_local_src_teleon_registry_primitive_match__blocking_evidence__query_text) | py_function_src_teleon_registry_primitive_match__primitive_keywords(py_arg_src_teleon_registry_primitive_match__blocking_evidence__request)
    py_local_src_teleon_registry_primitive_match__blocking_evidence__candidate_tokens = py_function_src_teleon_registry_primitive_match__primitive_keywords(py_arg_src_teleon_registry_primitive_match__blocking_evidence__candidate)
    py_local_src_teleon_registry_primitive_match__blocking_evidence__request_labels = py_function_src_teleon_registry_primitive_match__primitive_labels(py_arg_src_teleon_registry_primitive_match__blocking_evidence__request)
    py_local_src_teleon_registry_primitive_match__blocking_evidence__candidate_labels = py_function_src_teleon_registry_primitive_match__primitive_labels(py_arg_src_teleon_registry_primitive_match__blocking_evidence__candidate)
    py_local_src_teleon_registry_primitive_match__blocking_evidence__request_neighbors = {str(v).lower() for v in py_function_src_teleon_registry_primitive_match__as_list(py_arg_src_teleon_registry_primitive_match__blocking_evidence__request.get("graph_neighbors"))} | py_function_src_teleon_registry_primitive_match__graph_neighbors(py_arg_src_teleon_registry_primitive_match__blocking_evidence__request)
    py_local_src_teleon_registry_primitive_match__blocking_evidence__candidate_neighbors = py_function_src_teleon_registry_primitive_match__graph_neighbors(py_arg_src_teleon_registry_primitive_match__blocking_evidence__candidate)
    py_local_src_teleon_registry_primitive_match__blocking_evidence__exact = bool(
        py_arg_src_teleon_registry_primitive_match__blocking_evidence__request.get("id") and str(py_arg_src_teleon_registry_primitive_match__blocking_evidence__request["id"]).lower() == str(py_arg_src_teleon_registry_primitive_match__blocking_evidence__candidate.get("id", "")).lower()
        or py_local_src_teleon_registry_primitive_match__blocking_evidence__query_text and py_local_src_teleon_registry_primitive_match__blocking_evidence__query_text.lower() in str(py_arg_src_teleon_registry_primitive_match__blocking_evidence__candidate.get("id", "")).lower()
        or py_local_src_teleon_registry_primitive_match__blocking_evidence__query_text and py_local_src_teleon_registry_primitive_match__blocking_evidence__query_text.lower() in str(py_arg_src_teleon_registry_primitive_match__blocking_evidence__candidate.get("name", "")).lower()
    )
    py_local_src_teleon_registry_primitive_match__blocking_evidence__keyword_overlap = py_local_src_teleon_registry_primitive_match__blocking_evidence__request_tokens & py_local_src_teleon_registry_primitive_match__blocking_evidence__candidate_tokens
    py_local_src_teleon_registry_primitive_match__blocking_evidence__label_overlap = py_local_src_teleon_registry_primitive_match__blocking_evidence__request_labels & py_local_src_teleon_registry_primitive_match__blocking_evidence__candidate_labels
    py_local_src_teleon_registry_primitive_match__blocking_evidence__input_overlap = py_function_src_teleon_registry_primitive_match__fields(py_arg_src_teleon_registry_primitive_match__blocking_evidence__request.get("input_contract")) & py_function_src_teleon_registry_primitive_match__fields(py_arg_src_teleon_registry_primitive_match__blocking_evidence__candidate.get("input_contract"))
    py_local_src_teleon_registry_primitive_match__blocking_evidence__output_overlap = py_function_src_teleon_registry_primitive_match__fields(py_arg_src_teleon_registry_primitive_match__blocking_evidence__request.get("output_contract")) & py_function_src_teleon_registry_primitive_match__fields(py_arg_src_teleon_registry_primitive_match__blocking_evidence__candidate.get("output_contract"))
    py_local_src_teleon_registry_primitive_match__blocking_evidence__shape_overlap = {
        value
        for value in (
            py_function_src_teleon_registry_primitive_match__shape(py_arg_src_teleon_registry_primitive_match__blocking_evidence__request.get("input_contract")) if py_function_src_teleon_registry_primitive_match__shape(py_arg_src_teleon_registry_primitive_match__blocking_evidence__request.get("input_contract")) == py_function_src_teleon_registry_primitive_match__shape(py_arg_src_teleon_registry_primitive_match__blocking_evidence__candidate.get("input_contract")) else "",
            py_function_src_teleon_registry_primitive_match__shape(py_arg_src_teleon_registry_primitive_match__blocking_evidence__request.get("output_contract")) if py_function_src_teleon_registry_primitive_match__shape(py_arg_src_teleon_registry_primitive_match__blocking_evidence__request.get("output_contract")) == py_function_src_teleon_registry_primitive_match__shape(py_arg_src_teleon_registry_primitive_match__blocking_evidence__candidate.get("output_contract")) else "",
        )
        if value and value not in py_const_src_teleon_registry_primitive_match__GENERIC_CONTRACT_SHAPES
    }
    py_local_src_teleon_registry_primitive_match__blocking_evidence__graph_overlap = py_local_src_teleon_registry_primitive_match__blocking_evidence__request_neighbors & py_local_src_teleon_registry_primitive_match__blocking_evidence__candidate_neighbors
    py_local_src_teleon_registry_primitive_match__blocking_evidence__semantic_score = py_function_src_teleon_registry_primitive_match__cosine(py_function_src_teleon_registry_enrich__embedding({"text": py_function_src_teleon_registry_primitive_match__semantic_text(py_arg_src_teleon_registry_primitive_match__blocking_evidence__request)}), py_function_src_teleon_registry_enrich__embedding({"text": py_function_src_teleon_registry_primitive_match__semantic_text(py_arg_src_teleon_registry_primitive_match__blocking_evidence__candidate)}))
    py_local_src_teleon_registry_primitive_match__blocking_evidence__evidence = {
        "exact": py_local_src_teleon_registry_primitive_match__blocking_evidence__exact,
        "keyword_overlap": sorted(py_local_src_teleon_registry_primitive_match__blocking_evidence__keyword_overlap),
        "label_overlap": sorted(py_local_src_teleon_registry_primitive_match__blocking_evidence__label_overlap),
        "input_contract_overlap": sorted(py_local_src_teleon_registry_primitive_match__blocking_evidence__input_overlap | py_local_src_teleon_registry_primitive_match__blocking_evidence__shape_overlap),
        "output_contract_overlap": sorted(py_local_src_teleon_registry_primitive_match__blocking_evidence__output_overlap),
        "graph_overlap": sorted(py_local_src_teleon_registry_primitive_match__blocking_evidence__graph_overlap),
        "semantic_score": round(py_local_src_teleon_registry_primitive_match__blocking_evidence__semantic_score, 4),
    }
    py_local_src_teleon_registry_primitive_match__blocking_evidence__evidence["blocking_reasons"] = [
        name
        for name, active in (
            ("exact", py_local_src_teleon_registry_primitive_match__blocking_evidence__exact),
            ("keyword", bool(py_local_src_teleon_registry_primitive_match__blocking_evidence__keyword_overlap)),
            ("label", bool(py_local_src_teleon_registry_primitive_match__blocking_evidence__label_overlap)),
            ("semantic", py_local_src_teleon_registry_primitive_match__blocking_evidence__semantic_score >= py_const_src_teleon_registry_primitive_match__BLOCK_MIN_SCORE),
            ("input_contract", bool(py_local_src_teleon_registry_primitive_match__blocking_evidence__input_overlap or py_local_src_teleon_registry_primitive_match__blocking_evidence__shape_overlap)),
            ("output_contract", bool(py_local_src_teleon_registry_primitive_match__blocking_evidence__output_overlap)),
            ("graph_neighborhood", bool(py_local_src_teleon_registry_primitive_match__blocking_evidence__graph_overlap)),
        )
        if active
    ]
    return py_local_src_teleon_registry_primitive_match__blocking_evidence__evidence


def py_function_src_teleon_registry_primitive_match__affinity_signal(py_arg_src_teleon_registry_primitive_match__affinity_signal__candidate: dict, py_arg_src_teleon_registry_primitive_match__affinity_signal__request: dict, py_arg_src_teleon_registry_primitive_match__affinity_signal__affinity_table: dict | None) -> float:
    """Optional learned composition-affinity ranking signal (0.0 without a table or a known pair).

    Producer edges come from the request (``producer_edge`` plus raw ``graph_neighbors``); the consumer edge
    is the candidate's ``edge``/``id``/``name``. The value is clamped by the scorer and is BOOST-ONLY: it
    never changes fit_class/contract compatibility, and suppressed (negative) affinity never subtracts here.
    """
    if not py_arg_src_teleon_registry_primitive_match__affinity_signal__affinity_table:
        return 0.0
    py_local_src_teleon_registry_primitive_match__affinity_signal__consumer_edge = str(
        py_arg_src_teleon_registry_primitive_match__affinity_signal__candidate.get("edge")
        or py_arg_src_teleon_registry_primitive_match__affinity_signal__candidate.get("id")
        or py_arg_src_teleon_registry_primitive_match__affinity_signal__candidate.get("name")
        or ""
    ).strip()
    if not py_local_src_teleon_registry_primitive_match__affinity_signal__consumer_edge:
        return 0.0
    py_local_src_teleon_registry_primitive_match__affinity_signal__producer_edges = [
        str(py_local_src_teleon_registry_primitive_match__affinity_signal__value).strip()
        for py_local_src_teleon_registry_primitive_match__affinity_signal__value in (
            [py_arg_src_teleon_registry_primitive_match__affinity_signal__request.get("producer_edge")]
            + py_function_src_teleon_registry_primitive_match__as_list(py_arg_src_teleon_registry_primitive_match__affinity_signal__request.get("graph_neighbors"))
        )
        if py_local_src_teleon_registry_primitive_match__affinity_signal__value and str(py_local_src_teleon_registry_primitive_match__affinity_signal__value).strip()
    ]
    return max(
        (
            py_function_src_teleon_registry_composition_affinity__affinity_boost(
                py_local_src_teleon_registry_primitive_match__affinity_signal__producer_edge,
                py_local_src_teleon_registry_primitive_match__affinity_signal__consumer_edge,
                py_arg_src_teleon_registry_primitive_match__affinity_signal__affinity_table,
            )
            for py_local_src_teleon_registry_primitive_match__affinity_signal__producer_edge in py_local_src_teleon_registry_primitive_match__affinity_signal__producer_edges
        ),
        default=0.0,
    )


def py_function_src_teleon_registry_primitive_match__score_candidate(py_arg_src_teleon_registry_primitive_match__score_candidate__evidence: dict, py_arg_src_teleon_registry_primitive_match__score_candidate__compatibility_result: dict, *, py_arg_src_teleon_registry_primitive_match__score_candidate__affinity_boost: float = 0.0) -> float:
    py_local_src_teleon_registry_primitive_match__score_candidate__score = 0.0
    if py_arg_src_teleon_registry_primitive_match__score_candidate__evidence["exact"]:
        py_local_src_teleon_registry_primitive_match__score_candidate__score += 1.0
    py_local_src_teleon_registry_primitive_match__score_candidate__score += min(0.3, len(py_arg_src_teleon_registry_primitive_match__score_candidate__evidence["keyword_overlap"]) * 0.04)
    py_local_src_teleon_registry_primitive_match__score_candidate__score += min(0.25, len(py_arg_src_teleon_registry_primitive_match__score_candidate__evidence["label_overlap"]) * 0.06)
    py_local_src_teleon_registry_primitive_match__score_candidate__score += min(0.2, len(py_arg_src_teleon_registry_primitive_match__score_candidate__evidence["input_contract_overlap"]) * 0.08)
    py_local_src_teleon_registry_primitive_match__score_candidate__score += min(0.2, len(py_arg_src_teleon_registry_primitive_match__score_candidate__evidence["output_contract_overlap"]) * 0.08)
    py_local_src_teleon_registry_primitive_match__score_candidate__score += min(0.15, len(py_arg_src_teleon_registry_primitive_match__score_candidate__evidence["graph_overlap"]) * 0.05)
    py_local_src_teleon_registry_primitive_match__score_candidate__score += min(0.25, py_arg_src_teleon_registry_primitive_match__score_candidate__evidence["semantic_score"] * 0.25)
    py_local_src_teleon_registry_primitive_match__score_candidate__score += min(py_const_src_teleon_registry_primitive_match__AFFINITY_BOOST_CAP, max(0.0, float(py_arg_src_teleon_registry_primitive_match__score_candidate__affinity_boost)))
    if py_arg_src_teleon_registry_primitive_match__score_candidate__compatibility_result["fit_class"] == py_const_src_teleon_registry_primitive_match__FIT_EXACT_MATCH:
        py_local_src_teleon_registry_primitive_match__score_candidate__score += 0.5
    elif py_arg_src_teleon_registry_primitive_match__score_candidate__compatibility_result["fit_class"] == py_const_src_teleon_registry_primitive_match__FIT_DETERMINISTIC_EDIT_MATCH:
        py_local_src_teleon_registry_primitive_match__score_candidate__score += 0.32
    elif py_arg_src_teleon_registry_primitive_match__score_candidate__compatibility_result["fit_class"] == py_const_src_teleon_registry_primitive_match__FIT_NONDETERMINISTIC_EDIT_MATCH:
        py_local_src_teleon_registry_primitive_match__score_candidate__score += 0.12
    return round(py_local_src_teleon_registry_primitive_match__score_candidate__score, 4)


def py_function_src_teleon_registry_primitive_match__classify_candidate(py_arg_src_teleon_registry_primitive_match__classify_candidate__candidate: dict, py_arg_src_teleon_registry_primitive_match__classify_candidate__request: dict, *, py_arg_src_teleon_registry_primitive_match__classify_candidate__affinity_table: dict | None = None) -> dict:
    py_local_src_teleon_registry_primitive_match__classify_candidate__evidence = py_function_src_teleon_registry_primitive_match__blocking_evidence(py_arg_src_teleon_registry_primitive_match__classify_candidate__candidate, py_arg_src_teleon_registry_primitive_match__classify_candidate__request)
    py_local_src_teleon_registry_primitive_match__classify_candidate__compatibility_result = py_function_src_teleon_registry_primitive_match__compatibility(py_arg_src_teleon_registry_primitive_match__classify_candidate__candidate, py_arg_src_teleon_registry_primitive_match__classify_candidate__request)
    if py_local_src_teleon_registry_primitive_match__classify_candidate__compatibility_result["fit_class"] == py_const_src_teleon_registry_primitive_match__FIT_INCOMPATIBLE:
        py_local_src_teleon_registry_primitive_match__classify_candidate__signal = (
            py_local_src_teleon_registry_primitive_match__classify_candidate__evidence["semantic_score"]
            + len(py_local_src_teleon_registry_primitive_match__classify_candidate__evidence["keyword_overlap"]) * 0.04
            + len(py_local_src_teleon_registry_primitive_match__classify_candidate__evidence["label_overlap"]) * 0.05
            + len(py_local_src_teleon_registry_primitive_match__classify_candidate__evidence["graph_overlap"]) * 0.05
        )
        py_local_src_teleon_registry_primitive_match__classify_candidate__topical_evidence = (
            py_local_src_teleon_registry_primitive_match__classify_candidate__evidence["exact"]
            or len(py_local_src_teleon_registry_primitive_match__classify_candidate__evidence["keyword_overlap"]) >= 2
            or bool(py_local_src_teleon_registry_primitive_match__classify_candidate__evidence["label_overlap"])
            or bool(py_local_src_teleon_registry_primitive_match__classify_candidate__evidence["graph_overlap"])
            or py_local_src_teleon_registry_primitive_match__classify_candidate__evidence["semantic_score"] >= 0.5
        )
        if py_local_src_teleon_registry_primitive_match__classify_candidate__topical_evidence and py_local_src_teleon_registry_primitive_match__classify_candidate__signal >= py_const_src_teleon_registry_primitive_match__NONDETERMINISTIC_MIN_SIGNAL:
            py_local_src_teleon_registry_primitive_match__classify_candidate__compatibility_result = {
                **py_local_src_teleon_registry_primitive_match__classify_candidate__compatibility_result,
                "fit_class": py_const_src_teleon_registry_primitive_match__FIT_NONDETERMINISTIC_EDIT_MATCH,
                "required_mutations": [py_const_src_teleon_registry_primitive_match__MUTATION_GENERATED_ADAPTER_CANDIDATE],
            }
    py_local_src_teleon_registry_primitive_match__classify_candidate__affinity = py_function_src_teleon_registry_primitive_match__affinity_signal(
        py_arg_src_teleon_registry_primitive_match__classify_candidate__candidate,
        py_arg_src_teleon_registry_primitive_match__classify_candidate__request,
        py_arg_src_teleon_registry_primitive_match__classify_candidate__affinity_table,
    )
    if py_arg_src_teleon_registry_primitive_match__classify_candidate__affinity_table is not None:
        # Applied (clamped, boost-only) value; recorded only when a table is provided so the default
        # no-table output stays byte-identical.
        py_local_src_teleon_registry_primitive_match__classify_candidate__evidence["affinity_boost"] = round(
            min(py_const_src_teleon_registry_primitive_match__AFFINITY_BOOST_CAP, max(0.0, py_local_src_teleon_registry_primitive_match__classify_candidate__affinity)), 6
        )
    py_local_src_teleon_registry_primitive_match__classify_candidate__score = py_function_src_teleon_registry_primitive_match__score_candidate(py_local_src_teleon_registry_primitive_match__classify_candidate__evidence, py_local_src_teleon_registry_primitive_match__classify_candidate__compatibility_result, py_arg_src_teleon_registry_primitive_match__score_candidate__affinity_boost=py_local_src_teleon_registry_primitive_match__classify_candidate__affinity)
    py_local_src_teleon_registry_primitive_match__classify_candidate__adapter_plan = py_function_src_teleon_registry_primitive_match__adapter_plan(
        py_local_src_teleon_registry_primitive_match__classify_candidate__compatibility_result["required_mutations"],
        py_arg_src_teleon_registry_primitive_match__classify_candidate__candidate,
        py_arg_src_teleon_registry_primitive_match__classify_candidate__request,
    )
    return {
        "primitive_id": py_arg_src_teleon_registry_primitive_match__classify_candidate__candidate.get("id") or py_arg_src_teleon_registry_primitive_match__classify_candidate__candidate.get("name"),
        "name": py_arg_src_teleon_registry_primitive_match__classify_candidate__candidate.get("name") or py_arg_src_teleon_registry_primitive_match__classify_candidate__candidate.get("id"),
        "score": py_local_src_teleon_registry_primitive_match__classify_candidate__score,
        "fit_class": py_local_src_teleon_registry_primitive_match__classify_candidate__compatibility_result["fit_class"],
        "graph_assembly_status": py_function_src_teleon_registry_primitive_match__graph_assembly_status(py_local_src_teleon_registry_primitive_match__classify_candidate__compatibility_result["fit_class"]),
        "required_mutations": py_local_src_teleon_registry_primitive_match__classify_candidate__compatibility_result["required_mutations"],
        "adapter_plan": py_local_src_teleon_registry_primitive_match__classify_candidate__adapter_plan,
        "input_direct": py_local_src_teleon_registry_primitive_match__classify_candidate__compatibility_result["input_direct"],
        "output_direct": py_local_src_teleon_registry_primitive_match__classify_candidate__compatibility_result["output_direct"],
        "blocking_reasons": py_local_src_teleon_registry_primitive_match__classify_candidate__evidence["blocking_reasons"],
        "evidence": py_local_src_teleon_registry_primitive_match__classify_candidate__evidence,
        "promotion_required": py_local_src_teleon_registry_primitive_match__classify_candidate__compatibility_result["fit_class"] != py_const_src_teleon_registry_primitive_match__FIT_EXACT_MATCH,
        "serves_truth": False,
    }


def py_function_src_teleon_registry_primitive_match__hybrid_search(py_arg_src_teleon_registry_primitive_match__hybrid_search__request: dict, py_arg_src_teleon_registry_primitive_match__hybrid_search__candidates: list[dict], *, py_arg_src_teleon_registry_primitive_match__hybrid_search__limit: int = 10, py_arg_src_teleon_registry_primitive_match__hybrid_search__include_incompatible: bool = False, py_arg_src_teleon_registry_primitive_match__hybrid_search__blocking_index: dict | None = None, py_arg_src_teleon_registry_primitive_match__hybrid_search__affinity_table: dict | None = None) -> list[dict]:
    py_local_src_teleon_registry_primitive_match__hybrid_search__index = (
        py_arg_src_teleon_registry_primitive_match__hybrid_search__blocking_index
        if isinstance(py_arg_src_teleon_registry_primitive_match__hybrid_search__blocking_index, dict)
        else py_function_src_teleon_registry_primitive_match__blocking_index(py_arg_src_teleon_registry_primitive_match__hybrid_search__candidates)
    )
    py_local_src_teleon_registry_primitive_match__hybrid_search__selection = py_function_src_teleon_registry_primitive_match__blocked_candidate_indexes(
        py_arg_src_teleon_registry_primitive_match__hybrid_search__request,
        py_local_src_teleon_registry_primitive_match__hybrid_search__index,
    )
    py_local_src_teleon_registry_primitive_match__hybrid_search__candidate_indexes = (
        list(range(len(py_arg_src_teleon_registry_primitive_match__hybrid_search__candidates)))
        if py_arg_src_teleon_registry_primitive_match__hybrid_search__include_incompatible
        else py_local_src_teleon_registry_primitive_match__hybrid_search__selection["candidate_indexes"]
    )
    py_local_src_teleon_registry_primitive_match__hybrid_search__results = []
    for py_local_src_teleon_registry_primitive_match__hybrid_search__candidate_index in py_local_src_teleon_registry_primitive_match__hybrid_search__candidate_indexes:
        py_local_src_teleon_registry_primitive_match__hybrid_search__candidate = py_arg_src_teleon_registry_primitive_match__hybrid_search__candidates[py_local_src_teleon_registry_primitive_match__hybrid_search__candidate_index]
        py_local_src_teleon_registry_primitive_match__hybrid_search__classified = py_function_src_teleon_registry_primitive_match__classify_candidate(py_local_src_teleon_registry_primitive_match__hybrid_search__candidate, py_arg_src_teleon_registry_primitive_match__hybrid_search__request, py_arg_src_teleon_registry_primitive_match__classify_candidate__affinity_table=py_arg_src_teleon_registry_primitive_match__hybrid_search__affinity_table)
        py_local_src_teleon_registry_primitive_match__hybrid_search__classified["blocking_index"] = {
            "candidate_index": py_local_src_teleon_registry_primitive_match__hybrid_search__candidate_index,
            "match_count": py_local_src_teleon_registry_primitive_match__hybrid_search__selection["candidate_match_counts"].get(str(py_local_src_teleon_registry_primitive_match__hybrid_search__candidate_index), 0),
            "matched_keys": py_local_src_teleon_registry_primitive_match__hybrid_search__selection["matched_keys"].get(str(py_local_src_teleon_registry_primitive_match__hybrid_search__candidate_index), []),
            "serves_truth": False,
        }
        if py_local_src_teleon_registry_primitive_match__hybrid_search__classified["blocking_reasons"] or py_local_src_teleon_registry_primitive_match__hybrid_search__classified["score"] >= py_const_src_teleon_registry_primitive_match__BLOCK_MIN_SCORE or py_arg_src_teleon_registry_primitive_match__hybrid_search__include_incompatible:
            if py_arg_src_teleon_registry_primitive_match__hybrid_search__include_incompatible or py_local_src_teleon_registry_primitive_match__hybrid_search__classified["fit_class"] != py_const_src_teleon_registry_primitive_match__FIT_INCOMPATIBLE:
                py_local_src_teleon_registry_primitive_match__hybrid_search__results.append(py_local_src_teleon_registry_primitive_match__hybrid_search__classified)
    return sorted(py_local_src_teleon_registry_primitive_match__hybrid_search__results, key=lambda py_arg_src_teleon_registry_primitive_match__hybrid_search__row: (py_arg_src_teleon_registry_primitive_match__hybrid_search__row["score"], py_arg_src_teleon_registry_primitive_match__hybrid_search__row["fit_class"] == py_const_src_teleon_registry_primitive_match__FIT_EXACT_MATCH), reverse=True)[:py_arg_src_teleon_registry_primitive_match__hybrid_search__limit]


def py_function_src_teleon_registry_primitive_match__chain_compatibility(py_arg_src_teleon_registry_primitive_match__chain_compatibility__producer: dict, py_arg_src_teleon_registry_primitive_match__chain_compatibility__consumer: dict) -> dict:
    """Classify whether producer.output_contract can feed consumer.input_contract.

    This is the graph assembly test. It uses the same fit classes as search so the planner can insert direct
    edges, deterministic adapter nodes, generated-adapter candidate nodes, or reject the edge.
    """
    py_local_src_teleon_registry_primitive_match__chain_compatibility__producer_output = py_arg_src_teleon_registry_primitive_match__chain_compatibility__producer.get("output_contract")
    py_local_src_teleon_registry_primitive_match__chain_compatibility__consumer_input = py_arg_src_teleon_registry_primitive_match__chain_compatibility__consumer.get("input_contract")
    py_local_src_teleon_registry_primitive_match__chain_compatibility__direct = py_function_src_teleon_registry_primitive_match__direct_contract_compatible(
        py_local_src_teleon_registry_primitive_match__chain_compatibility__producer_output,
        py_local_src_teleon_registry_primitive_match__chain_compatibility__consumer_input,
    )
    py_local_src_teleon_registry_primitive_match__chain_compatibility__mutations: list[str] = []
    py_local_src_teleon_registry_primitive_match__chain_compatibility__producer_shape = py_function_src_teleon_registry_primitive_match__shape(py_local_src_teleon_registry_primitive_match__chain_compatibility__producer_output)
    py_local_src_teleon_registry_primitive_match__chain_compatibility__consumer_shape = py_function_src_teleon_registry_primitive_match__shape(py_local_src_teleon_registry_primitive_match__chain_compatibility__consumer_input)
    py_local_src_teleon_registry_primitive_match__chain_compatibility__consumer_fields = py_function_src_teleon_registry_primitive_match__fields(py_local_src_teleon_registry_primitive_match__chain_compatibility__consumer_input)
    py_local_src_teleon_registry_primitive_match__chain_compatibility__producer_fields = py_function_src_teleon_registry_primitive_match__fields(py_local_src_teleon_registry_primitive_match__chain_compatibility__producer_output)
    if not py_local_src_teleon_registry_primitive_match__chain_compatibility__direct:
        if py_local_src_teleon_registry_primitive_match__chain_compatibility__consumer_shape in {"object", "dict", "mapping"} and py_local_src_teleon_registry_primitive_match__chain_compatibility__consumer_fields and py_local_src_teleon_registry_primitive_match__chain_compatibility__producer_shape not in {"object", "dict", "mapping"} and len(py_local_src_teleon_registry_primitive_match__chain_compatibility__consumer_fields) == 1:
            py_local_src_teleon_registry_primitive_match__chain_compatibility__mutations.append(py_const_src_teleon_registry_primitive_match__MUTATION_OUTPUT_FIELD_WRAPPER)
        elif py_local_src_teleon_registry_primitive_match__chain_compatibility__producer_fields and py_local_src_teleon_registry_primitive_match__chain_compatibility__consumer_fields and len(py_local_src_teleon_registry_primitive_match__chain_compatibility__producer_fields) == len(py_local_src_teleon_registry_primitive_match__chain_compatibility__consumer_fields) and py_arg_src_teleon_registry_primitive_match__chain_compatibility__consumer.get("deterministic_field_map"):
            py_local_src_teleon_registry_primitive_match__chain_compatibility__mutations.append(py_const_src_teleon_registry_primitive_match__MUTATION_FIELD_RENAME_ADAPTER)
    if py_local_src_teleon_registry_primitive_match__chain_compatibility__direct:
        py_local_src_teleon_registry_primitive_match__chain_compatibility__fit = py_const_src_teleon_registry_primitive_match__FIT_EXACT_MATCH
    elif py_local_src_teleon_registry_primitive_match__chain_compatibility__mutations:
        py_local_src_teleon_registry_primitive_match__chain_compatibility__fit = py_const_src_teleon_registry_primitive_match__FIT_DETERMINISTIC_EDIT_MATCH
    else:
        py_local_src_teleon_registry_primitive_match__chain_compatibility__producer_labels = py_function_src_teleon_registry_primitive_match__primitive_labels(py_arg_src_teleon_registry_primitive_match__chain_compatibility__producer)
        py_local_src_teleon_registry_primitive_match__chain_compatibility__consumer_labels = py_function_src_teleon_registry_primitive_match__primitive_labels(py_arg_src_teleon_registry_primitive_match__chain_compatibility__consumer)
        py_local_src_teleon_registry_primitive_match__chain_compatibility__fit = (
            py_const_src_teleon_registry_primitive_match__FIT_NONDETERMINISTIC_EDIT_MATCH
            if py_local_src_teleon_registry_primitive_match__chain_compatibility__producer_labels & py_local_src_teleon_registry_primitive_match__chain_compatibility__consumer_labels
            else py_const_src_teleon_registry_primitive_match__FIT_INCOMPATIBLE
        )
        if py_local_src_teleon_registry_primitive_match__chain_compatibility__fit == py_const_src_teleon_registry_primitive_match__FIT_NONDETERMINISTIC_EDIT_MATCH:
            py_local_src_teleon_registry_primitive_match__chain_compatibility__mutations.append(py_const_src_teleon_registry_primitive_match__MUTATION_GENERATED_ADAPTER_CANDIDATE)
    py_local_src_teleon_registry_primitive_match__chain_compatibility__request = {
        "input_contract": {"shape": "any"},
        "output_contract": py_local_src_teleon_registry_primitive_match__chain_compatibility__consumer_input,
    }
    return {
        "producer_id": py_arg_src_teleon_registry_primitive_match__chain_compatibility__producer.get("id") or py_arg_src_teleon_registry_primitive_match__chain_compatibility__producer.get("name"),
        "consumer_id": py_arg_src_teleon_registry_primitive_match__chain_compatibility__consumer.get("id") or py_arg_src_teleon_registry_primitive_match__chain_compatibility__consumer.get("name"),
        "fit_class": py_local_src_teleon_registry_primitive_match__chain_compatibility__fit,
        "graph_assembly_status": py_function_src_teleon_registry_primitive_match__graph_assembly_status(py_local_src_teleon_registry_primitive_match__chain_compatibility__fit),
        "required_mutations": py_local_src_teleon_registry_primitive_match__chain_compatibility__mutations,
        "adapter_plan": py_function_src_teleon_registry_primitive_match__adapter_plan(py_local_src_teleon_registry_primitive_match__chain_compatibility__mutations, py_arg_src_teleon_registry_primitive_match__chain_compatibility__producer, py_local_src_teleon_registry_primitive_match__chain_compatibility__request),
        "serves_truth": False,
    }


def py_function_src_teleon_registry_primitive_match__assemble_match_plan(py_arg_src_teleon_registry_primitive_match__assemble_match_plan__request: dict, py_arg_src_teleon_registry_primitive_match__assemble_match_plan__candidates: list[dict], *, py_arg_src_teleon_registry_primitive_match__assemble_match_plan__limit: int = 10) -> dict:
    py_local_src_teleon_registry_primitive_match__assemble_match_plan__matches = py_function_src_teleon_registry_primitive_match__hybrid_search(
        py_arg_src_teleon_registry_primitive_match__assemble_match_plan__request,
        py_arg_src_teleon_registry_primitive_match__assemble_match_plan__candidates,
        py_arg_src_teleon_registry_primitive_match__hybrid_search__limit=py_arg_src_teleon_registry_primitive_match__assemble_match_plan__limit,
    )
    py_inst_src_teleon_registry_primitive_match__assemble_match_plan__by_fit = Counter(row["fit_class"] for row in py_local_src_teleon_registry_primitive_match__assemble_match_plan__matches)
    return {
        "query": py_arg_src_teleon_registry_primitive_match__assemble_match_plan__request.get("intent") or py_arg_src_teleon_registry_primitive_match__assemble_match_plan__request.get("query") or py_arg_src_teleon_registry_primitive_match__assemble_match_plan__request.get("id"),
        "search_dimensions": list(py_const_src_teleon_registry_primitive_match__SEARCH_DIMENSIONS),
        "blocking_profile_fields": list(py_const_src_teleon_registry_primitive_match__BLOCK_PROFILE_FIELDS),
        "matches": py_local_src_teleon_registry_primitive_match__assemble_match_plan__matches,
        "fit_counts": dict(py_inst_src_teleon_registry_primitive_match__assemble_match_plan__by_fit),
        "serves_truth": False,
        "promotion_boundary": "exact matches are usable candidate edges; deterministic/non-deterministic edits require proof before promotion",
    }


def py_function_src_teleon_registry_primitive_match__self_test() -> int:
    py_local_src_teleon_registry_primitive_match__self_test__failures: list[str] = []

    def py_function_src_teleon_registry_primitive_match__self_test__check(py_arg_src_teleon_registry_primitive_match__self_test_check__name: str, py_arg_src_teleon_registry_primitive_match__self_test_check__ok: bool) -> None:
        print(f"  [{'ok' if py_arg_src_teleon_registry_primitive_match__self_test_check__ok else 'FAIL'}] {py_arg_src_teleon_registry_primitive_match__self_test_check__name}")
        if not py_arg_src_teleon_registry_primitive_match__self_test_check__ok:
            py_local_src_teleon_registry_primitive_match__self_test__failures.append(py_arg_src_teleon_registry_primitive_match__self_test_check__name)

    py_local_src_teleon_registry_primitive_match__self_test__candidates = [
        {
            "id": "primitive.web.fetch_with_retry",
            "name": "Fetch URL with retry",
            "purpose": "Fetch one URL and return HTML/status with retry and timeout policy.",
            "labels": ["web", "http", "fetch", "retry"],
            "input_contract": {"shape": "object", "fields": {"url": "string"}},
            "output_contract": {"shape": "object", "fields": {"html": "string", "status": "integer"}},
            "graph_edges": [{"to": "primitive.scrape.extract_tables"}],
        },
        {
            "id": "primitive.rate.normalize_row",
            "name": "Normalize one rate row",
            "purpose": "Normalize a scalar jurisdiction interest-rate row.",
            "labels": ["interest", "rate", "normalize"],
            "input_contract": {"shape": "scalar", "fields": {"row": "object"}},
            "output_contract": {"shape": "scalar", "fields": {"rate_record": "object"}},
        },
        {
            "id": "primitive.rate.parse_numeric_value",
            "name": "Parse numeric rate value",
            "purpose": "Parse one maximum interest rate value from text.",
            "labels": ["interest", "rate", "parse"],
            "input_contract": {"shape": "scalar", "fields": {"text": "string"}},
            "output_contract": {"shape": "number"},
        },
        {
            "id": "primitive.scrape.llm_browser",
            "name": "LLM browser scraper",
            "purpose": "Use an LLM browser to scrape country interest-rate tables when structure is unknown.",
            "labels": ["web", "scrape", "interest", "rate", "llm", "browser"],
            "input_contract": {"shape": "object", "fields": {"url": "string"}},
            "output_contract": {"shape": "object", "fields": {"text": "string"}},
        },
        {
            "id": "primitive.weather.forecast",
            "name": "Weather forecast",
            "purpose": "Get weather forecast for a location.",
            "labels": ["weather"],
            "input_contract": {"shape": "object", "fields": {"location": "string"}},
            "output_contract": {"shape": "object", "fields": {"forecast": "string"}},
        },
    ]

    py_local_src_teleon_registry_primitive_match__self_test__exact_request = {
        "intent": "fetch url html",
        "labels": ["web", "fetch"],
        "input_contract": {"shape": "object", "fields": {"url": "string"}},
        "output_contract": {"shape": "object", "fields": {"html": "string"}},
        "graph_neighbors": ["primitive.scrape.extract_tables"],
    }
    py_local_src_teleon_registry_primitive_match__self_test__batch_request = {
        "intent": "normalize maximum interest rates for many jurisdiction rows",
        "labels": ["interest", "rate", "normalize"],
        "input_contract": {"shape": "sequence", "fields": {"row": "object"}},
        "output_contract": {"shape": "object", "fields": {"rate_record": "object"}},
    }
    py_local_src_teleon_registry_primitive_match__self_test__wrapper_request = {
        "intent": "parse maximum interest rate into rate_value field",
        "labels": ["interest", "rate", "parse"],
        "input_contract": {"shape": "scalar", "fields": {"text": "string"}},
        "output_contract": {"shape": "object", "fields": {"rate_value": "number"}},
    }
    py_local_src_teleon_registry_primitive_match__self_test__generated_request = {
        "intent": "deterministic extractor for country interest rate table",
        "labels": ["web", "scrape", "interest", "rate", "deterministic"],
        "input_contract": {"shape": "object", "fields": {"url": "string"}},
        "output_contract": {"shape": "object", "fields": {"rows": "array"}},
    }
    py_local_src_teleon_registry_primitive_match__self_test__unrelated_request = {
        "intent": "compile Rust crate",
        "labels": ["rust", "compiler"],
        "input_contract": {"shape": "object", "fields": {"crate": "string"}},
        "output_contract": {"shape": "object", "fields": {"binary": "path"}},
    }

    py_local_src_teleon_registry_primitive_match__self_test__blocking_index = py_function_src_teleon_registry_primitive_match__blocking_index(py_local_src_teleon_registry_primitive_match__self_test__candidates)
    py_local_src_teleon_registry_primitive_match__self_test__batch_selection = py_function_src_teleon_registry_primitive_match__blocked_candidate_indexes(
        py_local_src_teleon_registry_primitive_match__self_test__batch_request,
        py_local_src_teleon_registry_primitive_match__self_test__blocking_index,
    )
    py_local_src_teleon_registry_primitive_match__self_test__exact = py_function_src_teleon_registry_primitive_match__hybrid_search(py_local_src_teleon_registry_primitive_match__self_test__exact_request, py_local_src_teleon_registry_primitive_match__self_test__candidates)[0]
    py_local_src_teleon_registry_primitive_match__self_test__batch = next(row for row in py_function_src_teleon_registry_primitive_match__hybrid_search(py_local_src_teleon_registry_primitive_match__self_test__batch_request, py_local_src_teleon_registry_primitive_match__self_test__candidates) if row["primitive_id"] == "primitive.rate.normalize_row")
    py_local_src_teleon_registry_primitive_match__self_test__batch_indexed = next(row for row in py_function_src_teleon_registry_primitive_match__hybrid_search(py_local_src_teleon_registry_primitive_match__self_test__batch_request, py_local_src_teleon_registry_primitive_match__self_test__candidates, py_arg_src_teleon_registry_primitive_match__hybrid_search__blocking_index=py_local_src_teleon_registry_primitive_match__self_test__blocking_index) if row["primitive_id"] == "primitive.rate.normalize_row")
    py_local_src_teleon_registry_primitive_match__self_test__wrapped = next(row for row in py_function_src_teleon_registry_primitive_match__hybrid_search(py_local_src_teleon_registry_primitive_match__self_test__wrapper_request, py_local_src_teleon_registry_primitive_match__self_test__candidates) if row["primitive_id"] == "primitive.rate.parse_numeric_value")
    py_local_src_teleon_registry_primitive_match__self_test__generated = next(row for row in py_function_src_teleon_registry_primitive_match__hybrid_search(py_local_src_teleon_registry_primitive_match__self_test__generated_request, py_local_src_teleon_registry_primitive_match__self_test__candidates) if row["primitive_id"] == "primitive.scrape.llm_browser")
    py_local_src_teleon_registry_primitive_match__self_test__unrelated = py_function_src_teleon_registry_primitive_match__hybrid_search(py_local_src_teleon_registry_primitive_match__self_test__unrelated_request, py_local_src_teleon_registry_primitive_match__self_test__candidates)
    py_local_src_teleon_registry_primitive_match__self_test__plan = py_function_src_teleon_registry_primitive_match__assemble_match_plan(py_local_src_teleon_registry_primitive_match__self_test__batch_request, py_local_src_teleon_registry_primitive_match__self_test__candidates)
    py_local_src_teleon_registry_primitive_match__self_test__profile = py_function_src_teleon_registry_primitive_match__blocking_profile(py_local_src_teleon_registry_primitive_match__self_test__candidates[3])
    py_local_src_teleon_registry_primitive_match__self_test__chain_direct = py_function_src_teleon_registry_primitive_match__chain_compatibility(
        py_local_src_teleon_registry_primitive_match__self_test__candidates[0],
        {
            "id": "primitive.scrape.extract_html",
            "labels": ["web", "scrape"],
            "input_contract": {"shape": "object", "fields": {"html": "string"}},
            "output_contract": {"shape": "object", "fields": {"tables": "array"}},
        },
    )
    py_local_src_teleon_registry_primitive_match__self_test__chain_wrapped = py_function_src_teleon_registry_primitive_match__chain_compatibility(
        py_local_src_teleon_registry_primitive_match__self_test__candidates[2],
        {
            "id": "primitive.rate.store",
            "labels": ["interest", "rate"],
            "input_contract": {"shape": "object", "fields": {"rate_value": "number"}},
            "output_contract": {"shape": "object", "fields": {"stored": "boolean"}},
        },
    )

    # Optional composition-affinity boost: default OFF (zero behavior change), boost-only when provided.
    py_local_src_teleon_registry_primitive_match__self_test__affinity_request = {
        "intent": "parse html tables",
        "labels": ["web", "parse"],
        "producer_edge": "Url->Html",
        "input_contract": {"shape": "object", "fields": {"html": "string"}},
        "output_contract": {"shape": "object", "fields": {"tables": "array"}},
    }
    py_local_src_teleon_registry_primitive_match__self_test__affinity_candidates = [
        {
            "id": "primitive.html.table_parser_alpha",
            "name": "HTML table parser",
            "purpose": "Parse tables from HTML.",
            "labels": ["web", "parse"],
            "input_contract": {"shape": "object", "fields": {"html": "string"}},
            "output_contract": {"shape": "object", "fields": {"tables": "array"}},
        },
        {
            "id": "primitive.html.table_parser_beta",
            "name": "HTML table parser",
            "purpose": "Parse tables from HTML.",
            "labels": ["web", "parse"],
            "input_contract": {"shape": "object", "fields": {"html": "string"}},
            "output_contract": {"shape": "object", "fields": {"tables": "array"}},
        },
    ]
    py_local_src_teleon_registry_primitive_match__self_test__affinity_pair = py_function_src_teleon_registry_composition_affinity__pair_id("Url->Html", "primitive.html.table_parser_beta")
    py_local_src_teleon_registry_primitive_match__self_test__affinity_table = {
        py_local_src_teleon_registry_primitive_match__self_test__affinity_pair: {
            "pair_id": py_local_src_teleon_registry_primitive_match__self_test__affinity_pair,
            "producer_edge": "Url->Html",
            "consumer_edge": "primitive.html.table_parser_beta",
            "affinity": 2.0,
        },
    }
    py_local_src_teleon_registry_primitive_match__self_test__affinity_baseline = py_function_src_teleon_registry_primitive_match__hybrid_search(py_local_src_teleon_registry_primitive_match__self_test__affinity_request, py_local_src_teleon_registry_primitive_match__self_test__affinity_candidates)
    py_local_src_teleon_registry_primitive_match__self_test__affinity_boosted = py_function_src_teleon_registry_primitive_match__hybrid_search(py_local_src_teleon_registry_primitive_match__self_test__affinity_request, py_local_src_teleon_registry_primitive_match__self_test__affinity_candidates, py_arg_src_teleon_registry_primitive_match__hybrid_search__affinity_table=py_local_src_teleon_registry_primitive_match__self_test__affinity_table)
    py_local_src_teleon_registry_primitive_match__self_test__affinity_rescue_request = {**py_local_src_teleon_registry_primitive_match__self_test__unrelated_request, "producer_edge": "Crate->Binary"}
    py_local_src_teleon_registry_primitive_match__self_test__affinity_rescue_pair = py_function_src_teleon_registry_composition_affinity__pair_id("Crate->Binary", "primitive.weather.forecast")
    py_local_src_teleon_registry_primitive_match__self_test__affinity_rescued = py_function_src_teleon_registry_primitive_match__hybrid_search(
        py_local_src_teleon_registry_primitive_match__self_test__affinity_rescue_request,
        py_local_src_teleon_registry_primitive_match__self_test__candidates,
        py_arg_src_teleon_registry_primitive_match__hybrid_search__affinity_table={py_local_src_teleon_registry_primitive_match__self_test__affinity_rescue_pair: {"pair_id": py_local_src_teleon_registry_primitive_match__self_test__affinity_rescue_pair, "affinity": 100.0}},
    )

    py_function_src_teleon_registry_primitive_match__self_test__check("exact match uses blocking + direct I/O contracts", py_local_src_teleon_registry_primitive_match__self_test__exact["fit_class"] == py_const_src_teleon_registry_primitive_match__FIT_EXACT_MATCH and "input_contract" in py_local_src_teleon_registry_primitive_match__self_test__exact["blocking_reasons"])
    py_function_src_teleon_registry_primitive_match__self_test__check("blocking index exposes required fields and retrieves the mutation candidate", set(py_const_src_teleon_registry_primitive_match__BLOCKING_INDEX_FIELDS) <= set(py_local_src_teleon_registry_primitive_match__self_test__blocking_index) and 1 in py_local_src_teleon_registry_primitive_match__self_test__batch_selection["candidate_indexes"])
    py_function_src_teleon_registry_primitive_match__self_test__check("indexed search preserves mutation-aware rerank result", py_local_src_teleon_registry_primitive_match__self_test__batch_indexed["fit_class"] == py_local_src_teleon_registry_primitive_match__self_test__batch["fit_class"] and py_local_src_teleon_registry_primitive_match__self_test__batch_indexed["blocking_index"]["match_count"] >= 1)
    py_function_src_teleon_registry_primitive_match__self_test__check("scalar primitive matches batch request through deterministic scalar_to_sequence", py_local_src_teleon_registry_primitive_match__self_test__batch["fit_class"] == py_const_src_teleon_registry_primitive_match__FIT_DETERMINISTIC_EDIT_MATCH and py_const_src_teleon_registry_primitive_match__MUTATION_SCALAR_TO_SEQUENCE in py_local_src_teleon_registry_primitive_match__self_test__batch["required_mutations"])
    py_function_src_teleon_registry_primitive_match__self_test__check("scalar output can satisfy object output through deterministic output wrapper", py_local_src_teleon_registry_primitive_match__self_test__wrapped["fit_class"] == py_const_src_teleon_registry_primitive_match__FIT_DETERMINISTIC_EDIT_MATCH and py_const_src_teleon_registry_primitive_match__MUTATION_OUTPUT_FIELD_WRAPPER in py_local_src_teleon_registry_primitive_match__self_test__wrapped["required_mutations"])
    py_function_src_teleon_registry_primitive_match__self_test__check("strong topic match with incompatible contracts becomes non-deterministic generated adapter candidate", py_local_src_teleon_registry_primitive_match__self_test__generated["fit_class"] == py_const_src_teleon_registry_primitive_match__FIT_NONDETERMINISTIC_EDIT_MATCH and py_const_src_teleon_registry_primitive_match__MUTATION_GENERATED_ADAPTER_CANDIDATE in py_local_src_teleon_registry_primitive_match__self_test__generated["required_mutations"])
    py_function_src_teleon_registry_primitive_match__self_test__check("search rows can precompute blocking profiles", set(py_const_src_teleon_registry_primitive_match__BLOCK_PROFILE_FIELDS) <= set(py_local_src_teleon_registry_primitive_match__self_test__profile) and py_const_src_teleon_registry_primitive_match__MUTATION_BROWSER_TO_DETERMINISTIC_EXTRACTOR in py_local_src_teleon_registry_primitive_match__self_test__profile["mutation_hints"])
    py_function_src_teleon_registry_primitive_match__self_test__check("deterministic edit hit emits adapter graph node plan", py_local_src_teleon_registry_primitive_match__self_test__batch["graph_assembly_status"] == py_const_src_teleon_registry_primitive_match__GRAPH_STATUS_CHAINABLE_WITH_ADAPTERS and any(node["node_kind"] == "normalize_to_sequence_then_map" for node in py_local_src_teleon_registry_primitive_match__self_test__batch["adapter_plan"]))
    py_function_src_teleon_registry_primitive_match__self_test__check("non-deterministic edit hit is isolated to generated-candidate lane", py_local_src_teleon_registry_primitive_match__self_test__generated["graph_assembly_status"] == py_const_src_teleon_registry_primitive_match__GRAPH_STATUS_GENERATED_ADAPTER_REQUIRED and any(node["lane"] == "nondeterministic_generated_candidate" for node in py_local_src_teleon_registry_primitive_match__self_test__generated["adapter_plan"]))
    py_function_src_teleon_registry_primitive_match__self_test__check("producer output can chain directly into consumer input", py_local_src_teleon_registry_primitive_match__self_test__chain_direct["fit_class"] == py_const_src_teleon_registry_primitive_match__FIT_EXACT_MATCH and py_local_src_teleon_registry_primitive_match__self_test__chain_direct["graph_assembly_status"] == py_const_src_teleon_registry_primitive_match__GRAPH_STATUS_CHAINABLE_AS_IS)
    py_function_src_teleon_registry_primitive_match__self_test__check("producer scalar output can chain through deterministic output wrapper", py_local_src_teleon_registry_primitive_match__self_test__chain_wrapped["fit_class"] == py_const_src_teleon_registry_primitive_match__FIT_DETERMINISTIC_EDIT_MATCH and py_const_src_teleon_registry_primitive_match__MUTATION_OUTPUT_FIELD_WRAPPER in py_local_src_teleon_registry_primitive_match__self_test__chain_wrapped["required_mutations"])
    py_function_src_teleon_registry_primitive_match__self_test__check("unrelated primitive is filtered out", not py_local_src_teleon_registry_primitive_match__self_test__unrelated)
    py_function_src_teleon_registry_primitive_match__self_test__check("plan exposes every search dimension and never serves truth", set(py_const_src_teleon_registry_primitive_match__SEARCH_DIMENSIONS) <= set(py_local_src_teleon_registry_primitive_match__self_test__plan["search_dimensions"]) and py_local_src_teleon_registry_primitive_match__self_test__plan["serves_truth"] is False)
    py_function_src_teleon_registry_primitive_match__self_test__check("plan exposes blocking profile fields for efficient retrieval", set(py_const_src_teleon_registry_primitive_match__BLOCK_PROFILE_FIELDS) <= set(py_local_src_teleon_registry_primitive_match__self_test__plan["blocking_profile_fields"]))
    py_function_src_teleon_registry_primitive_match__self_test__check("non-exact matches require promotion/proofs before trust", all(row["promotion_required"] for row in py_local_src_teleon_registry_primitive_match__self_test__plan["matches"] if row["fit_class"] != py_const_src_teleon_registry_primitive_match__FIT_EXACT_MATCH))
    py_function_src_teleon_registry_primitive_match__self_test__check(
        "affinity default OFF: no table means tied scores and no affinity evidence (zero behavior change)",
        py_function_src_teleon_registry_primitive_match__classify_candidate(py_local_src_teleon_registry_primitive_match__self_test__affinity_candidates[0], py_local_src_teleon_registry_primitive_match__self_test__affinity_request)
        == py_function_src_teleon_registry_primitive_match__classify_candidate(py_local_src_teleon_registry_primitive_match__self_test__affinity_candidates[0], py_local_src_teleon_registry_primitive_match__self_test__affinity_request, py_arg_src_teleon_registry_primitive_match__classify_candidate__affinity_table=None)
        and all("affinity_boost" not in row["evidence"] for row in py_local_src_teleon_registry_primitive_match__self_test__affinity_baseline)
        and py_local_src_teleon_registry_primitive_match__self_test__affinity_baseline[0]["score"] == py_local_src_teleon_registry_primitive_match__self_test__affinity_baseline[1]["score"],
    )
    py_function_src_teleon_registry_primitive_match__self_test__check(
        "with a synthetic affinity table the known-good pair ranks higher (capped additive boost, fit_class untouched)",
        py_local_src_teleon_registry_primitive_match__self_test__affinity_boosted[0]["primitive_id"] == "primitive.html.table_parser_beta"
        and py_local_src_teleon_registry_primitive_match__self_test__affinity_boosted[0]["score"] > py_local_src_teleon_registry_primitive_match__self_test__affinity_boosted[1]["score"]
        and py_local_src_teleon_registry_primitive_match__self_test__affinity_boosted[0]["evidence"]["affinity_boost"] == py_const_src_teleon_registry_primitive_match__AFFINITY_BOOST_CAP
        and py_local_src_teleon_registry_primitive_match__self_test__affinity_boosted[1]["evidence"]["affinity_boost"] == 0.0
        and py_local_src_teleon_registry_primitive_match__self_test__affinity_boosted[0]["fit_class"] == py_local_src_teleon_registry_primitive_match__self_test__affinity_baseline[0]["fit_class"]
        and py_local_src_teleon_registry_primitive_match__self_test__affinity_boosted[1]["score"] == py_local_src_teleon_registry_primitive_match__self_test__affinity_baseline[1]["score"],
    )
    py_function_src_teleon_registry_primitive_match__self_test__check(
        "affinity never overrides contract compatibility: huge affinity cannot rescue an incompatible candidate",
        not py_local_src_teleon_registry_primitive_match__self_test__affinity_rescued,
    )

    if py_local_src_teleon_registry_primitive_match__self_test__failures:
        print(f"\nFAIL - primitive_match: {len(py_local_src_teleon_registry_primitive_match__self_test__failures)} failure(s)")
        return 1
    print("\nPASS - primitive_match: hybrid primitive blocking/search + exact/deterministic/non-deterministic fit classes")
    return 0


if __name__ == "__main__":
    raise SystemExit(py_function_src_teleon_registry_primitive_match__self_test())
