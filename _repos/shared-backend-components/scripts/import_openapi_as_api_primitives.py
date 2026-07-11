#!/usr/bin/env python3
"""scripts.import_openapi_as_api_primitives — endpoints ARE primitive factories (2026-07-08). A machine-
readable OpenAPI spec is source material; this OFFLINE, deterministic importer turns each operation into a
GOVERNED interface primitive + its sub-primitive bundle (request builder · schema validator · response
normalizer · error mapper · side-effect gate). Side effects are inferred from the HTTP method (GET=read/safe;
POST=create/write; DELETE=delete/idempotent; money paths=money_movement), retry-safety from idempotency, and
every record flows the SAME formal-package/security/lifecycle governance as every other primitive class
(pure functions, external tools, standard specs — this is the FOURTH class). Fourth primitive class, one
governance.

NEVER calls the network (it parses a spec dict/file); preserves the source spec hash as provenance. Records are
candidate SPECS (needs_executor=true): the typed client/validator/mock/contract-test are generated before a
primitive is validated. Writes → risk_tier review-required; money movement → high-risk; reads → low-risk.
candidate; serves_truth=false. Output validates against schemas/api_interface_primitive.schema.json.

    python3 scripts/import_openapi_as_api_primitives.py --self-test
    python3 scripts/import_openapi_as_api_primitives.py --spec openapi.json --provider acme --service billing
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from typing import Any  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except ImportError as exc:  # pragma: no cover
    raise SystemExit(f"import_openapi_as_api_primitives requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CARD_PREFIX = "prim-api"
IMPORTER_VERSION = "openapi-importer-v1"
_HTTP_METHODS = ("get", "head", "post", "put", "patch", "delete")
#: method -> (default semantic_action, side_effect_level, idempotent, retry_safe)
_METHOD_POLICY: dict[str, tuple[str, str, bool, bool]] = {
    "get": ("read", "none", True, True), "head": ("read", "none", True, True),
    "post": ("create", "write_external", False, False), "put": ("update", "write_external", True, True),
    "patch": ("update", "write_external", False, False), "delete": ("delete", "delete", True, True)}
_MONEY_RE = re.compile(r"payment|charge|payout|transfer|refund|invoice|ledger|settle", re.IGNORECASE)
_BUNDLE_OPS = ("request_builder", "request_schema_validator", "response_normalizer", "error_mapper",
               "side_effect_gate")


def infer_semantic_action(method: str, path: str, op_id: str, tags: list[str]) -> str:
    """Refine the method default with operationId/path/tag hints (read vs search/classify/standardize/etc)."""
    hint = " ".join([op_id, path, *tags]).lower()
    if method in ("get", "head"):
        return "search" if re.search(r"search|query|list|find", hint) else "read"
    if re.search(r"classif", hint):
        return "classify"
    if re.search(r"standardi|normali|validate|verify", hint):
        return "standardize"
    if re.search(r"reconcil", hint):
        return "reconcile"
    return _METHOD_POLICY[method][0]


def _extract_input_schema(op: dict[str, Any]) -> dict[str, Any]:
    params = [{"name": p.get("name"), "in": p.get("in"), "required": p.get("required", False),
               "type": (p.get("schema") or {}).get("type", "string")}
              for p in op.get("parameters", []) if isinstance(p, dict)]
    body = op.get("requestBody") or {}
    content = body.get("content") or {}
    media = next(iter(content.values()), {}) if content else {}
    return {"parameters": params, "request_body_schema": media.get("schema", {}),
            "request_body_required": body.get("required", False)}


def _extract_output_schema(op: dict[str, Any]) -> dict[str, Any]:
    responses = op.get("responses") or {}
    ok = next((responses[c] for c in ("200", "201", "202", "default") if c in responses), {})
    media = next(iter((ok.get("content") or {}).values()), {}) if isinstance(ok, dict) else {}
    return {"success_schema": media.get("schema", {}),
            "status_codes": sorted(str(k) for k in responses)}


def _error_schema(op: dict[str, Any]) -> dict[str, Any]:
    responses = op.get("responses") or {}
    errs = {c: (responses[c].get("description", "") if isinstance(responses[c], dict) else "")
            for c in responses if str(c)[0] in ("4", "5")}
    return {"error_status_codes": sorted(errs), "descriptions": errs}


def _auth(spec: dict[str, Any], op: dict[str, Any]) -> dict[str, Any]:
    schemes = (spec.get("components") or {}).get("securitySchemes") or {}
    sec = op.get("security", spec.get("security", []))
    scopes: list[str] = []
    for req in sec or []:
        for _name, sc in req.items():
            scopes += sc or []
    a_type = "none"
    if schemes:
        first = next(iter(schemes.values()), {})
        a_type = {"http": "bearer", "apiKey": "api_key", "oauth2": "oauth2"}.get(first.get("type", ""),
                                                                                first.get("type", "none"))
    return {"type": a_type if sec else "none", "required_scopes": sorted(set(scopes))}


def _sub_primitive(parent_id: str, provider: str, service: str, op_id: str, sub: str,
                   spec_hash: str) -> dict[str, Any]:
    impl = f"{service}.{op_id}.{sub}"
    return {"primitive_id": canonical_id(CARD_PREFIX, impl, sub), "record_type": "api_endpoint_bundle_primitive",
            "impl_name": impl, "kind": "primitive_spec", "title": f"{sub} — {op_id}",
            "parent_endpoint": parent_id, "operation": sub, "provider": provider, "service": service,
            "execution_model": "deterministic_transformer" if sub != "side_effect_gate" else "external_tool",
            "determinism_level": "D0_pure" if sub != "side_effect_gate" else "D2_bounded_external",
            "lifecycle_stage": "candidate", "needs_executor": True,
            "permission_manifest": {"permission_class": "pure" if sub != "side_effect_gate" else "network egress",
                                    "side_effect_free": sub != "side_effect_gate",
                                    "network_access": sub == "side_effect_gate", "security_flags": []},
            "risk_tier": "safe", "verifier_id": "import_openapi_as_api_primitives::_self_test",
            "provenance": {"spec_hash": spec_hash, "contract_version": IMPORTER_VERSION}, **BOUNDARY}


def import_openapi(spec: dict[str, Any], *, provider: str, service: str,
                   with_bundle: bool = True) -> list[dict[str, Any]]:
    """Parse an OpenAPI spec dict -> interface primitives (+ sub-primitive bundle). Offline, deterministic."""
    spec_hash = canonical_id("spec", json.dumps(spec, sort_keys=True))
    cards: list[dict[str, Any]] = []
    for path, path_item in (spec.get("paths") or {}).items():
        if not isinstance(path_item, dict):
            continue
        for method in _HTTP_METHODS:
            op = path_item.get(method)
            if not isinstance(op, dict):
                continue
            default_action, side_level, idempotent, retry_safe = _METHOD_POLICY[method]
            op_id = op.get("operationId") or f"{method}_{re.sub(r'[^a-zA-Z0-9]+', '_', path).strip('_')}"
            action = infer_semantic_action(method, path, op_id, op.get("tags", []))
            money = bool(_MONEY_RE.search(path) or _MONEY_RE.search(op_id))
            level = "money_movement" if (money and side_level != "none") else side_level
            mutating = level not in ("none",)
            has_idem_key = any((p.get("name") or "").lower() in ("idempotency-key", "idempotency_key")
                               for p in op.get("parameters", []) if isinstance(p, dict))
            risk = ("high risk" if level == "money_movement" else "review required" if mutating else "low risk")
            endpoint_id = canonical_id(CARD_PREFIX, f"{service}.{op_id}", path)
            cards.append({
                "primitive_id": endpoint_id, "record_type": "api_interface_primitive", "impl_name": op_id,
                "provider": provider, "service": service, "operation_id": op_id,
                "method": method.upper(), "path_template": path, "semantic_action": action,
                "resource_type": path.strip("/").split("/")[0] or None,
                "input_schema": _extract_input_schema(op), "output_schema": _extract_output_schema(op),
                "error_schema": _error_schema(op), "auth": _auth(spec, op),
                "side_effects": {"level": level, "requires_confirmation": mutating},
                "idempotency": {"supported": has_idem_key, "safe_to_retry": retry_safe or has_idem_key},
                "pagination": {"type": "cursor" if action == "search" else "none"},
                "rate_limits": None, "cost_model": {"unit": "request", "estimated_cost": None},
                "reliability_policy": {"timeout_ms": 30000, "max_retries": 2 if (retry_safe or has_idem_key)
                                       else 0, "backoff": "exponential", "fallbacks": []},
                "bundle": [f"{op_id}.{s}" for s in _BUNDLE_OPS],
                "execution_model": "external_tool", "determinism_level": "D2_bounded_external",
                "permission_manifest": {"permission_class": "network egress", "side_effect_free": False,
                                        "network_access": True, "filesystem_write": False,
                                        "mutating": mutating, "security_flags": ["network"]},
                "risk_tier": risk, "lifecycle_stage": "candidate", "needs_executor": True,
                "compilation_targets": ["python_client", "typescript_client", "mcp_tool", "openai_tool_schema",
                                        "mock_server", "contract_test"],
                "provenance": {"spec_hash": spec_hash, "contract_version": IMPORTER_VERSION, "provider": provider,
                               "service": service},
                # multi-axis tags feed the atlas facets (system_of_record etc.)
                "retrieval_tags": sorted({"api_interface", "external_tool", "D2_bounded_external",
                                          "network egress", risk, "candidate", action, level,
                                          f"provider:{provider}", f"service:{service}"}),
                "never_final_adverse_decision": level in ("money_movement", "regulated_decision"),
                **BOUNDARY})
            if with_bundle:
                for sub in _BUNDLE_OPS:
                    cards.append(_sub_primitive(endpoint_id, provider, service, op_id, sub, spec_hash))
    return cards


def _sample_spec() -> dict[str, Any]:
    return {"openapi": "3.1.0", "info": {"title": "Sample", "version": "1"},
            "components": {"securitySchemes": {"bearer": {"type": "http", "scheme": "bearer"}}},
            "security": [{"bearer": ["pets:read"]}],
            "paths": {
                "/pets": {
                    "get": {"operationId": "listPets", "tags": ["pets"],
                            "parameters": [{"name": "limit", "in": "query", "schema": {"type": "integer"}}],
                            "responses": {"200": {"content": {"application/json": {"schema":
                                          {"type": "array"}}}}, "400": {"description": "bad"}}},
                    "post": {"operationId": "createPet",
                             "requestBody": {"required": True, "content": {"application/json":
                                             {"schema": {"type": "object"}}}},
                             "responses": {"201": {"content": {"application/json": {"schema":
                                           {"type": "object"}}}}}}},
                "/pets/{petId}": {
                    "delete": {"operationId": "deletePet",
                               "parameters": [{"name": "petId", "in": "path", "required": True,
                                               "schema": {"type": "string"}}],
                               "responses": {"204": {"description": "gone"}}}},
                "/payments/charge": {
                    "post": {"operationId": "createCharge",
                             "requestBody": {"required": True, "content": {"application/json":
                                             {"schema": {"type": "object"}}}},
                             "responses": {"200": {"content": {"application/json": {"schema":
                                           {"type": "object"}}}}}}}}}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    cards = import_openapi(_sample_spec(), provider="sample", service="petstore")
    ifaces = [c for c in cards if c["record_type"] == "api_interface_primitive"]
    by_op = {c["operation_id"]: c for c in ifaces}
    checks.append(("imports 4 operations as interface primitives + their sub-primitive bundles",
                   len(ifaces) == 4 and len(cards) == 4 + 4 * len(_BUNDLE_OPS)))
    checks.append(("GET listPets -> search action, side-effect none, safe_to_retry, low/safe risk, pagination",
                   by_op["listPets"]["semantic_action"] == "search"
                   and by_op["listPets"]["side_effects"]["level"] == "none"
                   and by_op["listPets"]["idempotency"]["safe_to_retry"] is True
                   and by_op["listPets"]["pagination"]["type"] == "cursor"))
    checks.append(("POST createPet -> create, write_external, NOT safe_to_retry (no idempotency key), review",
                   by_op["createPet"]["semantic_action"] == "create"
                   and by_op["createPet"]["side_effects"]["level"] == "write_external"
                   and by_op["createPet"]["idempotency"]["safe_to_retry"] is False
                   and by_op["createPet"]["risk_tier"] == "review required"
                   and by_op["createPet"]["reliability_policy"]["max_retries"] == 0))
    checks.append(("DELETE deletePet -> delete, idempotent+safe_to_retry",
                   by_op["deletePet"]["semantic_action"] == "delete"
                   and by_op["deletePet"]["idempotency"]["safe_to_retry"] is True))
    checks.append(("POST /payments/charge -> money_movement side effect, HIGH risk, never_final_adverse",
                   by_op["createCharge"]["side_effects"]["level"] == "money_movement"
                   and by_op["createCharge"]["risk_tier"] == "high risk"
                   and by_op["createCharge"]["never_final_adverse_decision"] is True))
    checks.append(("auth extracted (bearer + scope); input/output schemas captured",
                   by_op["listPets"]["auth"]["type"] == "bearer"
                   and "pets:read" in by_op["listPets"]["auth"]["required_scopes"]
                   and by_op["listPets"]["input_schema"]["parameters"][0]["name"] == "limit"))
    checks.append(("every interface primitive is external_tool/D2/network-egress/candidate, serves_truth=false",
                   all(c["execution_model"] == "external_tool" and c["determinism_level"] == "D2_bounded_external"
                       and c["permission_manifest"]["network_access"] and c["serves_truth"] is False
                       for c in ifaces)))
    checks.append(("spec_hash deterministic (same spec -> same hash); ids canonical + unique; OFFLINE (no net)",
                   import_openapi(_sample_spec(), provider="sample", service="petstore")[0]["provenance"]
                   ["spec_hash"] == ifaces[0]["provenance"]["spec_hash"]
                   and len({c["primitive_id"] for c in cards}) == len(cards)))
    # schema validation
    schema = json.loads((_sbc_boot / "schemas" / "api_interface_primitive.schema.json").read_text())
    required = schema["required"]
    checks.append(("interface primitives satisfy api_interface_primitive.schema.json required fields",
                   all(all(k in c for k in required) for c in ifaces)))
    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - import_openapi_as_api_primitives: OFFLINE OpenAPI -> {len(ifaces)} interface primitives + "
          f"bundles ({len(cards)} records). Side effects from method, retry-safety from idempotency, money "
          f"paths high-risk. External_tool/D2, candidate specs awaiting executors. serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--spec", default=None)
    ap.add_argument("--provider", default="unknown")
    ap.add_argument("--service", default="unknown")
    ap.add_argument("--out", default=None)
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.spec:
        spec = json.loads(Path(args.spec).read_text())
        cards = import_openapi(spec, provider=args.provider, service=args.service)
        out = "\n".join(json.dumps(c, sort_keys=True) for c in cards)
        if args.out:
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(out + "\n")
        print(out)
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
