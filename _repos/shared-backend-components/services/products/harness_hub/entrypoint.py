"""OpenHubForAI — product service (request tier). Serves _repos/openhubforai/frontend/ + the OHH API.

Same shared backend as Baltor; this door differs only by OH_PRODUCT (front-end folder +
brand). Thin by design: pin the product, wire telemetry, hand off to the shared server.

    python -m services.products.harness_hub.entrypoint --port 8000
"""
from __future__ import annotations

import os
os.environ.setdefault("OH_PRODUCT", "openhubforai")  # MUST precede any scripts.showcase import (sets WEB_DIR)

import runpy
import sys

from services.platform._shared import telemetry


def main() -> int:
    port = int(os.environ.get("OH_METRICS_PORT", "0")) or None
    telemetry.configure("openhubforai", metrics_port=port)
    telemetry.log("product.boot", web_root="_repos/openhubforai/frontend", brand="OpenHubForAI")
    sys.argv = ["scripts.showcase", *sys.argv[1:]]            # forward --port etc. to the shared server
    runpy.run_module("scripts.showcase", run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
