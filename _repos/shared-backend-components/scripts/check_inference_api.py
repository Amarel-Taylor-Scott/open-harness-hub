#!/usr/bin/env python3
"""scripts.check_inference_api — PROOF: the /api/inference/* projection (_repos/teleon/backend/src/teleon/inference/api_projection) is a
safe, PROJECTION-ONLY read view over the shared LLM plane. It exposes the provider graph, free-endpoint due-diligence,
preference coverage, health, and a local resolve-preference path WITHOUT ever leaking a raw key or secret value, and
every declared route binds to a real callable.

Asserts:
  A. SURFACE: api_projection exposes providers/model_graph/free_endpoints/preferences_coverage/health/receipts/
     resolve_preference/error_envelope and a ROUTES map; every ROUTES handler resolves to a real callable.
  B. NO SECRET LEAK: NO raw-key pattern (sk-/gsk_/secret://value/Bearer …) appears anywhere in ANY projection; a
     provider entry carries only a has_secret_ref BOOLEAN — never the secret value or the secret_ref string.
  C. NUMERIC: every provider projection carries numeric tier_code/status_code + an int specialization_codes list
     (routing primitives are numeric, not display strings) — and DOES carry a node_id.
  D. FREE-ENDPOINTS: the free-endpoint projection is the due-diligence report list and every entry is is_truth=False
     (discovery≠trust; output≠truth).
  E. HEALTH IS OFFLINE-HONEST: no node is reported live_checked=True (we make no network probe); external nodes
     report a non-live status, the local stub reports healthy_local.
  F. RESOLVE WORKS OFFLINE: resolve_preference returns a ResolvedInferencePreference with numeric model_class codes.
  G. ERROR ENVELOPE: error_envelope conforms to ErrorEnvelope (all required fields) and is retryable-typed.
  H. PROJECTION-ONLY + DETERMINISM: all_projections() is byte-identical across two calls (pure read; no mutation).

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import os
import re
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.inference import api_projection as ap
from src.teleon.inference import oips

# raw-secret patterns that must NEVER appear in a projection (the secret_ref *scheme* with a value, or a bare key)
_LEAK = re.compile(r"(sk-[A-Za-z0-9]{8,}|gsk_[A-Za-z0-9]{8,}|secret://[^\"]*?:[^\"]+|Bearer\s+[A-Za-z0-9._-]{8,})")
_PREF = [{"preference_id": "p", "model_class_preference": {"tier_code": 400, "specialization_codes": [300]},
          "allowed_provider_nodes": ["model.local_stub@v1"], "disallowed_provider_nodes": [],
          "fallback_policy": {}, "data_policy": {}}]


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    surface = ["providers", "model_graph", "free_endpoints", "preferences_coverage", "health", "receipts",
               "resolve_preference", "error_envelope"]
    check("A: projection surface present", all(callable(getattr(ap, s, None)) for s in surface),
          str([s for s in surface if not callable(getattr(ap, s, None))]))
    handlers = {v: (getattr(ap, v, None) or getattr(oips, v, None)) for v in ap.ROUTES.values()}
    check("A: every declared ROUTE binds to a real callable",
          bool(ap.ROUTES) and all(callable(h) for h in handlers.values()),
          str([v for v, h in handlers.items() if not callable(h)]))

    proj = ap.all_projections()
    blob = json.dumps(proj)
    leaks = _LEAK.findall(blob)
    check("B: NO raw-key / secret-value pattern anywhere in the projections", not leaks, str(leaks[:3]))
    check("B: provider entries carry has_secret_ref BOOL and NOT a secret value/ref string",
          all(isinstance(p.get("has_secret_ref"), bool) and "secret_ref" not in p for p in proj["providers"]))

    provs = proj["providers"]
    check("C: every provider projection is numeric-coded + has node_id",
          bool(provs) and all(p.get("node_id") and isinstance(p.get("tier_code"), int)
                              and isinstance(p.get("status_code"), int) and isinstance(p.get("specialization_codes"), list)
                              and all(isinstance(c, int) for c in p["specialization_codes"]) for p in provs))

    fe = proj["free_endpoints"]
    check("D: free-endpoint projection is due-diligence reports, all is_truth=False",
          bool(fe) and all(r.get("is_truth") is False for r in fe))

    health = proj["health"]
    check("E: health is offline-honest — no node reports live_checked=True",
          bool(health) and all(h.get("live_checked") is False for h in health))
    by_local = {h["provider_node_id"]: h for h in health}
    check("E: external nodes report non-live status; the local stub reports healthy_local",
          by_local.get("model.local_stub@v1", {}).get("status") == "healthy_local"
          and all(h["status"] == "requires_secret_ref" for h in health
                  if h["provider_node_id"] != "model.local_stub@v1" and h["provider_node_id"]
                  in {n["node_id"] for n in oips.load_graph()["nodes"] if n.get("external")}))

    resolved = ap.resolve_preference(_PREF)
    mc = resolved.get("effective", {}).get("model_class_preference", {})
    check("F: resolve_preference works offline → numeric model_class codes",
          isinstance(mc.get("tier_code"), int) and isinstance(mc.get("specialization_codes"), list), json.dumps(resolved)[:120])

    req = json.loads((_resource("schemas") / "envelopes" / "ErrorEnvelope.schema.json").read_text())["required"]
    ee = ap.error_envelope("provider_unavailable", "model.fireworks@candidate has no secret_ref", retryable=True)
    check("G: error_envelope conforms to ErrorEnvelope + retryable-typed",
          all(k in ee for k in req) and isinstance(ee["retryable"], bool), str([k for k in req if k not in ee]))

    check("H: projection-only + deterministic (two builds byte-identical)", json.dumps(ap.all_projections()) == blob)

    print("\n" + ("PASS — check_inference_api: the /api/inference projection is projection-only — provider graph, "
                  "free-endpoint due-diligence, preference coverage, health and local resolve are exposed with numeric "
                  "codes and NO raw key/secret value; every declared route binds to a real callable; health is "
                  "offline-honest; errors are ErrorEnvelope." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_inference_api.py --self-test")
    raise SystemExit(0)
