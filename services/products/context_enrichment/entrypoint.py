"""Context Enrichment (CEaaS) — product service (request tier). Serves web/context-enrichment/ +
the CEaaS API (and, when built, the MCP serve endpoints for the content tiers + governed corpora).

Same shared backend as Open Harness Hub; this door differs only by OH_PRODUCT (front-end folder +
brand). Thin by design: pin the product, wire telemetry, hand off to the shared server.

    python -m services.products.context_enrichment.entrypoint --port 8001
"""
from __future__ import annotations

import os
os.environ.setdefault("OH_PRODUCT", "context-enrichment")  # MUST precede any scripts.showcase import

import runpy
import sys

from services.platform._shared import telemetry


def main() -> int:
    port = int(os.environ.get("OH_METRICS_PORT", "0")) or None
    telemetry.configure("context-enrichment", metrics_port=port)
    telemetry.log("product.boot", web_root="web/context-enrichment", brand="Context Enrichment")
    sys.argv = ["scripts.showcase", *sys.argv[1:]]
    runpy.run_module("scripts.showcase", run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
