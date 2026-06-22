"""src.teleon.components — the uniform Component standardization layer.

A single thin wrapper that normalizes every bespoke port (llm.complete / embedding.embed / reranker.rank / search.search
/ ocr.extract / ...) behind ONE shape: ``Component.invoke(typed_inputs: dict) -> typed_outputs: dict``, keyed by the
plane's typed I/O contract. This is what makes components glue-free swappable AND lets a compiled DAG actually RUN on
real ports (the abstract spec is LOWERED to the executable pipeline_dag via this wrapper). serves_truth=false.

  from src.teleon.components import make_component, register_component_invoker, lower_to_dag, run_compiled, assert_conforms
"""
from src.teleon.components.conformance import SYNTHETIC_INPUTS, assert_conforms
from src.teleon.components.lowering import lower_to_dag, run_compiled
from src.teleon.components.registry import (Component, ComponentUnavailable, available_invokers, make_component,
                                            register_component_invoker)

__all__ = ["Component", "ComponentUnavailable", "make_component", "register_component_invoker", "available_invokers",
           "lower_to_dag", "run_compiled", "assert_conforms", "SYNTHETIC_INPUTS"]
