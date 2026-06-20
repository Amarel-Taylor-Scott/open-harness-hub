#!/usr/bin/env python3
"""scripts.check_contextops_redteam — the ContextOps red-team: every attack on the invariant FAILS SAFELY.

THE INVARIANT under attack: *agents DISCOVER and PROPOSE; Baltor STORES, VERIFIES, RECONCILES, PROVES,
CONSUMES.* This proof drives each of the spec's nine attacks to the REAL guard that lives in a ContextOps
module and asserts the guard REFUSES — none can be talked around.

The nine attacks (spec §Red-team), each routed to the real module guard that stops it:

  1. a research agent PUBLISHES a fact directly        → research report serves_truth pinned False; a candidate
                                                          provider raises ResearchAgentUnavailable (never runs).
  2. a generated worker LACKS proof                    → the sandbox proof gate returns can_register=False / a
                                                          failing unit test → gate_decision='rejected'.
  3. a source candidate LACKS a source_handle          → FactAssertionCandidate raises MissingSourceHandleError.
  4. a FAQ OUTRANKS a regulation                       → reliability.outranks(faq, reg) is False; the M3
                                                          recipe REJECTS a FAQ winning_source_type.
  5. a tenant_private source updates a global_public   → reliability tenant_scope_ok is False; the
     fact                                                 tenant_private cross-source policy needs human signoff.
  6. a source recipe uses an UNAPPROVED network        → the sandbox statically BLOCKS network access; the
                                                          research stub REFUSES a secrets-bearing task.
  7. an extractor DROPS its source handle              → MissingSourceHandleError (same guard as #3, at extract).
  8. an LLM output is SERVED as truth                  → minting claim_status!='candidate' raises
                                                          CanonicalClaimError; llm_claim_requires_source_artifact
                                                          refuses an LLM claim with no backing source artifact.
  9. unverified generated code is REGISTERED as active → the proof gate's can_register is False until a unit-test
                                                          proof passes (no proof → no registration).

Deterministic, stdlib-only, offline (injected time, temp dirs created+cleaned by the sandbox gate, no network,
no RNG). No literal secret value appears in this file — where a negative test needs an api_key/sk- string it is
BUILT at runtime from fragments. CLI: PYTHONPATH=. python3 scripts/check_contextops_redteam.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.contextops.cross_source_confirmation import ConfirmedSource, confirm  # noqa: E402
from src.baltor.contextops.extractor_snippets import (  # noqa: E402
    CanonicalClaimError,
    FactAssertionCandidate,
    MissingSourceHandleError,
    extract_duration,
)
from src.baltor.contextops.reliability import outranks, score_source  # noqa: E402
from src.baltor.contextops.research_stub import (  # noqa: E402
    CandidateResearchStub,
    LocalResearchStub,
)
from src.baltor.contextops.sandbox_gate import SandboxViolation, gate_snippet, run_in_sandbox  # noqa: E402
from src.baltor.contextops.verification_recipe import build_verification_recipe  # noqa: E402
from src.baltor.ports.research_agent_provider import AGENT_SERVES_TRUTH, ResearchAgentUnavailable  # noqa: E402

_NOW = "2026-06-05T00:00:00Z"
_NOW_EPOCH = 1_780_000_000
_FACT_KEY = "reg_e.error_resolution.deadline"
_REG_HANDLE = "ctx://public/source/ecfr/12-CFR-1005.11#para.c.1.i"
_FAQ_HANDLE = "ctx://public/source/cfpb-faq/error-resolution#q12"

_REG_FACTORS = {"officialness": 1.0, "freshness": 0.95, "stability": 0.98, "machine_readability": 0.8,
                "contradiction_rate": 0.0, "availability": 0.99, "parse_stability": 0.9,
                "historical_accuracy": 1.0}
_FAQ_MAXED = {"officialness": 1.0, "freshness": 1.0, "stability": 1.0, "machine_readability": 1.0,
              "contradiction_rate": 0.0, "availability": 1.0, "parse_stability": 1.0,
              "historical_accuracy": 1.0}

_BASE_TASK = {
    "task_id": "rtask-redteam", "tenant_id": "acme", "source_scope": "global_public", "fact_key": _FACT_KEY,
    "question": "deadline?", "bounds": {"max_steps": 4, "allowed_access": ["fixture"], "offline": True,
                                        "secrets_allowed": False}, "created_at": _NOW,
}


def _ok_unit_test(_tmp: Path) -> None:
    """A passing proof: a benign extractor snippet's unit test (asserts nothing false)."""
    assert 1 + 1 == 2


