#!/usr/bin/env python3
"""scripts.check_teleon_lift — PROOF: Teleon Lift discovers/models existing cloud functions + K8s workloads and
lifts them into PurposeTask drafts WITHOUT taking over production, end-to-end and offline.

Asserts:
  A. END-TO-END: the offline inventory (canned K8s + Lambda) lifts every workload into a full LiftResult
     (workload · runtime_profile · trigger/dependency graphs · purpose_draft · capability_draft · adoption_plan).
  B. NO SECRET LEAK: env-var VALUES never survive normalization — only key NAMES; the canned secret markers
     never appear anywhere in an ImportedWorkload.
  C. INTERPRETATION MAP: Job→kubernetes-job/capability_task_implementation · CronJob→cron-task/scheduled_trigger ·
     Deployment→kubernetes-worker/long_running_worker_or_service · Lambda→cloud-function/capability_task_implementation.
  D. CTS-1 BINDABLE: every non-null runtime_class_guess is in the capability_runtime_classes vocabulary.
  E. INFERRED PURPOSE IS A DRAFT: purpose_draft.requires_human_review is ALWAYS true; confidence ∈ [0,1];
     inferred_from non-empty; capability_draft.requires_human_review true; allowed classes ⊆ vocab ∪ {human-review}.
  F. BASELINE = ROLLBACK: the legacy workload becomes the baseline ImplementationCandidate (status
     imported_baseline, is_rollback_target) which IS rollback_target == purpose_draft.baseline_implementation_id;
     a freshly lifted plan is NOT manageable (may_manage false).
  G. ADOPTION LADDER: entry/current mode is `discover` (read-only); ladder is 6 modes 0..5; reads-only for 0-2,
     affects-production only for 4-5.
  H. MANAGED GATE (safety): set_mode to a managed mode WITHOUT a human-confirmed purpose is BLOCKED (no
     production effect); WITH confirmation it is allowed (may_manage true); a read-only mode is always allowed;
     an unknown mode is blocked.
  I. RUNTIME PROFILE never fabricated: with observations → source 'observed' + p95; without → 'unavailable' +
     nulls; the success-criteria latency bound is derived from the observed p95.
  J. DETERMINISM: lifting the same workload twice with the same imported_at yields identical output.
  K. SCHEMA CONFORMANCE: workload/profile/purpose_draft/capability_draft/adoption_plan conform to their .v1
     schemas (required present · no extra keys · enum/const honored).
  L. CONNECTOR SEAM: offline connectors are the default; the live connector is a labelled seam that raises with
     the real provider API; the whole pipeline runs with no network.
  M. DEPENDENCY LAW (local): no module under src/teleon/lift imports src.baltor.

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

from src.teleon import lift
from src.teleon.lift import adoption, connectors, model, normalize, pipeline

_IMPORTED_AT = "2026-06-06T00:00:00Z"  # injected — determinism
_SECRET_MARKERS = ("REDACTME", "SECRET")
_SCHEMA_DIR = _REPO / "schemas" / "teleon" / "lift"


def _load_schema(name: str) -> dict:
    return json.loads((_SCHEMA_DIR / f"{name}.schema.json").read_text())


def _validate(obj: dict, schema: dict) -> list[str]:
    """Return a list of schema violations (required missing · extra key · enum/const mismatch). [] == valid."""
    errs: list[str] = []
    props = schema.get("properties", {})
    for r in schema.get("required", []):
        if r not in obj:
            errs.append(f"missing required {r}")
    if schema.get("additionalProperties") is False:
        for k in obj:
            if k not in props:
                errs.append(f"extra key {k}")
    for k, v in obj.items():
        spec = props.get(k, {})
        if "enum" in spec and v not in spec["enum"]:
            errs.append(f"{k}={v!r} not in enum {spec['enum']}")
        if "const" in spec and v != spec["const"]:
            errs.append(f"{k}={v!r} != const {spec['const']!r}")
    return errs


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    vocab = model.runtime_class_vocabulary()
    schemas = {n: _load_schema(n) for n in ("ImportedWorkload.v1", "RuntimeProfile.v1", "PurposeTaskDraft.v1",
                                            "CapabilityTaskDraft.v1", "AdoptionPlan.v1")}

    # observations only for the invoice job → exercises observed vs unavailable profiles
    obs = {"invoice-extraction": {"observed_window": "14d", "invocations": 124322, "p50_latency_ms": 4300,
                                  "p95_latency_ms": 48000, "error_rate": 0.027, "timeout_rate": 0.018,
                                  "estimated_cost_usd": 412.55}}
    results = lift.lift_inventory(connectors.offline_connectors(), imported_at=_IMPORTED_AT, observations_by_name=obs)

    # A. end-to-end
    check("A: offline inventory lifted all 4 canned workloads", len(results) == 4, str(len(results)))
    for r in results:
        complete = all([r.workload, r.runtime_profile, r.trigger_graph, r.dependency_graph, r.purpose_draft,
                        r.capability_draft, r.adoption_plan])
        check(f"A: {r.workload['native_name']} has a complete LiftResult", complete)

    by_name = {r.workload["native_name"]: r for r in results}

    # B. no secret leak
    for r in results:
        blob = json.dumps(r.workload)
        leak = [m for m in _SECRET_MARKERS if m in blob]
        check(f"B: {r.workload['native_name']} leaks no secret values", not leak, f"found {leak}")
    inv = by_name["invoice-extraction"].workload
    check("B: invoice job kept env KEY names (not values)",
          "DATABASE_URL" in inv["env_redacted_keys"] and "OPENAI_API_KEY" in inv["env_redacted_keys"])

    # C. interpretation map
    cases = {"invoice-extraction": ("kubernetes-job", "capability_task_implementation"),
             "nightly-fact-refresh": ("cron-task", "scheduled_trigger"),
             "risk-summary-api": ("kubernetes-worker", "long_running_worker_or_service"),
             "process-invoice-prod": ("cloud-function", "capability_task_implementation")}
    for nm, (rc, interp) in cases.items():
        w = by_name[nm].workload
        check(f"C: {nm} → {rc}/{interp}", w["runtime_class_guess"] == rc and w["interpretation"] == interp,
              f'{w["runtime_class_guess"]}/{w["interpretation"]}')

    # D. CTS-1 bindable
    for r in results:
        g = r.workload["runtime_class_guess"]
        check(f"D: {r.workload['native_name']} runtime_class_guess in vocabulary", g is None or g in vocab, str(g))

    # E. inferred purpose is a draft
    for r in results:
        pd, cd = r.purpose_draft, r.capability_draft
        check(f"E: {pd['name']} purpose is a DRAFT (requires_human_review)", pd["requires_human_review"] is True)
        check(f"E: {pd['name']} confidence in [0,1] + inferred_from non-empty",
              0.0 <= pd["confidence"] <= 1.0 and len(pd["inferred_from"]) >= 1, str(pd["confidence"]))
        allowed_ok = all(c in vocab or c == "human-review" for c in cd["allowed_runtime_classes"])
        check(f"E: {cd['name']} capability draft human-gated + allowed classes valid",
              cd["requires_human_review"] is True and allowed_ok, str(cd["allowed_runtime_classes"]))

    # F. baseline = rollback
    for r in results:
        base = r.adoption_plan["baseline_implementation"]
        ok = (base["status"] == "imported_baseline" and base["is_rollback_target"] is True
              and r.adoption_plan["rollback_target"] == base["impl_id"]
              and base["impl_id"] == r.purpose_draft["baseline_implementation_id"])
        check(f"F: {r.workload['native_name']} legacy workload is the rollback baseline", ok, json.dumps(base))
        check(f"F: {r.workload['native_name']} fresh plan is NOT manageable", r.adoption_plan["may_manage"] is False)

    # G. adoption ladder
    plan = by_name["invoice-extraction"].adoption_plan
    check("G: entry+current mode is discover (read-only)",
          plan["entry_mode"] == "discover" and plan["current_mode"] == "discover" and plan["reads_only"] is True
          and plan["affects_production"] is False)
    ladder = plan["ladder"]
    check("G: ladder is 6 modes ordered 0..5", [m["level"] for m in ladder] == [0, 1, 2, 3, 4, 5])
    check("G: levels 0-2 read-only, 3-5 not", all(ladder[i]["reads_only"] for i in (0, 1, 2)) and not any(ladder[i]["reads_only"] for i in (3, 4, 5)))
    check("G: affects_production only at 4-5", (not ladder[3]["affects_production"]) and ladder[4]["affects_production"] and ladder[5]["affects_production"])

    # H. managed gate — the key safety test
    blocked = adoption.set_mode(plan, "full_managed")
    check("H: managed mode WITHOUT confirmed purpose is BLOCKED",
          "blocked" in blocked and blocked["current_mode"] == "discover" and blocked["affects_production"] is False
          and blocked["may_manage"] is False, json.dumps({k: blocked.get(k) for k in ("blocked", "current_mode")}))
    allowed = adoption.set_mode(plan, "full_managed", human_confirmed_purpose=True)
    check("H: managed mode WITH confirmed purpose is allowed",
          "blocked" not in allowed and allowed["current_mode"] == "full_managed" and allowed["may_manage"] is True
          and allowed["affects_production"] is True and adoption.may_manage(allowed) is True)
    obsmode = adoption.set_mode(plan, "observe")
    check("H: a read-only mode (observe) is allowed without confirmation",
          "blocked" not in obsmode and obsmode["current_mode"] == "observe" and obsmode["may_manage"] is False)
    unknown = adoption.set_mode(plan, "take_over_everything")
    check("H: unknown mode is blocked", "blocked" in unknown)

    # I. runtime profile never fabricated
    obs_profile = by_name["invoice-extraction"].runtime_profile
    check("I: observed workload → source 'observed' + p95", obs_profile["source"] == "observed" and obs_profile["p95_latency_ms"] == 48000)
    unobs_profile = by_name["risk-summary-api"].runtime_profile
    check("I: unobserved workload → source 'unavailable' + null metrics",
          unobs_profile["source"] == "unavailable" and unobs_profile["p95_latency_ms"] is None)
    sc = by_name["invoice-extraction"].purpose_draft["success_criteria_draft"]
    check("I: success-criteria latency bound derived from observed p95 (48000*1.25=60000)",
          any("p95_latency_ms <= 60000" in s for s in sc), str(sc))

    # J. determinism
    native = connectors.CannedLambdaConnector().scan()[0]
    a = pipeline.lift_workload(native, imported_at=_IMPORTED_AT).as_dict()
    b = pipeline.lift_workload(native, imported_at=_IMPORTED_AT).as_dict()
    check("J: lifting the same workload twice is identical (deterministic)", a == b)

    # K. schema conformance
    for r in results:
        for obj, sname in ((r.workload, "ImportedWorkload.v1"), (r.runtime_profile, "RuntimeProfile.v1"),
                           (r.purpose_draft, "PurposeTaskDraft.v1"), (r.capability_draft, "CapabilityTaskDraft.v1"),
                           (r.adoption_plan, "AdoptionPlan.v1")):
            errs = _validate(obj, schemas[sname])
            check(f"K: {r.workload['native_name']} {sname} conforms", not errs, "; ".join(errs[:3]))

    # L. connector seam
    offline = connectors.offline_connectors()
    check("L: offline connectors are the default (k8s + aws)", {c.source for c in offline} == {"k8s", "aws"})
    seam = connectors.LiveConnectorSeam("aws")
    raised = False
    try:
        seam.scan()
    except NotImplementedError as e:
        raised = "ListFunctions" in str(e)
    check("L: live connector is a labelled seam citing the real API (ListFunctions)", raised)

    # M. dependency law (local) — no src.baltor import under src/teleon/lift
    bad = []
    for py in sorted((_REPO / "src" / "teleon" / "lift").rglob("*.py")):
        for line in py.read_text().splitlines():
            s = line.strip()
            if (s.startswith("import src.baltor") or s.startswith("from src.baltor")):
                bad.append(str(py.relative_to(_REPO)))
    check("M: no src/teleon/lift module imports src.baltor (dependency law)", not bad, "; ".join(bad))

    print("\n" + ("PASS — check_teleon_lift: Teleon Lift lifts canned K8s + Lambda workloads end-to-end into "
                  "PurposeTask drafts offline — secrets stripped to key-names, runtime classes CTS-1-bindable, "
                  "inferred purpose always human-gated, the legacy workload preserved as the rollback baseline, "
                  "adoption read-only-first with a managed-mode gate, profiles never fabricated, deterministic, "
                  "schema-conformant, connectors are offline-default with labelled live seams."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_teleon_lift.py --self-test")
    raise SystemExit(0)
