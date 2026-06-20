#!/usr/bin/env python3
"""scripts.check_verification_gate — proof (C40): the Verification Gate is a real blocking gate between
Enhancement and Optimization. It ALLOWS a verified source-grounded fact, and HOLDS OUT an unverified
allegation, a conclusion without support, an artifact missing source handles, an unresolved-conflict
artifact, a stale fragile fact (unless a verification task is queued), a tenant-private artifact aimed at the
global scope, and a model-dependent artifact without processor metadata — each with a schema-valid receipt
that explains the decision. The gate reads governance from the artifact-type registry and never mutates
canonical truth. Deterministic + offline (time injected; receipt ids content-addressed).

Covers the owner's seven named scenarios: allows_verified_fact, blocks_unverified_allegation,
blocks_unresolved_conflict, blocks_stale_fragile_fact, requires_source_handles, requires_conclusion_support,
receipt. CLI: python3 scripts/check_verification_gate.py --self-test
"""
from __future__ import annotations

import argparse
from pathlib import Path

from scripts.runtime.schema_validator import validate_ref
from scripts.runtime.verification_gate import VerificationGate

NOW = 1_000_000  # injected clock (epoch seconds) — no wall-clock anywhere
GLOBAL = "global_public"


def _fact(**over) -> dict:
    """A verified, source-grounded Reg E fact (the canonical 'allow' case)."""
    base = {"artifact_id": "fact-rege-10", "artifact_type": "atomic_fact",
            "source_handle": "ctx://cfpb/reg-e#error_resolution.deadline", "content_hash": "h-rege-10",
            "claim_status": "fact", "promotion_eligible": True, "scope": GLOBAL}
    base.update(over)
    return base


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    g = VerificationGate()

    def ev(art, **ctx):
        ctx.setdefault("now", NOW)
        ctx.setdefault("requested_scope", GLOBAL)
        return g.evaluate(art, context=ctx, now="2026-06-05T00:00:00Z")

    # 1) allows a verified, source-grounded canonical fact
    r = ev(_fact())
    check("allows a verified source-grounded fact (Reg E 10 business days)", r["decision"].decision == "allow", str(r["decision"].reasons))

    # 2) blocks an unverified allegation (correctly held out, no violation), and FLAGS a misrepresented one
    alleg = {"artifact_id": "alleg-1", "artifact_type": "narrative_allegation",
             "source_handle": "ctx://cfpb/complaint/1#narrative.s1", "content_hash": "h-a1", "promotion_eligible": False}
    ra = ev(alleg)
    check("holds out a narrative allegation (not promotable as fact)", ra["decision"].decision == "hold_out" and ra["report"].ok, str(ra["decision"].reasons))
    bad_alleg = dict(alleg); bad_alleg["promotion_eligible"] = True
    rb = ev(bad_alleg)
    check("FLAGS an allegation that misrepresents itself as promotion-eligible (blocking violation)",
          rb["decision"].decision == "hold_out" and any(c.name == "allegation_not_promoted_as_fact" and not c.passed for c in rb["report"].checks))

    # 3) blocks an unresolved/held-out conflict; the reconciled WINNER still passes (Reg E 10 wins, FAQ 30 held out)
    faq30 = _fact(artifact_id="fact-faq-30", source_handle="ctx://cfpb/faq#deadline", content_hash="h-faq-30")
    r_loser = ev(faq30, held_out_ids={"fact-faq-30"})
    check("holds out the reconciliation LOSER (FAQ 30 days)", r_loser["decision"].decision == "hold_out"
          and any(c.name == "conflict_absent_or_reconciled" and not c.passed for c in r_loser["report"].checks))
    r_winner = ev(_fact(), held_out_ids={"fact-faq-30"}, winners={"c1": "fact-rege-10"})
    check("allows the reconciliation WINNER (Reg E 10) when the loser is held out", r_winner["decision"].decision == "allow")
    r_open = ev(_fact(), open_conflict_ids={"fact-rege-10"})
    check("holds out an artifact in an UNRESOLVED (open) conflict", r_open["decision"].decision == "hold_out")

    # 4) blocks a stale fragile fact unless a verification task is queued
    stale = _fact(fragility={"volatility_class": "high", "next_verify_at": NOW - 1})
    r_stale = ev(stale)
    check("holds out a STALE fragile fact with no queued verification", r_stale["decision"].decision == "hold_out"
          and any(c.name == "fragile_fact_current_or_queued" and not c.passed for c in r_stale["report"].checks))
    r_queued = ev(stale, pending_verification_ids={"fact-rege-10"})
    check("allows a stale fragile fact once a verification task is QUEUED", r_queued["decision"].decision == "allow")
    fresh = _fact(fragility={"volatility_class": "high", "next_verify_at": NOW + 86400})
    check("allows a fresh fragile fact (within horizon)", ev(fresh)["decision"].decision == "allow")

    # 5) requires source handles on a source-grounded artifact
    no_handle = _fact(); no_handle.pop("source_handle")
    r_nh = ev(no_handle)
    check("holds out a source-grounded fact with NO source handle", r_nh["decision"].decision == "hold_out"
          and any(c.name == "source_handles_present" and not c.passed for c in r_nh["report"].checks))
    no_hash = _fact(content_hash="")
    check("holds out an artifact with NO content hash", ev(no_hash)["decision"].decision == "hold_out")

    # 6) requires a conclusion to cite supporting artifacts
    concl = {"artifact_id": "concl-1", "artifact_type": "conclusion", "content_hash": "h-c1"}
    r_c = ev(concl)
    check("holds out a conclusion with NO supporting artifacts", r_c["decision"].decision == "hold_out"
          and any(c.name == "conclusion_support_present" and not c.passed for c in r_c["report"].checks))
    concl_ok = dict(concl); concl_ok["supports"] = ["fact-rege-10"]
    rc2 = ev(concl_ok)
    check("a supported conclusion passes the support check (still held out: not a fact type)",
          all(c.passed for c in rc2["report"].checks if c.name == "conclusion_support_present"))

    # 7) tenant isolation + model grounding
    tpriv = _fact(artifact_id="tp-1", scope="tenant_private", source_handle="ctx://acme/policy#x", content_hash="h-tp")
    r_leak = ev(tpriv, requested_scope=GLOBAL)
    check("holds out a tenant_private artifact aimed at the GLOBAL scope (no leak)", r_leak["decision"].decision == "hold_out"
          and any(c.name == "tenant_isolation_preserved" and not c.passed for c in r_leak["report"].checks))
    r_tp_ok = ev(tpriv, requested_scope="tenant_private")
    check("tenant_private artifact promoted within its own tenant scope passes isolation",
          all(c.passed for c in r_tp_ok["report"].checks if c.name == "tenant_isolation_preserved"))
    emo = {"artifact_id": "emo-1", "artifact_type": "emotion_signal", "content_hash": "h-e1",
           "source_handle": "ctx://cfpb/complaint/1#narrative"}
    check("holds out a model-dependent artifact missing processor metadata",
          any(c.name == "model_output_grounded" and not c.passed for c in ev(emo)["report"].checks))

    # 8) receipt: schema-valid, deterministic, explanatory
    r1 = ev(_fact()); r2 = ev(_fact())
    rec = r1["receipt"].to_dict()
    check("receipt validates against VerificationReceipt.v1", validate_ref(rec, "artifacts/VerificationReceipt.v1") == [], str(validate_ref(rec, "artifacts/VerificationReceipt.v1")[:3]))
    check("receipt id is deterministic for identical input (content-addressed, no clock/rng)", r1["receipt"].receipt_id == r2["receipt"].receipt_id)
    check("a hold-out receipt explains WHY (non-empty reasons)", len(ev(no_handle)["receipt"].reasons) >= 1)
    check("receipt records the per-check results", len(rec["checks"]) >= 8)

    # 9) gate invariant: projection-only (no canonical mutation / no store/admin/web import)
    src = (Path(__file__).resolve().parents[1] / "scripts/runtime/verification_gate.py").read_text()
    forbidden = ["durable_store", "sqlite3", "baltor_admin_demo_server", "from web", "context_events"]
    check("the gate is projection-only (imports no store/bus/admin/web; never mutates canonical truth)",
          not any(f in src for f in forbidden), str([f for f in forbidden if f in src]))

    print(f"\n{'PASS — check_verification_gate: a real blocking Enhancement→Optimization gate (allow verified fact; hold out allegation/unresolved-conflict/stale-fragile/no-handle/unsupported-conclusion/tenant-leak/ungrounded-model) with deterministic schema-valid receipts; projection-only.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: Verification Gate v1 (Enhancement→Optimization).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
