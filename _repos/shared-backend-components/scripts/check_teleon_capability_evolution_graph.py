#!/usr/bin/env python3
"""check_teleon_capability_evolution_graph — proof for the capability EVOLUTION graph + the descent it supports.

Walks a capability from its non-deterministic runner toward the most-deterministic one through DOCUMENTED forks,
and proves the graph is LOSSLESS and the descent is well-defined:
  * a documented fork trades capability coverage for determinism (a 100%-deterministic rule covering 90% of cases),
    the parent is PRESERVED, and the uncovered residual is ROUTED to a higher-coverage runner — never dropped.
  * lineage(runner) traces back to the single root; descent_path() is the non-det -> most-det spine.
  * most_deterministic_runner(min_coverage) is the runner Teleon runs for the covered cases (residual -> ancestor).
  * a coverage-losing fork that drops its residual, a fork that claims MORE coverage, or one that is LESS
    deterministic all FAIL LOUD (the lossless-distillation law, enforced structurally).
  * the SELF-HEALING bridge: record_heal() appends a `heal` edge so the capability's history is one shared graph
    (healing writes heal edges; evolution writes fork/distill edges) — the two concerns stay separate in LOGIC.

CLI: python3 _repos/shared-backend-components/scripts/check_teleon_capability_evolution_graph.py --self-test
"""
from __future__ import annotations

import os
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.evolution import (
    EDGE_HEAL,
    CapabilityEvolutionGraph,
    EvolutionEdge,
    EvolutionError,
    RunnerNode,
    plan_descent_to_determinism,
    record_heal,
)


