#!/usr/bin/env python3
"""scripts.check_lossless_distillation_redteam — RED-TEAM-AS-PROOF: every attack on the lossless law FAILS SAFELY.

The lossless law (``docs/codex/lossless-distillation.md``) is only worth anything if it cannot be DEFEATED.
This proof is adversarial: it stages each way an attacker (or a careless transform) could try to make the
system lossy, and asserts that the store / lineage / rehydration / rollback layer REJECTS it — either by
raising, or by structurally making the destructive thing impossible. A "PASS" here means *the attack
failed*; a FAIL here means a lossless invariant could be broken.

Attacks, each must FAIL SAFELY:
  1. delete raw AFTER distillation                      → the store has no delete; raw stays gettable forever
  2. overwrite the baseline with the optimized pack     → put is append-only; the baseline id still resolves
  3. drop source handles during compression             → a handle-dropping output is NOT promotable (retention)
  4. hide FAQ-30 instead of holding it out              → a "hidden" (orphaned) input fails the retention report;
                                                           a properly held-out FAQ-30 stays rehydratable
  5. delete a rejected candidate                         → rejected entries are first-class + stay queryable
  6. promote WITHOUT a rollback plan                     → RollbackPlan.of refuses a bad/absent target
  7. tenant_private → global rule / global lineage       → put_derived raises TenantBoundaryError on that edge
  8. make an old ContextResponse unreadable (rollback)   → rollback moves the pointer only; the response stays
  9. rehydrate across a tenant boundary                  → rehydrate refuses a foreign tenant

Determinism: ``--self-test``, offline, injected ``now``, hashlib ids, no RNG, no temp files needed (the store
is in-memory). PASS/FAIL lines, exit 0/1.

CLI: PYTHONPATH=. python3 scripts/check_lossless_distillation_redteam.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.distillation.lossless_store import (  # noqa: E402
    GLOBAL_PUBLIC,
    TENANT_PRIVATE,
    DistillationStoreError,
    LosslessStore,
    TenantBoundaryError,
)
from src.baltor.distillation.rehydration import RehydrationError, rehydrate  # noqa: E402
from src.baltor.distillation.retention_report import build_retention_report  # noqa: E402
from src.baltor.distillation.rollback import RollbackPlan, execute  # noqa: E402

_NOW = "2026-06-05T00:00:00Z"
_TENANT = "acme"
_OTHER = "globex"
_HANDLE = "ctx://cfpb/consumer-complaints/complaint/demo-1001#timely"
_FAQ_HANDLE = "ctx://cfpb/faq/30"
_PACK_KEY = "cfpb/pack/regE"
_RAW_BYTES = b'{"native_id":"demo-1001","timely":"Yes","faq30":"FAQ #30 superseded by Reg E 1005.11"}'


def _build(store: LosslessStore, tenant: str = _TENANT, scope: str = TENANT_PRIVATE) -> dict:
    """raw → source → fact → baseline → (FAQ-30 held out) → promoted candidate (current), all lossless."""
    raw = store.put_raw(tenant, key="cfpb/raw/demo-1001", raw_bytes=_RAW_BYTES,
                        mime_type="application/json", scope=scope, now=_NOW)
    src = store.put_source(tenant, key="cfpb/source/demo-1001", body={"native_id": "demo-1001"},
                           parent_ids=[raw.entry_id], source_handles=[_HANDLE], scope=scope,
                           transform_run_id="run-normalize-1", now=_NOW)
    fact = store.put_derived(tenant, key="cfpb/fact/demo-1001/timely",
                             body={"text": "timely response is Yes.", "field": "timely"},
                             parent_ids=[src.entry_id], source_handles=[_HANDLE], scope=scope,
                             transform_type="decompose", transform_run_id="run-decompose-1",
                             role="atomic_fact", now=_NOW)
    # FAQ-30: a conflict loser, HELD OUT (kept, rehydratable) — NOT hidden, NOT deleted.
    faq30 = store.put_derived(tenant, key="cfpb/faq/30", body={"text": "FAQ #30: old guidance.", "field": "faq30"},
                              parent_ids=[src.entry_id], source_handles=[_FAQ_HANDLE], scope=scope,
                              transform_type="decompose", transform_run_id="run-decompose-1",
                              role="held_out", receipt_ids=["recon-faq30-receipt"], now=_NOW)
    baseline = store.put_derived(tenant, key=_PACK_KEY, body={"answer": "10 business days", "v": "baseline"},
                                 parent_ids=[fact.entry_id], source_handles=[_HANDLE], scope=scope,
                                 transform_type="optimize", transform_run_id="run-opt-baseline",
                                 role="baseline", held_out_ids=[faq30.entry_id], now=_NOW)
    # a rejected candidate (kept, first-class) and the promoted winner (current pointer).
    rejected = store.put_derived(tenant, key=_PACK_KEY, body={"answer": "10 business days", "v": "rejected", "lossy": True},
                                 parent_ids=[baseline.entry_id], source_handles=[_HANDLE], scope=scope,
                                 transform_type="promote", transform_run_id="run-promote-rej",
                                 role="rejected", now=_NOW)
    candidate = store.put_derived(tenant, key=_PACK_KEY, body={"answer": "10 business days", "v": "candidate", "compressed": True},
                                  parent_ids=[baseline.entry_id], source_handles=[_HANDLE], scope=scope,
                                  transform_type="promote", transform_run_id="run-promote-1",
                                  rejected_ids=[rejected.entry_id], rollback_target_ids=[baseline.entry_id],
                                  role="winner", now=_NOW)
    # an old ContextResponse served from the baseline (must stay readable across a rollback).
    old_response = store.put_derived(tenant, key="cfpb/response/regE",
                                     body={"schema_version": "ContextResponse.v1", "answer": "10 business days"},
                                     parent_ids=[baseline.entry_id], source_handles=[_HANDLE], scope=scope,
                                     transform_type="consume", transform_run_id="run-consume-1",
                                     role="context_response", now=_NOW)
    store.set_current(_PACK_KEY, candidate.entry_id, tenant=tenant)
    return {"raw": raw, "src": src, "fact": fact, "faq30": faq30, "baseline": baseline,
            "rejected": rejected, "candidate": candidate, "old_response": old_response}


def _self_test() -> int:
    fails: list[str] = []

    def attack_fails_safely(name: str, defended: bool, detail: str = "") -> None:
        """Record an attack: ``defended`` True means the store/proof rejected it (the GOOD outcome)."""
        print(f"  [{'ok' if defended else 'FAIL'}] attack defended: {name}{(': ' + detail) if detail and not defended else ''}")
        if not defended:
            fails.append(name)

    store = LosslessStore()
    g = _build(store)

    # ── ATTACK 1: delete raw after distillation ──────────────────────────────────────────────────
    # The store exposes NO delete/remove/pop API; raw is content-addressed and append-only.
    no_delete_api = not any(hasattr(store, m) for m in ("delete", "remove", "pop", "drop", "erase", "purge"))
    raw_still_there = store.has(g["raw"].entry_id) and store.get(g["raw"].entry_id, tenant=_TENANT).layer == "raw"
    attack_fails_safely("delete raw after distillation", no_delete_api and raw_still_there,
                        f"delete_api={not no_delete_api} raw_present={raw_still_there}")

    # ── ATTACK 2: overwrite the baseline with the optimized/promoted pack ─────────────────────────
    # Re-putting under the baseline key does NOT mutate the baseline entry: put is append-only +
    # content-addressed, so a different body yields a NEW id and the baseline id keeps its old body.
    baseline_body_before = dict(store.get(g["baseline"].entry_id, tenant=_TENANT).body)
    overwrite = store.put_derived(_TENANT, key=_PACK_KEY, body={"answer": "DIFFERENT", "v": "attacker"},
                                  parent_ids=[g["baseline"].entry_id], source_handles=[_HANDLE],
                                  transform_type="promote", transform_run_id="run-attack", now=_NOW)
    baseline_unchanged = (store.get(g["baseline"].entry_id, tenant=_TENANT).body == baseline_body_before
                          and overwrite.entry_id != g["baseline"].entry_id)
    attack_fails_safely("overwrite the baseline with the optimized pack", baseline_unchanged,
                        "baseline body changed under append-only put")

    # ── ATTACK 3: drop source handles during compression ─────────────────────────────────────────
    # Model the lossy compressor's output: same fact id, handles stripped. The retention report must
    # refuse to promote it (dropped_source_handle_count > 0, coverage < 1.0).
    in_fact = {"artifact_id": "fact-1", "claim_status": "fact", "artifact_type": "atomic_fact", "source_handle": _HANDLE}
    out_fact_stripped = {"artifact_id": "fact-1", "claim_status": "fact", "artifact_type": "atomic_fact"}
    rep_dropped = build_retention_report(transform_type="optimize", inputs=[in_fact],
                                         outputs=[out_fact_stripped], served=[out_fact_stripped])
    attack_fails_safely("drop source handles during compression",
                        (not rep_dropped.safe_to_promote) and rep_dropped.dropped_source_handle_count > 0,
                        f"safe={rep_dropped.safe_to_promote} dropped={rep_dropped.dropped_source_handle_count}")

    # ── ATTACK 4: hide FAQ-30 instead of holding it out ──────────────────────────────────────────
    # "Hiding" = dropping FAQ-30 from the output WITHOUT declaring it held_out/rejected/superseded.
    # The retention report flags it as an ORPHANED (silently dropped) input → NOT safe to promote.
    in_faq = {"artifact_id": "fact-faq-30", "claim_status": "fact", "artifact_type": "atomic_fact", "source_handle": _FAQ_HANDLE}
    rep_hidden = build_retention_report(transform_type="reconcile", inputs=[in_fact, in_faq],
                                        outputs=[in_fact], served=[in_fact])  # FAQ-30 silently gone
    hidden_caught = (not rep_hidden.safe_to_promote) and "fact-faq-30" in rep_hidden.orphaned_input_ids
    # the LAWFUL alternative (held out, not hidden) keeps FAQ-30 rehydratable from the store.
    rep_held = build_retention_report(transform_type="reconcile", inputs=[in_fact, in_faq],
                                      outputs=[in_fact], served=[in_fact], held_out=[in_faq])
    faq_rehydratable = rehydrate(store, g["faq30"].entry_id, _TENANT)["artifact"]["entry_id"] == g["faq30"].entry_id
    attack_fails_safely("hide FAQ-30 instead of holding it out",
                        hidden_caught and rep_held.safe_to_promote and faq_rehydratable,
                        f"hidden_caught={hidden_caught} held_safe={rep_held.safe_to_promote} rehydr={faq_rehydratable}")

    # ── ATTACK 5: delete a rejected candidate ─────────────────────────────────────────────────────
    # Rejected entries are first-class layers, queryable + gettable forever; there is no delete.
    rejected_present = (store.has(g["rejected"].entry_id)
                        and any(e.entry_id == g["rejected"].entry_id
                                for e in store.query(tenant=_TENANT, role="rejected")))
    attack_fails_safely("delete a rejected candidate", rejected_present and no_delete_api)

    # ── ATTACK 6: promote without a rollback plan ─────────────────────────────────────────────────
    # RollbackPlan.of refuses to build a plan whose target is not a real prior version of the key —
    # so a "promotion" that can't name a reversible prior pointer cannot get a valid rollback plan.
    no_plan = False
    try:
        RollbackPlan.of(store, key=_PACK_KEY, tenant=_TENANT, to_id=g["fact"].entry_id)  # not a version of the pack key
    except DistillationStoreError:
        no_plan = True
    # a key with NO active version also yields no plan (cannot promote-without-rollback on an empty key).
    no_active = False
    try:
        RollbackPlan.of(store, key="cfpb/pack/never-existed", tenant=_TENANT, to_id=g["baseline"].entry_id)
    except DistillationStoreError:
        no_active = True
    attack_fails_safely("promote without a rollback plan", no_plan and no_active,
                        f"bad_target_caught={no_plan} no_active_caught={no_active}")

    # ── ATTACK 7: tenant_private → global rule / global lineage ───────────────────────────────────
    # A global_public derived rule may NOT pull a tenant_private parent into its lineage.
    private_parent = store.get(g["fact"].entry_id, tenant=_TENANT)  # tenant_private by construction
    leaked = False
    try:
        store.put_derived(_TENANT, key="global/rule/regE", body={"rule": "10 business days"},
                          parent_ids=[private_parent.entry_id], source_handles=[_HANDLE],
                          scope=GLOBAL_PUBLIC, transform_type="promote",
                          transform_run_id="run-leak", now=_NOW)
        leaked = True  # if we get here the boundary did NOT hold
    except TenantBoundaryError:
        leaked = False
    attack_fails_safely("tenant_private -> global rule / global lineage", not leaked,
                        "a tenant_private parent entered a global_public lineage")

    # ── ATTACK 8: make an old ContextResponse unreadable (via rollback) ───────────────────────────
    # Roll the pack back candidate→baseline; the old response (served from baseline) must stay readable,
    # AND the candidate (promoted) must NOT be deleted by the rollback.
    plan = RollbackPlan.of(store, key=_PACK_KEY, tenant=_TENANT, to_id=g["baseline"].entry_id, reason="redteam")
    receipt = execute(store, plan, now=_NOW)
    resp_after = store.get(g["old_response"].entry_id, tenant=_TENANT)
    response_readable = resp_after.body.get("schema_version") == "ContextResponse.v1"
    candidate_kept = store.has(g["candidate"].entry_id) and receipt.candidate_preserved
    attack_fails_safely("make an old ContextResponse unreadable", response_readable and candidate_kept,
                        f"readable={response_readable} candidate_kept={candidate_kept}")

    # ── ATTACK 9: rehydrate across a tenant boundary ──────────────────────────────────────────────
    other = LosslessStore()
    go = _build(other, tenant=_OTHER)
    cross = False
    try:
        rehydrate(store, g["fact"].entry_id, _OTHER)  # acme's artifact, globex caller
    except RehydrationError:
        cross = True
    # also: the store itself rejects a cross-tenant read of a foreign id.
    cross_read = False
    try:
        store.get(g["fact"].entry_id, tenant=_OTHER)
    except TenantBoundaryError:
        cross_read = True
    # isolation, not breakage: each tenant rehydrates its OWN graph fine.
    own_ok = (rehydrate(store, g["fact"].entry_id, _TENANT)["artifact"]["entry_id"] == g["fact"].entry_id
              and rehydrate(other, go["fact"].entry_id, _OTHER)["artifact"]["entry_id"] == go["fact"].entry_id)
    attack_fails_safely("rehydrate across a tenant boundary", cross and cross_read and own_ok,
                        f"rehydrate_blocked={cross} read_blocked={cross_read} own_ok={own_ok}")

    # ── determinism: the whole red-team battery is reproducible on a clean store ──────────────────
    store2 = LosslessStore()
    g2 = _build(store2)
    det = (g2["candidate"].entry_id == g["candidate"].entry_id
           and g2["faq30"].entry_id == g["faq30"].entry_id
           and execute(store2, RollbackPlan.of(store2, key=_PACK_KEY, tenant=_TENANT,
                                                to_id=g2["baseline"].entry_id, reason="redteam"),
                       now=_NOW).receipt_id == receipt.receipt_id)
    print(f"  [{'ok' if det else 'FAIL'}] the red-team battery is deterministic (ids + receipt reproducible)")
    if not det:
        fails.append("determinism")

    ok = not fails
    print("\n" + ("PASS — check_lossless_distillation_redteam: every attack on the lossless law FAILED SAFELY — "
                  "raw cannot be deleted (no delete API; append-only), the baseline cannot be overwritten "
                  "(content-addressed put), handle-dropping compression and silently-hidden FAQ-30 are refused by "
                  "the retention report (a held-out FAQ-30 stays rehydratable), rejected candidates stay queryable, "
                  "a promotion with no real rollback target is rejected, a tenant_private parent cannot enter a "
                  "global_public lineage, rollback keeps the old ContextResponse readable and the candidate alive, "
                  "and cross-tenant rehydration is blocked — all deterministically."
                  if ok else f"{len(fails)} ATTACKS NOT DEFENDED: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Red-team-as-proof: every attack on the lossless law fails safely.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
