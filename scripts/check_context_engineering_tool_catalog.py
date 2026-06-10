#!/usr/bin/env python3
"""scripts.check_context_engineering_tool_catalog — proof (RESEARCH CANDIDATES, NEVER ACTIVE): the
context-engineering tool landscape (architecture/context_engineering_tool_catalog.json) is GOVERNED
by the candidate≠active / discovery≠trust / output≠truth law and the lossless-distillation law.

Asserts the governance shape that keeps these tools a due-diligence landscape rather than an adopted runtime:

  * The catalog loads as JSON and carries >=18 tools across exactly the 5 declared layers.
  * Every tool has all required fields (no silent gaps).
  * Every tool is status=="candidate" (0 active) and do_not_adopt_as_runtime is true.
  * Every tool's layer is one of the 5 declared layer ids; every layer has >=1 tool.
  * finds_redundant_context / finds_conflicting_context are each one of {True, False, "partial"}.
  * tool_ids are unique (no duplicates that would collide on merge).
  * governance_law references the lossless law (docs/codex/lossless-distillation.md) AND the word "candidate".
  * distinct_from references the context_compression_provider_catalog (no duplication of that catalog).
  * the_gap.status starts with "baltor_owned" (the Context Auditor is OUR build, not a vendored tool).
  * No raw secret/key literals leak into the catalog (regex over the serialized JSON).

Deterministic, stdlib-only, offline (no network, no RNG, no credentials). Discovery is not trust:
the tools listed here are CANDIDATES for due-diligence, never pip-installed, never adopted as runtime.

CLI:    PYTHONPATH=. python3 scripts/check_context_engineering_tool_catalog.py --self-test
Import: from scripts.check_context_engineering_tool_catalog import main; main()  # returns 0/1
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

#: the catalog under proof (single source — used by every check below).
_CATALOG = _REPO / "architecture" / "context_engineering_tool_catalog.json"

#: the lossless law this catalog's governance must reference (governs any dedupe/supersession ideas we adopt).
_LOSSLESS_LAW_REF = "docs/codex/lossless-distillation.md"

#: the broader compression-provider catalog this one must declare itself distinct from (no duplication).
_COMPRESSION_CATALOG_NAME = "context_compression_provider_catalog"

#: the exactly-5 layer ids the landscape is organized into.
_LAYERS = {
    "token_waste_observability",
    "context_compression",
    "tool_output_isolation",
    "code_context_selection",
    "memory_rag_dedupe_conflict",
}

#: minimum number of catalogued tools (the owner's researched landscape).
_MIN_TOOLS = 18

#: every tool entry must carry all of these fields (no silent gaps at scale).
_REQUIRED_FIELDS = (
    "tool_id",
    "display_name",
    "layer",
    "repo_url",
    "license",
    "what_it_does",
    "finds_redundant_context",
    "finds_conflicting_context",
    "status",
    "maturity",
    "due_diligence",
    "maps_to_baltor",
    "do_not_adopt_as_runtime",
)

#: fields whose value may legitimately be falsy (bool False / tri-state False), so presence must be
#: tested with `in`, not truthiness — otherwise a valid `False` reads as a missing field.
_FALSY_OK_FIELDS = {"finds_redundant_context", "finds_conflicting_context", "do_not_adopt_as_runtime"}

#: the only allowed maturity values.
_MATURITIES = {"research", "emerging", "ready_substrate"}

#: the only allowed values for the redundant/conflicting flags (tri-state).
_TRISTATE = {True, False, "partial"}

#: heuristic patterns for raw secret/key literals that must NOT appear anywhere in the catalog.
_SECRET_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9]{16,}"),            # OpenAI-style secret keys
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{16,}"),     # Anthropic-style secret keys
    re.compile(r"AKIA[0-9A-Z]{16}"),               # AWS access key id
    re.compile(r"gsk_[A-Za-z0-9]{16,}"),           # Groq-style secret keys
    re.compile(r"(?i)(api[_-]?key|secret|password|bearer)\s*[:=]\s*['\"][A-Za-z0-9_\-]{12,}['\"]"),
)


def _self_test() -> int:
    fails: list[str] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    chk("catalog file exists", _CATALOG.exists(), str(_CATALOG))
    if not _CATALOG.exists():
        print("\nRESULT: FAIL (catalog missing)")
        return 1

    raw_text = _CATALOG.read_text()
    cat = json.loads(raw_text)  # JSON must load

    # ---- no raw secret/key literals anywhere in the catalog ----
    leaks = [p.pattern for p in _SECRET_PATTERNS if p.search(raw_text)]
    chk("no raw secret/key literals in catalog", not leaks, f"matched: {leaks}")

    # ---- top-level identity ----
    chk("catalog_id is context_engineering_tools", cat.get("catalog_id") == "context_engineering_tools",
        f"got {cat.get('catalog_id')!r}")
    declared_layers = list(cat.get("layers") or [])
    chk("layers declares exactly the 5 layer ids", set(declared_layers) == _LAYERS,
        f"got {sorted(set(declared_layers))}")

    # ---- governance_law: lossless law + the word "candidate" ----
    gov = (cat.get("governance_law") or "")
    chk("governance_law references the lossless law", _LOSSLESS_LAW_REF in gov)
    chk("governance_law mentions 'candidate'", "candidate" in gov.lower())

    # ---- distinct_from references the compression-provider catalog (no duplication) ----
    distinct = (cat.get("distinct_from") or "")
    chk("distinct_from references the context_compression_provider_catalog",
        _COMPRESSION_CATALOG_NAME in distinct, f"got {distinct!r}")

    # ---- the_gap is OUR (Baltor-owned) build, not a vendored tool ----
    gap = cat.get("the_gap") or {}
    gap_status = str(gap.get("status") or "")
    chk("the_gap.status starts with 'baltor_owned'", gap_status.startswith("baltor_owned"),
        f"got {gap_status!r}")

    # ---- tools: count, fields, candidate-only, layers, flags, uniqueness ----
    tools = cat.get("tools") or []
    chk(f"catalog has >={_MIN_TOOLS} tools", len(tools) >= _MIN_TOOLS, str(len(tools)))

    active = [t for t in tools if t.get("status") != "candidate"]
    chk("0 active tools (every tool status==candidate)", not active,
        f"non-candidate: {[t.get('tool_id') for t in active]}")

    ids: list[str] = []
    layers_seen: set[str] = set()
    for t in tools:
        tid = t.get("tool_id", "?")
        for f in _REQUIRED_FIELDS:
            # tri-state / bool fields may be a valid `False` — test presence, not truthiness.
            present = (f in t) if f in _FALSY_OK_FIELDS else bool(t.get(f))
            chk(f"{tid} has '{f}'", present)
        chk(f"{tid} status==candidate", t.get("status") == "candidate", str(t.get("status")))
        chk(f"{tid} do_not_adopt_as_runtime is True", t.get("do_not_adopt_as_runtime") is True)
        chk(f"{tid} layer is one of the 5", t.get("layer") in _LAYERS, str(t.get("layer")))
        chk(f"{tid} maturity in {{research,emerging,ready_substrate}}", t.get("maturity") in _MATURITIES,
            str(t.get("maturity")))
        chk(f"{tid} finds_redundant_context in {{True,False,'partial'}}",
            t.get("finds_redundant_context") in _TRISTATE, repr(t.get("finds_redundant_context")))
        chk(f"{tid} finds_conflicting_context in {{True,False,'partial'}}",
            t.get("finds_conflicting_context") in _TRISTATE, repr(t.get("finds_conflicting_context")))
        ids.append(tid)
        if t.get("layer") in _LAYERS:
            layers_seen.add(t.get("layer"))

    chk("no duplicate tool_ids", len(ids) == len(set(ids)),
        f"dupes: {sorted({i for i in ids if ids.count(i) > 1})}")
    missing_layers = _LAYERS - layers_seen
    chk("every one of the 5 layers has >=1 tool", not missing_layers, f"empty layers: {sorted(missing_layers)}")

    ok = not fails
    if ok:
        by_layer = {layer: sum(1 for t in tools if t.get("layer") == layer) for layer in sorted(_LAYERS)}
        red = sum(1 for t in tools if t.get("finds_redundant_context") in (True, "partial"))
        con = sum(1 for t in tools if t.get("finds_conflicting_context") in (True, "partial"))
        print(
            f"\nPASS — check_context_engineering_tool_catalog: {len(tools)} context-engineering tools across "
            f"{len(layers_seen)} layers {by_layer}, all status=candidate (0 active) + do_not_adopt_as_runtime, "
            f"unique ids; {red} find-redundant (true/partial), {con} find-conflicting (true/partial); "
            f"governance = candidate≠active / discovery≠trust / output≠truth, lossless-governed "
            f"(supersede≠delete), distinct from the {_COMPRESSION_CATALOG_NAME}; the_gap = Baltor-owned "
            f"Context Auditor (build in progress); no raw keys."
        )
    else:
        print(f"\nRESULT: FAIL ({len(fails)} failing check(s)): {fails}")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Check the governed context-engineering tool landscape catalog.")
    ap.add_argument("--self-test", action="store_true", help="run the offline deterministic self-test")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    # No flag: run the self-test anyway so importers / bare invocation both return a real 0/1 verdict.
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(main())
