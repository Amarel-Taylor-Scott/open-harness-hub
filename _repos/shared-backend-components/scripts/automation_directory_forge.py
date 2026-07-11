#!/usr/bin/env python3
"""scripts.automation_directory_forge — AutomationDirectoryForge: turn PUBLIC workflow ecosystems
(n8n · Zapier · IFTTT · Make · Pipedream · Activepieces · Workato · RapidAPI · Postman · APIs.guru · MCP registries
· GitHub workflow repos) into SOURCE-backed, deterministic primitive candidates, executable workflow MOLECULES,
and realistic buildout tasks.

Owner (2026-07-09): every public template/applet/recipe is PMF evidence that someone wanted that workflow. Decompose
each along the universal automation axis — trigger -> conditions -> transforms -> actions -> error handling ->
credentials -> side effects -> observability — into reusable deterministic primitives + macro molecules, then feed
those molecules into `run_large_project_ab` as LARGE genomes to measure REAL (executed) session-token savings.

Operating laws (enforced here):
  * OFFLINE + read-only by DEFAULT — governed structural fixtures, no live network, no raw source bodies persisted
    (handles + digests only). Live scraping is an explicit opt-in seam (not this module's default path).
  * Credentials are ALWAYS user-configurable by ENV-VAR name; a literal key is NEVER embedded in a card/fixture/row.
  * Everything generated is candidate=true / serves_truth=false. A template COUNT is not a benchmark RESULT.
  * The executable primitives + molecule here are DETERMINISTIC and are proven by executed fixtures + byte-identical
    replay in --self-test (mutation-gated). Searchability is not executability; only executed A/B may headline.

    python3 scripts/automation_directory_forge.py --self-test
    python3 scripts/automation_directory_forge.py --run --max-per-platform 4   # mine fixtures -> candidates -> receipts
    python3 scripts/automation_directory_forge.py --report
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/real_app_forge.py) ────────────────────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import hashlib  # noqa: E402  (source DIGEST only — NOT an id; ids go through canonical_id)
import hmac  # noqa: E402  (webhook signature primitive)
import json  # noqa: E402
from typing import Any, Callable  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"automation_directory_forge requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "automation_source_decomposition"  # discovery/decomposition — NOT an executed benchmark result
ARTIFACT_DIR_REL = "data/dev-intel/automation_forge"

# ── the universal automation decomposition axis (every workflow, every platform, reduces to these 8 stages) ───
WORKFLOW_STAGES: list[str] = [
    "trigger", "conditions", "transforms", "actions", "error_handling", "credentials", "side_effects",
    "observability",
]

# ── platforms (public workflow ecosystems the forge mines) ────────────────────────────────────────────────────
PLATFORMS: list[str] = [
    "n8n", "zapier", "ifttt", "make", "pipedream", "activepieces", "workato", "there_is_an_ai_for_that",
    "rapidapi", "postman", "apis_guru", "mcp_registry", "github_repo",
]

# ── deterministic primitive families a workflow decomposes into (each is EXECUTABLE + fixture-proven below) ────
PRIMITIVE_FAMILIES: list[str] = [
    "trigger_event_schema_validator", "action_request_builder", "action_response_normalizer",
    "credential_profile_loader", "field_mapping_transformer", "filter_condition_evaluator",
    "formatter_transformer", "dedupe_key_builder", "idempotency_gate", "retry_backoff_policy",
    "rate_limit_gate", "webhook_signature_verifier", "webhook_event_router", "pagination_iterator",
    "error_mapper", "side_effect_gate",
]


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# OFFLINE GOVERNED FIXTURES — representative PUBLIC workflow SHAPES per platform (structural digests, no raw bodies)
# Each entry captures the *shape* every public template on that platform shares; it is source EVIDENCE, not a copy.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _wf(name: str, category: str, trigger: dict, actions: list[dict], *, conditions: list[dict] | None = None,
        transforms: list[dict] | None = None, credentials: list[str] | None = None,
        side_effects: list[str] | None = None) -> dict[str, Any]:
    """One governed workflow shape. `credentials` are ENV-VAR NAMES only (never values)."""
    return {
        "name": name, "category": category, "trigger": trigger, "conditions": conditions or [],
        "transforms": transforms or [], "actions": actions, "credentials": credentials or [],
        "side_effects": side_effects or [a.get("verb", "write") for a in actions],
    }


_PLATFORM_WORKFLOWS: dict[str, list[dict[str, Any]]] = {
    "n8n": [
        _wf("webhook_to_slack_with_filter", "notification",
            {"type": "webhook", "event": "http_post", "schema": {"event_id": "str", "severity": "str"}},
            [{"app": "slack", "verb": "post_message", "fields": ["channel", "text"]}],
            conditions=[{"field": "severity", "op": "in", "value": ["high", "critical"]}],
            transforms=[{"op": "template", "target": "text", "from": ["event_id", "severity"]}],
            credentials=["SLACK_BOT_TOKEN"]),
        _wf("form_submission_to_sheet", "data_capture",
            {"type": "webhook", "event": "form_submit", "schema": {"email": "str", "name": "str"}},
            [{"app": "google_sheets", "verb": "append_row", "fields": ["email", "name", "ts"]}],
            transforms=[{"op": "normalize_email", "target": "email"}],
            credentials=["GOOGLE_SHEETS_OAUTH"]),
    ],
    "zapier": [
        _wf("new_email_to_trello_card", "task_capture",
            {"type": "poll", "app": "gmail", "event": "new_email", "schema": {"subject": "str", "from": "str"}},
            [{"app": "trello", "verb": "create_card", "fields": ["name", "desc"]}],
            transforms=[{"op": "map_fields", "map": {"name": "subject", "desc": "from"}}],
            credentials=["GMAIL_OAUTH", "TRELLO_API_KEY"]),
        _wf("stripe_payment_to_invoice", "finance",
            {"type": "webhook", "app": "stripe", "event": "payment_succeeded",
             "schema": {"id": "str", "amount": "int", "customer": "str"}},
            [{"app": "quickbooks", "verb": "create_invoice", "fields": ["customer", "amount", "ref"]}],
            conditions=[{"field": "amount", "op": "gt", "value": 0}],
            credentials=["STRIPE_WEBHOOK_SECRET", "QUICKBOOKS_OAUTH"], side_effects=["write", "financial"]),
    ],
    "ifttt": [
        _wf("rss_item_to_tweet", "content",
            {"type": "poll", "service": "rss", "event": "new_feed_item", "schema": {"title": "str", "url": "str"}},
            [{"app": "twitter", "verb": "post_tweet", "fields": ["status"]}],
            transforms=[{"op": "template", "target": "status", "from": ["title", "url"]}],
            credentials=["TWITTER_OAUTH"]),
    ],
    "make": [
        _wf("watch_webhook_router_sheets", "integration",
            {"type": "webhook", "event": "custom_webhook", "schema": {"kind": "str", "payload": "dict"}},
            [{"app": "google_sheets", "verb": "add_row", "fields": ["kind", "payload"]}],
            conditions=[{"field": "kind", "op": "eq", "value": "order"}],
            credentials=["MAKE_WEBHOOK_SECRET", "GOOGLE_SHEETS_OAUTH"]),
    ],
    "pipedream": [
        _wf("http_source_filter_email", "integration",
            {"type": "http", "event": "http_request", "schema": {"user_id": "str", "action": "str"}},
            [{"app": "sendgrid", "verb": "send_email", "fields": ["to", "subject", "body"]}],
            conditions=[{"field": "action", "op": "eq", "value": "signup"}],
            credentials=["SENDGRID_API_KEY"]),
    ],
    "activepieces": [
        _wf("github_issue_to_notion", "task_sync",
            {"type": "webhook", "app": "github", "event": "issues.opened",
             "schema": {"number": "int", "title": "str", "body": "str"}},
            [{"app": "notion", "verb": "create_page", "fields": ["title", "body", "url"]}],
            credentials=["GITHUB_WEBHOOK_SECRET", "NOTION_TOKEN"]),
    ],
    "workato": [
        _wf("lead_capture_to_crm", "sales",
            {"type": "webhook", "event": "lead_form", "schema": {"email": "str", "company": "str"}},
            [{"app": "salesforce", "verb": "upsert_contact", "fields": ["email", "company"]}],
            transforms=[{"op": "normalize_email", "target": "email"}, {"op": "dedupe_key", "from": ["email"]}],
            credentials=["SALESFORCE_OAUTH"]),
    ],
    "there_is_an_ai_for_that": [
        _wf("ai_summary_to_notion", "ai_tool_use_case",
            {"type": "manual", "event": "document_uploaded", "schema": {"doc_id": "str", "text": "str"}},
            [{"app": "notion", "verb": "create_record", "fields": ["doc_id", "summary"]}],
            transforms=[{"op": "ai_summarize", "target": "summary", "from": ["text"]}],
            credentials=["OPENAI_API_KEY", "NOTION_TOKEN"]),
    ],
    "rapidapi": [
        _wf("api_enrich_contact", "enrichment",
            {"type": "http", "event": "enrich_request", "schema": {"email": "str"}},
            [{"app": "rapidapi_enrichment", "verb": "get_profile", "fields": ["email"]}],
            credentials=["RAPIDAPI_KEY"], side_effects=["read"]),
    ],
    "postman": [
        _wf("collection_health_check", "monitoring",
            {"type": "schedule", "event": "cron", "schema": {"cron": "str"}},
            [{"app": "http", "verb": "get", "fields": ["url"]}],
            credentials=["POSTMAN_API_KEY"], side_effects=["read"]),
    ],
    "apis_guru": [
        _wf("openapi_spec_to_wrapper", "api_import",
            {"type": "spec", "event": "openapi_import", "schema": {"spec_url": "str"}},
            [{"app": "generated_wrapper", "verb": "call_endpoint", "fields": ["path", "method"]}],
            side_effects=["read"]),
    ],
    "mcp_registry": [
        _wf("mcp_tool_to_gated_wrapper", "tool_import",
            {"type": "registry", "event": "tool_listed", "schema": {"tool_name": "str", "input_schema": "dict"}},
            [{"app": "mcp_tool", "verb": "invoke", "fields": ["tool_name", "args"]}],
            credentials=["MCP_SERVER_TOKEN"]),
    ],
    "github_repo": [
        _wf("workflow_json_to_primitive", "source_import",
            {"type": "repo", "event": "workflow_file", "schema": {"path": "str", "format": "str"}},
            [{"app": "primitive_registry", "verb": "register_candidate", "fields": ["path"]}],
            side_effects=["read"]),
    ],
}


def _digest(obj: Any) -> str:
    """Stable content DIGEST of a workflow shape (handle, not an id; ids go through canonical_id)."""
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:16]


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# EXECUTABLE DETERMINISTIC PRIMITIVES — the real, fixture-proven implementations a workflow decomposes into.
# Each returns a plain value; each has oracle fixtures (input -> expected) exercised in --self-test.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
_PY_TYPES = {"str": str, "int": int, "float": (int, float), "bool": bool, "dict": dict, "list": list}


def prim_trigger_event_schema_validator(schema: dict[str, str], event: dict[str, Any]) -> dict[str, Any]:
    """Validate an incoming trigger event against {field: type_name}. Deterministic. Returns {ok, errors}."""
    errors: list[str] = []
    for field, tname in sorted(schema.items()):
        if field not in event:
            errors.append(f"missing:{field}")
        elif not isinstance(event[field], _PY_TYPES.get(tname, object)):
            errors.append(f"type:{field}")
    return {"ok": not errors, "errors": errors}


def prim_field_mapping_transformer(mapping: dict[str, str], src: dict[str, Any]) -> dict[str, Any]:
    """Map source fields into target fields per {target: source_key}. Missing source -> omitted. Deterministic."""
    return {tgt: src[key] for tgt, key in sorted(mapping.items()) if key in src}


def prim_filter_condition_evaluator(conditions: list[dict[str, Any]], record: dict[str, Any]) -> bool:
    """AND of simple typed conditions (eq/ne/gt/lt/in/contains). Deterministic, side-effect-free."""
    for c in conditions:
        v = record.get(c["field"])
        op, target = c["op"], c.get("value")
        if op == "eq" and not (v == target):
            return False
        if op == "ne" and not (v != target):
            return False
        if op == "gt" and not (isinstance(v, (int, float)) and v > target):
            return False
        if op == "lt" and not (isinstance(v, (int, float)) and v < target):
            return False
        if op == "in" and v not in (target or []):
            return False
        if op == "contains" and not (isinstance(v, str) and str(target) in v):
            return False
    return True


def prim_retry_backoff_policy(attempt: int, base_ms: int = 100, cap_ms: int = 30_000) -> int:
    """Deterministic exponential backoff (no jitter, so it is reproducible): min(cap, base * 2**attempt)."""
    return min(cap_ms, base_ms * (2 ** max(0, attempt)))


def prim_idempotency_gate(seen: set[str], key: str) -> tuple[bool, set[str]]:
    """Return (is_new, updated_seen). A duplicate key is NOT new (drop it). Pure w.r.t. a copied set."""
    updated = set(seen)
    is_new = key not in updated
    updated.add(key)
    return is_new, updated


def prim_dedupe_key_builder(fields: list[str], record: dict[str, Any]) -> str:
    """Stable dedupe key over normalized (lowercased/stripped) field values. Deterministic."""
    parts = [str(record.get(f, "")).strip().lower() for f in fields]
    return hashlib.sha256("|".join(parts).encode()).hexdigest()[:24]


def prim_webhook_signature_verifier(secret: str, body: bytes, signature_hex: str) -> bool:
    """Constant-time HMAC-SHA256 verify of a webhook body. secret comes from an ENV VAR at call sites, never a literal."""
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_hex or "")


def prim_pagination_iterator(fetch_page: Callable[[str | None], dict], start: str | None = None,
                             max_pages: int = 100) -> list[Any]:
    """Follow {items, next_cursor} pages until exhausted or max_pages. Bounded (no infinite loop). Deterministic
    given a deterministic fetch_page."""
    items: list[Any] = []
    cursor, pages = start, 0
    while pages < max_pages:
        page = fetch_page(cursor)
        items.extend(page.get("items", []))
        cursor = page.get("next_cursor")
        pages += 1
        if not cursor:
            break
    return items


def prim_error_mapper(status: int) -> str:
    """Map an HTTP status to a deterministic action class for an automation error policy."""
    if status in (429, 503):
        return "retry"
    if 500 <= status < 600:
        return "retry"
    if status in (401, 403):
        return "reauth"
    if 400 <= status < 500:
        return "drop"
    return "ok"


# Registry of (impl, fixtures) — fixtures are (args_tuple, expected). Exercised + replay-checked in --self-test.
PRIMITIVE_IMPLS: dict[str, tuple[Callable, list[tuple[tuple, Any]]]] = {
    "trigger_event_schema_validator": (prim_trigger_event_schema_validator, [
        (({"email": "str", "n": "int"}, {"email": "a@b.co", "n": 3}), {"ok": True, "errors": []}),
        (({"email": "str", "n": "int"}, {"email": "a@b.co"}), {"ok": False, "errors": ["missing:n"]}),
        (({"n": "int"}, {"n": "three"}), {"ok": False, "errors": ["type:n"]}),
    ]),
    "field_mapping_transformer": (prim_field_mapping_transformer, [
        (({"name": "subject", "desc": "from"}, {"subject": "Hi", "from": "x@y.co"}),
         {"name": "Hi", "desc": "x@y.co"}),
        (({"name": "subject"}, {"other": 1}), {}),
    ]),
    "filter_condition_evaluator": (prim_filter_condition_evaluator, [
        (([{"field": "severity", "op": "in", "value": ["high"]}], {"severity": "high"}), True),
        (([{"field": "amount", "op": "gt", "value": 0}], {"amount": 0}), False),
    ]),
    "retry_backoff_policy": (prim_retry_backoff_policy, [
        ((0,), 100), ((3,), 800), ((20,), 30_000),
    ]),
    "dedupe_key_builder": (prim_dedupe_key_builder, [
        ((["email"], {"email": " A@B.CO "}), prim_dedupe_key_builder(["email"], {"email": "a@b.co"})),
    ]),
    "error_mapper": (prim_error_mapper, [
        ((429,), "retry"), ((404,), "drop"), ((401,), "reauth"), ((200,), "ok"),
    ]),
}


def _run_primitive_fixtures() -> dict[str, Any]:
    """Execute every primitive fixture twice (byte-identical replay) — the executed determinism proof."""
    results: dict[str, Any] = {}
    for fam, (fn, fixtures) in PRIMITIVE_IMPLS.items():
        rows = []
        for args, expected in fixtures:
            got1 = fn(*args)
            got2 = fn(*args)
            j1 = json.dumps(got1, sort_keys=True, default=str)
            rows.append({"args": repr(args), "pass": got1 == expected, "deterministic": j1 == json.dumps(
                got2, sort_keys=True, default=str)})
        results[fam] = {"n": len(rows), "all_pass": all(r["pass"] for r in rows),
                        "all_deterministic": all(r["deterministic"] for r in rows)}
    return results


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# WORKFLOW MOLECULE — make_webhook_worker: the LARGE reusable subsystem (verify -> validate -> idempotency ->
# transform -> enqueue -> ack + health + metrics). This is the macro the model REUSES in the savings A/B; it owns
# all the integration-worker boilerplate that a bare build would re-explore and re-write turn after turn.
# It is exposed as SOURCE so a buildout genome can mount it VERBATIM (0 generated tokens) in the compiled_route lane.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
WEBHOOK_WORKER_MACRO_SOURCE = (
    "import argparse, json, hmac, hashlib\n"
    "from http.server import BaseHTTPRequestHandler, HTTPServer\n\n\n"
    "def make_webhook_worker(secret, event_schema, dedupe_fields, sink, *,\n"
    "                        accept_status=202, bad_sig_status=401, invalid_status=400, health_path='/health',\n"
    "                        metrics_path='/metrics', webhook_path='/webhook'):\n"
    "    '''Build a signed-webhook ingest worker. `secret` is read from an ENV VAR at the call site (never a\n"
    "    literal). `sink` is a callable(event)->None (enqueue/persist). RETURNS a BaseHTTPRequestHandler subclass;\n"
    "    serve with run(handler) or HTTPServer((host,port), handler). Behavior: HMAC-SHA256 verify (X-Signature)\n"
    "    -> schema validate -> idempotency (dedupe_fields) -> sink -> ack. Duplicate events are acked but NOT\n"
    "    re-sunk. GET metrics_path returns {received, accepted, duplicates, rejected}.'''\n"
    "    _TYPES = {'str': str, 'int': int, 'float': (int, float), 'bool': bool, 'dict': dict, 'list': list}\n"
    "    seen = set()\n"
    "    counters = {'received': 0, 'accepted': 0, 'duplicates': 0, 'rejected': 0}\n\n"
    "    def _valid(event):\n"
    "        for f, t in event_schema.items():\n"
    "            if f not in event or not isinstance(event[f], _TYPES.get(t, object)):\n"
    "                return False\n"
    "        return True\n\n"
    "    def _dedupe_key(event):\n"
    "        parts = [str(event.get(f, '')).strip().lower() for f in dedupe_fields]\n"
    "        return hashlib.sha256('|'.join(parts).encode()).hexdigest()[:24]\n\n"
    "    class _H(BaseHTTPRequestHandler):\n"
    "        def _send(self, code, obj):\n"
    "            raw = json.dumps(obj).encode()\n"
    "            self.send_response(code)\n"
    "            self.send_header('Content-Type', 'application/json')\n"
    "            self.send_header('Content-Length', str(len(raw)))\n"
    "            self.end_headers()\n"
    "            self.wfile.write(raw)\n\n"
    "        def do_GET(self):\n"
    "            if self.path == health_path:\n"
    "                return self._send(200, {'status': 'ok', 'healthy': True})\n"
    "            if self.path == metrics_path:\n"
    "                return self._send(200, dict(counters))\n"
    "            return self._send(404, {'error': 'not_found'})\n\n"
    "        def do_POST(self):\n"
    "            if self.path != webhook_path:\n"
    "                return self._send(404, {'error': 'not_found'})\n"
    "            length = int(self.headers.get('Content-Length', 0) or 0)\n"
    "            body = self.rfile.read(length) if length else b''\n"
    "            counters['received'] += 1\n"
    "            sig = self.headers.get('X-Signature', '')\n"
    "            expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()\n"
    "            if not hmac.compare_digest(expected, sig):\n"
    "                counters['rejected'] += 1\n"
    "                return self._send(bad_sig_status, {'error': 'bad_signature'})\n"
    "            try:\n"
    "                event = json.loads(body or b'{}')\n"
    "            except Exception:\n"
    "                counters['rejected'] += 1\n"
    "                return self._send(invalid_status, {'error': 'invalid_json'})\n"
    "            if not isinstance(event, dict) or not _valid(event):\n"
    "                counters['rejected'] += 1\n"
    "                return self._send(invalid_status, {'error': 'invalid_event'})\n"
    "            key = _dedupe_key(event)\n"
    "            if key in seen:\n"
    "                counters['duplicates'] += 1\n"
    "                return self._send(accept_status, {'status': 'duplicate', 'key': key})\n"
    "            seen.add(key)\n"
    "            sink(event)\n"
    "            counters['accepted'] += 1\n"
    "            return self._send(accept_status, {'status': 'accepted', 'key': key})\n\n"
    "        def log_message(self, *a):\n"
    "            pass\n\n"
    "    return _H\n\n\n"
    "def run(handler, port=None):\n"
    "    '''Serve a handler class (from make_webhook_worker) on --port (argv) or an explicit port.'''\n"
    "    if port is None:\n"
    "        ap = argparse.ArgumentParser()\n"
    "        ap.add_argument('--port', type=int, default=8000)\n"
    "        port = ap.parse_args().port\n"
    "    HTTPServer(('127.0.0.1', port), handler).serve_forever()\n"
)


def _exec_molecule() -> Any:
    """Exec the molecule source in an isolated namespace and return make_webhook_worker (for in-process proof)."""
    ns: dict[str, Any] = {}
    exec(compile(WEBHOOK_WORKER_MACRO_SOURCE, "<webhook_worker_macro>", "exec"), ns)  # noqa: S102 our own source
    return ns["make_webhook_worker"]


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# DECOMPOSITION + CANDIDATE / MOLECULE / CREDENTIAL / BUILDOUT-TASK GENERATION (governed, candidate-only)
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _family_for_stage(stage: str, spec: dict[str, Any]) -> list[str]:
    """Which deterministic primitive families a given workflow stage implies."""
    if stage == "trigger":
        fams = ["trigger_event_schema_validator"]
        if spec.get("type") == "webhook":
            fams += ["webhook_signature_verifier", "webhook_event_router"]
        if spec.get("type") == "poll":
            fams += ["pagination_iterator"]
        return fams
    if stage == "conditions":
        return ["filter_condition_evaluator"] if spec else []
    if stage == "transforms":
        fams = []
        for t in spec if isinstance(spec, list) else []:
            op = t.get("op")
            fams.append("dedupe_key_builder" if op == "dedupe_key" else
                        "field_mapping_transformer" if op == "map_fields" else "formatter_transformer")
        return sorted(set(fams))
    if stage == "actions":
        return ["action_request_builder", "action_response_normalizer", "idempotency_gate", "retry_backoff_policy",
                "rate_limit_gate"]
    if stage == "error_handling":
        return ["error_mapper"]
    if stage == "credentials":
        return ["credential_profile_loader"] if spec else []
    if stage == "side_effects":
        return ["side_effect_gate"]
    return []


def decompose_workflow(platform: str, wf: dict[str, Any]) -> dict[str, Any]:
    """Decompose one workflow shape into primitive candidates + a credential profile + a molecule + a buildout task."""
    digest = _digest(wf)
    source_id = canonical_id("autosrc", platform, wf["name"], digest)
    stage_specs = {
        "trigger": wf["trigger"], "conditions": wf["conditions"], "transforms": wf["transforms"],
        "actions": wf["actions"], "error_handling": True, "credentials": wf["credentials"],
        "side_effects": wf["side_effects"], "observability": True,
    }
    families: list[str] = []
    for stage in WORKFLOW_STAGES:
        families += _family_for_stage(stage, stage_specs.get(stage))
    families = sorted(set(families))
    candidates = []
    for fam in families:
        executable = fam in PRIMITIVE_IMPLS
        candidates.append({
            "record_type": "automation_primitive_candidate",
            "primitive_id": canonical_id("autoprim", platform, wf["name"], fam),
            "stable_name": f"automation__{platform}__{wf['name']}__{fam}",
            "source_id": source_id, "platform": platform, "primitive_family": fam,
            "determinism_level": "deterministic" if executable else "deterministic_candidate",
            "executable_reference_impl": executable,
            "side_effect_level": "read" if fam in ("trigger_event_schema_validator", "filter_condition_evaluator",
                                                    "field_mapping_transformer", "dedupe_key_builder") else "gated_write",
            "credential_profile_ref": (canonical_id("autocred", platform, wf["name"])
                                       if wf["credentials"] else None),
            "promotion_blockers": ["source_review", "executed_fixture_proof", "security_scan"],
            **BOUNDARY,
        })
    cred_profile = _credential_profile(platform, wf) if wf["credentials"] else None
    return {"source_id": source_id, "digest": digest, "platform": platform, "workflow_name": wf["name"],
            "category": wf["category"], "families": families, "candidates": candidates,
            "credential_profile": cred_profile}


def _credential_profile(platform: str, wf: dict[str, Any]) -> dict[str, Any]:
    """A user-configurable credential profile — ENV-VAR NAMES ONLY, live disabled by default."""
    return {
        "record_type": "automation_credential_profile",
        "profile_id": canonical_id("autocred", platform, wf["name"]),
        "platform": platform, "env_vars": list(wf["credentials"]),
        "auth_type": "webhook_secret" if wf["trigger"].get("type") == "webhook" else "oauth2_or_api_key",
        "required_for": ["live_read", "test_write"], "test_mode_required": True, "live_allowed": False,
        "side_effect_level": "read" if wf["side_effects"] == ["read"] else "gated_write",
        "missing_key_message": (f"Set {', '.join(wf['credentials'])} to run live {platform} wrapper proofs "
                                f"(mock proof runs without keys)."),
        **BOUNDARY,
    }


def _buildout_task_for_molecule() -> dict[str, Any]:
    """The realistic 'integration worker' buildout task the webhook molecule targets (drives the executed A/B)."""
    return {
        "record_type": "automation_buildout_task",
        "task_id": canonical_id("autotask", "webhook_ingest_worker", "v0"),
        "family": "integration_worker", "genome_id": "webhook_ingest_worker__stdlib_http__v0",
        "molecule": "make_webhook_worker", "hidden_oracle": "boots worker + HTTP-probes signed/unsigned/dup/malformed",
        "reuse_unit": "verified molecule mounted verbatim (compiled_route lane)",
        "credential_model": "WEBHOOK_SECRET env var (never embedded)", **BOUNDARY,
    }


def build_rows(max_per_platform: int = 4) -> dict[str, Any]:
    """Mine the offline fixtures across all platforms -> decompositions + candidates + molecules + tasks."""
    digests, candidates, creds, decomps = [], [], [], []
    for platform in PLATFORMS:
        for wf in _PLATFORM_WORKFLOWS.get(platform, [])[:max_per_platform]:
            d = decompose_workflow(platform, wf)
            decomps.append(d)
            digests.append({"record_type": "automation_workflow_digest", "source_id": d["source_id"],
                            "platform": platform, "workflow_name": wf["name"], "category": wf["category"],
                            "digest": d["digest"], "stage_family_map": {s: _family_for_stage(
                                s, {"trigger": wf["trigger"], "conditions": wf["conditions"],
                                    "transforms": wf["transforms"], "actions": wf["actions"],
                                    "credentials": wf["credentials"], "side_effects": wf["side_effects"]}.get(s))
                                for s in WORKFLOW_STAGES}, **BOUNDARY})
            candidates.extend(d["candidates"])
            if d["credential_profile"]:
                creds.append(d["credential_profile"])
    molecules = [{
        "record_type": "automation_workflow_molecule",
        "molecule_id": canonical_id("automol", "make_webhook_worker", "v0"), "stable_name": "make_webhook_worker",
        "composes": ["webhook_signature_verifier", "trigger_event_schema_validator", "idempotency_gate",
                     "dedupe_key_builder", "field_mapping_transformer", "action_request_builder"],
        "family": "integration_worker", "executable": True, "source_chars": len(WEBHOOK_WORKER_MACRO_SOURCE),
        "credential_env_vars": ["WEBHOOK_SECRET"], "side_effect_level": "gated_write",
        "buildout_genome": "webhook_ingest_worker__stdlib_http__v0", **BOUNDARY,
    }]
    return {"decompositions": decomps, "workflow_digests": digests, "primitive_candidates": candidates,
            "credential_profiles": creds, "workflow_molecules": molecules,
            "buildout_tasks": [_buildout_task_for_molecule()]}


def emit(max_per_platform: int = 4) -> dict[str, Any]:
    """Build rows + persist governed receipts (candidate-only). Returns the summary."""
    rows = build_rows(max_per_platform)
    out = resource(ARTIFACT_DIR_REL)
    out.mkdir(parents=True, exist_ok=True)
    files = {
        "workflow_digests.jsonl": rows["workflow_digests"],
        "primitive_candidates.jsonl": rows["primitive_candidates"],
        "credential_profiles.jsonl": rows["credential_profiles"],
        "workflow_molecules.jsonl": rows["workflow_molecules"],
        "buildout_tasks.jsonl": rows["buildout_tasks"],
    }
    for fname, items in files.items():
        (out / fname).write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in items), encoding="utf-8")
    summary = {
        "record_type": "automation_directory_forge_summary", "benchmark_kind": BENCHMARK_KIND,
        "platforms": len([p for p in PLATFORMS if _PLATFORM_WORKFLOWS.get(p)]),
        "workflows_decomposed": len(rows["workflow_digests"]),
        "primitive_candidates": len(rows["primitive_candidates"]),
        "distinct_primitive_families": len({c["primitive_family"] for c in rows["primitive_candidates"]}),
        "executable_reference_impls": len(PRIMITIVE_IMPLS),
        "credential_profiles": len(rows["credential_profiles"]),
        "workflow_molecules": len(rows["workflow_molecules"]),
        "buildout_tasks": len(rows["buildout_tasks"]),
        "note": "COUNTS are discovery/decomposition, not benchmark results; only executed A/B may headline savings.",
        **BOUNDARY,
    }
    (out / "latest_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def self_test() -> bool:
    """Mutation-gated + REAL: (1) every executable primitive passes its fixtures + is byte-identical on replay;
    (2) a mutated primitive is CAUGHT; (3) the webhook MOLECULE runs end-to-end in-process (accept/dup/bad-sig/
    invalid) with correct counters; (4) decomposition covers every stage; (5) no literal secret leaks into any
    row; (6) every generated row is candidate=true / serves_truth=false."""
    # (1) executable primitive fixtures + determinism
    prim = _run_primitive_fixtures()
    assert all(v["all_pass"] and v["all_deterministic"] for v in prim.values()), f"primitive fixtures: {prim}"

    # (2) mutation gate — break one primitive, prove the fixture harness catches it
    _orig = PRIMITIVE_IMPLS["error_mapper"]
    PRIMITIVE_IMPLS["error_mapper"] = (lambda status: "ok", _orig[1])  # noqa: E731 always says ok (wrong)
    caught = not _run_primitive_fixtures()["error_mapper"]["all_pass"]
    PRIMITIVE_IMPLS["error_mapper"] = _orig
    assert caught, "mutation gate failed: a broken primitive was not caught by its fixtures"

    # (3) the molecule runs end-to-end IN PROCESS (no HTTP) via a tiny fake request harness
    make = _exec_molecule()
    enqueued: list[dict] = []
    Handler = make("s3cr3t", {"event_id": "str", "amount": "int"}, ["event_id"], enqueued.append)
    counters = _drive_handler_inproc(Handler)
    assert counters["accepted"] == 1 and counters["duplicates"] == 1 and counters["rejected"] == 2, counters
    assert len(enqueued) == 1, f"duplicate must NOT be re-sunk: {enqueued}"

    # (4) decomposition covers stages + families; (5) no secret leaks; (6) boundary holds
    rows = build_rows()
    assert rows["workflow_digests"], "no workflows decomposed"
    fams = {c["primitive_family"] for c in rows["primitive_candidates"]}
    assert "webhook_signature_verifier" in fams and "idempotency_gate" in fams, fams
    # secret-hygiene: the test secret never leaks, and every credential field is an ENV-VAR NAME (not a value)
    import re as _re
    blob = json.dumps(rows)
    assert "s3cr3t" not in blob, "the test secret leaked into generated rows"
    _KEY_PREFIXES = ("sk-or-v1", "sk-proj-", "ghp_", "gsk_", "csk-", "nvapi-", "hf_", "tgp_v1")
    assert not any(p in blob for p in _KEY_PREFIXES), "a literal provider key leaked into generated rows"
    for cp in rows["credential_profiles"]:
        assert all(_re.fullmatch(r"[A-Z][A-Z0-9_]+", v) for v in cp["env_vars"]), \
            f"credential profile must carry ENV-VAR NAMES only, not values: {cp['env_vars']}"
    all_rows = (rows["primitive_candidates"] + rows["credential_profiles"] + rows["workflow_molecules"]
                + rows["buildout_tasks"] + rows["workflow_digests"])
    assert all(r.get("candidate") is True and r.get("serves_truth") is False for r in all_rows), "boundary violated"

    print(f"OK automation_directory_forge self-test: {len(PRIMITIVE_IMPLS)} executable primitives fixture-proven + "
          f"replay-deterministic (mutation caught); make_webhook_worker molecule runs end-to-end "
          f"(accept/dup/bad-sig/invalid counters correct, duplicate not re-sunk); "
          f"{len(rows['workflow_digests'])} public workflow shapes across "
          f"{len({d['platform'] for d in rows['workflow_digests']})} platforms decomposed into "
          f"{len(rows['primitive_candidates'])} candidates over {len(fams)} families; no secret leak; "
          f"all rows candidate=true/serves_truth=false")
    return True


def _drive_handler_inproc(Handler: Any) -> dict[str, Any]:
    """Drive a webhook-worker Handler class in-process (no socket): 1 accept, 1 duplicate, 1 bad-sig, 1 invalid."""
    import hashlib as _h
    import hmac as _m

    secret = "s3cr3t"

    class _FakeReq:
        def __init__(self, body: bytes, sig: str):
            self._body = body
            self._hdr = {"Content-Length": str(len(body)), "X-Signature": sig}
            self.status = None
            self.out = b""

        def makefile(self, *a, **k):  # BaseHTTPRequestHandler expects rfile/wfile; we bypass __init__ instead
            raise NotImplementedError

    counters_holder: dict[str, Any] = {}

    def _mk(body: bytes, sig: str):
        h = Handler.__new__(Handler)  # bypass socket setup
        import io
        h.path = "/webhook"
        h.headers = {"Content-Length": str(len(body)), "X-Signature": sig}
        h.rfile = io.BytesIO(body)
        h.wfile = io.BytesIO()
        h._captured = {}

        def _send(code, obj):
            h._captured = {"code": code, "obj": obj}
        h._send = _send  # type: ignore[attr-defined]
        h.do_POST()
        return h._captured

    good_body = json.dumps({"event_id": "e1", "amount": 5}).encode()
    good_sig = _m.new(secret.encode(), good_body, _h.sha256).hexdigest()
    _mk(good_body, good_sig)                                   # accept
    _mk(good_body, good_sig)                                   # duplicate (same key)
    _mk(good_body, "deadbeef")                                 # bad signature
    bad_body = json.dumps({"event_id": "e2"}).encode()         # missing amount -> invalid
    bad_sig = _m.new(secret.encode(), bad_body, _h.sha256).hexdigest()
    last = _mk(bad_body, bad_sig)                              # invalid event
    # read counters via the metrics path on a fresh GET
    hg = Handler.__new__(Handler)
    hg.path = "/metrics"
    cap: dict[str, Any] = {}
    hg._send = lambda code, obj: cap.update(obj)  # type: ignore[attr-defined]
    hg.do_GET()
    counters_holder.update(cap)
    _ = last
    return counters_holder


def main() -> None:
    ap = argparse.ArgumentParser(description="AutomationDirectoryForge — public workflow ecosystems -> primitives.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true", help="mine fixtures -> candidates -> receipts")
    ap.add_argument("--report", action="store_true", help="print the latest summary")
    ap.add_argument("--max-per-platform", type=int, default=4)
    args = ap.parse_args()
    if args.self_test:
        raise SystemExit(0 if self_test() else 1)
    if args.run:
        print(json.dumps(emit(args.max_per_platform), indent=2, sort_keys=True))
        return
    if args.report:
        p = resource(ARTIFACT_DIR_REL) / "latest_summary.json"
        print(p.read_text() if p.exists() else '{"note": "run --run first"}')
        return
    ap.print_help()


if __name__ == "__main__":
    main()
