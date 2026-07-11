#!/usr/bin/env python3
"""scripts.check_trace_store — proof: the Determinism Factory TRACE STORE is append-only, content-addressed,
tenant-scoped, and a ``tenant_private`` trace can NEVER be read into a global-rule mining set.

The trace store is a LEDGER over Baltor's existing authorities — it records decisions, it never makes them.
This proof shows:

* **append-only** — appending never mutates/removes an earlier trace; an idempotent re-append of the same
  identity body returns the SAME id and grows the store by 0.
* **content-addressed + deterministic** — the id is ``dtrace:sha256:<hex>:<tenant>`` derived from the
  identity-bearing fields (NOT ``created_at``); the same logical trace re-built in a fresh store yields the
  same id with two different injected clocks; a different decision yields a different id.
* **verification law** — a trace may be ``verified`` ONLY if it is workflow/adjudication AND source-grounded
  (≥1 output handle) AND receipt-backed (≥1 receipt); an LLM or consensus trace can NEVER be verified, and a
  workflow decision without handles/receipts is rejected from being verified (negative-tested).
* **tenant-scoped** — a cross-tenant ``get`` is rejected; the id embeds the tenant.
* **tenant_private cannot train a global rule** (the load-bearing negative) — a raw ``tenant_private`` trace
  is silently excluded from a ``global_public`` ``mining_set``; forcing it in via ``assert_mineable_global``
  raises ``TenantBoundaryError``; only after BOTH anonymize AND approve does it enter the global set; a
  ``tenant_private`` mining set refuses an unscoped read and returns only the owning tenant's traces.

Determinism: injected ``now``, hashlib ids, no RNG, no clock, no network, no tempfiles needed (in-memory).

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_trace_store.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.determinism.trace_store import (  # noqa: E402
    GLOBAL_PUBLIC,
    TENANT_PRIVATE,
    TenantBoundaryError,
    TraceStore,
    TraceStoreError,
    parse_trace_id,
)

_T1 = "2026-01-01T00:00:00Z"
_T2 = "2026-09-09T09:09:09Z"  # a DIFFERENT injected clock — must not change the content id


def _verified_workflow(store: TraceStore, *, tenant: str, scope: str, step: str, decision: dict,
                       now: str = _T1):
    """Append a source-grounded, receipt-backed (i.e. verified) workflow trace."""
    return store.append(
        tenant_id=tenant, scope=scope, trace_kind="workflow", workflow_id="cfpb-recon", step_id=step,
        decision_key="reconcile:deadline_mismatch", decision=decision, verified=True,
        input_handles=[f"ctx://{step}#in"], output_handles=[f"ctx://{step}#winner"],
        receipt_ids=[f"recon-{step}"], now=now)


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    store = TraceStore()

    # 1) APPEND-ONLY + content-addressed id shape.
    t1 = _verified_workflow(store, tenant="acme", scope=GLOBAL_PUBLIC, step="s1",
                            decision={"winner": "reg-e-10bd", "reason": "authority"})
    check("append returns a trace with a dtrace:sha256:<hex>:<tenant> id",
          t1.trace_id.startswith("dtrace:sha256:") and t1.trace_id.endswith(":acme"))
    hex_, tid = parse_trace_id(t1.trace_id)
    check("the id parses to (sha256 hex, tenant)", len(hex_) == 64 and tid == "acme")
    check("store length is 1 after one append", len(store) == 1)

    # idempotent re-append of the SAME identity body → SAME id, store does NOT grow (append-only).
    t1_again = _verified_workflow(store, tenant="acme", scope=GLOBAL_PUBLIC, step="s1",
                                  decision={"winner": "reg-e-10bd", "reason": "authority"}, now=_T2)
    check("idempotent re-append returns the SAME id", t1_again.trace_id == t1.trace_id)
    check("idempotent re-append does NOT grow the store (append-only)", len(store) == 1)
    check("the original trace is unchanged (immutable; first write wins on created_at)",
          store.get(t1.trace_id).created_at == _T1)

    # 2) DETERMINISTIC across a fresh store + a different injected clock.
    store2 = TraceStore()
    t1_fresh = _verified_workflow(store2, tenant="acme", scope=GLOBAL_PUBLIC, step="s1",
                                  decision={"winner": "reg-e-10bd", "reason": "authority"}, now=_T2)
    check("same logical trace in a clean store yields the SAME id (deterministic, clock-independent)",
          t1_fresh.trace_id == t1.trace_id)
    # a DIFFERENT decision → a different id.
    t_diff = _verified_workflow(store, tenant="acme", scope=GLOBAL_PUBLIC, step="s2",
                                decision={"winner": "faq-30d", "reason": "freshness"})
    check("a different decision yields a different id", t_diff.trace_id != t1.trace_id)

    # 3) VERIFICATION LAW — only workflow/adjudication, source-grounded + receipt-backed, may be verified.
    llm_verified_rejected = False
    try:
        store.append(tenant_id="acme", scope=GLOBAL_PUBLIC, trace_kind="llm", workflow_id="cfpb-recon",
                     step_id="s1", decision_key="reconcile:deadline_mismatch",
                     decision={"winner": "reg-e-10bd"}, verified=True, output_handles=["ctx://x#y"],
                     receipt_ids=["r1"], model_id="m1")
    except TraceStoreError:
        llm_verified_rejected = True
    check("an LLM trace can NEVER be verified (consensus/LLM output is evidence, not truth)",
          llm_verified_rejected)

    consensus_verified_rejected = False
    try:
        store.append(tenant_id="acme", scope=GLOBAL_PUBLIC, trace_kind="consensus",
                     workflow_id="cfpb-recon", step_id="s1", decision_key="k",
                     decision={"agreement": 1.0}, verified=True, output_handles=["ctx://x#y"],
                     receipt_ids=["r1"])
    except TraceStoreError:
        consensus_verified_rejected = True
    check("a consensus trace can NEVER be verified", consensus_verified_rejected)

    no_handle_rejected = False
    try:
        store.append(tenant_id="acme", scope=GLOBAL_PUBLIC, trace_kind="workflow",
                     workflow_id="cfpb-recon", step_id="s3", decision_key="k",
                     decision={"winner": "x"}, verified=True, receipt_ids=["r1"])  # no output_handles
    except TraceStoreError:
        no_handle_rejected = True
    check("a verified trace WITHOUT source handles is rejected (no grounding → not a verified outcome)",
          no_handle_rejected)

    no_receipt_rejected = False
    try:
        store.append(tenant_id="acme", scope=GLOBAL_PUBLIC, trace_kind="workflow",
                     workflow_id="cfpb-recon", step_id="s4", decision_key="k",
                     decision={"winner": "x"}, verified=True, output_handles=["ctx://x#y"])  # no receipts
    except TraceStoreError:
        no_receipt_rejected = True
    check("a verified trace WITHOUT a receipt is rejected (no receipt → not a verified outcome)",
          no_receipt_rejected)

    # an unverified llm trace IS allowed (it is a proposal, recorded as evidence).
    llm_ok = store.append(tenant_id="acme", scope=GLOBAL_PUBLIC, trace_kind="llm",
                          workflow_id="cfpb-recon", step_id="s1", decision_key="reconcile:deadline_mismatch",
                          decision={"winner": "reg-e-10bd"}, model_id="m1", provider_id="p1",
                          prompt_hash="sha256:dead")
    check("an unverified LLM proposal IS recorded (evidence), but stays verified=False",
          llm_ok.verified is False and store.has(llm_ok.trace_id))

    # 4) TENANT-SCOPED reads — a cross-tenant get is rejected.
    cross_caught = False
    try:
        store.get(t1.trace_id, tenant="globex")  # globex asking for acme's trace
    except TenantBoundaryError:
        cross_caught = True
    check("a cross-tenant get is rejected (tenant is part of the id identity)", cross_caught)
    check("the owning tenant CAN read its own trace", store.get(t1.trace_id, tenant="acme").trace_id == t1.trace_id)

    # 5) THE LOAD-BEARING NEGATIVE — tenant_private cannot train a GLOBAL rule.
    priv = store.append(
        tenant_id="globex", scope=TENANT_PRIVATE, trace_kind="workflow", workflow_id="globex-wf",
        step_id="p1", decision_key="reconcile:deadline_mismatch",
        decision={"winner": "globex-private", "reason": "authority"}, verified=True,
        output_handles=["ctx://globex#winner"], receipt_ids=["recon-p1"], now=_T1)

    global_set = store.mining_set(scope=GLOBAL_PUBLIC, require_verified=True)
    priv_ids_in_global = {t.trace_id for t in global_set if t.scope == TENANT_PRIVATE}
    check("a raw tenant_private trace is EXCLUDED from a global_public mining set (cannot train a global rule)",
          priv.trace_id not in {t.trace_id for t in global_set} and not priv_ids_in_global)
    check("the global mining set still contains the legitimately-global verified workflow trace",
          t1.trace_id in {t.trace_id for t in global_set})

    forced_caught = False
    try:
        store.assert_mineable_global(priv)  # explicitly try to force a private trace into the global miner
    except TenantBoundaryError:
        forced_caught = True
    check("forcing a tenant_private trace into the global miner raises TenantBoundaryError", forced_caught)

    # only after anonymize AND approve does it become globally mineable.
    anon = store.append(
        tenant_id="globex", scope=TENANT_PRIVATE, trace_kind="workflow", workflow_id="globex-wf",
        step_id="p1", decision_key="reconcile:deadline_mismatch",
        decision={"winner": "globex-private", "reason": "authority"}, verified=True,
        anonymized=True, approved_for_global=True,
        output_handles=["ctx://globex#winner"], receipt_ids=["recon-p1"], now=_T1)
    global_set2 = store.mining_set(scope=GLOBAL_PUBLIC, require_verified=True)
    check("an ANONYMIZED + APPROVED private trace DOES enter the global mining set",
          anon.trace_id in {t.trace_id for t in global_set2})
    # assert_mineable_global accepts the anonymized+approved one without raising.
    anon_ok = True
    try:
        store.assert_mineable_global(anon)
    except TenantBoundaryError:
        anon_ok = False
    check("assert_mineable_global accepts an anonymized + approved private trace", anon_ok)

    # a tenant_private mining set refuses an unscoped read, and is scoped to ONE tenant.
    unscoped_caught = False
    try:
        store.mining_set(scope=TENANT_PRIVATE)  # no tenant given
    except TenantBoundaryError:
        unscoped_caught = True
    check("a tenant_private mining set refuses an UNSCOPED read", unscoped_caught)
    globex_priv = store.mining_set(scope=TENANT_PRIVATE, tenant="globex")
    check("a tenant_private mining set returns ONLY the owning tenant's traces",
          all(t.tenant_id == "globex" for t in globex_priv) and len(globex_priv) >= 1)
    acme_priv = store.mining_set(scope=TENANT_PRIVATE, tenant="acme")
    check("another tenant's private mining set does NOT see globex's private traces",
          all(t.tenant_id == "acme" for t in acme_priv))

    # require_verified excludes raw proposals from any mining set.
    unverified_in_set = any(not t.verified for t in store.mining_set(scope=GLOBAL_PUBLIC, require_verified=True))
    check("a (require_verified) mining set contains NO unverified traces (raw LLM proposals excluded)",
          not unverified_in_set)

    ok = not fails
    print(
        f"\n{'PASS — check_trace_store: the trace store is append-only (idempotent re-append, immutable, no growth), content-addressed + deterministic (clock-independent ids), enforces the verification law (LLM/consensus never verified; verified needs handles + receipts), tenant-scoped (cross-tenant get rejected), and a tenant_private trace can NEVER train a global rule (excluded from the global mining set; force-attempt raises; only anonymized+approved enters; private sets are tenant-scoped).' if ok else f'{len(fails)} FAILURES: {fails}'}"
    )
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: determinism-factory trace store (append-only, content-addressed, tenant-scoped, private-never-global).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
