#!/usr/bin/env python3
"""deterministic_edge_derivation — 0-token, deterministic typed edges from a SHARED canonical vocabulary.

Owner (2026-07-11): "deterministic edges may help ... save more tokens, allow for faster." The compose zoo
measured 0 exact joins across 112K primitives because independently-minted edges never equal each other
(`FederalJobOpportunityBatch` never matches another card's edge). The fix is not smarter matching — it is
DETERMINISM: derive every edge from one canonical type vocabulary, so a thing that produces JSON bytes and a
thing that consumes JSON bytes BOTH get the edge `JsonBytes` and therefore compose EXACTLY, at 0 tokens.

Deterministic edges ⇒ exact composition ⇒ 0-token remixing (deterministic_remix), better dedup, and a
graph-exact code graph. Pure functions: no model, no network, no clock.

    python3 scripts/deterministic_edge_derivation.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts"), str(_SBC.parent.parent),
           str(_SBC.parent.parent / "_repos" / "teleon" / "backend")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts.edge_only_capability_templates import CAPABILITY_TEMPLATES  # class → canonical edges (reuse)

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
TOKEN_COST = 0

#: the CANONICAL TYPE VOCABULARY — one name per conceptual type, so any two primitives touching the same
#: type get the SAME edge component and compose exactly. Extending it is one row (the open-world guarantee).
CANONICAL_TYPES: dict[str, str] = {
    # python annotations / common shapes → canonical component
    "str": "Text", "text": "Text", "bytes": "Bytes", "int": "IntValue", "float": "FloatValue", "bool": "BoolFlag",
    "dict": "Mapping", "list": "Sequence", "tuple": "Sequence", "set": "Sequence", "none": "Unit",
    "any": "OpaqueValue", "datetime": "DateTime", "date": "DateTime", "path": "PathObject",
    "json": "JsonBytes", "csv": "CsvText", "url": "UrlString", "uuid": "Uuid", "decimal": "DecimalValue",
    "dataframe": "DataFrame", "ndarray": "NdArray", "model": "ValidatedModel", "response": "HttpResponse",
    "request": "HttpRequestSpec",
}


def _pascal(word: str) -> str:
    return "".join(p[:1].upper() + p[1:] for p in re.split(r"[^A-Za-z0-9]+", str(word)) if p)


_CANON_VALUES = set(CANONICAL_TYPES.values())


def canonical_type(hint: str) -> str:
    """Map a raw type hint to its canonical component (deterministic + IDEMPOTENT). Matching is precise:
    (1) an already-canonical value returns itself (so normalize is idempotent — 'JsonBytes' stays 'JsonBytes',
    never re-matched to 'Bytes'); (2) exact key; (3) any WORD of a multi-word hint that is a known type
    ('some_text_field' → 'text' → Text). Unknown → PascalCase (open-world: never dropped; register to align)."""
    p = _pascal(hint)
    if p in _CANON_VALUES:
        return p
    key = re.sub(r"[^a-z0-9]", "", str(hint).lower())
    if key in CANONICAL_TYPES:
        return CANONICAL_TYPES[key]
    for word in re.findall(r"[a-z0-9]+", str(hint).lower()):
        if word in CANONICAL_TYPES:
            return CANONICAL_TYPES[word]
    return p or "OpaqueValue"


def normalize_edge(raw: str) -> str:
    """Canonicalize an edge: map each '+'-component through the vocabulary, dedupe, stable order.
    Idempotent — normalize(normalize(x)) == normalize(x)."""
    comps = [canonical_type(c) for c in str(raw).split("+") if c.strip()]
    seen: list[str] = []
    for c in comps:
        if c not in seen:
            seen.append(c)
    return "+".join(seen) if seen else "OpaqueValue"


def derive_from_signature(param_types: list[str], return_type: Optional[str]) -> tuple[str, str]:
    """Derive (input_edge, output_edge) deterministically from a signature's param + return type hints."""
    in_comps: list[str] = []
    for p in param_types:
        c = canonical_type(p)
        if c not in in_comps:
            in_comps.append(c)
    input_edge = "+".join(in_comps) if in_comps else "Unit"
    output_edge = canonical_type(return_type) if return_type else "OpaqueValue"
    return input_edge, output_edge


