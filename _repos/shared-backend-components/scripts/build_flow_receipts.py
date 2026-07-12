#!/usr/bin/env python3
"""scripts.build_flow_receipts — assemble the back-of-house artifacts the full-journey video shows:
the rendered verification email (from the email port's outbox) + a DRAFT invoice (from the billing
plane over sample usage). Writes dist/flow-receipts.json for e2e/journey_full.mjs to render.
No secrets; illustrative usage only. Stdlib + the standardized ports."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import sys
from pathlib import Path

REPO_ROOT = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import billing_plane, email_port  # the standardized ports

OUTBOX = email_port.email_outbox_dir()   # single source = email_port (the writer)
OUT = _resource("dist") / "flow-receipts.json"


def main() -> int:
    # 1) render a fresh verification email through the port (console adapter → outbox, not sent)
    email_port.send("baltor", "verify_email", "demo@aidoneright.dev",
                    {"verify_url": "local://baltor/verify/demo"})
    latest = max(OUTBOX.glob("*-baltor-verify_email.txt"), key=lambda p: p.stat().st_mtime, default=None)
    email_text = latest.read_text(encoding="utf-8") if latest else "(no outbox email)"

    # 2) a draft invoice from illustrative first-month usage (budget + batch + a little frontier)
    receipts = [
        {"ts": "2026-06-03", "realm": "baltor", "key_id": "demo_key", "model_class": "budget",
         "input_tokens": 8_000_000, "output_tokens": 4_000_000},
        {"ts": "2026-06-12", "realm": "baltor", "key_id": "demo_key", "model_class": "batch",
         "input_tokens": 20_000_000, "output_tokens": 10_000_000},
        {"ts": "2026-06-20", "realm": "baltor", "key_id": "demo_key", "model_class": "frontier",
         "input_tokens": 1_500_000, "output_tokens": 800_000},
    ]
    invoice = billing_plane.draft_invoice(
        {"id": "cust_demo", "realm": "baltor", "plan": "baltor_team"}, receipts, month="2026-06")

    OUT.write_text(json.dumps({"email": email_text, "invoice": invoice}, indent=2), encoding="utf-8")
    print(f"wrote {OUT} — verification email + draft invoice "
          f"(total ${invoice['total_cents'] / 100:.2f}, metered ${invoice['metered_usd']:.2f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
