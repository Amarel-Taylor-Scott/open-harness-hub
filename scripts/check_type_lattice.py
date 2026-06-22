#!/usr/bin/env python3
"""check_type_lattice — System 6: subtyping lattice + coercion graph (the representation-agnostic seam).

Proves: subtyping widens composition (jpeg <: image; an image-consumer accepts a jpeg, not vice-versa); coercion_path
finds the shortest converter sequence (html→markdown) and is honest (None) when nothing bridges; bridge() returns [] when
already compatible; and the verifier surfaces COERCIBLE incompatible edges (a converter can be auto-inserted). serves_truth=false.

  python3 scripts/check_type_lattice.py --self-test
"""
from __future__ import annotations

from src.teleon.synthesis.dag_contract import verify_buildable_dag
from src.teleon.synthesis.type_system import bridge, coercion_path, is_subtype, types_compatible


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    # subtyping
    ck("subtyping: jpeg <: image (and reflexive)", is_subtype("jpeg", "image") and is_subtype("text", "text"))
    ck("subtyping is directional: image is NOT a jpeg", not is_subtype("image", "jpeg"))
    ck("a producer of a SUBTYPE satisfies a consumer of the SUPERTYPE (jpeg→image ok; image→jpeg not)",
       types_compatible({"jpeg"}, {"image"}) and not types_compatible({"image"}, {"jpeg"}))
    ck("unrelated types stay incompatible (audio↛text)", not types_compatible({"audio"}, {"text"}))

    # coercion
    ck("coercion_path finds the shortest converter (html→markdown = [html_to_markdown])", coercion_path("html", "markdown") == ["html_to_markdown"])
    ck("coercion_path prefers the direct converter (html→text = [html_strip])", coercion_path("html", "text") == ["html_strip"])
    ck("coercion_path is honest when nothing bridges (audio→record = None)", coercion_path("audio", "record") is None)
    ck("bridge: [] when already compatible; converter list when coercible; None when impossible",
       bridge({"text"}, {"text"}) == [] and bridge({"table"}, {"record"}) == ["table_to_records"] and bridge({"audio"}, {"record"}) is None)

    # verifier surfaces a COERCIBLE incompatible edge: parsing_grammar (produces record/code) -> embedding (consumes text)
    v = verify_buildable_dag([{"step": "x", "plane": "parsing_grammar"}, {"step": "y", "plane": "embedding"}], [["x", "y"]])
    ck("verifier flags the edge type-incompatible (strict)", ["x", "y"] in v["type_incompatible_edges"])
    ck("...AND surfaces it as COERCIBLE (a converter can be auto-inserted)",
       any(c["edge"] == ["x", "y"] and c["via"] for c in v["coercible_edges"]), str(v.get("coercible_edges")))

    print("\n" + ("PASS - check_type_lattice: subtyping widens composition + a coercion graph auto-bridges types (the "
                  "compiler inserts converters); honest when nothing bridges." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
