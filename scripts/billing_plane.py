#!/usr/bin/env python3
"""scripts.billing_plane — metered billing on top of the ledger (BUSINESS-PLANE §3).

The chain the handoff specifies: usage receipts → meter → draft invoice (subscription + metered
overage) → Stripe (test mode). Built on scripts/billing_ledger (the receipt-derived ledger is the
authority — receipts reconcile the provider, NEVER the reverse). Stripe is an owner-gated SEAM:
without STRIPE_API_KEY it raises NotConfigured (a charge is never faked). Plans/prices are a single
named source (no magic literals scattered). Stdlib-only, deterministic, offline.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import billing_ledger  # the receipt-derived ledger = the authority

#: plan catalog — single source (BUSINESS-PLANE / PRO-FORMA pricing to validate). cents/month +
#: included metered allowance in USD before overage is billed.
PLANS: dict[str, dict] = {
    "baltor_team":    {"product": "baltor", "label": "Baltor Team",    "base_cents": 9900,  "included_usd": 25.0},
    "baltor_growth":  {"product": "baltor", "label": "Baltor Growth",  "base_cents": 49900, "included_usd": 250.0},
    "teleon_team":    {"product": "teleon", "label": "Teleon Team",    "base_cents": 9900,  "included_usd": 25.0},
    "teleon_growth":  {"product": "teleon", "label": "Teleon Growth",  "base_cents": 49900, "included_usd": 250.0},
}


class NotConfigured(RuntimeError):
    """Stripe was asked to act without its key — never fake a charge."""


def meter(receipts: list[dict], *, realm: str | None = None, month: str | None = None) -> dict:
    """Metered usage = the ledger statement over invocation receipts (the authority)."""
    return billing_ledger.statement(receipts, realm=realm, month=month)


def draft_invoice(customer: dict, receipts: list[dict], *, month: str | None = None) -> dict:
    """A DRAFT invoice from the customer's plan + metered usage. status='draft', never charged.
    Metered line bills only usage ABOVE the plan's included allowance (overage)."""
    plan = PLANS.get(customer.get("plan", ""))
    if plan is None:
        raise ValueError(f"unknown plan {customer.get('plan')!r}; known {sorted(PLANS)}")
    usage = meter(receipts, realm=customer.get("realm"), month=month)
    metered_usd = round(usage["total_usd"], 6)
    overage_usd = round(max(0.0, metered_usd - plan["included_usd"]), 6)
    lines = [
        {"desc": f"{plan['label']} — monthly subscription", "amount_cents": plan["base_cents"]},
        {"desc": f"Metered usage ${metered_usd:.2f} (incl. ${plan['included_usd']:.2f}) → "
                 f"overage ${overage_usd:.2f}", "amount_cents": round(overage_usd * 100)},
    ]
    total = sum(line["amount_cents"] for line in lines)
    return {
        "customer": customer.get("id"), "realm": customer.get("realm"), "plan": customer.get("plan"),
        "month": month, "status": "draft", "currency": "usd",
        "lines": lines, "total_cents": total,
        "metered_usd": metered_usd, "overage_usd": overage_usd,
        "source": "ledger", "authority": "receipts",
        "stripe": "not_charged (owner-gated seam — receipts reconcile Stripe, never the reverse)",
    }


class StripeAdapter:
    """Owner-gated SEAM. Without STRIPE_API_KEY, create_invoice raises — a charge is never faked.
    Real Stripe test-mode wiring (usage records + draft invoice + webhooks→events) drops in here."""

    name = "stripe"

    def create_invoice(self, invoice: dict) -> dict:
        if not os.environ.get("STRIPE_API_KEY"):
            raise NotConfigured("STRIPE_API_KEY unset — billing is ledger-only; Stripe is owner-gated, not faked")
        raise NotConfigured("Stripe transport not wired in this local build (seam present)")


def reconcile_invoice(invoice: dict, provider_total_usd: float) -> dict:
    """Reconcile our draft total against what the provider says — receipts stay the authority."""
    return billing_ledger.reconcile(invoice["total_cents"] / 100.0, provider_total_usd)


def _self_test() -> int:
    fails: list[str] = []

    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # k_a usage = $0.90 (from billing_ledger hand math); Team includes $25 → no overage
    receipts = [
        {"ts": "2026-06-03T10:00:00Z", "realm": "baltor", "key_id": "k_a", "model_class": "budget",
         "input_tokens": 1_000_000, "output_tokens": 500_000},
        {"ts": "2026-06-04T10:00:00Z", "realm": "baltor", "key_id": "k_a", "model_class": "batch",
         "input_tokens": 2_000_000, "output_tokens": 1_000_000},
    ]
    cust = {"id": "cust_1", "realm": "baltor", "plan": "baltor_team"}
    inv = draft_invoice(cust, receipts, month="2026-06")
    ck("draft invoice status=draft, not charged", inv["status"] == "draft" and "not_charged" in inv["stripe"])
    ck("subscription line = $99.00 (9900c)", inv["lines"][0]["amount_cents"] == 9900)
    ck("metered usage = $0.90 from the ledger", inv["metered_usd"] == 0.9)
    ck("under the $25 allowance → $0 overage → total = $99.00",
       inv["overage_usd"] == 0.0 and inv["total_cents"] == 9900, str(inv["total_cents"]))
    # heavy usage → overage billed
    heavy = receipts + [{"ts": "2026-06-05T10:00:00Z", "realm": "baltor", "key_id": "k_b",
                         "model_class": "frontier", "input_tokens": 5_000_000, "output_tokens": 3_000_000}]
    # frontier: 5M*3 + 3M*15 = 15 + 45 = $60 ; + $0.90 = $60.90 ; overage = 60.90 - 25 = $35.90
    inv2 = draft_invoice(cust, heavy, month="2026-06")
    ck("heavy usage bills overage above allowance ($35.90)", inv2["overage_usd"] == 35.9, str(inv2["overage_usd"]))
    ck("invoice total = base + overage ($99 + $35.90 = $134.90 = 13490c)",
       inv2["total_cents"] == 9900 + 3590, str(inv2["total_cents"]))
    # Stripe seam: never fakes a charge
    os.environ.pop("STRIPE_API_KEY", None)
    try:
        StripeAdapter().create_invoice(inv)
        ck("Stripe unconfigured → raises (no fake charge)", False)
    except NotConfigured:
        ck("Stripe unconfigured → NotConfigured (no fake charge)", True)
    # reconcile keeps receipts as authority
    rec = reconcile_invoice(inv, 99.50)
    ck("reconcile flags drift, receipts stay authority",
       rec["authority"] == "receipts" and rec["action"] == "flag_for_review")
    ck("unknown plan rejected", _raises(lambda: draft_invoice({"id": "x", "plan": "nope"}, [])))

    print("\n" + ("PASS — billing_plane: metered chain (receipts → meter → draft invoice = subscription + "
                  "overage-above-allowance) on the ledger authority; plans single-sourced; Stripe is an "
                  "owner-gated seam that never fakes a charge; reconcile keeps receipts authoritative."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _raises(fn) -> bool:
    try:
        fn()
        return False
    except Exception:  # noqa: BLE001
        return True


if __name__ == "__main__":
    if len(sys.argv) == 1 or "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/billing_plane.py --self-test")
    raise SystemExit(0)
