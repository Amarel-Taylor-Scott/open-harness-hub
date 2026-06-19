#!/usr/bin/env python3
"""scripts.teleon_preseed_capabilities — pre-seed Teleon with capability-DEFINED units across the full
execution-style spectrum, and PROVE the seed is coherent.

Each unit in architecture/teleon_capability_seed.json is a pure PurposeTaskSpec.v1 (declared by intent +
capability_slot + stable input->output contract, NOT by per-task code). This module:
  - validates every unit against the PurposeTaskSpec.v1 schema (+ the model-built eval_suite rule),
  - classifies each unit's escalation tier with the REAL ladder (src/teleon/exploration/ladder.py) and confirms
    it matches the declared tier (template T0 -> deterministic T1 -> model T2 -> open-ended T3),
  - provisions an implementation BY CAPABILITY (priority-ordered registry; provision-by-capability, not code),
  - and surfaces the SELF-IMPROVEMENT descent: each unit's adaptation_target is a cheaper rung (non-det -> det)
    Teleon drives it toward to cut cost, never an autonomous escalation UP, never an ENDS change.

The registry handlers here are explicit DEMONSTRATION stubs (output prefixed "<demo>") so provision/run are
exercised offline; the REAL implementations are the skills/tools/showcase pipelines bound by priority. Nothing
serves truth (serves_truth=false on every handler result). Deterministic, stdlib + jsonschema.

CLI: python3 scripts/teleon_preseed_capabilities.py --self-test | --list | --json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_SEED_PATH = _REPO / "architecture" / "teleon_capability_seed.json"
_SCHEMA_PATH = _REPO / "schemas" / "purpose_tasks" / "PurposeTaskSpec.v1.schema.json"


def _seed() -> dict:
    return json.loads(_SEED_PATH.read_text(encoding="utf-8"))


def _task_class_for(unit: dict):
    """Project a seed unit's model-INDEPENDENT ladder_signals onto the escalation ladder's TaskClass, so the
    REAL ladder (not this module) decides the tier."""
    from src.teleon.exploration.ladder import TaskClass
    sig = unit.get("ladder_signals", {})
    spec = unit["spec"]
    return TaskClass(
        task_id=spec["task_id"], intent=spec.get("purpose", ""), tenant_id="seed",
        task_class=sig.get("task_class", "routine"),
        template_match=bool(sig.get("template_match")),
        deterministic_primitive=bool(sig.get("deterministic_primitive")),
        change_type=sig.get("change_type"))


def _demo_handler(unit: dict):
    """A DEMONSTRATION impl handler (output prefixed '<demo>') so provision-by-capability + the hot path run
    offline. Real impls (skills/tools/showcases) replace this behind the same capability_slot by priority."""
    spec = unit["spec"]

    def handler(_input_snapshot):
        return {"output": f"<demo> {spec['purpose']}", "output_contract": spec["output_contract"],
                "cost": 0.0, "latency_ms": 1, "error": None, "source_handles": spec.get("source_dependencies", []),
                "impl_id": f"demo.{spec['capability_slot']}@v1", "serves_truth": False}
    return handler


def preseed() -> dict:
    """Provision every seeded capability unit by capability and return the registry view + the descent plan."""
    from src.teleon.exploration.ladder import escalation_decision
    from src.teleon.purpose_tasks.purpose_task import provision

    units = _seed()["units"]
    registry = {u["spec"]["capability_slot"]: [{"impl_id": f"demo.{u['spec']['capability_slot']}@v1",
                                                "priority": 100, "handler": _demo_handler(u)}] for u in units}
    out = []
    for u in units:
        spec = u["spec"]
        provisioned = provision(spec, registry)
        tier = escalation_decision(_task_class_for(u)).tier
        out.append({
            "variety": u["variety"], "task_id": spec["task_id"], "capability_slot": spec["capability_slot"],
            "build_mode": spec.get("build_mode"), "declared_tier": u["ladder_tier"], "classified_tier": tier,
            "current_impl_id": provisioned["current_impl_id"],
            "adaptation_target": u["adaptation_target"], "cost_rationale": u["cost_rationale"],
            "allowed_runtime_classes": spec.get("allowed_runtime_classes", []),
            "forbidden": (spec.get("capabilities") or {}).get("forbidden", []),
            "resolved_resources": resolve_resources(u),
        })
    return {"count": len(out), "registry_slots": sorted(registry), "units": out}


#: illustrative per-call costs (USD) for the descent demonstration: a model call vs a distilled deterministic
#: rule. The adapt()/promotion/rollback ENGINE is REAL; these two impls stand in for "the model" and "the rule
#: the determinism factory distilled from verified traces," so the descent runs offline + deterministically.
_MODEL_CALL_COST = 0.05
_DISTILLED_RULE_COST = 0.0
_DESCENT_ANSWER = "10 business days"  # the gated answer both impls must agree on (the CFPB reference fact)


def demonstrate_descent(variety: str = "model") -> dict:
    """Run Teleon's REAL adapt() engine to show a capability DESCEND non-deterministic -> deterministic: a
    model-tier impl is the current hot path; a distilled deterministic rule (cost ~0, EQUIVALENT output) is the
    candidate; adapt() runs them side-by-side through the Parallel-Path Engine and promotes the rule ONLY on a
    passing PathPromotionDecision (equivalent + not-more-expensive), keeping the model as a reversible
    rollback_target. This EXECUTES the cost self-improvement the seed's adaptation_target only declares."""
    from src.teleon.purpose_tasks.purpose_task import adapt, provision, run_current
    unit = next(u for u in _seed()["units"] if u["variety"] == variety)
    spec = unit["spec"]
    slot = spec["capability_slot"]

    def _impl(impl_id: str, cost: float):
        def handler(_inp):
            return {"output": _DESCENT_ANSWER, "output_contract": spec["output_contract"], "cost": cost,
                    "latency_ms": 1, "error": None, "source_handles": ["ctx://ecfr/reg-e"],
                    "impl_id": impl_id, "serves_truth": False}
        return handler

    model_id, rule_id = f"model.{slot}@v1", f"distilled_rule.{slot}@v1"
    registry = {slot: [
        {"impl_id": model_id, "priority": 100, "handler": _impl(model_id, _MODEL_CALL_COST)},
        {"impl_id": rule_id, "priority": 90, "handler": _impl(rule_id, _DISTILLED_RULE_COST)},
    ]}
    prov = provision(spec, registry)  # current = the model (the original, highest-priority impl)
    snap = {"x": "Reg E error-resolution deadline?"}
    before = run_current(prov, registry, snap)
    res = adapt(prov, registry, snap, now="descent-demo",
                promotion_criteria={"cost_tolerance": float((spec.get("promotion_criteria") or {}).get("cost_tolerance", 0.25))},
                candidate_impl_id=rule_id)
    after_spec = res["spec"]
    after = run_current(after_spec, registry, snap)
    return {"task_id": spec["task_id"], "capability_slot": slot, "variety": variety,
            "before_impl": prov["current_impl_id"], "after_impl": after_spec["current_impl_id"],
            "promoted": res["promoted"], "rollback_target": after_spec.get("rollback_target"),
            "before_cost": before["cost"], "after_cost": after["cost"],
            "answer_before": before["output"], "answer_after": after["output"],
            "equivalent": before["output"] == after["output"]}