def derive_edges(name: str, *, capability_class: Optional[str] = None,
                 param_types: Optional[list[str]] = None, return_type: Optional[str] = None,
                 raw_edges: Optional[tuple[str, str]] = None) -> dict[str, Any]:
    """One deterministic edge decision. Preference: (1) capability-class canonical template (best — shared
    vocabulary); (2) signature-derived; (3) normalize existing raw edges; (4) name-generic. Records which
    method so a consumer knows the confidence. 0-token."""
    if capability_class and capability_class in CAPABILITY_TEMPLATES:
        t = CAPABILITY_TEMPLATES[capability_class]
        return {"input_edge": normalize_edge(t["input_edge"]), "output_edge": normalize_edge(t["output_edge"]),
                "method": "class_template", "token_cost": TOKEN_COST, "exact_composable": True, **BOUNDARY}
    if param_types is not None or return_type is not None:
        ie, oe = derive_from_signature(param_types or [], return_type)
        return {"input_edge": ie, "output_edge": oe, "method": "signature",
                "token_cost": TOKEN_COST, "exact_composable": True, **BOUNDARY}
    if raw_edges:
        return {"input_edge": normalize_edge(raw_edges[0]), "output_edge": normalize_edge(raw_edges[1]),
                "method": "normalized_raw", "token_cost": TOKEN_COST, "exact_composable": True, **BOUNDARY}
    cap = _pascal(name.split(".")[0])
    return {"input_edge": f"{cap}Input", "output_edge": f"{cap}Output", "method": "name_generic",
            "token_cost": TOKEN_COST, "exact_composable": False, **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    # THE POINT: two independent primitives touching the same type get the SAME edge → exact composition
    producer = derive_edges("fetch", param_types=["str"], return_type="json")      # -> ... JsonBytes
    consumer = derive_edges("parse", param_types=["json"], return_type="dict")     # JsonBytes -> Mapping
    checks.append(("shared vocabulary makes edges EXACTLY composable (producer.out == consumer.in)",
                   producer["output_edge"] == "JsonBytes" and consumer["input_edge"] == "JsonBytes"
                   and producer["output_edge"] == consumer["input_edge"]))

    # class template gives the canonical shared edges
    ser = derive_edges("serde", capability_class="serialize")
    checks.append(("capability-class template yields canonical edges (method=class_template, 0-token)",
                   ser["method"] == "class_template" and ser["token_cost"] == 0 and ser["exact_composable"]))

    # normalization is idempotent + aligns divergent raw edges to the same canonical form
    n1 = normalize_edge("JSON+dict")
    n2 = normalize_edge(n1)
    checks.append(("normalize idempotent + aligns raw edges (JSON+dict → JsonBytes+Mapping)",
                   n1 == n2 and n1 == "JsonBytes+Mapping"))

    # two DIFFERENT raw names for the same type collapse to one canonical component (dedup win)
    checks.append(("divergent raw names for one type collapse (str/text → Text)",
                   canonical_type("str") == canonical_type("some_text_field") == "Text"))

    # signature derivation is deterministic
    checks.append(("signature derivation deterministic (byte-identical)",
                   json.dumps(derive_from_signature(["str", "int"], "bytes"))
                   == json.dumps(derive_from_signature(["str", "int"], "bytes"))))

    # unknown type is preserved (open-world), not dropped
    checks.append(("unknown type preserved as PascalCase (open-world, never dropped)",
                   canonical_type("WidgetFrobnicator") == "WidgetFrobnicator"))

    # name-generic fallback is honestly marked NOT exact-composable
    gen = derive_edges("mystery_pkg")
    checks.append(("name-generic fallback honestly marked not exact-composable",
                   gen["method"] == "name_generic" and gen["exact_composable"] is False))

    # everything is 0-token
    checks.append(("every derivation is 0-token (no model call)",
                   all(d["token_cost"] == 0 for d in (producer, consumer, ser, gen))))

    ok = all(v for _, v in checks)
    print("deterministic_edge_derivation — self-test")
    for name, v in checks:
        print(f"  [{'ok' if v else 'FAIL'}] {name}")
    print(f"  canonical vocabulary: {len(CANONICAL_TYPES)} types; producer.out={producer['output_edge']} "
          f"== consumer.in={consumer['input_edge']} (exact-composable). 0 tokens.")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


def _main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.parse_args()
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(_main())
