#!/usr/bin/env python3
"""Proof: Teleon's runtime profiles and egress route taxonomy are coherent.

The check keeps the new profile layer honest:
  - every capability runtime class has exactly one execution profile;
  - each profile's local backend matches the class's local_equivalent;
  - resource, lifecycle, SLA, and egress-route references resolve;
  - autotuning templates forbid trust/tenant/secret/source/egress/truth changes;
  - route policies capture every decision, store no raw payload by default, and
    never serve truth;
  - docs and schemas for the layer exist.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


_REPO = Path(__file__).resolve().parents[1]
_A = _REPO / "architecture"
_DOC = _REPO / "docs" / "architecture" / "teleon-execution-environment-taxonomy.md"
_EGRESS_DOC = _REPO / "docs" / "architecture" / "teleon-egress-graph.md"
_PROFILE_SCHEMA = _REPO / "schemas" / "runtime" / "ExecutionEnvironmentProfile.v1.schema.json"
_ROUTE_SCHEMA = _REPO / "schemas" / "egress" / "EgressRoutePolicy.v1.schema.json"

_FORBIDDEN_AUTOTUNE_LOCKS = {
    "trust_boundary",
    "tenant_scope",
    "secret_policy",
    "source_authority",
    "egress_blocklist",
    "serves_truth",
}
_HIGH_RISK_ROUTES = {"approved_proxy_exit", "approved_vpn_exit", "customer_private_connector"}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _bare_backend(local_equivalent: str) -> str:
    return local_equivalent.removeprefix("execution.")


def _self_test() -> int:
    fails: list[str] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    classes_doc = _load_json(_A / "capability_runtime_classes.json")
    matrix = _load_json(_A / "execution_backend_policy_matrix.json")
    resources = _load_json(_A / "worker_resource_classes.json")
    lifecycle = _load_json(_A / "worker_lifecycle_policies.json")
    sla = _load_json(_A / "worker_sla_policies.json")
    routes_doc = _load_json(_A / "egress_route_policy_taxonomy.json")
    profiles_doc = _load_json(_A / "execution_environment_profiles.json")
    route_schema = _load_json(_ROUTE_SCHEMA)
    profile_schema = _load_json(_PROFILE_SCHEMA)
    route_validator = Draft202012Validator(route_schema)
    profile_validator = Draft202012Validator(profile_schema)

    class_by_id = {c["class"]: c for c in classes_doc["classes"]}
    profile_by_class = {p["runtime_class"]: p for p in profiles_doc["profiles"]}
    resource_ids = {r["class_id"] for r in resources["classes"]}
    lifecycle_ids = {p["lifecycle_policy_id"] for p in lifecycle["policies"]}
    sla_ids = {p["sla_policy_id"] for p in sla["policies"]}
    route_ids = {r["route_policy_id"] for r in routes_doc["routes"]}
    backend_ids = set(matrix["backends_enum"]) | {_bare_backend(b) for b in matrix["local_equivalents_built"]}
    template_ids = set(profiles_doc["autotuning_policy_templates"])

    chk("schema file exists: ExecutionEnvironmentProfile.v1", _PROFILE_SCHEMA.exists())
    chk("schema file exists: EgressRoutePolicy.v1", _ROUTE_SCHEMA.exists())
    chk("route taxonomy has unique route_policy_id values", len(route_ids) == len(routes_doc["routes"]))
    chk("profile taxonomy has unique runtime_class values", len(profile_by_class) == len(profiles_doc["profiles"]))
    chk("every runtime class has one profile", set(class_by_id) == set(profile_by_class),
        f"missing={sorted(set(class_by_id) - set(profile_by_class))}; extra={sorted(set(profile_by_class) - set(class_by_id))}")

    for template_id, template in profiles_doc["autotuning_policy_templates"].items():
        locks = set(template.get("forbidden_knobs", []))
        chk(f"autotune template {template_id} forbids boundary-changing knobs",
            _FORBIDDEN_AUTOTUNE_LOCKS <= locks, str(sorted(_FORBIDDEN_AUTOTUNE_LOCKS - locks)))
        chk(f"autotune template {template_id} requires baseline rollback",
            template.get("requires_baseline_rollback") is True)
        chk(f"autotune template {template_id} has a promotion gate", bool(template.get("promotion_gate")))

    for route in routes_doc["routes"]:
        rid = route["route_policy_id"]
        text = " ".join(route.get("allowed_for", []) + route.get("forbidden_for", [])).lower()
        chk(f"route {rid} validates against EgressRoutePolicy.v1",
            not list(route_validator.iter_errors(route)))
        chk(f"route {rid} captures decisions", route.get("capture_required") is True)
        chk(f"route {rid} requires decision receipt", route.get("decision_receipt_required") is True)
        chk(f"route {rid} never serves truth", route.get("serves_truth") is False)
        chk(f"route {rid} stores no raw payload by default",
            route.get("payload_policy", {}).get("store_raw_by_default") is False)
        chk(f"route {rid} forbids bypass behavior", "access control bypass" in text and "captcha bypass" in text
            if route["route_kind"] != "blocked" else "silent fallback" in text)
        fallback = route.get("fallback_route_policy_id")
        chk(f"route {rid} fallback resolves or is null", fallback is None or fallback in route_ids, str(fallback))
        if rid in _HIGH_RISK_ROUTES:
            requires = set(route.get("requires", []))
            chk(f"high-risk route {rid} requires tenant/source approval",
                bool({"tenant_approval", "exit_policy_id", "vpn_profile_ref", "private_connector_binding"} & requires),
                str(sorted(requires)))
            chk(f"high-risk route {rid} is not default allowed", route.get("default_allowed") is False)

    for runtime_class, profile in sorted(profile_by_class.items()):
        class_doc = class_by_id[runtime_class]
        req = profile["requirements"]
        prefs = profile["policy_preferences"]
        obs = profile["observability"]
        expected_local = _bare_backend(class_doc["local_equivalent"])

        chk(f"{runtime_class}: validates against ExecutionEnvironmentProfile.v1",
            not list(profile_validator.iter_errors(profile)))
        chk(f"{runtime_class}: local backend matches capability_runtime_classes",
            profile["default_local_backend"] == expected_local,
            f"{profile['default_local_backend']} != {expected_local}")
        chk(f"{runtime_class}: local backend is declared/built",
            profile["default_local_backend"] in backend_ids, profile["default_local_backend"])
        chk(f"{runtime_class}: preferred candidates match class vendors",
            set(profile.get("preferred_candidate_backends", [])) <= set(class_doc.get("vendors", [])),
            str(sorted(set(profile.get("preferred_candidate_backends", [])) - set(class_doc.get("vendors", [])))))
        chk(f"{runtime_class}: min resource class resolves", req["min_resource_class"] in resource_ids)
        chk(f"{runtime_class}: lifecycle policy resolves", prefs["default_lifecycle_policy_id"] in lifecycle_ids)
        chk(f"{runtime_class}: SLA policy resolves", prefs["default_sla_policy_id"] in sla_ids)
        chk(f"{runtime_class}: egress route policy resolves", prefs["egress_route_policy_id"] in route_ids)
        chk(f"{runtime_class}: autotuning policy resolves", profile["autotuning_policy_id"] in template_ids)
        chk(f"{runtime_class}: trigger models are in enum",
            set(req["trigger_models"]) <= set(profiles_doc["trigger_model_enum"]))
        chk(f"{runtime_class}: state model is in enum", req["state_model"] in profiles_doc["state_model_enum"])
        chk(f"{runtime_class}: surface family is in enum", profile["surface_family"] in profiles_doc["surface_family_enum"])
        chk(f"{runtime_class}: receipt includes RuntimeClassBinding.v1",
            "RuntimeClassBinding.v1" in obs.get("required_receipts", []))
        chk(f"{runtime_class}: outbound egress observations required",
            obs.get("egress_observation_required_when_outbound") is True)
        chk(f"{runtime_class}: runtime profile never serves truth", obs.get("serves_truth") is False)
        chk(f"{runtime_class}: pre-autotune defaults reference worker_resource_classes",
            profile["pre_autotune_defaults"]["concurrency_source"].startswith("worker_resource_classes.")
            and profile["pre_autotune_defaults"]["timeout_source"].startswith("worker_resource_classes."))
        if req["requires_gpu"]:
            chk(f"{runtime_class}: gpu requirement uses gpu resource", req["min_resource_class"].startswith("gpu_"))
        if req["requires_browser"]:
            chk(f"{runtime_class}: browser requirement uses browser route",
                prefs["egress_route_policy_id"] == "browser_pool_render")

    doc_text = _DOC.read_text(encoding="utf-8") if _DOC.exists() else ""
    egress_text = _EGRESS_DOC.read_text(encoding="utf-8") if _EGRESS_DOC.exists() else ""
    for phrase in (
        "pre-autotune",
        "EgressIntent",
        "RoutePolicyDecision",
        "serves_truth=false",
        "graph/search layer is a projection",
    ):
        chk(f"execution taxonomy doc mentions {phrase!r}", phrase.lower() in doc_text.lower())
    for phrase in ("route broker", "append-only", "serves_truth=false"):
        chk(f"egress graph doc mentions {phrase!r}", phrase.lower() in egress_text.lower())

    print("\n" + (
        "PASS — check_teleon_execution_environment_taxonomy: every runtime class has a coherent "
        "ExecutionEnvironmentProfile; local equivalents, resource/lifecycle/SLA/route refs, autotune locks, "
        "capture-required egress route policies, no-truth boundaries, schemas, and docs all line up."
        if not fails else f"{len(fails)} FAILURES: {fails}"
    ))
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Proof for Teleon execution environment taxonomy.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
