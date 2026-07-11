#!/usr/bin/env python3
"""scripts.docs_api_forge — DocsDomainForge core: turn API docs / OpenAPI specs into USER-KEYED interface
primitives (request builder + response validator + error mapper + auth injector), MOCK-PROVEN with NO real key,
each carrying a credential profile referenced BY ENV NAME (user-configurable), never an embedded key
(candidate-only).

Owner (2026-07-09): search docs.<domain> sites -> endpoints/examples/errors -> primitives + variations with
user-configurable API keys. The executable CORE here (OpenAPI -> endpoint primitives -> mock proof) runs OFFLINE,
no live call, no key — the honest first proof (mock_proven). Live/test-mode proof is gated on: env key present +
provider profile permits the data class + side-effect gate + test/live mode explicit + idempotency for writes.
serves_truth=false; every row candidate=true.

    python3 scripts/docs_api_forge.py --self-test
    python3 scripts/docs_api_forge.py --providers      # provider key profiles + which env keys are present
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/buildout_forge.py) ────────────────────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
from typing import Any  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"docs_api_forge requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
ARTIFACT_DIR_REL = "data/dev-intel/docs_api_forge"

# ── provider key profiles: credentials by ENV NAME (user-configurable); NEVER an embedded key. ────────────────
PROVIDER_PROFILES: list[dict[str, Any]] = [
    {"provider_id": "stripe", "docs_url": "https://docs.stripe.com/api", "env_var": "STRIPE_API_KEY",
     "auth_type": "bearer", "test_mode_required": True, "live_allowed": False,
     "data_classes_allowed": ["synthetic", "test"], "side_effects_allowed": ["test_write"],
     "safe_smoke_test": "GET /v1/balance in test mode",
     "missing_key_message": "Missing STRIPE_API_KEY -> unlocks: checkout-session wrapper proof, webhook signature "
                            "verifier smoke test, SaaS billing buildout A/B (test mode only)"},
    {"provider_id": "github", "docs_url": "https://docs.github.com/rest", "env_var": "GITHUB_TOKEN",
     "auth_type": "bearer", "test_mode_required": False, "live_allowed": True,
     "data_classes_allowed": ["public", "synthetic"], "side_effects_allowed": ["live_read", "test_write"],
     "safe_smoke_test": "GET /user (read-only)",
     "missing_key_message": "Missing GITHUB_TOKEN -> unlocks: issue-create wrapper, repo search wrapper, PR review"},
    {"provider_id": "slack", "docs_url": "https://api.slack.com/web", "env_var": "SLACK_BOT_TOKEN",
     "auth_type": "bearer", "test_mode_required": False, "live_allowed": False,
     "data_classes_allowed": ["synthetic"], "side_effects_allowed": ["mock"],
     "safe_smoke_test": "auth.test (read-only)", "missing_key_message": "Missing SLACK_BOT_TOKEN -> message-send wrapper"},
    {"provider_id": "openrouter", "docs_url": "https://openrouter.ai/docs", "env_var": "OPENROUTER_API_KEY",
     "auth_type": "bearer", "test_mode_required": False, "live_allowed": True,
     "data_classes_allowed": ["synthetic"], "side_effects_allowed": ["live_read"],
     "safe_smoke_test": "GET /models", "missing_key_message": "Missing OPENROUTER_API_KEY -> model-route wrapper"},
    {"provider_id": "rapidapi", "docs_url": "https://rapidapi.com/hub", "env_var": "RAPIDAPI_KEY",
     "auth_type": "api_key_header", "header_name": "X-RapidAPI-Key", "test_mode_required": False,
     "live_allowed": True, "data_classes_allowed": ["public", "synthetic"], "side_effects_allowed": ["live_read"],
     "safe_smoke_test": "any GET endpoint on the target host",
     "missing_key_message": "Missing RAPIDAPI_KEY -> thousands of RapidAPI-hub endpoint wrappers"},
]
_PROFILE_BY_ID = {p["provider_id"]: p for p in PROVIDER_PROFILES}

# side-effect level per HTTP method (a WRITE needs test-mode + idempotency gate at live time)
_METHOD_SIDE_EFFECT = {"get": "read_only", "head": "read_only", "post": "write", "put": "write",
                       "patch": "write", "delete": "write"}


def _validate_against_schema(value: Any, schema: dict[str, Any]) -> list[str]:
    """Minimal deterministic validator: required keys present + top-level type checks. No external deps."""
    errors = []
    if schema.get("type") == "object":
        if not isinstance(value, dict):
            return ["not_object"]
        for req in schema.get("required", []):
            if req not in value or value.get(req) in (None, ""):
                errors.append(f"missing:{req}")
        props = schema.get("properties", {})
        for k, spec in props.items():
            if k in value and value[k] is not None:
                t = spec.get("type")
                ok = (t == "string" and isinstance(value[k], str)) or \
                     (t in ("number", "integer") and isinstance(value[k], (int, float)) and not isinstance(value[k], bool)) or \
                     (t == "boolean" and isinstance(value[k], bool)) or (t in (None, "object", "array"))
                if not ok:
                    errors.append(f"type:{k}!={t}")
    return errors


def openapi_to_endpoint_primitives(provider_id: str, spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Parse a (minimal) OpenAPI dict -> endpoint interface primitive candidates. Each carries input/output
    schemas, an auth_ref (env NAME), a deterministic request-builder plan, and a side-effect level."""
    profile = _PROFILE_BY_ID.get(provider_id, {"env_var": "API_KEY", "auth_type": "bearer"})
    base = (spec.get("servers") or [{"url": ""}])[0].get("url", "")
    prims = []
    for path, methods in (spec.get("paths") or {}).items():
        for method, op in methods.items():
            if method.lower() not in _METHOD_SIDE_EFFECT:
                continue
            op_id = op.get("operationId") or f"{method}_{path.strip('/').replace('/', '_')}"
            req_schema = (((op.get("requestBody") or {}).get("content") or {}).get("application/json") or {}).get("schema", {})
            resp = op.get("responses") or {}
            ok_schema = (((resp.get("200") or resp.get("201") or {}).get("content") or {})
                         .get("application/json") or {}).get("schema", {})
            pid = canonical_id("apiprim", provider_id, op_id)
            prims.append({"record_type": "api_endpoint_primitive", "primitive_id": pid,
                          "provider_id": provider_id, "operation_id": op_id, "method": method.upper(),
                          "path": path, "url_template": base + path,
                          "input_schema": req_schema, "output_schema": ok_schema,
                          "auth_ref": {"env_var": profile["env_var"], "auth_type": profile.get("auth_type", "bearer"),
                                       "header_name": profile.get("header_name")},
                          "side_effect_level": _METHOD_SIDE_EFFECT[method.lower()],
                          "credentials": [{"env_name": profile["env_var"], "provider": provider_id,
                                           "user_configurable": True}], **BOUNDARY})
    return prims