def _arch(name: str) -> dict:
    """Read a SHARED data registry (architecture/<name>). Data only — never a src.baltor import (Teleon is the
    logic; these registries are the resources). Keeps the resolver dependency-law-safe."""
    return json.loads((_REPO / "architecture" / name).read_text(encoding="utf-8"))


def _backend_cost(pricebook: dict, backend: str, *, est_seconds: float = 1.0) -> float:
    """A rough per-call cost (relative units) for a backend from the pricebook resource: request + duration*sec."""
    pb = pricebook.get(backend, {})
    return round(float(pb.get("request_cost", 0.0)) + float(pb.get("duration_cost_per_s", 0.0)) * est_seconds, 4)


#: which RESOURCE-holding service each declared resource kind integrates with (Teleon = logic; these hold details).
_RESOURCE_SERVICES = {
    "templates": "architecture/template_catalog.json",
    "skill_slots": "architecture/skill_to_tool_promotion_catalog.json",
    "tool_slots": "architecture/context_engineering_tool_catalog.json",
}


def resolve_resources(unit: dict) -> dict:
    """Integrate a capability unit with the RESOURCE-holding services to get useful details. Teleon owns the LOGIC
    (ladder/provision/adapt/descent); these registries hold the resources. Reads SHARED data registries only
    (architecture/*.json) — never imports src.baltor (dependency-law-safe). Per unit returns: the runtime PROFILE
    + pricebook COST (local floor + the cheapest cloud candidate) for each allowed runtime class, the catalog
    services its skill/tool/template slots integrate with, and the source-authority service its source
    dependencies are governed by."""
    spec = unit["spec"]
    profiles = {p["runtime_class"]: p for p in _arch("execution_environment_profiles.json")["profiles"]}
    pricebook = _arch("execution_backend_pricebook.json").get("backends", {})

    runtime = []
    for rc in spec.get("allowed_runtime_classes", []):
        prof = profiles.get(rc, {})
        pp = prof.get("policy_preferences", {})
        local_backend = prof.get("default_local_backend", "")
        cloud = next((b for b in prof.get("preferred_candidate_backends", []) if b in pricebook), None)
        runtime.append({
            "runtime_class": rc, "resolved": bool(prof),
            "default_local_backend": local_backend, "local_cost": _backend_cost(pricebook, local_backend),
            "cloud_backend": cloud, "cloud_cost": _backend_cost(pricebook, cloud) if cloud else None,
            "sla_policy": pp.get("default_sla_policy_id"), "egress_route": pp.get("egress_route_policy_id"),
            "autotune": prof.get("autotuning_policy_id"),
        })

    res = spec.get("resources", {}) or {}
    slot_integrations = {kind: {"refs": res.get(kind), "resource_service": svc}
                         for kind, svc in _RESOURCE_SERVICES.items() if res.get(kind)}
    governance = {}
    if spec.get("source_dependencies"):
        governance = {"source_dependencies": spec["source_dependencies"],
                      "resource_service": "architecture/source_authority_registry.json",
                      "detail": "earned source authority (tier/rank/basis) resolved by the source-authority service at runtime"}
    # the unit's cheapest runnable cost (the local floor) + the cloud cost it would pay un-distilled
    local_floor = min((r["local_cost"] for r in runtime), default=0.0)
    cloud_costs = [r["cloud_cost"] for r in runtime if r["cloud_cost"] is not None]
    return {"runtime": runtime, "local_floor_cost": local_floor,
            "cloud_cost": min(cloud_costs) if cloud_costs else None,
            "resource_slots": slot_integrations, "governance": governance}


