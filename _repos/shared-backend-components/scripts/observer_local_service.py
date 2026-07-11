#!/usr/bin/env python3
"""scripts.observer_local_service — the LOCAL backend for the AIDevObserver surface (_repos/aidevobserver/frontend).

This is the service-plane peer the AIDevObserver showcase reaches through a same-origin seam (the
showcase server proxies ``/api/observer/*`` here, exactly like ``/api/teleon/*`` → teleon_local_runtime).
It is a THIN HTTP front-end over the EXISTING observer engine (_repos/teleon/backend/src/teleon/observer) — it rebuilds
NOTHING: review is ``review.review_session``, live spotting is ``router.route_session``, transcript
intake is ``capture.from_transcript``, and zero-install discovery is ``sessions.discover_sessions``.

  GET  /health                      → {"ok": true, "service": "observer"}   (also /healthz /readyz)
  GET  /sessions[?cwd=PATH]         → {"sessions": discover_sessions(cwd)}    (tolerates none → [])
  POST /review  {messages:[...],    → the governed POST-SESSION report (review_session)
                 registry_cwd?}        optionally enriches findings with opt-in local source refs
        OR      {transcript_path:…} → review_session(from_transcript(path))
  POST /live    {messages:[...],    → route_session(events, mode) → {surfaced, summary}
                 mode?:"advisory"}
  POST /agentic {steps:[...], goal?, → supervise an autonomous agent loop (post-run review or, with
                 budget?, monitor?}     monitor:true, intra-run alerts + recommend_halt)
  POST /outcome {session_id, intervention_id, outcome}
                                      → append Accept/Reuse/Dismiss/Ignored outcome metadata
  GET  /outcomes?session_id=...       → read latest outcome memory for a session
  GET  /registry/search?q=...          → opt-in local repo symbol/doc/script candidate source-ref search
  GET  /config                         → model lanes, harness lanes, MCP/plugin/toggle state
  POST /config                         → update local model/harness/toggle state
  POST /ide/plan                       → compose a supervised browser-IDE coding-session launch plan
  POST /ide/session                    → save/update an IDE session and return a unique /ide/<id> URL
  GET  /ide/session/<id>               → load one saved IDE session
  GET  /ide/sessions                   → list recent saved IDE sessions

The seam forwards the FULL path (strip=""), so the service answers both the bare paths above AND the
seam-prefixed ``/api/observer/<path>`` (an internal prefix strip) — so a direct ``curl :PORT/review``
and a same-origin ``/api/observer/review`` both work. CORS is open for local preview.

LAW (mirrors the engine): serves_truth=false on EVERY response; read-only against code and transcripts
(it reads a session to write a report and stores no transcript text); optional triage writes append-only
outcome metadata only. Every finding is a governed CANDIDATE a human triages (discovery ≠ trust).
Synthetic/public session text only. Offline, stdlib-only. Port comes from the local service registry
(_repos/shared-backend-components/architecture/local_service_registry.json — single source; drift-gated by the proof).
"""
from __future__ import annotations

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
# install() prepends every code root so BOTH `scripts.*` and the MOVED `src.teleon.*` resolve on a bare
# `python3 scripts/<f>.py` launch — not only under run_proofs/pytest (which set the full PYTHONPATH for us).
import sys as _sys  # noqa: E402
from pathlib import Path as _Path  # noqa: E402

_here_boot = _Path(__file__).resolve()
_sbc_boot = next((p for p in _here_boot.parents if (p / "scripts" / "_repo_paths.py").exists()), _here_boot.parents[1])
if str(_sbc_boot) not in _sys.path:
    _sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import urllib.error
import urllib.request

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# REUSE the existing observer engine — this service rebuilds nothing of it.
from src.teleon.observer import review_session            # noqa: E402  governed post-session reviewer
from src.teleon.observer.router import MODES, route_session  # noqa: E402  live spotter router + modes
from src.teleon.observer.capture import from_transcript   # noqa: E402  transcript JSONL → events
from src.teleon.observer.sessions import discover_sessions  # noqa: E402  zero-install session discovery
from src.teleon.observer import session_store  # noqa: E402  append-only outcome memory, metadata only
from src.teleon.observer.agentic import monitor_step, review_agentic_run  # noqa: E402  autonomous agent-loop supervision
from src.teleon.observer.registry_search import (  # noqa: E402  candidate source-ref search adapter
    EDGE_FOUNDRY_SOURCE_KIND,
    LOCAL_REGISTRY_ENV,
    enrich_report_with_local_registry,
    global_primitives_enabled,
    local_registry_enabled,
    registry_search_response,
    search_route_level_primitives,
    set_global_primitives_enabled,
    source_ref_keys_from_value,
)
from src.teleon.observer.settings import SERVICE_SETTINGS  # noqa: E402
from scripts._config import (  # noqa: E402
    AIDEVOBSERVER_AUTO_REUSE_POLICY_FLOW,
    AIDEVOBSERVER_AUTO_REUSE_POLICY_ID,
    AIDEVOBSERVER_AUTO_REUSE_POLICY_LABEL,
    AIDEVOBSERVER_AUTO_REUSE_POLICY_STEPS,
    AIDEVOBSERVER_API_POLICY_APPLY_DECISION,
    AIDEVOBSERVER_API_POLICY_EMIT_RESPONSE,
    AIDEVOBSERVER_API_POLICY_FETCH_ACCOUNT,
    AIDEVOBSERVER_API_POLICY_PERSIST_DECISION,
    AIDEVOBSERVER_API_POLICY_PRIMITIVE_SOURCE_PATH,
    AIDEVOBSERVER_API_POLICY_VALIDATE_REQUEST,
    AIDEVOBSERVER_BROWSER_TABLE_EXTRACT,
    AIDEVOBSERVER_BROWSER_TABLE_FETCH_HTML,
    AIDEVOBSERVER_BROWSER_TABLE_PRIMITIVE_SOURCE_PATH,
    AIDEVOBSERVER_BROWSER_POLICY_API_RECIPE_TEMPLATE_ID,
    AIDEVOBSERVER_BROWSER_TABLE_RECIPE_TEMPLATE_ID,
    AIDEVOBSERVER_BROWSER_TABLE_WRITE_CSV,
    AIDEVOBSERVER_BROWSER_TABLE_WRITE_PARQUET,
    AIDEVOBSERVER_BUILD_INTENT_TERMS,
    AIDEVOBSERVER_BUILD_TASK_MIN_CHARS,
    AIDEVOBSERVER_CSV_PRIMITIVE_READ_ROWS,
    AIDEVOBSERVER_CSV_PRIMITIVE_SOURCE_PATH,
    AIDEVOBSERVER_CSV_PRIMITIVE_SUMMARIZE,
    AIDEVOBSERVER_CSV_PRIMITIVE_VALIDATE,
    AIDEVOBSERVER_CSV_RECIPE_TEMPLATE_ID,
    AIDEVOBSERVER_COMPLEX_TASK_MIN_CAPABILITY_GROUPS,
    AIDEVOBSERVER_DEFAULT_MODEL_PROVIDER,
    AIDEVOBSERVER_DETERMINISTIC_WORKER_IDS,
    AIDEVOBSERVER_DETERMINISTIC_MUTATOR_IDS,
    AIDEVOBSERVER_ENABLED_HARNESSES_ENV,
    AIDEVOBSERVER_GLM_MODEL_ENV,
    AIDEVOBSERVER_GLM_MODEL_ID,
    AIDEVOBSERVER_GREETING_TASKS,
    AIDEVOBSERVER_HARNESS_DEFAULTS,
    AIDEVOBSERVER_IDE_GRAPH_COMPONENT_LIMIT,
    AIDEVOBSERVER_IDE_SESSION_DIR_DEFAULT,
    AIDEVOBSERVER_IDE_SESSION_DIR_ENV,
    AIDEVOBSERVER_IDE_SESSION_ID_HEX_CHARS,
    AIDEVOBSERVER_IDE_SESSION_LIST_DEFAULT_LIMIT,
    AIDEVOBSERVER_IDE_SESSION_LIST_MAX_LIMIT,
    AIDEVOBSERVER_IDE_SESSION_TITLE_CHARS,
    AIDEVOBSERVER_INTELLIGENCE_TOGGLE_DEFAULTS,
    AIDEVOBSERVER_INTELLIGENCE_TOGGLE_ENVS,
    AIDEVOBSERVER_KIMI_MODEL_ENV,
    AIDEVOBSERVER_KIMI_MODEL_ID,
    AIDEVOBSERVER_MODEL_PROVIDER_ENV,
    AIDEVOBSERVER_MODEL_PROVIDERS,
    AIDEVOBSERVER_MUTATOR_API_ENDPOINT_WRAPPER,
    AIDEVOBSERVER_MUTATOR_ARTIFACT_REFERENCE,
    AIDEVOBSERVER_MUTATOR_CACHE_WRAPPER,
    AIDEVOBSERVER_MUTATOR_CLI_WRAPPER,
    AIDEVOBSERVER_MUTATOR_CLOUD_FUNCTION_WRAPPER,
    AIDEVOBSERVER_MUTATOR_FIELD_PROJECT,
    AIDEVOBSERVER_MUTATOR_FIELD_RENAME,
    AIDEVOBSERVER_MUTATOR_IDEMPOTENCY_WRAPPER,
    AIDEVOBSERVER_MUTATOR_K8S_CRONJOB_WRAPPER,
    AIDEVOBSERVER_MUTATOR_K8S_DEPLOYMENT_WRAPPER,
    AIDEVOBSERVER_MUTATOR_K8S_JOB_WRAPPER,
    AIDEVOBSERVER_MUTATOR_OUTPUT_WRAPPER,
    AIDEVOBSERVER_MUTATOR_PROVENANCE_WRAPPER,
    AIDEVOBSERVER_MUTATOR_RETRY_WRAPPER,
    AIDEVOBSERVER_MUTATOR_SCHEMA_VALIDATOR_INSERTER,
    AIDEVOBSERVER_NOOP_EXECUTION_MODE,
    AIDEVOBSERVER_OLLAMA_API_KEY_ENV,
    AIDEVOBSERVER_OLLAMA_CLOUD_BASE_URL,
    AIDEVOBSERVER_PLANNER_ROUTE_MAX_TOKENS,
    AIDEVOBSERVER_PLANNER_ROUTE_TEMPLATE_ID,
    AIDEVOBSERVER_PLANNER_TOOL_LOOP_MAX_CALLS,
    AIDEVOBSERVER_PLANNER_TOOL_PREINDEXED,
    AIDEVOBSERVER_PLANNER_TOOL_REGISTRY_SEARCH,
    AIDEVOBSERVER_PLANNER_TOOL_REQUEST_MAX_TOKENS,
    AIDEVOBSERVER_PLANNER_TOOL_RESULT_CHARS,
    AIDEVOBSERVER_PLANNER_TOOL_RESULT_COMPONENT_LIMIT,
    AIDEVOBSERVER_ROUTE_PACKET_ACTION,
    AIDEVOBSERVER_ROUTE_PACKET_BLACKBOX_CHARS,
    AIDEVOBSERVER_ROUTE_PACKET_COMPONENT_LIMIT,
    AIDEVOBSERVER_ROUTE_PACKET_LABEL,
    AIDEVOBSERVER_ROUTE_PACKET_MAX_PROMPT_CHARS,
    AIDEVOBSERVER_ROUTE_PACKET_NO_MATCH,
    AIDEVOBSERVER_ROUTE_BLUEPRINT_QUERY_SUFFIX,
    AIDEVOBSERVER_ROUTE_LEVEL_KINDS,
    AIDEVOBSERVER_ROUTE_LEVEL_OUTPUT_EDGES,
    AIDEVOBSERVER_ROUTE_QUALITY_BASE_SCORE,
    AIDEVOBSERVER_ROUTE_QUALITY_DETERMINISTIC_POINTS,
    AIDEVOBSERVER_ROUTE_QUALITY_EXACT_EDGE_POINTS,
    AIDEVOBSERVER_ROUTE_QUALITY_HARNESS_PENALTY,
    AIDEVOBSERVER_ROUTE_QUALITY_MAX_SCORE,
    AIDEVOBSERVER_ROUTE_QUALITY_NODE_POINTS,
    AIDEVOBSERVER_ROUTE_QUALITY_PLANNER_POINTS,
    AIDEVOBSERVER_ROUTE_QUALITY_TEST_POINTS,
    AIDEVOBSERVER_ROUTE_SLOT_KINDS,
    AIDEVOBSERVER_RUNTIME_TARGET_CLOUD_FUNCTION,
    AIDEVOBSERVER_RUNTIME_TARGET_CONTAINER,
    AIDEVOBSERVER_RUNTIME_TARGET_K8S_CRONJOB,
    AIDEVOBSERVER_RUNTIME_TARGET_K8S_DEPLOYMENT,
    AIDEVOBSERVER_RUNTIME_TARGET_K8S_JOB,
    AIDEVOBSERVER_RUNTIME_TARGET_LOCAL,
    AIDEVOBSERVER_RUNTIME_TARGET_NONE,
    AIDEVOBSERVER_TOKEN_CHAR_DIVISOR,
    AIDEVOBSERVER_TOKEN_ESTIMATE_SOURCE_OVERHEAD,
    AIDEVOBSERVER_VISIBILITY_SCOPE_LOCAL,
    AIDEVOBSERVER_VISIBILITY_SCOPE_PUBLIC,
    AIDEVOBSERVER_VISIBILITY_PRIVATE_INTERNAL_ONLY,
    AIDEVOBSERVER_WORKSPACE_BUILD_MANIFEST_PATH,
    AIDEVOBSERVER_WORKSPACE_PRIMITIVE_IMPORT_ROOT,
    AIDEVOBSERVER_WORKSPACE_PRIMITIVE_ROOT,
    AIDEVOBSERVER_WORKSPACE_SOURCE_PREFIX,
    AIDEVOBSERVER_WORKSPACE_TEST_PATH,
    AIDEVOBSERVER_WORKSPACE_TEST_TIMEOUT_SECONDS,
    DEFAULT_OLLAMA_HOST,
    OLLAMA_HOST_ENV,
)

SERVICE_ID = "observer_runtime"
REGISTRY_PATH = _resource("architecture") / "local_service_registry.json"
VERSION = "1.0"
DEFAULT_LIVE_MODE = "advisory"          # the WHEN axis default for /live (graduated-restraint mode)
MAX_BODY_BYTES = SERVICE_SETTINGS.max_body_bytes
_API_PREFIX = "/api/observer"           # the same-origin seam prefix the showcase forwards (strip="")
_TRUE_VALUES = {"1", "true", "yes", "on"}
_SAFE_ID = re.compile(rf"^[A-Za-z0-9_.:-]{{1,{SERVICE_SETTINGS.safe_id_max_chars}}}$")
_LOCAL_REGISTRY_ENV = LOCAL_REGISTRY_ENV
IDE_RUN_DIR = _resource(".agent") / "aidevobserver" / "ide-runs"
IDE_RUN_ID_HEX_CHARS = 16
IDE_RUN_OUTPUT_TAIL_CHARS = 8000
IDE_RUN_DEFAULT_TIMEOUT_SECONDS = 900
SELF_TEST_HTTP_TIMEOUT_SECONDS = 45
_CONFIG_LOCK = threading.Lock()
_RUNTIME_CONFIG: dict[str, object] = {
    "model_provider": os.environ.get(AIDEVOBSERVER_MODEL_PROVIDER_ENV, AIDEVOBSERVER_DEFAULT_MODEL_PROVIDER).strip()
    or AIDEVOBSERVER_DEFAULT_MODEL_PROVIDER,
    "toggles": {},
    "enabled_harnesses": [],
}