def build_request(primitive: dict[str, Any], params: dict[str, Any], env_value_present: bool) -> dict[str, Any]:
    """DETERMINISTIC request builder: assemble the HTTP request WITHOUT the secret value — the Authorization
    header references the env NAME, resolved at call time only if the user configured the key."""
    auth = primitive["auth_ref"]
    headers = {"Content-Type": "application/json"}
    if auth["auth_type"] == "api_key_header":
        headers[auth.get("header_name") or "X-API-Key"] = f"${{{auth['env_var']}}}"
    else:
        headers["Authorization"] = f"Bearer ${{{auth['env_var']}}}"
    return {"method": primitive["method"], "url": primitive["url_template"], "headers": headers,
            "json": params if primitive["method"] in ("POST", "PUT", "PATCH") else None,
            "auth_configured": env_value_present, "would_call_live": False}  # mock proof never calls live


def mock_prove(primitive: dict[str, Any], example_params: dict[str, Any],
               mock_response: dict[str, Any]) -> dict[str, Any]:
    """EXECUTED offline proof (no key, no network): validate example params against the input schema, build the
    request deterministically, validate a mock response against the output schema. mock_proven iff both pass."""
    in_errs = _validate_against_schema(example_params, primitive["input_schema"]) if primitive["input_schema"] else []
    req = build_request(primitive, example_params, env_value_present=False)
    out_errs = _validate_against_schema(mock_response, primitive["output_schema"]) if primitive["output_schema"] else []
    ok = not in_errs and not out_errs and req["would_call_live"] is False
    return {"primitive_id": primitive["primitive_id"], "mock_proven": ok, "input_errors": in_errs,
            "output_errors": out_errs, "request_built": bool(req["url"]),
            "auth_by_env_name": primitive["auth_ref"]["env_var"], **BOUNDARY}