#: SLA-policy-id duration suffix -> seconds. The latency budget is DECLARED in each profile's
#: default_sla_policy_id (e.g. "interactive_30s", "batch_15m", "offline_24h"); we read it, never re-type it.
_SLA_UNIT_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400}
_SLA_DEFAULT_SECONDS = 120.0  # an SLA id with no parseable duration -> a neutral "standard" budget (documented)


def _sla_seconds(sla_policy_id) -> float:
    """The latency budget (seconds) encoded in a profile's default_sla_policy_id ('interactive_30s' -> 30,
    'standard_2m' -> 120, 'batch_15m' -> 900, 'offline_24h' -> 86400). Real declared signal, not a magic number."""
    import re
    m = re.search(r"_(\d+)([smhd])$", str(sla_policy_id or ""))
    return float(m.group(1)) * _SLA_UNIT_SECONDS[m.group(2)] if m else _SLA_DEFAULT_SECONDS


def select_placement(unit: dict, objective) -> dict:
    """Choose WHICH allowed runtime class to run a capability unit on, under a CapabilityObjective — the objective
    layer applied to the unit's REAL resources. Candidates are the unit's allowed_runtime_classes; each is measured
    by its REAL production cost (the pricebook cloud-backend cost where the class runs on cloud, else its local
    floor) and its REAL latency budget (the profile's SLA policy). A tighter SLA generally costs more, so
    minimize_latency and minimize_cost pick DIFFERENT placements. Returns the objective layer's full, deterministic
    SelectionTrace (serves_truth False). Placement varies cost + latency only (determinism/llm/accuracy are impl
    properties, equal across placements -> they don't distort the choice)."""
    from src.teleon.objectives import MetricVector, ObjectiveError, select
    runtime = resolve_resources(unit)["runtime"]
    if not runtime:
        raise ObjectiveError(f"unit {unit['spec']['task_id']!r} has no resolvable runtime class to place on")
    candidates = [
        (r["runtime_class"],
         MetricVector(cost=float(r["cloud_cost"] if r["cloud_cost"] is not None else r["local_cost"]),
                      latency=_sla_seconds(r["sla_policy"])))
        for r in runtime
    ]
    return select(candidates, objective)


