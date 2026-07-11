"""conformance — the single gate every component/adapter must pass to be swappable: invoked with synthetic inputs for
its declared CONSUMED types, it must either (a) return a dict whose keys include >=1 declared PRODUCED type, or (b) raise
ComponentUnavailable honestly (a wired-but-offline lane). Anything else — wrong output shape, an undeclared output, a
silent None — is non-conformant. This makes "swap a component in" gated by PROOF it honors its port's I/O contract.
serves_truth=false.
"""
from __future__ import annotations

from src.teleon.components.registry import py_class_src_teleon_components_registry__Component, py_class_src_teleon_components_registry__ComponentUnavailable

# one synthetic value per type in the vocabulary (enough to exercise an invoker offline + deterministically)
py_const_src_teleon_components_conformance__SYNTHETIC_INPUTS: dict = {
    "bytes": b"%PDF-1.4 sample", "image": "/tmp/sample.png", "audio": "/tmp/sample.wav", "document": "/tmp/sample.pdf",
    "text": "sample text for the component", "text_chunks": ["chunk one", "chunk two"], "table": [["h1", "h2"], ["a", "b"]],
    "record": {"field": "value"}, "fields": {"a": 1}, "entities": [{"name": "ACME", "type": "ORG"}],
    "vector": [0.1, 0.2, 0.3, 0.4], "query": "what is the revenue", "ranked_docs": ["doc a", "doc b", "doc c"],
    "sources": [{"url": "https://example.gov/x", "title": "t"}], "html": "<html><body>hi</body></html>",
    "statement_pair": ("the sky is blue", "the sky is green"), "features": [1.0, 2.0, 3.0], "label": "POSITIVE",
    "series": [1.0, 2.0, 3.0, 4.0], "forecast": [5.0, 6.0], "diff": {"added": [], "removed": []},
    "validated_record": {"ok": True}, "code": "def f(): return 1",
}


def py_function_src_teleon_components_conformance__assert_conforms(py_arg_src_teleon_components_conformance__py_function_src_teleon_components_conformance__assert_conforms__component: py_class_src_teleon_components_registry__Component) -> dict:
    """Verdict: {component, conformant, reason}. A non-conformant adapter must NOT be swapped in."""
    py_local_src_teleon_components_conformance__assert_conforms__inputs = {t: py_const_src_teleon_components_conformance__SYNTHETIC_INPUTS.get(t, f"<{t}>") for t in py_arg_src_teleon_components_conformance__py_function_src_teleon_components_conformance__assert_conforms__component.consumes}
    try:
        py_local_src_teleon_components_conformance__assert_conforms__out = py_arg_src_teleon_components_conformance__py_function_src_teleon_components_conformance__assert_conforms__component.invoke(py_local_src_teleon_components_conformance__assert_conforms__inputs)
    except py_class_src_teleon_components_registry__ComponentUnavailable as py_local_src_teleon_components_conformance__assert_conforms__e:
        return {"component": py_arg_src_teleon_components_conformance__py_function_src_teleon_components_conformance__assert_conforms__component.id, "plane": py_arg_src_teleon_components_conformance__py_function_src_teleon_components_conformance__assert_conforms__component.plane, "conformant": True, "reason": f"honest-unavailable: {py_local_src_teleon_components_conformance__assert_conforms__e}"}
    if not isinstance(py_local_src_teleon_components_conformance__assert_conforms__out, dict):
        return {"component": py_arg_src_teleon_components_conformance__py_function_src_teleon_components_conformance__assert_conforms__component.id, "plane": py_arg_src_teleon_components_conformance__py_function_src_teleon_components_conformance__assert_conforms__component.plane, "conformant": False,
                "reason": f"output is {type(py_local_src_teleon_components_conformance__assert_conforms__out).__name__}, not a typed-output dict"}
    py_local_src_teleon_components_conformance__assert_conforms__produced = set(py_local_src_teleon_components_conformance__assert_conforms__out) & set(py_arg_src_teleon_components_conformance__py_function_src_teleon_components_conformance__assert_conforms__component.produces)
    return {"component": py_arg_src_teleon_components_conformance__py_function_src_teleon_components_conformance__assert_conforms__component.id, "plane": py_arg_src_teleon_components_conformance__py_function_src_teleon_components_conformance__assert_conforms__component.plane, "conformant": bool(py_local_src_teleon_components_conformance__assert_conforms__produced),
            "reason": (f"produced declared type(s) {sorted(py_local_src_teleon_components_conformance__assert_conforms__produced)}" if py_local_src_teleon_components_conformance__assert_conforms__produced
                       else f"output keys {sorted(py_local_src_teleon_components_conformance__assert_conforms__out)} include no declared produced type {list(py_arg_src_teleon_components_conformance__py_function_src_teleon_components_conformance__assert_conforms__component.produces)}")}
