#!/usr/bin/env python3
"""check_synthesis_discipline — disciplined prompts, per-step data tracking, and dead-end ESCAPE are real.

Owner: templated processes that keep the frontier LLM from jumping down too fast (enumerate-before-commit, deterministic-
before-model, test-before-descend, troubleshoot-before-backtrack, track-data); plus logic to SPROUT / break out / try
something new when no branch solves. Proves: the prompt-template library carries those discipline rules + a troubleshooting
ladder; frontier_prompts embeds them; the synthesis TRACE records per-step data (choice/alternatives/test/cost/confidence
+ deterministic ratio + 'jumped without alternatives'); the STRATEGIST escapes a dead-end (sprout) + is honest when it
can't + the registry-driven defaults produce real expanded plans. serves_truth=false.

  python3 scripts/check_synthesis_discipline.py --self-test
"""
from __future__ import annotations

import json
from pathlib import Path

from src.teleon.synthesis import intent_to_dag as I
from src.teleon.synthesis.strategist import default_strategies, resilient_synthesize
from src.teleon.synthesis.synthesis_trace import SynthesisTrace
from src.teleon.synthesis.synthesis_tree import Attempt, SynthesisTree

REPO = Path(__file__).resolve().parents[1]


def _self_test() -> int:
    tmpl = json.loads((REPO / "architecture" / "synthesis_prompt_templates.json").read_text(encoding="utf-8"))
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    # ── discipline + templates ────────────────────────────────────────────────────────────────────────────────
    rules = {d["rule"] for d in tmpl["discipline"]}
    need = {"enumerate_before_commit", "deterministic_before_model", "dont_jump_down_too_fast", "test_before_descend",
            "troubleshoot_before_backtrack", "track_data_every_step", "exhaust_before_unavailable"}
    ck("discipline carries the anti-premature-commitment rules", need <= rules, str(need - rules))
    stages = {s["stage"] for s in tmpl["stages"]}
    ck("5 stages templated", stages == {"outline", "fill", "dag_test", "verify", "alternatives"}, str(stages))
    ck("every stage has prompt + must + avoid + track", all(s.get("prompt") and s.get("must") and s.get("avoid") and s.get("track") for s in tmpl["stages"]))
    fill = next(s for s in tmpl["stages"] if s["stage"] == "fill")
    ck("fill stage forbids picking a model when a deterministic tool exists",
       any("model" in a and ("parser" in a or "classifier" in a or "solver" in a) for a in fill["avoid"]))
    tl = tmpl["troubleshooting_ladder"]
    ck("troubleshooting ladder is ordered", [t["step"] for t in tl] == sorted(t["step"] for t in tl))
    acts = {t["action"] for t in tl}
    ck("troubleshooting ladder: classify -> try_alternative -> backtrack -> honest_unavailable",
       {"classify", "try_alternative", "backtrack", "honest_unavailable"} <= acts, str(acts))

    fp = I.frontier_prompts("extract fields from these invoices into our schema")
    ck("frontier_prompts embeds must/avoid/track + discipline",
       all(p.get("must") and p.get("track") and "Discipline in force" in p["prompt"] for p in fp))

    # ── per-step DATA TRACKING (trace) ────────────────────────────────────────────────────────────────────────
    pts = [("A", ["a1", "a2"]), ("B", ["b1", "b2"])]
    def tester(path, partial):
        ids = [f"{d.id}={d.choice}" for d in path]
        if partial:
            return Attempt("A=a1" not in ids, "broke" if "A=a1" in ids else "ok", cost=0.001, confidence=0.9)
        return Attempt(ids == ["A=a2", "B=b2"], "assembly", cost=0.01, confidence=0.8)
    tree = SynthesisTree(); tree.synthesize(pts, tester)
    tr = SynthesisTrace.from_tree(tree, intent="toy")
    s = tr.summary()
    ck("trace records a step per explored node", s["steps"] >= 4)
    ck("trace tracks cost (summed)", s["total_cost"] > 0)
    ck("trace computes a deterministic ratio", 0.0 <= s["deterministic_ratio"] <= 1.0)
    ck("trace records alternatives + test + confidence per step",
       all(("alternatives_considered" in vars(st)) and (st.test_ok is not None) for st in tr.steps))
    ck("trace flags 'jumped without alternatives' (exploration health)", "jumped_without_alternatives" in s["exploration"])
    ck("trace persists as JSONL", bool(tr.to_jsonl()) and all(json.loads(l) for l in tr.to_jsonl().splitlines()))

    # ── ESCAPE: sprout/reframe/try-something-new when the tree dead-ends ──────────────────────────────────────
    base = [("A", ["a1"]), ("B", ["b1"])]
    def t2(path, partial):
        ids = [f"{d.id}={d.choice}" for d in path]
        return Attempt(True) if partial else Attempt(ids == ["A=a1", "B=b2"])   # needs b2, NOT in base -> must sprout
    sol, strat, attempts = resilient_synthesize(base, t2, intent="toy", strategies=[("sprout_b2", lambda h: [("A", ["a1"]), ("B", ["b1", "b2"])])])
    ck("escapes a dead-end by sprouting a new branch", sol is not None and strat == "sprout_b2")
    ck("every attempt kept (lossless: base loss + sprout win)", [a.solved for a in attempts] == [False, True])
    sol2, strat2, att2 = resilient_synthesize(base, t2, intent="toy", strategies=[("noop", lambda h: None)])
    ck("honest no-solution when no strategy escapes (never fabricated)", sol2 is None and strat2 is None)

    names = [n for n, _ in default_strategies("find public statements by X and flag contradictions")]
    ck("default strategies = sprout -> external -> bundles -> reframe -> llm_novel",
       names == ["sprout_same_plane", "add_external_apis", "add_bundles", "reframe_ladder", "llm_novel"], str(names))
    strat_fns = dict(default_strategies("extract fields from these invoices into our schema"))
    sprouted = strat_fns["sprout_same_plane"]([])
    ck("sprout strategy produces a real expanded plan (more options than base)",
       bool(sprouted) and any(len(opts) > 0 for _, opts in sprouted))
    ck("serves_truth=false", tmpl.get("serves_truth") is False)

    print("\n" + ("PASS - check_synthesis_discipline: disciplined templates (no jumping down too fast) + per-step data "
                  "tracking + dead-end escape (sprout/reframe/novel), honest when exhausted." if not fails
                  else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