def _graph() -> CapabilityEvolutionGraph:
    """A capability evolving model -> distilled rule (90% cov) -> template (60% cov), residuals routed up."""
    slot = "federal-register-rule-search"
    g = CapabilityEvolutionGraph(slot)
    g.add_runner(RunnerNode("model@v1", slot, "model", tier=2, determinism=0.2, capability_coverage=1.0, cost=0.07))
    g.document_fork("model@v1", RunnerNode("rule@v1", slot, "distilled_rule", tier=1, determinism=1.0,
                                           capability_coverage=0.9, cost=0.0),
                    rationale="distilled deterministic rule covers the 90% common citations; residual -> model")
    g.document_fork("rule@v1", RunnerNode("template@v1", slot, "template", tier=0, determinism=1.0,
                                          capability_coverage=0.6, cost=0.0),
                    rationale="exact-match template for the 60% canonical lookups; residual -> rule")
    return g


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    g = _graph()
    g.validate()

    # The single root is the non-deterministic model; lineage + descent spine walk non-det -> most-det.
    ck("the root is the non-deterministic model runner", g.root().runner_id == "model@v1")
    ck("lineage(template) traces root -> rule -> template",
       [n.runner_id for n in g.lineage("template@v1")] == ["model@v1", "rule@v1", "template@v1"])
    ck("descent_path is the non-det -> most-det spine",
       [n.runner_id for n in g.descent_path()] == ["model@v1", "rule@v1", "template@v1"])

    # Documented forks carry the trade (coverage down, determinism up); the parent is preserved.
    forks = g.forks()
    ck("two documented forks are recorded with their coverage/determinism trade",
       len(forks) == 2 and all(f["coverage_delta"] <= 0 and f["determinism_delta"] >= 0 for f in forks), str(forks))
    ck("the model parent is PRESERVED after forking (lossless — never replaced)", "model@v1" in g._nodes)
    ck("each coverage-losing fork routes its residual to a preserved higher-coverage runner",
       all(f["residual_routed_to"] in g._nodes for f in forks)
       and g.node(forks[0]["residual_routed_to"]).capability_coverage >= g.node(forks[0]["to"]).capability_coverage)

    # most_deterministic_runner: the most-deterministic runner meeting the coverage bar.
    ck("most_deterministic_runner(min_coverage=0.9) -> the distilled rule (det 1.0, covers 0.9)",
       g.most_deterministic_runner(min_coverage=0.9).runner_id == "rule@v1")
    ck("most_deterministic_runner(min_coverage=0.99) -> falls back to the model (only it covers ~all)",
       g.most_deterministic_runner(min_coverage=0.99).runner_id == "model@v1")

    # plan_descent_to_determinism ties it together (the proactive descent plan).
    plan = plan_descent_to_determinism(g, min_coverage=0.9)
    ck("plan_descent_to_determinism picks the rule, is fully deterministic, and never serves truth",
       plan["chosen_runner"] == "rule@v1" and plan["fully_deterministic"] is True and plan["serves_truth"] is False
       and plan["descent_spine"] == ["model@v1", "rule@v1", "template@v1"])

    # LOSSLESS enforcement — each violation fails loud.
    def raises(fn):
        try:
            fn()
            return False
        except EvolutionError:
            return True

    slot = "federal-register-rule-search"

    def drop_residual():
        bad = CapabilityEvolutionGraph(slot)
        bad.add_runner(RunnerNode("m", slot, "model", 2, 0.2, 1.0, 0.07))
        # residual routed to a runner that covers LESS than the fork itself -> residual dropped
        bad.add_runner(RunnerNode("low", slot, "template", 0, 1.0, 0.3, 0.0))
        bad.add_runner(RunnerNode("r", slot, "distilled_rule", 1, 1.0, 0.9, 0.0))
        bad.add_edge(EvolutionEdge("m", "r", "fork", "bad", residual_routed_to="low"))

    def gain_coverage():
        bad = CapabilityEvolutionGraph(slot)
        bad.add_runner(RunnerNode("m", slot, "model", 2, 0.2, 0.8, 0.07))
        bad.document_fork("m", RunnerNode("r", slot, "distilled_rule", 1, 1.0, 0.95, 0.0))  # 0.95 > 0.8

    def less_deterministic():
        bad = CapabilityEvolutionGraph(slot)
        bad.add_runner(RunnerNode("m", slot, "model", 2, 0.9, 1.0, 0.07))
        bad.document_fork("m", RunnerNode("r", slot, "distilled_rule", 1, 0.5, 0.9, 0.0))  # 0.5 < 0.9

    ck("a coverage-losing fork that DROPS its residual fails loud", raises(drop_residual))
    ck("a fork claiming MORE coverage than its parent fails loud", raises(gain_coverage))
    ck("a 'descent' that is LESS deterministic fails loud", raises(less_deterministic))
    ck("a node that tries to serve truth fails loud",
       raises(lambda: RunnerNode("x", slot, "model", 2, 0.2, 1.0, 0.0, serves_truth=True)))

    # SELF-HEALING bridge: a heal appends a heal-edge into the SAME lineage (separate concern, shared graph).
    healed = record_heal(g, drifted_runner_id="rule@v1",
                         healed_runner=RunnerNode("rule@v2", slot, "distilled_rule", 1, 1.0, 0.9, 0.0),
                         rationale="source API moved; re-healed the rule to re-pass its benchmark")
    g.validate()
    heal_edges = [e for e in g._edges if e.kind == EDGE_HEAL]
    ck("record_heal appends a heal edge (self-healing writes into the shared lineage)",
       len(heal_edges) == 1 and heal_edges[0].parent_id == "rule@v1" and healed.runner_id == "rule@v2")
    ck("the healed runner traces its lineage through the graph",
       [n.runner_id for n in g.lineage("rule@v2")] == ["model@v1", "rule@v1", "rule@v2"])

    # to_dict round-trips and never serves truth.
    d = g.to_dict()
    ck("to_dict serializes the whole graph and never serves truth",
       d["root"] == "model@v1" and d["serves_truth"] is False and len(d["runners"]) == 4 and len(d["forks"]) == 2)

    print("\n" + ("PASS - check_teleon_capability_evolution_graph: a capability evolves non-deterministic -> "
                  "most-deterministic through DOCUMENTED forks (coverage traded for determinism, parent preserved, "
                  "residual routed to a richer runner — never dropped); lineage + descent_path walk the spine; "
                  "most_deterministic_runner gives the runner to run within a coverage bar; lossless violations "
                  "fail loud; and the self-healing bridge writes heal edges into the same shared graph."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
