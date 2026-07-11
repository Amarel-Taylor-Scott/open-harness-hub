#!/usr/bin/env python3
"""scripts.check_inference_api_handler — PROOF: the Shared LLM Plane is SERVED end-to-end. The pure handler
scripts.api_inference_handler answers every /api/inference/* route safely, the admin server delegates to it (GET +
POST), and the read-only UI panel consumes it — with model output never served as truth and no secret value leaked.

Asserts (against scripts.api_inference_handler.handle, the server source, and _repos/baltor/frontend/inference-plane.html):
  A. SURFACE: handle() owns the 8 inference routes (the 6 GET projections + resolve-preference + structured-local);
     the read routes equal api_projection.ROUTES minus the compute route.
  B. GET PROJECTIONS: every GET route returns 200 with its projection.
  C. ERRORS: an unknown route → 404 ErrorEnvelope; resolve-preference with no layers → 400 ErrorEnvelope.
  D. RESOLVE: POST resolve-preference returns a ResolvedInferencePreference with numeric model-class codes.
  E. COMPUTE-NOT-TRUTH: POST structured-local returns is_truth=false + a ModelInvocationReceipt whose
     policy_checks.llm_output_is_truth is false; the receipt is recorded and then projected by GET receipts.
  F. NO SECRET LEAK: no secret-VALUE pattern (the handler's own guard regex) appears in ANY response.
  G. DETERMINISM: structured-local with the same `now` twice yields the same receipt_id.
  H. SERVER WIRED: the admin server delegates /api/inference/* to api_inference_handler in both do_GET and do_POST.
  I. UI PROJECTION: _repos/baltor/frontend/inference-plane.html exists, fetches the inference endpoints, declares itself
     projection-only with output-never-truth, and contains no secret-value pattern.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts import api_inference_handler as H
from src.teleon.inference import api_projection as ap

_LAYERS = [{"preference_id": "demo", "model_class_preference": {"tier_code": 400, "specialization_codes": [300]},
            "allowed_provider_nodes": ["model.local_stub@v1"], "disallowed_provider_nodes": [],
            "fallback_policy": {}, "data_policy": {}}]
_GET = ("/api/inference/providers", "/api/inference/model-graph", "/api/inference/free-endpoints",
        "/api/inference/preferences", "/api/inference/health", "/api/inference/receipts")


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    responses = []  # collect every response for the global no-leak scan

    check("A: handler owns the 8 inference routes incl. structured-local",
          len(H.ROUTES) == 8 and "/api/inference/structured-local" in H.ROUTES)
    ap_read = {r.split(" ", 1)[1] for r in ap.ROUTES if not r.endswith("structured-local")}
    check("A: handler read routes == api_projection read/resolve routes", set(_GET + ("/api/inference/resolve-preference",)) == ap_read,
          str(ap_read ^ set(_GET + ("/api/inference/resolve-preference",))))

    ok_get = True
    for r in _GET:
        c, p = H.handle("GET", r, None)
        responses.append(p)
        ok_get = ok_get and c == 200
    check("B: every GET route returns 200 with its projection", ok_get)

    c404, p404 = H.handle("GET", "/api/inference/does-not-exist", None)
    responses.append(p404)
    check("C: unknown route → 404 ErrorEnvelope",
          c404 == 404 and p404.get("schema_version") == "ErrorEnvelope" and p404.get("error_type") == "not_found")
    c400, p400 = H.handle("POST", "/api/inference/resolve-preference", {})
    responses.append(p400)
    check("C: resolve-preference with no layers → 400 ErrorEnvelope",
          c400 == 400 and p400.get("schema_version") == "ErrorEnvelope")

    cr, pr = H.handle("POST", "/api/inference/resolve-preference", {"layers": _LAYERS})
    responses.append(pr)
    mc = pr.get("effective", {}).get("model_class_preference", {})
    check("D: resolve-preference → ResolvedInferencePreference with numeric codes",
          cr == 200 and pr.get("schema_version") == "ResolvedInferencePreference"
          and isinstance(mc.get("tier_code"), int) and isinstance(mc.get("specialization_codes"), list))

    cs, ps = H.handle("POST", "/api/inference/structured-local",
                      {"object_id": "demo.object", "preference_layers": _LAYERS, "input_text": "hi", "now": "2026-06-05T00:00:00Z"})
    responses.append(ps)
    rcpt = ps.get("receipt", {})
    check("E: structured-local → 200, is_truth=false, ModelInvocationReceipt, output-not-truth",
          cs == 200 and ps.get("is_truth") is False and rcpt.get("schema_version") == "ModelInvocationReceipt"
          and rcpt.get("receipt_id") and rcpt.get("policy_checks", {}).get("llm_output_is_truth") is False)
    crc, prc = H.handle("GET", "/api/inference/receipts", None)
    responses.append(prc)
    check("E: the produced receipt is then projected by GET receipts",
          any(x.get("receipt_id") == rcpt.get("receipt_id") for x in prc.get("receipts", [])))

    leaks = [i for i, p in enumerate(responses) if H._LEAK.search(json.dumps(p))]
    check("F: no secret-value pattern in ANY response", not leaks, f"responses with a leak: {leaks}")

    _, ps2 = H.handle("POST", "/api/inference/structured-local",
                      {"object_id": "demo.object", "preference_layers": _LAYERS, "input_text": "hi", "now": "2026-06-05T00:00:00Z"})
    check("G: structured-local is deterministic (same now → same receipt_id)",
          ps2.get("receipt", {}).get("receipt_id") == rcpt.get("receipt_id"))

    src = (_resource("scripts/baltor_admin_demo_server.py")).read_text(encoding="utf-8")
    check("H: admin server delegates /api/inference/* to api_inference_handler (GET + POST)",
          src.count("from scripts.api_inference_handler import handle") >= 2
          and 'if path.startswith("/api/inference/")' in src
          and 'if parsed.path.startswith("/api/inference/")' in src)
    check("H: admin server serves the UI panel at /inference-plane", 'self._serve_web("inference-plane.html")' in src)

    ui_p = _resource("web/baltor/inference-plane.html")
    ui = ui_p.read_text(encoding="utf-8") if ui_p.is_file() else ""
    check("I: UI panel exists + fetches the inference endpoints", bool(ui)
          and "/api/inference/providers" in ui and "/api/inference/structured-local" in ui)
    check("I: UI declares projection-only + output-never-truth", "projection only" in ui.lower()
          and ("never served truth" in ui.lower() or "never truth" in ui.lower()))
    check("I: UI contains no secret-value pattern", not H._LEAK.search(ui))

    print("\n" + ("PASS — check_inference_api_handler: the Shared LLM Plane is served end-to-end — the handler answers "
                  "every /api/inference route safely (errors are ErrorEnvelope), structured-local output is a "
                  "candidate (never truth) with a ModelInvocationReceipt, the admin server delegates GET+POST, and the "
                  "read-only UI consumes the projection with no secret leak." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_inference_api_handler.py --self-test")
    raise SystemExit(0)
