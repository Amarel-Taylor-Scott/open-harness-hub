#!/usr/bin/env python3
"""scripts.ingest.promote_staged — the staging→measure→gate→promote JOB (closes health≠promotion).

`_repos/shared-backend-components/scripts/ingest/feed.py` lands ingested official-source rows in STAGING — honestly tagged
"lift not yet measured (staging only)", never tenant-visible — and notes that "a downstream
measure/gate run upgrades it." This is that downstream job, which was missing: it takes staged
candidates, MEASURES bare-vs-pipeline lift (via the model route when one exists), and runs the
foundry GATE to decide PROMOTED / REVIEW / CULL. The promotion boundary is preserved:

  * a route exists (owner's Mistral/Ollama/OpenRouter keys) → real measured lift → a candidate
    that clears the floor + has provenance + a durability class is PROMOTED (stamped
    ``approval_status`` — ``pending_human`` for sensitive types, else ``auto``);
  * NO route (offline) → nothing is measured → every candidate routes to REVIEW (honest: we
    never fabricate a lift, and an unmeasured row is never promoted).

Composes the existing single-source pieces: ``model_route.measurement_stage`` (the measurer)
and ``gate.evaluate`` (the decision). No new gate logic.

CLI:
    python3 -m scripts.ingest.promote_staged --self-test
    python3 _repos/shared-backend-components/scripts/ingest/promote_staged.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _RR = str(next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2]))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.foundry.contracts import Candidate, FoundryContext, PROMOTED, REVIEW
from scripts.foundry.gate import evaluate
from scripts.foundry.model_route import from_env, measurement_stage


def promote_staged(candidates: Iterable[Candidate], *, route: Any = None,
                   lift_floor: float = 0.0, require_structural: bool = False,
                   ctx: FoundryContext | None = None) -> dict[str, Any]:
    """Measure (when a route exists) then gate each staged candidate.

    ``route`` defaults to ``model_route.from_env()`` — None offline, so nothing is measured and
    every candidate routes to REVIEW (the promotion boundary holds). Mutates each candidate's
    ``decision`` and returns the per-candidate decisions + a summary.
    """
    cands = list(candidates)
    resolved_route = route if route is not None else from_env()
    ctx = ctx or FoundryContext()
    measured = resolved_route is not None
    if measured and cands:
        # attaches a measured `lift` (bare-vs-pipeline delta) to each candidate
        measurement_stage(resolved_route).run(cands, ctx)

    decisions: list[dict[str, Any]] = []
    for c in cands:
        d = evaluate(c, lift_floor=lift_floor, require_structural=require_structural)
        c.decision = d["decision"]
        record = d.get("record") or {}
        decisions.append({
            "component_id": c.component_id or (c.gap or {}).get("id", ""),
            "decision": d["decision"],
            "approval_status": record.get("approval_status"),
            "lift_delta": (c.lift or {}).get("delta"),
            "reasons": d["reasons"],
        })
    summary = dict(Counter(d["decision"] for d in decisions))
    return {"decisions": decisions, "summary": summary, "measured": measured,
            "route": getattr(resolved_route, "name", None),
            "note": ("measured via the model route" if measured else
                     "no model route — unmeasured, all routed to REVIEW (promotion boundary held)")}


def _staged_candidate(slug: str, *, art: str) -> Candidate:
    """A staged candidate shaped like a fed official-source row (gap + source, lift unset)."""
    return Candidate(
        target_type="knowledge-pack", component_id=f"knowledge-pack/{slug}",
        body={"description": "csddd article duties", "_entries": [{"art": art}]},
        gap={"id": f"gap-{slug}", "summary": "CSDDD article-level duties",
             "mechanism": "no_addressable_source", "lift_reason": "no_addressable_source",
             "retrievability_tier": "structured_no_api",
             # the model-INDEPENDENT signal the gap screen attaches (a real fed row carries it):
             # the gap is real regardless of any model's self-assessment.
             "model_independent_score": 0.8,
             "eval_tasks": [{"prompt": f"cite article {art}", "correct_answer": f"Article {art}"},
                            {"prompt": "cite article 29", "correct_answer": "Article 29"}]},
        source={"source_url": "https://eur-lex.europa.eu/x", "author": "EU", "license": "CC-BY-4.0",
                "source_kind": "source_of_law"})


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    import os
    from scripts.foundry.model_route import _FakeRoute

    # OFFLINE (no route, env cleared): nothing measured → every staged candidate → REVIEW.
    saved = {k: os.environ.pop(k, None) for k in
             ("OLLAMA_API_KEY", "MISTRAL_API_KEY", "OPENROUTER_API_KEY", "ANTHROPIC_API_KEY", "OPENAI_API_KEY")}
    try:
        off = promote_staged([_staged_candidate("a", art="8"), _staged_candidate("b", art="11")])
        check("offline: no route → measured False", off["measured"] is False)
        check("offline: every staged candidate routes to REVIEW (never promoted unmeasured)",
              all(d["decision"] == REVIEW for d in off["decisions"]) and off["summary"].get(REVIEW) == 2,
              str(off["summary"]))
        check("offline: no fabricated lift", all(d["lift_delta"] is None for d in off["decisions"]))
    finally:
        for k, v in saved.items():
            if v is not None:
                os.environ[k] = v

    # MEASURED (a route exists): a candidate with provenance + durability + a real measured lift
    # is PROMOTED; the decision carries the measured delta + an approval_status.
    measured = promote_staged([_staged_candidate("c", art="8")], route=_FakeRoute())
    check("measured: route used → measured True", measured["measured"] is True)
    promoted = [d for d in measured["decisions"] if d["decision"] == PROMOTED]
    check("measured: a provenance+durable+lifted candidate is PROMOTED", len(promoted) == 1,
          str(measured["summary"]))
    check("measured: the promotion carries a real lift delta + approval_status",
          promoted and promoted[0]["lift_delta"] is not None and promoted[0]["approval_status"] in ("auto", "pending_human"),
          str(promoted))

    # The job is deterministic given the same route + candidates.
    a = promote_staged([_staged_candidate("d", art="8")], route=_FakeRoute())["summary"]
    b = promote_staged([_staged_candidate("d", art="8")], route=_FakeRoute())["summary"]
    check("deterministic given the same route", a == b)

    ok = not fails
    print("\n" + ("PASS — promote_staged: the staging→measure→gate job — offline routes every "
                  "unmeasured staged candidate to REVIEW (boundary held, no fabricated lift); with a "
                  "model route it measures real bare-vs-pipeline lift and PROMOTES the ones that clear "
                  "the floor with provenance + durability. Closes the health≠promotion gap."
                  if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Promote staged ingest rows via measure + gate.")
    p.add_argument("--self-test", action="store_true")
    p.parse_args(argv)
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(main())
