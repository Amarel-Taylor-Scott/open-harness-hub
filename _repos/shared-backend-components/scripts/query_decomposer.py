"""scripts.query_decomposer — split a messy natural-language dev-task into SEMANTIC COMPONENTS so each is
retrieved on its own, then fuse. A multi-capability prompt ("scrape the site, dedupe the rows, and store
clean records") is three capabilities the flat query buries; decomposing it recovers a primitive per
component that whole-query retrieval misses. And a CONSTRAINT ("keeping the public api unchanged") is NOT a
capability — separating it stops the constraint words from polluting the match.

This is the "break it up into components then hand the components (with retrieved context) to the main LLM"
front of the product loop — done DETERMINISTIC-FIRST (free, fast, the default) with an LLM ESCALATION lane
(``decompose_fn`` seam) for prompts the deterministic split cannot cleanly cut. The multi-path law: the
deterministic path is ACTIVE_DEFAULT; the LLM lane is an opt-in row, not a replacement.

Deterministic decomposition (no model call):
  1. STRIP CONSTRAINTS — trailing "keeping/without/and add tests …" clauses become ``constraints``, not
     capability components (single-source constraint markers).
  2. CLAUSE SPLIT — split the remainder on coordinators (and / then / , / -> / ; / after / before) into
     ordered clauses.
  3. TYPE each clause — its operation/datatype facets + significant keyphrases (primitive_descriptor) so a
     component carries WHAT KIND it is, not just words.
  4. ORDER — clause order is the candidate wiring order (feeds straight into wiring_language A >> B >> C).

serves_truth=false — a decomposition is a candidate plan, never truth.

    PYTHONPATH=. python3 scripts/query_decomposer.py --self-test
    PYTHONPATH=. python3 scripts/query_decomposer.py --decompose "scrape the site, dedupe rows, store records"
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

from scripts import primitive_descriptor as _desc  # noqa: E402  REUSE: operation/datatype/keyphrase facets
from scripts import robust_query_grains as _grains  # noqa: E402  REUSE: char-trigram fuzzy match (variant-robust)

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_FUZZY_OP_FLOOR = 0.45  # char-trigram Jaccard for a clause token to fuzzy-map to an operation verb
                        # ("dedupe"->"dedup", "validat"->"validate", "dedupe"->"dedup"@0.50) — variant-robustness the exact
                        # lexicon lacks; below this it stays unmapped (no spurious operation)


def _robust_operations(clause: str) -> frozenset[str]:
    """Operation facets of a clause, EXACT first then char-trigram fuzzy — so common variants the
    OPERATION_LEXICON misses ('dedupe' vs 'dedup') still resolve. Never invents an op below the floor."""
    qc = {"title": clause, "blackbox": clause, "input_edge": "", "output_edge": ""}
    ops = set(_desc.operations(qc))  # exact lexicon hits, UNIONed with the fuzzy variants below
    words = [w for w in re.findall(r"[a-z]+", clause.lower()) if len(w) >= 4]
    for op, variants in _desc.OPERATION_LEXICON.items():
        for w in words:
            if any(_grains._jaccard(_grains._char_ngrams(w), _grains._char_ngrams(v)) >= _FUZZY_OP_FLOOR
                   for v in variants):
                ops.add(op)
                break
    return frozenset(ops)

#: clauses that MODIFY rather than add capability — stripped to `constraints`, single-source. A clause
#: beginning with one of these markers is a constraint, not a component.
_CONSTRAINT_MARKERS: tuple[str, ...] = (
    "keeping", "without", "and add tests", "and make it", "so that", "so it", "while keeping",
    "but keep", "ensuring", "and prove", "and ensure", "without adding", "without breaking",
)
#: coordinators that separate ordered capability clauses (the wiring order). Longest-first so "->" and
#: multi-word markers match before single chars.
_COORDINATORS: tuple[str, ...] = ("->", "→", ";", " then ", " and then ", ", and ", " after ", " before ",
                                  " and ", ",")
_MIN_CLAUSE_CHARS = 3


def strip_constraints(query: str) -> tuple[str, list[str]]:
    """Split off trailing constraint clauses (not capabilities). Returns (capability_text, constraints)."""
    text = str(query).strip()
    constraints: list[str] = []
    lowered = text.lower()
    # find the earliest constraint marker; everything from it onward is a constraint tail
    cut = len(text)
    for marker in _CONSTRAINT_MARKERS:
        idx = lowered.find(marker)
        if idx != -1:
            cut = min(cut, idx)
    if cut < len(text):
        tail = text[cut:].strip(" ,.;")
        # the tail may itself be several constraints joined by ", and" / " and "
        for part in re.split(r",\s*and\s+|\s+and\s+|,\s*", tail):
            part = part.strip()
            if len(part) >= _MIN_CLAUSE_CHARS:
                constraints.append(part)
        text = text[:cut].strip(" ,.;")
    return text, constraints


def _split_clauses(text: str) -> list[str]:
    """Split capability text into ordered clauses on any coordinator (longest coordinator first)."""
    parts = [text]
    for coord in _COORDINATORS:
        nxt: list[str] = []
        for p in parts:
            nxt.extend(p.split(coord))
        parts = nxt
    return [c.strip(" ,.;") for c in parts if len(c.strip(" ,.;")) >= _MIN_CLAUSE_CHARS]


def _type_clause(clause: str, index: int) -> dict[str, Any]:
    """A clause typed by its facets — WHAT KIND of capability it is, not just its words."""
    qc = {"title": clause, "blackbox": clause, "input_edge": "", "output_edge": ""}
    return {"index": index, "text": clause,
            "operations": sorted(_robust_operations(clause)),
            "datatypes": sorted(_desc.datatypes(qc)),
            "keyphrases": sorted(_desc.keyphrases(qc)),
            "impact_class": _desc.impact_class(qc), **BOUNDARY}


def decompose(query: str, *, decompose_fn: Optional[Callable[[str], list[str]]] = None) -> dict[str, Any]:
    """Decompose a dev-task query into ordered, typed capability COMPONENTS + separated constraints.

    ``decompose_fn`` is the LLM ESCALATION seam: ``fn(capability_text) -> [clause, ...]``. It is used ONLY
    when the deterministic clause split yields a single clause that STILL carries multiple operation facets
    (a compound the coordinators could not cut, e.g. "build a resilient deduplicating importer") — the one
    case a model splits better than punctuation. The deterministic path is the ACTIVE_DEFAULT; the LLM lane
    never runs on an already-clean split. Escalation output is re-typed by the same deterministic facets, so
    the model only proposes CUTS, never types (it can't fabricate a capability kind)."""
    capability_text, constraints = strip_constraints(query)
    clauses = _split_clauses(capability_text)
    escalated = False
    if decompose_fn is not None and len(clauses) == 1:
        qc = {"title": clauses[0], "blackbox": clauses[0], "input_edge": "", "output_edge": ""}
        if len(_robust_operations(clauses[0])) >= 2:  # a single clause with >=2 operations = a compound worth escalating
            try:
                model_clauses = [c.strip() for c in decompose_fn(clauses[0]) if c and c.strip()]
            except Exception:  # noqa: BLE001 — the LLM lane never crashes decomposition; fall back to deterministic
                model_clauses = []
            if len(model_clauses) > 1:
                clauses = model_clauses
                escalated = True
    components = [_type_clause(c, i) for i, c in enumerate(clauses)]
    return {"record_type": "query_decomposition", "query": query,
            "capability_text": capability_text, "constraints": constraints,
            "components": components, "component_count": len(components),
            "wiring_order": [c["text"] for c in components],  # feeds wiring_language A >> B >> C
            "path": "deterministic_llm_escalated" if escalated else "deterministic_clause_split", **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    # (a) multi-capability prompt -> ordered components (the wiring order)
    d = decompose("scrape the site, dedupe the rows, and store clean records")
    checks.append(("a multi-capability prompt splits into ordered components", d["component_count"] == 3))
    checks.append(("component order is the wiring order",
                   d["wiring_order"] == ["scrape the site", "dedupe the rows", "store clean records"]))
    checks.append(("each component is TYPED by facets (dedupe -> dedup operation)",
                   "dedup" in d["components"][1]["operations"]))

    # (b) constraints are SEPARATED from capabilities
    c = decompose("add retry logic to the importer, keeping the public api unchanged and add tests that prove it")
    checks.append(("constraints are stripped, not treated as capabilities",
                   any("public api" in x for x in c["constraints"])
                   and all("public api" not in comp["text"] for comp in c["components"])))
    checks.append(("the capability survives constraint stripping",
                   c["components"] and "retry" in c["components"][0]["text"]))

    # (c) arrow/edge syntax splits too (the wiring-language input shape)
    a = decompose("RawRecord -> NormalizedRecord -> DedupedRecord")
    checks.append(("arrow syntax decomposes into the edge chain", a["component_count"] == 3))

    # (d) LLM ESCALATION seam: a single compound clause with >=2 operations escalates; a clean split does not
    esc = decompose("build a resilient deduplicating normalizer",
                    decompose_fn=lambda t: ["deduplicate the records", "normalize the records"])
    checks.append(("a compound single clause escalates to the LLM lane and re-types deterministically",
                   esc["path"] == "deterministic_llm_escalated" and esc["component_count"] == 2
                   and "dedup" in esc["components"][0]["operations"]))
    clean = decompose("scrape the site, dedupe the rows",
                      decompose_fn=lambda t: ["THIS SHOULD NEVER RUN"])
    checks.append(("an already-clean split NEVER calls the LLM lane (deterministic default)",
                   clean["path"] == "deterministic_clause_split"
                   and all("NEVER" not in comp["text"] for comp in clean["components"])))
    # the LLM lane crashing degrades to deterministic, never crashes
    crash = decompose("build a resilient deduplicating normalizer",
                      decompose_fn=lambda t: (_ for _ in ()).throw(RuntimeError("model down")))
    checks.append(("an LLM-lane crash degrades to the deterministic single clause (never crashes)",
                   crash["component_count"] == 1 and crash["path"] == "deterministic_clause_split"))

    # (e) determinism + governance
    checks.append(("determinism (byte-identical twice)",
                   json.dumps(decompose("scrape, dedupe, store"), sort_keys=True)
                   == json.dumps(decompose("scrape, dedupe, store"), sort_keys=True)))
    checks.append(("decomposition + components are candidate/serves_truth=false",
                   d["serves_truth"] is False and all(x["serves_truth"] is False for x in d["components"])))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - query_decomposer: split a messy dev-task into ordered TYPED capability components + "
          "separated constraints, DETERMINISTIC-FIRST (clause split on coordinators, facet-typed) with an "
          "opt-in LLM ESCALATION lane for compound single clauses (model proposes CUTS only, deterministic "
          "re-types; a clean split never calls it, a crash degrades gracefully). Feeds wiring_language "
          "A >> B >> C. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--decompose", metavar="QUERY", default=None, help="decompose one query (deterministic)")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.decompose:
        print(json.dumps(decompose(args.decompose), indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
