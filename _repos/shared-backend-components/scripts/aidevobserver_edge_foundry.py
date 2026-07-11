#!/usr/bin/env python3
"""Deterministic edge foundry for source-backed primitive candidates.

This scanner turns real source into compact primitive cards:

source tree -> functions/classes -> input/output edges -> mutator hints -> JSONL cards

It is intentionally deterministic and candidate-only. It does not promote
records, call models, fetch the network, or claim served truth.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import ast
import hashlib
import json
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Iterable

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts._config import (  # noqa: E402
    AIDEVOBSERVER_DETERMINISTIC_MUTATOR_IDS,
    AIDEVOBSERVER_MUTATOR_API_ENDPOINT_WRAPPER,
    AIDEVOBSERVER_MUTATOR_ARTIFACT_MATERIALIZE,
    AIDEVOBSERVER_MUTATOR_ARTIFACT_REFERENCE,
    AIDEVOBSERVER_MUTATOR_BATCH_CHUNKER,
    AIDEVOBSERVER_MUTATOR_CACHE_WRAPPER,
    AIDEVOBSERVER_MUTATOR_CLI_WRAPPER,
    AIDEVOBSERVER_MUTATOR_CLOUD_FUNCTION_WRAPPER,
    AIDEVOBSERVER_MUTATOR_DATE_TIME_NORMALIZE,
    AIDEVOBSERVER_MUTATOR_FANOUT_FANIN,
    AIDEVOBSERVER_MUTATOR_FIELD_PROJECT,
    AIDEVOBSERVER_MUTATOR_FIELD_RENAME,
    AIDEVOBSERVER_MUTATOR_IDEMPOTENCY_WRAPPER,
    AIDEVOBSERVER_MUTATOR_INPUT_ENVELOPE_WRAPPER,
    AIDEVOBSERVER_MUTATOR_K8S_CRONJOB_WRAPPER,
    AIDEVOBSERVER_MUTATOR_K8S_DEPLOYMENT_WRAPPER,
    AIDEVOBSERVER_MUTATOR_K8S_JOB_WRAPPER,
    AIDEVOBSERVER_MUTATOR_MAP_SEQUENCE,
    AIDEVOBSERVER_MUTATOR_OUTPUT_WRAPPER,
    AIDEVOBSERVER_MUTATOR_PAGINATION_EXPANDER,
    AIDEVOBSERVER_MUTATOR_PROVENANCE_WRAPPER,
    AIDEVOBSERVER_MUTATOR_REDACTION_WRAPPER,
    AIDEVOBSERVER_MUTATOR_RETRY_WRAPPER,
    AIDEVOBSERVER_MUTATOR_SCHEMA_VALIDATOR_INSERTER,
    AIDEVOBSERVER_MUTATOR_SECRET_REF_WRAPPER,
    AIDEVOBSERVER_MUTATOR_TYPE_CAST,
    AIDEVOBSERVER_RUNTIME_TARGET_CLOUD_FUNCTION,
    AIDEVOBSERVER_RUNTIME_TARGET_CONTAINER,
    AIDEVOBSERVER_RUNTIME_TARGET_K8S_CRONJOB,
    AIDEVOBSERVER_RUNTIME_TARGET_K8S_DEPLOYMENT,
    AIDEVOBSERVER_RUNTIME_TARGET_K8S_JOB,
    AIDEVOBSERVER_RUNTIME_TARGET_LOCAL,
    AIDEVOBSERVER_VISIBILITY_PRIVATE_INTERNAL_ONLY,
    AIDEVOBSERVER_VISIBILITY_PUBLIC_DEMO_SAFE,
)

DEFAULT_OUT = _resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / "primitive_edge_cards.jsonl"
DEFAULT_MANIFEST = _resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / "manifest.json"
DEFAULT_SUMMARY = _resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / "summary.md"
# UNBOUNDED by default (owner directive 2026-07-05: no silent scale caps — a default cap once truncated a
# monorepo sweep to 50k of 84k+ records with no warning). Bounded runs are OPT-IN via --max-files/--max-records.
DEFAULT_MAX_FILES = None
DEFAULT_MAX_RECORDS = None


def _cap_or_unbounded(cap: "int | None") -> float:
    """None = unbounded (inf). A cap is an explicit, opt-in choice — never a silent default."""
    return float("inf") if cap is None else float(cap)
DEFAULT_MAX_STRUCTURED_FILE_BYTES = 2 * 1024 * 1024
DEFAULT_MAX_STRUCTURED_ROWS_PER_FILE = 64
PRIVATE_NAME_PREFIX = "_"
PY_SUFFIX = ".py"
JS_SUFFIXES = (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")
NOTEBOOK_SUFFIXES = (".ipynb",)
STRUCTURED_SUFFIXES = (".json", ".jsonl", ".yaml", ".yml", ".tf", ".sql", *NOTEBOOK_SUFFIXES)
DOC_SUFFIXES = (".md", ".mdx", ".rst")
SHELL_SUFFIXES = (".sh", ".bash", ".zsh")
MAKEFILE_NAMES = {"makefile", "gnumakefile", "justfile", "taskfile.yml", "taskfile.yaml"}
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options", "trace"}
HTTP_READ_METHODS = {"get", "head", "options"}
ARTIFACT_KIND_CAPABILITY_TEMPLATE_ROUTE = "capability_template_route"
ARTIFACT_KIND_CAPABILITY_SLOT = "capability_slot"
EDGE_DEVELOPER_INTENT_WITH_CANDIDATES = "DeveloperIntent+CandidatePrimitiveSet"
EDGE_PIPELINE_RECIPE = "PipelineRecipe"
DEFAULT_EXCLUDE_PARTS = {
    ".agent",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "_reference",
    "artifacts",
    "coverage",
    "data",
    "demo-data",
    "dist",
    "media",
    "node_modules",
    "site",
    "vendor",
}

_WORD_RE = re.compile(r"[a-z0-9]+")
_JS_FUNCTION_RE = re.compile(
    r"(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(([^)]*)\)"
    r"|(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>"
    r"|(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?([A-Za-z_$][\w$]*)\s*=>",
    re.MULTILINE,
)
_JS_TEST_CASE_RE = re.compile(
    r"\b(?:test|it)\s*\(\s*['\"]([^'\"]{1,160})['\"]",
    re.MULTILINE,
)
_FENCED_CODE_RE = re.compile(
    r"```([A-Za-z0-9_+.-]*)[^\n]*\n(.*?)\n```",
    re.DOTALL,
)
_MAKE_TARGET_RE = re.compile(r"^([A-Za-z0-9_.-][A-Za-z0-9_.-]*):(?:\s|$)", re.MULTILINE)
_JUST_TARGET_RE = re.compile(r"^([A-Za-z0-9_.-][A-Za-z0-9_.-]*)(?:\s+[^:\n]*)?:\s*$", re.MULTILINE)
_SHELL_FUNC_RE = re.compile(r"^(?:function\s+)?([A-Za-z_][A-Za-z0-9_-]*)\s*(?:\(\))?\s*\{", re.MULTILINE)
_SCRIPT_LINE_RE = re.compile(r"^\s*(python3?|node|npm|pnpm|yarn|uv|pip|pytest|ruff|mypy|docker|kubectl|helm|terraform|make|just|curl|wget|gh|git)\b(.*)$", re.MULTILINE)
_YAML_KEY_RE = re.compile(r"^\s*([A-Za-z0-9_.-]+)\s*:\s*(.*?)\s*$", re.MULTILINE)
_EFFECT_CALLS = {
    "open": "fs.read_write",
    "urlopen": "net.read",
    "Request": "net.read",
    "Popen": "subprocess",
    "run": "subprocess",
    "check_call": "subprocess",
    "check_output": "subprocess",
}
_WRITE_METHODS = {"write", "write_text", "write_bytes", "mkdir", "unlink", "rename", "replace"}
_READ_METHODS = {"read", "read_text", "read_bytes", "glob", "rglob", "iterdir"}
_DOMAIN_RULES: dict[str, tuple[str, ...]] = {
    "software_engineering": (
        "test", "pytest", "lint", "compile", "refactor", "migration", "git", "diff", "patch",
        "proof", "contract", "schema", "package", "import", "module", "build",
    ),
    "app_building_frontend": (
        "react", "jsx", "tsx", "component", "page", "route", "form", "button", "modal", "css",
        "layout", "dashboard", "ui", "view", "screen",
    ),
    "backend_api": (
        "api", "request", "response", "http", "server", "endpoint", "webhook", "fastapi",
        "handler", "route", "json",
    ),
    "data_engineering": (
        "csv", "parquet", "sql", "table", "schema", "ingest", "extract", "load", "warehouse",
        "dataset", "catalog", "pipeline", "etl",
    ),
    "data_science_ml": (
        "model", "feature", "train", "eval", "score", "regression", "classifier", "embedding",
        "vector", "metric", "benchmark", "prediction",
    ),
    "browser_automation": (
        "browser", "playwright", "scrape", "crawl", "html", "dom", "page", "render", "fetch",
    ),
    "devops_cloud_k8s": (
        "docker", "k8s", "kubernetes", "deploy", "cloud", "function", "lambda", "job",
        "cron", "runtime", "container", "manifest",
    ),
    "security_governance": (
        "secret", "auth", "policy", "redact", "sandbox", "permission", "governance",
        "privacy", "token", "approval",
    ),
    "workflow_automation": (
        "workflow", "dag", "queue", "worker", "orchestr", "schedule", "task", "n8n",
        "trigger",
    ),
    "llm_agent_tools": (
        "llm", "model", "prompt", "agent", "tool", "mcp", "planner", "rerank", "candidate",
        "token", "context",
    ),
    "document_extraction": (
        "pdf", "ocr", "document", "invoice", "contract", "resume", "extract", "span",
    ),
    "observability_replay": (
        "log", "ledger", "trace", "metric", "receipt", "event", "replay", "monitor",
    ),
}


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha(value: Any, *, n: int = 20) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()[:n]


def _slug(value: str) -> str:
    return ".".join(_WORD_RE.findall(str(value).lower())) or "primitive"


def _repo_rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path)


def _source_visibility(path: Path) -> str:
    parts = set(path.parts)
    if "_reference" in parts or "repo_reference" in parts or ".agent" in parts:
        return AIDEVOBSERVER_VISIBILITY_PRIVATE_INTERNAL_ONLY
    return AIDEVOBSERVER_VISIBILITY_PUBLIC_DEMO_SAFE


def _domains_for_text(text: str) -> list[str]:
    words = set(_WORD_RE.findall(text.lower()))
    domains = [
        domain
        for domain, rules in _DOMAIN_RULES.items()
        if words & set(rules)
    ]
    return sorted(domains) or ["general_software"]


def _quality_score(
    *,
    doc: str,
    input_edge: str,
    output_edge: str,
    domains: list[str],
    effects: list[str],
    source_family: str,
) -> int:
    """Deterministic ranking hint for source-backed candidate cards.

    This is not a trust score and never promotes a record. It only helps the
    search layer prefer useful, well-described edges over anonymous helpers.
    """

    score = 30
    if doc:
        score += 18
    if input_edge not in {"Any", "JsArg", "JsArgs"}:
        score += 10
    if output_edge not in {"Any", "JsValue"}:
        score += 10
    if domains and domains != ["general_software"]:
        score += 12
    if any(domain in domains for domain in {
        "app_building_frontend",
        "backend_api",
        "data_engineering",
        "data_science_ml",
        "devops_cloud_k8s",
        "workflow_automation",
    }):
        score += 8
    if effects:
        score += 4
    if source_family == "javascript_typescript_source" and not doc:
        score -= 8
    return max(0, min(score, 100))


def _source_family(path: Path) -> str:
    rel = _repo_rel(path).lower()
    suffix = path.suffix.lower()
    name = path.name.lower()
    if suffix == ".py":
        return "python_source"
    if suffix in JS_SUFFIXES:
        return "javascript_typescript_source"
    if name == "dockerfile" or rel.endswith("/dockerfile"):
        return "container_manifest"
    if ".github/workflows/" in rel or rel.startswith(".github/workflows/"):
        return "ci_workflow"
    if "openapi" in name or "swagger" in name:
        return "openapi_spec"
    if "asyncapi" in name:
        return "asyncapi_spec"
    if name == "package.json":
        return "package_manifest"
    if name.endswith(".schema.json") or "/schemas/" in rel or "/code-templates/" in rel and name in {"input.schema.json", "output.schema.json"}:
        return "json_schema"
    if "/catalog/" in rel and suffix in {".yaml", ".yml"}:
        return "catalog_component_yaml"
    if suffix in {".yaml", ".yml"} and any(token in rel for token in ("k8s", "kubernetes", "deploy/", "deployment", "cronjob", "job")):
        return "k8s_manifest"
    if suffix == ".tf":
        return "terraform_manifest"
    if suffix == ".sql":
        return "sql_source"
    if suffix == ".jsonl":
        return "jsonl_data_source"
    if suffix in NOTEBOOK_SUFFIXES:
        return "notebook_source"
    if suffix == ".json" and ("n8n" in name or "workflow" in name):
        return "workflow_json"
    if suffix in DOC_SUFFIXES:
        return "documentation_executable_snippet"
    if suffix in SHELL_SUFFIXES:
        return "shell_script"
    if name in MAKEFILE_NAMES:
        return "command_taskfile"
    if suffix in {".json", ".yaml", ".yml"}:
        return "structured_config"
    return "source"


def _annotation(node: ast.AST | None) -> str:
    if node is None:
        return "Any"
    try:
        return ast.unparse(node).replace("typing.", "")
    except Exception:
        return "Any"


def _returns_dict_literal(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for node in ast.walk(fn):
        if isinstance(node, ast.Return) and isinstance(node.value, ast.Dict):
            return True
    return False


def _return_edge(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    ann = _annotation(fn.returns)
    if ann != "Any":
        return ann
    if _returns_dict_literal(fn):
        return "dict[str,object]"
    return "Any"


def _input_edge(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    args: list[str] = []
    positional = list(fn.args.posonlyargs) + list(fn.args.args)
    for arg in positional:
        if arg.arg in {"self", "cls"}:
            continue
        args.append(_annotation(arg.annotation))
    for arg in fn.args.kwonlyargs:
        args.append(f"{arg.arg}:{_annotation(arg.annotation)}")
    if fn.args.vararg:
        args.append(f"*{_annotation(fn.args.vararg.annotation)}")
    if fn.args.kwarg:
        args.append(f"**{_annotation(fn.args.kwarg.annotation)}")
    if not args:
        return "None"
    return args[0] if len(args) == 1 else "+".join(args)


def _doc_summary(node: ast.AST) -> str:
    doc = ast.get_docstring(node) or ""
    line = " ".join(doc.strip().split())
    if not line:
        return ""
    for sep in (". ", "\n"):
        if sep in line:
            line = line.split(sep, 1)[0]
            break
    return line[:220]


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _effects(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    effects: set[str] = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            name = _call_name(node.func)
            if name in _EFFECT_CALLS:
                effects.add(_EFFECT_CALLS[name])
            if name in _WRITE_METHODS:
                effects.add("fs.write")
            if name in _READ_METHODS:
                effects.add("fs.read")
    return sorted(effects)


def _is_test_path(path: Path) -> bool:
    lowered_parts = {part.lower() for part in path.parts}
    name = path.name.lower()
    return (
        "tests" in lowered_parts
        or "__tests__" in lowered_parts
        or name.startswith("test_")
        or name.endswith("_test.py")
        or ".test." in name
        or ".spec." in name
    )


def _python_proof_kind(path: Path, fn_name: str) -> str:
    if fn_name in {"_self_test", "self_test"}:
        return "self_test"
    if fn_name.startswith("test_") or _is_test_path(path):
        return "pytest_test"
    return ""


def _runtime_targets(effects: list[str], input_edge: str, output_edge: str) -> list[str]:
    targets = {AIDEVOBSERVER_RUNTIME_TARGET_LOCAL}
    edge_text = f"{input_edge} {output_edge}".lower()
    if any(effect in {"net.read", "subprocess", "container.build", "k8s.apply"} for effect in effects):
        targets.add(AIDEVOBSERVER_RUNTIME_TARGET_CONTAINER)
    if any(effect == "cloud.deploy" for effect in effects):
        targets.add(AIDEVOBSERVER_RUNTIME_TARGET_CLOUD_FUNCTION)
    if "dict" in edge_text and not any(effect in {"subprocess", "container.build", "k8s.apply"} for effect in effects):
        targets.add(AIDEVOBSERVER_RUNTIME_TARGET_CLOUD_FUNCTION)
    if "httprequest" in edge_text or "httpresponse" in edge_text:
        targets.add(AIDEVOBSERVER_RUNTIME_TARGET_CLOUD_FUNCTION)
    if "kubernetes" in edge_text or "k8s" in edge_text or "k8s.apply" in effects:
        targets.add(AIDEVOBSERVER_RUNTIME_TARGET_K8S_JOB)
        targets.add(AIDEVOBSERVER_RUNTIME_TARGET_K8S_DEPLOYMENT)
    if "cron" in edge_text or "schedule" in edge_text:
        targets.add(AIDEVOBSERVER_RUNTIME_TARGET_K8S_CRONJOB)
    return sorted(targets)


def _mutator_options(input_edge: str, output_edge: str, effects: list[str]) -> list[dict[str, Any]]:
    options: list[dict[str, Any]] = []
    edge_text = f"{input_edge} {output_edge}".lower()

    def add(
        short_code: str,
        reason: str,
        proof: list[str],
        *,
        target_input: str | None = None,
        target_output: str | None = None,
        effect_delta: str = "preserve",
        preconditions: list[str] | None = None,
        runtime_targets: list[str] | None = None,
    ) -> None:
        if short_code not in AIDEVOBSERVER_DETERMINISTIC_MUTATOR_IDS:
            return
        options.append({
            "mutator": short_code,
            "mutator_agent_id": f"mut:deterministic:{short_code}@1",
            "reason": reason,
            "input_edge_before": input_edge,
            "output_edge_before": output_edge,
            "target_edge_template": {
                "input": target_input or input_edge,
                "output": target_output or output_edge,
                "mutation": short_code,
            },
            "effect_delta": effect_delta,
            "preconditions": preconditions or [],
            "proof_obligations": proof,
            "runtime_targets": runtime_targets or [],
            "candidate": True,
            "serves_truth": False,
        })

    if not input_edge.startswith("list[") and not output_edge.startswith("list["):
        add(
            AIDEVOBSERVER_MUTATOR_MAP_SEQUENCE,
            "scalar edge can be lifted to list edge",
            ["singleton_equivalence", "order_preserved", "error_mapping_preserved"],
            target_input=f"list[{input_edge}]",
            target_output=f"list[{output_edge}]",
            preconditions=["primitive_is_itemwise", "side_effects_absent_or_idempotent"],
        )
    if "+" in input_edge:
        add(
            AIDEVOBSERVER_MUTATOR_INPUT_ENVELOPE_WRAPPER,
            "multi-input edge can be wrapped into an explicit request envelope",
            ["envelope_fields_declared", "payload_preserved"],
            target_input=f"Envelope[{input_edge}]",
            preconditions=["field_names_declared"],
        )
    if "dict" in input_edge or "dict" in output_edge:
        add(
            AIDEVOBSERVER_MUTATOR_FIELD_RENAME,
            "record-shaped edge can accept explicit field aliases",
            ["field_mapping_unambiguous"],
            preconditions=["source_and_target_field_names_declared"],
        )
        add(
            AIDEVOBSERVER_MUTATOR_FIELD_PROJECT,
            "record-shaped edge can project safe subsets",
            ["projected_fields_declared", "no_required_field_dropped"],
            preconditions=["required_fields_known"],
        )
        add(
            AIDEVOBSERVER_MUTATOR_SCHEMA_VALIDATOR_INSERTER,
            "record-shaped edge can be guarded by deterministic schema validation",
            ["schema_contract_declared", "invalid_payload_blocks_execution"],
            target_output=f"Validated[{output_edge}]",
            effect_delta="add_validation_gate",
            preconditions=["schema_available"],
        )
    if any(token in edge_text for token in ("str", "int", "float", "bool", "path")):
        add(
            AIDEVOBSERVER_MUTATOR_TYPE_CAST,
            "common scalar/path edge can be deterministically cast from compatible serialized input",
            ["cast_rules_declared", "cast_failure_is_typed"],
            preconditions=["source_type_declared", "target_type_declared"],
        )
    if any(token in edge_text for token in ("date", "time", "datetime", "timestamp")):
        add(
            AIDEVOBSERVER_MUTATOR_DATE_TIME_NORMALIZE,
            "date/time-like edge can normalize format and timezone deterministically",
            ["timezone_policy_declared", "invalid_date_is_typed"],
            preconditions=["input_format_declared"],
        )
    if "Path" in input_edge or "Path" in output_edge or "bytes" in output_edge.lower():
        add(
            AIDEVOBSERVER_MUTATOR_ARTIFACT_REFERENCE,
            "large/file-shaped edge can pass ArtifactRef instead of inline data",
            ["artifact_digest_stable", "artifact_ref_resolves"],
            target_input=input_edge.replace("Path", "ArtifactRef"),
            target_output=output_edge.replace("Path", "ArtifactRef"),
            effect_delta="artifact_ref",
        )
        add(
            AIDEVOBSERVER_MUTATOR_ARTIFACT_MATERIALIZE,
            "artifact-shaped edge can be materialized to a local runtime path",
            ["materialized_digest_matches_artifact"],
            target_input=input_edge.replace("ArtifactRef", "Path"),
            target_output=output_edge.replace("ArtifactRef", "Path"),
            effect_delta="fs.read_write",
        )
    if "fs.write" in effects:
        add(
            AIDEVOBSERVER_MUTATOR_IDEMPOTENCY_WRAPPER,
            "write effect should be protected by idempotency key",
            ["duplicate_run_same_receipt", "idempotency_key_digest_logged"],
            target_input=f"{input_edge}+IdempotencyKey",
            preconditions=["idempotency_key_available"],
        )
    if "net.read" in effects:
        add(
            AIDEVOBSERVER_MUTATOR_CACHE_WRAPPER,
            "network read can use TTL/content cache",
            ["cache_key_no_secret", "ttl_policy_declared"],
            preconditions=["cache_key_fields_declared"],
        )
        add(
            AIDEVOBSERVER_MUTATOR_RETRY_WRAPPER,
            "network read can use bounded retry",
            ["retry_bound_declared", "retry_errors_typed"],
            preconditions=["retry_policy_declared"],
        )
        add(
            AIDEVOBSERVER_MUTATOR_PAGINATION_EXPANDER,
            "paginated network read can expand pages into a sequence output",
            ["page_order_preserved", "pagination_stop_condition_declared"],
            target_output=f"list[{output_edge}]",
            preconditions=["pagination_cursor_or_next_link_available"],
        )
    if input_edge.startswith("list[") or output_edge.startswith("list["):
        add(
            AIDEVOBSERVER_MUTATOR_BATCH_CHUNKER,
            "sequence-shaped edge can be split into bounded batches",
            ["batch_bound_declared", "order_preserved"],
            target_input=f"Batch[{input_edge}]",
            target_output=f"Batch[{output_edge}]",
            preconditions=["batch_size_declared"],
        )
        add(
            AIDEVOBSERVER_MUTATOR_FANOUT_FANIN,
            "sequence-shaped edge can fan out item work and fan in ordered results",
            ["fanout_bound_declared", "fanin_order_preserved"],
            preconditions=["parallelism_bound_declared"],
        )
    if any(token in edge_text for token in ("secret", "token", "password", "apikey", "api_key", "credential")):
        add(
            AIDEVOBSERVER_MUTATOR_SECRET_REF_WRAPPER,
            "secret-like edge can pass SecretRef instead of raw secret value",
            ["secret_value_never_logged", "secret_ref_resolves_at_runtime"],
            target_input=input_edge.replace("str", "SecretRef"),
            effect_delta="secret_ref",
            preconditions=["secret_ref_provider_available"],
        )
        add(
            AIDEVOBSERVER_MUTATOR_REDACTION_WRAPPER,
            "sensitive edge can redact logs and ledger events",
            ["secret_values_redacted", "canary_not_exposed"],
            effect_delta="redact_observability",
        )
    if any(effect in effects for effect in ("net.read", "fs.read_write", "fs.write")) or "artifact" in edge_text:
        add(
            AIDEVOBSERVER_MUTATOR_PROVENANCE_WRAPPER,
            "effectful or artifact edge can attach provenance metadata",
            ["provenance_payload_preserved", "source_ref_attached"],
            target_output=f"Provenanced[{output_edge}]",
            effect_delta="add_metadata",
        )
    if "httprequest" in edge_text or "httpresponse" in edge_text or ("dict" in edge_text and not effects):
        add(
            AIDEVOBSERVER_MUTATOR_API_ENDPOINT_WRAPPER,
            "request/response-shaped edge can be exposed as an API endpoint",
            ["request_schema_validated", "response_schema_validated"],
            target_input=f"HttpRequest[{input_edge}]",
            target_output=f"HttpResponse[{output_edge}]",
            effect_delta="api_boundary",
        )
        add(
            AIDEVOBSERVER_MUTATOR_CLOUD_FUNCTION_WRAPPER,
            "request/response-shaped edge can be emitted as a cloud-function handler",
            ["handler_contract_declared", "cold_start_inputs_bounded"],
            target_input=f"CloudFunctionRequest[{input_edge}]",
            target_output=f"CloudFunctionResponse[{output_edge}]",
            effect_delta="runtime_wrapper",
            runtime_targets=[AIDEVOBSERVER_RUNTIME_TARGET_CLOUD_FUNCTION],
        )
    if any(effect in effects for effect in ("subprocess", "container.build")) or "command" in edge_text:
        add(
            AIDEVOBSERVER_MUTATOR_CLI_WRAPPER,
            "command-shaped edge can be exposed as a CLI entry point",
            ["argv_schema_declared", "exit_codes_typed"],
            target_input=f"CommandArgs[{input_edge}]",
            target_output=f"CommandRunReceipt[{output_edge}]",
            effect_delta="cli_boundary",
        )
    if "kubernetes" in edge_text or "k8s" in edge_text or "k8s.apply" in effects:
        add(
            AIDEVOBSERVER_MUTATOR_K8S_JOB_WRAPPER,
            "container/cloud edge can be emitted as a Kubernetes Job",
            ["job_manifest_valid", "restart_policy_declared"],
            target_input=f"KubernetesJobSpec[{input_edge}]",
            target_output=f"KubernetesJobReceipt[{output_edge}]",
            effect_delta="k8s_runtime_wrapper",
            runtime_targets=[AIDEVOBSERVER_RUNTIME_TARGET_K8S_JOB],
        )
        add(
            AIDEVOBSERVER_MUTATOR_K8S_DEPLOYMENT_WRAPPER,
            "service-shaped edge can be emitted as a Kubernetes Deployment and Service",
            ["deployment_manifest_valid", "readiness_probe_declared"],
            target_input=f"KubernetesDeploymentSpec[{input_edge}]",
            target_output=f"KubernetesServiceReceipt[{output_edge}]",
            effect_delta="k8s_runtime_wrapper",
            runtime_targets=[AIDEVOBSERVER_RUNTIME_TARGET_K8S_DEPLOYMENT],
        )
        if "cron" in edge_text or "schedule" in edge_text:
            add(
                AIDEVOBSERVER_MUTATOR_K8S_CRONJOB_WRAPPER,
                "scheduled edge can be emitted as a Kubernetes CronJob",
                ["cron_schedule_declared", "concurrency_policy_declared"],
                target_input=f"KubernetesCronJobSpec[{input_edge}]",
                target_output=f"KubernetesCronJobReceipt[{output_edge}]",
                effect_delta="k8s_runtime_wrapper",
                runtime_targets=[AIDEVOBSERVER_RUNTIME_TARGET_K8S_CRONJOB],
            )
    add(
        AIDEVOBSERVER_MUTATOR_OUTPUT_WRAPPER,
        "output can be wrapped with provenance metadata",
        ["payload_preserved"],
        target_output=f"Wrapped[{output_edge}]",
        effect_delta="add_metadata",
    )
    return options


def _record_for_function(path: Path, root: Path, fn: ast.FunctionDef | ast.AsyncFunctionDef, source: str) -> dict[str, Any] | None:
    proof_kind = _python_proof_kind(path, fn.name)
    if fn.name.startswith(PRIVATE_NAME_PREFIX) and not ast.get_docstring(fn) and not proof_kind:
        return None
    if proof_kind == "self_test":
        input_edge = "RepoCheckout+ProofConfig"
        output_edge = "ProofRunReceipt"
        effects = sorted(set(_effects(fn)) | {"subprocess"})
    elif proof_kind == "pytest_test":
        input_edge = "ProjectUnderTest+TestFixture"
        output_edge = "TestProofReceipt"
        effects = sorted(set(_effects(fn)) | {"subprocess"})
    else:
        input_edge = _input_edge(fn)
        output_edge = _return_edge(fn)
        effects = _effects(fn)
    rel = _repo_rel(path)
    line = int(getattr(fn, "lineno", 1))
    module_slug = _slug(rel[:-len(PY_SUFFIX)].replace("/", "."))
    slug = f"{module_slug}.{_slug(fn.name)}"
    doc = _doc_summary(fn)
    proof_terms = "pytest test proof regression behavior self-test" if proof_kind else ""
    domain_text = f"{slug} {input_edge} {output_edge} {doc} {rel} {proof_terms}"
    domains = _domains_for_text(domain_text)
    source_family = _source_family(path)
    kind = "py.fn"
    readiness = "R3_contract_known"
    if proof_kind == "self_test":
        kind = "py.proof_fn"
        readiness = "R2_proof_candidate"
    elif proof_kind == "pytest_test":
        kind = "py.test_fn"
        readiness = "R2_test_candidate"
    return {
        "primitive_id": "prim:" + _sha({"path": rel, "name": fn.name, "line": line}),
        "slug": slug,
        "title": fn.name,
        "kind": kind,
        "input_edge": input_edge,
        "output_edge": output_edge,
        "contract": {"input": input_edge, "output": output_edge},
        "blackbox": {
            "does": doc
            or (
                f"Run proof function {fn.name} and return a typed proof receipt."
                if proof_kind
                else f"Calls {fn.name} with {input_edge} and returns {output_edge}."
            )
        },
        "domains": domains,
        "capability_tags": domains,
        "effects": effects,
        "memory": "artifact" if "Path" in input_edge or "Path" in output_edge else "inline",
        "cache": "content_hash" if not effects else "policy_required",
        "runtime_targets": _runtime_targets(effects, input_edge, output_edge),
        "mutations": _mutator_options(input_edge, output_edge, effects),
        "source_ref": {
            "path": rel,
            "name": fn.name,
            "line": line,
            "language": "python",
        },
        "source_family": source_family,
        "surface_visibility": _source_visibility(path),
        "quality_score": _quality_score(
            doc=doc,
            input_edge=input_edge,
            output_edge=output_edge,
            domains=domains,
            effects=effects,
            source_family=source_family,
        ),
        "blocking_keys": sorted(set(_WORD_RE.findall(f"{slug} {input_edge} {output_edge} {doc}".lower()))),
        "source_digest": hashlib.sha256(source.encode("utf-8")).hexdigest()[:24],
        "generated_at": _utc(),
        "source_evidence_status": "source_backed",
        "trust": "candidate",
        "readiness": readiness,
        "candidate": True,
        "serves_truth": False,
    }


def _skip_path(path: Path, exclude_parts: set[str]) -> bool:
    parts = set(path.parts)
    if {"catalog", "knowledge-packs", "data"} <= parts:
        return bool(parts & (exclude_parts - {"data"}))
    return bool(parts & exclude_parts)


def scan_python_tree(
    root: Path,
    *,
    max_files: "int | None" = DEFAULT_MAX_FILES,
    max_records: "int | None" = DEFAULT_MAX_RECORDS,
    exclude_parts: set[str] | None = None,
) -> list[dict[str, Any]]:
    root = root.resolve()
    exclude_parts = set(DEFAULT_EXCLUDE_PARTS if exclude_parts is None else exclude_parts)
    records: list[dict[str, Any]] = []
    count_files = 0
    for path in sorted(root.rglob("*.py")):
        if _skip_path(path, exclude_parts):
            continue
        count_files += 1
        if count_files > _cap_or_unbounded(max_files) or len(records) >= _cap_or_unbounded(max_records):
            break
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                record = _record_for_function(path, root, node, source)
                if record:
                    records.append(record)
            elif isinstance(node, ast.ClassDef):
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and not child.name.startswith("__"):
                        record = _record_for_function(path, root, child, source)
                        if record:
                            record["kind"] = "py.method"
                            record["slug"] = f"{_slug(record['slug'])}.{_slug(node.name)}.{_slug(child.name)}"
                            records.append(record)
            if len(records) >= _cap_or_unbounded(max_records):
                break
    return records


def _js_args_edge(raw_args: str) -> str:
    args = [
        arg.strip().split(":", 1)[0].strip("{}[] ...")
        for arg in str(raw_args or "").split(",")
        if arg.strip()
    ]
    if not args:
        return "None"
    return "JsArg" if len(args) == 1 else "JsArgs"


def _js_comment_before(source: str, start: int) -> str:
    prefix = source[:start].splitlines()[-5:]
    comments: list[str] = []
    for line in reversed(prefix):
        stripped = line.strip()
        if stripped.startswith("//"):
            comments.append(stripped[2:].strip())
        elif stripped.startswith("*"):
            comments.append(stripped.lstrip("*").strip())
        elif stripped in {"/**", "/*"}:
            continue
        elif comments:
            break
    return " ".join(reversed(comments))[:220]


def _record_for_js_function(path: Path, name: str, args: str, source: str, start: int) -> dict[str, Any] | None:
    if name.startswith(PRIVATE_NAME_PREFIX):
        return None
    rel = _repo_rel(path)
    line = source[:start].count("\n") + 1
    slug = f"{_slug(rel.rsplit('.', 1)[0].replace('/', '.'))}.{_slug(name)}"
    input_edge = _js_args_edge(args)
    output_edge = "JsValue"
    doc = _js_comment_before(source, start)
    lowered = source[start:start + 900].lower()
    effects: set[str] = set()
    if "fetch(" in lowered or "axios." in lowered:
        effects.add("net.read")
    if "localstorage" in lowered or "sessionstorage" in lowered:
        effects.add("browser.storage")
    if "dispatch(" in lowered:
        effects.add("ui.event")
    domain_text = f"{slug} {input_edge} {output_edge} {doc} {rel}"
    domains = _domains_for_text(domain_text)
    source_family = _source_family(path)
    effect_list = sorted(effects)
    return {
        "primitive_id": "prim:" + _sha({"path": rel, "name": name, "line": line}),
        "slug": slug,
        "title": name,
        "kind": "js.fn",
        "input_edge": input_edge,
        "output_edge": output_edge,
        "contract": {"input": input_edge, "output": output_edge},
        "blackbox": {"does": doc or f"Calls {name} with {input_edge} and returns {output_edge}."},
        "domains": domains,
        "capability_tags": domains,
        "effects": effect_list,
        "memory": "inline",
        "cache": "content_hash" if not effects else "policy_required",
        "runtime_targets": _runtime_targets(effect_list, input_edge, output_edge),
        "mutations": _mutator_options(input_edge, output_edge, effect_list),
        "source_ref": {
            "path": rel,
            "name": name,
            "line": line,
            "language": "javascript" if path.suffix.lower() in {".js", ".jsx"} else "typescript",
        },
        "source_family": source_family,
        "surface_visibility": _source_visibility(path),
        "quality_score": _quality_score(
            doc=doc,
            input_edge=input_edge,
            output_edge=output_edge,
            domains=domains,
            effects=effect_list,
            source_family=source_family,
        ),
        "blocking_keys": sorted(set(_WORD_RE.findall(domain_text.lower()))),
        "source_digest": hashlib.sha256(source.encode("utf-8")).hexdigest()[:24],
        "generated_at": _utc(),
        "source_evidence_status": "source_backed",
        "trust": "candidate",
        "readiness": "R2_signature_candidate",
        "candidate": True,
        "serves_truth": False,
    }


def _record_for_js_test_case(path: Path, name: str, source: str, start: int) -> dict[str, Any]:
    rel = _repo_rel(path)
    line = source[:start].count("\n") + 1
    test_slug = _slug(name)
    slug = f"{_slug(rel.rsplit('.', 1)[0].replace('/', '.'))}.{test_slug}"
    input_edge = "FrontendProject+TestFixture" if path.suffix.lower() in {".jsx", ".tsx"} else "NodeProject+TestFixture"
    output_edge = "TestProofReceipt"
    body = source[start:start + 1200]
    doc = f"Run JavaScript/TypeScript test case `{name}` and return a typed proof receipt."
    domain_text = f"{slug} {input_edge} {output_edge} {doc} {rel} test proof playwright vitest jest regression"
    domains = _domains_for_text(domain_text)
    effects = ["subprocess"]
    source_family = _source_family(path)
    return {
        "primitive_id": "prim:" + _sha({"path": rel, "kind": "js_test_case", "name": name, "line": line}),
        "slug": slug,
        "title": name,
        "kind": "js.test_case",
        "input_edge": input_edge,
        "output_edge": output_edge,
        "contract": {"input": input_edge, "output": output_edge},
        "blackbox": {"does": doc},
        "domains": domains,
        "capability_tags": domains,
        "effects": effects,
        "memory": "artifact",
        "cache": "policy_required",
        "runtime_targets": _runtime_targets(effects, input_edge, output_edge),
        "mutations": _mutator_options(input_edge, output_edge, effects),
        "source_ref": {
            "path": rel,
            "name": name,
            "line": line,
            "language": "javascript" if path.suffix.lower() in {".js", ".jsx", ".mjs", ".cjs"} else "typescript",
        },
        "source_family": source_family,
        "surface_visibility": _source_visibility(path),
        "quality_score": _quality_score(
            doc=doc,
            input_edge=input_edge,
            output_edge=output_edge,
            domains=domains,
            effects=effects,
            source_family=source_family,
        ),
        "blocking_keys": sorted(set(_WORD_RE.findall(domain_text.lower()))),
        "source_digest": hashlib.sha256(body.encode("utf-8")).hexdigest()[:24],
        "generated_at": _utc(),
        "source_evidence_status": "source_backed",
        "trust": "candidate",
        "readiness": "R2_test_candidate",
        "candidate": True,
        "serves_truth": False,
    }


def scan_js_tree(
    root: Path,
    *,
    max_files: "int | None" = DEFAULT_MAX_FILES,
    max_records: "int | None" = DEFAULT_MAX_RECORDS,
    exclude_parts: set[str] | None = None,
) -> list[dict[str, Any]]:
    root = root.resolve()
    exclude_parts = set(DEFAULT_EXCLUDE_PARTS if exclude_parts is None else exclude_parts)
    records: list[dict[str, Any]] = []
    count_files = 0
    for suffix in JS_SUFFIXES:
        for path in sorted(root.rglob(f"*{suffix}")):
            if _skip_path(path, exclude_parts):
                continue
            if ".min." in path.name:
                continue
            count_files += 1
            if count_files > _cap_or_unbounded(max_files) or len(records) >= _cap_or_unbounded(max_records):
                break
            try:
                source = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for match in _JS_FUNCTION_RE.finditer(source):
                name = match.group(1) or match.group(3) or match.group(5) or ""
                args = match.group(2) or match.group(4) or match.group(6) or ""
                record = _record_for_js_function(path, name, args, source, match.start())
                if record:
                    records.append(record)
                if len(records) >= _cap_or_unbounded(max_records):
                    break
            for match in _JS_TEST_CASE_RE.finditer(source):
                if len(records) >= _cap_or_unbounded(max_records):
                    break
                records.append(_record_for_js_test_case(path, match.group(1), source, match.start()))
            if len(records) >= _cap_or_unbounded(max_records):
                break
    return records


def _line_for_text(source: str, needle: str) -> int:
    if not needle:
        return 1
    idx = source.find(needle)
    if idx < 0:
        return 1
    return source[:idx].count("\n") + 1


def _yaml_value(source: str, key: str) -> str:
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*:\s*['\"]?([^'\"\n#]+)", re.MULTILINE)
    match = pattern.search(source)
    return match.group(1).strip() if match else ""


def _json_value_summary(value: Any, *, limit: int = 120) -> str:
    if isinstance(value, str):
        return value[:limit]
    if isinstance(value, (int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return f"list[{len(value)}]"
    if isinstance(value, dict):
        keys = ", ".join(str(key) for key in list(value)[:8])
        return f"object[{keys}]"
    return type(value).__name__


def _list_str(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _row_body(row: dict[str, Any]) -> dict[str, Any]:
    body = row.get("body")
    return body if isinstance(body, dict) else {}


def _row_value(row: dict[str, Any], key: str, default: Any = "") -> Any:
    if key in row:
        return row.get(key)
    body = _row_body(row)
    if key in body:
        return body.get(key)
    return default


def _edge_type_name(value: str) -> str:
    parts = _WORD_RE.findall(str(value).lower())
    if not parts:
        return "Value"
    return "".join(part[:1].upper() + part[1:] for part in parts[:4])


def _joined_edge(values: list[str], fallback: str, *, max_parts: int = 4) -> str:
    if not values:
        return fallback
    return "+".join(_edge_type_name(value) for value in values[:max_parts])


def _capability_row_kind(row: dict[str, Any]) -> str:
    source_kind = str(row.get("source_kind") or "")
    if source_kind == "curated_public_codegen_use_case" or row.get("expected_template") or row.get("expected_primitives"):
        return "use_case_blueprint"
    if row.get("surface_family") or row.get("common_actions") or row.get("candidate_primitives"):
        return "microsurface_blueprint"
    if row.get("type") == "use_case_seed" or row.get("required_stages"):
        return "capability_blueprint"
    body = _row_body(row)
    if row.get("object_type") == "task" or body.get("workflow_steps") or body.get("automation_opportunities"):
        return "task_archetype_blueprint"
    if row.get("recommended_components") or row.get("expected_constraints"):
        return "scenario_blueprint"
    return ""


def _row_effects(row: dict[str, Any], text: str = "") -> list[str]:
    effects = set(_list_str(_row_value(row, "effects")))
    lowered = f"{text} {' '.join(effects)}".lower()
    if any(token in lowered for token in ("http", "web", "api", "fetch", "source", "search", "geocode")):
        effects.add("net.read")
    if any(token in lowered for token in ("db.write", "database write", "persist", "record", "audit", "approval", "session")):
        effects.add("db.write")
    if any(token in lowered for token in ("db.read", "database", "lookup", "query")):
        effects.add("db.read")
    if any(token in lowered for token in ("email", "sms", "notify", "send", "publish")):
        effects.add("external.write")
    if any(token in lowered for token in ("file", "csv", "parquet", "artifact", "document", "image", "video", "audio")):
        effects.add("fs.read")
    if any(token in lowered for token in ("write", "output", "export", "download", "media", "submission")):
        effects.add("fs.write")
    if "model.call" in effects or any(token in lowered for token in ("model", "llm", "classifier", "generate", "embedding")):
        effects.add("model.call")
    if any(token in lowered for token in ("k8s", "kubernetes", "deploy", "container", "cloud function")):
        effects.add("cloud.deploy")
    return sorted(effects)


def _action_edge_pair(action: str) -> tuple[str, str]:
    lowered = str(action).lower()
    if any(token in lowered for token in ("validate", "verify", "check", "gate", "screen", "scan")):
        return "CapabilityState", "ValidatedCapabilityState"
    if any(token in lowered for token in ("emit", "write", "publish", "persist", "record", "send", "notify", "download")):
        return "CapabilityState", "DeliveryOrArtifactReceipt"
    if any(token in lowered for token in ("fetch", "discover", "read", "load", "lookup", "search", "parse", "extract", "geocode")):
        return "CapabilityRequest", "SourceArtifactSet"
    if any(token in lowered for token in ("classify", "score", "evaluate", "route", "decide", "rank", "triage")):
        return "CapabilityState", "DecisionOrRouteRecord"
    if any(token in lowered for token in ("normalize", "clean", "cast", "rename", "dedupe", "cluster", "map")):
        return "SourceArtifactSet", "NormalizedRecordSet"
    if any(token in lowered for token in ("train", "feature", "model", "predict", "forecast", "metric", "submission")):
        return "TrainingDataset", "ModelOrEvaluationArtifact"
    if any(token in lowered for token in ("render", "component", "form", "page", "ui")):
        return "UiIntent", "UiComponentArtifact"
    return "CapabilityState", "CapabilityState"


def _action_effects(action: str, row_effects: list[str]) -> list[str]:
    lowered = str(action).lower()
    effects = set(row_effects)
    if any(token in lowered for token in ("send", "notify", "publish", "email", "sms", "webhook")):
        effects.add("external.write")
    if any(token in lowered for token in ("persist", "record", "write", "update", "create_session", "sync")):
        effects.add("db.write")
    if any(token in lowered for token in ("fetch", "lookup", "search", "geocode", "discover")):
        effects.add("net.read")
    if any(token in lowered for token in ("train", "classify", "model", "generate", "embedding")):
        effects.add("model.call")
    if any(token in lowered for token in ("csv", "file", "parquet", "artifact", "image", "video", "audio")):
        effects.add("fs.read")
    return sorted(effects)


def _artifact_record(
    *,
    path: Path,
    source: str,
    artifact_kind: str,
    name: str,
    input_edge: str,
    output_edge: str,
    effects: list[str],
    doc: str,
    line: int = 1,
    extra_keys: Iterable[str] = (),
) -> dict[str, Any]:
    rel = _repo_rel(path)
    slug = f"{_slug(rel.rsplit('.', 1)[0].replace('/', '.'))}.{_slug(name)}"
    domain_text = f"{slug} {artifact_kind} {input_edge} {output_edge} {doc} {rel} {' '.join(extra_keys)}"
    domains = _domains_for_text(domain_text)
    source_family = _source_family(path)
    effect_list = sorted(set(effects))
    return {
        "primitive_id": "prim:" + _sha({"path": rel, "kind": artifact_kind, "name": name, "line": line}),
        "slug": slug,
        "title": name,
        "kind": f"artifact.{artifact_kind}",
        "input_edge": input_edge,
        "output_edge": output_edge,
        "contract": {"input": input_edge, "output": output_edge},
        "blackbox": {"does": doc},
        "domains": domains,
        "capability_tags": domains,
        "effects": effect_list,
        "memory": "artifact",
        "cache": "content_hash" if not effect_list else "policy_required",
        "runtime_targets": _runtime_targets(effect_list, input_edge, output_edge),
        "mutations": _mutator_options(input_edge, output_edge, effect_list),
        "source_ref": {
            "path": rel,
            "name": name,
            "line": line,
            "language": source_family,
        },
        "source_family": source_family,
        "surface_visibility": _source_visibility(path),
        "quality_score": _quality_score(
            doc=doc,
            input_edge=input_edge,
            output_edge=output_edge,
            domains=domains,
            effects=effect_list,
            source_family=source_family,
        ),
        "blocking_keys": sorted(set(_WORD_RE.findall(domain_text.lower()))),
        "source_digest": hashlib.sha256(source.encode("utf-8")).hexdigest()[:24],
        "generated_at": _utc(),
        "source_evidence_status": "source_backed",
        "trust": "candidate",
        "readiness": "R2_artifact_edge_candidate",
        "candidate": True,
        "serves_truth": False,
    }


def _template_route_record(
    *,
    path: Path,
    source: str,
    name: str,
    title: str,
    route_family: str,
    stages: Iterable[str],
    effects: list[str],
    line: int = 1,
    input_edge: str = EDGE_DEVELOPER_INTENT_WITH_CANDIDATES,
    extra_keys: Iterable[str] = (),
) -> dict[str, Any]:
    stage_names = [str(stage).strip() for stage in stages if str(stage).strip()]
    stage_text = " -> ".join(stage_names[:12]) or route_family
    return _artifact_record(
        path=path,
        source=source,
        artifact_kind=ARTIFACT_KIND_CAPABILITY_TEMPLATE_ROUTE,
        name=name,
        input_edge=input_edge,
        output_edge=EDGE_PIPELINE_RECIPE,
        effects=effects,
        doc=f"Use source-backed `{route_family}` route `{title}` as a candidate pipeline recipe: {stage_text}.",
        line=line,
        extra_keys=(route_family, title, *stage_names[:20], *extra_keys),
    )


def _capability_slot_record(
    *,
    path: Path,
    source: str,
    route_name: str,
    slot_name: str,
    input_edge: str,
    output_edge: str,
    effects: list[str],
    doc: str,
    line: int = 1,
    extra_keys: Iterable[str] = (),
) -> dict[str, Any]:
    return _artifact_record(
        path=path,
        source=source,
        artifact_kind=ARTIFACT_KIND_CAPABILITY_SLOT,
        name=f"{route_name}.{slot_name}",
        input_edge=input_edge,
        output_edge=output_edge,
        effects=effects,
        doc=doc,
        line=line,
        extra_keys=(route_name, slot_name, *extra_keys),
    )


def _capability_blueprint_records(
    path: Path,
    line: str,
    row: dict[str, Any],
    *,
    line_no: int,
    max_rows: int,
) -> list[dict[str, Any]]:
    artifact_kind = _capability_row_kind(row)
    if not artifact_kind or max_rows <= 0:
        return []

    body = _row_body(row)
    row_id = str(row.get("id") or row.get("object_id") or row.get("source_record_id") or f"row_{line_no}")
    title = str(_row_value(row, "title", row_id) or row_id)
    task = str(
        _row_value(row, "intent")
        or _row_value(row, "task")
        or _row_value(row, "problem_statement")
        or body.get("problem_statement")
        or title
    )
    inputs = _list_str(_row_value(row, "inputs"))
    outputs = _list_str(_row_value(row, "outputs") or body.get("deliverables"))
    templates = [
        *(_list_str(_row_value(row, "expected_template"))),
        *_list_str(_row_value(row, "candidate_templates")),
    ]
    primitive_names = [
        *_list_str(_row_value(row, "expected_primitives")),
        *_list_str(_row_value(row, "candidate_primitives")),
    ]
    actions = [
        *_list_str(_row_value(row, "common_actions")),
        *_list_str(_row_value(row, "required_stages")),
        *_list_str(body.get("workflow_steps")),
        *_list_str(body.get("automation_opportunities")),
    ]
    row_effects = _row_effects(row, f"{title} {task} {' '.join(primitive_names)} {' '.join(actions)}")
    input_edge = _joined_edge(inputs, "DeveloperIntent")
    output_edge = _joined_edge(outputs, "CapabilityBlueprint")
    extra_keys = (
        row_id,
        title,
        task,
        str(_row_value(row, "task_family")),
        str(_row_value(row, "surface_family")),
        str(_row_value(row, "domain")),
        str(_row_value(row, "industry")),
        *templates,
        *primitive_names[:12],
        *actions[:12],
        *_list_str(_row_value(row, "reinvention_patterns"))[:8],
        *_list_str(_row_value(row, "observed_reinvention_patterns"))[:8],
    )
    records = [
        _artifact_record(
            path=path,
            source=line,
            artifact_kind=artifact_kind,
            name=row_id,
            input_edge=input_edge,
            output_edge=output_edge,
            effects=row_effects,
            doc=f"Compile capability blueprint `{title}`: {task[:220]}.",
            line=line_no,
            extra_keys=extra_keys,
        )
    ]

    for template in templates[: max(0, max_rows - len(records))]:
        records.append(_artifact_record(
            path=path,
            source=line,
            artifact_kind=ARTIFACT_KIND_CAPABILITY_TEMPLATE_ROUTE,
            name=f"{row_id}.{template}",
            input_edge=EDGE_DEVELOPER_INTENT_WITH_CANDIDATES,
            output_edge=EDGE_PIPELINE_RECIPE,
            effects=row_effects,
            doc=f"Use template `{template}` as a candidate route for `{title}`.",
            line=line_no,
            extra_keys=(row_id, title, template, task, *primitive_names[:12], *actions[:12]),
        ))
        if len(records) >= max_rows:
            return records[:max_rows]

    slot_names = [*primitive_names, *actions]
    seen_slots: set[str] = set()
    for index, slot_name in enumerate(slot_names, start=1):
        if len(records) >= max_rows:
            break
        slot = str(slot_name).strip()
        if not slot or slot in seen_slots:
            continue
        seen_slots.add(slot)
        slot_input, slot_output = _action_edge_pair(slot)
        records.append(_artifact_record(
            path=path,
            source=line,
            artifact_kind=ARTIFACT_KIND_CAPABILITY_SLOT,
            name=f"{row_id}.{index:02d}.{slot}",
            input_edge=slot_input,
            output_edge=slot_output,
            effects=_action_effects(slot, row_effects),
            doc=f"Candidate slot `{slot}` for capability blueprint `{title}`.",
            line=line_no,
            extra_keys=(row_id, title, slot, task, *templates, *_list_str(_row_value(row, "common_objects"))[:8]),
        ))
    return records[:max_rows]


def _json_artifact_records(path: Path, source: str, *, max_rows: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    name = path.name
    try:
        obj = json.loads(source)
    except json.JSONDecodeError:
        obj = None
    lower_name = name.lower()
    if isinstance(obj, dict):
        if lower_name == "package.json":
            scripts = obj.get("scripts")
            if isinstance(scripts, dict):
                script_names = [str(name) for name in sorted(scripts) if isinstance(name, str) and name]
                records.append(_template_route_record(
                    path=path,
                    source=source[:8000],
                    name=f"{path.parent.name or path.stem}.package_script_route",
                    title=path.parent.name or path.stem,
                    route_family="package_script_workflow",
                    stages=script_names,
                    effects=["subprocess"],
                    line=_line_for_text(source, "\"scripts\"") or 1,
                    input_edge="RepoCheckout+PackageManagerContext",
                    extra_keys=("package", "npm", "scripts", *script_names[:12]),
                ))
                for script_name, command in sorted(scripts.items()):
                    if len(records) >= max_rows:
                        break
                    if not isinstance(script_name, str) or not script_name:
                        continue
                    records.append(_artifact_record(
                        path=path,
                        source=source,
                        artifact_kind="package_script",
                        name=f"script.{script_name}",
                        input_edge="RepoCheckout+PackageManagerContext",
                        output_edge="ScriptRunReceipt",
                        effects=["subprocess"],
                        doc=f"Run package script `{script_name}`: {_json_value_summary(command)}.",
                        line=_line_for_text(source, f"\"{script_name}\""),
                        extra_keys=(script_name, str(command)),
                    ))
        if "openapi" in obj or "swagger" in obj:
            api_title = ((obj.get("info") or {}).get("title") if isinstance(obj.get("info"), dict) else "") or "openapi"
            records.append(_artifact_record(
                path=path,
                source=source,
                artifact_kind="openapi_spec",
                name=str(api_title),
                input_edge="HttpRequestSpec",
                output_edge="ApiRouteContractSet",
                effects=["net.read"],
                doc=f"Describe OpenAPI routes for `{api_title}`.",
                line=_line_for_text(source, "\"openapi\"") or _line_for_text(source, "\"swagger\""),
                extra_keys=("openapi", api_title),
            ))
            records.extend(_openapi_json_route_records(
                path=path,
                source=source,
                obj=obj,
                api_title=str(api_title),
                max_rows=max_rows - len(records),
            ))
            records.extend(_openapi_json_operation_records(
                path=path,
                source=source,
                obj=obj,
                api_title=str(api_title),
                max_rows=max_rows - len(records),
            ))
        if "$schema" in obj or "properties" in obj or lower_name.endswith(".schema.json"):
            title = str(obj.get("title") or path.stem)
            records.append(_artifact_record(
                path=path,
                source=source,
                artifact_kind="json_schema",
                name=title,
                input_edge="AnyJson",
                output_edge="SchemaValidationReport",
                effects=[],
                doc=f"Validate JSON values against schema `{title}`.",
                line=_line_for_text(source, "\"properties\""),
                extra_keys=(title, "schema", "validate"),
            ))
        if lower_name == ".mcp.json" or "mcpServers" in obj or "mcp" in lower_name:
            records.append(_artifact_record(
                path=path,
                source=source,
                artifact_kind="mcp_manifest",
                name="mcp_servers",
                input_edge="McpClientConfig",
                output_edge="ToolServerBindingSet",
                effects=["subprocess"],
                doc="Bind MCP server definitions into a tool-capable agent surface.",
                line=_line_for_text(source, "mcp"),
                extra_keys=("mcp", "tool", "server"),
            ))
            records.extend(_mcp_server_records(
                path=path,
                source=source,
                obj=obj,
                max_rows=max_rows - len(records),
            ))
        if _looks_like_n8n_workflow(obj, lower_name):
            records.extend(_n8n_workflow_records(
                path=path,
                source=source,
                obj=obj,
                max_rows=max_rows - len(records),
            ))
        if _looks_like_generic_workflow_dict(obj, lower_name):
            records.extend(_generic_workflow_records(
                path=path,
                source=source,
                workflows=[obj],
                max_rows=max_rows - len(records),
            ))
    elif isinstance(obj, list) and ("workflow" in lower_name or "pipeline" in lower_name or "dag" in lower_name):
        workflows = [item for item in obj if isinstance(item, dict)]
        records.extend(_generic_workflow_records(
            path=path,
            source=source,
            workflows=workflows,
            max_rows=max_rows,
        ))
    return records[:max_rows]


def _openapi_json_route_records(
    *,
    path: Path,
    source: str,
    obj: dict[str, Any],
    api_title: str,
    max_rows: int,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if max_rows <= 0:
        return records
    paths = obj.get("paths")
    if not isinstance(paths, dict):
        return records
    operations: list[tuple[str, str, str, str, list[str], int]] = []
    for route, methods in sorted(paths.items()):
        if not isinstance(route, str) or not isinstance(methods, dict):
            continue
        for method, operation in sorted(methods.items()):
            method_l = str(method).lower()
            if method_l not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            summary = str(operation.get("summary") or operation.get("description") or operation.get("operationId") or f"{method_l}_{route}")
            effects = ["net.read"] if method_l in HTTP_READ_METHODS else ["net.write"]
            operations.append((method_l.upper(), route, str(operation.get("operationId") or ""), summary, effects, _line_for_text(source, f"\"{route}\"")))
    if not operations:
        return records
    route_name = f"{api_title}.api_route_plan"
    records.append(_template_route_record(
        path=path,
        source=source[:8000],
        name=route_name,
        title=api_title,
        route_family="openapi_service",
        stages=[f"{method} {route}" for method, route, *_ in operations],
        effects=sorted({effect for *_, effects, __ in operations for effect in effects}),
        line=_line_for_text(source, "\"paths\"") or 1,
        input_edge="ApiProductIntent+OpenApiSpec",
        extra_keys=("openapi", "api", "route", "service", api_title),
    ))
    for index, (method, route, op_id, summary, effects, line) in enumerate(operations, start=1):
        if len(records) >= max_rows:
            break
        records.append(_capability_slot_record(
            path=path,
            source=f"{method} {route} {summary}",
            route_name=route_name,
            slot_name=f"{index:02d}.{method.lower()}.{_slug(route)}",
            input_edge=f"HttpRequest[{method} {route}]",
            output_edge="HttpResponseContract",
            effects=effects,
            doc=f"Candidate OpenAPI route slot `{method} {route}` from `{api_title}`: {summary[:180]}.",
            line=line,
            extra_keys=("openapi", api_title, route, method, op_id, summary),
        ))
    return records[:max_rows]


def _openapi_json_operation_records(
    *,
    path: Path,
    source: str,
    obj: dict[str, Any],
    api_title: str,
    max_rows: int,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if max_rows <= 0:
        return records
    paths = obj.get("paths")
    if not isinstance(paths, dict):
        return records
    for route, methods in sorted(paths.items()):
        if len(records) >= max_rows:
            break
        if not isinstance(route, str) or not isinstance(methods, dict):
            continue
        for method, operation in sorted(methods.items()):
            method_l = str(method).lower()
            if method_l not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            op_id = str(operation.get("operationId") or operation.get("summary") or f"{method_l}_{route}")
            summary = str(operation.get("summary") or operation.get("description") or op_id)
            effects = ["net.read"] if method_l in HTTP_READ_METHODS else ["net.write"]
            records.append(_artifact_record(
                path=path,
                source=json.dumps(operation, sort_keys=True),
                artifact_kind="openapi_operation",
                name=f"{method_l.upper()} {route}",
                input_edge=f"HttpRequest[{method_l.upper()} {route}]",
                output_edge="HttpResponseContract",
                effects=effects,
                doc=f"Call OpenAPI operation `{method_l.upper()} {route}` from `{api_title}`: {summary[:180]}.",
                line=_line_for_text(source, f"\"{route}\""),
                extra_keys=(api_title, route, method_l, op_id, summary),
            ))
            if len(records) >= max_rows:
                break
    return records


def _looks_like_n8n_workflow(obj: dict[str, Any], lower_name: str) -> bool:
    nodes = obj.get("nodes")
    return (
        isinstance(nodes, list)
        and (
            "n8n" in lower_name
            or "workflow" in lower_name
            or "connections" in obj
            or any(isinstance(node, dict) and str(node.get("type") or "").startswith("n8n-nodes-base.") for node in nodes[:12])
        )
    )


def _looks_like_generic_workflow_dict(obj: dict[str, Any], lower_name: str) -> bool:
    return (
        "workflow" in lower_name
        or "pipeline" in lower_name
        or "dag" in lower_name
        or any(key in obj for key in ("steps", "tasks", "workflowType", "promptTemplate", "preferredDomains"))
    )


def _generic_workflow_effects(text: str) -> tuple[list[str], tuple[str, ...]]:
    lowered = text.lower()
    effects: set[str] = {"workflow.task"}
    keys: set[str] = {"workflow"}
    if any(token in lowered for token in ("http", "webhook", "api", "fetch", "request")):
        effects.add("net.read")
        keys.add("api")
    if any(token in lowered for token in ("email", "slack", "send", "notify", "publish")):
        effects.add("external.write")
        keys.add("delivery")
    if any(token in lowered for token in ("sql", "database", "postgres", "warehouse")):
        effects.add("db.read")
        keys.add("database")
    if any(token in lowered for token in ("python", "script", "shell", "command")):
        effects.add("subprocess")
        keys.add("command")
    if any(token in lowered for token in ("deploy", "kubernetes", "docker", "cloud")):
        effects.add("cloud.deploy")
        keys.add("deploy")
    return sorted(effects), tuple(sorted(keys))


def _generic_workflow_records(
    *,
    path: Path,
    source: str,
    workflows: list[dict[str, Any]],
    max_rows: int,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for idx, workflow in enumerate(workflows, start=1):
        if len(records) >= max_rows:
            break
        name = str(workflow.get("name") or workflow.get("id") or workflow.get("slug") or f"workflow_{idx}")[:140]
        description = str(
            workflow.get("description")
            or workflow.get("task")
            or workflow.get("promptTemplate")
            or workflow.get("intent")
            or ""
        )
        workflow_text = json.dumps(workflow, sort_keys=True)[:5000]
        effects, keys = _generic_workflow_effects(workflow_text)
        workflow_type = str(workflow.get("workflowType") or workflow.get("type") or "workflow")
        steps = workflow.get("steps") or workflow.get("tasks") or workflow.get("nodes")
        step_names: list[str] = []
        if isinstance(steps, list):
            for step_index, step in enumerate(steps, start=1):
                if not isinstance(step, dict):
                    continue
                step_names.append(str(step.get("name") or step.get("id") or step.get("type") or f"step_{step_index}")[:120])
        records.append(_template_route_record(
            path=path,
            source=workflow_text,
            name=f"{name}.workflow_route",
            title=name,
            route_family="workflow_automation",
            stages=step_names or [workflow_type],
            effects=effects,
            line=_line_for_text(source, name),
            input_edge="WorkflowIntent+CandidatePrimitiveSet",
            extra_keys=(name, workflow_type, description, *keys, *step_names[:12]),
        ))
        if len(records) >= max_rows:
            break
        records.append(_artifact_record(
            path=path,
            source=workflow_text,
            artifact_kind="workflow_definition",
            name=name,
            input_edge="WorkflowIntent+WorkflowInputs",
            output_edge="WorkflowExecutionPlan",
            effects=effects,
            doc=f"Materialize workflow `{name}` of type `{workflow_type}`: {description[:180]}.",
            line=_line_for_text(source, name),
            extra_keys=(name, workflow_type, description, *keys),
        ))
        if not isinstance(steps, list):
            continue
        for step_index, step in enumerate(steps, start=1):
            if len(records) >= max_rows:
                break
            if not isinstance(step, dict):
                continue
            step_name = str(step.get("name") or step.get("id") or step.get("type") or f"step_{step_index}")[:120]
            step_text = json.dumps(step, sort_keys=True)[:3000]
            step_effects, step_keys = _generic_workflow_effects(step_text)
            records.append(_artifact_record(
                path=path,
                source=step_text,
                artifact_kind="workflow_step",
                name=f"{name}.{step_name}",
                input_edge="WorkflowState",
                output_edge="WorkflowState",
                effects=step_effects,
                doc=f"Execute workflow step `{step_name}` inside `{name}`.",
                line=_line_for_text(source, step_name),
                extra_keys=(name, step_name, *step_keys),
            ))
            if len(records) >= max_rows:
                break
            records.append(_capability_slot_record(
                path=path,
                source=step_text,
                route_name=f"{name}.workflow_route",
                slot_name=f"{step_index:02d}.{_slug(step_name)}",
                input_edge="WorkflowState",
                output_edge="WorkflowState",
                effects=step_effects,
                doc=f"Candidate workflow automation slot `{step_name}` inside `{name}`.",
                line=_line_for_text(source, step_name),
                extra_keys=(name, step_name, *step_keys),
            ))
    return records[:max_rows]


def _n8n_node_edges(node: dict[str, Any]) -> tuple[str, str, list[str], tuple[str, ...]]:
    node_type = str(node.get("type") or "")
    lowered = node_type.lower()
    effects: set[str] = {"workflow.task"}
    keys = {"workflow", "n8n", node_type}
    input_edge = "WorkflowState"
    output_edge = "WorkflowState"
    if "trigger" in lowered or "webhook" in lowered:
        input_edge = "ExternalEvent"
        output_edge = "WorkflowState"
        effects.add("net.read")
    if "httprequest" in lowered or "http" in lowered:
        input_edge = "WorkflowState+HttpRequestSpec"
        output_edge = "WorkflowState+HttpResponse"
        effects.add("net.read")
    if any(token in lowered for token in ("postgres", "mysql", "mongo", "database", "supabase", "airtable")):
        effects.add("db.read")
        output_edge = "WorkflowState+DatabaseResult"
    if any(token in lowered for token in ("slack", "email", "gmail", "discord", "telegram", "send")):
        effects.add("external.write")
        output_edge = "WorkflowState+DeliveryReceipt"
    if "code" in lowered or "function" in lowered:
        input_edge = "WorkflowState+CodeContext"
        output_edge = "WorkflowState+CodeResult"
        effects.add("subprocess")
    return input_edge, output_edge, sorted(effects), tuple(sorted(keys))


def _n8n_workflow_records(path: Path, source: str, obj: dict[str, Any], *, max_rows: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if max_rows <= 0:
        return records
    workflow_name = str(obj.get("name") or path.stem)
    nodes = obj.get("nodes")
    if not isinstance(nodes, list):
        return records
    records.append(_artifact_record(
        path=path,
        source=source[:4000],
        artifact_kind="n8n_workflow",
        name=workflow_name,
        input_edge="WorkflowTriggerEvent",
        output_edge="WorkflowExecutionReceipt",
        effects=["workflow.task"],
        doc=f"Run n8n workflow `{workflow_name}` with {len(nodes)} nodes.",
        line=_line_for_text(source, "\"nodes\""),
        extra_keys=("n8n", "workflow", workflow_name, *(str(node.get("type") or "") for node in nodes[:10] if isinstance(node, dict))),
    ))
    route_name = f"{workflow_name}.n8n_route"
    records.append(_template_route_record(
        path=path,
        source=source[:8000],
        name=route_name,
        title=workflow_name,
        route_family="n8n_workflow",
        stages=[str(node.get("name") or node.get("type") or f"node_{idx}") for idx, node in enumerate(nodes[:20], start=1) if isinstance(node, dict)],
        effects=["workflow.task"],
        line=_line_for_text(source, "\"nodes\""),
        input_edge="WorkflowIntent+N8nWorkflowDefinition",
        extra_keys=("n8n", "workflow", workflow_name, *(str(node.get("type") or "") for node in nodes[:10] if isinstance(node, dict))),
    ))
    for idx, node in enumerate(nodes, start=1):
        if len(records) >= max_rows:
            break
        if not isinstance(node, dict):
            continue
        node_name = str(node.get("name") or node.get("id") or f"node_{idx}")
        node_type = str(node.get("type") or "n8n_node")
        input_edge, output_edge, effects, keys = _n8n_node_edges(node)
        records.append(_artifact_record(
            path=path,
            source=json.dumps(node, sort_keys=True)[:4000],
            artifact_kind="n8n_node",
            name=f"{workflow_name}.{node_name}",
            input_edge=input_edge,
            output_edge=output_edge,
            effects=effects,
            doc=f"Execute n8n node `{node_name}` of type `{node_type}` within workflow `{workflow_name}`.",
            line=_line_for_text(source, f"\"{node_name}\""),
            extra_keys=(workflow_name, node_name, node_type, *keys),
        ))
        if len(records) >= max_rows:
            break
        records.append(_capability_slot_record(
            path=path,
            source=json.dumps(node, sort_keys=True)[:4000],
            route_name=route_name,
            slot_name=f"{idx:02d}.{_slug(node_name)}",
            input_edge=input_edge,
            output_edge=output_edge,
            effects=effects,
            doc=f"Candidate n8n workflow slot `{node_name}` of type `{node_type}` inside `{workflow_name}`.",
            line=_line_for_text(source, f"\"{node_name}\""),
            extra_keys=("n8n", workflow_name, node_name, node_type, *keys),
        ))
    return records[:max_rows]


def _mcp_server_records(path: Path, source: str, obj: dict[str, Any], *, max_rows: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if max_rows <= 0:
        return records
    servers = obj.get("mcpServers")
    if not isinstance(servers, dict):
        return records
    server_names = [str(name) for name in sorted(servers) if isinstance(servers.get(name), dict)]
    route_name = f"{path.stem}.mcp_tool_route"
    records.append(_template_route_record(
        path=path,
        source=source[:8000],
        name=route_name,
        title=path.stem,
        route_family="mcp_tool_binding",
        stages=server_names or ["bind_mcp_server"],
        effects=["subprocess"],
        line=_line_for_text(source, "mcpServers") or 1,
        input_edge="AgentToolIntent+McpClientConfig",
        extra_keys=("mcp", "tool", "server", *server_names[:12]),
    ))
    for server_name, server in sorted(servers.items()):
        if len(records) >= max_rows:
            break
        if not isinstance(server, dict):
            continue
        command = str(server.get("command") or "")
        args = server.get("args")
        arg_text = " ".join(str(arg) for arg in args) if isinstance(args, list) else ""
        records.append(_artifact_record(
            path=path,
            source=json.dumps(server, sort_keys=True),
            artifact_kind="mcp_server_binding",
            name=str(server_name),
            input_edge="AgentToolRequest",
            output_edge="McpToolCallResult",
            effects=["subprocess"],
            doc=f"Start MCP server `{server_name}` using `{command} {arg_text}` and expose its tools to an agent.",
            line=_line_for_text(source, str(server_name)),
            extra_keys=("mcp", "server", str(server_name), command, arg_text),
        ))
        if len(records) >= max_rows:
            break
        records.append(_capability_slot_record(
            path=path,
            source=json.dumps(server, sort_keys=True),
            route_name=route_name,
            slot_name=f"{_slug(str(server_name))}.server_binding",
            input_edge="AgentToolRequest",
            output_edge="McpToolCallResult",
            effects=["subprocess"],
            doc=f"Candidate MCP server binding slot `{server_name}` using `{command} {arg_text}`.",
            line=_line_for_text(source, str(server_name)),
            extra_keys=("mcp", "server", str(server_name), command, arg_text),
        ))
    return records


def _jsonl_artifact_records(path: Path, source: str, *, max_rows: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for idx, line in enumerate(source.splitlines(), start=1):
        if len(records) >= max_rows:
            break
        text = line.strip()
        if not text:
            continue
        try:
            row = json.loads(text)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict):
            continue
        if len(records) < max_rows:
            records.extend(_capability_blueprint_records(
                path,
                line,
                row,
                line_no=idx,
                max_rows=max_rows - len(records),
            ))
            if len(records) >= max_rows:
                break
        name = str(row.get("id") or row.get("slug") or row.get("title") or f"row_{idx}")[:120]
        intent = str(row.get("intent") or row.get("description") or row.get("title") or "")
        output = "PrimitiveRecordDraft"
        if row.get("expected_primitives"):
            output = "PrimitiveFamilyOpportunity"
        elif row.get("candidate_templates"):
            output = "PipelineTemplateOpportunity"
        elif row.get("record_type"):
            output = f"{_slug(str(row.get('record_type'))).replace('.', '_').title()}Record"
        records.append(_artifact_record(
            path=path,
            source=line,
            artifact_kind="jsonl_record",
            name=name,
            input_edge="SourceEvidence",
            output_edge=output,
            effects=[],
            doc=intent or f"Materialize candidate record `{name}` from JSONL evidence.",
            line=idx,
            extra_keys=tuple(str(key) for key in list(row)[:12]),
        ))
    return records


def _yaml_artifact_records(path: Path, source: str, *, max_rows: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    rel = _repo_rel(path).lower()
    lower = source.lower()
    if ".github/workflows/" in rel or rel.startswith(".github/workflows/"):
        name = _yaml_value(source, "name") or path.stem
        records.append(_artifact_record(
            path=path,
            source=source,
            artifact_kind="ci_workflow",
            name=name,
            input_edge="RepoEvent+RepoCheckout",
            output_edge="WorkflowRunReport",
            effects=["subprocess"],
            doc=f"Run CI workflow `{name}` for repository validation/build/release steps.",
            line=_line_for_text(source, "name:"),
            extra_keys=("ci", "workflow", "test", "build"),
        ))
        records.extend(_ci_workflow_route_records(
            path=path,
            source=source,
            workflow_name=name,
            max_rows=max_rows - len(records),
        ))
    if "openapi:" in lower or "swagger:" in lower:
        title = _yaml_value(source, "title") or path.stem
        records.append(_artifact_record(
            path=path,
            source=source,
            artifact_kind="openapi_spec",
            name=title,
            input_edge="HttpRequestSpec",
            output_edge="ApiRouteContractSet",
            effects=["net.read"],
            doc=f"Describe OpenAPI routes for `{title}`.",
            line=_line_for_text(source, "openapi:"),
            extra_keys=("openapi", "api", "route"),
        ))
        records.extend(_openapi_yaml_route_records(
            path=path,
            source=source,
            api_title=title,
            max_rows=max_rows - len(records),
        ))
        records.extend(_openapi_yaml_operation_records(
            path=path,
            source=source,
            api_title=title,
            max_rows=max_rows - len(records),
        ))
    if "asyncapi:" in lower:
        title = _yaml_value(source, "title") or path.stem
        records.append(_artifact_record(
            path=path,
            source=source,
            artifact_kind="asyncapi_spec",
            name=title,
            input_edge="EventMessageSpec",
            output_edge="AsyncApiChannelContractSet",
            effects=["net.read"],
            doc=f"Describe AsyncAPI channels/messages for `{title}`.",
            line=_line_for_text(source, "asyncapi:"),
            extra_keys=("asyncapi", "event", "channel"),
        ))
    kind = _yaml_value(source, "kind")
    api_version = _yaml_value(source, "apiVersion")
    if kind and api_version:
        name = _yaml_value(source, "name") or kind
        records.append(_artifact_record(
            path=path,
            source=source,
            artifact_kind="k8s_manifest",
            name=f"{kind}.{name}",
            input_edge="ContainerImageSpec+RuntimeConfig",
            output_edge="KubernetesWorkloadManifest",
            effects=["k8s.apply"],
            doc=f"Define Kubernetes `{kind}` workload/config `{name}`.",
            line=_line_for_text(source, "kind:"),
            extra_keys=(kind, api_version, name, "kubernetes"),
        ))
        records.extend(_k8s_manifest_route_records(
            path=path,
            source=source,
            kind=kind,
            name=name,
            api_version=api_version,
            max_rows=max_rows - len(records),
        ))
    if "/catalog/" in rel:
        component_id = _yaml_value(source, "id") or _yaml_value(source, "slug") or path.stem
        records.append(_artifact_record(
            path=path,
            source=source,
            artifact_kind="catalog_component",
            name=component_id,
            input_edge="ComponentDefinitionYaml",
            output_edge="RegistryComponentRecord",
            effects=[],
            doc=f"Load catalog component definition `{component_id}` as a registry candidate.",
            line=1,
            extra_keys=("catalog", "registry", component_id),
        ))
    return records


def _ci_workflow_route_records(
    *,
    path: Path,
    source: str,
    workflow_name: str,
    max_rows: int,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if max_rows <= 0:
        return records
    jobs: list[tuple[str, int]] = []
    commands: list[tuple[str, int]] = []
    in_jobs = False
    for line_no, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        if stripped == "jobs:":
            in_jobs = True
            continue
        if in_jobs and stripped and not line.startswith((" ", "\t")) and stripped.endswith(":"):
            break
        if in_jobs:
            job_match = re.match(r"^\s{2}([A-Za-z0-9_.-]+):\s*$", line)
            if job_match and job_match.group(1) not in {"steps", "env", "with"}:
                jobs.append((job_match.group(1), line_no))
            if "run:" in stripped:
                command = stripped.split("run:", 1)[1].strip().strip("'\"")
                if command:
                    commands.append((command[:120], line_no))
    stages = [f"job:{job}" for job, _ in jobs] + [f"run:{cmd}" for cmd, _ in commands[:8]]
    records.append(_template_route_record(
        path=path,
        source=source[:8000],
        name=f"{workflow_name}.ci_route",
        title=workflow_name,
        route_family="ci_workflow",
        stages=stages or ["checkout", "test", "build"],
        effects=["subprocess"],
        line=_line_for_text(source, "jobs:") or 1,
        input_edge="RepoEvent+RepoCheckout",
        extra_keys=("ci", "workflow", "build", "test", workflow_name, *stages[:12]),
    ))
    route_name = f"{workflow_name}.ci_route"
    for index, (job, line_no) in enumerate(jobs, start=1):
        if len(records) >= max_rows:
            break
        records.append(_capability_slot_record(
            path=path,
            source=job,
            route_name=route_name,
            slot_name=f"{index:02d}.job.{_slug(job)}",
            input_edge="RepoCheckout+WorkflowContext",
            output_edge="WorkflowRunReport",
            effects=["subprocess"],
            doc=f"Candidate CI job slot `{job}` from workflow `{workflow_name}`.",
            line=line_no,
            extra_keys=("ci", "job", workflow_name, job),
        ))
    for index, (command, line_no) in enumerate(commands, start=1):
        if len(records) >= max_rows:
            break
        input_edge, output_edge, effects, keys = _snippet_edges("bash", command)
        records.append(_capability_slot_record(
            path=path,
            source=command,
            route_name=route_name,
            slot_name=f"{index:02d}.run.{_slug(command)}",
            input_edge=input_edge,
            output_edge=output_edge,
            effects=effects or ["subprocess"],
            doc=f"Candidate CI command slot `{command}` from workflow `{workflow_name}`.",
            line=line_no,
            extra_keys=("ci", "run", workflow_name, command, *keys),
        ))
    return records[:max_rows]


def _k8s_manifest_route_records(
    *,
    path: Path,
    source: str,
    kind: str,
    name: str,
    api_version: str,
    max_rows: int,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if max_rows <= 0:
        return records
    lowered = source.lower()
    stages = ["validate_manifest", "apply_manifest"]
    if "readinessprobe" in lowered:
        stages.append("check_readiness_probe")
    if "livenessprobe" in lowered:
        stages.append("check_liveness_probe")
    if str(kind).lower() in {"cronjob"} or "schedule:" in lowered:
        stages.append("validate_schedule")
    route_name = f"{kind}.{name}.k8s_route"
    records.append(_template_route_record(
        path=path,
        source=source[:8000],
        name=route_name,
        title=f"{kind}.{name}",
        route_family="kubernetes_runtime",
        stages=stages,
        effects=["k8s.apply"],
        line=_line_for_text(source, "kind:") or 1,
        input_edge="RuntimeIntent+ContainerImageSpec",
        extra_keys=("kubernetes", "k8s", kind, name, api_version, *stages),
    ))
    slot_specs = [
        ("validate_manifest", "KubernetesManifest", "ValidatedKubernetesManifest", []),
        ("apply_manifest", "ValidatedKubernetesManifest", "KubernetesApplyReceipt", ["k8s.apply"]),
    ]
    if "readinessprobe" in lowered:
        slot_specs.append(("check_readiness_probe", "KubernetesWorkloadManifest", "ReadinessProbeReport", []))
    if "livenessprobe" in lowered:
        slot_specs.append(("check_liveness_probe", "KubernetesWorkloadManifest", "LivenessProbeReport", []))
    if str(kind).lower() in {"cronjob"} or "schedule:" in lowered:
        slot_specs.append(("validate_schedule", "KubernetesCronJobManifest", "ScheduleValidationReport", []))
    for index, (slot_name, input_edge, output_edge, effects) in enumerate(slot_specs, start=1):
        if len(records) >= max_rows:
            break
        records.append(_capability_slot_record(
            path=path,
            source=source[:4000],
            route_name=route_name,
            slot_name=f"{index:02d}.{slot_name}",
            input_edge=input_edge,
            output_edge=output_edge,
            effects=effects,
            doc=f"Candidate Kubernetes `{slot_name}` slot for `{kind}.{name}`.",
            line=_line_for_text(source, "kind:") or 1,
            extra_keys=("kubernetes", "k8s", kind, name, api_version, slot_name),
        ))
    return records[:max_rows]


def _openapi_yaml_route_records(
    *,
    path: Path,
    source: str,
    api_title: str,
    max_rows: int,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if max_rows <= 0:
        return records
    operations: list[tuple[str, str, list[str], int]] = []
    current_route = ""
    current_line = 1
    in_paths = False
    for line_no, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        if stripped == "paths:":
            in_paths = True
            continue
        if not in_paths:
            continue
        if stripped and not line.startswith((" ", "\t")) and stripped.endswith(":") and stripped != "paths:":
            break
        if stripped.startswith("/") and stripped.endswith(":"):
            current_route = stripped[:-1].strip("'\"")
            current_line = line_no
            continue
        if current_route:
            method = stripped[:-1].lower() if stripped.endswith(":") else ""
            if method in HTTP_METHODS:
                effects = ["net.read"] if method in HTTP_READ_METHODS else ["net.write"]
                operations.append((method.upper(), current_route, effects, current_line))
    if not operations:
        return records
    route_name = f"{api_title}.api_route_plan"
    records.append(_template_route_record(
        path=path,
        source=source[:8000],
        name=route_name,
        title=api_title,
        route_family="openapi_service",
        stages=[f"{method} {route}" for method, route, *_ in operations],
        effects=sorted({effect for *_, effects, __ in operations for effect in effects}),
        line=_line_for_text(source, "paths:") or 1,
        input_edge="ApiProductIntent+OpenApiSpec",
        extra_keys=("openapi", "api", "route", "service", api_title),
    ))
    for index, (method, route, effects, line) in enumerate(operations, start=1):
        if len(records) >= max_rows:
            break
        records.append(_capability_slot_record(
            path=path,
            source=f"{method} {route}",
            route_name=route_name,
            slot_name=f"{index:02d}.{method.lower()}.{_slug(route)}",
            input_edge=f"HttpRequest[{method} {route}]",
            output_edge="HttpResponseContract",
            effects=effects,
            doc=f"Candidate OpenAPI route slot `{method} {route}` from `{api_title}`.",
            line=line,
            extra_keys=("openapi", api_title, route, method),
        ))
    return records[:max_rows]


def _openapi_yaml_operation_records(
    *,
    path: Path,
    source: str,
    api_title: str,
    max_rows: int,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if max_rows <= 0:
        return records
    current_route = ""
    current_line = 1
    in_paths = False
    for line_no, line in enumerate(source.splitlines(), start=1):
        stripped = line.strip()
        if stripped == "paths:":
            in_paths = True
            continue
        if not in_paths:
            continue
        if stripped and not line.startswith((" ", "\t")) and stripped.endswith(":") and stripped != "paths:":
            break
        if stripped.startswith("/") and stripped.endswith(":"):
            current_route = stripped[:-1].strip("'\"")
            current_line = line_no
            continue
        if current_route:
            method = stripped[:-1].lower() if stripped.endswith(":") else ""
            if method in HTTP_METHODS:
                effects = ["net.read"] if method in HTTP_READ_METHODS else ["net.write"]
                records.append(_artifact_record(
                    path=path,
                    source=f"{method.upper()} {current_route}",
                    artifact_kind="openapi_operation",
                    name=f"{method.upper()} {current_route}",
                    input_edge=f"HttpRequest[{method.upper()} {current_route}]",
                    output_edge="HttpResponseContract",
                    effects=effects,
                    doc=f"Call OpenAPI operation `{method.upper()} {current_route}` from `{api_title}`.",
                    line=current_line,
                    extra_keys=(api_title, current_route, method, "openapi", "operation"),
                ))
                if len(records) >= max_rows:
                    break
    return records


def _dockerfile_records(path: Path, source: str) -> list[dict[str, Any]]:
    return [_artifact_record(
        path=path,
        source=source,
        artifact_kind="dockerfile",
        name="container_build",
        input_edge="RuntimeBuildContext",
        output_edge="ContainerImageSpec",
        effects=["container.build", "subprocess"],
        doc="Build a container image from a Dockerfile runtime definition.",
        line=_line_for_text(source, "FROM"),
        extra_keys=("docker", "container", "runtime"),
    )]


def _terraform_records(path: Path, source: str) -> list[dict[str, Any]]:
    return [_artifact_record(
        path=path,
        source=source,
        artifact_kind="terraform_module",
        name=path.stem,
        input_edge="CloudResourceConfig",
        output_edge="TerraformPlanCandidate",
        effects=["cloud.deploy", "subprocess"],
        doc=f"Plan cloud resources described by Terraform file `{path.name}`.",
        line=1,
        extra_keys=("terraform", "cloud", "plan"),
    )]


def _sql_records(path: Path, source: str) -> list[dict[str, Any]]:
    lower = source.lower()
    output = "SqlResultSet" if "select" in lower else "MigrationReceipt"
    effects = ["db.read"] if output == "SqlResultSet" else ["db.write"]
    return [_artifact_record(
        path=path,
        source=source,
        artifact_kind="sql_artifact",
        name=path.stem,
        input_edge="SqlExecutionContext",
        output_edge=output,
        effects=effects,
        doc=f"Execute SQL artifact `{path.name}` as a reusable database operation candidate.",
        line=1,
        extra_keys=("sql", "database", output),
    )]


def _ipynb_records(path: Path, source: str, *, max_rows: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    try:
        notebook = json.loads(source)
    except json.JSONDecodeError:
        return records
    if not isinstance(notebook, dict):
        return records
    cells = notebook.get("cells")
    if not isinstance(cells, list):
        return records
    metadata = notebook.get("metadata") if isinstance(notebook.get("metadata"), dict) else {}
    kernelspec = metadata.get("kernelspec") if isinstance(metadata.get("kernelspec"), dict) else {}
    language_info = metadata.get("language_info")
    language = str(
        kernelspec.get("language")
        or (language_info.get("name") if isinstance(language_info, dict) else "")
        or "python"
    )
    stage_names: list[str] = []
    stage_heading = ""
    for idx, cell in enumerate(cells, start=1):
        if not isinstance(cell, dict):
            continue
        raw_source = cell.get("source") or ""
        if isinstance(raw_source, list):
            body = "".join(str(part) for part in raw_source)
        else:
            body = str(raw_source)
        body = body.strip()
        if not body:
            continue
        cell_type = str(cell.get("cell_type") or "")
        if cell_type == "markdown":
            for line in body.splitlines():
                if line.strip().startswith("#"):
                    stage_heading = line.strip().lstrip("#").strip()[:120]
                    break
        elif cell_type == "code":
            first_line = " ".join(body.splitlines()[:1])[:80]
            stage_names.append(stage_heading or first_line or f"cell_{idx}")
    if stage_names and max_rows > 0:
        records.append(_template_route_record(
            path=path,
            source=source[:8000],
            name=f"{path.stem}.notebook_pipeline",
            title=path.stem,
            route_family="notebook_pipeline",
            stages=stage_names[:20],
            effects=["subprocess"],
            line=1,
            input_edge="AnalysisIntent+NotebookContext",
            extra_keys=("notebook", "kaggle", "jupyter", language, *stage_names[:12]),
        ))
    markdown_context = ""
    for idx, cell in enumerate(cells, start=1):
        if len(records) >= max_rows:
            break
        if not isinstance(cell, dict):
            continue
        raw_source = cell.get("source") or ""
        if isinstance(raw_source, list):
            body = "".join(str(part) for part in raw_source)
        else:
            body = str(raw_source)
        body = body.strip()
        if not body:
            continue
        cell_type = str(cell.get("cell_type") or "")
        if cell_type == "markdown":
            for line in body.splitlines():
                if line.strip().startswith("#"):
                    markdown_context = line.strip().lstrip("#").strip()[:120]
                    break
            continue
        if cell_type != "code":
            continue
        input_edge, output_edge, effects, keys = _snippet_edges(language or "python", body)
        first_line = " ".join(body.splitlines()[:2])[:160]
        records.append(_artifact_record(
            path=path,
            source=body[:8000],
            artifact_kind="notebook_code_cell",
            name=f"{path.stem}.cell_{idx}",
            input_edge=input_edge,
            output_edge=output_edge,
            effects=effects or ["subprocess"],
            doc=f"Run notebook code cell {idx} from `{path.name}`"
            + (f" under `{markdown_context}`" if markdown_context else "")
            + f": {first_line}.",
            line=idx,
            extra_keys=(path.stem, markdown_context, first_line, *keys),
        ))
        if len(records) >= max_rows:
            break
        records.append(_capability_slot_record(
            path=path,
            source=body[:8000],
            route_name=f"{path.stem}.notebook_pipeline",
            slot_name=f"{idx:02d}.cell",
            input_edge=input_edge,
            output_edge=output_edge,
            effects=effects or ["subprocess"],
            doc=f"Candidate notebook pipeline slot cell {idx} from `{path.name}`"
            + (f" under `{markdown_context}`" if markdown_context else "")
            + f": {first_line}.",
            line=idx,
            extra_keys=("notebook", path.stem, markdown_context, first_line, *keys),
        ))
    return records[:max_rows]


def _snippet_edges(language: str, body: str) -> tuple[str, str, list[str], tuple[str, ...]]:
    lang = _slug(language or "text").replace(".", "_")
    lowered = body.lower()
    effects: set[str] = set()
    keys: set[str] = {lang}
    input_edge = "SnippetExecutionContext"
    output_edge = "SnippetRunReceipt"
    if lang in {"bash", "shell", "sh", "zsh", "console", "terminal"}:
        input_edge = "ShellExecutionContext"
        output_edge = "CommandRunReceipt"
        effects.add("subprocess")
    elif lang in {"python", "py"}:
        input_edge = "PythonExecutionContext"
        output_edge = "PythonRunReceipt"
        effects.add("subprocess")
    elif lang in {"javascript", "js", "typescript", "ts", "tsx", "jsx"}:
        input_edge = "NodeExecutionContext"
        output_edge = "NodeRunReceipt"
        effects.add("subprocess")
    elif lang in {"yaml", "yml", "json", "toml"}:
        input_edge = "ConfigDocument"
        output_edge = "ConfigValidationCandidate"
    if any(token in lowered for token in ("curl ", "wget ", "http://", "https://", "fetch(")):
        effects.add("net.read")
        keys.add("network")
    if any(token in lowered for token in ("kubectl", "helm", "kubernetes", "k8s")):
        effects.add("k8s.apply")
        output_edge = "KubernetesOperationReceipt"
        keys.add("kubernetes")
    if any(token in lowered for token in ("docker", "container")):
        effects.add("container.build")
        keys.add("container")
    if any(token in lowered for token in ("terraform", "aws ", "gcloud ", "az ")):
        effects.add("cloud.deploy")
        keys.add("cloud")
    if any(token in lowered for token in ("pytest", "ruff", "mypy", "vitest", "playwright test", "npm test")):
        keys.add("test")
    return input_edge, output_edge, sorted(effects), tuple(sorted(keys))


def _doc_heading_before(source: str, start: int) -> str:
    prefix = source[:start].splitlines()
    for line in reversed(prefix[-40:]):
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()[:120]
    return ""


def _markdown_records(path: Path, source: str, *, max_rows: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    executable_langs = {
        "bash", "shell", "sh", "zsh", "console", "terminal",
        "python", "py", "javascript", "js", "typescript", "ts", "tsx", "jsx",
        "yaml", "yml", "json", "toml",
    }
    for index, match in enumerate(_FENCED_CODE_RE.finditer(source), start=1):
        if len(records) >= max_rows:
            break
        raw_lang = (match.group(1) or "").strip().lower()
        lang = raw_lang.split("+", 1)[0].split(".", 1)[0]
        if lang not in executable_langs:
            continue
        body = (match.group(2) or "").strip()
        if not body or len(body) > 8000:
            continue
        input_edge, output_edge, effects, keys = _snippet_edges(lang, body)
        heading = _doc_heading_before(source, match.start())
        name = f"{heading or path.stem}.snippet_{index}.{lang}"
        first_line = " ".join(body.splitlines()[:2])[:140]
        records.append(_artifact_record(
            path=path,
            source=body,
            artifact_kind="markdown_executable_snippet",
            name=name,
            input_edge=input_edge,
            output_edge=output_edge,
            effects=effects,
            doc=f"Run documented `{lang}` snippet from `{heading or path.name}`: {first_line}.",
            line=source[:match.start()].count("\n") + 1,
            extra_keys=(lang, heading, first_line, *keys),
        ))
    return records


def _shell_records(path: Path, source: str, *, max_rows: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for match in _SHELL_FUNC_RE.finditer(source):
        if len(records) >= max_rows:
            break
        name = match.group(1)
        body = source[match.start():match.start() + 1200]
        input_edge, output_edge, effects, keys = _snippet_edges("bash", body)
        records.append(_artifact_record(
            path=path,
            source=body,
            artifact_kind="shell_function",
            name=name,
            input_edge=input_edge,
            output_edge=output_edge,
            effects=effects or ["subprocess"],
            doc=f"Run shell function `{name}` as a reusable command primitive.",
            line=source[:match.start()].count("\n") + 1,
            extra_keys=(name, *keys),
        ))
    for index, match in enumerate(_SCRIPT_LINE_RE.finditer(source), start=1):
        if len(records) >= max_rows:
            break
        command = f"{match.group(1)}{match.group(2)}".strip()
        input_edge, output_edge, effects, keys = _snippet_edges("bash", command)
        records.append(_artifact_record(
            path=path,
            source=command,
            artifact_kind="shell_command",
            name=f"command.{index}.{match.group(1)}",
            input_edge=input_edge,
            output_edge=output_edge,
            effects=effects or ["subprocess"],
            doc=f"Run shell command `{command[:140]}` as a reusable command primitive.",
            line=source[:match.start()].count("\n") + 1,
            extra_keys=(command, *keys),
        ))
    if not records and source.strip():
        input_edge, output_edge, effects, keys = _snippet_edges("bash", source[:2000])
        records.append(_artifact_record(
            path=path,
            source=source[:2000],
            artifact_kind="shell_script",
            name=path.stem,
            input_edge=input_edge,
            output_edge=output_edge,
            effects=effects or ["subprocess"],
            doc=f"Run shell script `{path.name}` as a reusable command primitive.",
            line=1,
            extra_keys=(path.stem, *keys),
        ))
    return records[:max_rows]


def _taskfile_records(path: Path, source: str, *, max_rows: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    name = path.name.lower()
    regex = _JUST_TARGET_RE if name == "justfile" else _MAKE_TARGET_RE
    for match in regex.finditer(source):
        if len(records) >= max_rows:
            break
        target = match.group(1)
        if target.startswith(".") or target in {"if", "else", "for", "while"}:
            continue
        body = source[match.start():match.start() + 1000]
        input_edge, output_edge, effects, keys = _snippet_edges("bash", body)
        records.append(_artifact_record(
            path=path,
            source=body,
            artifact_kind="command_target",
            name=target,
            input_edge="RepoCheckout+CommandArgs",
            output_edge=output_edge,
            effects=effects or ["subprocess"],
            doc=f"Run command target `{target}` from `{path.name}`.",
            line=source[:match.start()].count("\n") + 1,
            extra_keys=(target, path.name, *keys),
        ))
    return records


def _structured_records_for_file(path: Path, *, max_rows: int) -> list[dict[str, Any]]:
    if path.name.lower() in {"package-lock.json", "pnpm-lock.yaml", "yarn.lock"}:
        return []
    try:
        if path.stat().st_size > DEFAULT_MAX_STRUCTURED_FILE_BYTES:
            return []
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    suffix = path.suffix.lower()
    name = path.name.lower()
    if name == "dockerfile":
        return _dockerfile_records(path, source)
    if name in MAKEFILE_NAMES:
        return _taskfile_records(path, source, max_rows=max_rows)
    if suffix in DOC_SUFFIXES:
        return _markdown_records(path, source, max_rows=max_rows)
    if suffix in SHELL_SUFFIXES:
        return _shell_records(path, source, max_rows=max_rows)
    if suffix == ".json":
        return _json_artifact_records(path, source, max_rows=max_rows)
    if suffix in NOTEBOOK_SUFFIXES:
        return _ipynb_records(path, source, max_rows=max_rows)
    if suffix == ".jsonl":
        return _jsonl_artifact_records(path, source, max_rows=max_rows)
    if suffix in {".yaml", ".yml"}:
        return _yaml_artifact_records(path, source, max_rows=max_rows)
    if suffix == ".tf":
        return _terraform_records(path, source)
    if suffix == ".sql":
        return _sql_records(path, source)
    return []


def scan_structured_tree(
    root: Path,
    *,
    max_files: "int | None" = DEFAULT_MAX_FILES,
    max_records: "int | None" = DEFAULT_MAX_RECORDS,
    exclude_parts: set[str] | None = None,
    max_rows_per_file: int = DEFAULT_MAX_STRUCTURED_ROWS_PER_FILE,
) -> list[dict[str, Any]]:
    root = root.resolve()
    exclude_parts = set(DEFAULT_EXCLUDE_PARTS if exclude_parts is None else exclude_parts)
    records: list[dict[str, Any]] = []
    count_files = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file() or _skip_path(path, exclude_parts):
            continue
        suffix = path.suffix.lower()
        name = path.name.lower()
        if name != "dockerfile" and name not in MAKEFILE_NAMES and suffix not in STRUCTURED_SUFFIXES + DOC_SUFFIXES + SHELL_SUFFIXES:
            continue
        count_files += 1
        if count_files > _cap_or_unbounded(max_files) or len(records) >= _cap_or_unbounded(max_records):
            break
        for record in _structured_records_for_file(path, max_rows=max_rows_per_file):
            records.append(record)
            if len(records) >= _cap_or_unbounded(max_records):
                break
    return records


def scan_source_roots(
    roots: list[Path],
    *,
    max_files: "int | None" = DEFAULT_MAX_FILES,
    max_records: "int | None" = DEFAULT_MAX_RECORDS,
    exclude_parts: set[str] | None = None,
    include_js: bool = True,
    include_structured: bool = True,
    max_structured_rows_per_file: int = DEFAULT_MAX_STRUCTURED_ROWS_PER_FILE,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    per_root_file_limit = max_files
    for root in roots:
        if not root.is_dir():
            continue
        for record in scan_python_tree(root, max_files=per_root_file_limit, max_records=max_records, exclude_parts=exclude_parts):
            key = str(record.get("primitive_id"))
            if key not in seen:
                seen.add(key)
                records.append(record)
            if len(records) >= _cap_or_unbounded(max_records):
                return records
        if include_js:
            for record in scan_js_tree(root, max_files=per_root_file_limit, max_records=max_records, exclude_parts=exclude_parts):
                key = str(record.get("primitive_id"))
                if key not in seen:
                    seen.add(key)
                    records.append(record)
                if len(records) >= _cap_or_unbounded(max_records):
                    return records
        if include_structured:
            for record in scan_structured_tree(
                root,
                max_files=per_root_file_limit,
                max_records=max_records,
                exclude_parts=exclude_parts,
                max_rows_per_file=max_structured_rows_per_file,
            ):
                key = str(record.get("primitive_id"))
                if key not in seen:
                    seen.add(key)
                    records.append(record)
                if len(records) >= _cap_or_unbounded(max_records):
                    return records
    return records


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(_stable_json(row) + "\n")
            count += 1
    return count


def write_outputs(records: list[dict[str, Any]], out: Path, manifest: Path, summary: Path, roots: list[Path]) -> None:
    count = _write_jsonl(out, records)
    mutator_counts: dict[str, int] = {}
    runtime_counts: dict[str, int] = {}
    domain_counts: dict[str, int] = {}
    family_counts: dict[str, int] = {}
    visibility_counts: dict[str, int] = {}
    for record in records:
        for option in record.get("mutations") or []:
            mutator_counts[str(option.get("mutator"))] = mutator_counts.get(str(option.get("mutator")), 0) + 1
        for target in record.get("runtime_targets") or []:
            runtime_counts[str(target)] = runtime_counts.get(str(target), 0) + 1
        for domain in record.get("domains") or ["general_software"]:
            domain_counts[str(domain)] = domain_counts.get(str(domain), 0) + 1
        family_counts[str(record.get("source_family") or "source")] = family_counts.get(str(record.get("source_family") or "source"), 0) + 1
        visibility_counts[str(record.get("surface_visibility") or "unknown")] = visibility_counts.get(str(record.get("surface_visibility") or "unknown"), 0) + 1
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({
        "record_count": count,
        "roots": [str(root) for root in roots],
        "output": str(out),
        "domain_counts": domain_counts,
        "source_family_counts": family_counts,
        "surface_visibility_counts": visibility_counts,
        "mutator_counts": mutator_counts,
        "runtime_target_counts": runtime_counts,
        "candidate": True,
        "serves_truth": False,
        "generated_at": _utc(),
    }, indent=2, sort_keys=True), encoding="utf-8")
    summary.parent.mkdir(parents=True, exist_ok=True)
    top_mutators = ", ".join(f"{key}:{value}" for key, value in sorted(mutator_counts.items())[:12])
    top_runtimes = ", ".join(f"{key}:{value}" for key, value in sorted(runtime_counts.items()))
    top_domains = ", ".join(f"{key}:{value}" for key, value in sorted(domain_counts.items(), key=lambda item: (-item[1], item[0]))[:16])
    top_families = ", ".join(f"{key}:{value}" for key, value in sorted(family_counts.items()))
    top_visibility = ", ".join(f"{key}:{value}" for key, value in sorted(visibility_counts.items()))
    summary.write_text(
        "# AIDevObserver Edge Foundry Summary\n\n"
        f"- Source roots: `{', '.join(str(root) for root in roots)}`\n"
        f"- Primitive candidates: `{count}`\n"
        f"- Output: `{out}`\n"
        f"- Source families: {top_families or 'none'}\n"
        f"- Surface visibility: {top_visibility or 'none'}\n"
        f"- Domains: {top_domains or 'none'}\n"
        f"- Runtime targets: {top_runtimes or 'none'}\n"
        f"- Mutator options: {top_mutators or 'none'}\n\n"
        "All rows are source-backed candidates with `serves_truth=false`.\n",
        encoding="utf-8",
    )


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "demo.py").write_text(
            "from pathlib import Path\n\n"
            "def read_rows(path: Path) -> list[dict[str, str]]:\n"
            "    \"\"\"Read rows from a CSV-like file.\"\"\"\n"
            "    return []\n\n"
            "def emit_response(value: dict[str, object]) -> dict[str, object]:\n"
            "    return {\"ok\": True, \"value\": value}\n\n"
            "def _self_test() -> int:\n"
            "    return 0\n",
            encoding="utf-8",
        )
        tests_dir = root / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_import_flow.py").write_text(
            "def test_import_flow_accepts_required_columns():\n"
            "    assert True\n",
            encoding="utf-8",
        )
        records = scan_python_tree(root)
        js_path = root / "demo.jsx"
        js_path.write_text(
            "export function CsvUploader({onRows}) { return onRows([]); }\n"
            "const routeTicket = (ticket) => ({team: 'support', ticket});\n",
            encoding="utf-8",
        )
        (root / "demo.test.ts").write_text(
            "import { test, expect } from 'vitest';\n"
            "test('routes tickets to support', () => { expect(true).toBe(true); });\n",
            encoding="utf-8",
        )
        (root / "package.json").write_text(
            json.dumps({"scripts": {"test": "pytest", "build": "vite build"}}),
            encoding="utf-8",
        )
        workflow_dir = root / ".github" / "workflows"
        workflow_dir.mkdir(parents=True)
        (workflow_dir / "ci.yml").write_text(
            "name: CI\non: [push]\njobs:\n  test:\n    runs-on: ubuntu-latest\n    steps:\n      - run: pytest\n",
            encoding="utf-8",
        )
        (root / "input.schema.json").write_text(
            json.dumps({"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "DemoInput", "type": "object", "properties": {"name": {"type": "string"}}}),
            encoding="utf-8",
        )
        (root / "README.md").write_text(
            "# Demo workflow\n\n"
            "```bash\n"
            "pytest tests && docker build -t demo .\n"
            "```\n\n"
            "```python\n"
            "print('hello')\n"
            "```\n",
            encoding="utf-8",
        )
        (root / "Makefile").write_text(
            "test:\n\tpytest\n\n"
            "deploy:\n\tkubectl apply -f k8s.yaml\n",
            encoding="utf-8",
        )
        (root / "scripts").mkdir()
        (root / "scripts" / "deploy.sh").write_text(
            "#!/usr/bin/env bash\n"
            "deploy_app() {\n"
            "  kubectl apply -f k8s.yaml\n"
            "}\n"
            "pytest tests\n",
            encoding="utf-8",
        )
        (root / "openapi.json").write_text(
            json.dumps({
                "openapi": "3.1.0",
                "info": {"title": "Demo API"},
                "paths": {
                    "/imports": {
                        "post": {
                            "operationId": "createImport",
                            "summary": "Create an import job",
                        }
                    },
                    "/imports/{id}": {
                        "get": {
                            "operationId": "getImport",
                            "summary": "Read import status",
                        }
                    },
                },
            }),
            encoding="utf-8",
        )
        (root / "workflow.json").write_text(
            json.dumps({
                "name": "Demo n8n workflow",
                "nodes": [
                    {"name": "Webhook", "type": "n8n-nodes-base.webhook"},
                    {"name": "HTTP Request", "type": "n8n-nodes-base.httpRequest"},
                    {"name": "Send Email", "type": "n8n-nodes-base.emailSend"},
                ],
                "connections": {},
            }),
            encoding="utf-8",
        )
        (root / ".mcp.json").write_text(
            json.dumps({"mcpServers": {"demo": {"command": "python", "args": ["server.py"]}}}),
            encoding="utf-8",
        )
        (root / "notebook.ipynb").write_text(
            json.dumps({
                "metadata": {"kernelspec": {"language": "python"}},
                "cells": [
                    {"cell_type": "markdown", "source": ["# Train model\n"]},
                    {"cell_type": "code", "source": ["import pandas as pd\n", "pytest.main([])\n"]},
                ],
            }),
            encoding="utf-8",
        )
        seed_dir = root / "catalog" / "knowledge-packs" / "data" / "aidevobserver-public-codegen-use-cases"
        seed_dir.mkdir(parents=True)
        (seed_dir / "use-cases.jsonl").write_text(
            json.dumps({
                "id": "csv-to-warehouse-ingestion",
                "source_kind": "curated_public_codegen_use_case",
                "title": "CSV to warehouse or parquet ingestion",
                "intent": "Ingest vendor CSV files, validate schema, normalize columns, cast types, write an artifact, and publish metadata.",
                "expected_template": "template.data_ingest_validate_transform_publish",
                "expected_primitives": [
                    "file.read_csv_artifact",
                    "table.validate_schema",
                    "table.rename_columns",
                    "table.write_parquet",
                ],
                "effects": ["fs.read", "fs.write"],
                "serves_truth": False,
            }) + "\n" + json.dumps({
                "id": "auth-login-session",
                "surface_family": "auth_identity",
                "title": "Login, signup, session, password reset, and MFA surfaces",
                "common_actions": ["validate_credentials", "create_session", "send_reset_link"],
                "candidate_templates": ["template.auth_identity_flow"],
                "candidate_primitives": ["auth.validate_credentials", "auth.create_session"],
                "effects": ["db.read", "db.write", "email.send"],
                "serves_truth": False,
            }) + "\n",
            encoding="utf-8",
        )
        records = scan_source_roots([root])
        mutators = {
            str(option.get("mutator"))
            for record in records
            for option in (record.get("mutations") or [])
        }
        route_records = [
            record
            for record in records
            if record.get("kind") == f"artifact.{ARTIFACT_KIND_CAPABILITY_TEMPLATE_ROUTE}"
        ]
        route_blob = json.dumps(route_records, sort_keys=True)
        checks = [
            (len(records) >= 24, "extracts Python, JS, docs, commands, workflow, notebook, and structured artifact records"),
            (records[0]["contract"]["input"] == "Path", "captures input annotation"),
            (records[0]["contract"]["output"] == "list[dict[str, str]]", "captures output annotation"),
            (any(item.get("mutator") == AIDEVOBSERVER_MUTATOR_MAP_SEQUENCE for item in records[1]["mutations"]), "adds scalar map mutator"),
            (all(option.get("mutator_agent_id") for record in records for option in (record.get("mutations") or [])), "adds stable mutator agent ids"),
            (all(option.get("target_edge_template") for record in records for option in (record.get("mutations") or [])), "adds target edge templates for mutators"),
            (AIDEVOBSERVER_MUTATOR_SCHEMA_VALIDATOR_INSERTER in mutators, "adds schema validator insertion mutator"),
            (AIDEVOBSERVER_MUTATOR_API_ENDPOINT_WRAPPER in mutators, "adds API endpoint wrapper mutator"),
            (AIDEVOBSERVER_MUTATOR_CLOUD_FUNCTION_WRAPPER in mutators, "adds cloud function wrapper mutator"),
            (AIDEVOBSERVER_MUTATOR_CLI_WRAPPER in mutators, "adds CLI wrapper mutator"),
            (AIDEVOBSERVER_MUTATOR_BATCH_CHUNKER in mutators, "adds batch chunker mutator"),
            (AIDEVOBSERVER_MUTATOR_K8S_JOB_WRAPPER in mutators, "adds Kubernetes job wrapper mutator"),
            (records[0]["serves_truth"] is False and records[0]["candidate"] is True, "candidate-only truth boundary"),
            (any("app_building_frontend" in row.get("domains", []) for row in records), "adds frontend domain tags"),
            (any(row.get("kind") == "artifact.package_script" for row in records), "extracts package scripts"),
            (any(row.get("kind") == "artifact.ci_workflow" for row in records), "extracts CI workflows"),
            (any(row.get("kind") == "artifact.json_schema" for row in records), "extracts JSON Schemas"),
            (any(row.get("kind") == "artifact.markdown_executable_snippet" for row in records), "extracts documentation executable snippets"),
            (any(row.get("kind") == "artifact.command_target" for row in records), "extracts Makefile/Justfile command targets"),
            (any(row.get("kind") == "artifact.shell_function" for row in records), "extracts shell functions"),
            (any(row.get("kind") == "artifact.openapi_operation" for row in records), "extracts OpenAPI operations"),
            (any(row.get("kind") == "artifact.n8n_node" for row in records), "extracts n8n workflow nodes"),
            (any(row.get("kind") == "artifact.workflow_definition" for row in records), "extracts generic workflow definitions"),
            (any(row.get("kind") == "artifact.mcp_server_binding" for row in records), "extracts MCP server bindings"),
            (any(row.get("kind") == "artifact.notebook_code_cell" for row in records), "extracts notebook code cells"),
            (any(row.get("kind") == "py.proof_fn" for row in records), "extracts Python self-test proof functions"),
            (any(row.get("kind") == "py.test_fn" for row in records), "extracts Python test functions as proof primitives"),
            (any(row.get("kind") == "js.test_case" for row in records), "extracts JS/TS test cases as proof primitives"),
            (any(row.get("output_edge") == "ProofRunReceipt" for row in records), "adds proof receipt output edge"),
            (any(row.get("output_edge") == "TestProofReceipt" for row in records), "adds test proof receipt output edge"),
            (any(row.get("kind") == "artifact.use_case_blueprint" for row in records), "extracts use-case capability blueprints"),
            (any(row.get("kind") == "artifact.microsurface_blueprint" for row in records), "extracts microsurface capability blueprints"),
            (any(row.get("kind") == "artifact.capability_template_route" for row in records), "extracts capability template routes"),
            (any(row.get("kind") == "artifact.capability_slot" for row in records), "extracts capability primitive slots"),
            (any("PipelineRecipe" == row.get("output_edge") for row in records), "adds pipeline recipe output edge"),
            ("package_script_workflow" in route_blob, "adds package script template routes"),
            ("openapi_service" in route_blob, "adds OpenAPI service template routes"),
            ("ci_workflow" in route_blob, "adds CI workflow template routes"),
            ("n8n_workflow" in route_blob, "adds n8n workflow template routes"),
            ("mcp_tool_binding" in route_blob, "adds MCP tool-binding template routes"),
            ("notebook_pipeline" in route_blob, "adds notebook pipeline template routes"),
        ]
        failed = [name for ok, name in checks if not ok]
        if failed:
            for name in failed:
                print(f"FAIL - {name}", file=sys.stderr)
            return 1
        out = root / "out.jsonl"
        manifest = root / "manifest.json"
        summary = root / "summary.md"
        write_outputs(records, out, manifest, summary, [root])
        if not out.exists() or not manifest.exists() or not summary.exists():
            print("FAIL - outputs missing", file=sys.stderr)
            return 1
    print("PASS - aidevobserver_edge_foundry: source-backed code + docs/commands/structured artifacts -> edge cards + mutator hints.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract source-backed primitive edge cards from local source code.")
    parser.add_argument("--root", action="append", default=None, help="Source tree to scan. May be repeated.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="JSONL output path.")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Manifest JSON path.")
    parser.add_argument("--summary", default=str(DEFAULT_SUMMARY), help="Summary Markdown path.")
    parser.add_argument("--exclude", action="append", default=[], help="Path part to exclude. May be repeated.")
    parser.add_argument(
        "--include-part",
        action="append",
        default=[],
        help="Default-excluded path part to re-admit (pair with a bounded --root). May be repeated. --exclude wins on conflict.",
    )
    parser.add_argument("--no-js", action="store_true", help="Disable JavaScript/TypeScript regex scanning.")
    parser.add_argument("--no-structured", action="store_true", help="Disable JSON/YAML/Dockerfile/SQL/Terraform artifact scanning.")
    parser.add_argument("--max-structured-rows-per-file", type=int, default=DEFAULT_MAX_STRUCTURED_ROWS_PER_FILE)
    parser.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES,
                    help="Opt-in file cap (default: unbounded).")
    parser.add_argument("--max-records", type=int, default=DEFAULT_MAX_RECORDS,
                    help="Opt-in record cap (default: unbounded).")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    raw_roots = args.root or ["."]
    roots = [Path(root).expanduser().resolve() for root in raw_roots]
    missing = [str(root) for root in roots if not root.is_dir()]
    if missing:
        print(f"root is not a directory: {', '.join(missing)}", file=sys.stderr)
        return 2
    exclude_parts = (set(DEFAULT_EXCLUDE_PARTS) - {str(item) for item in args.include_part}) | {str(item) for item in args.exclude}
    records = scan_source_roots(
        roots,
        max_files=args.max_files,
        max_records=args.max_records,
        exclude_parts=exclude_parts,
        include_js=not args.no_js,
        include_structured=not args.no_structured,
        max_structured_rows_per_file=max(0, args.max_structured_rows_per_file),
    )
    write_outputs(records, Path(args.out), Path(args.manifest), Path(args.summary), roots)
    print(f"wrote {len(records)} primitive edge cards to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