def _flag_enabled(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    return raw.strip().lower() in _TRUE_VALUES


def _set_flag(name: str, enabled: bool) -> None:
    os.environ[name] = "1" if enabled else "0"


def _configured_toggles() -> dict[str, bool]:
    with _CONFIG_LOCK:
        overrides = dict(_RUNTIME_CONFIG.get("toggles") or {})
    out: dict[str, bool] = {}
    for key, env_name in AIDEVOBSERVER_INTELLIGENCE_TOGGLE_ENVS.items():
        default = AIDEVOBSERVER_INTELLIGENCE_TOGGLE_DEFAULTS.get(key, False)
        if key in overrides:
            out[key] = bool(overrides[key])
        else:
            out[key] = _flag_enabled(env_name, default)
    out["global_primitives"] = global_primitives_enabled()
    out["local_registry"] = _local_registry_enabled()
    out["local_sessions"] = _local_session_discovery_enabled()
    return out


def _model_provider() -> str:
    with _CONFIG_LOCK:
        provider = str(_RUNTIME_CONFIG.get("model_provider") or "").strip()
    if provider not in AIDEVOBSERVER_MODEL_PROVIDERS:
        return AIDEVOBSERVER_DEFAULT_MODEL_PROVIDER
    return provider


def _configured_harnesses() -> list[str]:
    with _CONFIG_LOCK:
        configured = _RUNTIME_CONFIG.get("enabled_harnesses") or []
    if isinstance(configured, list) and configured:
        return [str(key) for key in configured if str(key) in AIDEVOBSERVER_HARNESS_DEFAULTS]
    raw = os.environ.get(AIDEVOBSERVER_ENABLED_HARNESSES_ENV, "").strip()
    if raw:
        out = [part.strip() for part in raw.split(",") if part.strip() in AIDEVOBSERVER_HARNESS_DEFAULTS]
        if out:
            return out
    return ["opencode"]


def _component_is_actionable(component: dict) -> bool:
    fit = str(component.get("edge_fit") or "").strip().lower()
    source_ref = component.get("source_ref") or {}
    source_name = str(source_ref.get("name") or "").strip().rsplit(".", 1)[-1]
    if source_name.startswith("_"):
        return False
    return fit in {"exact_match", "deterministic_edit_match"}


def _actionable_components(components: list[dict], limit: int | None = None) -> list[dict]:
    rows = [component for component in components if _component_is_actionable(component)]
    return rows[:limit] if limit is not None else rows


def _compact_text(value: object, limit: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _blackbox_does(component: dict) -> str:
    blackbox = component.get("blackbox")
    if isinstance(blackbox, dict):
        return str(blackbox.get("does") or blackbox.get("summary") or "")
    return str(blackbox or "")


def _mutation_id(item: object) -> str:
    if isinstance(item, dict):
        return str(
            item.get("mutator")
            or item.get("id")
            or item.get("mutation")
            or item.get("mutator_agent_id")
            or ""
        )
    return str(item or "")


def _mutation_agent_id(item: object) -> str:
    if isinstance(item, dict):
        return str(item.get("mutator_agent_id") or item.get("id") or item.get("mutator") or "")
    mutation = _mutation_id(item)
    return f"mut:deterministic:{mutation}@1" if mutation else ""


def _mutation_ids(items: object) -> list[str]:
    if not isinstance(items, list):
        return []
    out: list[str] = []
    for item in items:
        mutation = _mutation_id(item)
        if mutation and mutation not in out:
            out.append(mutation)
    return out


def _mutation_option(
    mutator: str,
    *,
    reason: str,
    input_edge: str,
    output_edge: str,
    target_input: str | None = None,
    target_output: str | None = None,
    effect_delta: str = "preserve",
    preconditions: list[str] | None = None,
    proof_obligations: list[str] | None = None,
    runtime_targets: list[str] | None = None,
) -> dict:
    return {
        "mutator": mutator,
        "mutator_agent_id": f"mut:deterministic:{mutator}@1",
        "reason": reason,
        "input_edge_before": input_edge,
        "output_edge_before": output_edge,
        "target_edge_template": {
            "input": target_input or input_edge,
            "output": target_output or output_edge,
            "mutation": mutator,
        },
        "effect_delta": effect_delta,
        "preconditions": preconditions or [],
        "proof_obligations": proof_obligations or [],
        "runtime_targets": runtime_targets or [],
        "candidate": True,
        "serves_truth": False,
    }


def _normalize_mutation_options(values: object) -> list[dict]:
    if not isinstance(values, list):
        return []
    normalized: list[dict] = []
    seen: set[str] = set()
    for value in values:
        mutator = _mutation_id(value)
        if not mutator or mutator in seen:
            continue
        seen.add(mutator)
        if isinstance(value, dict):
            record = {**value}
            record.setdefault("mutator", mutator)
            record.setdefault("mutator_agent_id", _mutation_agent_id(record))
            record.setdefault("candidate", True)
            record.setdefault("serves_truth", False)
            normalized.append(record)
        else:
            normalized.append({
                "mutator": mutator,
                "mutator_agent_id": _mutation_agent_id(value),
                "reason": "selected by registry edge-fit metadata",
                "candidate": True,
                "serves_truth": False,
            })
    return normalized


def _default_component_mutations(input_edge: str, output_edge: str, name: str, does: str = "") -> list[dict]:
    text = f"{input_edge} {output_edge} {name} {does}".lower()
    options: list[dict] = [
        _mutation_option(
            AIDEVOBSERVER_MUTATOR_OUTPUT_WRAPPER,
            reason="output can be wrapped with provenance metadata",
            input_edge=input_edge,
            output_edge=output_edge,
            target_output=f"Wrapped[{output_edge}]",
            effect_delta="add_metadata",
            proof_obligations=["payload_preserved"],
        )
    ]
    if "dict" in text or "request" in text or "response" in text:
        options.extend([
            _mutation_option(
                AIDEVOBSERVER_MUTATOR_SCHEMA_VALIDATOR_INSERTER,
                reason="record/request edge can be guarded by deterministic schema validation",
                input_edge=input_edge,
                output_edge=output_edge,
                target_output=f"Validated[{output_edge}]",
                effect_delta="add_validation_gate",
                preconditions=["schema_available"],
                proof_obligations=["schema_contract_declared", "invalid_payload_blocks_execution"],
            ),
            _mutation_option(
                AIDEVOBSERVER_MUTATOR_FIELD_RENAME,
                reason="record-shaped edge can accept explicit field aliases",
                input_edge=input_edge,
                output_edge=output_edge,
                preconditions=["source_and_target_field_names_declared"],
                proof_obligations=["field_mapping_unambiguous"],
            ),
            _mutation_option(
                AIDEVOBSERVER_MUTATOR_FIELD_PROJECT,
                reason="record-shaped edge can project safe subsets",
                input_edge=input_edge,
                output_edge=output_edge,
                preconditions=["required_fields_known"],
                proof_obligations=["projected_fields_declared", "no_required_field_dropped"],
            ),
            _mutation_option(
                AIDEVOBSERVER_MUTATOR_API_ENDPOINT_WRAPPER,
                reason="request/response-shaped edge can be exposed as an API endpoint",
                input_edge=input_edge,
                output_edge=output_edge,
                target_input=f"HttpRequest[{input_edge}]",
                target_output=f"HttpResponse[{output_edge}]",
                effect_delta="api_boundary",
                proof_obligations=["request_schema_validated", "response_schema_validated"],
            ),
            _mutation_option(
                AIDEVOBSERVER_MUTATOR_CLOUD_FUNCTION_WRAPPER,
                reason="request/response-shaped edge can be emitted as a cloud-function handler",
                input_edge=input_edge,
                output_edge=output_edge,
                target_input=f"CloudFunctionRequest[{input_edge}]",
                target_output=f"CloudFunctionResponse[{output_edge}]",
                effect_delta="runtime_wrapper",
                runtime_targets=[AIDEVOBSERVER_RUNTIME_TARGET_CLOUD_FUNCTION],
                proof_obligations=["handler_contract_declared", "cold_start_inputs_bounded"],
            ),
        ])
    if any(token in text for token in ("url", "html", "browser", "playwright", "fetch", "visit", "network")):
        options.extend([
            _mutation_option(
                AIDEVOBSERVER_MUTATOR_CACHE_WRAPPER,
                reason="network/browser read can use bounded cache",
                input_edge=input_edge,
                output_edge=output_edge,
                preconditions=["cache_key_fields_declared"],
                proof_obligations=["cache_key_no_secret", "ttl_policy_declared"],
            ),
            _mutation_option(
                AIDEVOBSERVER_MUTATOR_RETRY_WRAPPER,
                reason="network/browser read can use bounded retry",
                input_edge=input_edge,
                output_edge=output_edge,
                preconditions=["retry_policy_declared"],
                proof_obligations=["retry_bound_declared", "retry_errors_typed"],
            ),
        ])
    if any(token in text for token in ("path", "artifact", "csv", "parquet", "file", "table")):
        options.append(_mutation_option(
            AIDEVOBSERVER_MUTATOR_ARTIFACT_REFERENCE,
            reason="file/table edge can pass ArtifactRef instead of inline payload",
            input_edge=input_edge,
            output_edge=output_edge,
            target_input=input_edge.replace("Path", "ArtifactRef"),
            target_output=output_edge.replace("Path", "ArtifactRef"),
            effect_delta="artifact_ref",
            proof_obligations=["artifact_digest_stable", "artifact_ref_resolves"],
        ))
    if any(token in text for token in ("write", "persist", "receipt", "decision", "database", "fs.write")):
        options.append(_mutation_option(
            AIDEVOBSERVER_MUTATOR_IDEMPOTENCY_WRAPPER,
            reason="write/persist edge should be protected by idempotency key",
            input_edge=input_edge,
            output_edge=output_edge,
            target_input=f"{input_edge}+IdempotencyKey",
            preconditions=["idempotency_key_available"],
            proof_obligations=["duplicate_run_same_receipt", "idempotency_key_digest_logged"],
        ))
    if any(token in text for token in ("api", "endpoint", "request", "response", "cloud", "k8s", "kubernetes")):
        options.extend([
            _mutation_option(
                AIDEVOBSERVER_MUTATOR_CLI_WRAPPER,
                reason="route can be exposed as a CLI entry point for local/CI execution",
                input_edge=input_edge,
                output_edge=output_edge,
                target_input=f"CommandArgs[{input_edge}]",
                target_output=f"CommandRunReceipt[{output_edge}]",
                effect_delta="cli_boundary",
                proof_obligations=["argv_schema_declared", "exit_codes_typed"],
            ),
            _mutation_option(
                AIDEVOBSERVER_MUTATOR_K8S_JOB_WRAPPER,
                reason="compiled route can be emitted as a Kubernetes Job",
                input_edge=input_edge,
                output_edge=output_edge,
                target_input=f"KubernetesJobSpec[{input_edge}]",
                target_output=f"KubernetesJobReceipt[{output_edge}]",
                effect_delta="k8s_runtime_wrapper",
                runtime_targets=[AIDEVOBSERVER_RUNTIME_TARGET_K8S_JOB],
                proof_obligations=["job_manifest_valid", "restart_policy_declared"],
            ),
            _mutation_option(
                AIDEVOBSERVER_MUTATOR_K8S_DEPLOYMENT_WRAPPER,
                reason="compiled API route can be emitted as a Kubernetes Deployment and Service",
                input_edge=input_edge,
                output_edge=output_edge,
                target_input=f"KubernetesDeploymentSpec[{input_edge}]",
                target_output=f"KubernetesServiceReceipt[{output_edge}]",
                effect_delta="k8s_runtime_wrapper",
                runtime_targets=[AIDEVOBSERVER_RUNTIME_TARGET_K8S_DEPLOYMENT],
                proof_obligations=["deployment_manifest_valid", "readiness_probe_declared"],
            ),
            _mutation_option(
                AIDEVOBSERVER_MUTATOR_K8S_CRONJOB_WRAPPER,
                reason="compiled route can be emitted as a Kubernetes CronJob when scheduled",
                input_edge=input_edge,
                output_edge=output_edge,
                target_input=f"KubernetesCronJobSpec[{input_edge}]",
                target_output=f"KubernetesCronJobReceipt[{output_edge}]",
                effect_delta="k8s_runtime_wrapper",
                runtime_targets=[AIDEVOBSERVER_RUNTIME_TARGET_K8S_CRONJOB],
                preconditions=["schedule_declared"],
                proof_obligations=["cron_schedule_declared", "concurrency_policy_declared"],
            ),
        ])
    if any(token in text for token in ("source", "artifact", "html", "table", "csv", "parquet", "decision", "receipt")):
        options.append(_mutation_option(
            AIDEVOBSERVER_MUTATOR_PROVENANCE_WRAPPER,
            reason="effectful/artifact edge can attach provenance metadata",
            input_edge=input_edge,
            output_edge=output_edge,
            target_output=f"Provenanced[{output_edge}]",
            effect_delta="add_metadata",
            proof_obligations=["provenance_payload_preserved", "source_ref_attached"],
        ))
    return _normalize_mutation_options(options)


def _component_edge_context(components: list[dict], limit: int = AIDEVOBSERVER_ROUTE_PACKET_COMPONENT_LIMIT) -> list[str]:
    out: list[str] = []
    for component in _actionable_components(components, limit=limit):
        contract = component.get("contract") or {}
        source_ref = component.get("source_ref") or {}
        mutations = component.get("mutations") or []
        mutation_ids = _mutation_ids(mutations)
        out.append(
            "- "
            f"id:{component.get('label') or 'component'}; "
            f"edge:{contract.get('input') or 'unknown'}=>{contract.get('output') or 'unknown'}; "
            f"does:{_compact_text(_blackbox_does(component), AIDEVOBSERVER_ROUTE_PACKET_BLACKBOX_CHARS)}; "
            f"mut:{','.join(mutation_ids) or '-'}; "
            f"ref:{source_ref.get('path') or '-'}::{source_ref.get('name') or '-'}"
        )
    return out


def _deterministic_worker_catalog() -> list[dict]:
    descriptions = {
        "edge_matcher": "Matches user intent to reusable components by input edge, output edge, and blackbox behavior.",
        "route_recipe_compiler": "Turns selected components into an ordered recipe/DAG before any coding harness runs.",
        "template_materializer": "Writes framework files from a known template and selected component imports.",
        "artifact_writer": "Persists generated task, bundle, recipe, code, and report files as workspace artifacts.",
        "workspace_proof_runner": "Runs deterministic proof checks on generated files before marking the run succeeded.",
        "ledger_writer": "Records what was selected, materialized, and proved without making registry truth claims.",
        "gap_recorder": "Records missing-component opportunities when no high-confidence reusable route exists.",
    }
    return [
        {
            "id": worker_id,
            "description": descriptions.get(worker_id, worker_id.replace("_", " ")),
            "deterministic": True,
            "model_calls": 0,
            "candidate": True,
            "serves_truth": False,
        }
        for worker_id in AIDEVOBSERVER_DETERMINISTIC_WORKER_IDS
    ]


def _ide_task_edges(task: str) -> dict[str, str | None]:
    """Infer a coarse desired edge from the plain task.

    This is deliberately small and deterministic. The LLM does not need to ask
    the user to say "search the registry"; the observer can infer enough edge
    shape for common development requests and still keep the result candidate-
    only until proof.
    """

    text = task.lower()
    if _ide_task_is_complex_composition(task):
        return {
            "requested_input": "PlainTask",
            "requested_output": "CompositeImplementationPlan",
        }
    if _ide_task_is_browser_table_export(task):
        return {
            "requested_input": "Url",
            "requested_output": "TableExportArtifacts",
        }
    if "csv" in text and any(term in text for term in ("upload", "uploaded", "import", "ingest", "vendor")):
        return {
            "requested_input": "Path",
            "requested_output": "list[dict[str,str]]",
        }
    if "json" in text and any(term in text for term in ("extract", "schema", "document", "invoice")):
        return {
            "requested_input": "DocumentArtifact",
            "requested_output": "dict[str,object]",
        }
    if any(term in text for term in ("classify", "classification", "route ticket", "routing")):
        return {
            "requested_input": "str",
            "requested_output": "dict[str,object]",
        }
    return {"requested_input": None, "requested_output": None}


def _ide_task_is_csv_import(task: str) -> bool:
    text = task.lower()
    return "csv" in text and any(term in text for term in ("upload", "uploaded", "import", "ingest", "vendor"))


def _ide_task_is_browser_table_export(task: str) -> bool:
    text = task.lower()
    has_browser_source = any(term in text for term in (
        "playwright",
        "browser",
        "site",
        "web page",
        "webpage",
        "scrape",
        "visit",
        "crawl",
    ))
    has_table_output = "table" in text or "tables" in text
    has_export = any(term in text for term in ("csv", "parquet", "dataset", "save", "export"))
    return has_browser_source and has_table_output and has_export


def _ide_task_capability_groups(task: str) -> set[str]:
    text = task.lower()
    groups: set[str] = set()
    if _ide_task_is_csv_import(task):
        groups.add("csv_import")
    if _ide_task_is_browser_table_export(task):
        groups.add("browser_table_export")
    if "api" in text or "endpoint" in text or "json request" in text:
        groups.add("api_boundary")
    if "account state" in text or "account id" in text or "account_id" in text:
        groups.add("account_state")
    if "policy" in text or "decision" in text:
        groups.add("policy_decision")
    if "persist" in text or "idempotency" in text or "database" in text or "receipt" in text:
        groups.add("persistence")
    if "response" in text or "audit metadata" in text:
        groups.add("response_emit")
    return groups


def _ide_task_is_complex_composition(task: str) -> bool:
    return len(_ide_task_capability_groups(task)) >= AIDEVOBSERVER_COMPLEX_TASK_MIN_CAPABILITY_GROUPS


def _ide_task_has_build_intent(task: str) -> bool:
    text = " ".join(str(task or "").strip().lower().split())
    if not text or text in AIDEVOBSERVER_GREETING_TASKS:
        return False
    if len(text) < AIDEVOBSERVER_BUILD_TASK_MIN_CHARS and " " not in text:
        return False
    tokens = set(re.findall(r"[a-z][a-z0-9_-]*", text))
    return any(term in text or term in tokens for term in AIDEVOBSERVER_BUILD_INTENT_TERMS)


def _csv_import_component(label: str, name: str, input_edge: str, output_edge: str, does: str) -> dict:
    return {
        "label": label,
        "source_kind": "first_party_repo_record",
        "blackbox": {"does": does},
        "contract": {"input": input_edge, "output": output_edge},
        "edge_fit": "exact_match",
        "mutations": _default_component_mutations(input_edge, output_edge, name, does),
        "source_ref": {
            "path": AIDEVOBSERVER_CSV_PRIMITIVE_SOURCE_PATH,
            "name": name,
            "line": None,
        },
        "candidate": True,
        "serves_truth": False,
    }


def _browser_table_component(label: str, name: str, input_edge: str, output_edge: str, does: str) -> dict:
    return {
        "label": label,
        "source_kind": "first_party_repo_record",
        "blackbox": {"does": does},
        "contract": {"input": input_edge, "output": output_edge},
        "edge_fit": "exact_match",
        "mutations": _default_component_mutations(input_edge, output_edge, name, does),
        "source_ref": {
            "path": AIDEVOBSERVER_BROWSER_TABLE_PRIMITIVE_SOURCE_PATH,
            "name": name,
            "line": None,
        },
        "candidate": True,
        "serves_truth": False,
    }


def _api_policy_component(label: str, name: str, input_edge: str, output_edge: str, does: str) -> dict:
    return {
        "label": label,
        "source_kind": "first_party_repo_record",
        "blackbox": {"does": does},
        "contract": {"input": input_edge, "output": output_edge},
        "edge_fit": "exact_match",
        "mutations": _default_component_mutations(input_edge, output_edge, name, does),
        "source_ref": {
            "path": AIDEVOBSERVER_API_POLICY_PRIMITIVE_SOURCE_PATH,
            "name": name,
            "line": None,
        },
        "candidate": True,
        "serves_truth": False,
    }


def _browser_table_components() -> list[dict]:
    return [
        _browser_table_component(
            "teleon.ingest.browser.fetch_page_html_with_playwright",
            AIDEVOBSERVER_BROWSER_TABLE_FETCH_HTML,
            "Url",
            "HtmlDocument",
            "Visit a web page with Playwright when available, falling back to deterministic HTTP fetch.",
        ),
        _browser_table_component(
            "teleon.ingest.browser.extract_html_tables",
            AIDEVOBSERVER_BROWSER_TABLE_EXTRACT,
            "HtmlDocument",
            "list[HtmlTable]",
            "Extract HTML tables into row dictionaries without asking a model to parse the page.",
        ),
        _browser_table_component(
            "teleon.ingest.browser.write_table_csv",
            AIDEVOBSERVER_BROWSER_TABLE_WRITE_CSV,
            "HtmlTable+Path",
            "CsvArtifact",
            "Persist one extracted table as a CSV artifact.",
        ),
        _browser_table_component(
            "teleon.ingest.browser.write_table_parquet",
            AIDEVOBSERVER_BROWSER_TABLE_WRITE_PARQUET,
            "HtmlTable+Path",
            "ParquetArtifact",
            "Persist one extracted table as a Parquet artifact when pyarrow-compatible dependencies are installed.",
        ),
    ]


def _api_policy_components() -> list[dict]:
    return [
        _api_policy_component(
            "teleon.api.policy.validate_company_enrichment_request",
            AIDEVOBSERVER_API_POLICY_VALIDATE_REQUEST,
            "dict[str,object]",
            "ValidatedCompanyEnrichmentRequest",
            "Validate company-domain/account JSON requests.",
        ),
        _api_policy_component(
            "teleon.api.policy.fetch_account_state",
            AIDEVOBSERVER_API_POLICY_FETCH_ACCOUNT,
            "ValidatedCompanyEnrichmentRequest",
            "AccountState",
            "Fetch the account state snapshot used by downstream policy.",
        ),
        _api_policy_component(
            "teleon.api.policy.apply_enrichment_policy",
            AIDEVOBSERVER_API_POLICY_APPLY_DECISION,
            "ValidatedCompanyEnrichmentRequest+AccountState+Artifacts",
            "PolicyDecision",
            "Apply deterministic enrichment policy to account state and extracted artifacts.",
        ),
        _api_policy_component(
            "teleon.api.policy.persist_policy_decision",
            AIDEVOBSERVER_API_POLICY_PERSIST_DECISION,
            "PolicyDecision+IdempotencyKey+Path",
            "DecisionReceipt",
            "Persist policy decisions with an idempotency key.",
        ),
        _api_policy_component(
            "teleon.api.policy.emit_api_response",
            AIDEVOBSERVER_API_POLICY_EMIT_RESPONSE,
            "ValidatedCompanyEnrichmentRequest+PolicyDecision+DecisionReceipt+Artifacts",
            "ApiResponse",
            "Emit a JSON-compatible API response with artifact paths and audit metadata.",
        ),
    ]


def _preindexed_components_for_groups(groups: set[str]) -> list[dict]:
    components: list[dict] = []
    if "browser_table_export" in groups:
        components.extend(_browser_table_components())
    if groups & {"api_boundary", "account_state", "policy_decision", "persistence", "response_emit"}:
        components.extend(_api_policy_components())
    if "csv_import" in groups:
        components.extend([
            _csv_import_component(
                "teleon.ingest.csv.read_uploaded_csv_rows",
                AIDEVOBSERVER_CSV_PRIMITIVE_READ_ROWS,
                "Path",
                "list[CsvRow]",
                "Read an uploaded CSV file into dictionaries keyed by header names.",
            ),
            _csv_import_component(
                "teleon.ingest.csv.validate_required_columns",
                AIDEVOBSERVER_CSV_PRIMITIVE_VALIDATE,
                "list[CsvRow]+tuple[str,...]",
                "CsvImportResult",
                "Validate required CSV columns and return a deterministic import result.",
            ),
            _csv_import_component(
                "teleon.ingest.csv.summarize_csv_import",
                AIDEVOBSERVER_CSV_PRIMITIVE_SUMMARIZE,
                "CsvImportResult",
                "dict[str,object]",
                "Convert a CSV import result into a JSON-compatible response packet.",
            ),
        ])
    return _dedupe_components(components)


def _preindexed_ide_components(task: str) -> list[dict]:
    """Return fast exact primitive cards for common routes before broad search.

    These are real first-party primitives, not synthetic placeholders. The
    broad registry remains available for ambiguous tasks, but obvious tasks
    should not spend seconds indexing the repo or tokens asking a model to find
    a function we already know how to call.
    """

    groups = _ide_task_capability_groups(task)
    if _ide_task_is_complex_composition(task):
        return _preindexed_components_for_groups(groups)
    if _ide_task_is_browser_table_export(task):
        return _browser_table_components()
    if _ide_task_is_csv_import(task):
        return _preindexed_components_for_groups({"csv_import"})
    return [
    ]


def _component_key(component: dict) -> tuple[str, str, str]:
    source_ref = component.get("source_ref") or {}
    return (
        str(component.get("label") or ""),
        str(source_ref.get("path") or ""),
        str(source_ref.get("name") or ""),
    )


def _dedupe_components(components: list[dict]) -> list[dict]:
    seen: set[tuple[str, str, str]] = set()
    out: list[dict] = []
    for component in components:
        key = _component_key(component)
        if key in seen:
            continue
        seen.add(key)
        out.append(component)
    return out


def _component_kind(component: dict) -> str:
    return str(component.get("kind") or component.get("record_type") or "").strip()


def _component_output_edge(component: dict) -> str:
    contract = component.get("contract") if isinstance(component.get("contract"), dict) else {}
    return str(contract.get("output") or component.get("output_edge") or "").strip()


def _component_is_route_level(component: dict) -> bool:
    return (
        _component_output_edge(component) in set(AIDEVOBSERVER_ROUTE_LEVEL_OUTPUT_EDGES)
        or _component_kind(component) in set(AIDEVOBSERVER_ROUTE_LEVEL_KINDS)
    )


def _component_is_route_slot(component: dict) -> bool:
    return _component_kind(component) in set(AIDEVOBSERVER_ROUTE_SLOT_KINDS)


def _component_route_rank(component: dict) -> tuple[int, str]:
    if _component_is_route_level(component):
        return (0, str(component.get("label") or ""))
    if _component_is_route_slot(component):
        return (1, str(component.get("label") or ""))
    return (2, str(component.get("label") or ""))


def _component_from_registry_hit(hit: dict) -> dict | None:
    if not isinstance(hit, dict):
        return None
    hit_name = hit.get("name")
    hit_source_kind = hit.get("source_kind")
    card = hit.get("reuse_card")
    if not isinstance(card, dict):
        card = hit
    contract = card.get("contract") or {}
    source_ref = card.get("source_ref") or {}
    edge_fit_raw = card.get("edge_fit") or {}
    edge_fit = edge_fit_raw if isinstance(edge_fit_raw, dict) else {"fit_class": str(edge_fit_raw)}
    mutation_options = (
        card.get("edge_mutation_options")
        or card.get("mutations")
        or edge_fit.get("mutation_options")
        or edge_fit.get("required_mutations")
        or []
    )
    return {
        "label": card.get("label") or hit_name or card.get("primitive_id") or "candidate component",
        "kind": card.get("kind") or card.get("record_type"),
        "primitive_id": card.get("primitive_id") or hit.get("primitive_id"),
        "source_kind": card.get("source_kind") or hit_source_kind or "registry_candidate",
        "blackbox": card.get("blackbox"),
        "contract": {
            "input": contract.get("input") or card.get("input_edge") or "unknown",
            "output": contract.get("output") or card.get("output_edge") or "unknown",
        },
        "edge_fit": edge_fit.get("fit_class") or "candidate",
        "mutations": _normalize_mutation_options(mutation_options),
        "source_ref": {
            "path": source_ref.get("path"),
            "name": source_ref.get("name"),
            "line": source_ref.get("line"),
        },
        "surface_visibility": card.get("surface_visibility") or hit.get("surface_visibility"),
        "visibility_scope": card.get("visibility_scope") or hit.get("visibility_scope"),
        "score": card.get("score") or hit.get("score"),
        "quality_score": card.get("quality_score") or hit.get("quality_score"),
        "candidate": True,
        "serves_truth": False,
    }


def _components_from_registry_payload(payload: dict) -> list[dict]:
    components: list[dict] = []
    for hit in payload.get("hits", [])[:AIDEVOBSERVER_IDE_GRAPH_COMPONENT_LIMIT]:
        component = _component_from_registry_hit(hit)
        if component:
            components.append(component)
    return components


def _registry_components_for_task(
    task: str,
    body: dict,
    *,
    route_level: bool = False,
    limit: int = AIDEVOBSERVER_IDE_GRAPH_COMPONENT_LIMIT,
) -> list[dict]:
    edges = _ide_task_edges(task)
    registry_cwd = str(body.get("registry_cwd") or "") or None
    query = task
    requested_output = body.get("requested_output") or edges.get("requested_output")
    visibility_scope = body.get("visibility_scope") or (
        AIDEVOBSERVER_VISIBILITY_SCOPE_LOCAL if registry_cwd else AIDEVOBSERVER_VISIBILITY_SCOPE_PUBLIC
    )
    if route_level:
        query = f"{task} {AIDEVOBSERVER_ROUTE_BLUEPRINT_QUERY_SUFFIX}"
        requested_output = "PipelineRecipe"
        route_hits = search_route_level_primitives(
            query,
            limit=limit,
            requested_input=body.get("requested_input") or edges.get("requested_input"),
            requested_output=requested_output,
            visibility_scope=visibility_scope,
        )
        route_cards = [
            component
            for component in (
                _component_from_registry_hit(
                    {
                        "source_kind": hit.get("source_kind"),
                        "primitive_id": hit.get("primitive_id"),
                        "score": hit.get("score"),
                        "quality_score": hit.get("quality_score"),
                        "surface_visibility": hit.get("surface_visibility"),
                        "visibility_scope": hit.get("visibility_scope") or visibility_scope,
                        "reuse_card": hit,
                    }
                )
                for hit in route_hits
            )
            if component and (_component_is_route_level(component) or _component_is_route_slot(component))
        ]
        return sorted(route_cards, key=_component_route_rank)
    status, payload = registry_search_response(
        query,
        registry_cwd,
        limit=limit,
        requested_input=body.get("requested_input") or edges.get("requested_input"),
        requested_output=requested_output,
        visibility_scope=visibility_scope,
    )
    if status != 200:
        return []
    components = _components_from_registry_payload(payload)
    if route_level:
        route_cards = [
            component
            for component in components
            if _component_is_route_level(component) or _component_is_route_slot(component)
        ]
        return sorted(route_cards, key=_component_route_rank)
    return components


def _planner_route_packet_lines(planner_result: dict | None) -> list[str]:
    if not isinstance(planner_result, dict):
        return []
    route = planner_result.get("route") if isinstance(planner_result.get("route"), dict) else {}
    nodes = route.get("nodes") if isinstance(route.get("nodes"), list) else []
    out: list[str] = []
    for node in nodes[:AIDEVOBSERVER_PLANNER_TOOL_RESULT_COMPONENT_LIMIT]:
        if not isinstance(node, dict):
            continue
        out.append(
            "- "
            f"{node.get('id') or node.get('slot') or 'node'}; "
            f"uses:{node.get('candidate_alias') or node.get('component_alias') or node.get('component') or '-'}; "
            f"in:{node.get('input') or '-'}; out:{node.get('output') or '-'}; "
            f"why:{_compact_text(node.get('why') or node.get('blackbox') or '', 90)}"
        )
    return out


def _observer_wrapped_task(task: str, components: list[dict] | None = None, planner_result: dict | None = None) -> str:
    edge_context = _component_edge_context(components or [])
    selected = "\n".join(edge_context) if edge_context else "- " + AIDEVOBSERVER_ROUTE_PACKET_NO_MATCH
    route_context = _route_context_components(components or [], limit=2)
    blueprint_lines: list[str] = []
    for component in route_context:
        contract = component.get("contract") if isinstance(component.get("contract"), dict) else {}
        source_ref = component.get("source_ref") if isinstance(component.get("source_ref"), dict) else {}
        blueprint_lines.append(
            "- "
            f"id:{component.get('label') or 'route'}; "
            f"edge:{contract.get('input') or 'unknown'}=>{contract.get('output') or 'unknown'}; "
            f"kind:{_component_kind(component) or '-'}; "
            f"does:{_compact_text(_blackbox_does(component), AIDEVOBSERVER_ROUTE_PACKET_BLACKBOX_CHARS)}; "
            f"ref:{source_ref.get('path') or '-'}::{source_ref.get('name') or '-'}"
        )
    blueprint_block = ("route_blueprints:\n" + "\n".join(blueprint_lines) + "\n") if blueprint_lines else ""
    planner_route_lines = _planner_route_packet_lines(planner_result)
    route_block = ("planner_route:\n" + "\n".join(planner_route_lines) + "\n") if planner_route_lines else ""
    packet = (
        f"TASK: {task}\n"
        f"{AIDEVOBSERVER_ROUTE_PACKET_LABEL}\n"
        f"action: {AIDEVOBSERVER_ROUTE_PACKET_ACTION}\n"
        f"{blueprint_block}"
        "selected:\n"
        f"{selected}\n"
        f"{route_block}"
    )
    if len(packet) <= AIDEVOBSERVER_ROUTE_PACKET_MAX_PROMPT_CHARS:
        return packet
    selected = "\n".join(_component_edge_context(components or [], limit=1)) or "- " + AIDEVOBSERVER_ROUTE_PACKET_NO_MATCH
    blueprint_block = ("route_blueprints:\n" + blueprint_lines[0] + "\n") if blueprint_lines else ""
    route_block = ("planner_route:\n" + planner_route_lines[0] + "\n") if planner_route_lines else ""
    return (
        f"TASK: {_compact_text(task, AIDEVOBSERVER_ROUTE_PACKET_BLACKBOX_CHARS)}\n"
        f"{AIDEVOBSERVER_ROUTE_PACKET_LABEL}\n"
        f"action: {AIDEVOBSERVER_ROUTE_PACKET_ACTION}\n"
        f"{blueprint_block}"
        "selected:\n"
        f"{selected}\n"
        f"{route_block}"
    )


def _ide_plan_components(task: str, body: dict) -> list[dict]:
    preindexed = _preindexed_ide_components(task)
    if _ide_task_is_complex_composition(task):
        if _can_materialize_browser_policy_route(preindexed, None):
            return preindexed
        route_cards = _registry_components_for_task(
            task,
            body,
            route_level=True,
            limit=AIDEVOBSERVER_PLANNER_TOOL_RESULT_COMPONENT_LIMIT,
        )
        if route_cards:
            return _dedupe_components(route_cards + preindexed)
    if preindexed:
        return preindexed
    return _registry_components_for_task(task, body)


def _source_module(path: str | None) -> str | None:
    if not path or not path.endswith(".py"):
        return None
    module = path[:-3].replace("/", ".")
    if module.endswith(".__init__"):
        module = module[:-9]
    return module or None


def _source_callable_name(source_ref: dict) -> str | None:
    raw = str(source_ref.get("name") or "").strip()
    if not raw:
        return None
    if "." in raw:
        raw = raw.rsplit(".", 1)[-1]
    return raw if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", raw) else None


def _component_imports(components: list[dict]) -> list[str]:
    by_module: dict[str, set[str]] = {}
    for component in _actionable_components(components):
        source_ref = component.get("source_ref") or {}
        module = _source_module(source_ref.get("path"))
        name = _source_callable_name(source_ref)
        if not module or not name:
            continue
        by_module.setdefault(module, set()).add(name)
    return [
        f"from {module} import {', '.join(sorted(names))}"
        for module, names in sorted(by_module.items())
    ]


def _component_by_name(components: list[dict], name: str) -> dict | None:
    for component in components:
        source_ref = component.get("source_ref") or {}
        if source_ref.get("name") == name:
            return component
    return None


def _component_names(components: list[dict]) -> set[str]:
    return {
        str((component.get("source_ref") or {}).get("name") or "")
        for component in components
    }


def _can_materialize_browser_policy_route(components: list[dict], planner_result: dict | None) -> bool:
    names = _component_names(components)
    required = {
        AIDEVOBSERVER_BROWSER_TABLE_FETCH_HTML,
        AIDEVOBSERVER_BROWSER_TABLE_EXTRACT,
        AIDEVOBSERVER_BROWSER_TABLE_WRITE_CSV,
        AIDEVOBSERVER_BROWSER_TABLE_WRITE_PARQUET,
        AIDEVOBSERVER_API_POLICY_VALIDATE_REQUEST,
        AIDEVOBSERVER_API_POLICY_FETCH_ACCOUNT,
        AIDEVOBSERVER_API_POLICY_APPLY_DECISION,
        AIDEVOBSERVER_API_POLICY_PERSIST_DECISION,
        AIDEVOBSERVER_API_POLICY_EMIT_RESPONSE,
    }
    return required <= names


def _browser_policy_api_recipe_nodes(components: list[dict]) -> list[dict]:
    specs = (
        (
            "validate_request",
            AIDEVOBSERVER_API_POLICY_VALIDATE_REQUEST,
            "$input.json_body",
            "$state.validated_request",
            "Validate JSON request and derive idempotency key if absent.",
        ),
        (
            "fetch_page",
            AIDEVOBSERVER_BROWSER_TABLE_FETCH_HTML,
            "$state.validated_request.company_domain",
            "$state.html_document",
            "Fetch browser-rendered company page HTML.",
        ),
        (
            "extract_tables",
            AIDEVOBSERVER_BROWSER_TABLE_EXTRACT,
            "$state.html_document",
            "$state.html_tables",
            "Extract HTML table records.",
        ),
        (
            "write_csv",
            AIDEVOBSERVER_BROWSER_TABLE_WRITE_CSV,
            "$state.html_tables[0] + $output.csv_path",
            "$artifacts.csv",
            "Persist first table as CSV artifact.",
        ),
        (
            "write_parquet",
            AIDEVOBSERVER_BROWSER_TABLE_WRITE_PARQUET,
            "$state.html_tables[0] + $output.parquet_path",
            "$artifacts.parquet",
            "Persist first table as Parquet artifact.",
        ),
        (
            "fetch_account",
            AIDEVOBSERVER_API_POLICY_FETCH_ACCOUNT,
            "$state.validated_request",
            "$state.account_state",
            "Fetch deterministic account-state snapshot.",
        ),
        (
            "apply_policy",
            AIDEVOBSERVER_API_POLICY_APPLY_DECISION,
            "$state.validated_request + $state.account_state + $artifacts",
            "$state.policy_decision",
            "Apply deterministic enrichment policy.",
        ),
        (
            "persist_decision",
            AIDEVOBSERVER_API_POLICY_PERSIST_DECISION,
            "$state.policy_decision + $state.validated_request.idempotency_key + $output.decisions_path",
            "$artifacts.decision_receipt",
            "Persist decision receipt with idempotency.",
        ),
        (
            "emit_response",
            AIDEVOBSERVER_API_POLICY_EMIT_RESPONSE,
            "$state.validated_request + $state.policy_decision + $artifacts.decision_receipt + $artifacts",
            "$output.api_response",
            "Emit JSON-compatible API response.",
        ),
    )
    fallback_paths = {
        AIDEVOBSERVER_BROWSER_TABLE_FETCH_HTML: AIDEVOBSERVER_BROWSER_TABLE_PRIMITIVE_SOURCE_PATH,
        AIDEVOBSERVER_BROWSER_TABLE_EXTRACT: AIDEVOBSERVER_BROWSER_TABLE_PRIMITIVE_SOURCE_PATH,
        AIDEVOBSERVER_BROWSER_TABLE_WRITE_CSV: AIDEVOBSERVER_BROWSER_TABLE_PRIMITIVE_SOURCE_PATH,
        AIDEVOBSERVER_BROWSER_TABLE_WRITE_PARQUET: AIDEVOBSERVER_BROWSER_TABLE_PRIMITIVE_SOURCE_PATH,
        AIDEVOBSERVER_API_POLICY_VALIDATE_REQUEST: AIDEVOBSERVER_API_POLICY_PRIMITIVE_SOURCE_PATH,
        AIDEVOBSERVER_API_POLICY_FETCH_ACCOUNT: AIDEVOBSERVER_API_POLICY_PRIMITIVE_SOURCE_PATH,
        AIDEVOBSERVER_API_POLICY_APPLY_DECISION: AIDEVOBSERVER_API_POLICY_PRIMITIVE_SOURCE_PATH,
        AIDEVOBSERVER_API_POLICY_PERSIST_DECISION: AIDEVOBSERVER_API_POLICY_PRIMITIVE_SOURCE_PATH,
        AIDEVOBSERVER_API_POLICY_EMIT_RESPONSE: AIDEVOBSERVER_API_POLICY_PRIMITIVE_SOURCE_PATH,
    }
    nodes: list[dict] = []
    prior: str | None = None
    for node_id, primitive_name, input_edge, output_edge, description in specs:
        component = _component_by_name(components, primitive_name) or {}
        source_ref = component.get("source_ref") or {}
        node = {
            "id": node_id,
            "component": component.get("label") or primitive_name,
            "primitive": primitive_name,
            "source_ref": {
                "path": source_ref.get("path") or fallback_paths[primitive_name],
                "name": source_ref.get("name") or primitive_name,
            },
            "input": input_edge,
            "output": output_edge,
            "depends_on": [prior] if prior else [],
            "blackbox": description,
            "candidate": True,
            "serves_truth": False,
        }
        nodes.append(node)
        prior = node_id
    return nodes


def _csv_recipe_nodes(components: list[dict]) -> list[dict]:
    specs = (
        (
            "read_rows",
            AIDEVOBSERVER_CSV_PRIMITIVE_READ_ROWS,
            "$input.path",
            "$state.rows",
            "Read the uploaded CSV artifact into typed row dictionaries.",
        ),
        (
            "validate_columns",
            AIDEVOBSERVER_CSV_PRIMITIVE_VALIDATE,
            "$state.rows + $config.required_columns",
            "$state.import_result",
            "Validate required vendor columns and preserve deterministic import metadata.",
        ),
        (
            "summarize",
            AIDEVOBSERVER_CSV_PRIMITIVE_SUMMARIZE,
            "$state.import_result",
            "$output",
            "Return a JSON-compatible import response for the app boundary.",
        ),
    )
    nodes: list[dict] = []
    for node_id, primitive_name, input_edge, output_edge, description in specs:
        component = _component_by_name(components, primitive_name) or {}
        source_ref = component.get("source_ref") or {}
        nodes.append({
            "id": node_id,
            "component": component.get("label") or f"teleon.ingest.csv.{primitive_name}",
            "primitive": primitive_name,
            "source_ref": {
                "path": source_ref.get("path") or AIDEVOBSERVER_CSV_PRIMITIVE_SOURCE_PATH,
                "name": source_ref.get("name") or primitive_name,
            },
            "input": input_edge,
            "output": output_edge,
            "blackbox": description,
            "candidate": True,
            "serves_truth": False,
        })
    return nodes


def _browser_table_recipe_nodes(components: list[dict]) -> list[dict]:
    specs = (
        (
            "fetch_html",
            AIDEVOBSERVER_BROWSER_TABLE_FETCH_HTML,
            "$input.url",
            "$state.html",
            "Fetch a browser-rendered or static HTML document.",
        ),
        (
            "extract_tables",
            AIDEVOBSERVER_BROWSER_TABLE_EXTRACT,
            "$state.html",
            "$state.tables",
            "Extract HTML tables into deterministic row dictionaries.",
        ),
        (
            "write_csv",
            AIDEVOBSERVER_BROWSER_TABLE_WRITE_CSV,
            "$state.tables[0] + $output.csv_path",
            "$artifacts.csv",
            "Write the selected table to a CSV artifact.",
        ),
        (
            "write_parquet",
            AIDEVOBSERVER_BROWSER_TABLE_WRITE_PARQUET,
            "$state.tables[0] + $output.parquet_path",
            "$artifacts.parquet",
            "Write the selected table to a Parquet artifact.",
        ),
    )
    nodes: list[dict] = []
    for node_id, primitive_name, input_edge, output_edge, description in specs:
        component = _component_by_name(components, primitive_name) or {}
        source_ref = component.get("source_ref") or {}
        nodes.append({
            "id": node_id,
            "component": component.get("label") or f"teleon.ingest.browser.{primitive_name}",
            "primitive": primitive_name,
            "source_ref": {
                "path": source_ref.get("path") or AIDEVOBSERVER_BROWSER_TABLE_PRIMITIVE_SOURCE_PATH,
                "name": source_ref.get("name") or primitive_name,
            },
            "input": input_edge,
            "output": output_edge,
            "blackbox": description,
            "candidate": True,
            "serves_truth": False,
        })
    return nodes


def _planner_recipe_nodes(planner_result: dict | None, components: list[dict]) -> list[dict]:
    if not isinstance(planner_result, dict):
        return []
    route = planner_result.get("route") if isinstance(planner_result.get("route"), dict) else {}
    raw_nodes = route.get("nodes") if isinstance(route.get("nodes"), list) else []
    if not raw_nodes:
        return []
    alias_map = {
        str(component.get("planner_alias") or ""): component
        for component in components
        if component.get("planner_alias")
    }
    nodes: list[dict] = []
    for index, raw in enumerate(raw_nodes):
        if not isinstance(raw, dict):
            continue
        alias = str(raw.get("candidate_alias") or raw.get("component_alias") or "")
        component = alias_map.get(alias) or {}
        source_ref = component.get("source_ref") or {}
        contract = component.get("contract") or {}
        primitive = source_ref.get("name") or raw.get("primitive") or alias or "candidate_component"
        nodes.append({
            "id": str(raw.get("id") or raw.get("slot") or f"step_{index + 1}"),
            "component": component.get("label") or raw.get("component") or alias or "candidate component",
            "primitive": primitive,
            "planner_alias": alias or None,
            "source_ref": {
                "path": source_ref.get("path"),
                "name": source_ref.get("name") or primitive,
            },
            "input": raw.get("input") or contract.get("input") or "unknown",
            "output": raw.get("output") or contract.get("output") or "unknown",
            "depends_on": raw.get("depends_on") if isinstance(raw.get("depends_on"), list) else [],
            "blackbox": raw.get("why") or raw.get("blackbox") or "",
            "candidate": True,
            "serves_truth": False,
        })
    return nodes


def _route_recipe(
    task: str,
    components: list[dict],
    execution_mode: str,
    planner_result: dict | None = None,
) -> dict:
    deterministic = execution_mode == "deterministic_template_worker"
    template = None
    nodes: list[dict] = []
    if deterministic and _can_materialize_browser_policy_route(components, planner_result):
        nodes = _browser_policy_api_recipe_nodes(components)
        template = AIDEVOBSERVER_BROWSER_POLICY_API_RECIPE_TEMPLATE_ID
    elif deterministic and planner_result and planner_result.get("status") == "used":
        nodes = _planner_recipe_nodes(planner_result, components)
        template = AIDEVOBSERVER_PLANNER_ROUTE_TEMPLATE_ID if nodes else None
    elif deterministic and _ide_task_is_browser_table_export(task):
        nodes = _browser_table_recipe_nodes(components)
        template = AIDEVOBSERVER_BROWSER_TABLE_RECIPE_TEMPLATE_ID
    elif deterministic and _ide_task_is_csv_import(task):
        nodes = _csv_recipe_nodes(components)
        template = AIDEVOBSERVER_CSV_RECIPE_TEMPLATE_ID
    elif planner_result and planner_result.get("status") == "used":
        nodes = _planner_recipe_nodes(planner_result, components)
        template = AIDEVOBSERVER_PLANNER_ROUTE_TEMPLATE_ID if nodes else None
    return {
        "recipe_id": "recipe_" + _digest({
            "task": task,
            "execution_mode": execution_mode,
            "nodes": nodes,
        }),
        "kind": (
            "deterministic_route_recipe"
            if deterministic
            else "no_op_notice" if execution_mode == AIDEVOBSERVER_NOOP_EXECUTION_MODE
            else "harness_fallback_recipe"
        ),
        "template": template,
        "execution_mode": execution_mode,
        "nodes": nodes,
        "deterministic_workers": [
            worker["id"]
            for worker in _deterministic_worker_catalog()
            if deterministic or worker["id"] in {"edge_matcher", "route_recipe_compiler", "gap_recorder"}
        ],
        "model_calls": 0 if deterministic or execution_mode == AIDEVOBSERVER_NOOP_EXECUTION_MODE else "fallback_only",
        "coding_harness_invoked": False if deterministic or execution_mode == AIDEVOBSERVER_NOOP_EXECUTION_MODE else "fallback_only",
        "candidate": True,
        "serves_truth": False,
    }


def _render_candidate_bundle(task: str, components: list[dict]) -> str:
    rows = [
        f"Q {task}",
        "O ImportFlow",
        "T0 browser_ide_reuse_search",
        "",
        "S0 reusable_route PlainTask>ImplementationPlan req:input_output_edges allow:map,field,wrap,cache,retry",
    ]
    for index, component in enumerate(components):
        contract = component.get("contract") or {}
        source_ref = component.get("source_ref") or {}
        mutations = component.get("mutations") or []
        mutation_ids = ",".join(_mutation_ids(mutations)) or "-"
        rows.append(
            "C0."
            f"{index} {component.get('label') or 'component'} "
            f"{contract.get('input') or 'unknown'}>{contract.get('output') or 'unknown'} "
            f"fit:{component.get('edge_fit') or 'candidate'} tools:{mutation_ids} "
            f"src:{source_ref.get('path') or '-'}::{source_ref.get('name') or '-'}"
        )
    if not _actionable_components(components):
        rows.extend([
            "",
            "N0 reason:no_high_confidence_input_output_edge_match",
            "G0 record_candidate_primitive_opportunity true",
        ])
    return "\n".join(rows) + "\n"


def _render_csv_scaffold(components: list[dict]) -> str:
    selected = _actionable_components(components)
    selected_notes = "\n".join(
        f"# selected: {item.get('label')} ({(item.get('contract') or {}).get('input')} -> {(item.get('contract') or {}).get('output')})"
        for item in selected[:5]
    ) or "# selected: none; this flow records a primitive gap if no reusable CSV route exists"
    return (
        '"""CSV import flow assembled from AIDevObserver registry edge matches."""\n'
        "from __future__ import annotations\n\n"
        "from pathlib import Path\n\n"
        f"from {AIDEVOBSERVER_WORKSPACE_PRIMITIVE_IMPORT_ROOT}.ingest.csv_import import (\n"
        f"    {AIDEVOBSERVER_CSV_PRIMITIVE_READ_ROWS},\n"
        f"    {AIDEVOBSERVER_CSV_PRIMITIVE_SUMMARIZE},\n"
        f"    {AIDEVOBSERVER_CSV_PRIMITIVE_VALIDATE},\n"
        ")\n\n"
        f"{selected_notes}\n\n\n"
        'REQUIRED_VENDOR_COLUMNS = ("vendor_id", "invoice_number", "amount")\n\n\n'
        "def import_uploaded_vendor_csv(path: Path) -> dict[str, object]:\n"
        f"    rows = {AIDEVOBSERVER_CSV_PRIMITIVE_READ_ROWS}(path)\n"
        f"    result = {AIDEVOBSERVER_CSV_PRIMITIVE_VALIDATE}(rows, REQUIRED_VENDOR_COLUMNS)\n"
        f"    return {AIDEVOBSERVER_CSV_PRIMITIVE_SUMMARIZE}(result)\n"
    )


def _render_browser_table_scaffold(components: list[dict]) -> str:
    selected = _actionable_components(components)
    selected_notes = "\n".join(
        f"# selected: {item.get('label')} ({(item.get('contract') or {}).get('input')} -> {(item.get('contract') or {}).get('output')})"
        for item in selected[:5]
    ) or "# selected: none; this flow records a primitive gap if no reusable browser-table route exists"
    return (
        '"""Browser table ingestion flow assembled from AIDevObserver registry edge matches."""\n'
        "from __future__ import annotations\n\n"
        "from pathlib import Path\n\n"
        f"from {AIDEVOBSERVER_WORKSPACE_PRIMITIVE_IMPORT_ROOT}.ingest.browser_table import (\n"
        f"    {AIDEVOBSERVER_BROWSER_TABLE_EXTRACT},\n"
        f"    {AIDEVOBSERVER_BROWSER_TABLE_FETCH_HTML},\n"
        f"    {AIDEVOBSERVER_BROWSER_TABLE_WRITE_CSV},\n"
        f"    {AIDEVOBSERVER_BROWSER_TABLE_WRITE_PARQUET},\n"
        ")\n\n"
        f"{selected_notes}\n\n\n"
        "def export_first_page_table(url: str, output_dir: Path) -> dict[str, object]:\n"
        f"    html = {AIDEVOBSERVER_BROWSER_TABLE_FETCH_HTML}(url)\n"
        f"    tables = {AIDEVOBSERVER_BROWSER_TABLE_EXTRACT}(html)\n"
        "    if not tables:\n"
        "        return {\"table_count\": 0, \"csv\": None, \"parquet\": None}\n"
        "    output_dir.mkdir(parents=True, exist_ok=True)\n"
        "    table = tables[0]\n"
        f"    csv_path = {AIDEVOBSERVER_BROWSER_TABLE_WRITE_CSV}(table, output_dir / \"table.csv\")\n"
        f"    parquet_path = {AIDEVOBSERVER_BROWSER_TABLE_WRITE_PARQUET}(table, output_dir / \"table.parquet\")\n"
        "    return {\n"
        "        \"table_count\": len(tables),\n"
        "        \"rows\": len(table.rows),\n"
        "        \"columns\": list(table.headers),\n"
        "        \"csv\": str(csv_path),\n"
        "        \"parquet\": str(parquet_path),\n"
        "    }\n"
    )


def _render_browser_policy_api_scaffold(components: list[dict]) -> str:
    selected = _actionable_components(components)
    selected_notes = "\n".join(
        f"# selected: {item.get('label')} ({(item.get('contract') or {}).get('input')} -> {(item.get('contract') or {}).get('output')})"
        for item in selected[:AIDEVOBSERVER_PLANNER_TOOL_RESULT_COMPONENT_LIMIT]
    ) or "# selected: none; this flow records a primitive gap if no reusable composite route exists"
    return (
        '"""Composite API + browser-table + policy flow assembled from AIDevObserver planner edge matches."""\n'
        "from __future__ import annotations\n\n"
        "from pathlib import Path\n\n"
        f"from {AIDEVOBSERVER_WORKSPACE_PRIMITIVE_IMPORT_ROOT}.api.policy_flow import (\n"
        f"    {AIDEVOBSERVER_API_POLICY_APPLY_DECISION},\n"
        f"    {AIDEVOBSERVER_API_POLICY_EMIT_RESPONSE},\n"
        f"    {AIDEVOBSERVER_API_POLICY_FETCH_ACCOUNT},\n"
        f"    {AIDEVOBSERVER_API_POLICY_PERSIST_DECISION},\n"
        f"    {AIDEVOBSERVER_API_POLICY_VALIDATE_REQUEST},\n"
        ")\n"
        f"from {AIDEVOBSERVER_WORKSPACE_PRIMITIVE_IMPORT_ROOT}.ingest.browser_table import (\n"
        f"    {AIDEVOBSERVER_BROWSER_TABLE_EXTRACT},\n"
        f"    {AIDEVOBSERVER_BROWSER_TABLE_FETCH_HTML},\n"
        f"    {AIDEVOBSERVER_BROWSER_TABLE_WRITE_CSV},\n"
        f"    {AIDEVOBSERVER_BROWSER_TABLE_WRITE_PARQUET},\n"
        ")\n\n"
        f"{selected_notes}\n\n\n"
        "def handle_company_table_policy_request(payload: dict[str, object], output_dir: Path) -> dict[str, object]:\n"
        "    request = validate_company_enrichment_request(payload)\n"
        "    output_dir.mkdir(parents=True, exist_ok=True)\n"
        "    html = fetch_page_html_with_playwright(f\"https://{request.company_domain}\")\n"
        "    tables = extract_html_tables(html)\n"
        "    artifacts: dict[str, object] = {\"table_count\": len(tables), \"csv\": None, \"parquet\": None}\n"
        "    if tables:\n"
        "        table = tables[0]\n"
        "        artifacts.update({\n"
        "            \"rows\": len(table.rows),\n"
        "            \"columns\": list(table.headers),\n"
        "            \"csv\": str(write_table_csv(table, output_dir / \"company_table.csv\")),\n"
        "            \"parquet\": str(write_table_parquet(table, output_dir / \"company_table.parquet\")),\n"
        "        })\n"
        "    account = fetch_account_state(request)\n"
        "    decision = apply_enrichment_policy(request, account, artifacts)\n"
        "    receipt = persist_policy_decision(decision, request.idempotency_key, output_dir / \"decisions\")\n"
        "    return emit_api_response(request, decision, receipt, artifacts)\n"
    )


def _runtime_entrypoint(plan: dict, task: str) -> dict | None:
    recipe = plan.get("recipe") if isinstance(plan.get("recipe"), dict) else {}
    template = recipe.get("template")
    if template == AIDEVOBSERVER_BROWSER_POLICY_API_RECIPE_TEMPLATE_ID:
        return {
            "kind": "json_api",
            "module": "app.company_table_policy_api_flow",
            "function": "handle_company_table_policy_request",
            "sample_payload": {
                "company_domain": "example.com",
                "account_id": "acct_demo",
                "idempotency_key": "acct_demo_example",
            },
            "output_dir_arg": True,
        }
    if template == AIDEVOBSERVER_BROWSER_TABLE_RECIPE_TEMPLATE_ID or _ide_task_is_browser_table_export(task):
        return {
            "kind": "browser_table_export",
            "module": "app.browser_table_export_flow",
            "function": "export_first_page_table",
            "sample_payload": {"url": "https://example.com"},
            "output_dir_arg": True,
        }
    if template == AIDEVOBSERVER_CSV_RECIPE_TEMPLATE_ID or _ide_task_is_csv_import(task):
        return {
            "kind": "csv_import",
            "module": "app.vendor_csv_import_flow",
            "function": "import_uploaded_vendor_csv",
            "sample_payload": {"path": "fixtures/vendor.csv"},
            "output_dir_arg": False,
        }
    return None


def _render_runtime_local_runner(entrypoint: dict) -> str:
    payload = json.dumps(entrypoint.get("sample_payload") or {}, sort_keys=True)
    return (
        '"""Local runtime wrapper generated by AIDevObserver.\n\n'
        "This file contains no business logic. It calls the deterministic app\n"
        "entry point materialized from selected primitive edges.\n"
        '"""\n'
        "from __future__ import annotations\n\n"
        "import argparse\n"
        "import json\n"
        "from pathlib import Path\n\n"
        f"from {entrypoint['module']} import {entrypoint['function']}\n\n\n"
        f"ROUTE_KIND = {json.dumps(entrypoint['kind'])}\n"
        f"DEFAULT_PAYLOAD = {payload}\n\n\n"
        "def run(payload: dict[str, object], output_dir: Path) -> dict[str, object]:\n"
        "    if ROUTE_KIND == \"csv_import\":\n"
        f"        result = {entrypoint['function']}(Path(str(payload.get(\"path\") or DEFAULT_PAYLOAD[\"path\"])))\n"
        "    elif ROUTE_KIND == \"browser_table_export\":\n"
        f"        result = {entrypoint['function']}(str(payload.get(\"url\") or DEFAULT_PAYLOAD[\"url\"]), output_dir)\n"
        "    else:\n"
        f"        result = {entrypoint['function']}(payload, output_dir)\n"
        "    return result if isinstance(result, dict) else {\"result\": result}\n\n\n"
        "def main() -> int:\n"
        "    parser = argparse.ArgumentParser(description=\"Run the compiled AIDevObserver route locally.\")\n"
        "    parser.add_argument(\"--payload-json\", default=\"\", help=\"JSON payload for the route.\")\n"
        "    parser.add_argument(\"--payload-file\", default=\"\", help=\"Path to JSON payload file.\")\n"
        "    parser.add_argument(\"--output-dir\", default=\"out\", help=\"Artifact output directory.\")\n"
        "    args = parser.parse_args()\n"
        "    if args.payload_file:\n"
        "        payload = json.loads(Path(args.payload_file).read_text(encoding=\"utf-8\"))\n"
        "    elif args.payload_json:\n"
        "        payload = json.loads(args.payload_json)\n"
        "    else:\n"
        "        payload = dict(DEFAULT_PAYLOAD)\n"
        "    output = run(payload, Path(args.output_dir))\n"
        "    print(json.dumps(output, indent=2, sort_keys=True))\n"
        "    return 0\n\n\n"
        "if __name__ == \"__main__\":\n"
        "    raise SystemExit(main())\n"
    )


def _render_runtime_http_app() -> str:
    return (
        '"""HTTP runtime wrapper generated by AIDevObserver.\n\n'
        "If FastAPI is installed this exposes POST /run. Without FastAPI the\n"
        "module still provides a stdlib-callable handle(payload) function.\n"
        '"""\n'
        "from __future__ import annotations\n\n"
        "import json\n"
        "import sys\n"
        "from pathlib import Path\n"
        "from typing import Any\n\n"
        "from runtime.local_runner import run\n\n"
        "try:\n"
        "    from fastapi import FastAPI\n"
        "except Exception:  # pragma: no cover - optional runtime dependency\n"
        "    FastAPI = None\n\n"
        "app = FastAPI(title=\"AIDevObserver compiled route\") if FastAPI else None\n\n\n"
        "def handle(payload: dict[str, Any], output_dir: Path | None = None) -> dict[str, object]:\n"
        "    return run(payload, output_dir or Path(\"out\"))\n\n\n"
        "if app is not None:\n"
        "    @app.post(\"/run\")\n"
        "    def run_route(payload: dict[str, Any]) -> dict[str, object]:\n"
        "        return handle(payload)\n\n\n"
        "def main() -> int:\n"
        "    payload = json.loads(sys.stdin.read() or \"{}\")\n"
        "    print(json.dumps(handle(payload), indent=2, sort_keys=True))\n"
        "    return 0\n\n\n"
        "if __name__ == \"__main__\":\n"
        "    raise SystemExit(main())\n"
    )


def _render_cloud_function_handler() -> str:
    return (
        '"""Cloud-function HTTP handler generated by AIDevObserver.\n\n'
        "No provider SDK is required for syntax/proof. Provider adapters can bind\n"
        "this `handler` function to AWS Lambda, GCP Cloud Functions, Azure\n"
        "Functions, or Cloudflare workers-style HTTP shims.\n"
        '"""\n'
        "from __future__ import annotations\n\n"
        "import json\n"
        "from pathlib import Path\n"
        "from typing import Any\n\n"
        "from runtime.local_runner import run\n\n\n"
        "def _payload_from_request(request: Any) -> dict[str, object]:\n"
        "    if isinstance(request, dict):\n"
        "        return request\n"
        "    get_json = getattr(request, \"get_json\", None)\n"
        "    if callable(get_json):\n"
        "        value = get_json(silent=True) if \"silent\" in getattr(get_json, \"__code__\", type(\"X\", (), {\"co_varnames\": ()})).co_varnames else get_json()\n"
        "        return value if isinstance(value, dict) else {}\n"
        "    body = getattr(request, \"body\", b\"\") or getattr(request, \"data\", b\"\")\n"
        "    if isinstance(body, bytes):\n"
        "        body = body.decode(\"utf-8\")\n"
        "    return json.loads(body or \"{}\")\n\n\n"
        "def handler(request: Any) -> dict[str, object]:\n"
        "    payload = _payload_from_request(request)\n"
        "    return run(payload, Path(\"/tmp/aidevobserver-output\"))\n"
    )


def _runtime_name(plan: dict) -> str:
    recipe = plan.get("recipe") if isinstance(plan.get("recipe"), dict) else {}
    raw = str(recipe.get("template") or plan.get("plan_id") or "aidevobserver-route")
    name = re.sub(r"[^a-z0-9-]+", "-", raw.lower()).strip("-")
    return (name or "aidevobserver-route")[:63].strip("-") or "aidevobserver-route"


def _render_dockerfile() -> str:
    return (
        "# Generated by AIDevObserver deterministic runtime emitter.\n"
        "FROM python:3.11-slim\n"
        "WORKDIR /workspace\n"
        "COPY . /workspace\n"
        "ENV PYTHONPATH=/workspace\n"
        "CMD [\"python\", \"runtime/local_runner.py\", \"--output-dir\", \"/tmp/aidevobserver-output\"]\n"
    )


def _render_k8s_job(name: str) -> str:
    return (
        "apiVersion: batch/v1\n"
        "kind: Job\n"
        "metadata:\n"
        f"  name: {name}-job\n"
        "  labels:\n"
        "    app.kubernetes.io/name: aidevobserver-route\n"
        "    app.kubernetes.io/managed-by: aidevobserver\n"
        "spec:\n"
        "  backoffLimit: 1\n"
        "  template:\n"
        "    spec:\n"
        "      restartPolicy: Never\n"
        "      containers:\n"
        "        - name: route\n"
        "          image: aidevobserver-route:candidate\n"
        "          imagePullPolicy: IfNotPresent\n"
        "          command: [\"python\", \"runtime/local_runner.py\"]\n"
    )


def _render_k8s_deployment(name: str) -> str:
    return (
        "apiVersion: apps/v1\n"
        "kind: Deployment\n"
        "metadata:\n"
        f"  name: {name}\n"
        "  labels:\n"
        "    app.kubernetes.io/name: aidevobserver-route\n"
        "    app.kubernetes.io/managed-by: aidevobserver\n"
        "spec:\n"
        "  replicas: 1\n"
        "  selector:\n"
        "    matchLabels:\n"
        f"      app: {name}\n"
        "  template:\n"
        "    metadata:\n"
        "      labels:\n"
        f"        app: {name}\n"
        "    spec:\n"
        "      containers:\n"
        "        - name: route\n"
        "          image: aidevobserver-route:candidate\n"
        "          imagePullPolicy: IfNotPresent\n"
        "          command: [\"python\", \"-m\", \"uvicorn\", \"runtime.http_app:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8080\"]\n"
        "          ports:\n"
        "            - containerPort: 8080\n"
    )


def _render_k8s_cronjob(name: str) -> str:
    return (
        "apiVersion: batch/v1\n"
        "kind: CronJob\n"
        "metadata:\n"
        f"  name: {name}-cron\n"
        "  labels:\n"
        "    app.kubernetes.io/name: aidevobserver-route\n"
        "    app.kubernetes.io/managed-by: aidevobserver\n"
        "spec:\n"
        "  schedule: \"0 * * * *\"\n"
        "  jobTemplate:\n"
        "    spec:\n"
        "      template:\n"
        "        spec:\n"
        "          restartPolicy: Never\n"
        "          containers:\n"
        "            - name: route\n"
        "              image: aidevobserver-route:candidate\n"
        "              imagePullPolicy: IfNotPresent\n"
        "              command: [\"python\", \"runtime/local_runner.py\"]\n"
    )


def _render_runtime_manifest(plan: dict, entrypoint: dict) -> str:
    return json.dumps({
        "runtime_manifest": "aidevobserver.runtime.v1",
        "entrypoint": entrypoint,
        "runtime_target": plan.get("runtime_target"),
        "recipe": plan.get("recipe"),
        "emitted_files": [
            "runtime/local_runner.py",
            "runtime/http_app.py",
            "runtime/cloud_function_handler.py",
            "Dockerfile",
            "deploy/k8s-job.yaml",
            "deploy/k8s-deployment.yaml",
            "deploy/k8s-cronjob.yaml",
        ],
        "candidate": True,
        "serves_truth": False,
    }, indent=2, sort_keys=True)


def _runtime_emitter_files(task: str, plan: dict) -> list[dict]:
    if plan.get("execution_mode") != "deterministic_template_worker":
        return []
    recipe = plan.get("recipe") if isinstance(plan.get("recipe"), dict) else {}
    if not recipe.get("nodes"):
        return []
    entrypoint = _runtime_entrypoint(plan, task)
    if not entrypoint:
        return []
    name = _runtime_name(plan)
    return [
        {
            "path": "runtime/local_runner.py",
            "language": "python",
            "content": _render_runtime_local_runner(entrypoint),
        },
        {
            "path": "runtime/http_app.py",
            "language": "python",
            "content": _render_runtime_http_app(),
        },
        {
            "path": "runtime/cloud_function_handler.py",
            "language": "python",
            "content": _render_cloud_function_handler(),
        },
        {
            "path": "Dockerfile",
            "language": "dockerfile",
            "content": _render_dockerfile(),
        },
        {
            "path": "deploy/k8s-job.yaml",
            "language": "yaml",
            "content": _render_k8s_job(name),
        },
        {
            "path": "deploy/k8s-deployment.yaml",
            "language": "yaml",
            "content": _render_k8s_deployment(name),
        },
        {
            "path": "deploy/k8s-cronjob.yaml",
            "language": "yaml",
            "content": _render_k8s_cronjob(name),
        },
        {
            "path": "runtime/runtime_manifest.json",
            "language": "json",
            "content": _render_runtime_manifest(plan, entrypoint),
        },
    ]


def _render_test_loader() -> str:
    return (
        "from __future__ import annotations\n\n"
        "import importlib.util\n"
        "import sys\n"
        "import tempfile\n"
        "from pathlib import Path\n\n\n"
        "ROOT = Path(__file__).resolve().parents[1]\n"
        "if str(ROOT) not in sys.path:\n"
        "    sys.path.insert(0, str(ROOT))\n\n\n"
        "def load_module(relpath: str):\n"
        # GENERATED code resolves against its own workspace ROOT — never the repo's _resource(), which does not
        # exist inside the emitted file (a path-decoupling sweep once rewrote this string literal and broke
        # every workspace proof with NameError)
        "    path = ROOT / relpath\n"
        "    spec = importlib.util.spec_from_file_location(path.stem, path)\n"
        "    if spec is None or spec.loader is None:\n"
        "        raise RuntimeError(f\"could not load {relpath}\")\n"
        "    module = importlib.util.module_from_spec(spec)\n"
        "    sys.modules[path.stem] = module\n"
        "    spec.loader.exec_module(module)\n"
        "    return module\n\n\n"
        "HTML_FIXTURE = \"\"\"\n"
        "<html><body>\n"
        "<table>\n"
        "  <tr><th>Name</th><th>Value</th></tr>\n"
        "  <tr><td>Alpha</td><td>1</td></tr>\n"
        "</table>\n"
        "</body></html>\n"
        "\"\"\"\n\n\n"
        "def fake_parquet_writer(table, path: Path) -> Path:\n"
        "    path.parent.mkdir(parents=True, exist_ok=True)\n"
        "    path.write_text(\"parquet fixture\\n\", encoding=\"utf-8\")\n"
        "    return path\n\n\n"
    )


def _render_csv_flow_test() -> str:
    return (
        _render_test_loader()
        + "def test_generated_csv_import_flow_accepts_required_columns() -> None:\n"
        "    flow = load_module(\"app/vendor_csv_import_flow.py\")\n"
        "    with tempfile.TemporaryDirectory() as tmp:\n"
        "        csv_path = Path(tmp) / \"vendors.csv\"\n"
        "        csv_path.write_text(\"vendor_id,invoice_number,amount\\nv1,inv-1,12.50\\n\", encoding=\"utf-8\")\n"
        "        result = flow.import_uploaded_vendor_csv(csv_path)\n"
        "    assert result[\"valid\"] is True\n"
        "    assert result[\"row_count\"] == 1\n"
        "    assert result[\"missing_required_columns\"] == []\n\n\n"
        "def test_generated_csv_import_flow_reports_missing_columns() -> None:\n"
        "    flow = load_module(\"app/vendor_csv_import_flow.py\")\n"
        "    with tempfile.TemporaryDirectory() as tmp:\n"
        "        csv_path = Path(tmp) / \"vendors.csv\"\n"
        "        csv_path.write_text(\"vendor_id,invoice_number\\nv1,inv-1\\n\", encoding=\"utf-8\")\n"
        "        result = flow.import_uploaded_vendor_csv(csv_path)\n"
        "    assert result[\"valid\"] is False\n"
        "    assert result[\"row_count\"] == 1\n"
        "    assert result[\"missing_required_columns\"] == [\"amount\"]\n\n\n"
        "if __name__ == \"__main__\":\n"
        "    test_generated_csv_import_flow_accepts_required_columns()\n"
        "    test_generated_csv_import_flow_reports_missing_columns()\n"
    )


def _render_browser_table_flow_test() -> str:
    return (
        _render_test_loader()
        + "def test_generated_browser_table_flow_exports_first_table() -> None:\n"
        "    flow = load_module(\"app/browser_table_export_flow.py\")\n"
        "    flow.fetch_page_html_with_playwright = lambda url: HTML_FIXTURE\n"
        "    flow.write_table_parquet = fake_parquet_writer\n"
        "    with tempfile.TemporaryDirectory() as tmp:\n"
        "        result = flow.export_first_page_table(\"https://example.com\", Path(tmp))\n"
        "        assert Path(result[\"csv\"]).is_file()\n"
        "        assert Path(result[\"parquet\"]).is_file()\n"
        "    assert result[\"table_count\"] == 1\n"
        "    assert result[\"rows\"] == 1\n"
        "    assert result[\"columns\"] == [\"Name\", \"Value\"]\n\n\n"
        "def test_generated_browser_table_flow_handles_no_tables() -> None:\n"
        "    flow = load_module(\"app/browser_table_export_flow.py\")\n"
        "    flow.fetch_page_html_with_playwright = lambda url: \"<html><body>No tables</body></html>\"\n"
        "    with tempfile.TemporaryDirectory() as tmp:\n"
        "        result = flow.export_first_page_table(\"https://example.com\", Path(tmp))\n"
        "    assert result == {\"table_count\": 0, \"csv\": None, \"parquet\": None}\n\n\n"
        "if __name__ == \"__main__\":\n"
        "    test_generated_browser_table_flow_exports_first_table()\n"
        "    test_generated_browser_table_flow_handles_no_tables()\n"
    )


def _render_browser_policy_api_flow_test() -> str:
    return (
        _render_test_loader()
        + "def test_generated_browser_policy_api_flow_allows_table_backed_request() -> None:\n"
        "    flow = load_module(\"app/company_table_policy_api_flow.py\")\n"
        "    flow.fetch_page_html_with_playwright = lambda url: HTML_FIXTURE\n"
        "    flow.write_table_parquet = fake_parquet_writer\n"
        "    payload = {\n"
        "        \"company_domain\": \"example.com\",\n"
        "        \"account_id\": \"acct_1\",\n"
        "        \"idempotency_key\": \"acct_1_example\",\n"
        "    }\n"
        "    with tempfile.TemporaryDirectory() as tmp:\n"
        "        result = flow.handle_company_table_policy_request(payload, Path(tmp))\n"
        "        assert Path(result[\"artifacts\"][\"csv\"]).is_file()\n"
        "        assert Path(result[\"artifacts\"][\"parquet\"]).is_file()\n"
        "        assert Path(result[\"receipt\"]).is_file()\n"
        "    assert result[\"policy_status\"] == \"allowed\"\n"
        "    assert result[\"company_domain\"] == \"example.com\"\n"
        "    assert result[\"account_id\"] == \"acct_1\"\n"
        "    assert result[\"artifacts\"][\"table_count\"] == 1\n\n\n"
        "def test_generated_browser_policy_api_flow_blocks_when_no_tables() -> None:\n"
        "    flow = load_module(\"app/company_table_policy_api_flow.py\")\n"
        "    flow.fetch_page_html_with_playwright = lambda url: \"<html><body>No tables</body></html>\"\n"
        "    payload = {\"company_domain\": \"example.com\", \"account_id\": \"acct_1\", \"idempotency_key\": \"acct_1_no_tables\"}\n"
        "    with tempfile.TemporaryDirectory() as tmp:\n"
        "        result = flow.handle_company_table_policy_request(payload, Path(tmp))\n"
        "        assert Path(result[\"receipt\"]).is_file()\n"
        "    assert result[\"policy_status\"] == \"blocked\"\n"
        "    assert result[\"policy_reason\"] == \"no_tables_or_enrichment_disabled\"\n\n\n"
        "def test_generated_browser_policy_api_flow_rejects_invalid_payload() -> None:\n"
        "    flow = load_module(\"app/company_table_policy_api_flow.py\")\n"
        "    try:\n"
        "        flow.handle_company_table_policy_request({\"account_id\": \"acct_1\"}, Path(\"/tmp\"))\n"
        "    except ValueError as exc:\n"
        "        assert \"company_domain\" in str(exc)\n"
        "    else:\n"
        "        raise AssertionError(\"invalid payload should fail validation\")\n\n\n"
        "if __name__ == \"__main__\":\n"
        "    test_generated_browser_policy_api_flow_allows_table_backed_request()\n"
        "    test_generated_browser_policy_api_flow_blocks_when_no_tables()\n"
        "    test_generated_browser_policy_api_flow_rejects_invalid_payload()\n"
    )


def _render_run_report(plan: dict) -> str:
    execution_mode = plan.get("execution_mode") or "coding_harness_fallback"
    ai_trace = plan.get("ai_trace") if isinstance(plan.get("ai_trace"), dict) else {}
    adapter_summary = _adapter_summary(plan)
    return json.dumps({
        "run_context_id": plan.get("plan_id"),
        "task_summary": plan.get("task_summary"),
        "models": plan.get("models"),
        "harnesses": plan.get("harnesses"),
        "selected_route_context": plan.get("selected_route_context") or [],
        "route_context": plan.get("route_context"),
        "selected_components": plan.get("selected_components") or [],
        "edge_adapters": adapter_summary,
        "recipe": plan.get("recipe"),
        "planner_result": plan.get("planner_result"),
        "gap_recorded": not bool(plan.get("selected_components")),
        "automatic_component_selection": True,
        "execution_mode": execution_mode,
        "route_quality": plan.get("route_quality"),
        "token_savings": plan.get("token_savings"),
        "runtime_target": plan.get("runtime_target"),
        "fallback_strategy": plan.get("fallback_strategy"),
        "ai_trace": ai_trace,
        "known_model_calls": ai_trace.get("known_model_calls", 0),
        "harness_status": "not_invoked_deterministic_worker_used" if execution_mode == "deterministic_template_worker" else "starts_when_task_is_submitted",
        "orchestrator_role": (
            "search primitives, match input/output edges, compile selected deterministic template route"
            if execution_mode == "deterministic_template_worker"
            else "search primitives, match input/output edges, inject selected component context, then run the coding harness"
        ),
        "candidate": True,
        "serves_truth": False,
    }, indent=2, sort_keys=True)


def _render_edge_adapter_plan(plan: dict, components: list[dict]) -> str:
    selected = _actionable_components(components)
    recipe = plan.get("recipe") if isinstance(plan.get("recipe"), dict) else {}
    nodes = recipe.get("nodes") if isinstance(recipe.get("nodes"), list) else []
    runtime_target = plan.get("runtime_target") if isinstance(plan.get("runtime_target"), dict) else {}
    adapters: list[dict] = []
    for component in selected:
        contract = component.get("contract") if isinstance(component.get("contract"), dict) else {}
        published = _normalize_mutation_options(component.get("mutations"))
        adapters.append({
            "component": component.get("label"),
            "input": contract.get("input"),
            "output": contract.get("output"),
            "published_mutators": [
                _mutation_id(item)
                for item in published
            ],
            "mutator_details": [
                {
                    "mutator": _mutation_id(item),
                    "mutator_agent_id": _mutation_agent_id(item),
                    "reason": item.get("reason"),
                    "target_edge_template": item.get("target_edge_template"),
                    "effect_delta": item.get("effect_delta"),
                    "preconditions": item.get("preconditions") or [],
                    "proof_obligations": item.get("proof_obligations") or [],
                    "runtime_targets": item.get("runtime_targets") or [],
                    "candidate": True,
                    "serves_truth": False,
                }
                for item in published
            ],
            "selection_reasons": component.get("selection_reasons") or _component_selection_reasons(component),
            "candidate": True,
            "serves_truth": False,
        })
    return json.dumps({
        "plan_id": plan.get("plan_id"),
        "execution_mode": plan.get("execution_mode"),
        "runtime_target": plan.get("runtime_target"),
        "route_nodes": [
            {
                "id": node.get("id"),
                "primitive": node.get("primitive"),
                "input": node.get("input"),
                "output": node.get("output"),
            }
            for node in nodes
        ],
        "selected_edges": adapters,
        "adapter_summary": _adapter_summary(plan, components),
        "deterministic_mutators_available": list(AIDEVOBSERVER_DETERMINISTIC_MUTATOR_IDS),
        "runtime_emitters": {
            "target": runtime_target.get("target"),
            "trigger": runtime_target.get("trigger"),
            "status": "candidate",
            "files": [
                "runtime/local_runner.py",
                "runtime/http_app.py",
                "runtime/cloud_function_handler.py",
                "Dockerfile",
                "deploy/k8s-job.yaml",
                "deploy/k8s-deployment.yaml",
                "deploy/k8s-cronjob.yaml",
            ],
        },
        "missing_route_record": {
            "record_candidate_primitive": not bool(nodes),
            "reason": "no_compiled_route" if not nodes else "compiled_route_exists",
        },
        "candidate": True,
        "serves_truth": False,
    }, indent=2, sort_keys=True)


def _primitive_snapshot_relpath(source_path: str) -> Path | None:
    source_rel = _safe_workspace_relpath(source_path)
    if source_rel is None or source_rel.suffix != ".py":
        return None
    try:
        suffix = source_rel.relative_to(Path(AIDEVOBSERVER_WORKSPACE_SOURCE_PREFIX))
    except ValueError:
        return None
    return Path(*AIDEVOBSERVER_WORKSPACE_PRIMITIVE_IMPORT_ROOT.split(".")) / suffix


def _primitive_package_init_files(module_rel: Path) -> list[Path]:
    out: list[Path] = []
    current = Path()
    for part in module_rel.parent.parts:
        current = current / part
        out.append(current / "__init__.py")
    return out


def _primitive_snapshot_files(components: list[dict]) -> tuple[list[dict], list[dict]]:
    files_by_path: dict[str, dict] = {}
    snapshots: list[dict] = []
    seen_sources: set[str] = set()
    for component in _actionable_components(components):
        source_ref = component.get("source_ref") or {}
        source_path = str(source_ref.get("path") or "").strip()
        if not source_path or source_path in seen_sources:
            continue
        module_rel = _primitive_snapshot_relpath(source_path)
        source_rel = _safe_workspace_relpath(source_path)
        if module_rel is None or source_rel is None:
            continue
        source_file = _resource(source_rel)
        if not source_file.is_file():
            continue
        try:
            source_text = source_file.read_text(encoding="utf-8")
        except OSError:
            continue
        seen_sources.add(source_path)
        for init_rel in _primitive_package_init_files(module_rel):
            files_by_path.setdefault(str(init_rel), {
                "path": str(init_rel),
                "language": "python",
                "source_snapshot": True,
                "content": '"""Workspace-local primitive snapshots materialized by AIDevObserver."""\n',
            })
        files_by_path[str(module_rel)] = {
            "path": str(module_rel),
            "language": "python",
            "source_snapshot": True,
            "source_path": source_path,
            "content": (
                f"# Workspace-local primitive snapshot copied by AIDevObserver from {source_path}.\n"
                f"{source_text}"
            ),
        }
        snapshots.append({
            "source_path": source_path,
            "workspace_path": str(module_rel),
            "component_labels": sorted({
                str(item.get("label") or "")
                for item in _actionable_components(components)
                if ((item.get("source_ref") or {}).get("path") == source_path)
            }),
            "candidate": True,
            "serves_truth": False,
        })
    return list(files_by_path.values()), snapshots


def _workspace_file_summary(files: list[dict]) -> dict:
    paths = [str(file.get("path") or "") for file in files]
    primitive_prefix = AIDEVOBSERVER_WORKSPACE_PRIMITIVE_ROOT + "/"
    return {
        "total_files": len(paths),
        "generated_app_files": len([path for path in paths if path.startswith("app/")]),
        "primitive_snapshot_files": len([path for path in paths if path.startswith(primitive_prefix)]),
        "test_files": len([path for path in paths if path.startswith("tests/") and path.endswith(".py")]),
        "runtime_files": len([
            path for path in paths
            if path.startswith("runtime/") or path.startswith("deploy/") or path == "Dockerfile"
        ]),
        "json_artifacts": len([path for path in paths if path.endswith(".json")]),
        "candidate": True,
        "serves_truth": False,
    }


def _component_selection_reasons(component: dict) -> list[str]:
    contract = component.get("contract") if isinstance(component.get("contract"), dict) else {}
    source_ref = component.get("source_ref") if isinstance(component.get("source_ref"), dict) else {}
    blackbox = component.get("blackbox") if isinstance(component.get("blackbox"), dict) else {}
    mutations = component.get("mutations") if isinstance(component.get("mutations"), list) else []
    fit = str(component.get("edge_fit") or "candidate")
    reasons: list[str] = []
    if _component_is_route_level(component):
        reasons.append("route-level capability blueprint/template record")
    elif _component_is_route_slot(component):
        reasons.append("typed capability slot record")
    if fit == "exact_match":
        reasons.append("exact input/output edge match")
    elif fit and fit not in {"candidate", "query_only"}:
        reasons.append(f"{fit.replace('_', ' ')} edge fit")
    if contract.get("input") and contract.get("output"):
        reasons.append(f"{contract.get('input')} -> {contract.get('output')}")
    if blackbox.get("does"):
        reasons.append(_compact_text(str(blackbox.get("does")), 120))
    if source_ref.get("path") and source_ref.get("name"):
        reasons.append(f"importable source ref: {source_ref.get('path')}::{source_ref.get('name')}")
    if mutations:
        reasons.append(
            "registered mutators: "
            + ", ".join(_mutation_ids(mutations)[:3])
        )
    return reasons[:5]


def _annotate_component_selection(components: list[dict]) -> list[dict]:
    out: list[dict] = []
    for component in components:
        annotated = {**component}
        annotated["selection_reasons"] = _component_selection_reasons(component)
        out.append(annotated)
    return out


def _route_context_components(components: list[dict], limit: int | None = None) -> list[dict]:
    rows = [
        component
        for component in components
        if _component_is_route_level(component) or _component_is_route_slot(component)
    ]
    rows = sorted(rows, key=_component_route_rank)
    return rows[:limit] if limit is not None else rows


def _route_context_summary(components: list[dict]) -> dict:
    rows = _route_context_components(components)
    return {
        "selected_route_records": len(rows),
        "blueprints": len([component for component in rows if _component_is_route_level(component)]),
        "slots": len([component for component in rows if _component_is_route_slot(component)]),
        "records": _annotate_component_selection(rows[:AIDEVOBSERVER_PLANNER_TOOL_RESULT_COMPONENT_LIMIT]),
        "policy": "route-level records guide broad tasks; executable primitives still provide implementation edges",
        "candidate": True,
        "serves_truth": False,
    }


def _source_token_budget_for_components(components: list[dict]) -> tuple[int, list[dict]]:
    total = 0
    files: list[dict] = []
    seen: set[str] = set()
    for component in _actionable_components(components):
        source_ref = component.get("source_ref") if isinstance(component.get("source_ref"), dict) else {}
        source_path = str(source_ref.get("path") or "")
        if not source_path or source_path in seen:
            continue
        source_rel = _safe_workspace_relpath(source_path)
        if source_rel is None:
            continue
        source_file = _resource(source_rel)
        if not source_file.is_file():
            continue
        try:
            text = source_file.read_text(encoding="utf-8")
        except OSError:
            continue
        seen.add(source_path)
        tokens = _estimate_token_count(text) + AIDEVOBSERVER_TOKEN_ESTIMATE_SOURCE_OVERHEAD
        total += tokens
        files.append({
            "path": source_path,
            "estimated_tokens": tokens,
            "chars": len(text),
            "candidate": True,
            "serves_truth": False,
        })
    return total, files


def _token_savings_summary(task: str, components: list[dict], planner_result: dict, execution_mode: str) -> dict:
    source_tokens, source_files = _source_token_budget_for_components(components)
    planner_tokens = int(planner_result.get("input_tokens") or 0) + int(planner_result.get("output_tokens") or 0)
    route_packet_tokens = _estimate_token_count(_observer_wrapped_task(task, components, planner_result)) if task else 0
    avoided = max(0, source_tokens - route_packet_tokens)
    return {
        "estimated_source_tokens_if_read": source_tokens,
        "compact_route_packet_tokens": route_packet_tokens,
        "planner_tokens": planner_tokens,
        "estimated_tokens_avoided": avoided,
        "codegen_tokens": 0 if execution_mode == "deterministic_template_worker" else "harness_fallback",
        "basis": (
            "source snapshots were copied into workspace; the planner/harness saw compact edge cards instead of full source"
            if source_tokens
            else "no source-backed primitive selected"
        ),
        "source_files": source_files,
        "candidate": True,
        "serves_truth": False,
    }


def _runtime_target_summary(task: str, execution_mode: str, recipe: dict) -> dict:
    lowered = task.lower()
    nodes = recipe.get("nodes") if isinstance(recipe.get("nodes"), list) else []
    trigger = "cli"
    target = AIDEVOBSERVER_RUNTIME_TARGET_LOCAL
    reason = "default local Python route"
    browserish = any(term in lowered for term in ("playwright", "browser", "scrape", "crawl", "extract tables"))
    apiish = any(term in lowered for term in ("api endpoint", "http endpoint", "webhook", "server", "service"))
    if execution_mode == AIDEVOBSERVER_NOOP_EXECUTION_MODE:
        target = AIDEVOBSERVER_RUNTIME_TARGET_NONE
        reason = "no build task accepted"
    elif any(term in lowered for term in ("cloud function", "lambda", "azure function", "gcp function")):
        target = AIDEVOBSERVER_RUNTIME_TARGET_CLOUD_FUNCTION
        trigger = "http"
        reason = "task explicitly requested a cloud-function-style runtime"
    elif any(term in lowered for term in ("cronjob", "cron job", "scheduled")):
        target = AIDEVOBSERVER_RUNTIME_TARGET_K8S_CRONJOB
        trigger = "cron"
        reason = "task is scheduled job-shaped"
    elif any(term in lowered for term in ("k8s", "kubernetes", "kube", "job")):
        target = AIDEVOBSERVER_RUNTIME_TARGET_K8S_JOB
        reason = "task mentions Kubernetes or job runtime"
    elif browserish and apiish:
        target = AIDEVOBSERVER_RUNTIME_TARGET_CONTAINER
        trigger = "http"
        reason = "HTTP/API boundary with browser automation benefits from a containerized runtime"
    elif browserish:
        target = AIDEVOBSERVER_RUNTIME_TARGET_CONTAINER
        reason = "browser automation benefits from a containerized runtime"
    elif apiish:
        target = AIDEVOBSERVER_RUNTIME_TARGET_CONTAINER
        trigger = "http"
        reason = "HTTP/API boundary is container-service shaped"
    if target == AIDEVOBSERVER_RUNTIME_TARGET_K8S_DEPLOYMENT:
        trigger = "http"
    return {
        "target": target,
        "trigger": trigger,
        "reason": reason,
        "emitter_status": "metadata_ready",
        "next_emitters": [
            "container.Dockerfile",
            "k8s.job.yaml",
            "k8s.deployment.yaml",
            "cloud.function.handler",
        ],
        "nodes": len(nodes),
        "candidate": True,
        "serves_truth": False,
    }


def _route_quality_summary(
    *,
    execution_mode: str,
    selected_components: list[dict],
    planner_result: dict,
    recipe: dict,
    workspace_files: list[dict] | None = None,
) -> dict:
    nodes = recipe.get("nodes") if isinstance(recipe.get("nodes"), list) else []
    exact = [
        item for item in selected_components
        if str(item.get("edge_fit") or "") == "exact_match"
    ]
    test_count = len([
        file for file in (workspace_files or [])
        if str(file.get("path") or "").startswith("tests/") and str(file.get("path") or "").endswith(".py")
    ])
    score = AIDEVOBSERVER_ROUTE_QUALITY_BASE_SCORE
    score += min(len(exact), AIDEVOBSERVER_IDE_GRAPH_COMPONENT_LIMIT) * AIDEVOBSERVER_ROUTE_QUALITY_EXACT_EDGE_POINTS
    score += min(len(nodes), AIDEVOBSERVER_PLANNER_TOOL_RESULT_COMPONENT_LIMIT) * AIDEVOBSERVER_ROUTE_QUALITY_NODE_POINTS
    if planner_result.get("status") == "used":
        score += AIDEVOBSERVER_ROUTE_QUALITY_PLANNER_POINTS
    if execution_mode == "deterministic_template_worker":
        score += AIDEVOBSERVER_ROUTE_QUALITY_DETERMINISTIC_POINTS
    elif execution_mode == "coding_harness_fallback":
        score -= AIDEVOBSERVER_ROUTE_QUALITY_HARNESS_PENALTY
    if test_count:
        score += AIDEVOBSERVER_ROUTE_QUALITY_TEST_POINTS
    score = max(0, min(AIDEVOBSERVER_ROUTE_QUALITY_MAX_SCORE, score))
    return {
        "score": score,
        "label": "high" if score >= 80 else "medium" if score >= 55 else "low",
        "exact_edge_matches": len(exact),
        "selected_components": len(selected_components),
        "recipe_nodes": len(nodes),
        "generated_test_files": test_count,
        "planner_used": planner_result.get("status") == "used",
        "deterministic": execution_mode == "deterministic_template_worker",
        "coding_harness_required": execution_mode == "coding_harness_fallback",
        "candidate": True,
        "serves_truth": False,
    }


def _adapter_summary(plan: dict, components: list[dict] | None = None, files: list[dict] | None = None) -> dict:
    selected = components if components is not None else plan.get("selected_components")
    if not isinstance(selected, list):
        selected = []
    runtime_target = plan.get("runtime_target") if isinstance(plan.get("runtime_target"), dict) else {}
    target = str(runtime_target.get("target") or "")
    mutator_ids: list[str] = []
    proof_obligations: list[str] = []
    runtime_mutators: list[str] = []
    selected_edges = 0
    for component in selected:
        if not isinstance(component, dict):
            continue
        if _component_is_actionable(component):
            selected_edges += 1
        for mutation in _normalize_mutation_options(component.get("mutations")):
            mutator = _mutation_id(mutation)
            if mutator and mutator not in mutator_ids:
                mutator_ids.append(mutator)
            for proof in mutation.get("proof_obligations") or []:
                proof_text = str(proof)
                if proof_text and proof_text not in proof_obligations:
                    proof_obligations.append(proof_text)
            runtime_targets = [str(item) for item in (mutation.get("runtime_targets") or [])]
            if target and target in runtime_targets and mutator and mutator not in runtime_mutators:
                runtime_mutators.append(mutator)
    emitted_files = [
        str(file.get("path") or "")
        for file in (files or [])
        if str(file.get("path") or "").startswith("runtime/")
        or str(file.get("path") or "").startswith("deploy/")
        or str(file.get("path") or "") == "Dockerfile"
    ]
    return {
        "selected_edge_count": selected_edges,
        "available_mutator_count": len(mutator_ids),
        "available_mutators": mutator_ids,
        "runtime_target": target or None,
        "runtime_target_mutators": runtime_mutators,
        "proof_obligations": proof_obligations,
        "emitted_runtime_files": emitted_files,
        "coding_harness_adapter_policy": "deterministic adapters before codegen",
        "candidate": True,
        "serves_truth": False,
    }


def _fallback_strategy(
    *,
    execution_mode: str,
    selected_models: list[str],
    selected_harnesses: list[str],
    model_ids: dict[str, str],
    planner_result: dict,
) -> dict:
    ordered_models = [
        {"key": key, "model": model_id}
        for key, model_id in _planner_model_candidates(selected_models, model_ids)
    ]
    return {
        "needed": execution_mode == "coding_harness_fallback",
        "reason": (
            "deterministic route compiled"
            if execution_mode == "deterministic_template_worker"
            else "input was not a build task"
            if execution_mode == AIDEVOBSERVER_NOOP_EXECUTION_MODE
            else "missing exact primitive route or unresolved glue"
        ),
        "planner_attempts": planner_result.get("attempts") or [],
        "model_order": ordered_models,
        "harness_order": list(selected_harnesses or ["opencode"]),
        "context_policy": "compact edge cards, blackbox descriptions, source refs, and generated tests only",
        "coding_harness_scope": "write missing glue/new primitive candidates only",
        "candidate": True,
        "serves_truth": False,
    }


def _build_process_phases(plan: dict, source_snapshots: list[dict], files: list[dict]) -> list[dict]:
    execution_mode = plan.get("execution_mode") or "coding_harness_fallback"
    ai_trace = plan.get("ai_trace") if isinstance(plan.get("ai_trace"), dict) else {}
    planner_trace = ai_trace.get("route_planning") if isinstance(ai_trace.get("route_planning"), dict) else {}
    recipe = plan.get("recipe") if isinstance(plan.get("recipe"), dict) else {}
    nodes = recipe.get("nodes") if isinstance(recipe.get("nodes"), list) else []
    selected = plan.get("selected_components") if isinstance(plan.get("selected_components"), list) else []
    route_context = plan.get("route_context") if isinstance(plan.get("route_context"), dict) else {}
    route_records = int(route_context.get("selected_route_records") or 0)
    test_files = [
        file for file in files
        if str(file.get("path") or "").startswith("tests/") and str(file.get("path") or "").endswith(".py")
    ]
    runtime_files = [
        file for file in files
        if str(file.get("path") or "").startswith("runtime/")
        or str(file.get("path") or "").startswith("deploy/")
        or str(file.get("path") or "") == "Dockerfile"
    ]
    deterministic = execution_mode == "deterministic_template_worker"
    no_op = execution_mode == AIDEVOBSERVER_NOOP_EXECUTION_MODE
    return [
        {
            "id": "task_received",
            "label": "Task received",
            "status": "skipped" if no_op else "done",
            "detail": "Concrete build task accepted." if not no_op else "Input did not look like a build task.",
        },
        {
            "id": "registry_search",
            "label": "Registry search",
            "status": "skipped" if no_op else "done",
            "detail": f"{len(selected)} high-confidence reusable edge match" + ("" if len(selected) == 1 else "es"),
        },
        {
            "id": "route_blueprints",
            "label": "Route blueprint search",
            "status": "skipped" if no_op else "done" if route_records else "gap",
            "detail": (
                f"{route_records} blueprint/template/slot record" + ("" if route_records == 1 else "s")
                if route_records
                else "No route-level record selected; using primitive edges directly."
            ),
        },
        {
            "id": "planner_tool_loop",
            "label": "Planner tool loop",
            "status": "done" if planner_trace.get("status") == "used" else "skipped",
            "detail": (
                f"{planner_trace.get('model') or 'planner'} made {planner_trace.get('model_calls') or 0} model call"
                f"{'' if planner_trace.get('model_calls') == 1 else 's'}."
                if planner_trace.get("status") == "used"
                else "Skipped because deterministic matching was sufficient."
            ),
        },
        {
            "id": "route_compiled",
            "label": "Route compiled",
            "status": "done" if nodes else ("skipped" if no_op else "pending"),
            "detail": f"{len(nodes)} recipe node" + ("" if len(nodes) == 1 else "s"),
        },
        {
            "id": "workspace_materialized",
            "label": "Workspace materialized",
            "status": "done" if files and not no_op else "skipped",
            "detail": f"{len(files)} workspace file" + ("" if len(files) == 1 else "s"),
        },
        {
            "id": "primitive_snapshots",
            "label": "Primitive code copied",
            "status": "done" if source_snapshots else ("skipped" if no_op else "pending"),
            "detail": f"{len(source_snapshots)} primitive source module" + ("" if len(source_snapshots) == 1 else "s"),
        },
        {
            "id": "smoke_tests",
            "label": "Behavior tests prepared",
            "status": "done" if test_files else ("skipped" if no_op else "pending"),
            "detail": f"{len(test_files)} generated test file" + ("" if len(test_files) == 1 else "s"),
        },
        {
            "id": "runtime_emitters",
            "label": "Runtime emitters prepared",
            "status": "done" if runtime_files else ("skipped" if no_op else "pending"),
            "detail": f"{len(runtime_files)} runtime/deploy artifact" + ("" if len(runtime_files) == 1 else "s"),
        },
        {
            "id": "coding_harness",
            "label": "Coding harness",
            "status": "skipped" if deterministic or no_op else "pending",
            "detail": "Not invoked; deterministic worker handled this run." if deterministic else "Used only when missing glue is required.",
        },
    ]


def _render_build_manifest(task: str, plan: dict, source_snapshots: list[dict], files: list[dict]) -> str:
    execution_mode = plan.get("execution_mode") or "coding_harness_fallback"
    ai_trace = plan.get("ai_trace") if isinstance(plan.get("ai_trace"), dict) else {}
    return json.dumps({
        "task": task.strip(),
        "execution_mode": execution_mode,
        "built_with": (
            "deterministic_template_worker"
            if execution_mode == "deterministic_template_worker"
            else "coding_harness_fallback"
            if execution_mode != AIDEVOBSERVER_NOOP_EXECUTION_MODE
            else "not_started"
        ),
        "known_model_calls": ai_trace.get("known_model_calls", 0),
        "planner_model_calls": (ai_trace.get("route_planning") or {}).get("model_calls", 0)
        if isinstance(ai_trace.get("route_planning"), dict) else 0,
        "coding_harness_calls": 0 if execution_mode == "deterministic_template_worker" else "fallback_only",
        "route_quality": plan.get("route_quality"),
        "token_savings": plan.get("token_savings"),
        "runtime_target": plan.get("runtime_target"),
        "fallback_strategy": plan.get("fallback_strategy"),
        "selected_route_context": plan.get("selected_route_context") or [],
        "route_context": plan.get("route_context"),
        "selected_components": plan.get("selected_components") or [],
        "edge_adapters": _adapter_summary(plan, plan.get("selected_components"), files),
        "source_snapshots": source_snapshots,
        "workspace": _workspace_file_summary(files),
        "runtime_emitters": [
            file.get("path")
            for file in files
            if str(file.get("path") or "").startswith("runtime/")
            or str(file.get("path") or "").startswith("deploy/")
            or str(file.get("path") or "") == "Dockerfile"
        ],
        "process_phases": _build_process_phases(plan, source_snapshots, files),
        "candidate": True,
        "serves_truth": False,
    }, indent=2, sort_keys=True)


def _new_ide_run_id() -> str:
    return "run_" + secrets.token_hex(IDE_RUN_ID_HEX_CHARS // 2)


def _ide_run_path(run_id: str) -> Path:
    return IDE_RUN_DIR / f"{run_id}.json"


def _ide_run_log_path(run_id: str) -> Path:
    return IDE_RUN_DIR / f"{run_id}.log"


def _read_ide_run(run_id: str) -> dict | None:
    if not _safe_id(run_id):
        return None
    path = _ide_run_path(run_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _write_ide_run(record: dict) -> dict:
    IDE_RUN_DIR.mkdir(parents=True, exist_ok=True)
    run_id = str(record.get("run_id") or _new_ide_run_id())
    existing = _read_ide_run(run_id) or {}
    stored = {
        **existing,
        **record,
        "run_id": run_id,
        "updated_at": int(time.time()),
        "candidate": True,
        "serves_truth": False,
    }
    if not stored.get("created_at"):
        stored["created_at"] = stored["updated_at"]
    _ide_run_path(run_id).write_text(json.dumps(stored, indent=2, sort_keys=True), encoding="utf-8")
    return stored


def _tail_text(path: Path, chars: int = IDE_RUN_OUTPUT_TAIL_CHARS) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return text[-chars:]


def _pid_running(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
        return True
    except OSError:
        return False


def _public_ide_run(record: dict, *, include_plan: bool = False) -> dict:
    out = dict(record)
    out.pop("log_path", None)
    if not include_plan:
        out.pop("plan", None)
    return out


def _ide_run_status(run_id: str) -> tuple[int, dict]:
    record = _read_ide_run(run_id)
    if not record:
        return 404, {"error": "IDE run not found", "serves_truth": False}
    pid = int(record.get("pid") or 0)
    log_path = Path(str(record.get("log_path") or _ide_run_log_path(run_id)))
    if record.get("status") == "running" and not _pid_running(pid):
        record = _write_ide_run({**record, "status": "finished_unknown", "finished_at": int(time.time())})
    return 200, {
        "service": SERVICE_ID,
        "run": {
            **_public_ide_run(record),
            "log_tail": _tail_text(log_path),
        },
        "candidate": True,
        "serves_truth": False,
    }


def _model_id_for_run(selected_models: list[str]) -> str:
    if "kimi" in selected_models:
        return os.environ.get(AIDEVOBSERVER_KIMI_MODEL_ENV, AIDEVOBSERVER_KIMI_MODEL_ID).strip() or AIDEVOBSERVER_KIMI_MODEL_ID
    return os.environ.get(AIDEVOBSERVER_GLM_MODEL_ENV, AIDEVOBSERVER_GLM_MODEL_ID).strip() or AIDEVOBSERVER_GLM_MODEL_ID


def _watch_ide_run(run_id: str, proc: subprocess.Popen) -> None:
    code = proc.wait()
    record = _read_ide_run(run_id) or {"run_id": run_id}
    _write_ide_run({
        **record,
        "status": "succeeded" if code == 0 else "failed",
        "returncode": code,
        "finished_at": int(time.time()),
    })


def _can_run_deterministic_template(task: str, plan: dict) -> bool:
    selected = plan.get("selected_components") or []
    if not selected:
        return False
    if _ide_task_is_complex_composition(task):
        return False
    if not (_ide_task_is_csv_import(task) or _ide_task_is_browser_table_export(task)):
        return False
    for component in selected:
        source_ref = component.get("source_ref") or {}
        if source_ref.get("path") in {
            AIDEVOBSERVER_CSV_PRIMITIVE_SOURCE_PATH,
            AIDEVOBSERVER_BROWSER_TABLE_PRIMITIVE_SOURCE_PATH,
        }:
            return True
    return False


def _safe_workspace_relpath(path: str) -> Path | None:
    rel = Path(str(path or ""))
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        return None
    return rel


def _materialize_workspace(run_id: str, files: list[dict]) -> tuple[Path, list[str]]:
    workspace_dir = IDE_RUN_DIR / run_id / "workspace"
    written: list[str] = []
    for file in files:
        rel = _safe_workspace_relpath(str(file.get("path") or ""))
        if rel is None:
            continue
        target = workspace_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(file.get("content") or ""), encoding="utf-8")
        written.append(str(rel))
    return workspace_dir, written


def _workspace_proofs(workspace_dir: Path, written: list[str]) -> list[dict]:
    proofs: list[dict] = []

    def add(proof_id: str, status: str, detail: str) -> None:
        proofs.append({
            "id": proof_id,
            "status": status,
            "detail": detail,
            "candidate": True,
            "serves_truth": False,
        })

    add("workspace_materialized", "pass" if written else "fail", f"{len(written)} files written")
    for rel in written:
        path = workspace_dir / rel
        if rel.endswith(".json"):
            try:
                parsed = json.loads(path.read_text(encoding="utf-8"))
                add(f"json_valid:{rel}", "pass", "valid JSON")
                if rel == "edge_adapter_plan.json":
                    selected_edges = parsed.get("selected_edges") if isinstance(parsed, dict) else None
                    available = parsed.get("deterministic_mutators_available") if isinstance(parsed, dict) else None
                    adapter_summary = parsed.get("adapter_summary") if isinstance(parsed, dict) else None
                    summary_ok = isinstance(adapter_summary, dict) and adapter_summary.get("candidate") is True
                    add(
                        "edge_adapter_plan_shape",
                        "pass" if isinstance(selected_edges, list) and isinstance(available, list) and summary_ok else "fail",
                        (
                            f"{len(selected_edges or [])} selected edges; {len(available or [])} deterministic mutators"
                            if isinstance(selected_edges, list) and isinstance(available, list) and summary_ok
                            else "missing selected_edges, deterministic_mutators_available, or candidate adapter_summary"
                        ),
                    )
                    truth_ok = isinstance(parsed, dict) and parsed.get("candidate") is True and parsed.get("serves_truth") is False
                    add(
                        "edge_adapter_plan_truth_boundary",
                        "pass" if truth_ok else "fail",
                        "candidate-only adapter plan" if truth_ok else "adapter plan missing candidate=true or serves_truth=false",
                    )
                if rel == AIDEVOBSERVER_WORKSPACE_BUILD_MANIFEST_PATH:
                    adapters = parsed.get("edge_adapters") if isinstance(parsed, dict) else None
                    add(
                        "build_manifest_adapter_summary",
                        "pass" if isinstance(adapters, dict) and adapters.get("candidate") is True else "fail",
                        (
                            f"{adapters.get('available_mutator_count', 0)} available mutators"
                            if isinstance(adapters, dict)
                            else "missing edge_adapters summary"
                        ),
                    )
            except (OSError, json.JSONDecodeError) as exc:
                add(f"json_valid:{rel}", "fail", str(exc))
        elif rel.endswith(".py"):
            try:
                compile(path.read_text(encoding="utf-8"), str(path), "exec")
                add(f"python_compiles:{rel}", "pass", "valid Python syntax")
            except (OSError, SyntaxError) as exc:
                add(f"python_compiles:{rel}", "fail", str(exc))
        elif rel.endswith(".yaml") or rel.endswith(".yml"):
            try:
                text = path.read_text(encoding="utf-8")
                has_api = "apiVersion:" in text
                has_kind = "\nkind:" in "\n" + text
                add(
                    f"yaml_k8s_shape:{rel}",
                    "pass" if has_api and has_kind else "fail",
                    "contains apiVersion and kind" if has_api and has_kind else "missing apiVersion or kind",
                )
            except OSError as exc:
                add(f"yaml_k8s_shape:{rel}", "fail", str(exc))
        elif rel == "Dockerfile":
            try:
                text = path.read_text(encoding="utf-8")
                ok = text.lstrip().startswith("#") and "\nFROM " in "\n" + text and "\nCMD " in "\n" + text
                add(
                    "dockerfile_shape:Dockerfile",
                    "pass" if ok else "fail",
                    "contains FROM and CMD" if ok else "missing FROM or CMD",
                )
            except OSError as exc:
                add("dockerfile_shape:Dockerfile", "fail", str(exc))
    for rel in written:
        if not rel.startswith("tests/") or not rel.endswith(".py"):
            continue
        try:
            proc = subprocess.run(  # noqa: S603
                [sys.executable, rel],
                cwd=str(workspace_dir),
                capture_output=True,
                text=True,
                timeout=AIDEVOBSERVER_WORKSPACE_TEST_TIMEOUT_SECONDS,
                check=False,
            )
            detail = (proc.stdout + "\n" + proc.stderr).strip() or f"exit {proc.returncode}"
            add(
                f"smoke_test:{rel}",
                "pass" if proc.returncode == 0 else "fail",
                _compact_text(detail, 700),
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            add(f"smoke_test:{rel}", "fail", str(exc))
    return proofs


def _repo_relative_label(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return path.name


def _run_deterministic_template_worker(plan: dict, *, dry_run: bool) -> tuple[int, dict]:
    run_id = _new_ide_run_id()
    log_path = _ide_run_log_path(run_id)
    IDE_RUN_DIR.mkdir(parents=True, exist_ok=True)
    files = plan.get("workspace_files") if isinstance(plan.get("workspace_files"), list) else []
    workspace_dir, written = _materialize_workspace(run_id, files)
    selected = plan.get("selected_components") or []
    recipe = plan.get("recipe") if isinstance(plan.get("recipe"), dict) else {}
    ai_trace = plan.get("ai_trace") if isinstance(plan.get("ai_trace"), dict) else {}
    known_model_calls = ai_trace.get("known_model_calls", 0)
    source_snapshots: list[dict] = []
    for file in files:
        if file.get("path") != AIDEVOBSERVER_WORKSPACE_BUILD_MANIFEST_PATH:
            continue
        try:
            manifest = json.loads(str(file.get("content") or "{}"))
        except json.JSONDecodeError:
            manifest = {}
        if isinstance(manifest.get("source_snapshots"), list):
            source_snapshots = manifest["source_snapshots"]
    proofs = _workspace_proofs(workspace_dir, written)
    proof_pass = all(proof.get("status") == "pass" for proof in proofs)
    with log_path.open("w", encoding="utf-8") as log:
        log.write("AIDevObserver deterministic route compiler\n")
        log.write("mode: deterministic_template_worker\n")
        log.write(f"recipe_id: {recipe.get('recipe_id') or '-'}\n")
        log.write(f"model_calls: {known_model_calls}\n")
        log.write("coding_harness_invoked: false\n")
        if isinstance(plan.get("route_quality"), dict):
            log.write(
                "route_quality: "
                f"{plan['route_quality'].get('score')}/{AIDEVOBSERVER_ROUTE_QUALITY_MAX_SCORE} "
                f"({plan['route_quality'].get('label')})\n"
            )
        if isinstance(plan.get("runtime_target"), dict):
            log.write(
                "runtime_target: "
                f"{plan['runtime_target'].get('target')} "
                f"trigger:{plan['runtime_target'].get('trigger')}\n"
            )
        if isinstance(plan.get("token_savings"), dict):
            log.write(
                "estimated_tokens_avoided: "
                f"{plan['token_savings'].get('estimated_tokens_avoided')}\n"
            )
        log.write(f"dry_run: {str(dry_run).lower()}\n")
        log.write(f"selected_components: {len(selected)}\n")
        log.write("process_phases:\n")
        for phase in _build_process_phases(plan, source_snapshots, files):
            log.write(
                "- "
                f"{phase.get('label')}: {phase.get('status')} "
                f"({phase.get('detail')})\n"
            )
        if recipe.get("nodes"):
            log.write("recipe_nodes:\n")
            for node in recipe.get("nodes") or []:
                log.write(
                    "- "
                    f"{node.get('id')}: {node.get('primitive')} "
                    f"{node.get('input')} -> {node.get('output')}\n"
                )
        for component in selected[:AIDEVOBSERVER_ROUTE_PACKET_COMPONENT_LIMIT]:
            contract = component.get("contract") or {}
            source_ref = component.get("source_ref") or {}
            log.write(
                "- "
                f"{component.get('label')}; "
                f"edge:{contract.get('input')}=>{contract.get('output')}; "
                f"ref:{source_ref.get('path')}::{source_ref.get('name')}\n"
            )
        workspace_label = _repo_relative_label(workspace_dir)
        log.write(f"workspace_artifact: {workspace_label}\n")
        if source_snapshots:
            log.write("source_snapshots:\n")
            for snapshot in source_snapshots:
                log.write(
                    "- "
                    f"{snapshot.get('source_path')} -> {snapshot.get('workspace_path')}\n"
                )
        log.write("files:\n")
        for path in written:
            log.write(f"- {path}\n")
        log.write("proofs:\n")
        for proof in proofs:
            log.write(f"- {proof.get('id')}: {proof.get('status')} ({proof.get('detail')})\n")
    run = _write_ide_run({
        "run_id": run_id,
        "status": "succeeded" if proof_pass else "failed",
        "pid": None,
        "plan_id": plan.get("plan_id"),
        "task_summary": plan.get("task_summary"),
        "harness": "deterministic_template_worker",
        "model": "none" if not known_model_calls else "planner_only",
        "execution_mode": "deterministic_template_worker",
        "timeout_seconds": 0,
        "dry_run": dry_run,
        "returncode": 0 if proof_pass else 1,
        "finished_at": int(time.time()),
        "log_path": str(log_path),
        "workspace_artifact": _repo_relative_label(workspace_dir),
        "workspace_files_written": written,
        "recipe": recipe,
        "ai_trace": plan.get("ai_trace"),
        "route_quality": plan.get("route_quality"),
        "token_savings": plan.get("token_savings"),
        "runtime_target": plan.get("runtime_target"),
        "fallback_strategy": plan.get("fallback_strategy"),
        "proofs": proofs,
        "command_preview": "deterministic template compiler -> materialize selected primitive route",
        "plan": plan,
    })
    return 200, {
        "service": SERVICE_ID,
        "run": {**_public_ide_run(run), "log_tail": _tail_text(log_path)},
        "plan": plan,
        "candidate": True,
        "serves_truth": False,
    }


def ide_run_start(body: dict) -> tuple[int, dict]:
    """POST /ide/run — compile deterministic routes first; use the coding harness only as fallback."""

    status, plan = ide_run_plan(body)
    if status != 200:
        return status, plan
    dry_run = bool(body.get("dry_run"))
    force_harness = bool(body.get("force_harness"))
    if plan.get("execution_mode") == AIDEVOBSERVER_NOOP_EXECUTION_MODE:
        return 200, {
            "service": SERVICE_ID,
            "run": {
                "status": "not_started",
                "harness": "none",
                "model": "none",
                "execution_mode": AIDEVOBSERVER_NOOP_EXECUTION_MODE,
                "message": "No run was started because the input was not a build, review, or implementation task.",
                "route_quality": plan.get("route_quality"),
                "token_savings": plan.get("token_savings"),
                "runtime_target": plan.get("runtime_target"),
                "fallback_strategy": plan.get("fallback_strategy"),
                "candidate": True,
                "serves_truth": False,
            },
            "plan": plan,
            "candidate": True,
            "serves_truth": False,
        }
    if not force_harness and plan.get("execution_mode") == "deterministic_template_worker":
        return _run_deterministic_template_worker(plan, dry_run=dry_run)
    harnesses = plan.get("harnesses") or ["opencode"]
    harness = str(harnesses[0] if harnesses else "opencode")
    if harness not in {"opencode", "aider"}:
        return 400, {
            "error": "browser IDE execution currently supports opencode or aider",
            "plan": plan,
            "serves_truth": False,
        }
    timeout = int(body.get("timeout_seconds") or IDE_RUN_DEFAULT_TIMEOUT_SECONDS)
    timeout = max(30, min(timeout, IDE_RUN_DEFAULT_TIMEOUT_SECONDS))
    run_id = _new_ide_run_id()
    log_path = _ide_run_log_path(run_id)
    IDE_RUN_DIR.mkdir(parents=True, exist_ok=True)
    model = _model_id_for_run(list(plan.get("models") or []))
    argv = [
        sys.executable,
        str(_resource("scripts/build_loop.py")),
        "--run",
        "--harness",
        harness,
        "--model",
        model,
        "--task",
        str(plan.get("harness_task") or plan.get("user_task") or ""),
        "--timeout-sec",
        str(timeout),
    ]
    if dry_run:
        argv.append("--dry-run")
    env = {
        **os.environ,
        "PYTHONPATH": str(REPO_ROOT) + os.pathsep + os.environ.get("PYTHONPATH", ""),
        "AIDEVOBSERVER_IDE_RUN_ID": run_id,
    }
    with log_path.open("w", encoding="utf-8") as log:
        log.write("AIDevObserver starting coding harness\n")
        display_argv = [
            sys.executable,
            str(_resource("scripts/build_loop.py")),
            "--run",
            "--harness",
            harness,
            "--model",
            model,
            "<observer-wrapped-task>",
            "--timeout-sec",
            str(timeout),
        ]
        if dry_run:
            display_argv.append("--dry-run")
        log.write("$ " + " ".join(display_argv) + "\n\n")
        log.flush()
        proc = subprocess.Popen(  # noqa: S603
            argv,
            cwd=str(REPO_ROOT),
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
            start_new_session=True,
        )
    run = _write_ide_run({
        "run_id": run_id,
        "status": "running",
        "pid": proc.pid,
        "plan_id": plan.get("plan_id"),
        "task_summary": plan.get("task_summary"),
        "harness": harness,
        "model": model,
        "execution_mode": "coding_harness_fallback",
        "timeout_seconds": timeout,
        "dry_run": dry_run,
        "log_path": str(log_path),
        "command_preview": (
            f"{sys.executable} scripts/build_loop.py --run --harness {harness} "
            f"--model {model} --task <observer-wrapped-task>"
            + (" --dry-run" if dry_run else "")
        ),
        "ai_trace": plan.get("ai_trace"),
        "route_quality": plan.get("route_quality"),
        "token_savings": plan.get("token_savings"),
        "runtime_target": plan.get("runtime_target"),
        "fallback_strategy": plan.get("fallback_strategy"),
        "plan": plan,
    })
    threading.Thread(target=_watch_ide_run, args=(run_id, proc), name=f"aidevobserver-{run_id}", daemon=True).start()
    return 200, {
        "service": SERVICE_ID,
        "run": {**_public_ide_run(run), "log_tail": _tail_text(log_path)},
        "plan": plan,
        "candidate": True,
        "serves_truth": False,
    }


def _ide_workspace_files(task: str, plan: dict, components: list[dict]) -> list[dict]:
    test_content = ""
    files = [
        {
            "path": "task.md",
            "language": "markdown",
            "content": "# Task\n\n" + task.strip() + "\n",
        },
    ]
    if plan.get("execution_mode") == AIDEVOBSERVER_NOOP_EXECUTION_MODE:
        return files
    files.append({
        "path": "candidate_bundle.txt",
        "language": "text",
        "content": _render_candidate_bundle(task, components),
    })
    can_materialize = plan.get("execution_mode") == "deterministic_template_worker"
    if (
        can_materialize
        and
        isinstance(plan.get("recipe"), dict)
        and plan["recipe"].get("template") in {
            AIDEVOBSERVER_PLANNER_ROUTE_TEMPLATE_ID,
            AIDEVOBSERVER_BROWSER_POLICY_API_RECIPE_TEMPLATE_ID,
        }
        and _can_materialize_browser_policy_route(components, plan.get("planner_result"))
    ):
        files.append({
            "path": "app/company_table_policy_api_flow.py",
            "language": "python",
            "content": _render_browser_policy_api_scaffold(components),
        })
        test_content = _render_browser_policy_api_flow_test()
    elif can_materialize and _ide_task_is_browser_table_export(task):
        files.append({
            "path": "app/browser_table_export_flow.py",
            "language": "python",
            "content": _render_browser_table_scaffold(components),
        })
        test_content = _render_browser_table_flow_test()
    elif can_materialize and _ide_task_is_csv_import(task):
        files.append({
            "path": "app/vendor_csv_import_flow.py",
            "language": "python",
            "content": _render_csv_scaffold(components),
        })
        test_content = _render_csv_flow_test()
    if test_content:
        files.append({
            "path": AIDEVOBSERVER_WORKSPACE_TEST_PATH,
            "language": "python",
            "content": test_content,
        })
    primitive_files, source_snapshots = _primitive_snapshot_files(components)
    files.extend(primitive_files)
    files.extend(_runtime_emitter_files(task, plan))
    if isinstance(plan.get("recipe"), dict):
        files.append({
            "path": "recipe.json",
            "language": "json",
            "content": json.dumps(plan["recipe"], indent=2, sort_keys=True),
        })
    if isinstance(plan.get("planner_result"), dict) and plan["planner_result"].get("tool_loop"):
        files.append({
            "path": "planner_trace.json",
            "language": "json",
            "content": json.dumps(plan["planner_result"], indent=2, sort_keys=True),
        })
    files.append({
        "path": "run_report.json",
        "language": "json",
        "content": _render_run_report(plan),
    })
    files.append({
        "path": "edge_adapter_plan.json",
        "language": "json",
        "content": _render_edge_adapter_plan(plan, components),
    })
    manifest_placeholder = {
        "path": AIDEVOBSERVER_WORKSPACE_BUILD_MANIFEST_PATH,
        "language": "json",
    }
    files.append({
        "path": AIDEVOBSERVER_WORKSPACE_BUILD_MANIFEST_PATH,
        "language": "json",
        "content": _render_build_manifest(task, plan, source_snapshots, files + [manifest_placeholder]),
    })
    return files


def _ide_run_graph(
    task: str,
    selected_models: list[str],
    selected_harnesses: list[str],
    components: list[dict],
    execution_mode: str,
    planner_result: dict | None = None,
) -> dict:
    selected = _actionable_components(components)
    route_context = _route_context_components(components)
    component_labels = [str(component.get("label") or "candidate") for component in selected[:3]]
    component_detail = ", ".join(component_labels) if component_labels else "no high-confidence reusable route selected"
    route_labels = [str(component.get("label") or "route") for component in route_context[:2]]
    route_detail = ", ".join(route_labels) if route_labels else "no route-level blueprint selected"
    deterministic = execution_mode == "deterministic_template_worker"
    no_op = execution_mode == AIDEVOBSERVER_NOOP_EXECUTION_MODE
    planner_status = str((planner_result or {}).get("status") or "skipped")
    tool_results = (planner_result or {}).get("tool_results") if isinstance((planner_result or {}).get("tool_results"), list) else []
    planner_tool_count = sum(int(result.get("component_count") or 0) for result in tool_results if isinstance(result, dict))
    return {
        "nodes": [
            {
                "id": "task",
                "label": "Plain task",
                "status": "received",
                "detail": task[:140],
            },
            {
                "id": "guidance",
                "label": "Observer guidance",
                "status": "idle" if no_op else "enabled",
                "detail": (
                    "waiting for a concrete build/review/implementation task"
                    if no_op
                    else "reuse search, edge matching, mutator checks, token estimates"
                ),
            },
            {
                "id": "planner",
                "label": "Planner tool loop",
                "status": "skipped" if no_op or deterministic else planner_status,
                "detail": (
                    "not needed for exact deterministic route"
                    if deterministic
                    else
                    f"registry tool results: {planner_tool_count} compact component cards"
                    if planner_tool_count
                    else "planner may request registry tools for ambiguous routes"
                ),
            },
            {
                "id": "search",
                "label": "Primitive search",
                "status": "skipped" if no_op else "searched",
                "detail": "not run for greeting/status input" if no_op else component_detail,
            },
            {
                "id": "route_context",
                "label": "Blueprint/template route",
                "status": "skipped" if no_op else "selected" if route_context else "gap",
                "detail": "not run for greeting/status input" if no_op else route_detail,
            },
            {
                "id": "edges",
                "label": "Edge + mutation fit",
                "status": "candidate",
                "detail": "input/output contracts and deterministic mutation options are checked before rebuilds",
            },
            {
                "id": "execution",
                "label": "No run" if no_op else "Deterministic worker" if deterministic else "Coding harness fallback",
                "status": "idle" if no_op else "selected" if deterministic else "planned",
                "detail": (
                    "type a concrete task to start a run"
                    if no_op
                    else
                    "compile selected primitive/template route; no model call needed"
                    if deterministic
                    else ", ".join(selected_harnesses)
                ),
            },
            {
                "id": "review",
                "label": "Session review",
                "status": "pending",
                "detail": "findings, source refs, and tokens saved appear after execution or transcript review",
            },
        ],
        "components": components,
        "route_context": _route_context_summary(components),
        "selected_components": selected,
        "models": selected_models,
        "execution_mode": execution_mode,
        "candidate": True,
        "serves_truth": False,
    }


def _harness_status(key: str) -> str:
    if key == "opencode":
        return "ready" if (_resource("build")).exists() and (_resource("opencode.json")).exists() else "missing"
    if key == "claude_code":
        return "ready" if (_resource("scripts") / "aidevobserver_mcp_server.py").exists() else "missing"
    if key == "codex":
        return "available"
    if key == "aider":
        return "available"
    return "candidate"


def _harness_lanes() -> list[dict]:
    enabled = set(_configured_harnesses())
    lanes = []
    for key, meta in AIDEVOBSERVER_HARNESS_DEFAULTS.items():
        lanes.append({
            "key": key,
            **meta,
            "enabled": key in enabled,
            "status": _harness_status(key),
            "candidate": True,
            "serves_truth": False,
        })
    return lanes


def _ollama_tags(base_url: str) -> tuple[list[str], str | None]:
    url = base_url.rstrip("/") + "/api/tags"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            payload = json.loads(resp.read() or b"{}")
        tags = sorted(
            str(item.get("name"))
            for item in payload.get("models", [])
            if isinstance(item, dict) and item.get("name")
        )
        return tags, None
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        return [], str(exc)


def _model_lanes() -> list[dict]:
    local_base = os.environ.get(OLLAMA_HOST_ENV, DEFAULT_OLLAMA_HOST).strip() or DEFAULT_OLLAMA_HOST
    local_tags, _local_error = _ollama_tags(local_base)
    cloud_ready = bool(os.environ.get(AIDEVOBSERVER_OLLAMA_API_KEY_ENV, "").strip())
    kimi_model = os.environ.get(AIDEVOBSERVER_KIMI_MODEL_ENV, AIDEVOBSERVER_KIMI_MODEL_ID).strip() or AIDEVOBSERVER_KIMI_MODEL_ID
    glm_model = os.environ.get(AIDEVOBSERVER_GLM_MODEL_ENV, AIDEVOBSERVER_GLM_MODEL_ID).strip() or AIDEVOBSERVER_GLM_MODEL_ID
    selected = _model_provider()

    def lane(key: str, title: str, model: str, role: str) -> dict:
        local_ready = model in local_tags
        return {
            "key": key,
            "title": title,
            "model": model,
            "role": role,
            "provider": "ollama-cloud",
            "cloud_base_url": AIDEVOBSERVER_OLLAMA_CLOUD_BASE_URL,
            "cloud_ready": cloud_ready,
            "local_ollama_host": local_base,
            "local_ready": local_ready,
            "reachable": bool(cloud_ready or local_ready),
            "status": "ready" if (cloud_ready or local_ready) else "not_connected",
            "selected": selected == key,
        }

    deterministic_lane = {
        "key": "deterministic",
        "title": "Deterministic",
        "model": "",
        "role": "edge search, route compilation, and template workers — no model calls",
        "provider": "local-deterministic",
        "cloud_base_url": "",
        "cloud_ready": False,
        "local_ollama_host": "",
        "local_ready": True,
        "reachable": True,
        "status": "ready",
        "selected": selected == "deterministic",
    }
    return [
        deterministic_lane,
        lane("kimi", "Kimi code", kimi_model, "code-session digesting and implementation-oriented rerank"),
        lane("glm", "GLM reasoning", glm_model, "architecture review and higher-reasoning rerank"),
    ]


def _estimate_token_count(text: str) -> int:
    return max(1, (len(text or "") + AIDEVOBSERVER_TOKEN_CHAR_DIVISOR - 1) // AIDEVOBSERVER_TOKEN_CHAR_DIVISOR)


def _planner_model_choice(selected_models: list[str], model_ids: dict[str, str]) -> tuple[str, str]:
    key = "kimi" if "kimi" in selected_models else "glm" if "glm" in selected_models else _model_provider()
    if key not in {"kimi", "glm"}:
        key = "kimi"
    return key, model_ids.get(key) or AIDEVOBSERVER_KIMI_MODEL_ID


def _planner_model_candidates(selected_models: list[str], model_ids: dict[str, str]) -> list[tuple[str, str]]:
    keys = [str(model) for model in selected_models if str(model) in {"kimi", "glm"}]
    if not keys:
        keys = [_model_provider()]
    ordered: list[str] = []
    for key in keys + ["kimi", "glm"]:
        if key in {"kimi", "glm"} and key not in ordered:
            ordered.append(key)
    return [
        (key, model_ids.get(key) or (AIDEVOBSERVER_KIMI_MODEL_ID if key == "kimi" else AIDEVOBSERVER_GLM_MODEL_ID))
        for key in ordered
    ]


def _planner_endpoint(model_id: str) -> tuple[str, dict[str, str], str | None]:
    api_key = os.environ.get(AIDEVOBSERVER_OLLAMA_API_KEY_ENV, "").strip()
    if api_key:
        return (
            AIDEVOBSERVER_OLLAMA_CLOUD_BASE_URL.rstrip("/") + "/chat/completions",
            {"Authorization": f"Bearer {api_key}"},
            "ollama-cloud",
        )
    local_base = os.environ.get(OLLAMA_HOST_ENV, DEFAULT_OLLAMA_HOST).strip() or DEFAULT_OLLAMA_HOST
    local_tags, error = _ollama_tags(local_base)
    if model_id in local_tags:
        return (
            local_base.rstrip("/") + "/v1/chat/completions",
            {},
            "ollama-local",
        )
    return "", {}, error or "model_not_available"


def _planner_candidate_bundle(task: str, components: list[dict]) -> str:
    rows = [
        f"Q {task}",
        "T0 candidate_route",
        "OUTPUT PlanDelta JSON only",
        "",
    ]
    if components:
        rows.append("S0 route PlainTask>ImplementationPlan req:contracts,blackbox")
        for idx, component in enumerate(components[:AIDEVOBSERVER_IDE_GRAPH_COMPONENT_LIMIT]):
            contract = component.get("contract") or {}
            source_ref = component.get("source_ref") or {}
            blackbox = component.get("blackbox") or {}
            does = blackbox.get("does") if isinstance(blackbox, dict) else str(blackbox or "")
            rows.append(
                f"C0.{idx} {component.get('label') or 'component'} "
                f"{contract.get('input') or 'unknown'}>{contract.get('output') or 'unknown'} "
                f"fit:{component.get('edge_fit') or 'candidate'} "
                f"does:{_compact_text(str(does or ''), 110)} "
                f"src:{source_ref.get('path') or '-'}::{source_ref.get('name') or '-'}"
            )
    else:
            rows.append("N0 reason:no_candidate_components_found")
    return "\n".join(rows) + "\n"


def _planner_chat_json(
    *,
    stage: str,
    task: str,
    selected_models: list[str],
    model_ids: dict[str, str],
    system: str,
    user: str,
    max_tokens: int,
) -> dict:
    model_key, model_id = _planner_model_choice(selected_models, model_ids)
    base = {
        "stage": stage,
        "model_key": model_key,
        "model": model_id,
        "model_calls": 0,
        "candidate": True,
        "serves_truth": False,
    }
    attempts: list[dict] = []
    for candidate_key, candidate_model_id in _planner_model_candidates(selected_models, model_ids):
        endpoint, auth_headers, provider = _planner_endpoint(candidate_model_id)
        attempt_base = {
            **base,
            "model_key": candidate_key,
            "model": candidate_model_id,
            "provider": provider,
        }
        if not endpoint:
            attempts.append({
                "model_key": candidate_key,
                "model": candidate_model_id,
                "status": "unavailable",
                "reason": str(provider or "model_unavailable"),
            })
            continue
        body = {
            "model": candidate_model_id,
            "temperature": 0,
            "max_tokens": max_tokens,
            "stream": False,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(body).encode("utf-8"),
                headers={"Content-Type": "application/json", **auth_headers},
                method="POST",
            )
            started = time.perf_counter()
            with urllib.request.urlopen(req, timeout=24) as resp:
                payload = json.loads(resp.read() or b"{}")
            output = str(((payload.get("choices") or [{}])[0].get("message") or {}).get("content") or "")
            finish_reason = (payload.get("choices") or [{}])[0].get("finish_reason")
            parsed = _extract_json_object(output)
            usage = payload.get("usage") or {}
            prior_model_calls = len([
                item for item in attempts
                if item.get("status") in {"used", "malformed"}
            ])
            result = {
                **attempt_base,
                "status": "used" if parsed else "malformed",
                "finish_reason": finish_reason,
                "endpoint_kind": "openai_compatible",
                "model_calls": prior_model_calls + 1,
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "input_tokens": usage.get("prompt_tokens") or _estimate_token_count(system + user),
                "output_tokens": usage.get("completion_tokens") or _estimate_token_count(output),
                "prompt_chars": len(system) + len(user),
                "output_chars": len(output),
                "json": parsed,
                "raw_output": output[:900],
                "task_digest": _digest({"task": task}),
                "attempts": attempts + [{
                    "model_key": candidate_key,
                    "model": candidate_model_id,
                    "status": "used" if parsed else "malformed",
                    "provider": provider,
                }],
            }
            if parsed:
                return result
            attempts.append(result["attempts"][-1])
        except (OSError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            attempts.append({
                "model_key": candidate_key,
                "model": candidate_model_id,
                "status": "unavailable",
                "reason": f"{type(exc).__name__}: {exc}",
                "provider": provider,
            })
    return {
        **base,
        "status": "unavailable",
        "reason": "all_planner_models_unavailable_or_malformed",
        "model_calls": len([item for item in attempts if item.get("status") in {"used", "malformed"}]),
        "attempts": attempts,
    }


def _planner_component_card(component: dict) -> dict:
    contract = component.get("contract") or {}
    source_ref = component.get("source_ref") or {}
    blackbox = component.get("blackbox") if isinstance(component.get("blackbox"), dict) else {}
    mutations = component.get("mutations") or []
    return {
        "alias": component.get("planner_alias"),
        "label": component.get("label"),
        "input": contract.get("input") or "unknown",
        "output": contract.get("output") or "unknown",
        "fit": component.get("edge_fit") or "candidate",
        "does": _compact_text(blackbox.get("does") if blackbox else "", 120),
        "mutations": _mutation_ids(mutations)[:3],
        "source": f"{source_ref.get('path') or '-'}::{source_ref.get('name') or '-'}",
    }


def _planner_tool_groups(task: str, request: dict | None = None) -> set[str]:
    allowed = {
        "csv_import",
        "browser_table_export",
        "api_boundary",
        "account_state",
        "policy_decision",
        "persistence",
        "response_emit",
    }
    groups = set(_ide_task_capability_groups(task))
    raw = (request or {}).get("groups") if isinstance(request, dict) else None
    if isinstance(raw, list):
        groups.update(str(item) for item in raw if str(item) in allowed)
    elif isinstance(raw, str) and raw in allowed:
        groups.add(raw)
    return groups & allowed


def _execute_planner_tool_requests(
    *,
    task: str,
    requests: list,
    registry_cwd: str | None,
) -> tuple[list[dict], list[dict]]:
    combined: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    def add_component(component: dict) -> dict:
        key = _component_key(component)
        for existing in combined:
            if _component_key(existing) == key:
                return existing
        item = {**component, "planner_alias": f"P{len(combined)}"}
        seen.add(key)
        combined.append(item)
        return item

    results: list[dict] = []
    bounded_requests = requests[:AIDEVOBSERVER_PLANNER_TOOL_LOOP_MAX_CALLS]
    for index, raw_request in enumerate(bounded_requests):
        request = raw_request if isinstance(raw_request, dict) else {}
        tool = str(request.get("tool") or request.get("name") or "").strip()
        if tool == AIDEVOBSERVER_PLANNER_TOOL_PREINDEXED:
            groups = _planner_tool_groups(task, request)
            found = _preindexed_components_for_groups(groups)
            cards = [_planner_component_card(add_component(component)) for component in found]
            results.append({
                "index": index,
                "tool": tool,
                "status": "ok",
                "groups": sorted(groups),
                "component_count": len(cards),
                "components": cards,
                "candidate": True,
                "serves_truth": False,
            })
            continue
        if tool == AIDEVOBSERVER_PLANNER_TOOL_REGISTRY_SEARCH:
            edges = _ide_task_edges(task)
            query = str(request.get("query") or task).strip()
            requested_input = request.get("requested_input") or edges.get("requested_input")
            requested_output = request.get("requested_output") or edges.get("requested_output")
            status, payload = registry_search_response(
                query,
                registry_cwd,
                limit=AIDEVOBSERVER_PLANNER_TOOL_RESULT_COMPONENT_LIMIT,
                requested_input=requested_input,
                requested_output=requested_output,
                visibility_scope=AIDEVOBSERVER_VISIBILITY_SCOPE_LOCAL if registry_cwd else AIDEVOBSERVER_VISIBILITY_SCOPE_PUBLIC,
            )
            found = _components_from_registry_payload(payload) if status == 200 else []
            cards = [_planner_component_card(add_component(component)) for component in found]
            results.append({
                "index": index,
                "tool": tool,
                "status": "ok" if status == 200 else "error",
                "query": query,
                "requested_input": requested_input,
                "requested_output": requested_output,
                "component_count": len(cards),
                "components": cards,
                "error": None if status == 200 else payload.get("error"),
                "candidate": True,
                "serves_truth": False,
            })
            continue
        results.append({
            "index": index,
            "tool": tool or "unknown",
            "status": "error",
            "error": "unknown_planner_tool",
            "candidate": True,
            "serves_truth": False,
        })

    if not results:
        groups = _planner_tool_groups(task)
        found = _preindexed_components_for_groups(groups)
        cards = [_planner_component_card(add_component(component)) for component in found]
        results.append({
            "index": 0,
            "tool": AIDEVOBSERVER_PLANNER_TOOL_PREINDEXED,
            "status": "ok",
            "groups": sorted(groups),
            "component_count": len(cards),
            "components": cards,
            "fallback": "no_tool_requests",
            "candidate": True,
            "serves_truth": False,
        })

    return combined, results


def _planner_tool_result_lines(tool_results: list[dict]) -> str:
    rows: list[str] = []
    for result in tool_results:
        rows.append(
            f"TOOL {result.get('index')} {result.get('tool')} status:{result.get('status')} "
            f"count:{result.get('component_count') or 0}"
        )
        for card in result.get("components") or []:
            rows.append(
                f"{card.get('alias')} {card.get('label')} "
                f"{card.get('input')}>{card.get('output')} "
                f"fit:{card.get('fit')} does:{_compact_text(card.get('does'), 100)} "
                f"src:{card.get('source')}"
            )
    return _compact_text("\n".join(rows), AIDEVOBSERVER_PLANNER_TOOL_RESULT_CHARS)


def _planner_component_sort_key(component: dict) -> tuple[int, str]:
    name = str((component.get("source_ref") or {}).get("name") or component.get("label") or "")
    ordered_names = {
        AIDEVOBSERVER_API_POLICY_VALIDATE_REQUEST: 10,
        AIDEVOBSERVER_BROWSER_TABLE_FETCH_HTML: 20,
        AIDEVOBSERVER_BROWSER_TABLE_EXTRACT: 30,
        AIDEVOBSERVER_BROWSER_TABLE_WRITE_CSV: 40,
        AIDEVOBSERVER_BROWSER_TABLE_WRITE_PARQUET: 50,
        AIDEVOBSERVER_API_POLICY_FETCH_ACCOUNT: 60,
        AIDEVOBSERVER_API_POLICY_APPLY_DECISION: 70,
        AIDEVOBSERVER_API_POLICY_PERSIST_DECISION: 80,
        AIDEVOBSERVER_API_POLICY_EMIT_RESPONSE: 90,
        AIDEVOBSERVER_CSV_PRIMITIVE_READ_ROWS: 20,
        AIDEVOBSERVER_CSV_PRIMITIVE_VALIDATE: 30,
        AIDEVOBSERVER_CSV_PRIMITIVE_SUMMARIZE: 40,
    }
    return ordered_names.get(name, 999), name


def _fallback_route_from_tool_components(task: str, components: list[dict], why: str) -> dict:
    nodes: list[dict] = []
    ordered = sorted(components, key=_planner_component_sort_key)
    prior_id: str | None = None
    for index, component in enumerate(ordered[:AIDEVOBSERVER_PLANNER_TOOL_RESULT_COMPONENT_LIMIT]):
        source_ref = component.get("source_ref") or {}
        contract = component.get("contract") or {}
        primitive = str(source_ref.get("name") or component.get("label") or f"component_{index + 1}")
        node_id = re.sub(r"[^a-z0-9_]+", "_", primitive.lower()).strip("_") or f"step_{index + 1}"
        if any(node.get("id") == node_id for node in nodes):
            node_id = f"{node_id}_{index + 1}"
        nodes.append({
            "id": node_id,
            "candidate_alias": component.get("planner_alias"),
            "input": contract.get("input") or "unknown",
            "output": contract.get("output") or "unknown",
            "depends_on": [prior_id] if prior_id else [],
            "why": _compact_text((component.get("blackbox") or {}).get("does") if isinstance(component.get("blackbox"), dict) else "", 120),
        })
        prior_id = node_id
    return {
        "v": 1,
        "status": "route" if nodes else "gap",
        "nodes": nodes,
        "plan_delta": {
            "v": 1,
            "p": "pairs",
            "t": 0,
            "b": [[index, index] for index in range(len(nodes))],
            "r": [],
            "g": [] if nodes else [{"s": 0, "need": "route_components", "why": "no_components"}],
        },
        "confidence": 0.62 if nodes else 0.0,
        "why": why,
        "task_digest": _digest({"task": task}),
        "candidate": True,
        "serves_truth": False,
    }


def _invoke_planner_tool_loop(
    *,
    task: str,
    selected_models: list[str],
    model_ids: dict[str, str],
    registry_cwd: str | None,
    enabled: bool,
) -> dict:
    model_key, model_id = _planner_model_choice(selected_models, model_ids)
    base = {
        "stage": "planner_tool_loop",
        "tool_loop": True,
        "model_key": model_key,
        "model": model_id,
        "model_calls": 0,
        "candidate": True,
        "serves_truth": False,
    }
    if not enabled:
        return {**base, "status": "skipped", "reason": "planner_llm_disabled"}

    groups = sorted(_ide_task_capability_groups(task))
    edges = _ide_task_edges(task)
    request_system = (
        "You are the AIDevObserver route planner. "
        "First choose which registry tools to call. Do not write code. "
        "Return JSON only."
    )
    request_user = (
        "Task:\n"
        f"{task}\n\n"
        "Detected capability groups:\n"
        f"{json.dumps(groups)}\n\n"
        "Inferred edge request:\n"
        f"{json.dumps(edges, sort_keys=True)}\n\n"
        "Available tools:\n"
        f"- {AIDEVOBSERVER_PLANNER_TOOL_PREINDEXED}: return known first-party primitive families by groups.\n"
        f"- {AIDEVOBSERVER_PLANNER_TOOL_REGISTRY_SEARCH}: search local/global primitive registry by query and requested edges.\n\n"
        "Return:\n"
        "{\"v\":1,\"tool_requests\":[{\"tool\":\"registry.preindexed\",\"groups\":[\"...\"]},"
        "{\"tool\":\"registry.search\",\"query\":\"...\",\"requested_input\":\"...\",\"requested_output\":\"...\"}]}"
    )
    request_call = _planner_chat_json(
        stage="planner_tool_request",
        task=task,
        selected_models=selected_models,
        model_ids=model_ids,
        system=request_system,
        user=request_user,
        max_tokens=AIDEVOBSERVER_PLANNER_TOOL_REQUEST_MAX_TOKENS,
    )
    if request_call.get("status") not in {"used", "malformed"}:
        return {**base, **request_call, "stage": "planner_tool_loop", "tool_loop": True}

    request_json = request_call.get("json") if isinstance(request_call.get("json"), dict) else {}
    tool_requests = request_json.get("tool_requests") if isinstance(request_json.get("tool_requests"), list) else []
    tool_requests = tool_requests[:AIDEVOBSERVER_PLANNER_TOOL_LOOP_MAX_CALLS]
    components, tool_results = _execute_planner_tool_requests(
        task=task,
        requests=tool_requests,
        registry_cwd=registry_cwd,
    )

    route_system = (
        "You are the AIDevObserver route designer. "
        "Use only component aliases from TOOL_RESULTS. "
        "Choose order and connections. Do not write code. Return JSON only."
    )
    route_user = (
        "Task:\n"
        f"{task}\n\n"
        "TOOL_RESULTS:\n"
        f"{_planner_tool_result_lines(tool_results)}\n\n"
        "Return one JSON object:\n"
        "{\"v\":1,\"status\":\"route|gap\",\"nodes\":[{\"id\":\"short_step\","
        "\"candidate_alias\":\"P0\",\"input\":\"$input...\",\"output\":\"$state...\","
        "\"depends_on\":[\"prior_step\"],\"why\":\"short\"}],"
        "\"plan_delta\":{\"v\":1,\"p\":\"pairs\",\"t\":0,\"b\":[],\"r\":[],\"g\":[]},"
        "\"confidence\":0.0,\"why\":\"short\"}"
    )
    route_call = _planner_chat_json(
        stage="planner_route_design",
        task=task,
        selected_models=selected_models,
        model_ids=model_ids,
        system=route_system,
        user=route_user,
        max_tokens=AIDEVOBSERVER_PLANNER_ROUTE_MAX_TOKENS,
    )
    route_json = route_call.get("json") if isinstance(route_call.get("json"), dict) else {}
    route_fallback = None
    if not route_json and components:
        route_fallback = "deterministic_route_from_tool_results"
        route_json = _fallback_route_from_tool_components(task, components, "planner_route_json_unavailable")
    model_calls = int(request_call.get("model_calls") or 0) + int(route_call.get("model_calls") or 0)
    input_tokens = int(request_call.get("input_tokens") or 0) + int(route_call.get("input_tokens") or 0)
    output_tokens = int(request_call.get("output_tokens") or 0) + int(route_call.get("output_tokens") or 0)
    status = "used" if route_json else str(route_call.get("status") or request_call.get("status") or "malformed")
    return {
        **base,
        "status": status,
        "model_key": route_call.get("model_key") or request_call.get("model_key") or base.get("model_key"),
        "model": route_call.get("model") or request_call.get("model") or base.get("model"),
        "provider": route_call.get("provider") or request_call.get("provider"),
        "model_calls": model_calls,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "tool_calls": tool_requests,
        "tool_request": request_json,
        "tool_results": tool_results,
        "components": components,
        "route": route_json,
        "route_fallback": route_fallback,
        "attempts": (request_call.get("attempts") or []) + (route_call.get("attempts") or []),
        "tool_request_status": request_call.get("status"),
        "tool_request_finish_reason": request_call.get("finish_reason"),
        "route_model_status": route_call.get("status"),
        "route_finish_reason": route_call.get("finish_reason"),
        "plan_delta": route_json.get("plan_delta") or route_json if isinstance(route_json, dict) else None,
        "raw_tool_request": request_call.get("raw_output"),
        "raw_output": route_call.get("raw_output"),
        "candidate": True,
        "serves_truth": False,
    }


def _components_from_planner_result(planner_result: dict, fallback: list[dict]) -> list[dict]:
    if not isinstance(planner_result, dict) or not planner_result.get("components"):
        return fallback
    components = planner_result.get("components") if isinstance(planner_result.get("components"), list) else []
    route = planner_result.get("route") if isinstance(planner_result.get("route"), dict) else {}
    nodes = route.get("nodes") if isinstance(route.get("nodes"), list) else []
    alias_map = {
        str(component.get("planner_alias") or ""): component
        for component in components
        if component.get("planner_alias")
    }
    ordered: list[dict] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        alias = str(node.get("candidate_alias") or node.get("component_alias") or "")
        component = alias_map.get(alias)
        if component:
            ordered.append(component)
    return _dedupe_components(ordered or components)


def _extract_json_object(text: str) -> dict | None:
    raw = str(text or "").strip()
    if not raw:
        return None
    try:
        value = json.loads(raw)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        pass
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end <= start:
        return None
    try:
        value = json.loads(raw[start:end + 1])
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        return None


def _ai_trace(
    *,
    task: str,
    execution_mode: str,
    deterministic_route: bool,
    planner_result: dict,
    selected_components: list[dict],
) -> dict:
    no_op = execution_mode == AIDEVOBSERVER_NOOP_EXECUTION_MODE
    deterministic_execution = execution_mode == "deterministic_template_worker"
    planner_calls = int(planner_result.get("model_calls") or 0)
    codegen_calls = 0
    known_calls = planner_calls + codegen_calls
    return {
        "intent_interpretation": {
            "lane": (
                "not_started"
                if no_op
                else "deterministic_rule_match"
                if deterministic_route
                else "planner_tool_loop"
                if planner_result.get("tool_loop") and planner_result.get("status") == "used"
                else "planner_llm"
                if planner_result.get("status") == "used"
                else "deterministic_heuristic_plus_registry"
            ),
            "model_calls": 0 if deterministic_route or no_op else planner_calls,
            "reason": (
                "input did not look like a build/review task"
                if no_op
                else "exact route matched by task terms and input/output edges"
                if deterministic_route
                else "LLM planner called registry tools and selected a candidate route"
                if planner_result.get("tool_loop") and planner_result.get("status") == "used"
                else "multi-capability composition requires compact planner and/or harness"
                if _ide_task_is_complex_composition(task)
                else "ambiguous task; compact planner may interpret intent"
            ),
        },
        "registry_search": {
            "lane": "deterministic_edge_search",
            "candidate_count": len(selected_components),
            "model_calls": 0,
        },
        "route_planning": {
            **planner_result,
            "lane": (
                "deterministic_template_match"
                if deterministic_route
                else "planner_tool_loop"
                if planner_result.get("tool_loop") and planner_result.get("status") == "used"
                else "compact_planner_llm"
                if planner_result.get("status") == "used"
                else "gap_or_fallback"
            ),
        },
        "compiler": {
            "lane": "deterministic_compiler",
            "accepted": deterministic_execution,
            "model_calls": 0,
        },
        "code_generation": {
            "lane": "none" if deterministic_execution or no_op else "coding_harness_fallback",
            "model_calls": codegen_calls,
            "harness_invoked": False if deterministic_execution or no_op else "fallback_only",
        },
        "known_model_calls": known_calls,
        "coding_harness_model_calls": 0 if deterministic_execution or no_op else "not_started_yet",
        "candidate": True,
        "serves_truth": False,
    }


def _apply_runtime_config(body: dict) -> tuple[int, dict]:
    if not isinstance(body, dict):
        return 400, {"error": "body must be a JSON object", "serves_truth": False}
    provider = str(body.get("model_provider") or _model_provider()).strip()
    if provider not in AIDEVOBSERVER_MODEL_PROVIDERS:
        return 400, {"error": f"model_provider must be one of {list(AIDEVOBSERVER_MODEL_PROVIDERS)}", "serves_truth": False}
    toggles = body.get("toggles") if isinstance(body.get("toggles"), dict) else {}
    enabled_harnesses = body.get("enabled_harnesses")
    sanitized: dict[str, bool] = {}
    for key, value in toggles.items():
        if key in AIDEVOBSERVER_INTELLIGENCE_TOGGLE_ENVS:
            sanitized[key] = bool(value)
    harnesses = _configured_harnesses()
    if isinstance(enabled_harnesses, list):
        harnesses = [
            str(key)
            for key in enabled_harnesses
            if str(key) in AIDEVOBSERVER_HARNESS_DEFAULTS
        ] or harnesses
    with _CONFIG_LOCK:
        _RUNTIME_CONFIG["model_provider"] = provider
        _RUNTIME_CONFIG["enabled_harnesses"] = harnesses
        merged = dict(_RUNTIME_CONFIG.get("toggles") or {})
        merged.update(sanitized)
        _RUNTIME_CONFIG["toggles"] = merged
    os.environ[AIDEVOBSERVER_ENABLED_HARNESSES_ENV] = ",".join(harnesses)
    for key, enabled in sanitized.items():
        _set_flag(AIDEVOBSERVER_INTELLIGENCE_TOGGLE_ENVS[key], enabled)
        if key == "global_primitives":
            set_global_primitives_enabled(enabled)
    return runtime_config()


def runtime_config() -> tuple[int, dict]:
    toggles = _configured_toggles()
    return 200, {
        "service": SERVICE_ID,
        "version": VERSION,
        "model_provider": _model_provider(),
        "model_lanes": _model_lanes(),
        "harnesses": _harness_lanes(),
        "enabled_harnesses": _configured_harnesses(),
        "toggles": toggles,
        "deterministic_workers": _deterministic_worker_catalog(),
        "integration_layers": {
            "mcp": {"enabled": toggles.get("mcp"), "surface": "Claude Code MCP server"},
            "plugins": {"enabled": toggles.get("plugins"), "surface": "VS Code / Cursor / plugin adapters"},
            "live_hook": {"enabled": toggles.get("live_hook"), "surface": "Claude Code PreToolUse hook"},
            "local_registry": {"enabled": toggles.get("local_registry"), "surface": "local helper/source-ref search"},
            "global_primitives": {"enabled": toggles.get("global_primitives"), "surface": "quality-gated global primitive cards"},
        },
        "review_mode": "registry_search_with_model_assist",
        "candidate": True,
        "serves_truth": False,
    }


def ide_run_plan(body: dict) -> tuple[int, dict]:
    """POST /ide/plan — compose the observer context used by a harness run."""

    if not isinstance(body, dict):
        return 400, {"error": "body must be a JSON object", "serves_truth": False}
    task = str(body.get("task") or "").strip()
    if not task:
        return 400, {"error": "provide task", "serves_truth": False}
    models = body.get("models") if isinstance(body.get("models"), list) else [_model_provider()]
    selected_models = [
        str(model)
        for model in models
        if str(model) in {"kimi", "glm"}
    ] or [_model_provider()]
    harnesses = body.get("harnesses") if isinstance(body.get("harnesses"), list) else _configured_harnesses()
    selected_harnesses = [
        str(harness)
        for harness in harnesses
        if str(harness) in AIDEVOBSERVER_HARNESS_DEFAULTS
    ] or _configured_harnesses()
    model_ids = {
        "kimi": os.environ.get(AIDEVOBSERVER_KIMI_MODEL_ENV, AIDEVOBSERVER_KIMI_MODEL_ID).strip() or AIDEVOBSERVER_KIMI_MODEL_ID,
        "glm": os.environ.get(AIDEVOBSERVER_GLM_MODEL_ENV, AIDEVOBSERVER_GLM_MODEL_ID).strip() or AIDEVOBSERVER_GLM_MODEL_ID,
    }
    has_build_intent = _ide_task_has_build_intent(task)
    components = _ide_plan_components(task, body) if has_build_intent else []
    initial_components = list(components)
    selected_components = _annotate_component_selection(_actionable_components(components))
    deterministic_route = has_build_intent and _can_run_deterministic_template(task, {"selected_components": selected_components})
    planner_enabled = (
        has_build_intent
        and not deterministic_route
        and bool(_configured_toggles().get("llm_rerank"))
        and body.get("planner_llm") is not False
    )
    planner_result = (
        {
            "stage": "planner_llm",
            "status": "skipped",
            "reason": "exact_deterministic_route" if deterministic_route else "not_a_build_task",
            "model_calls": 0,
            "candidate": True,
            "serves_truth": False,
        }
        if not planner_enabled
        else _invoke_planner_tool_loop(
            task=task,
            selected_models=selected_models,
            model_ids=model_ids,
            registry_cwd=str(body.get("registry_cwd") or "") or None,
            enabled=True,
        )
    )
    if planner_result.get("status") == "used":
        components = _components_from_planner_result(planner_result, components)
        selected_components = _annotate_component_selection(_actionable_components(components))
    route_context = _annotate_component_selection(
        _route_context_components(_dedupe_components(initial_components + components))
    )
    components = _annotate_component_selection(components)
    context_components = _annotate_component_selection(_dedupe_components(route_context + components))
    harness_task = _observer_wrapped_task(task, context_components, planner_result) if has_build_intent else ""
    planner_materialized_route = (
        has_build_intent
        and not deterministic_route
        and _can_materialize_browser_policy_route(selected_components, planner_result)
    )
    execution_mode = (
        "deterministic_template_worker"
        if deterministic_route or planner_materialized_route
        else AIDEVOBSERVER_NOOP_EXECUTION_MODE
        if not has_build_intent
        else "coding_harness_fallback"
    )
    recipe = _route_recipe(task, selected_components, execution_mode, planner_result)
    trace = _ai_trace(
        task=task,
        execution_mode=execution_mode,
        deterministic_route=deterministic_route,
        planner_result=planner_result,
        selected_components=selected_components,
    )
    if isinstance(recipe, dict):
        recipe["model_calls"] = trace.get("known_model_calls", recipe.get("model_calls"))
        recipe["planner_model_calls"] = int(planner_result.get("model_calls") or 0)
        recipe["planner_status"] = planner_result.get("status")
    runtime_target = _runtime_target_summary(task, execution_mode, recipe)
    if isinstance(recipe, dict):
        recipe["runtime_target"] = runtime_target
    token_savings = _token_savings_summary(task, selected_components, planner_result, execution_mode)
    fallback_strategy = _fallback_strategy(
        execution_mode=execution_mode,
        selected_models=selected_models,
        selected_harnesses=selected_harnesses,
        model_ids=model_ids,
        planner_result=planner_result,
    )
    deterministic_workers = _deterministic_worker_catalog()
    run_graph = _ide_run_graph(task, selected_models, selected_harnesses, context_components, execution_mode, planner_result)
    if execution_mode == "deterministic_template_worker":
        commands = [{
            "harness": "deterministic_template_worker",
            "label": "Deterministic template worker",
            "command": "compile selected primitive route -> materialize workspace files",
        }]
    elif execution_mode == AIDEVOBSERVER_NOOP_EXECUTION_MODE:
        commands = []
    else:
        commands = []
        for harness in selected_harnesses:
            meta = AIDEVOBSERVER_HARNESS_DEFAULTS[harness]
            if harness == "opencode":
                primary = model_ids.get("kimi" if "kimi" in selected_models else "glm", AIDEVOBSERVER_KIMI_MODEL_ID)
                commands.append({
                    "harness": harness,
                    "label": meta["label"],
                    "command": f"{meta['launch']} --model ollama-cloud/{primary} --task <observer-wrapped-task>",
                })
            elif harness == "claude_code":
                commands.append({
                    "harness": harness,
                    "label": meta["label"],
                    "command": meta["launch"],
                })
            else:
                commands.append({
                    "harness": harness,
                    "label": meta["label"],
                    "command": meta["launch"],
                })
    response = {
        "service": SERVICE_ID,
        "plan_id": "ide_plan_" + _digest({
            "task": task,
            "policy": AIDEVOBSERVER_AUTO_REUSE_POLICY_ID,
            "models": selected_models,
            "harnesses": selected_harnesses,
        }),
        "policy_applied": True,
        "policy_id": AIDEVOBSERVER_AUTO_REUSE_POLICY_ID,
        "guidance_applied": True,
        "guidance_id": AIDEVOBSERVER_AUTO_REUSE_POLICY_ID,
        "task_summary": task[:240],
        "user_task": task,
        "harness_task": harness_task,
        "observer_policy": {
            "id": AIDEVOBSERVER_AUTO_REUSE_POLICY_ID,
            "label": AIDEVOBSERVER_AUTO_REUSE_POLICY_LABEL,
            "steps": list(AIDEVOBSERVER_AUTO_REUSE_POLICY_STEPS),
            "automatic": True,
        },
        "observer_guidance": {
            "id": AIDEVOBSERVER_AUTO_REUSE_POLICY_ID,
            "label": AIDEVOBSERVER_AUTO_REUSE_POLICY_LABEL,
            "steps": list(AIDEVOBSERVER_AUTO_REUSE_POLICY_STEPS),
            "automatic": True,
        },
        "models": selected_models,
        "model_ids": model_ids,
        "harnesses": selected_harnesses,
        "commands": commands,
        "execution_mode": execution_mode,
        "runtime_target": runtime_target,
        "token_savings": token_savings,
        "fallback_strategy": fallback_strategy,
        "ai_trace": trace,
        "planner_result": planner_result,
        "recipe": recipe,
        "deterministic_workers": deterministic_workers,
        "deterministic_workers_used": [
            worker
            for worker in deterministic_workers
            if worker["id"] in set(recipe.get("deterministic_workers") or [])
        ],
        "observer_layers": _configured_toggles(),
        "run_graph": run_graph,
        "selected_route_context": route_context,
        "route_context": _route_context_summary(context_components),
        "selected_components": selected_components,
        "next_actions": [
            (
                "The deterministic worker will compile the selected route into workspace files; no coding harness/codegen call is needed."
                if execution_mode == "deterministic_template_worker"
                else "No run was started because the terminal input did not look like a build, review, or implementation task."
                if execution_mode == AIDEVOBSERVER_NOOP_EXECUTION_MODE
                else "The coding harness receives only the compact selected edge summaries needed for missing glue."
            ),
            (
                "Type a concrete task such as build, extract, classify, migrate, validate, scrape, or wire a pipeline."
                if execution_mode == AIDEVOBSERVER_NOOP_EXECUTION_MODE
                else "AIDevObserver searched reusable components by input/output edge and blackbox behavior."
            ),
            "High-confidence reusable routes are selected automatically; there is nothing for the user to click.",
        ],
        "flow": list(AIDEVOBSERVER_AUTO_REUSE_POLICY_FLOW),
        "candidate": True,
        "serves_truth": False,
    }
    provisional_files = _ide_workspace_files(task, response, context_components)
    response["route_quality"] = _route_quality_summary(
        execution_mode=execution_mode,
        selected_components=selected_components,
        planner_result=planner_result,
        recipe=recipe,
        workspace_files=provisional_files,
    )
    response["workspace_files"] = _ide_workspace_files(task, response, context_components)
    return 200, response


def ide_session_save(body: dict) -> tuple[int, dict]:
    if not isinstance(body, dict):
        return 400, {"error": "body must be a JSON object", "serves_truth": False}
    session_id = str(body.get("session_id") or "").strip()
    if session_id and not _safe_id(session_id):
        return 400, {"error": "session_id must be a safe metadata id", "serves_truth": False}
    existing = _read_ide_session(session_id) if session_id else None
    task = str(body.get("task") or (existing or {}).get("task") or "").strip()
    if not task:
        return 400, {"error": "provide task", "serves_truth": False}
    raw_models = body.get("models") if isinstance(body.get("models"), list) else (existing or {}).get("models") or [_model_provider()]
    if not isinstance(raw_models, list):
        raw_models = [_model_provider()]
    models = [
        str(model)
        for model in raw_models
        if str(model) in AIDEVOBSERVER_MODEL_PROVIDERS
    ] or [_model_provider()]
    harnesses = body.get("harnesses") if isinstance(body.get("harnesses"), list) else (existing or {}).get("harnesses") or _configured_harnesses()
    toggles = body.get("toggles") if isinstance(body.get("toggles"), dict) else (existing or {}).get("toggles") or _configured_toggles()
    plan = body.get("plan") if isinstance(body.get("plan"), dict) else (existing or {}).get("plan")
    run = body.get("run") if isinstance(body.get("run"), dict) else (existing or {}).get("run")
    observer_output = (
        body.get("observer_output")
        if isinstance(body.get("observer_output"), list)
        else (existing or {}).get("observer_output") or []
    )
    observer_latest = (
        body.get("observer_latest")
        if isinstance(body.get("observer_latest"), list)
        else (existing or {}).get("observer_latest") or observer_output
    )
    terminal_output = (
        body.get("terminal_output")
        if isinstance(body.get("terminal_output"), list)
        else (existing or {}).get("terminal_output") or []
    )
    workspace_overrides = (
        body.get("workspace_overrides")
        if isinstance(body.get("workspace_overrides"), dict)
        else (existing or {}).get("workspace_overrides") or {}
    )
    record = _write_ide_session({
        "session_id": session_id or None,
        "task": task,
        "models": models,
        "harnesses": [str(harness) for harness in harnesses],
        "toggles": {str(k): bool(v) for k, v in dict(toggles).items()},
        "plan": plan,
        "run": run,
        "observer_latest": [str(line) for line in observer_latest],
        "observer_output": [str(line) for line in observer_output],
        "terminal_output": [str(line) for line in terminal_output],
        "workspace_overrides": {str(k): str(v) for k, v in dict(workspace_overrides).items()},
        "saved_by": "aidevobserver_browser_ide",
    })
    return 200, {"service": SERVICE_ID, "session": record, "serves_truth": False}


def ide_session_load(session_id: str) -> tuple[int, dict]:
    data = _read_ide_session(session_id)
    if not data:
        return 404, {"error": "IDE session not found", "serves_truth": False}
    return 200, {"service": SERVICE_ID, "session": data, "serves_truth": False}


def ide_sessions_list(limit_raw: str | int | None = None) -> tuple[int, dict]:
    try:
        limit = max(1, min(AIDEVOBSERVER_IDE_SESSION_LIST_MAX_LIMIT,
                           int(limit_raw or AIDEVOBSERVER_IDE_SESSION_LIST_DEFAULT_LIMIT)))
    except (TypeError, ValueError):
        limit = AIDEVOBSERVER_IDE_SESSION_LIST_DEFAULT_LIMIT
    root = _ide_session_dir()
    rows: list[dict] = []
    if root.exists():
        for path in sorted(root.glob("ide_*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            data = _read_ide_session(path.stem)
            if not data:
                continue
            rows.append({
                "session_id": data.get("session_id"),
                "title": data.get("title"),
                "updated_at": data.get("updated_at"),
                "created_at": data.get("created_at"),
                "share_url": data.get("share_url"),
                "models": data.get("models") or [],
                "harnesses": data.get("harnesses") or [],
                "candidate": True,
                "serves_truth": False,
            })
            if len(rows) >= limit:
                break
    return 200, {"service": SERVICE_ID, "sessions": rows, "serves_truth": False}


def _registry_port() -> int:
    reg = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    svc = next(s for s in reg["services"] if s["service_id"] == SERVICE_ID)
    return int(svc["port"])


def _route_path(path: str) -> str:
    """Normalize an incoming path to the bare route. The seam forwards the full ``/api/observer/…``
    (strip=""), while a direct caller hits ``/review`` — both resolve to the same handler here."""
    if path == _API_PREFIX or path.startswith(_API_PREFIX + "/"):
        return path[len(_API_PREFIX):] or "/"
    return path


def _coerce_messages(items) -> list[dict]:
    """Tolerate either engine-shaped message dicts or bare strings (a string → a user turn). The
    router reads ``content``/``text`` off dicts, so a non-dict item would crash it — coerce first."""
    out: list[dict] = []
    for m in items or []:
        if isinstance(m, dict):
            out.append(m)
        elif isinstance(m, str) and m.strip():
            out.append({"role": "user", "content": m})
    return out


def _stable_json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(value) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()[:SERVICE_SETTINGS.digest_chars]


def _safe_id(value: str) -> bool:
    return bool(_SAFE_ID.fullmatch(value))


def _ide_session_dir() -> Path:
    configured = os.environ.get(AIDEVOBSERVER_IDE_SESSION_DIR_ENV, AIDEVOBSERVER_IDE_SESSION_DIR_DEFAULT)
    path = Path(configured).expanduser()
    return path if path.is_absolute() else _resource(path)


def _ide_session_path(session_id: str) -> Path:
    return _ide_session_dir() / f"{session_id}.json"


def _new_ide_session_id() -> str:
    return "ide_" + secrets.token_hex(AIDEVOBSERVER_IDE_SESSION_ID_HEX_CHARS // 2)


def _ide_title(task: str) -> str:
    text = " ".join(str(task or "").split())
    if len(text) <= AIDEVOBSERVER_IDE_SESSION_TITLE_CHARS:
        return text or "Untitled AIDevObserver IDE session"
    return text[:AIDEVOBSERVER_IDE_SESSION_TITLE_CHARS - 1].rstrip() + "…"


def _ide_session_url(session_id: str) -> str:
    return f"/ide/{session_id}"


def _read_ide_session(session_id: str) -> dict | None:
    if not _safe_id(session_id):
        return None
    path = _ide_session_path(session_id)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _write_ide_session(record: dict) -> dict:
    _ide_session_dir().mkdir(parents=True, exist_ok=True)
    now = int(time.time())
    session_id = str(record.get("session_id") or _new_ide_session_id())
    prior = _read_ide_session(session_id) or {}
    stored = {
        **prior,
        **record,
        "session_id": session_id,
        "title": _ide_title(str(record.get("task") or prior.get("task") or "")),
        "updated_at": now,
        "created_at": int(prior.get("created_at") or record.get("created_at") or now),
        "share_url": _ide_session_url(session_id),
        "candidate": True,
        "serves_truth": False,
    }
    _ide_session_path(session_id).write_text(json.dumps(stored, indent=2, sort_keys=True), encoding="utf-8")
    return stored


def _review_session_id(body: dict, messages: list[dict]) -> str:
    """Stable metadata id for review/outcome memory. Never returns raw transcript text or local paths."""
    explicit = body.get("session_id")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()[:SERVICE_SETTINGS.session_id_max_chars]
    if body.get("transcript_path"):
        return "transcript_" + hashlib.sha256(str(body["transcript_path"]).encode("utf-8")).hexdigest()[:SERVICE_SETTINGS.digest_chars]
    return "review_" + _digest(messages)


def _intervention_id(session_id: str, finding: dict) -> str:
    """Stable id for a finding inside one session/review, based on governed metadata only."""
    material = {
        "session_id": session_id,
        "type": finding.get("type"),
        "message_index": finding.get("message_index"),
        "dedup_id": finding.get("dedup_id"),
        "message": finding.get("message"),
        "source_ref": finding.get("source_ref"),
    }
    return "iv_" + _digest(material)


def _stamp_review_ids(rep: dict, session_id: str) -> dict:
    report = []
    for finding in rep.get("report", []):
        stamped = {**finding}
        stamped["session_id"] = session_id
        stamped["intervention_id"] = _intervention_id(session_id, stamped)
        report.append(stamped)
    return {**rep, "session_id": session_id, "report": report}


def _messages_from_body(body: dict) -> tuple[list[dict], str | None]:
    """Resolve a /review or /live body into the engine's message list. Accepts {messages:[...]} or
    {transcript_path:"…"} (read via capture.from_transcript). Returns (messages, error_or_None)."""
    if not isinstance(body, dict):
        return [], "body must be a JSON object"
    if body.get("transcript_path"):
        try:
            return from_transcript(str(body["transcript_path"])), None
        except FileNotFoundError:
            return [], f"transcript not found: {body['transcript_path']}"
        except OSError as exc:
            return [], f"cannot read transcript: {exc}"
    msgs = body.get("messages")
    if not isinstance(msgs, list):
        return [], "provide messages:[...] or transcript_path:'…'"
    coerced = _coerce_messages(msgs)
    if not coerced:
        return [], "messages is empty — nothing to review"
    return coerced, None


def _local_session_discovery_enabled() -> bool:
    """Return whether zero-install Claude Code / Codex session discovery is enabled."""

    return _flag_enabled(
        AIDEVOBSERVER_INTELLIGENCE_TOGGLE_ENVS["local_sessions"],
        AIDEVOBSERVER_INTELLIGENCE_TOGGLE_DEFAULTS.get("local_sessions", False),
    )


def _local_registry_enabled() -> bool:
    """Local source search is opt-in, just like session discovery."""
    return local_registry_enabled()


# --- the three operations (pure functions → the proof calls them directly, no socket) ---------------
def sessions_list(cwd: str | None) -> tuple[int, dict]:
    """GET /sessions — discovered Claude Code sessions for a cwd, newest first. Tolerates none → []."""
    if not _local_session_discovery_enabled():
        return 200, {
            "service": SERVICE_ID,
            "sessions": [],
            "local_session_discovery_enabled": False,
            "reason": "disabled_for_public_demo",
            "serves_truth": False,
        }
    try:
        found = discover_sessions(cwd) if cwd else discover_sessions()
    except OSError:             # filesystem discovery must never fail the surface — honest empty list
        found = []              # (narrow: a NON-filesystem bug should surface as a 500, not hide as empty)
    return 200, {
        "service": SERVICE_ID,
        "sessions": found or [],
        "local_session_discovery_enabled": True,
        "serves_truth": False,
    }


def review_report(body: dict) -> tuple[int, dict]:
    """POST /review — the governed post-session report (review_session over the full taxonomy)."""
    messages, err = _messages_from_body(body)
    if err:
        return 400, {"error": err, "serves_truth": False}
    session_id = _review_session_id(body, messages)
    rep = enrich_report_with_local_registry(
        review_session(messages),
        root_value=body.get("registry_cwd") or body.get("cwd"),
        requested_input=body.get("requested_input") or body.get("input_contract"),
        requested_output=body.get("requested_output") or body.get("output_contract"),
    )
    rep = _stamp_review_ids(rep, session_id)
    return 200, {
        **rep,
        "service": SERVICE_ID,
        "observer_intelligence": runtime_config()[1],
        "serves_truth": False,
    }


def live_report(body: dict) -> tuple[int, dict]:
    """POST /live — the live spotter (route_session) → what WOULD interrupt + the summary."""
    messages, err = _messages_from_body(body)
    if err:
        return 400, {"error": err, "serves_truth": False}
    mode = str(body.get("mode") or DEFAULT_LIVE_MODE)
    if mode not in MODES:
        return 400, {"error": f"mode must be one of {sorted(MODES)}", "serves_truth": False}
    r = route_session(messages, mode=mode)
    return 200, {"service": SERVICE_ID, "mode": r["mode"], "surfaced": r["surfaced"],
                 "summary": r["summary"], "savings": r.get("savings", {}),
                 "governed": r["governed"], "serves_truth": False}


def agentic_report(body: dict) -> tuple[int, dict]:
    """POST /agentic — supervise an AUTONOMOUS agent loop. {steps:[{action,ok?,error?,cost?,output?}], goal?,
    budget?:{max_steps?,max_cost?}, monitor?:bool, mode?}. monitor=true -> intra-run monitor_step (alerts +
    recommend_halt); else post-run review_agentic_run. Read-only; never halts a process (recommend only)."""
    if not isinstance(body, dict):
        return 400, {"error": "body must be a JSON object", "serves_truth": False}
    steps = body.get("steps")
    if not isinstance(steps, list) or not steps:
        return 400, {"error": "provide steps:[{action, ok?, error?, cost?, output?}, ...]", "serves_truth": False}
    goal = str(body.get("goal") or "")
    budget = body.get("budget") if isinstance(body.get("budget"), dict) else {}
    if body.get("monitor"):
        out = monitor_step(steps, goal=goal, budget=budget, mode=str(body.get("mode") or "advisory"))
    else:
        out = review_agentic_run(steps, goal=goal, budget=budget)
    return 200, {**out, "service": SERVICE_ID, "serves_truth": False}


def outcome_report(body: dict) -> tuple[int, dict]:
    """POST /outcome — append-only human triage memory. Stores ids/outcome only; never transcript text."""
    if not isinstance(body, dict):
        return 400, {"error": "body must be a JSON object", "serves_truth": False}
    session_id = str(body.get("session_id") or "").strip()
    intervention_id = str(body.get("intervention_id") or "").strip()
    outcome = str(body.get("outcome") or "").strip()
    if not session_id:
        return 400, {"error": "provide session_id", "serves_truth": False}
    if not _safe_id(session_id):
        return 400, {"error": "session_id must be a safe metadata id", "serves_truth": False}
    if not intervention_id:
        return 400, {"error": "provide intervention_id", "serves_truth": False}
    if not _safe_id(intervention_id):
        return 400, {"error": "intervention_id must be a safe metadata id", "serves_truth": False}
    try:
        finding_type = str(body.get("type") or body.get("finding_type") or "").strip()
        if not _safe_id(finding_type):
            finding_type = ""
        record = session_store.outcome_record(
            session_id,
            intervention_id,
            outcome,
            source_ref_keys=source_ref_keys_from_value(body.get("source_ref")),
            finding_type=finding_type or None,
        )
    except ValueError as exc:
        return 400, {"error": str(exc), "serves_truth": False}
    session_store.append(record)
    return 200, {
        "service": SERVICE_ID,
        "record": "outcome",
        "session_id": session_id,
        "intervention_id": intervention_id,
        "outcome": outcome,
        "source_ref_keys": record.get("source_ref_keys", []),
        "stored": "outcome_metadata_only",
        "candidate": True,
        "serves_truth": False,
    }


def outcomes_list(session_id: str | None) -> tuple[int, dict]:
    """GET /outcomes?session_id=... — latest-wins outcome memory for one session."""
    sid = str(session_id or "").strip()
    if not sid:
        return 400, {"error": "provide session_id", "serves_truth": False}
    if not _safe_id(sid):
        return 400, {"error": "session_id must be a safe metadata id", "serves_truth": False}
    records = session_store.load(sid)
    outcomes = {
        intervention_id: record.get("outcome")
        for intervention_id, record in session_store.resolve_outcomes(records).items()
        if record.get("outcome")
    }
    # Metadata-only outcome writes may arrive before/without intervention records.
    # Preserve latest-wins for that launch-alpha path too.
    for record in records:
        if record.get("record") == "outcome" and record.get("intervention_id"):
            outcomes[record["intervention_id"]] = record.get("outcome")
    return 200, {
        "service": SERVICE_ID,
        "session_id": sid,
        "outcomes": outcomes,
        "stored": "outcome_metadata_only",
        "serves_truth": False,
    }


def registry_search(
    query: str | None,
    cwd: str | None = None,
    limit: str | int | None = None,
    *,
    requested_input: str | dict | None = None,
    requested_output: str | dict | None = None,
    visibility_scope: str | None = None,
) -> tuple[int, dict]:
    """GET /registry/search — candidate-only local repo source-ref search.

    Disabled by default for public demos. When enabled, it indexes the explicit
    cwd or process cwd, returns repo-relative source refs, and never includes
    the raw root path in the response.
    """
    status, payload = registry_search_response(
        query,
        cwd,
        limit,
        requested_input=requested_input,
        requested_output=requested_output,
        visibility_scope=visibility_scope,
    )
    return status, {"service": SERVICE_ID, **payload}


# --- HTTP surface -----------------------------------------------------------------------------------
class _Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict, headers: dict[str, str] | None = None) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")   # local preview / same-origin seam
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-AIDR-Request-Id")
        self.send_header("Cache-Control", "no-store")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = min(int(self.headers.get("Content-Length") or 0), MAX_BODY_BYTES)
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        return json.loads(raw or "{}")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = _route_path(parsed.path)
        if path in ("/health", "/healthz", "/readyz"):
            return self._send(200, {"ok": True, "service": "observer", "engine": "teleon.observer",
                                    "serves_truth": False})
        if path == "/version":
            return self._send(200, {"service": SERVICE_ID, "version": VERSION, "serves_truth": False})
        if path == "/config":
            return self._send(*runtime_config())
        if path == "/ide/sessions":
            params = parse_qs(parsed.query)
            return self._send(*ide_sessions_list((params.get("limit") or [None])[0]))
        if path.startswith("/ide/session/"):
            return self._send(*ide_session_load(path.rsplit("/", 1)[-1]))
        if path.startswith("/ide/run/"):
            return self._send(*_ide_run_status(path.rsplit("/", 1)[-1]))
        if path == "/sessions":
            cwd = (parse_qs(parsed.query).get("cwd") or [None])[0]
            return self._send(*sessions_list(cwd))
        if path == "/outcomes":
            session_id = (parse_qs(parsed.query).get("session_id") or [None])[0]
            return self._send(*outcomes_list(session_id))
        if path == "/registry/search":
            params = parse_qs(parsed.query)
            return self._send(*registry_search(
                (params.get("q") or [None])[0],
                (params.get("cwd") or [None])[0],
                (params.get("limit") or [None])[0],
                requested_input=(params.get("input") or params.get("input_contract") or [None])[0],
                requested_output=(params.get("output") or params.get("output_contract") or [None])[0],
                visibility_scope=(params.get("visibility_scope") or params.get("visibility") or [None])[0],
            ))
        return self._send(404, {"error": "unknown path", "serves_truth": False})

    def do_POST(self) -> None:  # noqa: N802
        path = _route_path(urlparse(self.path).path)
        ops = {
            "/review": review_report,
            "/live": live_report,
            "/agentic": agentic_report,
            "/outcome": outcome_report,
            "/config": _apply_runtime_config,
            "/ide/plan": ide_run_plan,
            "/ide/run": ide_run_start,
            "/ide/session": ide_session_save,
        }
        if path not in ops:
            return self._send(404, {"error": "unknown path", "serves_truth": False})
        try:
            body = self._read_json()
        except json.JSONDecodeError:
            return self._send(400, {"error": "invalid JSON", "serves_truth": False})
        try:
            result = ops[path](body)
        except Exception as exc:  # a handler op must never crash the seam — clean 500, never an unhandled traceback
            return self._send(500, {"error": "handler failed", "detail": str(exc), "serves_truth": False})
        return self._send(*result)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send(200, {"ok": True})

    def log_message(self, *args) -> None:  # the engine output is the record; keep the console quiet
        pass


def start_service(port: int = 0):
    """Bind a ThreadingHTTPServer on 127.0.0.1 (ephemeral port when 0) and serve in a daemon thread.
    Returns (server, thread, bound_port) — the same shape as events_local_service.start_service."""
    server = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
    thread = threading.Thread(target=server.serve_forever, name=SERVICE_ID, daemon=True)
    thread.start()
    return server, thread, server.server_address[1]


def serve(port: int | None = None) -> None:
    port = port or _registry_port()
    bind_host = os.environ.get("OH_BIND_HOST", "127.0.0.1")   # 0.0.0.0 only in container deploys
    server = ThreadingHTTPServer((bind_host, port), _Handler)
    pid_file = _resource(".agent") / "local-services" / f"{SERVICE_ID}.pid"
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(os.getpid()), encoding="utf-8")
    print(f"{SERVICE_ID} on http://{bind_host}:{port} — AIDevObserver session review "
          f"(review/live/sessions over the observer engine; serves_truth=false, read-only) "
          f"(stop by exact pid {os.getpid()})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        pid_file.unlink(missing_ok=True)


# --- offline proof of the wire (the cross-cutting seam/registry proof is check_observer_local_service) ---
def _self_test() -> int:
    """In-process + loopback-HTTP proof: review yields a governed report (serves_truth=false,
    candidate findings) over a synthetic session AND a synthetic transcript file; live yields
    surfaced+summary; sessions tolerates none; a bad body 400s; the wire keeps serves_truth=false
    and CORS open. Ephemeral port, temp files, stdlib-only. Exit 0/1."""
    import tempfile
    import urllib.error
    import urllib.request

    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # synthetic session (no real PII): a grounded reinvention + a destructive-command footgun
    messages = [
        {"role": "user", "content": "let me write my own pdf parser from scratch"},
        {"role": "assistant", "content": "ok — first: git push --force origin main"},
    ]

    # in-process: review
    st, rep = review_report({"messages": messages})
    findings = rep.get("report", [])
    ck("review → 200 governed report (serves_truth=false)", st == 200 and rep["serves_truth"] is False)
    ck("review surfaces candidate findings", len(findings) >= 1
       and all(f.get("candidate") and f.get("serves_truth") is False for f in findings))
    ck("review stamps stable session/intervention ids", bool(rep.get("session_id"))
       and all(f.get("session_id") == rep["session_id"] and f.get("intervention_id") for f in findings))

    # in-process: append-only outcome memory, metadata only
    synthetic_sid = "selftest_outcome_" + _digest({"case": "observer_local_service"})
    synthetic_iv = "iv_" + _digest({"case": "observer_local_service", "finding": 1})
    try:
        st_o, out_o = outcome_report({"session_id": synthetic_sid, "intervention_id": synthetic_iv, "outcome": "dismissed"})
        ck("outcome → 200 metadata-only append",
           st_o == 200 and out_o.get("stored") == "outcome_metadata_only" and out_o.get("serves_truth") is False)
        st_o2, _ = outcome_report({"session_id": synthetic_sid, "intervention_id": synthetic_iv, "outcome": "reused"})
        st_l, out_l = outcomes_list(synthetic_sid)
        ck("outcomes latest-wins folds append-only records",
           st_o2 == 200 and st_l == 200 and out_l.get("outcomes", {}).get(synthetic_iv) == "reused")
        st_bad_outcome, _ = outcome_report({"session_id": synthetic_sid, "intervention_id": synthetic_iv, "outcome": "truth"})
        ck("invalid outcome rejected", st_bad_outcome == 400)
        st_bad_sid, _ = outcome_report({"session_id": "../bad", "intervention_id": synthetic_iv, "outcome": "reused"})
        ck("path-like outcome session id rejected", st_bad_sid == 400)
    finally:
        session_store._path(synthetic_sid).unlink(missing_ok=True)

    # in-process: review over a synthetic TRANSCRIPT file (capture.from_transcript path)
    tmp = Path(tempfile.mkdtemp(prefix="observer-svc-selftest-"))
    prev_ide_session_dir = os.environ.get(AIDEVOBSERVER_IDE_SESSION_DIR_ENV)
    os.environ[AIDEVOBSERVER_IDE_SESSION_DIR_ENV] = str(tmp / "ide-sessions")
    try:
        tpath = tmp / "session.jsonl"
        tpath.write_text("\n".join(json.dumps(
            {"type": "user", "message": {"role": "user", "content": c}}) for c in
            ["let me build a custom retry with exponential backoff", "and my own oauth login"]) + "\n",
            encoding="utf-8")
        st_t, rep_t = review_report({"transcript_path": str(tpath)})
        ck("review over a transcript_path → 200 governed report",
           st_t == 200 and rep_t["serves_truth"] is False and len(rep_t.get("report", [])) >= 1)
        st_miss, _ = review_report({"transcript_path": str(tmp / "nope.jsonl")})
        ck("a missing transcript → honest 400 (not a crash)", st_miss == 400)

        # in-process: live + sessions tolerance + bad body
        st_l, live = live_report({"messages": messages, "mode": "advisory"})
        ck("live → 200 with surfaced + summary (serves_truth=false)",
           st_l == 200 and "surfaced" in live and "summary" in live and live["serves_truth"] is False)
        st_s, sess = sessions_list("/no/such/project/here")
        ck("sessions tolerates none → 200 with []", st_s == 200 and sess["sessions"] == []
           and sess["serves_truth"] is False)
        st_bad, _ = review_report({})
        ck("a body with neither messages nor transcript → 400", st_bad == 400)

        st_reg_off, reg_off = registry_search("parse csv", str(tmp))
        ck("local registry search is enabled by default for low-config developer use",
           st_reg_off == 200 and reg_off.get("local_registry_enabled") is True)
        st_enrich_off, enrich_off = review_report({
            "messages": [{"role": "user", "content": "I'll write a CSV parser from scratch"}],
            "registry_cwd": str(tmp),
        })
        ck("review local-registry enrichment is enabled by default",
           st_enrich_off == 200 and (enrich_off.get("local_registry") or {}).get("enabled") is True)
        repo_dir = tmp / "repo"
        repo_dir.mkdir()
        (repo_dir / "helpers.py").write_text(
            "MAX_ROWS = 100\n\n"
            "def read_rows(path: str) -> list[dict[str, str]]:\n"
            "    \"\"\"Read CSV rows with header handling.\"\"\"\n"
            "    return []\n",
            encoding="utf-8",
        )
        prev_registry = os.environ.get(_LOCAL_REGISTRY_ENV)
        os.environ[_LOCAL_REGISTRY_ENV] = "1"
        try:
            st_reg, reg = registry_search("creating parse_csv helper", str(repo_dir))
            reg_blob = json.dumps(reg, sort_keys=True)
            ck("local registry search finds repo-relative helper source refs when opted in",
               st_reg == 200 and "read_rows" in reg_blob and str(repo_dir) not in reg_blob
               and reg.get("serves_truth") is False)
            st_enriched, enriched = review_report({
                "messages": [
                    {"role": "user", "content": "add a CSV import to the importer"},
                    {"role": "assistant", "content": "I'll write a CSV parser. Creating parse_csv() in importer.py"},
                ],
                "registry_cwd": str(repo_dir),
            })
            enriched_blob = json.dumps(enriched, sort_keys=True)
            ck("review attaches local registry source refs when opted in",
               st_enriched == 200 and "local_repo" in enriched_blob and "read_rows" in enriched_blob
               and str(repo_dir) not in enriched_blob and enriched.get("serves_truth") is False)
        finally:
            if prev_registry is None:
                os.environ.pop(_LOCAL_REGISTRY_ENV, None)
            else:
                os.environ[_LOCAL_REGISTRY_ENV] = prev_registry

        # in-process: agentic-loop supervision (post-run review + intra-run monitor + empty-steps guard)
        thrash = [{"action": "pytest", "ok": False, "error": "ImportError"} for _ in range(3)]
        st_ar, arep = agentic_report({"steps": thrash, "goal": "run tests"})
        ck("agentic review → 200 governed report with a verdict",
           st_ar == 200 and arep["serves_truth"] is False and "verdict" in arep.get("summary", {}))
        st_am, amon = agentic_report({"steps": [{"action": "x"} for _ in range(6)],
                                      "budget": {"max_steps": 3}, "monitor": True, "mode": "active"})
        ck("agentic monitor → recommend_halt on a runaway (active mode)",
           st_am == 200 and amon.get("recommend_halt") is True)
        st_ae, _ = agentic_report({"steps": []})
        ck("agentic with no steps → 400", st_ae == 400)

        planner_tool_task = (
            "Build an API endpoint that validates a JSON request, uses Playwright to process site tables, "
            "fetches account state, applies a policy decision, persists it, and returns a JSON response."
        )
        planner_components, planner_tool_results = _execute_planner_tool_requests(
            task=planner_tool_task,
            requests=[{
                "tool": AIDEVOBSERVER_PLANNER_TOOL_PREINDEXED,
                "groups": ["browser_table_export", "api_boundary", "account_state", "policy_decision", "persistence", "response_emit"],
            }],
            registry_cwd=str(tmp),
        )
        planner_labels = {str(component.get("label") or "") for component in planner_components}
        planner_tool_blob = json.dumps(planner_tool_results, sort_keys=True)
        ck("planner registry tools return compact edge cards for composite routes",
           any("browser.fetch_page_html" in label for label in planner_labels)
           and any("api.policy.validate" in label for label in planner_labels)
           and "components" in planner_tool_blob
           and "def " not in planner_tool_blob)

        # over the WIRE: ephemeral loopback server, both bare and seam-prefixed paths
        server, thread, port = start_service(port=0)
        try:
            def call(method: str, path: str, body: dict | None = None):
                data = json.dumps(body).encode() if body is not None else None
                req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data,
                                             method=method, headers={"Content-Type": "application/json"})
                try:
                    with urllib.request.urlopen(req, timeout=SELF_TEST_HTTP_TIMEOUT_SECONDS) as r:
                        return r.status, json.loads(r.read() or b"{}"), dict(r.headers)
                except urllib.error.HTTPError as e:
                    return e.code, json.loads(e.read() or b"{}"), dict(e.headers)

            hs, hb, hh = call("GET", "/health")
            ck("wire GET /health → {ok, service:'observer'} + CORS open",
               hs == 200 and hb.get("service") == "observer"
               and hh.get("Access-Control-Allow-Origin") == "*")
            rs, rb, _ = call("POST", "/review", {"messages": messages})
            ck("wire POST /review → governed report (bare path)",
               rs == 200 and rb["serves_truth"] is False and len(rb.get("report", [])) >= 1)
            ps, pb, _ = call("POST", "/api/observer/review", {"messages": messages})
            ck("wire POST /api/observer/review → same report (seam-prefixed path)",
               ps == 200 and pb.get("summary", {}).get("findings") == rb.get("summary", {}).get("findings"))
            cs, cb, _ = call("GET", "/api/observer/config")
            ck("wire GET /api/observer/config → model lanes + toggles",
               cs == 200 and {lane.get("key") for lane in cb.get("model_lanes", [])} == {"deterministic", "kimi", "glm"}
               and isinstance(cb.get("toggles"), dict)
               and any(worker.get("id") == "route_recipe_compiler" for worker in cb.get("deterministic_workers", []))
               and cb.get("serves_truth") is False)
            ps_cfg, pb_cfg, _ = call("POST", "/api/observer/config", {
                "model_provider": "glm",
                "toggles": {"local_registry": False, "local_sessions": False, "llm_rerank": True},
            })
            ck("wire POST /api/observer/config updates model lane and toggles",
               ps_cfg == 200 and pb_cfg.get("model_provider") == "glm"
               and pb_cfg.get("toggles", {}).get("local_registry") is False
               and pb_cfg.get("toggles", {}).get("llm_rerank") is True)
            ps_cfg2, pb_cfg2, _ = call("POST", "/api/observer/config", {
                "model_provider": "kimi",
                "toggles": {"local_registry": True, "local_sessions": False, "llm_rerank": True},
            })
            ck("wire POST /api/observer/config can re-enable local registry for IDE routing",
               ps_cfg2 == 200 and pb_cfg2.get("model_provider") == "kimi"
               and pb_cfg2.get("toggles", {}).get("local_registry") is True)
            ip_s, ip_b, _ = call("POST", "/api/observer/ide/plan", {
                "task": "Build a CSV import without reinventing a parser.",
                "models": ["kimi", "glm"],
                "harnesses": ["opencode", "claude_code"],
            })
            ck("wire POST /api/observer/ide/plan selects deterministic worker for exact primitive routes",
               ip_s == 200 and ip_b.get("models") == ["kimi", "glm"]
               and ip_b.get("execution_mode") == "deterministic_template_worker"
               and (ip_b.get("ai_trace") or {}).get("known_model_calls") == 0
               and ((ip_b.get("ai_trace") or {}).get("route_planning") or {}).get("reason") == "exact_deterministic_route"
               and (ip_b.get("commands") or [{}])[0].get("harness") == "deterministic_template_worker"
               and (ip_b.get("recipe") or {}).get("template") == AIDEVOBSERVER_CSV_RECIPE_TEMPLATE_ID
               and len((ip_b.get("recipe") or {}).get("nodes") or []) == 3
               and ip_b.get("serves_truth") is False)
            ck("wire POST /api/observer/ide/plan keeps first route packet compact",
               ip_s == 200
               and len(str(ip_b.get("harness_task") or "")) <= AIDEVOBSERVER_ROUTE_PACKET_MAX_PROMPT_CHARS
               and str(ip_b.get("harness_task") or "").startswith("TASK:"))
            amb_s, amb_b, _ = call("POST", "/api/observer/ide/plan", {
                "task": "Build an API endpoint that validates requests and persists decisions.",
                "models": ["kimi"],
                "harnesses": ["opencode"],
                "registry_cwd": str(tmp),
                "planner_llm": False,
            })
            amb_trace = amb_b.get("ai_trace") or {}
            ck("wire POST /api/observer/ide/plan exposes planner/fallback lane trace",
               amb_s == 200
               and amb_b.get("execution_mode") == "coding_harness_fallback"
               and (amb_trace.get("route_planning") or {}).get("status") == "skipped"
               and (amb_trace.get("code_generation") or {}).get("lane") == "coding_harness_fallback"
               and amb_trace.get("known_model_calls") == 0)
            complex_task = (
                "Build a backend API service that accepts a JSON request with a company domain and account id, "
                "validates the request, uses Playwright to visit the company website, extracts visible tables "
                "and metadata, normalizes the result into CSV and Parquet artifacts, fetches the account state, "
                "applies an enrichment policy decision, persists the decision with an idempotency key, and returns "
                "a JSON API response with artifact paths, policy status, and audit metadata."
            )
            cx_s, cx_b, _ = call("POST", "/api/observer/ide/plan", {
                "task": complex_task,
                "models": ["kimi"],
                "harnesses": ["opencode"],
                "registry_cwd": str(tmp),
                "planner_llm": False,
            })
            cx_components = cx_b.get("selected_components") or []
            cx_labels = {str(component.get("label") or "") for component in cx_components}
            ck("wire POST /api/observer/ide/plan compiles known composite primitive route",
               cx_s == 200
               and cx_b.get("execution_mode") == "deterministic_template_worker"
               and (cx_b.get("recipe") or {}).get("template") == AIDEVOBSERVER_BROWSER_POLICY_API_RECIPE_TEMPLATE_ID
               and any("browser.fetch_page_html" in label for label in cx_labels)
               and any("api.policy.validate" in label for label in cx_labels)
               and (cx_b.get("route_quality") or {}).get("deterministic") is True)
            bp_s, bp_b, _ = call("POST", "/api/observer/ide/plan", {
                "task": (
                    "Build auth login and session management with password reset, MFA, API routes, "
                    "database persistence, and audit logging."
                ),
                "models": ["kimi"],
                "harnesses": ["opencode"],
                "visibility_scope": AIDEVOBSERVER_VISIBILITY_SCOPE_PUBLIC,
                "planner_llm": False,
            })
            bp_route_context = bp_b.get("route_context") or {}
            bp_route_records = bp_b.get("selected_route_context") or []
            bp_blob = json.dumps(bp_route_records, sort_keys=True)
            ck("wire POST /api/observer/ide/plan selects route-level blueprints for broad tasks",
               bp_s == 200
               and bp_route_context.get("blueprints", 0) >= 1
               and any((item.get("contract") or {}).get("output") == "PipelineRecipe" for item in bp_route_records)
               and "artifact.capability_template_route" in bp_blob
               and "catalog/knowledge-packs/data/aidevobserver-microsurface-atlas/microsurfaces.jsonl" in bp_blob
               and bp_b.get("serves_truth") is False)
            no_s, no_b, _ = call("POST", "/api/observer/ide/run", {
                "task": "Hello",
                "models": ["kimi"],
                "harnesses": ["opencode"],
            })
            no_run = no_b.get("run") or {}
            no_plan = no_b.get("plan") or {}
            ck("wire POST /api/observer/ide/run keeps greetings idle",
               no_s == 200
               and no_run.get("status") == "not_started"
               and no_run.get("execution_mode") == AIDEVOBSERVER_NOOP_EXECUTION_MODE
               and not no_run.get("run_id")
               and no_run.get("harness") == "none"
               and no_plan.get("commands") == []
               and len(no_plan.get("workspace_files") or []) == 1)
            ir_s, ir_b, _ = call("POST", "/api/observer/ide/run", {
                "task": "Build a CSV import flow for uploaded vendor files.",
                "models": ["kimi"],
                "harnesses": ["opencode"],
                "dry_run": True,
            })
            ir_run = ir_b.get("run") or {}
            ir_id = str(ir_run.get("run_id") or "")
            ck("wire POST /api/observer/ide/run compiles deterministic primitive route first",
               ir_s == 200 and ir_id.startswith("run_")
               and ir_run.get("harness") == "deterministic_template_worker"
               and ir_run.get("execution_mode") == "deterministic_template_worker"
               and ir_run.get("model") == "none"
               and ir_run.get("returncode") == 0
               and len((ir_run.get("recipe") or {}).get("nodes") or []) == 3
               and all(proof.get("status") == "pass" for proof in ir_run.get("proofs", []))
               and ir_run.get("dry_run") is True
               and ir_b.get("serves_truth") is False)
            ir_proof_ids = {str(proof.get("id") or "") for proof in ir_run.get("proofs", [])}
            ir_file_paths = {str(file.get("path") or "") for file in (ir_b.get("plan") or {}).get("workspace_files", [])}
            ir_mutators = {
                mutation
                for component in (ir_b.get("plan") or {}).get("selected_components", [])
                for mutation in _mutation_ids(component.get("mutations") or [])
            }
            ck("wire POST /api/observer/ide/run emits adapter artifacts and proofs",
               "edge_adapter_plan.json" in ir_file_paths
               and AIDEVOBSERVER_WORKSPACE_BUILD_MANIFEST_PATH in ir_file_paths
               and "edge_adapter_plan_shape" in ir_proof_ids
               and "edge_adapter_plan_truth_boundary" in ir_proof_ids
               and "build_manifest_adapter_summary" in ir_proof_ids
               and AIDEVOBSERVER_MUTATOR_SCHEMA_VALIDATOR_INSERTER in ir_mutators
               and AIDEVOBSERVER_MUTATOR_ARTIFACT_REFERENCE in ir_mutators)
            run_poll_s, run_poll_b = 0, {}
            if ir_id:
                for _ in range(30):
                    run_poll_s, run_poll_b, _ = call("GET", f"/api/observer/ide/run/{ir_id}")
                    if (run_poll_b.get("run") or {}).get("status") != "running":
                        break
                    time.sleep(0.1)
            run_poll = run_poll_b.get("run") or {}
            ck("wire GET /api/observer/ide/run/<id> reports deterministic completion and log tail",
               run_poll_s == 200
               and run_poll.get("status") == "succeeded"
               and run_poll.get("returncode") == 0
               and "model_calls: 0" in str(run_poll.get("log_tail") or "")
               and "coding_harness_invoked: false" in str(run_poll.get("log_tail") or "")
               and "recipe_nodes:" in str(run_poll.get("log_tail") or "")
               and "proofs:" in str(run_poll.get("log_tail") or ""))
            ir_f_s, ir_f_b, _ = call("POST", "/api/observer/ide/run", {
                "task": "Build a CSV import flow for uploaded vendor files.",
                "models": ["kimi"],
                "harnesses": ["opencode"],
                "dry_run": True,
                "force_harness": True,
            })
            ir_f_run = ir_f_b.get("run") or {}
            ir_f_id = str(ir_f_run.get("run_id") or "")
            ck("wire POST /api/observer/ide/run supports forced harness fallback",
               ir_f_s == 200 and ir_f_id.startswith("run_")
               and ir_f_run.get("harness") == "opencode"
               and ir_f_run.get("execution_mode") == "coding_harness_fallback"
               and ir_f_run.get("dry_run") is True)
            fallback_poll_s, fallback_poll_b = 0, {}
            if ir_f_id:
                for _ in range(30):
                    fallback_poll_s, fallback_poll_b, _ = call("GET", f"/api/observer/ide/run/{ir_f_id}")
                    if (fallback_poll_b.get("run") or {}).get("status") != "running":
                        break
                    time.sleep(0.1)
            fallback_poll = fallback_poll_b.get("run") or {}
            ck("wire GET /api/observer/ide/run/<id> reports forced fallback dry-run output",
               fallback_poll_s == 200
               and fallback_poll.get("status") == "succeeded"
               and fallback_poll.get("returncode") == 0
               and '"dry_run": true' in str(fallback_poll.get("log_tail") or ""))
            save_s, save_b, _ = call("POST", "/api/observer/ide/session", {
                "task": "Build a CSV import without reinventing a parser.",
                "models": ["kimi", "glm"],
                "harnesses": ["opencode", "claude_code"],
                "plan": ip_b,
            })
            saved_session = (save_b.get("session") or {})
            load_s, load_b, _ = call("GET", f"/api/observer/ide/session/{saved_session.get('session_id', '')}")
            list_s, list_b, _ = call("GET", "/api/observer/ide/sessions?limit=3")
            ck("wire POST/GET /api/observer/ide/session creates a reopenable share URL",
               save_s == 200 and load_s == 200
               and str(saved_session.get("share_url") or "").startswith("/ide/")
               and (load_b.get("session") or {}).get("session_id") == saved_session.get("session_id"))
            ck("wire GET /api/observer/ide/sessions lists saved IDE sessions",
               list_s == 200 and any(s.get("session_id") == saved_session.get("session_id") for s in list_b.get("sessions", [])))
            wire_sid = "wire_outcome_" + _digest({"port": port})
            wire_iv = "iv_" + _digest({"port": port})
            os_, ob, _ = call("POST", "/outcome", {"session_id": wire_sid, "intervention_id": wire_iv, "outcome": "accepted"})
            gs, gb, _ = call("GET", f"/outcomes?session_id={wire_sid}")
            ck("wire POST /outcome + GET /outcomes → metadata memory",
               os_ == 200 and ob.get("stored") == "outcome_metadata_only" and gs == 200
               and gb.get("outcomes", {}).get(wire_iv) == "accepted")
            session_store._path(wire_sid).unlink(missing_ok=True)
            call("POST", "/api/observer/config", {
                "model_provider": "kimi",
                "toggles": {"local_registry": False, "local_sessions": False, "llm_rerank": True},
            })
            reg_off_s, reg_off_b, _ = call("GET", "/registry/search?q=parse+csv")
            allowed_registry_kinds = {
                "edge_foundry_candidate_registry",
                "global_surfaceable_primitive_registry",
                "operational_primitive_registry",
            }
            ck("wire GET /registry/search keeps local repo disabled unless opted in",
               reg_off_s == 200 and reg_off_b.get("local_registry_enabled") is False
               and all((hit.get("source_kind") in allowed_registry_kinds
                        or (hit.get("reuse_card") or {}).get("source_kind") in allowed_registry_kinds)
                       for hit in reg_off_b.get("hits", [])))
            reg_public_s, reg_public_b, _ = call("GET", "/registry/search?q=notebook+train+model+pandas&visibility=public")
            reg_local_s, reg_local_b, _ = call("GET", "/registry/search?q=notebook+train+model+pandas&visibility=local")

            def edge_visibility_hits(payload: dict) -> list[str]:
                out: list[str] = []
                for hit in payload.get("hits", []):
                    card = hit.get("reuse_card") if isinstance(hit.get("reuse_card"), dict) else hit
                    if card.get("source_kind") == EDGE_FOUNDRY_SOURCE_KIND:
                        out.append(str(card.get("surface_visibility") or ""))
                return out

            public_visibilities = edge_visibility_hits(reg_public_b)
            local_visibilities = edge_visibility_hits(reg_local_b)
            ck("wire GET /registry/search public visibility excludes private edge-foundry cards",
               reg_public_s == 200
               and reg_public_b.get("visibility_scope") == AIDEVOBSERVER_VISIBILITY_SCOPE_PUBLIC
               and AIDEVOBSERVER_VISIBILITY_PRIVATE_INTERNAL_ONLY not in public_visibilities)
            ck("wire GET /registry/search local visibility can include private edge-foundry cards",
               reg_local_s == 200
               and reg_local_b.get("visibility_scope") == AIDEVOBSERVER_VISIBILITY_SCOPE_LOCAL
               and AIDEVOBSERVER_VISIBILITY_PRIVATE_INTERNAL_ONLY in local_visibilities)
            ls, lb, _ = call("POST", "/live", {"messages": messages})
            ck("wire POST /live → surfaced + summary", ls == 200 and "surfaced" in lb and "summary" in lb)
            ss, sb, _ = call("GET", "/sessions?cwd=/no/such/project")
            ck("wire GET /sessions tolerates none → []", ss == 200 and sb["sessions"] == [])
        finally:
            server.shutdown()
            thread.join(timeout=5)
    finally:
        import shutil
        if prev_ide_session_dir is None:
            os.environ.pop(AIDEVOBSERVER_IDE_SESSION_DIR_ENV, None)
        else:
            os.environ[AIDEVOBSERVER_IDE_SESSION_DIR_ENV] = prev_ide_session_dir
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n" + ("PASS — observer_local_service: a thin HTTP front-end over the observer engine "
                  "(review_session / route_session / from_transcript / discover_sessions) — review "
                  "returns a governed report (serves_truth=false, candidate findings) over both inline "
                  "messages and a synthetic transcript, live returns surfaced+summary, sessions "
                  "tolerates none, bare and /api/observer-prefixed paths both resolve; CORS open, "
                  "read-only, stdlib-only."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AIDevObserver session-review local service.")
    ap.add_argument("--serve", action="store_true", help="run the HTTP service")
    ap.add_argument("--port", type=int, default=None, help="override the registry port")
    ap.add_argument("--self-test", action="store_true", help="run the offline proof")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.serve:
        serve(args.port)
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