def _failing_unit_test(_tmp: Path) -> None:
    """A FAILING proof — stands in for a generated worker whose test does not pass (no proof)."""
    assert False, "the generated worker's unit test does not pass"


def _self_test() -> int:
    fails: list[str] = []

    def attack(name: str, refused: bool, detail: str = "") -> None:
        print(f"  [{'BLOCKED' if refused else 'BREACH '}] {name}{(': ' + detail) if detail and not refused else ''}")
        if not refused:
            fails.append(name)

    # ── 1) a research agent PUBLISHES a fact directly ──────────────────────────────────────────────────
    report = LocalResearchStub().research(_BASE_TASK, now=_NOW)
    refused = report.get("serves_truth") is False and AGENT_SERVES_TRUTH is False
    attack("a research agent cannot publish a fact directly (report serves_truth pinned False)", refused)
    candidate_refused = False
    try:
        CandidateResearchStub("research.hermes@candidate").research(_BASE_TASK, now=_NOW)
    except ResearchAgentUnavailable as exc:
        # the refusal names the env:// credential ref, never a value, and never imports/executes the agent.
        candidate_refused = exc.credential_ref.startswith("env://") and "candidate" in str(exc)
    attack("a candidate open-ended agent never runs to publish a fact (raises ResearchAgentUnavailable, "
           "naming an env:// ref)", candidate_refused)

    # ── 2) a generated worker LACKS proof ──────────────────────────────────────────────────────────────
    benign = "def extract(payload):\n    return payload.strip()\n"
    no_proof = gate_snippet(benign, _failing_unit_test, gated_at=_NOW_EPOCH)
    attack("a generated worker with NO passing proof can never register (failing unit test → rejected)",
           no_proof.can_register is False and no_proof.gate_decision == "rejected")

    # ── 3) a source candidate LACKS a source_handle ─────────────────────────────────────────────────────
    handle_refused = False
    try:
        FactAssertionCandidate(fact_key=_FACT_KEY, extractor_type="duration_parser", value=10,
                               unit="business_days", source_handle="", scope="global_public",
                               extracted_at=_NOW_EPOCH)
    except MissingSourceHandleError:
        handle_refused = True
    attack("a candidate with NO source_handle is rejected (MissingSourceHandleError)", handle_refused)

    # ── 4) a FAQ OUTRANKS a regulation ──────────────────────────────────────────────────────────────────
    reg = score_source(candidate_id="scand-reg", source_type="regulation", factors=_REG_FACTORS,
                        scored_at=_NOW_EPOCH)
    faq_maxed = score_source(candidate_id="scand-faq", source_type="agency_faq", factors=_FAQ_MAXED,
                             scored_at=_NOW_EPOCH)
    rank_refused = outranks(faq_maxed, reg) is False and outranks(reg, faq_maxed) is True
    attack("a FAQ — even with EVERY factor maxed — cannot outrank a regulation (authority is decisive)",
           rank_refused)
    recipe_refused = False
    try:
        build_verification_recipe(
            tenant_id="acme", source_scope="global_public", fact_key=_FACT_KEY,
            input_source_recipe_ids=["srecipe-x"], extractor_id="x", winning_source_type="agency_faq",
            min_authority_rank=20, cross_source_policy="two_independent_sources_required",
            min_independent_sources=2, now=_NOW)
    except ValueError:
        recipe_refused = True
    attack("a verification recipe can never let a FAQ WIN (FAQ winning_source_type → ValueError)", recipe_refused)

    # ── 5) a tenant_private source updates a global_public fact ──────────────────────────────────────────
    priv_global = score_source(candidate_id="tdoc", source_type="tenant_document", factors=_REG_FACTORS,
                               source_scope="tenant_private", fact_scope="global_public", scored_at=_NOW_EPOCH)
    attack("a tenant_private source cannot back a GLOBAL fact (tenant_scope_ok False)",
           priv_global.tenant_scope_ok is False)
    tpriv = ConfirmedSource(source_handle="ctx://tenant/acme/policy", source_type="tenant_document",
                            scope="tenant_private", fetched_at=_NOW_EPOCH, independent_group="acme")
    no_signoff = confirm("tenant_private_requires_human_signoff", [tpriv], now=_NOW_EPOCH,
                         has_human_signoff=False)
    attack("a tenant_private source cannot auto-confirm a fact (human signoff required)",
           no_signoff.confirmed is False and no_signoff.human_signoff_required is True)

    # ── 6) a source recipe uses an UNAPPROVED network ────────────────────────────────────────────────────
    # build the forbidden network-using snippet at runtime (no literal http:// in this file's static code).
    net_snippet = "import url" + "lib.request\n" + "def extract(p):\n    return url" + "lib.request.urlopen(p)\n"
    net_blocked = False
    try:
        run_in_sandbox(net_snippet, _ok_unit_test, allow_network=False)
    except SandboxViolation:
        net_blocked = True
    attack("a recipe/snippet that reaches for an UNAPPROVED network is statically BLOCKED (SandboxViolation)",
           net_blocked)
    # the research stub REFUSES a secrets-bearing task (never accepts a task that would use a network secret).
    secret_task = dict(_BASE_TASK, bounds=dict(_BASE_TASK["bounds"], secrets_allowed=True))
    secrets_refused = False
    try:
        LocalResearchStub().research(secret_task, now=_NOW)
    except ResearchAgentUnavailable:
        secrets_refused = True
    attack("the research stub REFUSES a secrets-bearing task (no secret-backed network access)", secrets_refused)

    # ── 7) an extractor DROPS its source handle ──────────────────────────────────────────────────────────
    extract_handle_refused = False
    try:
        extract_duration("10 business days", fact_key=_FACT_KEY, source_handle="", extracted_at=_NOW_EPOCH)
    except MissingSourceHandleError:
        extract_handle_refused = True
    attack("an extractor that drops its source_handle at extract time is rejected (MissingSourceHandleError)",
           extract_handle_refused)

    # ── 8) an LLM output is SERVED as truth ──────────────────────────────────────────────────────────────
    canonical_refused = False
    try:
        FactAssertionCandidate(fact_key=_FACT_KEY, extractor_type="duration_parser", value=10,
                               unit="business_days", source_handle=_REG_HANDLE, scope="global_public",
                               extracted_at=_NOW_EPOCH, claim_status="canonical")
    except CanonicalClaimError:
        canonical_refused = True
    attack("an extractor/LLM output can never be minted as canonical/served truth (CanonicalClaimError)",
           canonical_refused)
    # an LLM-origin claim with no backing source artifact is never confirmed (the model can't be its own evidence).
    llm_only = ConfirmedSource(source_handle="ctx://llm/claim/1", source_type="secondary_summary",
                               origin="llm_claim", fetched_at=_NOW_EPOCH, independent_group="llm")
    llm_refused = confirm("llm_claim_requires_source_artifact", [llm_only], now=_NOW_EPOCH)
    attack("an LLM claim with NO backing source artifact is never confirmed (the model can't be its own "
           "evidence)", llm_refused.confirmed is False)

    # ── 9) unverified generated code is REGISTERED as an active worker ───────────────────────────────────
    # a snippet that PASSES (sandbox + proof) earns can_register; an unproven one NEVER does — so unverified
    # code can never be registered active. (Also: a high-risk passing snippet still needs human approval.)
    proven = gate_snippet(benign, _ok_unit_test, gated_at=_NOW_EPOCH)
    high_risk = gate_snippet(benign, _ok_unit_test, high_risk=True, has_human_approval=False, gated_at=_NOW_EPOCH)
    attack("only a PROVEN snippet may register (can_register True ONLY after a passing proof); the unproven "
           "one above could not",
           proven.can_register is True and no_proof.can_register is False)
    attack("a high-risk snippet, even when it passes, cannot auto-register without human approval "
           "(needs_human_approval)",
           high_risk.can_register is False and high_risk.gate_decision == "needs_human_approval")

    ok = not fails
    print(
        "\n" + ("PASS — check_contextops_redteam: all nine attacks on the invariant FAIL SAFELY against the REAL "
                "module guards — a research agent can never publish a fact (serves_truth pinned False; a "
                "candidate agent raises ResearchAgentUnavailable); a generated worker with no proof can never "
                "register; a candidate / extractor with no source_handle is rejected (MissingSourceHandleError); "
                "a FAQ can never outrank a regulation (authority decisive; the M3 recipe rejects a FAQ winner); a "
                "tenant_private source can never back a global fact or auto-confirm one; an unapproved network is "
                "statically blocked and a secrets-bearing task refused; an LLM output can never be minted "
                "canonical (CanonicalClaimError) or confirmed without a backing source artifact; and unverified "
                "generated code can never register active (no proof → no registration; high-risk needs human "
                "approval)."
                if ok else f"{len(fails)} BREACHES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Red-team: every attack on the ContextOps invariant fails safely.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
