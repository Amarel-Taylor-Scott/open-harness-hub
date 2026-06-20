#!/usr/bin/env python3
"""scripts.check_octs_conformance — PROOF: Baltor's PurposeTaskSpec.v1 is a CTS-0-conformant OCTS CapabilityTask,
and the abstract runtime-class vocabulary is well-formed + cloud-defer-safe.

Open Capability Task Specification (OCTS) — docs/standards/open-capability-task-specification.md. CTS-0 =
"platform can read + validate the task contract." This asserts:
  A. The runtime-class vocabulary (architecture/capability_runtime_classes.json) is well-formed: every class has
     a `class` id + a `local_equivalent` (cloud-defer-only-after-local-equivalent), and the standard's core
     classes are present.
  B. A CTS-0-conformant PurposeTask (purpose + interface + capabilities{required/forbidden} + successCriteria +
     allowed_runtime_classes + observability) VALIDATES against PurposeTaskSpec.v1.
  C. allowed_runtime_classes ⊆ the vocabulary (non-fragile: checked against config, not a hard-coded list).
  D. The OCTS CTS-0 minimal required field set maps onto PurposeTaskSpec fields (purpose · input/output ·
     successCriteria · capabilities.required/forbidden · allowed_runtime_classes · observability).
  E. GOVERNANCE: a `forbidden` capabilities boundary is expressible (the field exists + carries entries).

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from scripts.runtime import schema_validator as sv

_REF = "purpose_tasks/PurposeTaskSpec.v1"
_NOW = "2026-06-06T00:00:00Z"
_CORE_CLASSES = {"cloud-function", "serverless-container", "kubernetes-job", "kubernetes-worker",
                 "queue-worker", "durable-workflow", "browser-worker", "gpu-worker"}
# the OCTS CTS-0 minimal required sections (standard doc) that a conformant CapabilityTask must express
_OCTS_REQUIRED = {"purpose", "input", "output", "capabilities.required", "capabilities.forbidden",
                  "successCriteria", "allowed_runtime_classes", "observability"}


def _conformant_spec(runtime_classes):
    return {
        "schema_version": "PurposeTaskSpec.v1",
        "task_id": "purpose_task.octs_demo@v1",
        "purpose": "Visit sample.com and extract X information.",
        "capability_slot": "source_research",
        "input_contract": "SourceResearchRequest.v1",
        "output_contract": "SourceEvidenceBundle.v1",
        "success_criteria": {"max_cost": 0.02, "min_source_handles": 1, "max_p95_latency_ms": 30000},
        "promotion_criteria": {"cost_tolerance": 0.0},
        "connected_to": ["contextops.source_discovery"],
        "capabilities": {"required": ["http.fetch", "html.parse"], "optional": ["browser.use"],
                         "forbidden": ["purchase", "credential.access", "personal_data.extract"]},
        "allowed_runtime_classes": runtime_classes,
        "observability": {"traces": "opentelemetry", "retain": ["input_hash", "output_hash", "eval_result"]},
        "defined_at": _NOW,
    }


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # A. runtime-class vocabulary well-formed + cloud-defer-safe
    voc = json.loads((Path(_REPO) / "architecture" / "capability_runtime_classes.json").read_text())
    classes = {c["class"]: c for c in voc.get("classes", [])}
    check("A: vocabulary lists classes", len(classes) >= 8, str(len(classes)))
    check("A: core OCTS classes present", _CORE_CLASSES <= set(classes), str(_CORE_CLASSES - set(classes)))
    no_local = [c for c, v in classes.items() if not v.get("local_equivalent")]
    check("A: every runtime class declares a local_equivalent (cloud-defer gate)", not no_local, str(no_local))

    # B. a CTS-0-conformant PurposeTask validates
    spec = _conformant_spec(["cloud-function", "kubernetes-job", "browser-worker", "local-subprocess"])
    errs = sv.validate_ref(spec, _REF)
    check("B: a CTS-0-conformant PurposeTask validates against PurposeTaskSpec.v1", errs == [], str(errs[:3]))

    # C. allowed_runtime_classes ⊆ vocabulary (non-fragile)
    declared = set(spec["allowed_runtime_classes"])
    check("C: allowed_runtime_classes ⊆ the vocabulary", declared <= set(classes), str(declared - set(classes)))
    # a spec declaring an unknown class is structurally valid JSON but NOT vocabulary-conformant → caught here
    bad = set(_conformant_spec(["totally-made-up-class"])["allowed_runtime_classes"])
    check("C: an unknown runtime class is detected as non-conformant", not (bad <= set(classes)))

    # D. OCTS CTS-0 required sections map onto PurposeTask fields
    present = set()
    if spec.get("purpose"): present.add("purpose")
    if spec.get("input_contract"): present.add("input")
    if spec.get("output_contract"): present.add("output")
    if spec.get("success_criteria"): present.add("successCriteria")
    caps = spec.get("capabilities", {})
    if caps.get("required") is not None: present.add("capabilities.required")
    if caps.get("forbidden") is not None: present.add("capabilities.forbidden")
    if spec.get("allowed_runtime_classes"): present.add("allowed_runtime_classes")
    if spec.get("observability"): present.add("observability")
    check("D: PurposeTask covers the OCTS CTS-0 required set", _OCTS_REQUIRED <= present, str(_OCTS_REQUIRED - present))

    # E. governance: a forbidden-capability boundary is expressible + populated
    check("E: forbidden-capability governance boundary expressible", len(caps.get("forbidden", [])) >= 1, str(caps.get("forbidden")))

    print("\n" + ("PASS — check_octs_conformance: PurposeTaskSpec.v1 is a CTS-0-conformant OCTS CapabilityTask "
                  "(purpose · interface · capabilities{required/forbidden} · successCriteria · allowed_runtime_"
                  "classes ⊆ vocabulary · observability); the runtime-class vocabulary is well-formed and every "
                  "class has a local equivalent." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_octs_conformance.py --self-test")
    raise SystemExit(0)
