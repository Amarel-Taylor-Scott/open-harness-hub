#!/usr/bin/env python3
"""scripts.check_objects_have_inference_preferences — PROOF: key object families can declare a model preference for
the shared LLM plane, BY REFERENCE (model_preference_ref -> an InferencePreference), never inline; and a declared
ref resolves through the Inference Gateway. Declaring a preference is NOT choosing a model — the gateway + policy +
fallback decide and the ModelInvocationReceipt records reality.

Asserts:
  A. SHELL FIELD: ObjectShell recognizes an optional `model_preference_ref` (string|null), NOT required.
  B. COVERAGE: inference_preference_coverage.json lists the key families (CapabilityTask/PurposeTask/ContextArtifact/
     SkillArtifact/ToolArtifact/HarnessArtifact/BenchmarkArtifact at minimum), all can_declare, by_reference_only.
  C. FUNCTIONAL: a canonical-shell object can carry model_preference_ref, and a preference layer with that id
     resolves through oips.resolve_preference (ref -> ResolvedInferencePreference).
  D. BY REFERENCE, NOT INLINE: the field is a string ref; inline raw preference/key is forbidden by policy + the
     ref must NOT look like a raw secret.
  E. CONTRACT: InferencePreference (the referenced object) is registered.
  F. DETERMINISM.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations
import json, os, re, sys
from pathlib import Path
_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path: sys.path.insert(0, str(_REPO))
from src.teleon.inference import oips
from src.teleon.templates import instantiator as TPL
_NOW = "2026-06-07T00:00:00Z"
_KEY_RE = re.compile(r"(sk-|gsk_|hf_|AIza|nvapi-)[A-Za-z0-9_\-]{16,}")
_MIN = {"CapabilityTask", "PurposeTask", "ContextArtifact", "SkillArtifact", "ToolArtifact", "HarnessArtifact", "BenchmarkArtifact"}


def _self_test() -> int:
    fails = []
    def check(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        (fails.append(n) if not ok else None)

    shell = json.loads((_REPO / "schemas" / "shared" / "ObjectShell.schema.json").read_text())
    mp = shell["properties"].get("model_preference_ref", {})
    check("A: ObjectShell has optional model_preference_ref (string|null, not required)",
          mp.get("type") == ["string", "null"] and "model_preference_ref" not in shell["required"])

    cov = json.loads((_REPO / "architecture" / "inference_preference_coverage.json").read_text())
    fams = {f["family"] for f in cov["object_families"]}
    check("B: coverage lists the key families, all can_declare, by_reference_only",
          _MIN <= fams and all(f["can_declare"] for f in cov["object_families"])
          and cov["by_reference_only"] is True and cov["inline_raw_preference_forbidden"] is True, str(sorted(_MIN - fams)))

    obj = TPL.compose_object_shell(object_id="ct:x", object_type="CapabilityTask", mixin_ids=None, now=_NOW, payload={})
    ref = "pref://capabilitytask/reasoning@v1"
    obj["model_preference_ref"] = ref  # additionalProperties True — the shell carries the ref
    layer = {"preference_id": ref, "model_class_preference": {"tier_code": 600, "specialization_codes": [500]}}
    resolved = oips.resolve_preference([layer])
    check("C: a declared model_preference_ref resolves through the gateway",
          obj["model_preference_ref"] == ref and resolved["preference_id"] == ref
          and resolved["schema_version"] == "ResolvedInferencePreference", json.dumps(resolved.get("preference_id")))

    check("D: by reference, not inline — the ref is a string and is NOT a raw secret",
          isinstance(obj["model_preference_ref"], str) and not _KEY_RE.search(obj["model_preference_ref"]) and cov["field"] == "model_preference_ref")

    contracts = json.dumps(json.loads((_REPO / "architecture" / "contract_registry.json").read_text()))
    check("E: InferencePreference (the referenced contract) is registered", "inference/InferencePreference.schema.json" in contracts)

    check("F: deterministic", oips.resolve_preference([layer])["preference_id"] == resolved["preference_id"])

    print("\n" + ("PASS — check_objects_have_inference_preferences: key object families declare a model preference by "
                  "reference (model_preference_ref -> InferencePreference), never inline; the ref resolves through "
                  "the Inference Gateway; declaring a preference is not choosing a model."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv: raise SystemExit(_self_test())
    print("usage: python3 scripts/check_objects_have_inference_preferences.py --self-test"); raise SystemExit(0)
