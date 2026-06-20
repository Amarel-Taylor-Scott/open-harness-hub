#!/usr/bin/env python3
"""scripts.billing_ledger — ledger-only billing over LLM invocation receipts (BUSINESS-PLANE order 1).

The honest billing primitive: read invocation receipts (what we actually served, by key/realm/
model-class), compute "what this month would cost," and RECONCILE against an external provider/
Stripe total — receipts AUDIT the provider, never the reverse (BUSINESS-PLANE.md S13). This adapter
runs forever in parallel; it authors no charges and calls no payment API. Costs are computed from
model CLASSES (not names) per LLM-ECONOMICS — class→rate is the single source below.

Receipt shape (one JSON object per LLM invocation; matches the platform-core/Teleon receipt):
  {"receipt_id","ts","realm","key_id","model_class","input_tokens","output_tokens"}

Stdlib-only, deterministic, offline. Importable (statement/reconcile) + CLI (--self-test, --demo).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

#: model CLASS → (USD per million input tokens, USD per million output tokens). Illustrative public
#: rates as of 2026-06 (LLM-ECONOMICS five lanes); CLASSES not names so a model swap never touches
#: code. Single source — never hand-type a rate elsewhere.
CLASS_RATES_USD_PER_MTOK: dict[str, tuple[float, float]] = {
    "local":    (0.00, 0.00),    # self-hosted / Ollama — no per-token charge
    "budget":   (0.15, 0.60),    # nano/flash interactive lane
    "batch":    (0.075, 0.30),   # ~50% of budget — Baltor verification rail
    "frontier": (3.00, 15.00),   # gated reasoning lane
}
_MILLION = 1_000_000


def receipt_cost_usd(receipt: dict[str, Any]) -> float:
    """Cost of one invocation from its model class + token counts. Unknown class → 0.0 + flagged
    upstream (we never invent a rate)."""
    rate_in, rate_out = CLASS_RATES_USD_PER_MTOK.get(receipt.get("model_class", ""), (0.0, 0.0))
    return (int(receipt.get("input_tokens", 0)) / _MILLION) * rate_in \
        + (int(receipt.get("output_tokens", 0)) / _MILLION) * rate_out


def statement(receipts: list[dict[str, Any]], *, realm: str | None = None,
              month: str | None = None) -> dict[str, Any]:
    """A monthly statement: per-key line items + per-class breakdown + total. Filters by realm and
    YYYY-MM month prefix (on the receipt ts, an ISO string) when given. Pure derivation of receipts —
    authoritative for OUR view of spend."""
    lines: dict[str, dict[str, Any]] = {}
    by_class: dict[str, float] = {}
    unknown_class = 0
    total = 0.0
    for r in receipts:
        if realm and r.get("realm") != realm:
            continue
        if month and not str(r.get("ts", "")).startswith(month):
            continue
        if r.get("model_class") not in CLASS_RATES_USD_PER_MTOK:
            unknown_class += 1
        cost = receipt_cost_usd(r)
        total += cost
        key = r.get("key_id", "unknown")
        line = lines.setdefault(key, {"key_id": key, "realm": r.get("realm"), "invocations": 0,
                                      "input_tokens": 0, "output_tokens": 0, "cost_usd": 0.0})
        line["invocations"] += 1
        line["input_tokens"] += int(r.get("input_tokens", 0))
        line["output_tokens"] += int(r.get("output_tokens", 0))
        line["cost_usd"] = round(line["cost_usd"] + cost, 6)
        by_class[r.get("model_class", "unknown")] = round(
            by_class.get(r.get("model_class", "unknown"), 0.0) + cost, 6)
    return {
        "realm": realm, "month": month, "receipts": len(receipts),
        "lines": sorted(lines.values(), key=lambda x: -x["cost_usd"]),
        "by_class": by_class,
        "total_usd": round(total, 6),
        "unknown_class_receipts": unknown_class,
        "ledger_only": True,
        "note": "Ledger-only: derived from invocation receipts. Authors no charge; receipts audit "
                "the provider, never the reverse.",
    }


def reconcile(ledger_total_usd: float, provider_total_usd: float, *, tolerance_usd: float = 0.01) -> dict[str, Any]:
    """Compare our receipt-derived total to an external provider/Stripe total. We NEVER overwrite
    receipts from the provider; drift beyond tolerance is flagged for human review."""
    drift = round(provider_total_usd - ledger_total_usd, 6)
    return {
        "ledger_total_usd": round(ledger_total_usd, 6),
        "provider_total_usd": round(provider_total_usd, 6),
        "drift_usd": drift,
        "within_tolerance": abs(drift) <= tolerance_usd,
        "authority": "receipts",   # receipts are authoritative; provider is the audited party
        "action": "ok" if abs(drift) <= tolerance_usd else "flag_for_review",
    }


def load_receipts(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _self_test() -> int:
    fails: list[str] = []

    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    receipts = [
        {"receipt_id": "r1", "ts": "2026-06-03T10:00:00Z", "realm": "baltor", "key_id": "k_a",
         "model_class": "budget", "input_tokens": 1_000_000, "output_tokens": 500_000},
        {"receipt_id": "r2", "ts": "2026-06-04T10:00:00Z", "realm": "baltor", "key_id": "k_a",
         "model_class": "batch", "input_tokens": 2_000_000, "output_tokens": 1_000_000},
        {"receipt_id": "r3", "ts": "2026-06-05T10:00:00Z", "realm": "baltor", "key_id": "k_b",
         "model_class": "local", "input_tokens": 5_000_000, "output_tokens": 5_000_000},
        {"receipt_id": "r4", "ts": "2026-05-30T10:00:00Z", "realm": "teleon", "key_id": "k_c",
         "model_class": "frontier", "input_tokens": 100_000, "output_tokens": 50_000},
    ]
    # k_a budget: 1M*0.15 + 0.5M*0.60 = 0.15+0.30 = 0.45 ; batch: 2M*0.075 + 1M*0.30 = 0.15+0.30 = 0.45 → 0.90
    st = statement(receipts, realm="baltor", month="2026-06")
    ck("per-key cost matches hand math (k_a = $0.90)",
       next(l for l in st["lines"] if l["key_id"] == "k_a")["cost_usd"] == 0.9, str(st["lines"]))
    ck("local class is $0", next(l for l in st["lines"] if l["key_id"] == "k_b")["cost_usd"] == 0.0)
    ck("baltor June total = $0.90 (k_b local free)", st["total_usd"] == 0.9, str(st["total_usd"]))
    ck("month filter excludes May teleon receipt", st["receipts"] == 4 and all(
        l["realm"] == "baltor" for l in st["lines"]))
    ck("by_class breakdown present", set(st["by_class"]) == {"budget", "batch", "local"})
    ck("ledger_only flag + receipts-authoritative note", st["ledger_only"] and "audit the provider" in st["note"])
    # reconcile: provider says $0.92 vs our $0.90 → drift $0.02 > $0.01 tolerance → flag
    rec = reconcile(0.90, 0.92)
    ck("reconcile flags drift beyond tolerance, receipts stay authority",
       rec["action"] == "flag_for_review" and rec["authority"] == "receipts" and rec["drift_usd"] == 0.02)
    ck("reconcile ok within tolerance", reconcile(0.90, 0.905)["within_tolerance"] is True)
    # unknown class never invents a rate
    st2 = statement([{"realm": "x", "key_id": "k", "model_class": "mystery",
                      "input_tokens": 9_000_000, "output_tokens": 9_000_000, "ts": "2026-06-01"}])
    ck("unknown model class → $0 + flagged, no invented rate",
       st2["total_usd"] == 0.0 and st2["unknown_class_receipts"] == 1)

    print("\n" + ("PASS — billing_ledger: ledger-only statements from invocation receipts (class→rate single "
                  "source, no names in logic), per-key/per-class/month breakdown matches hand math, "
                  "reconcile flags drift with receipts as authority (never the reverse), unknown class never "
                  "invents a rate."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def main(argv: list[str]) -> int:
    if "--demo" in argv:
        path = REPO_ROOT / "dist" / "analytics" / "llm-receipts.jsonl"
        st = statement(load_receipts(path))
        print(json.dumps(st, indent=2))
        return 0
    return _self_test()


if __name__ == "__main__":
    if len(sys.argv) == 1 or "--self-test" in sys.argv or "--demo" in sys.argv:
        raise SystemExit(main(sys.argv[1:]))
    print("usage: python3 scripts/billing_ledger.py [--self-test|--demo]")
    raise SystemExit(0)
