#!/usr/bin/env python3
"""scripts.check_determinism_pattern_miner — proof: the pattern miner distills REPEATED VERIFIED decisions
into PatternCandidates, mining ONLY verified/adjudicated traces (raw/ungrounded/consensus excluded),
deterministically.

The miner is the M5 layer: it observes that the EXISTING Baltor authorities kept deciding the same thing and
proposes that repetition as a deterministic-rule candidate. It never decides truth and never deletes the
traces it distilled from (lossless link-back). This proof builds a deterministic fixture of traces — verified
CFPB reconciliation decisions (Reg E "10 business days" beats FAQ "30 days") plus raw LLM proposals,
consensus runs, an under-supported decision, and a tenant_private decision — and shows:

* **repeated verified decisions are mined** — the recurring ``reconcile:deadline_mismatch → reg-e-10bd``
  decision (support ≥ min_support) becomes ONE PatternCandidate whose ``support_trace_ids`` link back to
  EVERY supporting verified trace (lossless), with the union of source handles + receipts.
* **only VERIFIED/adjudicated traces are mined** — raw LLM proposals, consensus runs, and unverified
  traces contribute ZERO support; an adjudication record (verified) is mined alongside workflow traces.
* **support floor** — a decision seen fewer than ``min_support`` times yields NO candidate (one-offs are
  not patterns).
* **the verified reference invariant holds** — the mined CFPB candidate's decision is "Reg E 10 business
  days"; the held-out "FAQ 30 days" is NOT mined as a competing winner (it never recurs as a verified
  outcome — it was the loser).
* **tenant_private cannot create a global pattern** — a recurring tenant_private decision does NOT appear in
  the global patterns (the miner reads only through the boundary-enforcing mining_set), but DOES mine within
  that tenant's own private set.
* **deterministic** — the same fixture yields byte-identical candidate ids + ordering across two runs with
  different injected clocks.

Determinism: injected ``now``, hashlib ids, no RNG, no network/model.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_determinism_pattern_miner.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.determinism.consensus import ModelOutput, record_consensus  # noqa: E402
from src.baltor.determinism.pattern_miner import (  # noqa: E402
    DEFAULT_MIN_SUPPORT,
    PatternMinerError,
    mine_patterns,
)
from src.baltor.determinism.trace_store import GLOBAL_PUBLIC, TENANT_PRIVATE, TraceStore  # noqa: E402

_T1 = "2026-01-01T00:00:00Z"
_T2 = "2026-08-08T08:08:08Z"

_RECON_KEY = "reconcile:deadline_mismatch"
# the verified reference CFPB outcome that recurs: Reg E "10 business days" beats FAQ "30 days".
_VERIFIED_DECISION = {"winner_source": "reg-e", "winner_value": "10 business days",
                    "loser_source": "cfpb-faq", "loser_value": "30 days", "reason": "authority"}


def _build_fixture(now: str) -> TraceStore:
    """A deterministic fixture: 3 verified workflow + 1 verified adjudication of the SAME reference CFPB
    decision; plus raw LLM proposals, consensus runs, an under-supported one-off, and a tenant_private
    decision that must NOT pollute the global patterns."""
    store = TraceStore()

    # 3 verified workflow reconciliations of the reference decision (different inputs, same verified outcome).
    for i in range(3):
        store.append(
            tenant_id="acme", scope=GLOBAL_PUBLIC, trace_kind="workflow", workflow_id=f"cfpb-recon-{i}",
            step_id="resolve", decision_key=_RECON_KEY, decision=_VERIFIED_DECISION, verified=True,
            input_handles=[f"ctx://reg-e#{i}", f"ctx://faq#{i}"], output_handles=["ctx://reg-e#deadline"],
            receipt_ids=[f"recon-{i}"], now=now)

    # 1 verified ADJUDICATION record of the SAME decision (M4 human/policy label) — also mined.
    store.append(
        tenant_id="acme", scope=GLOBAL_PUBLIC, trace_kind="adjudication", workflow_id="cfpb-recon-adj",
        step_id="adjudicate", decision_key=_RECON_KEY, decision=_VERIFIED_DECISION, verified=True,
        input_handles=["ctx://reg-e#adj"], output_handles=["ctx://reg-e#deadline"],
        receipt_ids=["adj-1"], now=now)

    # RAW LLM proposals of the SAME decision — unverified evidence; must contribute ZERO support.
    for i in range(4):
        store.append(
            tenant_id="acme", scope=GLOBAL_PUBLIC, trace_kind="llm", workflow_id=f"cfpb-recon-{i}",
            step_id="propose", decision_key=_RECON_KEY, decision=_VERIFIED_DECISION, verified=False,
            model_id=f"m{i}", provider_id="p1", prompt_hash="sha256:dead", now=now)

    # CONSENSUS runs of the SAME decision — evidence, never truth; must contribute ZERO support.
    for i in range(3):
        run = record_consensus(
            tenant_id="acme", scope=GLOBAL_PUBLIC, workflow_id=f"cfpb-recon-{i}", step_id="consensus",
            decision_key=_RECON_KEY,
            outputs=[ModelOutput("m1", _VERIFIED_DECISION), ModelOutput("m2", _VERIFIED_DECISION)], now=now)
        store.append_trace(run.to_trace())

    # an UNDER-SUPPORTED one-off verified decision (a different verified outcome, seen ONCE) — no candidate.
    store.append(
        tenant_id="acme", scope=GLOBAL_PUBLIC, trace_kind="workflow", workflow_id="oneoff",
        step_id="resolve", decision_key="reconcile:field_value_mismatch",
        decision={"winner_source": "structured", "reason": "scope"}, verified=True,
        input_handles=["ctx://a#1"], output_handles=["ctx://a#current"], receipt_ids=["recon-oneoff"],
        now=now)

    # a RECURRING TENANT_PRIVATE verified decision — must NOT enter the global patterns.
    for i in range(4):
        store.append(
            tenant_id="globex", scope=TENANT_PRIVATE, trace_kind="workflow", workflow_id=f"globex-recon-{i}",
            step_id="resolve", decision_key=_RECON_KEY,
            decision={"winner_source": "globex-internal-policy", "reason": "authority"}, verified=True,
            input_handles=[f"ctx://globex#{i}"], output_handles=["ctx://globex#winner"],
            receipt_ids=[f"recon-globex-{i}"], now=now)

    return store


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    store = _build_fixture(_T1)

    # 1) the recurring VERIFIED reference decision is mined into ONE candidate (3 workflow + 1 adjudication = 4).
    patterns = mine_patterns(store, scope=GLOBAL_PUBLIC, min_support=DEFAULT_MIN_SUPPORT, now=_T1)
    reference = [p for p in patterns if p.decision_key == _RECON_KEY]
    check("the recurring verified CFPB decision is mined into exactly ONE candidate", len(reference) == 1,
          f"got {len(reference)}")
    cand = reference[0] if reference else None
    check("the candidate's support counts BOTH workflow + adjudication verified traces (4)",
          cand is not None and cand.support == 4, str(cand.support if cand else None))

    # 2) ONLY verified traces contributed — raw LLM (4) + consensus (3) were excluded.
    #    Total verified RECON traces in the fixture = 4; raw+consensus = 7; the candidate must show only 4.
    check("raw LLM proposals + consensus runs contributed ZERO support (only verified mined)",
          cand is not None and cand.support == 4 and len(cand.support_trace_ids) == 4)

    # 3) lossless link-back: every supporting trace id is real, verified, and preserved in the store.
    if cand:
        all_real = all(store.has(tid) for tid in cand.support_trace_ids)
        all_verified = all(store.get(tid).verified for tid in cand.support_trace_ids)
        check("the candidate links back to its supporting trace ids (lossless — traces preserved)", all_real)
        check("every supporting trace is a VERIFIED trace", all_verified)
        check("the candidate carries the union of source handles", "ctx://reg-e#deadline" in cand.source_handles)
        check("the candidate carries the union of receipts", "adj-1" in cand.receipt_ids and "recon-0" in cand.receipt_ids)

    # 4) the verified reference invariant — the mined decision is Reg E "10 business days"; FAQ-30 is the LOSER,
    #    never mined as a competing winner.
    if cand:
        check("the mined decision's WINNER is Reg E '10 business days'",
              cand.decision.get("winner_value") == "10 business days" and cand.decision.get("winner_source") == "reg-e")
        check("the held-out FAQ '30 days' is the LOSER in the mined decision (never a competing winner)",
              cand.decision.get("loser_value") == "30 days")
        winners_30 = [p for p in patterns if p.decision.get("winner_value") == "30 days"]
        check("NO mined candidate ever has FAQ '30 days' as the winner", winners_30 == [])

    # 5) support floor — the one-off verified decision (seen once) yields NO candidate.
    oneoffs = [p for p in patterns if p.decision_key == "reconcile:field_value_mismatch"]
    check("an under-supported one-off verified decision yields NO candidate (one-off != pattern)", oneoffs == [])

    # 6) tenant_private cannot create a global pattern — globex's recurring private decision is absent globally.
    globex_winners = [p for p in patterns if p.decision.get("winner_source") == "globex-internal-policy"]
    check("a recurring tenant_private decision does NOT appear in the GLOBAL patterns", globex_winners == [])
    # but it DOES mine within globex's own private set.
    globex_patterns = mine_patterns(store, scope=TENANT_PRIVATE, tenant="globex", min_support=3, now=_T1)
    check("the same private decision DOES mine within globex's own private set",
          any(p.decision.get("winner_source") == "globex-internal-policy" for p in globex_patterns))
    check("globex's private patterns are tenant_scoped (not promotable as global rules)",
          all(p.tenant_scoped for p in globex_patterns))
    # acme cannot mine globex's private decisions.
    acme_priv = mine_patterns(store, scope=TENANT_PRIVATE, tenant="acme", min_support=1, now=_T1)
    check("acme's private mining set never contains globex's private winner",
          not any(p.decision.get("winner_source") == "globex-internal-policy" for p in acme_priv))

    # 7) DETERMINISTIC — a second build with a DIFFERENT clock yields byte-identical candidate ids + order.
    store2 = _build_fixture(_T2)
    patterns2 = mine_patterns(store2, scope=GLOBAL_PUBLIC, min_support=DEFAULT_MIN_SUPPORT, now=_T2)
    ids1 = [p.candidate_id for p in patterns]
    ids2 = [p.candidate_id for p in patterns2]
    check("candidate ids + ordering are identical across runs (deterministic, clock-independent)", ids1 == ids2)
    if reference and patterns2:
        g2 = [p for p in patterns2 if p.decision_key == _RECON_KEY]
        check("the reference candidate id is byte-stable across runs",
              bool(g2) and g2[0].candidate_id == reference[0].candidate_id)
        check("the reference candidate content_hash is byte-stable across runs",
              bool(g2) and g2[0].content_hash == reference[0].content_hash)

    # 8) guard: min_support must be ≥1.
    bad = False
    try:
        mine_patterns(store, min_support=0)
    except PatternMinerError:
        bad = True
    check("mine_patterns rejects min_support < 1", bad)

    ok = not fails
    print(
        f"\n{'PASS — check_determinism_pattern_miner: repeated VERIFIED decisions are mined into PatternCandidates that link back losslessly to their supporting traces; only verified/adjudicated traces are mined (raw LLM + consensus contribute zero); the support floor rejects one-offs; the reference invariant holds (winner = Reg E 10 business days, FAQ-30 stays the loser, never a mined winner); tenant_private cannot create a global pattern (but mines within its own tenant); and the miner is deterministic (byte-identical ids/order across clocks).' if ok else f'{len(fails)} FAILURES: {fails}'}"
    )
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: determinism pattern miner (verified-only, lossless, tenant-safe, deterministic).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