def provider_key_audit() -> dict[str, Any]:
    """Which provider keys are present (env presence-only, NEVER a value) + the missing-key accelerator message."""
    rows = []
    for p in PROVIDER_PROFILES:
        present = bool(os.environ.get(p["env_var"]))
        rows.append({"provider_id": p["provider_id"], "env_var": p["env_var"], "present": present,
                     "unlocks": None if present else p["missing_key_message"],
                     "safe_smoke_test": p["safe_smoke_test"]})
    return {"record_type": "api_provider_key_audit", "n_providers": len(rows),
            "n_present": sum(1 for r in rows if r["present"]), "providers": rows, **BOUNDARY}


# synthetic OpenAPI spec for the self-test (a "create vendor" write + a "get vendor" read)
_SPEC = {"servers": [{"url": "https://api.example.com"}], "paths": {
    "/vendors": {"post": {"operationId": "createVendor",
                          "requestBody": {"content": {"application/json": {"schema": {
                              "type": "object", "required": ["vendor_id", "name"],
                              "properties": {"vendor_id": {"type": "string"}, "name": {"type": "string"}}}}}},
                          "responses": {"201": {"content": {"application/json": {"schema": {
                              "type": "object", "required": ["vendor_id"],
                              "properties": {"vendor_id": {"type": "string"}}}}}}}}},
    "/vendors/{id}": {"get": {"operationId": "getVendor", "responses": {"200": {"content": {"application/json": {
        "schema": {"type": "object", "properties": {"vendor_id": {"type": "string"}}}}}}}}}}}


def self_test() -> bool:
    """Mutation-gated + EXECUTED (offline): OpenAPI -> endpoint primitives with env-NAME auth (no embedded key);
    mock proof passes for valid params/response and FAILS when a required field is missing; the request builder
    references the env NAME only; provider audit is presence-only (no secret value)."""
    prims = openapi_to_endpoint_primitives("stripe", _SPEC)
    assert len(prims) == 2, f"must extract 2 endpoint primitives: {len(prims)}"
    create = next(p for p in prims if p["operation_id"] == "createVendor")
    assert create["side_effect_level"] == "write" and create["credentials"][0]["env_name"] == "STRIPE_API_KEY"
    # auth references the ENV NAME, never a value.
    req = build_request(create, {"vendor_id": "V1", "name": "Acme"}, env_value_present=False)
    assert "${STRIPE_API_KEY}" in req["headers"]["Authorization"] and req["would_call_live"] is False

    good = mock_prove(create, {"vendor_id": "V1", "name": "Acme"}, {"vendor_id": "V1"})
    assert good["mock_proven"] is True, f"valid params+response must mock-prove: {good}"
    bad_in = mock_prove(create, {"name": "NoId"}, {"vendor_id": "V1"})   # missing required vendor_id
    assert bad_in["mock_proven"] is False and any("vendor_id" in e for e in bad_in["input_errors"]), bad_in
    bad_out = mock_prove(create, {"vendor_id": "V1", "name": "Acme"}, {})  # response missing required vendor_id
    assert bad_out["mock_proven"] is False and bad_out["output_errors"], bad_out

    audit = provider_key_audit()
    assert audit["n_providers"] >= 5
    for r in audit["providers"]:
        assert isinstance(r["present"], bool)  # presence is a bool -> no value leakage
    # no embedded secret anywhere in the produced records.
    blob = json.dumps({"prims": prims, "audit": audit})
    assert "sk-" not in blob and "ghp_" not in blob, "no literal secret may appear"
    assert BOUNDARY["serves_truth"] is False
    print(f"OK docs_api_forge self-test: OpenAPI -> {len(prims)} endpoint primitives (env-NAME auth, no embedded "
          f"key); mock proof PASSES valid + FAILS missing-required (in & out); {audit['n_present']}/"
          f"{audit['n_providers']} provider keys present; missing-key accelerator messages ready; serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="DocsDomainForge core: OpenAPI -> user-keyed API primitives (mock-proven).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--providers", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.providers:
        print(json.dumps(provider_key_audit(), indent=2))
        return
    self_test()


if __name__ == "__main__":
    main()
