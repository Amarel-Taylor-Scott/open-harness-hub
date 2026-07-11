#!/usr/bin/env python3
"""check_teleon_codex_lane — proof that OpenAI Codex is a first-class, governed inference LANE, selected by
objective and bounded by org policy (an alternative to the local Ollama/Gemma layers).

  * Codex is a registered provider node (model.openai.codex) on the standardized openai_compatible adapter —
    external, requires a secret, with a LOCAL_EQUIVALENT (Ollama) for governed fallback; offline / no key it
    degrades to provider_unavailable (never a fabricated call), exactly like every other governed lane.
  * Codex is one INFERENCE LANE among many (local stub, Ollama, Gemma, Mistral, frontier APIs). The objective
    layer routes among them: minimize_cost -> a free LOCAL lane; a capability priority -> Codex (highest
    capability); a generic accuracy priority -> a capable cloud lane.
  * the org guardrail policy BOUNDS the lane: an air-gapped (no_external_egress) org FORBIDS every cloud lane —
    Codex included — so inference falls back to local Ollama; a no-LLM org forbids EVERY model lane (escalate).
  * deterministic; never serves truth.

CLI: python3 _repos/shared-backend-components/scripts/check_teleon_codex_lane.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.governance import load_policy
from src.teleon.inference.adapters import resolve_adapter
from src.teleon.inference.lane_selection import forbidden_lanes, lanes, select_lane
from src.teleon.inference.oips import load_graph
from src.teleon.objectives import PRESETS, CapabilityObjective, ObjectiveError

_CODEX = "model.openai.codex@candidate"


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # Codex is a registered, governed provider node.
    node = next((n for n in load_graph()["nodes"] if n["node_id"] == _CODEX), None)
    ck("Codex is a registered provider node on the openai_compatible adapter (a real lane)",
       node is not None and node["adapter_style"] == "openai_compatible" and node["base_url"] == "https://api.openai.com/v1")
    ck("the Codex lane is governed: external, requires a secret, has a LOCAL_EQUIVALENT fallback (Ollama)",
       node and node.get("external") is True and node.get("secret_ref") and node.get("local_equivalent") == "model.ollama_local@candidate")

    # Offline / no key -> the Codex adapter is unavailable (governed fallback, never a fabricated call).
    adapter = resolve_adapter(node)
    avail, reason = adapter.available(secrets=set(), allow_network=False)
    ck("offline / no OpenAI key -> Codex degrades to provider_unavailable (never fabricated)", avail is False, reason)

    # Codex is one lane among many; the objective routes among them.
    lane_ids = {l["lane_id"] for l in lanes()}
    ck("Codex is one inference lane among local + cloud lanes", _CODEX in lane_ids and "model.ollama_local@candidate" in lane_ids)

    cost = select_lane(PRESETS["minimize_cost"])
    ck("minimize_cost routes to a FREE LOCAL lane (not Codex)", cost["chosen_lane"]["is_local"] is True and cost["chosen"] != _CODEX, cost["chosen"])

    coding = CapabilityObjective("coding-capability", {"accuracy": 0.9, "cost": 0.05, "latency": 0.05})
    cap = select_lane(coding)
    ck("a capability-first objective routes to Codex (highest-capability lane)", cap["chosen"] == _CODEX, cap["chosen"])

    acc = select_lane(PRESETS["maximize_accuracy"])
    ck("maximize_accuracy routes to a capable CLOUD lane (never the local stub)", acc["chosen_lane"]["is_local"] is False, acc["chosen"])

    # Traceable + deterministic + never truth.
    ck("lane selection is a full SelectionTrace with the chosen lane detail, never truth",
       len(cap["ranked"]) == len(lane_ids) and cap["serves_truth"] is False and cap["chosen_lane"]["lane_id"] == cap["chosen"])
    ck("lane selection is deterministic", select_lane(coding)["chosen"] == cap["chosen"])

    # ORG POLICY bounds the lane: air-gapped forbids cloud (incl Codex) -> falls back to local Ollama.
    airgapped = load_policy("air-gapped-local-llm")
    forb = forbidden_lanes(airgapped)
    ck("an air-gapped org FORBIDS every cloud lane, Codex included", _CODEX in forb and "model.openrouter.gemma_4_26b@candidate" in forb)
    ck("a local lane stays allowed under air-gapped", "model.ollama_local@candidate" not in forb)
    bounded = select_lane(coding, forbidden=forb)
    ck("under air-gapped, even a capability-first task falls back to a LOCAL lane (Codex forbidden)",
       bounded["chosen_lane"]["is_local"] is True and bounded["chosen"] != _CODEX, bounded["chosen"])

    # a no-LLM org forbids EVERY model lane -> selection fails loud (escalate, never a silent model call).
    nollm = load_policy("deterministic-audit")
    allforb = forbidden_lanes(nollm)
    ck("a no-LLM org forbids EVERY inference lane", allforb == lane_ids)
    raised = False
    try:
        select_lane(PRESETS["balanced"], forbidden=allforb)
    except ObjectiveError:
        raised = True
    ck("with every lane forbidden, lane selection fails loud (escalate to human)", raised)

    print("\n" + ("PASS - check_teleon_codex_lane: OpenAI Codex is a first-class governed inference lane (openai_"
                  "compatible node, external + secret + local Ollama fallback; offline -> provider_unavailable, "
                  "never fabricated). The objective routes among lanes — minimize_cost -> free local, a capability "
                  "priority -> Codex — and the org guardrail policy bounds it: an air-gapped org forbids cloud "
                  "(Codex falls back to local Ollama), a no-LLM org forbids every lane (escalate). Deterministic, never truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
