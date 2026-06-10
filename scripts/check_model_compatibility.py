#!/usr/bin/env python3
"""scripts.check_model_compatibility — PROOF: the model-compatibility runner determines which models a digested
skill works with (and which it does NOT), and on what inputs/outputs — via the Inference Gateway, honestly.

Asserts:
  A. CONTRACT: ModelCompatibilityReport.v1 registered.
  B. RUN: a digested skill yields a per-node report list + works_with / not_compatible_with summary.
  C. SPECIALIZATION MISMATCH → not_compatible: an embeddings-only node for a reasoning skill is not_compatible.
  D. LOCAL STUB → draft_only (plumbing proven, not production).
  E. CREDENTIALED+HEALTHY external reasoning node → production_allowed_after_gate.
  F. EXTERNAL WITHOUT CREDS → eval_only (honest — cannot verify offline), never silently production.
  G. STRUCTURED-OUTPUT flag + required_spec_codes reported.
  H. COMPOSES the Inference Gateway (uses its numeric provider graph).
  I. DETERMINISM + output-not-truth + dependency law.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon import digestion as D

_NOW = "2026-06-06T00:00:00Z"
_FX = _REPO / "fixtures" / "digestion"


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    contracts = json.dumps(json.loads((_REPO / "architecture" / "contract_registry.json").read_text()))
    check("A: ModelCompatibilityReport.v1 registered", "digestion/ModelCompatibilityReport.v1.schema.json" in contracts)

    dg = D.digest_skill(D.parse_skill_md((_FX / "deterministic_skill_sample" / "SKILL.md").read_text()),
                        source_ref="x", now=_NOW)
    res = D.run_model_compatibility(dg, now=_NOW)
    by_node = {r["provider_node_id"]: r for r in res["reports"]}

    check("B: per-node reports + works/not-compatible summary", res["reports"] and "works_with" in res and "not_compatible_with" in res)
    check("C: embeddings-only node → not_compatible for a reasoning skill",
          by_node.get("embedding.local_hash@v1", {}).get("recommended_use") == "not_compatible", json.dumps(by_node.get("embedding.local_hash@v1")))
    check("D: local stub → draft_only", by_node.get("model.local_stub@v1", {}).get("recommended_use") == "draft_only", json.dumps(by_node.get("model.local_stub@v1")))

    # E credentialed+healthy external
    res_creds = D.run_model_compatibility(dg, now=_NOW, available_secrets={"secret://provider/anthropic"}, provider_health={})
    anth = {r["provider_node_id"]: r for r in res_creds["reports"]}.get("model.anthropic.frontier@candidate", {})
    check("E: credentialed+healthy external reasoning node → production_allowed_after_gate",
          anth.get("recommended_use") == "production_allowed_after_gate", json.dumps(anth))
    # F external no creds → eval_only
    check("F: external without creds → eval_only (not production)",
          by_node.get("model.anthropic.frontier@candidate", {}).get("recommended_use") == "eval_only", json.dumps(by_node.get("model.anthropic.frontier@candidate")))

    # G structured-output + required spec codes
    check("G: structured_output flag + required_spec_codes reported",
          all("structured_output_ok" in r for r in res["reports"]) and 500 in res["required_spec_codes"])

    # H composes inference gateway
    check("H: composes the Inference Gateway provider graph", (_REPO / "architecture" / "model_provider_graph.json").exists() and all(r["tested_via"].startswith("inference_gateway") for r in res["reports"]))

    # I determinism + not truth + dependency law
    check("I: deterministic for fixed now", D.run_model_compatibility(dg, now=_NOW) == res)
    check("I: reports are not truth", all(r["is_truth"] is False for r in res["reports"]))
    bad_imp = [str(p.relative_to(_REPO)) for p in (_REPO / "src" / "teleon" / "digestion").rglob("*.py")
               for line in p.read_text().splitlines() if line.strip().startswith(("import src.baltor", "from src.baltor"))]
    check("I: no src/teleon/digestion module imports src.baltor", not bad_imp, "; ".join(bad_imp))

    print("\n" + ("PASS — check_model_compatibility: the runner reports which models a skill works with (local "
                  "stub=draft_only, credentialed external=production_allowed_after_gate, uncredentialed=eval_only) "
                  "and which it does NOT (specialization mismatch=not_compatible), via the Inference Gateway graph; "
                  "deterministic; output is not truth." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_model_compatibility.py --self-test")
    raise SystemExit(0)
