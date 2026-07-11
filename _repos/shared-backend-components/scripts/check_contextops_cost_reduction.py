#!/usr/bin/env python3
"""scripts.check_contextops_cost_reduction — proof (CONTEXTOPS COST-LADDER MODE): the M0→M7 cost-reduction
ladder makes the economic moat visible and DETERMINISTIC.

What it proves (the spec's cost ladder: unbounded LLM cost → a bounded research ONCE → deterministic
verification FOREVER):

  * the FIRST verification of a fact is EXPENSIVE (an agent_research run — the bounded discovery, once);
  * the SECOND verification is DETERMINISTIC + CHEAP (the deterministic extractor, no LLM in the loop) —
    far cheaper than the agent research it reuses;
  * a SCHEDULED watch is NEAR-ZERO (a source-unchanged hash check), as is a cached_fact_hit;
  * ``llm_calls_avoided`` RISES with every deterministic verify / cached hit / scheduled check (each is an LLM
    call the M0 baseline would have spent and we did not);
  * ``cost_reduction_estimate`` > 0 the moment a single deterministic verify replaces an M0 LLM call, and rises
    as more cheap events amortize the one-time research;
  * the metrics are an OBSERVATION, never a served fact (serves_truth pinned False);
  * determinism: same events + same now → byte-identical metrics + a content-addressed ladder id;
  * an unknown event kind is an explicit error (never a silently-dropped cost).

Deterministic, stdlib-only, offline (token costs are injected named constants; no pricing API, no clock, no RNG).
CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_contextops_cost_reduction.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.contextops.cost_tracking import (  # noqa: E402
    AGENT_RESEARCH,
    CACHED_FACT_HIT,
    DETERMINISTIC_VERIFY,
    SCHEDULED_HASHCHECK,
    SOURCE_FETCH,
    CostEvent,
    CostTrackingError,
    cfpb_reference_lifecycle,
    compute_cost_ladder,
)

_NOW = "2026-06-05T00:00:00Z"
_FK = "reg_e.error_resolution.deadline"


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # ── per-event cost shape: research expensive, deterministic cheap, scheduled/cached near-zero. ──
    research = CostEvent(AGENT_RESEARCH, _FK).token_cost
    deterministic = CostEvent(DETERMINISTIC_VERIFY, _FK).token_cost
    scheduled = CostEvent(SCHEDULED_HASHCHECK, _FK).token_cost
    cached = CostEvent(CACHED_FACT_HIT, _FK).token_cost
    check("the FIRST verification (agent_research) is EXPENSIVE", research >= 1000, str(research))
    check("the SECOND verification (deterministic_verify) is CHEAP vs the agent research",
          deterministic * 10 < research, f"det={deterministic} research={research}")
    check("a scheduled hash-check is NEAR-ZERO (cheaper than the deterministic verify)",
          scheduled < deterministic, f"sched={scheduled} det={deterministic}")
    check("a cached_fact_hit is NEAR-ZERO", cached < deterministic, f"cached={cached} det={deterministic}")

    # ── the canonical CFPB lifecycle: research once → deterministic verify → cached hit → scheduled check. ──
    events = cfpb_reference_lifecycle(_FK, now=_NOW)
    m = compute_cost_ladder(events, now=_NOW)
    check("the ladder records exactly ONE agent_research run (research happens ONCE per fact)",
          m.agent_research_runs == 1, str(m.agent_research_runs))
    check("the ladder records the deterministic re-verification", m.deterministic_verifications == 1)
    check("the ladder records the cached fact hit + the scheduled watch run",
          m.cached_fact_hits == 1 and m.scheduled_watch_runs == 1)
    check("the ladder records the source fetch", m.source_fetches == 1)

    # ── llm_calls_avoided rises; every cheap event is an avoided M0 LLM call. ──
    check("llm_calls_avoided counts the deterministic verify + cached hit + scheduled check (3)",
          m.llm_calls_avoided == 3, str(m.llm_calls_avoided))
    check("cost_reduction_estimate > 0 (the ladder saves money vs asking the LLM every time)",
          m.cost_reduction_estimate > 0, str(m.cost_reduction_estimate))
    check("token_cost_after < token_cost_before (we spent less than the M0 baseline)",
          m.token_cost_after < m.token_cost_before, f"after={m.token_cost_after} before={m.token_cost_before}")
    check("the metrics are an OBSERVATION, never a served fact (serves_truth pinned False)",
          m.serves_truth is False)

    # ── llm_calls_avoided RISES as more cheap (deterministic/cached/scheduled) events accrue. ──
    more = events + [CostEvent(DETERMINISTIC_VERIFY, _FK, at=_NOW),
                     CostEvent(CACHED_FACT_HIT, _FK, at=_NOW)]
    m_more = compute_cost_ladder(more, now=_NOW)
    check("llm_calls_avoided RISES as more deterministic/cached events accrue",
          m_more.llm_calls_avoided > m.llm_calls_avoided,
          f"{m_more.llm_calls_avoided} !> {m.llm_calls_avoided}")
    check("cost_reduction_estimate RISES as cheap events amortize the one-time research",
          m_more.cost_reduction_estimate > m.cost_reduction_estimate,
          f"{m_more.cost_reduction_estimate} !> {m.cost_reduction_estimate}")

    # ── the OPPOSITE extreme: the M0 world (all LLM, no deterministic path) avoids NOTHING. ──
    m0 = compute_cost_ladder([CostEvent(AGENT_RESEARCH, _FK, at=_NOW)], now=_NOW)
    check("a research-only ladder avoids NO LLM calls yet (nothing deterministic has replaced an LLM call)",
          m0.llm_calls_avoided == 0)

    # ── a long-tail of cheap verifications drives cost_per_verified_fact DOWN toward the deterministic floor. ──
    amortized = [CostEvent(AGENT_RESEARCH, _FK, at=_NOW)] + [
        CostEvent(DETERMINISTIC_VERIFY, _FK, at=_NOW) for _ in range(50)]
    m_amort = compute_cost_ladder(amortized, now=_NOW)
    one_shot = compute_cost_ladder([CostEvent(AGENT_RESEARCH, _FK, at=_NOW)], now=_NOW)
    check("cost_per_verified_fact FALLS as the one-time research amortizes over many cheap verifications",
          m_amort.cost_per_verified_fact < one_shot.cost_per_verified_fact,
          f"amortized={m_amort.cost_per_verified_fact} one_shot={one_shot.cost_per_verified_fact}")
    check("with a long deterministic tail, cost_reduction_estimate approaches the deterministic floor (>0.9)",
          m_amort.cost_reduction_estimate > 0.9, str(m_amort.cost_reduction_estimate))

    # ── determinism: same events + same now → byte-identical metrics + a stable ladder id. ──
    m2 = compute_cost_ladder(cfpb_reference_lifecycle(_FK, now=_NOW), now=_NOW)
    check("the ladder is deterministic (same events+now → byte-identical metrics)",
          json.dumps(m.to_dict(), sort_keys=True) == json.dumps(m2.to_dict(), sort_keys=True))
    check("the ladder id is content-addressed (costladder- prefix + stable hash)",
          m.ladder_id.startswith("costladder-") and m.ladder_id == m2.ladder_id)

    # ── an unknown event kind is an explicit error (never a silently-dropped cost). ──
    bad = False
    try:
        CostEvent("free_lunch", _FK)
    except CostTrackingError:
        bad = True
    check("an unknown cost event kind is an explicit CostTrackingError (never a silent zero)", bad)

    # ── the serialized metrics carry the full set of moat numbers the dashboard shows. ──
    d = m.to_dict()
    for key in ("llm_calls_avoided", "agent_research_runs", "deterministic_verifications",
                "cached_fact_hits", "source_fetches", "cost_per_verified_fact",
                "cost_reduction_estimate", "token_cost_before", "token_cost_after"):
        check(f"serialized metrics carry the moat number {key!r}", key in d)

    ok = not fails
    print(
        "\n" + ("PASS — check_contextops_cost_reduction: the M0→M7 cost ladder is deterministic and makes the "
                "moat visible — the FIRST verification is an expensive agent_research (once), the SECOND is a "
                "cheap deterministic_verify (no LLM), a scheduled watch + cached hit are near-zero; "
                "llm_calls_avoided and cost_reduction_estimate both RISE as cheap events amortize the one-time "
                "research; cost_per_verified_fact FALLS toward the deterministic floor; metrics never serve "
                "truth; the ladder id is content-addressed; and an unknown event kind is an explicit error."
                if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: the ContextOps M0→M7 cost-reduction ladder.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
