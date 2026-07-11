"""src.teleon.components — the uniform Component standardization layer.

A single thin wrapper that normalizes every bespoke port (llm.complete / embedding.embed / reranker.rank / search.search
/ ocr.extract / ...) behind ONE shape: ``Component.invoke(typed_inputs: dict) -> typed_outputs: dict``, keyed by the
plane's typed I/O contract. This is what makes components glue-free swappable AND lets a compiled DAG actually RUN on
real ports (the abstract spec is LOWERED to the executable pipeline_dag via this wrapper). serves_truth=false.

  from src.teleon.components import make_component, register_component_invoker, lower_to_dag, run_compiled, assert_conforms
"""
from src.teleon.components.conformance import py_const_src_teleon_components_conformance__SYNTHETIC_INPUTS, py_function_src_teleon_components_conformance__assert_conforms
from src.teleon.components.lowering import py_function_src_teleon_components_lowering__lower_to_dag, py_function_src_teleon_components_lowering__run_compiled
from src.teleon.components.registry import (py_class_src_teleon_components_registry__Component, py_class_src_teleon_components_registry__ComponentUnavailable, py_function_src_teleon_components_registry__available_invokers, py_function_src_teleon_components_registry__make_component,
                                            py_function_src_teleon_components_registry__register_component_invoker)

__all__ = ["py_class_src_teleon_components_registry__Component", "py_class_src_teleon_components_registry__ComponentUnavailable", "py_function_src_teleon_components_registry__make_component", "py_function_src_teleon_components_registry__register_component_invoker", "py_function_src_teleon_components_registry__available_invokers",
           "py_function_src_teleon_components_lowering__lower_to_dag", "py_function_src_teleon_components_lowering__run_compiled", "py_function_src_teleon_components_conformance__assert_conforms", "py_const_src_teleon_components_conformance__SYNTHETIC_INPUTS"]
