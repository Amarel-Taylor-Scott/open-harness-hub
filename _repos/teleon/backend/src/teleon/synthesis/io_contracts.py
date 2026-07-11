"""io_contracts — typed I/O contracts per tool-plane (the Haystack/Langflow pre-runtime type-check, grounded in our
shared-I/O spine). Single source: _repos/shared-backend-components/architecture/plane_io_contracts.json. The compiler uses edge_compatible() to surface
DAG edges that connect incompatible types (a producer whose output type no consumer input accepts) BEFORE running —
the same guarantee Haystack gives by typing component ports. serves_truth=false (this types the flow, it doesn't judge truth).

Coverage is partial-but-grounded (the composing planes); an edge touching an UNCOVERED plane is treated as compatible
(unknown, not penalized) so the check never blocks on a plane we haven't typed yet.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from functools import lru_cache
from pathlib import Path

py_var_src_teleon_synthesis_io_contracts___CONTRACTS = _resource("architecture") / "plane_io_contracts.json"


@lru_cache(maxsize=1)
def py_function_src_teleon_synthesis_io_contracts__load_contracts() -> dict:
    return json.loads(py_var_src_teleon_synthesis_io_contracts___CONTRACTS.read_text())


def py_function_src_teleon_synthesis_io_contracts__plane_io(py_arg_src_teleon_synthesis_io_contracts__plane_io__plane: str | None) -> dict | None:
    """The {consumes, produces} contract for a plane, or None if the plane is not (yet) typed."""
    if not py_arg_src_teleon_synthesis_io_contracts__plane_io__plane:
        return None
    return py_function_src_teleon_synthesis_io_contracts__load_contracts().get("planes", {}).get(py_arg_src_teleon_synthesis_io_contracts__plane_io__plane)


def py_function_src_teleon_synthesis_io_contracts__edge_compatible(py_arg_src_teleon_synthesis_io_contracts__edge_compatible__producer_plane: str | None, py_arg_src_teleon_synthesis_io_contracts__edge_compatible__consumer_plane: str | None) -> bool:
    """True iff the producer can feed the consumer: producer.produces ∩ consumer.consumes ≠ ∅. An edge touching an
    UNCOVERED plane is compatible (unknown, never penalized). This is the pre-runtime type-check Haystack does on ports."""
    py_local_src_teleon_synthesis_io_contracts__edge_compatible__p, py_local_src_teleon_synthesis_io_contracts__edge_compatible__c = py_function_src_teleon_synthesis_io_contracts__plane_io(py_arg_src_teleon_synthesis_io_contracts__edge_compatible__producer_plane), py_function_src_teleon_synthesis_io_contracts__plane_io(py_arg_src_teleon_synthesis_io_contracts__edge_compatible__consumer_plane)
    if py_local_src_teleon_synthesis_io_contracts__edge_compatible__p is None or py_local_src_teleon_synthesis_io_contracts__edge_compatible__c is None:
        return True                                   # at least one plane isn't typed yet -> don't block
    return bool(set(py_local_src_teleon_synthesis_io_contracts__edge_compatible__p.get("produces", [])) & set(py_local_src_teleon_synthesis_io_contracts__edge_compatible__c.get("consumes", [])))
