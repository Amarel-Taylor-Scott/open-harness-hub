#!/usr/bin/env python3
"""scripts.check_contextops_cross_source_confirmation — proof (CONTEXTOPS CROSS-SOURCE MODE): the six
confirmation policies are evaluated deterministically over a candidate's backing sources, and the
invariant-bearing policies hold.

What it proves:
  * single_official_source_ok — one official source-of-record confirms a regulation fact; no official → not confirmed;
  * two_independent_sources_required — two INDEPENDENT sources confirm; two reads of the same publisher do NOT;
  * official_source_plus_secondary_confirmation — needs an official source AND an independent secondary;
  * current_value_requires_fresh_source — a current/rate/fee value needs a FRESH read; a stale read is NOT confirmed
    (negative-tested); a non-current value is fine with a stored source;
  * tenant_private_requires_human_signoff — a tenant_private source can NEVER auto-confirm; without signoff it is
    NOT confirmed (human_signoff_required=True); WITH signoff it confirms (negative + positive tested);
  * llm_claim_requires_source_artifact — an LLM-origin claim with NO backing source artifact is NEVER confirmed
    (the model can't be its own evidence); backed by a stored source it confirms (negative-tested);
  * a ConfirmationResult never serves truth (served_as_truth pinned False); an unknown policy is an explicit error.

Deterministic, stdlib-only, offline (freshness uses injected `now` + each source's fetched_at).
CLI: PYTHONPATH=. python3 scripts/check_contextops_cross_source_confirmation.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.contextops.cross_source_confirmation import (  # noqa: E402
    POLICIES,
    ConfirmedSource,
    CrossSourceError,
    confirm,
)

_NOW = 1_700_000_000  # injected epoch seconds
_DAY = 86400


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    reg = ConfirmedSource(source_handle="ctx://public/source/ecfr/12-CFR-1005.11", source_type="regulation",
                          fetched_at=_NOW, independent_group="ecfr")
    faq = ConfirmedSource(source_handle="ctx://public/source/cfpb-faq/errors", source_type="agency_faq",
                          fetched_at=_NOW, independent_group="cfpb-web")
    second_indep = ConfirmedSource(source_handle="ctx://public/source/state-ag/reg-e", source_type="official_agency",
                                   fetched_at=_NOW, independent_group="state-ag")

    # ── single_official_source_ok ──
    r = confirm("single_official_source_ok", [reg], now=_NOW)
    check("single_official_source_ok: one official regulation source CONFIRMS", r.confirmed is True)
    check("single_official_source_ok: cites the confirming handle", reg.source_handle in r.confirming_handles)
    r = confirm("single_official_source_ok", [faq], now=_NOW)
    check("single_official_source_ok: a FAQ alone (not official-rank) does NOT confirm", r.confirmed is False)

    # ── two_independent_sources_required ──
    r = confirm("two_independent_sources_required", [reg, second_indep], now=_NOW)
    check("two_independent_sources_required: two INDEPENDENT sources CONFIRM", r.confirmed is True)
    same_pub = ConfirmedSource(source_handle="ctx://public/source/ecfr/mirror", source_type="regulation",
                               fetched_at=_NOW, independent_group="ecfr")  # SAME group as reg
    r = confirm("two_independent_sources_required", [reg, same_pub], now=_NOW)
    check("two_independent_sources_required: two reads of the SAME publisher do NOT confirm (not independent)",
          r.confirmed is False)

    # ── official_source_plus_secondary_confirmation ──
    r = confirm("official_source_plus_secondary_confirmation", [reg, second_indep], now=_NOW)
    check("official+secondary: an official source AND an independent secondary CONFIRM", r.confirmed is True)
    r = confirm("official_source_plus_secondary_confirmation", [reg], now=_NOW)
    check("official+secondary: an official source ALONE does NOT confirm (needs a secondary)", r.confirmed is False)

    # ── current_value_requires_fresh_source (negative-tested) ──
    fresh = ConfirmedSource(source_handle="ctx://public/source/rate/today", source_type="official_agency",
                            fetched_at=_NOW - 60, independent_group="agency")  # 60s old
    stale = ConfirmedSource(source_handle="ctx://public/source/rate/old", source_type="official_agency",
                            fetched_at=_NOW - 90 * _DAY, independent_group="agency")  # 90 days old
    r = confirm("current_value_requires_fresh_source", [fresh], now=_NOW, is_current_value=True,
                max_staleness_seconds=_DAY)
    check("current_value: a FRESH read (<= max staleness) CONFIRMS a current value", r.confirmed is True)
    r = confirm("current_value_requires_fresh_source", [stale], now=_NOW, is_current_value=True,
                max_staleness_seconds=_DAY)
    check("current_value: a STALE read does NOT confirm a current value (negative-tested)", r.confirmed is False)
    r = confirm("current_value_requires_fresh_source", [stale], now=_NOW, is_current_value=False,
                max_staleness_seconds=_DAY)
    check("current_value: a NON-current value is fine with a stored source", r.confirmed is True)

    # ── tenant_private_requires_human_signoff (negative + positive) ──
    tpriv = ConfirmedSource(source_handle="ctx://tenant/acme/source/policy", source_type="tenant_document",
                            scope="tenant_private", fetched_at=_NOW, independent_group="acme")
    r = confirm("tenant_private_requires_human_signoff", [tpriv], now=_NOW, has_human_signoff=False)
    check("tenant_private: WITHOUT human signoff a tenant_private source does NOT auto-confirm (negative-tested)",
          r.confirmed is False)
    check("tenant_private: the result flags human_signoff_required=True", r.human_signoff_required is True)
    r = confirm("tenant_private_requires_human_signoff", [tpriv], now=_NOW, has_human_signoff=True)
    check("tenant_private: WITH human signoff the tenant_private source confirms", r.confirmed is True)

    # ── llm_claim_requires_source_artifact (negative-tested) ──
    llm_only = ConfirmedSource(source_handle="ctx://llm/claim/1", source_type="secondary_summary",
                               origin="llm_claim", fetched_at=_NOW, independent_group="llm")
    r = confirm("llm_claim_requires_source_artifact", [llm_only], now=_NOW)
    check("llm_claim: an LLM claim with NO backing source artifact is NEVER confirmed (negative-tested)",
          r.confirmed is False)
    r = confirm("llm_claim_requires_source_artifact", [llm_only, reg], now=_NOW)
    check("llm_claim: an LLM claim BACKED by a stored source artifact confirms", r.confirmed is True)
    check("llm_claim: the confirming handle is the SOURCE ARTIFACT, not the llm claim",
          reg.source_handle in r.confirming_handles and "ctx://llm/claim/1" not in r.confirming_handles)

    # ── a handle-less / llm-origin source never counts as evidence under ANY policy. ──
    nohandle = ConfirmedSource(source_handle="", source_type="regulation", fetched_at=_NOW)
    r = confirm("single_official_source_ok", [nohandle], now=_NOW)
    check("a source with NO handle never confirms (it can't be cited)", r.confirmed is False)

    # ── invariant: a ConfirmationResult never serves truth; unknown policy is an explicit error. ──
    check("every ConfirmationResult pins served_as_truth False",
          confirm("single_official_source_ok", [reg], now=_NOW).served_as_truth is False)
    bad = False
    try:
        confirm("trust_me_bro", [reg], now=_NOW)
    except CrossSourceError:
        bad = True
    check("an unknown confirmation policy is an explicit CrossSourceError (never a silent pass)", bad)
    check("the six policies are exactly the documented set", set(POLICIES) == {
        "single_official_source_ok", "two_independent_sources_required",
        "official_source_plus_secondary_confirmation", "tenant_private_requires_human_signoff",
        "llm_claim_requires_source_artifact", "current_value_requires_fresh_source"})

    # ── determinism: same inputs → same result. ──
    a = confirm("two_independent_sources_required", [reg, second_indep], now=_NOW).to_dict()
    b = confirm("two_independent_sources_required", [second_indep, reg], now=_NOW).to_dict()  # order-insensitive
    check("confirmation is deterministic + order-insensitive (same sources → same result)",
          a["confirmed"] == b["confirmed"] and sorted(a["confirming_handles"]) == sorted(b["confirming_handles"]))

    ok = not fails
    print(
        f"\n{'PASS — check_contextops_cross_source_confirmation: the six policies evaluate deterministically over the backing sources of a candidate; one official source confirms a regulation, two-independent rejects same-publisher reads, official+secondary needs both, a CURRENT value needs a FRESH read (stale REJECTED), a tenant_private source can NEVER auto-confirm without human signoff, and an LLM claim with no backing source artifact is NEVER confirmed (the model cannot be its own evidence); a handle-less source never confirms; results never serve truth; an unknown policy is an explicit error.' if ok else f'{len(fails)} FAILURES: {fails}'}"
    )
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: ContextOps cross-source confirmation policies (deterministic).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