def _self_test() -> int:
    from jsonschema import Draft202012Validator

    from src.teleon.exploration.ladder import escalation_decision
    from src.teleon.purpose_tasks.purpose_task import eval_suite_for, provision, run_current

    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    seed = _seed()
    units = seed["units"]
    ladder_order = seed["ladder_order"]
    validator = Draft202012Validator(json.loads(_SCHEMA_PATH.read_text(encoding="utf-8")))

    ck("the seed covers EVERY execution-style variety in ladder order",
       [u["variety"] for u in units] == ladder_order and len(units) == 8, str([u["variety"] for u in units]))

    for u in units:
        spec, v = u["spec"], u["variety"]
        ck(f"{v}: spec is a valid PurposeTaskSpec.v1 (capability-defined, not code)",
           validator.is_valid(spec), str([e.message for e in validator.iter_errors(spec)][:1]))
        # model-built units must carry the eval_suite that DEFINES done (the spec's own rule, via eval_suite_for)
        if str(spec.get("build_mode")) == "model":
            suite = eval_suite_for(spec)
            ck(f"{v}: model-built unit carries a non-empty eval_suite (benchmark-as-spec)",
               bool(suite) and len(suite.get("examples", [])) >= 1, str(suite))
        # the REAL escalation ladder classifies it at the declared tier
        ck(f"{v}: the real escalation ladder classifies it at the declared tier T{u['ladder_tier']}",
           escalation_decision(_task_class_for(u)).tier == u["ladder_tier"])
        # SELF-IMPROVEMENT: the adaptation target is a CHEAPER (or equal) rung — never an autonomous escalation up
        ck(f"{v}: adaptation_target T{u['adaptation_target']} <= current tier T{u['ladder_tier']} (non-det -> det descent)",
           u["adaptation_target"] <= u["ladder_tier"])
        # the governance boundary: every unit declares forbidden capabilities it may never cross
        ck(f"{v}: declares a forbidden-capabilities boundary", bool((spec.get("capabilities") or {}).get("forbidden")))

    # ladder order is cheapest -> dearest (tiers non-decreasing down the list)
    tiers = [u["ladder_tier"] for u in units]
    ck("units are seeded cheapest -> dearest (tiers non-decreasing)", tiers == sorted(tiers), str(tiers))

    # at least the two expensive varieties (model T2, open-ended T3) DESCEND toward deterministic (the moat claim)
    descenders = [u["variety"] for u in units if u["adaptation_target"] < u["ladder_tier"]]
    ck("the expensive (model + open-ended) units declare a descent toward deterministic (cost self-improvement)",
       "model" in descenders and "open_ended" in descenders, str(descenders))

    # provision-by-capability works for EVERY unit, and the hot path never serves truth
    pre = preseed()
    ck("every unit provisions an implementation BY CAPABILITY (priority-ordered, not code)",
       pre["count"] == 8 and all(u["current_impl_id"] for u in pre["units"]))
    reg = {u["spec"]["capability_slot"]: [{"impl_id": f"demo.{u['spec']['capability_slot']}@v1",
           "priority": 100, "handler": _demo_handler(u)}] for u in units}
    sample = units[1]  # the fully-deterministic unit
    prov = provision(sample["spec"], reg)
    res = run_current(prov, reg, {"x": "Section 1005.11: resolve within 10 business days."})
    ck("a provisioned hot-path run returns a candidate, never served truth (serves_truth=false)",
       res.get("serves_truth") is False and str(res.get("output", "")).startswith("<demo>"), str(res)[:120])

    # the open-ended (T3) unit is the only one requiring a human boundary + a sandboxed candidate-only safety class
    oe = next(u for u in units if u["variety"] == "open_ended")
    ck("the open-ended worker unit requires a human boundary + sandboxed candidate-only safety",
       oe["spec"]["success_criteria"].get("requires_human_boundary") is True
       and oe["spec"].get("safety_class") == "human_approval_required")

    # THE LIVE DESCENT (cost self-improvement on the REAL adapt() engine, not just a declared adaptation_target):
    # a model-tier capability is descended to a distilled deterministic rule — promoted ONLY because it is
    # EQUIVALENT and cheaper, with the model kept as a reversible rollback_target.
    d = demonstrate_descent("model")
    ck("descent: Teleon PROMOTES the distilled deterministic rule over the model (real adapt() engine)",
       d["promoted"] is True and d["before_impl"].startswith("model") and d["after_impl"].startswith("distilled_rule"),
       str(d))
    ck("descent: the promotion is COST-REDUCING (model call -> ~0 deterministic)",
       d["after_cost"] < d["before_cost"] and d["after_cost"] == 0.0, f"{d['before_cost']} -> {d['after_cost']}")
    ck("descent: the promoted rule is EQUIVALENT (same gated answer) — never a cheaper-but-wrong swap",
       d["equivalent"] and d["answer_after"] == _DESCENT_ANSWER)
    ck("descent: the model is kept as a reversible rollback_target (promotion is never one-way)",
       bool(d["rollback_target"]) and d["rollback_target"].startswith("model"))

    # RESOURCE INTEGRATION: Teleon (the LOGIC) pulls useful details from the resource-holding services.
    for u in units:
        rr = resolve_resources(u)
        ck(f"{u['variety']}: every runtime class resolves to a real profile + pricebook cost (runtime+cost resources)",
           bool(rr["runtime"]) and all(r["resolved"] and r["local_cost"] is not None for r in rr["runtime"]),
           str(rr["runtime"])[:120])
    ck("resource integration surfaces a REAL cloud cost from the pricebook (what un-distilled execution would cost)",
       any((resolve_resources(u)["cloud_cost"] or 0) > 0 for u in units))
    ck("skill/tool/template units name their catalog resource service (integration point)",
       len([u for u in units if resolve_resources(u)["resource_slots"]]) >= 3)
    ck("source-dependent units integrate with the source-authority service for earned-authority detail",
       len([u for u in units if resolve_resources(u)["governance"]]) >= 3)

    print("\n" + ("PASS - teleon_preseed_capabilities: 8 capability-DEFINED units span the full spectrum "
                  "(template -> deterministic -> det+tool -> skill -> tool -> skill+tool -> model -> open-ended), "
                  "each a valid PurposeTaskSpec.v1 classified at its tier by the real ladder, provisioned by "
                  "capability; nothing serves truth; the open-ended worker stays a sandboxed, human-bounded "
                  "candidate; AND the non-det -> det descent is DEMONSTRATED on the real adapt() engine — a model "
                  "capability is promoted to an equivalent, cheaper deterministic rule with the model kept as a "
                  "reversible rollback_target (the cost self-improvement, executed not just declared)."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Pre-seed Teleon with capability-defined units across the spectrum.")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--list", action="store_true")
    p.add_argument("--descent", action="store_true", help="run the live model->deterministic descent on the real adapt() engine")
    p.add_argument("--resources", action="store_true", help="show each unit's resolved resource details (runtime profile, cost, catalogs, source-authority)")
    p.add_argument("--objective", metavar="PRESET", help="show each unit's objective-driven placement (e.g. minimize_cost | minimize_latency | balanced)")
    p.add_argument("--json", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    if a.objective:
        from src.teleon.objectives import PRESETS
        if a.objective not in PRESETS:
            print(f"unknown objective {a.objective!r}; choose one of: {', '.join(sorted(PRESETS))}")
            return 2
        obj = PRESETS[a.objective]
        for u in _seed()["units"]:
            sel = select_placement(u, obj)
            ranked = "  ".join(f"{r['impl_id']}={r['score']}" for r in sel["ranked"])
            print(f"  {u['variety']:22} -> {sel['chosen']:20} under {a.objective}   [{ranked}]")
        return 0
    if a.descent:
        print(json.dumps(demonstrate_descent("model"), indent=2))
        return 0
    if a.resources:
        for u in preseed()["units"]:
            rr = u["resolved_resources"]
            print(f"  {u['variety']:22} local_floor={rr['local_floor_cost']} cloud={rr['cloud_cost']} "
                  f"runtime={[r['runtime_class'] for r in rr['runtime']]} slots={list(rr['resource_slots'])} "
                  f"governed={bool(rr['governance'])}")
        return 0
    pre = preseed()
    if a.json:
        print(json.dumps(pre, indent=2))
        return 0
    if a.list:
        for u in pre["units"]:
            print(f"  T{u['declared_tier']} {u['variety']:22} {u['capability_slot']:28} "
                  f"-> adapt to T{u['adaptation_target']}  ({u['build_mode']})")
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
