#!/usr/bin/env python3
"""check_teleon_control_plane — proof that Teleon is a CONTROL/METADATA plane, not a compute unit.

Proves: (1) an EXTERNAL run (e.g. Cloudflare/customer compute) is recorded into the descent brain WITHOUT Teleon
running the unit; (2) Teleon GUIDES the next improvement from those tracked results (no run); (3) the brain LEARNS
from external runs (training corpus incl. them); (4) Cloudflare Workers AI is a BYO model lane + CloudflareWorkers is
a customer_account compute provider; (5) the positioning is documented. serves_truth=false throughout.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_teleon_control_plane.py --self-test
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.evolution.descent_attempt_store import DescentAttemptStore
from src.teleon.evolution.external_outcomes import record_external_outcome, guide_next

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource


def _self_test() -> int:
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)

    with tempfile.TemporaryDirectory() as d:
        brain = DescentAttemptStore(os.path.join(d, "ext.jsonl"))
        # an external Cloudflare run is recorded into the brain — Teleon did NOT run the unit
        r = record_external_outcome(
            brain, unit_id="extraction:doc_schema", provider="cloudflare_workers",
            before={"cost": 0.30, "determinism": 0.2, "tokens_in": 4000, "llm_usage": 1, "freshness": 0.2},
            after={"cost": 0.02, "determinism": 0.2, "tokens_in": 800, "llm_usage": 1, "freshness": 0.2},
            receipt_ref="receipt://cf/run/123")
        ck("an external run is recorded into the brain WITHOUT Teleon executing the unit",
           r["recorded"] and r["teleon_executed_unit"] is False and r["ran_on"] == "cloudflare_workers")
        ck("the recorded outcome reflects the external result (improved)", r["outcome"] == "improved")
        ck("the brain holds the external attempt + lineage to where it ran",
           any(a["unit_id"] == "extraction:doc_schema" and a["substrate_ref"].startswith("external:cloudflare") for a in brain.all()))

        # add a second external run so the brain can guide
        record_external_outcome(brain, unit_id="enrichment:search", provider="customer_k8s",
                                before={"cost": 0.035, "determinism": 0.2, "tokens_in": 2000, "llm_usage": 1, "freshness": 1.0},
                                after={"cost": 0.005, "determinism": 0.2, "tokens_in": 1000, "llm_usage": 1, "freshness": 1.0},
                                strategy="model_downgrade")
        # Teleon GUIDES the next improvement from tracked results — no run
        g = guide_next(brain, {"cost": 0.30, "determinism": 0.2, "tokens_in": 4000, "llm_usage": 1, "freshness": 0.2})
        ck("Teleon guides the next improvement from TRACKED results (no run needed)",
           g["learned_from_attempts"] >= 2 and "serves_truth" in g)
        # the brain learns from external runs (training corpus includes them)
        ck("the brain learns from external runs (training corpus incl. external)",
           len(brain.training_examples()) >= 2)
        ck("nothing serves truth (records are evidence, not truth)",
           r["serves_truth"] is False and g["serves_truth"] is False and all(a["serves_truth"] is False for a in brain.all()))

    # Cloudflare is a BYO LLM lane AND a customer_account compute provider
    lanes = json.loads((_resource("architecture") / "lowcost_llm_endpoint_registry.json").read_text())["entries"]
    ck("Cloudflare Workers AI is a BYO edge LLM lane (improvement LLMs can run on Cloudflare)",
       any(e["provider_id"] == "cloudflare_workers_ai" and e["cost_class"] == "byo_customer_account" for e in lanes))
    from src.teleon.runtime.execution_providers.cloudflare_workers import py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider
    ck("the final unit runs on the customer's account (compute_ownership=customer_account)",
       py_class_src_teleon_runtime_execution_providers_cloudflare_workers__CloudflareWorkersProvider().compute_ownership == "customer_account")

    # the positioning is documented (single source, non-fragile)
    ck("the control-plane positioning is documented",
       (_resource("docs") / "architecture" / "teleon-control-plane-vs-compute.md").exists())

    print("\n" + ("PASS - check_teleon_control_plane: Teleon is a thin CONTROL/METADATA plane — external runs "
                  "(Cloudflare/customer) are recorded into the brain WITHOUT Teleon executing the unit, Teleon GUIDES "
                  "the next improvement from tracked results, the brain learns from external runs, Cloudflare is both a "
                  "BYO LLM lane and a customer_account compute provider. serves_truth=false; compute is the customer's."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_teleon_control_plane.py --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
