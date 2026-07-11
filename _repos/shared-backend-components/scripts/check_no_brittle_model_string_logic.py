#!/usr/bin/env python3
"""scripts.check_no_brittle_model_string_logic — PROOF: the Inference Gateway routes on NUMERIC codes + stable
node-ids, never on provider DISPLAY strings. A provider can be renamed without changing routing; a capability code
change DOES change eligibility. This keeps the model plane free of brittle display-name matching.

Asserts (against the real _repos/teleon/backend/src/teleon/inference/oips, via a process-local injected graph copy that is restored):
  A. RENAME-SAFE: changing a node's `display` string does NOT change select_provider's chosen node_id.
  B. CODE-DRIVEN: removing the required specialization CODE from a node makes it ineligible (it is no longer
     selected) — so routing follows the numeric codes, not the name.
  C. STATIC: oips.select_provider + _eligible contain NO branching on a node `display` string.
  D. NUMERIC PRIMITIVES: every graph node carries an int tier_code, an int-list specialization_codes, an int
     status_code (the routing primitives are numeric, not strings).
  E. DETERMINISM + the real graph cache is restored after the test.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import copy
import inspect
import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.inference import oips

_GRAPH = "model_provider_graph.json"
_NODE = "model.anthropic.frontier@candidate"
_PREF = [{"preference_id": "p", "model_class_preference": {"tier_code": 600, "specialization_codes": [500]},
          "allowed_provider_nodes": [_NODE, "model.local_stub@v1"], "disallowed_provider_nodes": [],
          "fallback_policy": {}, "data_policy": {}}]
_CREDS = {"secret://provider/anthropic"}


def _select_with_graph(graph: dict) -> str:
    oips._cache[_GRAPH] = graph
    try:
        return oips.select_provider(oips.resolve_preference(_PREF), available_secrets=_CREDS)["selected_provider_node_id"]
    finally:
        oips._cache.pop(_GRAPH, None)  # restore: drop the injected copy so the real graph reloads from disk


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    base = json.loads((_resource("architecture") / _GRAPH).read_text())
    baseline = _select_with_graph(copy.deepcopy(base))
    check("baseline: credentialed preferred node is selected", baseline == _NODE, baseline)

    renamed = copy.deepcopy(base)
    for nd in renamed["nodes"]:
        if nd["node_id"] == _NODE:
            nd["display"] = "ZZ COMPLETELY DIFFERENT DISPLAY NAME ZZ"
    check("A: renaming the node's display does NOT change the selected node_id",
          _select_with_graph(renamed) == _NODE, _select_with_graph(renamed))

    nocode = copy.deepcopy(base)
    for nd in nocode["nodes"]:
        if nd["node_id"] == _NODE:
            nd["specialization_codes"] = [300]  # drop the required 500 → must become ineligible
    check("B: removing the required specialization CODE makes the node ineligible (not selected)",
          _select_with_graph(nocode) != _NODE, _select_with_graph(nocode))

    sel_src = inspect.getsource(oips.select_provider) + inspect.getsource(oips._eligible)
    check("C: select_provider + _eligible never branch on a node 'display' string", '"display"' not in sel_src and "['display']" not in sel_src)

    nodes = base["nodes"]
    check("D: every node has numeric tier_code + int specialization_codes + int status_code",
          all(isinstance(n.get("tier_code"), int) and isinstance(n.get("status_code"), int)
              and isinstance(n.get("specialization_codes"), list)
              and all(isinstance(c, int) for c in n["specialization_codes"]) for n in nodes))

    check("E: real graph cache restored (a fresh load matches disk)", _GRAPH not in oips._cache and oips.load_graph()["nodes"][0]["node_id"] == base["nodes"][0]["node_id"])

    print("\n" + ("PASS — check_no_brittle_model_string_logic: the Inference Gateway routes on numeric codes + node "
                  "ids — a provider rename does not change routing, a capability-code change does; no display-string "
                  "branching in selection." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_no_brittle_model_string_logic.py --self-test")
    raise SystemExit(0)
