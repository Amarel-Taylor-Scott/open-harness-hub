#!/usr/bin/env python3
"""Zero-dependency MCP-style stdio wrapper for the Baltor context gateway.

This intentionally keeps the first local bridge small: it exposes the same tool
surface documented for the MCP gateway and forwards calls to the running admin
demo HTTP API. It speaks JSON-RPC over stdio with Content-Length framing, which
is the transport shape used by MCP clients.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts._config import CONTEXT_GATEWAY_RUNTIME_SETTINGS
from scripts.db.runtime_settings import runtime_setting


CONTEXT_GATEWAY_RUNTIME_NAMESPACE = "baltor.context_gateway.runtime"

def _gateway_setting(name: str) -> str:
    return runtime_setting(
        namespace=CONTEXT_GATEWAY_RUNTIME_NAMESPACE,
        definitions=CONTEXT_GATEWAY_RUNTIME_SETTINGS,
        name=name,
    )


DEFAULT_BASE_URL = _gateway_setting("gateway_base_url")

TOOLS: list[dict[str, Any]] = [
    {
        "name": "context_status",
        "description": "Return Baltor context gateway readiness, policy, backend, and tool surface.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": {"readOnlyHint": True, "destructiveHint": False},
    },
    {
        "name": "context_search",
        "description": "Search indexed context and return a bounded task-specific context pack with source handles.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "task_type": {"type": "string", "default": "code_change"},
                "pack_type": {"type": "string", "default": "implementation_pack"},
                "run_id": {"type": "string"},
                "token_budget": {"type": "integer", "minimum": 256, "maximum": 12000, "default": 3000},
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False},
    },
    {
        "name": "context_fetch",
        "description": "Fetch one bounded source component or claim by ctx:// handle.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "handle": {"type": "string"},
                "run_id": {"type": "string"},
                "max_tokens": {"type": "integer", "minimum": 64, "maximum": 4000, "default": 1000},
            },
            "required": ["handle"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False},
    },
    {
        "name": "context_trace",
        "description": "Explain how a gateway context result was produced and which policy gates applied.",
        "inputSchema": {
            "type": "object",
            "properties": {"result_id": {"type": "string"}},
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False},
    },
    {
        "name": "context_connectors",
        "description": "List governed source connector envelopes available to the Baltor context gateway.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": {"readOnlyHint": True, "destructiveHint": False},
    },
    {
        "name": "context_sync_contracts",
        "description": "Return trigger, check-gate, artifact-manifest, and worker-routing contracts for context sync.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": {"readOnlyHint": True, "destructiveHint": False},
    },
    {
        "name": "context_object_schema",
        "description": "Return the Baltor context-object schema profile and standards mapping for durable context objects.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": {"readOnlyHint": True, "destructiveHint": False},
    },
    {
        "name": "context_schema_catalog",
        "description": "Return the full Baltor context object graph schema catalog for objects, versions, artifacts, relationships, events, and packs.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": {"readOnlyHint": True, "destructiveHint": False},
    },
    {
        "name": "context_product_surface",
        "description": "Return the Baltor Context Fabric product surface: modules, interfaces, deployment models, standards mappings, MVP phases, and invariants.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": {"readOnlyHint": True, "destructiveHint": False},
    },
    {
        "name": "context_heartbeat",
        "description": "Return server, queue, run, event-stream, and worker heartbeat diagnostics.",
        "inputSchema": {
            "type": "object",
            "properties": {"run_id": {"type": "string"}},
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False},
    },
    {
        "name": "context_queue_health",
        "description": "Return queue backlog, active worker jobs, stale-job warnings, and recent worker events.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": {"readOnlyHint": True, "destructiveHint": False},
    },
    {
        "name": "context_operational_readiness",
        "description": "Return database-backed import status, object governance status, archive candidate visibility, and setting drift readiness.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": {"readOnlyHint": True, "destructiveHint": False},
    },
    {
        "name": "context_glossary",
        "description": "Return source-scoped glossary resolution packets for unclear, multi-meaning, or undefined terms.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "term": {"type": "string"},
                "run_id": {"type": "string"},
                "max_packets": {"type": "integer", "minimum": 1, "maximum": 50, "default": 12},
            },
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False},
    },
    {
        "name": "context_dimensions",
        "description": "Return context dimension definitions and bounded dimension assessments for a run, dimension, or subject.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {"type": "string"},
                "dimension_id": {"type": "string"},
                "subject_id": {"type": "string"},
                "max_values": {"type": "integer", "minimum": 1, "maximum": 500, "default": 100},
            },
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False},
    },
    {
        "name": "context_model_routing",
        "description": "Return the provider-neutral model routing ladder and risk-based escalation policy.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {"type": "string"},
                "task_type": {"type": "string", "default": "claim_review"},
                "risk": {"type": "object"},
            },
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False},
    },
    {
        "name": "context_reranking",
        "description": "Return the source-aware reranking ladder, including lexical, vector, cross-encoder, LoRA/domain, LLM-judge, and human-review stages.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {"type": "string"},
                "query": {"type": "string"},
                "task_type": {"type": "string", "default": "implementation_pack"},
                "risk": {"type": "object"},
            },
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False},
    },
    {
        "name": "context_local_memory",
        "description": "Return the hybrid local encrypted memory and company context sync contract.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "run_id": {"type": "string"},
                "scope": {"type": "string", "default": "personal"},
            },
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False},
    },
]


def http_json(base_url: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    url = urllib.parse.urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method="POST" if body is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return {"ok": False, "error": f"HTTP {exc.code}", "detail": detail}


def call_gateway_tool(base_url: str, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "context_status":
        return http_json(base_url, "/api/context-gateway/status")
    if name == "context_search":
        return http_json(base_url, "/api/context-gateway/search", arguments)
    if name == "context_fetch":
        return http_json(base_url, "/api/context-gateway/fetch", arguments)
    if name == "context_trace":
        query = urllib.parse.urlencode({"result_id": arguments.get("result_id", "")})
        return http_json(base_url, f"/api/context-gateway/trace?{query}")
    if name == "context_connectors":
        return http_json(base_url, "/api/context-gateway/connectors")
    if name == "context_sync_contracts":
        return http_json(base_url, "/api/context-gateway/sync-contracts")
    if name == "context_object_schema":
        return http_json(base_url, "/api/context-gateway/context-object-schema")
    if name == "context_schema_catalog":
        return http_json(base_url, "/api/context-gateway/context-schema-catalog")
    if name == "context_product_surface":
        return http_json(base_url, "/api/context-gateway/product-surface")
    if name == "context_heartbeat":
        query = urllib.parse.urlencode({"run_id": arguments.get("run_id", "")})
        return http_json(base_url, f"/api/debug/heartbeat?{query}")
    if name == "context_queue_health":
        return http_json(base_url, "/api/admin-dashboard/queue-health")
    if name == "context_operational_readiness":
        return http_json(base_url, "/api/admin-dashboard/operational-readiness")
    if name == "context_glossary":
        return http_json(base_url, "/api/context-gateway/glossary", arguments)
    if name == "context_dimensions":
        return http_json(base_url, "/api/context-gateway/dimensions", arguments)
    if name == "context_model_routing":
        return http_json(base_url, "/api/context-gateway/model-routing", arguments)
    if name == "context_reranking":
        return http_json(base_url, "/api/context-gateway/reranking", arguments)
    if name == "context_local_memory":
        return http_json(base_url, "/api/context-gateway/local-memory", arguments)
    return {"ok": False, "error": f"unknown tool: {name}"}


def response(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def error_response(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def handle_rpc(message: dict[str, Any], *, base_url: str) -> dict[str, Any] | None:
    method = str(message.get("method") or "")
    request_id = message.get("id")
    params = message.get("params") if isinstance(message.get("params"), dict) else {}
    if method == "initialize":
        return response(request_id, {
            "protocolVersion": "2025-11-25",
            "serverInfo": {"name": "baltor-context-gateway", "version": "0.1.0"},
            "capabilities": {"tools": {"listChanged": False}},
        })
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return response(request_id, {"tools": TOOLS})
    if method == "tools/call":
        tool_name = str(params.get("name") or "")
        arguments = params.get("arguments") if isinstance(params.get("arguments"), dict) else {}
        result = call_gateway_tool(base_url, tool_name, arguments)
        return response(request_id, {"content": [{"type": "text", "text": json.dumps(result, indent=2, sort_keys=True)}], "isError": not bool(result.get("ok", True))})
    if request_id is None:
        return None
    return error_response(request_id, -32601, f"method not found: {method}")


def read_message() -> dict[str, Any] | None:
    headers: dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line in {b"\r\n", b"\n"}:
            break
        key, _, value = line.decode("ascii", errors="ignore").partition(":")
        headers[key.lower()] = value.strip()
    length = int(headers.get("content-length") or "0")
    if length <= 0:
        return None
    return json.loads(sys.stdin.buffer.read(length).decode("utf-8"))


def write_message(payload: dict[str, Any]) -> None:
    body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii"))
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()


def serve_stdio(base_url: str) -> int:
    while True:
        message = read_message()
        if message is None:
            return 0
        result = handle_rpc(message, base_url=base_url)
        if result is not None:
            write_message(result)


def self_test(base_url: str) -> dict[str, Any]:
    status = call_gateway_tool(base_url, "context_status", {})
    connectors = call_gateway_tool(base_url, "context_connectors", {})
    sync_contracts = call_gateway_tool(base_url, "context_sync_contracts", {})
    context_object_schema = call_gateway_tool(base_url, "context_object_schema", {})
    context_schema_catalog = call_gateway_tool(base_url, "context_schema_catalog", {})
    context_product_surface = call_gateway_tool(base_url, "context_product_surface", {})
    heartbeat = call_gateway_tool(base_url, "context_heartbeat", {})
    queue_health = call_gateway_tool(base_url, "context_queue_health", {})
    glossary = call_gateway_tool(base_url, "context_glossary", {"max_packets": 3})
    dimensions = call_gateway_tool(base_url, "context_dimensions", {"dimension_id": "dim://baltor/trust/verifiability", "max_values": 5})
    model_routing = call_gateway_tool(base_url, "context_model_routing", {"task_type": "claim_review"})
    reranking = call_gateway_tool(base_url, "context_reranking", {"query": "current ownership threshold", "task_type": "implementation_pack"})
    local_memory = call_gateway_tool(base_url, "context_local_memory", {"scope": "personal"})
    search = call_gateway_tool(base_url, "context_search", {"query": "Acme Bank compliance", "token_budget": 1200})
    handles = ((search.get("context_pack") or {}).get("source_handles") or []) if isinstance(search, dict) else []
    fetch = call_gateway_tool(base_url, "context_fetch", {"handle": handles[0]}) if handles else {"ok": False, "error": "no handle returned"}
    trace = call_gateway_tool(base_url, "context_trace", {"result_id": search.get("result_id", "") if isinstance(search, dict) else ""})
    return {
        "ok": bool(status.get("ok")) and bool(connectors.get("ok")) and bool(sync_contracts.get("ok")) and bool(context_object_schema.get("ok")) and bool(context_schema_catalog.get("ok")) and bool(context_product_surface.get("ok")) and bool(heartbeat.get("ok")) and bool(queue_health.get("ok")) and bool(glossary.get("ok")) and bool(dimensions.get("ok")) and bool(model_routing.get("ok")) and bool(reranking.get("ok")) and bool(local_memory.get("ok")) and bool(search.get("ok")) and bool(fetch.get("ok")) and bool(trace.get("ok")),
        "base_url": base_url,
        "tools": [tool["name"] for tool in TOOLS],
        "status_ok": bool(status.get("ok")),
        "connector_count": len(connectors.get("connectors") or []) if isinstance(connectors, dict) else 0,
        "sync_contract_kind": sync_contracts.get("kind") if isinstance(sync_contracts, dict) else None,
        "sync_trigger_count": len(sync_contracts.get("trigger_types") or []) if isinstance(sync_contracts, dict) else 0,
        "context_object_kind": context_object_schema.get("context_object_kind") if isinstance(context_object_schema, dict) else None,
        "context_schema_catalog_kind": context_schema_catalog.get("kind") if isinstance(context_schema_catalog, dict) else None,
        "context_schema_count": context_schema_catalog.get("schema_count") if isinstance(context_schema_catalog, dict) else None,
        "context_product_surface_kind": context_product_surface.get("kind") if isinstance(context_product_surface, dict) else None,
        "context_product_module_count": len(context_product_surface.get("modules") or []) if isinstance(context_product_surface, dict) else 0,
        "heartbeat_kind": heartbeat.get("kind") if isinstance(heartbeat, dict) else None,
        "queue_health_kind": queue_health.get("package_type") if isinstance(queue_health, dict) else None,
        "queue_health_warnings": len(queue_health.get("warnings") or []) if isinstance(queue_health, dict) else 0,
        "glossary_kind": glossary.get("kind") if isinstance(glossary, dict) else None,
        "glossary_packet_count": glossary.get("packet_count") if isinstance(glossary, dict) else None,
        "dimensions_kind": dimensions.get("kind") if isinstance(dimensions, dict) else None,
        "dimension_definition_count": dimensions.get("counts", {}).get("dimension_definitions") if isinstance(dimensions, dict) else None,
        "dimension_value_count": dimensions.get("counts", {}).get("dimension_values") if isinstance(dimensions, dict) else None,
        "model_routing_kind": model_routing.get("kind") if isinstance(model_routing, dict) else None,
        "model_profile_count": len(model_routing.get("model_profiles") or []) if isinstance(model_routing, dict) else 0,
        "model_recommended_route": model_routing.get("sample_route_decision", {}).get("recommended_route") if isinstance(model_routing, dict) else None,
        "reranking_kind": reranking.get("kind") if isinstance(reranking, dict) else None,
        "reranker_profile_count": len(reranking.get("reranker_profiles") or []) if isinstance(reranking, dict) else 0,
        "reranking_recommended_stage": reranking.get("sample_rerank_decision", {}).get("recommended_stage") if isinstance(reranking, dict) else None,
        "local_memory_kind": local_memory.get("kind") if isinstance(local_memory, dict) else None,
        "local_memory_profile_count": len(local_memory.get("memory_profiles") or []) if isinstance(local_memory, dict) else 0,
        "private_e2ee_cloud_searchable": not bool(local_memory.get("gateway_policy", {}).get("private_e2ee_memory_not_cloud_searchable")) if isinstance(local_memory, dict) else None,
        "search_result_id": search.get("result_id") if isinstance(search, dict) else None,
        "handle_count": len(handles),
        "fetch_kind": fetch.get("kind") if isinstance(fetch, dict) else None,
        "trace_steps": len(trace.get("trace") or []) if isinstance(trace, dict) else 0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        result = self_test(args.base_url)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("ok") else 1
    return serve_stdio(args.base_url)


if __name__ == "__main__":
    raise SystemExit(main())
