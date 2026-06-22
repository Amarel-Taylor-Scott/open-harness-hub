"""conformance — the single gate every component/adapter must pass to be swappable: invoked with synthetic inputs for
its declared CONSUMED types, it must either (a) return a dict whose keys include >=1 declared PRODUCED type, or (b) raise
ComponentUnavailable honestly (a wired-but-offline lane). Anything else — wrong output shape, an undeclared output, a
silent None — is non-conformant. This makes "swap a component in" gated by PROOF it honors its port's I/O contract.
serves_truth=false.
"""
from __future__ import annotations

from src.teleon.components.registry import Component, ComponentUnavailable

# one synthetic value per type in the vocabulary (enough to exercise an invoker offline + deterministically)
SYNTHETIC_INPUTS: dict = {
    "bytes": b"%PDF-1.4 sample", "image": "/tmp/sample.png", "audio": "/tmp/sample.wav", "document": "/tmp/sample.pdf",
    "text": "sample text for the component", "text_chunks": ["chunk one", "chunk two"], "table": [["h1", "h2"], ["a", "b"]],
    "record": {"field": "value"}, "fields": {"a": 1}, "entities": [{"name": "ACME", "type": "ORG"}],
    "vector": [0.1, 0.2, 0.3, 0.4], "query": "what is the revenue", "ranked_docs": ["doc a", "doc b", "doc c"],
    "sources": [{"url": "https://example.gov/x", "title": "t"}], "html": "<html><body>hi</body></html>",
    "statement_pair": ("the sky is blue", "the sky is green"), "features": [1.0, 2.0, 3.0], "label": "POSITIVE",
    "series": [1.0, 2.0, 3.0, 4.0], "forecast": [5.0, 6.0], "diff": {"added": [], "removed": []},
    "validated_record": {"ok": True}, "code": "def f(): return 1",
}


def assert_conforms(component: Component) -> dict:
    """Verdict: {component, conformant, reason}. A non-conformant adapter must NOT be swapped in."""
    inputs = {t: SYNTHETIC_INPUTS.get(t, f"<{t}>") for t in component.consumes}
    try:
        out = component.invoke(inputs)
    except ComponentUnavailable as e:
        return {"component": component.id, "plane": component.plane, "conformant": True, "reason": f"honest-unavailable: {e}"}
    if not isinstance(out, dict):
        return {"component": component.id, "plane": component.plane, "conformant": False,
                "reason": f"output is {type(out).__name__}, not a typed-output dict"}
    produced = set(out) & set(component.produces)
    return {"component": component.id, "plane": component.plane, "conformant": bool(produced),
            "reason": (f"produced declared type(s) {sorted(produced)}" if produced
                       else f"output keys {sorted(out)} include no declared produced type {list(component.produces)}")}
