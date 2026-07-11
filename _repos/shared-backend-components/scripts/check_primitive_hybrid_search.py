#!/usr/bin/env python3
"""Proof: primitive hybrid search uses blocking, contracts, graph evidence, and mutation-aware fit classes."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import json
import sys
from pathlib import Path


py_const_scripts_check_primitive_hybrid_search__REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(py_const_scripts_check_primitive_hybrid_search__REPO) not in sys.path:
    sys.path.insert(0, str(py_const_scripts_check_primitive_hybrid_search__REPO))

from src.teleon.registry import primitive_match as py_var_scripts_check_primitive_hybrid_search__primitive_match


py_const_scripts_check_primitive_hybrid_search__CONTRACT = (
    _resource("architecture/primitive_hybrid_search_contracts.json")
)

py_const_scripts_check_primitive_hybrid_search__REQUIRED_DIMENSIONS = {
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
}

py_const_scripts_check_primitive_hybrid_search__REQUIRED_FIT_CLASSES = {
    "exact_match",
    "deterministic_edit_match",
    "nondeterministic_edit_match",
    "incompatible",
}

py_const_scripts_check_primitive_hybrid_search__REQUIRED_MUTATIONS = {
    "scalar_to_sequence",
    "output_field_wrapper",
    "field_rename_adapter",
    "retry_cache_rate_limit_adapter",
    "model_cost_downshift",
    "browser_to_deterministic_extractor",
    "local_api_implementation_swap",
    "generated_adapter_candidate",
}

py_const_scripts_check_primitive_hybrid_search__REQUIRED_RESULT_FIELDS = {
    "fit_class",
    "graph_assembly_status",
    "blocking_index",
    "blocking_reasons",
    "evidence",
    "required_mutations",
    "adapter_plan",
    "promotion_required",
    "serves_truth",
}

py_const_scripts_check_primitive_hybrid_search__REQUIRED_GRAPH_STATUSES = {
    "chainable_as_is",
    "chainable_with_adapter_nodes",
    "candidate_generated_adapter_required",
    "not_chainable",
}

py_const_scripts_check_primitive_hybrid_search__REQUIRED_BLOCKING_INDEX_FIELDS = {
    "candidate_count",
    "profile_fields",
    "inverted",
    "profile_keys",
    "serves_truth",
}
py_const_scripts_check_primitive_hybrid_search__REQUIRED_COMPACT_VIEW_LANES = {
    "deterministic_compact_view",
    "nondeterministic_enriched_view",
}


def py_function_scripts_check_primitive_hybrid_search__load_contract():
    return json.loads(py_const_scripts_check_primitive_hybrid_search__CONTRACT.read_text(encoding="utf-8"))


def py_function_scripts_check_primitive_hybrid_search___self_test():
    py_local_scripts_check_primitive_hybrid_search__self_test__failures = []

    def py_function_scripts_check_primitive_hybrid_search___self_test__check(py_arg_name, py_arg_ok, py_arg_detail=""):
        print(f"  [{'ok' if py_arg_ok else 'FAIL'}] {py_arg_name}{(': ' + py_arg_detail) if py_arg_detail and not py_arg_ok else ''}")
        if not py_arg_ok:
            py_local_scripts_check_primitive_hybrid_search__self_test__failures.append(py_arg_name)

    py_local_scripts_check_primitive_hybrid_search__self_test__contract = py_function_scripts_check_primitive_hybrid_search__load_contract()
    py_local_scripts_check_primitive_hybrid_search__self_test__contract_dimensions = set(
        py_local_scripts_check_primitive_hybrid_search__self_test__contract.get("required_search_dimensions", [])
    )
    py_local_scripts_check_primitive_hybrid_search__self_test__contract_fit_classes = set(
        py_local_scripts_check_primitive_hybrid_search__self_test__contract.get("fit_classes", [])
    )
    py_local_scripts_check_primitive_hybrid_search__self_test__contract_mutations = {
        py_var_row.get("id")
        for py_var_row in py_local_scripts_check_primitive_hybrid_search__self_test__contract.get("deterministic_mutations", [])
    } | {
        py_var_row.get("id")
        for py_var_row in py_local_scripts_check_primitive_hybrid_search__self_test__contract.get("nondeterministic_mutations", [])
    }
    py_local_scripts_check_primitive_hybrid_search__self_test__contract_result_fields = set(
        py_local_scripts_check_primitive_hybrid_search__self_test__contract.get("required_result_fields", [])
    )
    py_local_scripts_check_primitive_hybrid_search__self_test__contract_graph_statuses = set(
        py_local_scripts_check_primitive_hybrid_search__self_test__contract.get("graph_assembly_statuses", [])
    )
    py_local_scripts_check_primitive_hybrid_search__self_test__contract_blocking_profile_fields = set(
        py_local_scripts_check_primitive_hybrid_search__self_test__contract.get("blocking_profile_fields", [])
    )
    py_local_scripts_check_primitive_hybrid_search__self_test__contract_blocking_index_fields = set(
        py_local_scripts_check_primitive_hybrid_search__self_test__contract.get("blocking_index_fields", [])
    )
    py_local_scripts_check_primitive_hybrid_search__self_test__contract_compact_view_lanes = set(
        py_local_scripts_check_primitive_hybrid_search__self_test__contract.get("compact_view_lanes", [])
    )
    py_local_scripts_check_primitive_hybrid_search__self_test__doc_text = (
        _resource("docs/codex/primitive-hybrid-search-and-mutation-routing.md")
    ).read_text(encoding="utf-8")
    py_local_scripts_check_primitive_hybrid_search__self_test__module_dimensions = set(
        py_var_scripts_check_primitive_hybrid_search__primitive_match.py_const_src_teleon_registry_primitive_match__SEARCH_DIMENSIONS
    )
    py_local_scripts_check_primitive_hybrid_search__self_test__module_fit_classes = {
        py_var_scripts_check_primitive_hybrid_search__primitive_match.py_const_src_teleon_registry_primitive_match__FIT_EXACT_MATCH,
        py_var_scripts_check_primitive_hybrid_search__primitive_match.py_const_src_teleon_registry_primitive_match__FIT_DETERMINISTIC_EDIT_MATCH,
        py_var_scripts_check_primitive_hybrid_search__primitive_match.py_const_src_teleon_registry_primitive_match__FIT_NONDETERMINISTIC_EDIT_MATCH,
        py_var_scripts_check_primitive_hybrid_search__primitive_match.py_const_src_teleon_registry_primitive_match__FIT_INCOMPATIBLE,
    }
    py_local_scripts_check_primitive_hybrid_search__self_test__module_mutations = {
        py_var_scripts_check_primitive_hybrid_search__primitive_match.py_const_src_teleon_registry_primitive_match__MUTATION_SCALAR_TO_SEQUENCE,
        py_var_scripts_check_primitive_hybrid_search__primitive_match.py_const_src_teleon_registry_primitive_match__MUTATION_OUTPUT_FIELD_WRAPPER,
        py_var_scripts_check_primitive_hybrid_search__primitive_match.py_const_src_teleon_registry_primitive_match__MUTATION_FIELD_RENAME_ADAPTER,
        py_var_scripts_check_primitive_hybrid_search__primitive_match.py_const_src_teleon_registry_primitive_match__MUTATION_RETRY_CACHE_RATE_LIMIT_ADAPTER,
        py_var_scripts_check_primitive_hybrid_search__primitive_match.py_const_src_teleon_registry_primitive_match__MUTATION_MODEL_COST_DOWNSHIFT,
        py_var_scripts_check_primitive_hybrid_search__primitive_match.py_const_src_teleon_registry_primitive_match__MUTATION_BROWSER_TO_DETERMINISTIC_EXTRACTOR,
        py_var_scripts_check_primitive_hybrid_search__primitive_match.py_const_src_teleon_registry_primitive_match__MUTATION_LOCAL_API_IMPLEMENTATION_SWAP,
        py_var_scripts_check_primitive_hybrid_search__primitive_match.py_const_src_teleon_registry_primitive_match__MUTATION_GENERATED_ADAPTER_CANDIDATE,
    }

    py_function_scripts_check_primitive_hybrid_search___self_test__check(
        "contract is candidate evidence, not truth",
        py_local_scripts_check_primitive_hybrid_search__self_test__contract.get("serves_truth") is False,
    )
    py_function_scripts_check_primitive_hybrid_search___self_test__check(
        "contract lists every required search dimension",
        py_const_scripts_check_primitive_hybrid_search__REQUIRED_DIMENSIONS <= py_local_scripts_check_primitive_hybrid_search__self_test__contract_dimensions,
        str(sorted(py_const_scripts_check_primitive_hybrid_search__REQUIRED_DIMENSIONS - py_local_scripts_check_primitive_hybrid_search__self_test__contract_dimensions)),
    )
    py_function_scripts_check_primitive_hybrid_search___self_test__check(
        "module exposes every required search dimension",
        py_const_scripts_check_primitive_hybrid_search__REQUIRED_DIMENSIONS <= py_local_scripts_check_primitive_hybrid_search__self_test__module_dimensions,
        str(sorted(py_const_scripts_check_primitive_hybrid_search__REQUIRED_DIMENSIONS - py_local_scripts_check_primitive_hybrid_search__self_test__module_dimensions)),
    )
    py_function_scripts_check_primitive_hybrid_search___self_test__check(
        "contract and module cover all fit classes",
        py_const_scripts_check_primitive_hybrid_search__REQUIRED_FIT_CLASSES <= py_local_scripts_check_primitive_hybrid_search__self_test__contract_fit_classes
        and py_const_scripts_check_primitive_hybrid_search__REQUIRED_FIT_CLASSES <= py_local_scripts_check_primitive_hybrid_search__self_test__module_fit_classes,
    )
    py_function_scripts_check_primitive_hybrid_search___self_test__check(
        "contract and module cover deterministic and non-deterministic mutation lanes",
        py_const_scripts_check_primitive_hybrid_search__REQUIRED_MUTATIONS <= py_local_scripts_check_primitive_hybrid_search__self_test__contract_mutations
        and py_const_scripts_check_primitive_hybrid_search__REQUIRED_MUTATIONS <= py_local_scripts_check_primitive_hybrid_search__self_test__module_mutations,
    )
    py_function_scripts_check_primitive_hybrid_search___self_test__check(
        "contract requires graph assembly statuses and result fields",
        py_const_scripts_check_primitive_hybrid_search__REQUIRED_RESULT_FIELDS <= py_local_scripts_check_primitive_hybrid_search__self_test__contract_result_fields
        and py_const_scripts_check_primitive_hybrid_search__REQUIRED_GRAPH_STATUSES <= py_local_scripts_check_primitive_hybrid_search__self_test__contract_graph_statuses,
    )
    py_function_scripts_check_primitive_hybrid_search___self_test__check(
        "contract and module expose blocking profile fields",
        set(py_var_scripts_check_primitive_hybrid_search__primitive_match.py_const_src_teleon_registry_primitive_match__BLOCK_PROFILE_FIELDS)
        <= py_local_scripts_check_primitive_hybrid_search__self_test__contract_blocking_profile_fields,
    )
    py_function_scripts_check_primitive_hybrid_search___self_test__check(
        "contract and module expose blocking index fields",
        py_const_scripts_check_primitive_hybrid_search__REQUIRED_BLOCKING_INDEX_FIELDS
        <= py_local_scripts_check_primitive_hybrid_search__self_test__contract_blocking_index_fields
        and py_const_scripts_check_primitive_hybrid_search__REQUIRED_BLOCKING_INDEX_FIELDS
        <= set(py_var_scripts_check_primitive_hybrid_search__primitive_match.py_const_src_teleon_registry_primitive_match__BLOCKING_INDEX_FIELDS),
    )
    py_function_scripts_check_primitive_hybrid_search___self_test__check(
        "compact LLM views have deterministic and nondeterministic candidate lanes",
        py_const_scripts_check_primitive_hybrid_search__REQUIRED_COMPACT_VIEW_LANES
        <= py_local_scripts_check_primitive_hybrid_search__self_test__contract_compact_view_lanes
        and "deterministic compact view" in py_local_scripts_check_primitive_hybrid_search__self_test__doc_text
        and "nondeterministic enriched view" in py_local_scripts_check_primitive_hybrid_search__self_test__doc_text
        and "Neither serves truth by itself" in py_local_scripts_check_primitive_hybrid_search__self_test__doc_text,
    )
    py_function_scripts_check_primitive_hybrid_search___self_test__check(
        "schema boilerplate is blocked from creating false semantic matches",
        {"shape", "object", "string"} <= py_var_scripts_check_primitive_hybrid_search__primitive_match.py_const_src_teleon_registry_primitive_match__STOPWORDS,
    )
    py_function_scripts_check_primitive_hybrid_search___self_test__check(
        "primitive_match self-test passes",
        py_var_scripts_check_primitive_hybrid_search__primitive_match.py_function_src_teleon_registry_primitive_match__self_test() == 0,
    )

    py_local_scripts_check_primitive_hybrid_search__self_test__unrelated_request = {
        "intent": "compile Rust crate",
        "labels": ["rust", "compiler"],
        "input_contract": {"shape": "object", "fields": {"crate": "string"}},
        "output_contract": {"shape": "object", "fields": {"binary": "path"}},
    }
    py_local_scripts_check_primitive_hybrid_search__self_test__unrelated_candidate = {
        "id": "primitive.weather.forecast",
        "name": "Weather forecast",
        "purpose": "Get weather forecast for a location.",
        "labels": ["weather"],
        "input_contract": {"shape": "object", "fields": {"location": "string"}},
        "output_contract": {"shape": "object", "fields": {"forecast": "string"}},
    }
    py_local_scripts_check_primitive_hybrid_search__self_test__unrelated_hits = (
        py_var_scripts_check_primitive_hybrid_search__primitive_match.py_function_src_teleon_registry_primitive_match__hybrid_search(
            py_local_scripts_check_primitive_hybrid_search__self_test__unrelated_request,
            [py_local_scripts_check_primitive_hybrid_search__self_test__unrelated_candidate],
        )
    )
    py_local_scripts_check_primitive_hybrid_search__self_test__batch_request = {
        "intent": "normalize many rate rows",
        "labels": ["rate", "normalize"],
        "input_contract": {"shape": "sequence", "fields": {"row": "object"}},
        "output_contract": {"shape": "object", "fields": {"record": "object"}},
    }
    py_local_scripts_check_primitive_hybrid_search__self_test__scalar_candidate = {
        "id": "primitive.rate.normalize_one",
        "name": "Normalize one rate row",
        "purpose": "Normalize one interest rate row.",
        "labels": ["rate", "normalize"],
        "input_contract": {"shape": "scalar", "fields": {"row": "object"}},
        "output_contract": {"shape": "object", "fields": {"record": "object"}},
    }
    py_local_scripts_check_primitive_hybrid_search__self_test__batch_hit = (
        py_var_scripts_check_primitive_hybrid_search__primitive_match.py_function_src_teleon_registry_primitive_match__hybrid_search(
            py_local_scripts_check_primitive_hybrid_search__self_test__batch_request,
            [py_local_scripts_check_primitive_hybrid_search__self_test__scalar_candidate],
        )[0]
    )
    py_local_scripts_check_primitive_hybrid_search__self_test__profile = (
        py_var_scripts_check_primitive_hybrid_search__primitive_match.py_function_src_teleon_registry_primitive_match__blocking_profile(
            py_local_scripts_check_primitive_hybrid_search__self_test__scalar_candidate
        )
    )
    py_local_scripts_check_primitive_hybrid_search__self_test__index = (
        py_var_scripts_check_primitive_hybrid_search__primitive_match.py_function_src_teleon_registry_primitive_match__blocking_index(
            [py_local_scripts_check_primitive_hybrid_search__self_test__scalar_candidate]
        )
    )
    py_function_scripts_check_primitive_hybrid_search___self_test__check(
        "unrelated primitive does not enter the graph assembly candidate set",
        not py_local_scripts_check_primitive_hybrid_search__self_test__unrelated_hits,
    )
    py_function_scripts_check_primitive_hybrid_search___self_test__check(
        "deterministic adapter hit exposes required result fields and adapter plan",
        py_const_scripts_check_primitive_hybrid_search__REQUIRED_RESULT_FIELDS <= set(py_local_scripts_check_primitive_hybrid_search__self_test__batch_hit)
        and py_local_scripts_check_primitive_hybrid_search__self_test__batch_hit["graph_assembly_status"] == "chainable_with_adapter_nodes"
        and any(node["node_kind"] == "normalize_to_sequence_then_map" for node in py_local_scripts_check_primitive_hybrid_search__self_test__batch_hit["adapter_plan"]),
    )
    py_function_scripts_check_primitive_hybrid_search___self_test__check(
        "blocking profile carries efficient exact/keyword/label/contract/graph/semantic/mutation keys",
        set(py_var_scripts_check_primitive_hybrid_search__primitive_match.py_const_src_teleon_registry_primitive_match__BLOCK_PROFILE_FIELDS)
        <= set(py_local_scripts_check_primitive_hybrid_search__self_test__profile),
    )
    py_function_scripts_check_primitive_hybrid_search___self_test__check(
        "blocking index carries reusable inverted retrieval keys and hit evidence",
        py_const_scripts_check_primitive_hybrid_search__REQUIRED_BLOCKING_INDEX_FIELDS
        <= set(py_local_scripts_check_primitive_hybrid_search__self_test__index)
        and py_local_scripts_check_primitive_hybrid_search__self_test__index["serves_truth"] is False
        and py_local_scripts_check_primitive_hybrid_search__self_test__batch_hit["blocking_index"]["match_count"] >= 1,
    )

    if py_local_scripts_check_primitive_hybrid_search__self_test__failures:
        print(f"\nFAIL - check_primitive_hybrid_search: {len(py_local_scripts_check_primitive_hybrid_search__self_test__failures)} failure(s)")
        return 1
    print("\nPASS - check_primitive_hybrid_search: hybrid primitive search/mutation contracts are governed")
    return 0


def py_function_scripts_check_primitive_hybrid_search__main():
    return py_function_scripts_check_primitive_hybrid_search___self_test()


if __name__ == "__main__":
    raise SystemExit(py_function_scripts_check_primitive_hybrid_search__main())
