#!/usr/bin/env python3
"""scripts.domain_med_message_shapes — WORKABLE (proven + TYPED) deterministic MESSAGE-SHAPE leaves.

ADD-ONLY parallel path (its OWN shard file). It IMPORTS the shared machinery, never edits it:
  * `run_primitive_proof` / `MUTATOR_REGISTRY` / `_receipt` from `scripts.mutator_registry` — the proof-runner EXECUTES
    each pure mutator against a synthetic fixture and flips serves_truth false->true ONLY on a PASSING executed proof;
  * `canonicalize_edge` from `scripts.build_edge_type_retrofit` — folds each leaf's logical edge labels to canonical
    type_ids so every proven leaf is also TYPED (input_edge_type_id + output_edge_type_id) and can chain.

Covers deterministic message-SHAPE builders/parsers/validators (SYNTHETIC fixtures, NO real secrets/PII/PAN/SSN):
  SQL SELECT/WHERE/INSERT/ORDER-BY clause builder (PARAMETRIZED — value placeholders, never string-concat) + parse ·
  GraphQL query/variables request envelope + operation-name/type extraction · gRPC method-path + protobuf status shape ·
  webhook payload parse (GitHub-shape + Stripe-shape, synthetic) · queue-message envelope (Kafka ProducerRecord + SQS
  batch-entry shape) · CloudEvents envelope + validation · time-series point (metric,ts,value,tags) + InfluxDB line +
  Prometheus sample · OpenTelemetry-span shape. Every mutator operates on the SHAPE only — no live send ever happens.

DOMAIN LAWS honored: NO insurance primitives (any domain); NO healthcare-clinical work (this is message plumbing, not a
health domain — the 'med' tag is 'message' shapes); synthetic/public shapes only — table/column/topic/metric names are
fabricated, and NO real PII / PAN / SSN / secret ever appears (the SQL builders are PARAMETRIZED so values are
placeholders, not concatenated). NETWORK/EFFECTFUL CALLS (execute a query against a DB, POST a GraphQL/webhook request,
make a gRPC unary call, produce to Kafka, emit a CloudEvent over HTTP, write to InfluxDB / Prometheus remote_write,
export an OTLP span) are NEVER run through the proof runner and NEVER serve_truth — they are declared as GATED-EFFECT
candidates (candidate=true, serves_truth=false, effect, proof_obligation) in a SEPARATE section of the shard, with
SEPARATE honest counts.

Deterministic + offline: no network, no LLM, no wall-clock, no RNG (fixed literal manifest timestamp; stable string
seeds only). CLI: --self-test | --write.

Register tuple for the shared proof suite (REPORT ONLY — this module does NOT self-register):
    ("_repos/shared-backend-components/scripts/domain_med_message_shapes.py", "domain_med_message_shapes")
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# IMPORT the shared machinery — never edit it (ADD-ONLY / flexible-multi-path).
from scripts.mutator_registry import (  # noqa: E402
    MUTATOR_REGISTRY,
    _receipt,
    run_primitive_proof,
)
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402

DOMAIN = "med_message_shapes"
_FIXED_UTC = "2026-07-03"  # fixed literal timestamp — NO wall-clock (repo law: deterministic + offline)

OUT_DIR = _resource("data") / "dev-intel" / "domain_primitives"
OUT_JSONL = OUT_DIR / "domain_med_message_shapes.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_med_message_shapes.json"


# ── PURE deterministic mutators, contract (payload, **kwargs) -> (output, receipt). Domain-prefixed (`mms_`) so they
#    never collide with existing registry entries; registered via setdefault (idempotent, never overwrites). ──

# ─────────────────────────── SQL clause shapes (PARAMETRIZED — values are ? placeholders, never concatenated) ───
def mms_sql_select_build(spec: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    cols = ", ".join(spec["columns"])
    out = f"SELECT {cols} FROM {spec['table']}"
    return out, _receipt("mms_sql_select_build", before=spec, after=out, lossless=False, note="{table,columns} -> 'SELECT c1, c2 FROM t' (column order preserved)")


_SQL_OP_WHITELIST = {"=", "!=", "<", "<=", ">", ">=", "LIKE", "IN"}  # SHAPE-safe comparison ops only


def mms_sql_where_build(spec: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    for cond in spec["conditions"]:
        op = cond["op"]
        if op not in _SQL_OP_WHITELIST:
            raise ValueError(f"disallowed SQL op: {op}")
        clauses.append(f"{cond['col']} {op} ?")  # PARAMETRIZED: value never enters the SQL string
        params.append(cond["value"])
    out = {"sql": "WHERE " + " AND ".join(clauses), "params": params}
    return out, _receipt("mms_sql_where_build", before=spec, after=out, lossless=False, note="conditions -> parametrized {sql:'WHERE c op ? AND ...', params:[...]} (values bound, never concatenated)")


def mms_sql_insert_build(spec: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    cols = sorted(spec["row"])  # sorted -> deterministic column order regardless of dict order
    placeholders = ", ".join("?" for _ in cols)
    out = {"sql": f"INSERT INTO {spec['table']} ({', '.join(cols)}) VALUES ({placeholders})",
           "params": [spec["row"][c] for c in cols]}
    return out, _receipt("mms_sql_insert_build", before=spec, after=out, lossless=False, note="{table,row} -> parametrized INSERT (columns sorted, values bound as params)")


def mms_sql_orderby_build(spec: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    parts = [f"{c['col']} {c['dir']}" for c in spec["columns"]]
    out = "ORDER BY " + ", ".join(parts)
    return out, _receipt("mms_sql_orderby_build", before=spec, after=out, lossless=False, note="{columns:[{col,dir}]} -> 'ORDER BY c1 ASC, c2 DESC'")


def mms_sql_select_columns(clause: str, **_kw: Any) -> tuple[list[str], dict[str, Any]]:
    body = clause[len("SELECT "):clause.index(" FROM ")]
    out = [c.strip() for c in body.split(",")]
    return out, _receipt("mms_sql_select_columns", before=clause, after=out, lossless=False, note="parse projected columns out of a SELECT clause")


def mms_sql_select_table(clause: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = clause.split(" FROM ", 1)[1].split()[0]
    return out, _receipt("mms_sql_select_table", before=clause, after=out, lossless=False, note="parse the FROM table out of a SELECT clause")


# ─────────────────────────── GraphQL request-message shape ───
def mms_graphql_operation_type(query: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    head = query.strip().split(None, 1)[0]
    out = head if head in {"query", "mutation", "subscription"} else "query"  # anonymous shorthand defaults to query
    return out, _receipt("mms_graphql_operation_type", before=query, after=out, lossless=False, note="extract GraphQL operation type (query/mutation/subscription)")


def mms_graphql_operation_name(query: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    toks = query.strip().split(None, 2)
    name = toks[1] if len(toks) > 1 else ""
    out = name.split("(")[0].split("{")[0].strip()
    return out, _receipt("mms_graphql_operation_name", before=query, after=out, lossless=False, note="extract GraphQL operation name (token after the operation keyword)")


def mms_graphql_request_wrap(query: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {"query": query, "variables": {}}
    return out, _receipt("mms_graphql_request_wrap", before=query, after=out, lossless=True, note="query string -> {query, variables:{}} request envelope; mms_graphql_request_query restores")


def mms_graphql_request_query(env: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = env["query"]
    return out, _receipt("mms_graphql_request_query", before=env, after=out, lossless=True, note="{query, variables} envelope -> query string")


# ─────────────────────────── gRPC / Protobuf message envelope shape ───
def mms_grpc_method_path_build(spec: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = f"/{spec['package']}.{spec['service']}/{spec['method']}"
    return out, _receipt("mms_grpc_method_path_build", before=spec, after=out, lossless=True, note="{package,service,method} -> '/pkg.Service/Method' gRPC path; mms_grpc_method_path_parse restores")


def mms_grpc_method_path_parse(path: str, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    if not path.startswith("/") or "/" not in path[1:]:
        raise ValueError("not a '/pkg.Service/Method' gRPC path")
    svc_full, method = path[1:].split("/", 1)
    package, service = svc_full.rsplit(".", 1)
    out = {"package": package, "service": service, "method": method}
    return out, _receipt("mms_grpc_method_path_parse", before=path, after=out, lossless=True, note="'/pkg.Service/Method' -> {package,service,method}")


_GRPC_STATUS = {0: "OK", 1: "CANCELLED", 2: "UNKNOWN", 3: "INVALID_ARGUMENT", 4: "DEADLINE_EXCEEDED",
                5: "NOT_FOUND", 6: "ALREADY_EXISTS", 7: "PERMISSION_DENIED", 8: "RESOURCE_EXHAUSTED",
                9: "FAILED_PRECONDITION", 10: "ABORTED", 11: "OUT_OF_RANGE", 12: "UNIMPLEMENTED",
                13: "INTERNAL", 14: "UNAVAILABLE", 15: "DATA_LOSS", 16: "UNAUTHENTICATED"}


def mms_grpc_status_name(code: int, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = _GRPC_STATUS.get(code, "UNKNOWN")
    return out, _receipt("mms_grpc_status_name", before=code, after=out, lossless=False, note="canonical gRPC status code int -> status name")


# ─────────────────────────── Webhook payload shapes (GitHub-shape + Stripe-shape; SYNTHETIC) ───
def mms_github_webhook_parse(payload_json: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    obj = json.loads(payload_json)
    out = {"action": obj.get("action"), "repo": obj.get("repository", {}).get("full_name"),
           "number": obj.get("number")}
    return out, _receipt("mms_github_webhook_parse", before=payload_json, after=out, lossless=False, note="GitHub-shape webhook JSON -> {action, repo, number} summary (synthetic)")


def mms_github_webhook_action(payload_json: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = json.loads(payload_json).get("action", "")
    return out, _receipt("mms_github_webhook_action", before=payload_json, after=out, lossless=False, note="extract GitHub webhook 'action' field")


def mms_stripe_webhook_event_type(payload_json: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = json.loads(payload_json).get("type", "")
    return out, _receipt("mms_stripe_webhook_event_type", before=payload_json, after=out, lossless=False, note="extract Stripe-shape event 'type' (e.g. 'charge.succeeded')")


def mms_stripe_webhook_object(payload_json: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = json.loads(payload_json).get("data", {}).get("object", {})
    return out, _receipt("mms_stripe_webhook_object", before=payload_json, after=out, lossless=False, note="extract Stripe-shape event data.object (synthetic)")


# ─────────────────────────── Queue-message envelope shapes (Kafka ProducerRecord + SQS batch-entry) ───
def mms_kafka_record_build(spec: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    headers = spec.get("headers", {})
    hdr_list = [{"key": k, "value": headers[k]} for k in sorted(headers)]  # dict headers -> sorted Kafka header list
    out = {"topic": spec["topic"], "key": spec.get("key"), "value": spec["value"], "headers": hdr_list}
    return out, _receipt("mms_kafka_record_build", before=spec, after=out, lossless=True, note="{topic,key,value,headers{}} -> Kafka ProducerRecord (headers as sorted list); mms_kafka_record_parse restores")


def mms_kafka_record_parse(record: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    headers = {h["key"]: h["value"] for h in record.get("headers", [])}
    out = {"topic": record["topic"], "key": record.get("key"), "value": record["value"], "headers": headers}
    return out, _receipt("mms_kafka_record_parse", before=record, after=out, lossless=True, note="Kafka ProducerRecord -> {topic,key,value,headers{}} (header list -> dict)")


def mms_kafka_record_key(record: dict[str, Any], **_kw: Any) -> tuple[Any, dict[str, Any]]:
    out = record.get("key")
    return out, _receipt("mms_kafka_record_key", before=record, after=out, lossless=False, note="extract Kafka record partition key")


def mms_sqs_batch_entry_build(spec: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {"Id": spec["id"], "MessageBody": spec["body"]}
    return out, _receipt("mms_sqs_batch_entry_build", before=spec, after=out, lossless=False, note="{id,body} -> SQS SendMessageBatch entry {Id,MessageBody}")


# ─────────────────────────── CloudEvents envelope shape ───
def mms_cloudevents_wrap(spec: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {"specversion": "1.0", "type": spec["type"], "source": spec["source"], "id": spec["id"],
           "data": spec.get("data")}
    return out, _receipt("mms_cloudevents_wrap", before=spec, after=out, lossless=False, note="{type,source,id,data} -> CloudEvents 1.0 envelope")


_CE_REQUIRED = ("specversion", "id", "source", "type")


def mms_cloudevents_validate_shape(ce: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    missing = [f for f in _CE_REQUIRED if f not in ce]
    out = {"valid": not missing, "missing": missing}
    return out, _receipt("mms_cloudevents_validate_shape", before=ce, after=out, lossless=False, note="validate CloudEvents required attributes (specversion,id,source,type)")


def mms_cloudevents_type(ce: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = ce.get("type", "")
    return out, _receipt("mms_cloudevents_type", before=ce, after=out, lossless=False, note="extract CloudEvents 'type' attribute")


def mms_cloudevents_data(ce: dict[str, Any], **_kw: Any) -> tuple[Any, dict[str, Any]]:
    out = ce.get("data")
    return out, _receipt("mms_cloudevents_data", before=ce, after=out, lossless=False, note="extract CloudEvents 'data' payload")


# ─────────────────────────── Time-series point + line-protocol shapes ───
def mms_timeseries_point_build(spec: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {"metric": spec["metric"], "timestamp": spec["ts"], "value": spec["value"], "tags": spec.get("tags", {})}
    return out, _receipt("mms_timeseries_point_build", before=spec, after=out, lossless=True, note="{metric,ts,value,tags} -> {metric,timestamp,value,tags} point; mms_timeseries_point_parse restores")


def mms_timeseries_point_parse(point: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {"metric": point["metric"], "ts": point["timestamp"], "value": point["value"], "tags": point.get("tags", {})}
    return out, _receipt("mms_timeseries_point_parse", before=point, after=out, lossless=True, note="{metric,timestamp,value,tags} point -> {metric,ts,value,tags}")


def mms_influx_line_build(spec: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    tags = "".join(f",{k}={spec['tags'][k]}" for k in sorted(spec.get("tags", {})))  # tags sorted -> deterministic
    fields = ",".join(f"{k}={spec['fields'][k]}" for k in sorted(spec["fields"]))
    out = f"{spec['metric']}{tags} {fields} {spec['ts']}"
    return out, _receipt("mms_influx_line_build", before=spec, after=out, lossless=False, note="{metric,tags,fields,ts} -> InfluxDB line protocol (tags+fields sorted)")


def mms_prometheus_sample_build(spec: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    labels = ",".join(f'{k}="{spec["labels"][k]}"' for k in sorted(spec.get("labels", {})))  # labels sorted
    out = f"{spec['name']}{{{labels}}} {spec['value']}"
    return out, _receipt("mms_prometheus_sample_build", before=spec, after=out, lossless=False, note="{name,labels,value} -> Prometheus text-exposition sample (labels sorted)")


# ─────────────────────────── OpenTelemetry span shape ───
def mms_otel_span_build(spec: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {"name": spec["name"], "trace_id": spec["trace_id"], "span_id": spec["span_id"],
           "start_time_unix_nano": spec["start"], "end_time_unix_nano": spec["end"]}
    return out, _receipt("mms_otel_span_build", before=spec, after=out, lossless=False, note="{name,trace_id,span_id,start,end} -> OTLP span shape (unix-nano times)")


def mms_otel_span_duration(span: dict[str, Any], **_kw: Any) -> tuple[int, dict[str, Any]]:
    out = span["end_time_unix_nano"] - span["start_time_unix_nano"]
    return out, _receipt("mms_otel_span_duration", before=span, after=out, lossless=False, note="OTLP span -> duration nanos (end - start)")


def mms_otel_span_name(span: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = span["name"]
    return out, _receipt("mms_otel_span_name", before=span, after=out, lossless=False, note="extract OTLP span name")


def mms_otel_span_validate_shape(span: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    required = ("name", "trace_id", "span_id", "start_time_unix_nano", "end_time_unix_nano")
    missing = [f for f in required if f not in span]
    out = {"valid": not missing, "missing": missing}
    return out, _receipt("mms_otel_span_validate_shape", before=span, after=out, lossless=False, note="validate OTLP span required fields")


#: new pure mutators to plug into the shared registry (idempotent setdefault — never overwrites an existing entry)
_NEW_MUTATORS = {
    "mms_sql_select_build": mms_sql_select_build, "mms_sql_where_build": mms_sql_where_build,
    "mms_sql_insert_build": mms_sql_insert_build, "mms_sql_orderby_build": mms_sql_orderby_build,
    "mms_sql_select_columns": mms_sql_select_columns, "mms_sql_select_table": mms_sql_select_table,
    "mms_graphql_operation_type": mms_graphql_operation_type, "mms_graphql_operation_name": mms_graphql_operation_name,
    "mms_graphql_request_wrap": mms_graphql_request_wrap, "mms_graphql_request_query": mms_graphql_request_query,
    "mms_grpc_method_path_build": mms_grpc_method_path_build, "mms_grpc_method_path_parse": mms_grpc_method_path_parse,
    "mms_grpc_status_name": mms_grpc_status_name,
    "mms_github_webhook_parse": mms_github_webhook_parse, "mms_github_webhook_action": mms_github_webhook_action,
    "mms_stripe_webhook_event_type": mms_stripe_webhook_event_type, "mms_stripe_webhook_object": mms_stripe_webhook_object,
    "mms_kafka_record_build": mms_kafka_record_build, "mms_kafka_record_parse": mms_kafka_record_parse,
    "mms_kafka_record_key": mms_kafka_record_key, "mms_sqs_batch_entry_build": mms_sqs_batch_entry_build,
    "mms_cloudevents_wrap": mms_cloudevents_wrap, "mms_cloudevents_validate_shape": mms_cloudevents_validate_shape,
    "mms_cloudevents_type": mms_cloudevents_type, "mms_cloudevents_data": mms_cloudevents_data,
    "mms_timeseries_point_build": mms_timeseries_point_build, "mms_timeseries_point_parse": mms_timeseries_point_parse,
    "mms_influx_line_build": mms_influx_line_build, "mms_prometheus_sample_build": mms_prometheus_sample_build,
    "mms_otel_span_build": mms_otel_span_build, "mms_otel_span_duration": mms_otel_span_duration,
    "mms_otel_span_name": mms_otel_span_name, "mms_otel_span_validate_shape": mms_otel_span_validate_shape,
}


def register_new_mutators() -> None:
    """Plug the domain's pure mutators into the shared MUTATOR_REGISTRY (registration, not a rewrite). Idempotent."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)


register_new_mutators()


# ── proven-deterministic leaves: each a REAL SHAPE capability with a synthetic fixture + expected (+ inverse where a
#    roundtrip holds). spec fields: id, mutator, fixture, expected, args?, inverse?, format, input_edge, output_edge ──
LEAF_SPECS: list[dict[str, Any]] = [
    # ── SQL clause shapes (parametrized) ──
    {"id": "prim:leaf:mms_sql_select_build", "mutator": "mms_sql_select_build", "format": "sql_clause",
     "fixture": {"table": "orders", "columns": ["id", "total", "status"]},
     "expected": "SELECT id, total, status FROM orders", "input_edge": "SqlSelectSpec", "output_edge": "SqlSelectClause"},
    {"id": "prim:leaf:mms_sql_where_build", "mutator": "mms_sql_where_build", "format": "sql_clause",
     "fixture": {"conditions": [{"col": "status", "op": "=", "value": "active"}, {"col": "age", "op": ">", "value": 18}]},
     "expected": {"sql": "WHERE status = ? AND age > ?", "params": ["active", 18]},
     "input_edge": "SqlWhereSpec", "output_edge": "SqlParametrizedClause"},
    {"id": "prim:leaf:mms_sql_insert_build", "mutator": "mms_sql_insert_build", "format": "sql_clause",
     "fixture": {"table": "users", "row": {"name": "alice", "age": 30}},
     "expected": {"sql": "INSERT INTO users (age, name) VALUES (?, ?)", "params": [30, "alice"]},
     "input_edge": "SqlInsertSpec", "output_edge": "SqlParametrizedClause"},
    {"id": "prim:leaf:mms_sql_orderby_build", "mutator": "mms_sql_orderby_build", "format": "sql_clause",
     "fixture": {"columns": [{"col": "created_at", "dir": "DESC"}, {"col": "id", "dir": "ASC"}]},
     "expected": "ORDER BY created_at DESC, id ASC", "input_edge": "SqlOrderBySpec", "output_edge": "SqlOrderByClause"},
    {"id": "prim:leaf:mms_sql_select_columns", "mutator": "mms_sql_select_columns", "format": "sql_clause",
     "fixture": "SELECT id, total, status FROM orders", "expected": ["id", "total", "status"],
     "input_edge": "SqlSelectClause", "output_edge": "SqlColumnList"},
    {"id": "prim:leaf:mms_sql_select_table", "mutator": "mms_sql_select_table", "format": "sql_clause",
     "fixture": "SELECT id, total FROM orders WHERE id = ?", "expected": "orders",
     "input_edge": "SqlSelectClause", "output_edge": "SqlTableName"},

    # ── GraphQL request-message shape ──
    {"id": "prim:leaf:mms_graphql_operation_type", "mutator": "mms_graphql_operation_type", "format": "graphql_message",
     "fixture": "mutation CreateUser($n: String!) { createUser(name: $n) { id } }", "expected": "mutation",
     "input_edge": "GraphqlQuery", "output_edge": "GraphqlOperationType"},
    {"id": "prim:leaf:mms_graphql_operation_name", "mutator": "mms_graphql_operation_name", "format": "graphql_message",
     "fixture": "query GetUser($id: ID!) { user(id: $id) { name } }", "expected": "GetUser",
     "input_edge": "GraphqlQuery", "output_edge": "GraphqlOperationName"},
    {"id": "prim:leaf:mms_graphql_request_wrap", "mutator": "mms_graphql_request_wrap", "format": "graphql_message",
     "fixture": "query Ping { __typename }", "expected": {"query": "query Ping { __typename }", "variables": {}},
     "inverse": "mms_graphql_request_query", "input_edge": "GraphqlQuery", "output_edge": "GraphqlRequestEnvelope"},
    {"id": "prim:leaf:mms_graphql_request_query", "mutator": "mms_graphql_request_query", "format": "graphql_message",
     "fixture": {"query": "query Ping { __typename }", "variables": {}}, "expected": "query Ping { __typename }",
     "inverse": "mms_graphql_request_wrap", "input_edge": "GraphqlRequestEnvelope", "output_edge": "GraphqlQuery"},

    # ── gRPC / protobuf envelope shape ──
    {"id": "prim:leaf:mms_grpc_method_path_build", "mutator": "mms_grpc_method_path_build", "format": "grpc_envelope",
     "fixture": {"package": "acme.orders.v1", "service": "OrderService", "method": "GetOrder"},
     "expected": "/acme.orders.v1.OrderService/GetOrder",
     "inverse": "mms_grpc_method_path_parse", "input_edge": "GrpcMethodSpec", "output_edge": "GrpcMethodPath"},
    {"id": "prim:leaf:mms_grpc_method_path_parse", "mutator": "mms_grpc_method_path_parse", "format": "grpc_envelope",
     "fixture": "/acme.orders.v1.OrderService/GetOrder",
     "expected": {"package": "acme.orders.v1", "service": "OrderService", "method": "GetOrder"},
     "inverse": "mms_grpc_method_path_build", "input_edge": "GrpcMethodPath", "output_edge": "GrpcMethodSpec"},
    {"id": "prim:leaf:mms_grpc_status_name", "mutator": "mms_grpc_status_name", "format": "grpc_envelope",
     "fixture": 5, "expected": "NOT_FOUND", "input_edge": "GrpcStatusCode", "output_edge": "GrpcStatusName"},

    # ── Webhook payload shapes (synthetic) ──
    {"id": "prim:leaf:mms_github_webhook_parse", "mutator": "mms_github_webhook_parse", "format": "webhook_payload",
     "fixture": '{"action": "opened", "number": 42, "repository": {"full_name": "acme/widgets"}}',
     "expected": {"action": "opened", "repo": "acme/widgets", "number": 42},
     "input_edge": "GithubWebhookJson", "output_edge": "GithubWebhookSummary"},
    {"id": "prim:leaf:mms_github_webhook_action", "mutator": "mms_github_webhook_action", "format": "webhook_payload",
     "fixture": '{"action": "closed", "number": 7}', "expected": "closed",
     "input_edge": "GithubWebhookJson", "output_edge": "GithubWebhookAction"},
    {"id": "prim:leaf:mms_stripe_webhook_event_type", "mutator": "mms_stripe_webhook_event_type", "format": "webhook_payload",
     "fixture": '{"id": "evt_1", "type": "charge.succeeded", "data": {"object": {"id": "ch_1"}}}',
     "expected": "charge.succeeded", "input_edge": "StripeWebhookJson", "output_edge": "StripeEventType"},
    {"id": "prim:leaf:mms_stripe_webhook_object", "mutator": "mms_stripe_webhook_object", "format": "webhook_payload",
     "fixture": '{"id": "evt_1", "type": "invoice.paid", "data": {"object": {"id": "in_9", "amount": 100}}}',
     "expected": {"id": "in_9", "amount": 100}, "input_edge": "StripeWebhookJson", "output_edge": "StripeEventObject"},

    # ── Queue-message envelope shapes ──
    {"id": "prim:leaf:mms_kafka_record_build", "mutator": "mms_kafka_record_build", "format": "queue_message",
     "fixture": {"topic": "orders", "key": "o-1", "value": {"amt": 5}, "headers": {"trace": "t1", "src": "web"}},
     "expected": {"topic": "orders", "key": "o-1", "value": {"amt": 5},
                  "headers": [{"key": "src", "value": "web"}, {"key": "trace", "value": "t1"}]},
     "inverse": "mms_kafka_record_parse", "input_edge": "KafkaRecordSpec", "output_edge": "KafkaProducerRecord"},
    {"id": "prim:leaf:mms_kafka_record_parse", "mutator": "mms_kafka_record_parse", "format": "queue_message",
     "fixture": {"topic": "orders", "key": "o-1", "value": {"amt": 5},
                 "headers": [{"key": "src", "value": "web"}, {"key": "trace", "value": "t1"}]},
     "expected": {"topic": "orders", "key": "o-1", "value": {"amt": 5}, "headers": {"src": "web", "trace": "t1"}},
     "inverse": "mms_kafka_record_build", "input_edge": "KafkaProducerRecord", "output_edge": "KafkaRecordSpec"},
    {"id": "prim:leaf:mms_kafka_record_key", "mutator": "mms_kafka_record_key", "format": "queue_message",
     "fixture": {"topic": "orders", "key": "customer-9", "value": {"amt": 5}, "headers": []},
     "expected": "customer-9", "input_edge": "KafkaProducerRecord", "output_edge": "KafkaPartitionKey"},
    {"id": "prim:leaf:mms_sqs_batch_entry_build", "mutator": "mms_sqs_batch_entry_build", "format": "queue_message",
     "fixture": {"id": "m1", "body": "order-123 shipped"},
     "expected": {"Id": "m1", "MessageBody": "order-123 shipped"},
     "input_edge": "SqsBatchEntrySpec", "output_edge": "SqsBatchEntry"},

    # ── CloudEvents envelope shape ──
    {"id": "prim:leaf:mms_cloudevents_wrap", "mutator": "mms_cloudevents_wrap", "format": "cloudevents_envelope",
     "fixture": {"type": "com.acme.order.created", "source": "/orders", "id": "e-1", "data": {"order": "o-1"}},
     "expected": {"specversion": "1.0", "type": "com.acme.order.created", "source": "/orders", "id": "e-1",
                  "data": {"order": "o-1"}}, "input_edge": "CloudEventSpec", "output_edge": "CloudEventEnvelope"},
    {"id": "prim:leaf:mms_cloudevents_validate_shape", "mutator": "mms_cloudevents_validate_shape", "format": "cloudevents_envelope",
     "fixture": {"specversion": "1.0", "type": "com.acme.x", "source": "/s", "id": "1"},
     "expected": {"valid": True, "missing": []}, "input_edge": "CloudEventEnvelope", "output_edge": "ValidationResult"},
    {"id": "prim:leaf:mms_cloudevents_type", "mutator": "mms_cloudevents_type", "format": "cloudevents_envelope",
     "fixture": {"specversion": "1.0", "type": "com.acme.order.created", "source": "/o", "id": "1"},
     "expected": "com.acme.order.created", "input_edge": "CloudEventEnvelope", "output_edge": "CloudEventType"},
    {"id": "prim:leaf:mms_cloudevents_data", "mutator": "mms_cloudevents_data", "format": "cloudevents_envelope",
     "fixture": {"specversion": "1.0", "type": "t", "source": "/s", "id": "1", "data": {"k": "v"}},
     "expected": {"k": "v"}, "input_edge": "CloudEventEnvelope", "output_edge": "CloudEventData"},

    # ── Time-series point + line-protocol shapes ──
    {"id": "prim:leaf:mms_timeseries_point_build", "mutator": "mms_timeseries_point_build", "format": "timeseries_point",
     "fixture": {"metric": "cpu.usage", "ts": 1633024800, "value": 0.42, "tags": {"host": "web-1"}},
     "expected": {"metric": "cpu.usage", "timestamp": 1633024800, "value": 0.42, "tags": {"host": "web-1"}},
     "inverse": "mms_timeseries_point_parse", "input_edge": "TimeseriesPointSpec", "output_edge": "TimeseriesPoint"},
    {"id": "prim:leaf:mms_timeseries_point_parse", "mutator": "mms_timeseries_point_parse", "format": "timeseries_point",
     "fixture": {"metric": "cpu.usage", "timestamp": 1633024800, "value": 0.42, "tags": {"host": "web-1"}},
     "expected": {"metric": "cpu.usage", "ts": 1633024800, "value": 0.42, "tags": {"host": "web-1"}},
     "inverse": "mms_timeseries_point_build", "input_edge": "TimeseriesPoint", "output_edge": "TimeseriesPointSpec"},
    {"id": "prim:leaf:mms_influx_line_build", "mutator": "mms_influx_line_build", "format": "timeseries_point",
     "fixture": {"metric": "cpu", "tags": {"region": "us", "host": "a"}, "fields": {"value": 0.5}, "ts": 1000},
     "expected": "cpu,host=a,region=us value=0.5 1000", "input_edge": "InfluxPointSpec", "output_edge": "InfluxLine"},
    {"id": "prim:leaf:mms_prometheus_sample_build", "mutator": "mms_prometheus_sample_build", "format": "timeseries_point",
     "fixture": {"name": "http_requests_total", "labels": {"method": "GET", "code": "200"}, "value": 42},
     "expected": 'http_requests_total{code="200",method="GET"} 42',
     "input_edge": "PrometheusSampleSpec", "output_edge": "PrometheusSample"},

    # ── OpenTelemetry span shape ──
    {"id": "prim:leaf:mms_otel_span_build", "mutator": "mms_otel_span_build", "format": "otel_span",
     "fixture": {"name": "GET /orders", "trace_id": "4bf92f3577b34da6", "span_id": "00f067aa0ba902b7",
                 "start": 1000, "end": 1500},
     "expected": {"name": "GET /orders", "trace_id": "4bf92f3577b34da6", "span_id": "00f067aa0ba902b7",
                  "start_time_unix_nano": 1000, "end_time_unix_nano": 1500},
     "input_edge": "OtelSpanSpec", "output_edge": "OtelSpan"},
    {"id": "prim:leaf:mms_otel_span_duration", "mutator": "mms_otel_span_duration", "format": "otel_span",
     "fixture": {"name": "op", "trace_id": "a", "span_id": "b", "start_time_unix_nano": 1000,
                 "end_time_unix_nano": 1500}, "expected": 500,
     "input_edge": "OtelSpan", "output_edge": "DurationNanos"},
    {"id": "prim:leaf:mms_otel_span_name", "mutator": "mms_otel_span_name", "format": "otel_span",
     "fixture": {"name": "GET /orders", "trace_id": "a", "span_id": "b", "start_time_unix_nano": 1,
                 "end_time_unix_nano": 2}, "expected": "GET /orders",
     "input_edge": "OtelSpan", "output_edge": "SpanName"},
    {"id": "prim:leaf:mms_otel_span_validate_shape", "mutator": "mms_otel_span_validate_shape", "format": "otel_span",
     "fixture": {"name": "op", "trace_id": "a", "span_id": "b", "start_time_unix_nano": 1, "end_time_unix_nano": 2},
     "expected": {"valid": True, "missing": []}, "input_edge": "OtelSpan", "output_edge": "ValidationResult"},
]

#: deliberately-wrong leaf — the proof gate MUST leave it candidate (never persisted as proven-deterministic)
NEGATIVE_SPEC: dict[str, Any] = {
    "id": "prim:leaf:mms_WRONG_expected", "mutator": "mms_grpc_status_name", "format": "grpc_envelope",
    "fixture": 5, "expected": "OK", "input_edge": "GrpcStatusCode", "output_edge": "GrpcStatusName"}


# ── GATED-EFFECT candidates: NETWORK / EFFECTFUL sends. NEVER run through the proof runner, NEVER serve_truth.
#    Each declares effect + proof_obligation (a live integration test with a credential) + typed edges. ──
GATED_EFFECT_SPECS: list[dict[str, Any]] = [
    {"id": "prim:gated:mms_sql_execute_query", "capability": "Execute a SELECT against a live database and return rows",
     "effect": "network_read", "proof_obligation": "live integration test against a sandbox database with a connection credential",
     "input_edge": "SqlSelectClause", "output_edge": "SqlResultRows", "format": "sql_clause"},
    {"id": "prim:gated:mms_sql_execute_write", "capability": "Execute an INSERT/UPDATE against a live database",
     "effect": "network_write", "proof_obligation": "live integration test against a sandbox database with a connection credential",
     "input_edge": "SqlParametrizedClause", "output_edge": "SqlWriteResult", "format": "sql_clause"},
    {"id": "prim:gated:mms_graphql_http_post", "capability": "POST a GraphQL request to a live endpoint",
     "effect": "network_read", "proof_obligation": "live integration test against a sandbox GraphQL endpoint with an auth token",
     "input_edge": "GraphqlRequestEnvelope", "output_edge": "GraphqlResponse", "format": "graphql_message"},
    {"id": "prim:gated:mms_grpc_unary_call", "capability": "Make a gRPC unary call to a live service",
     "effect": "network_read", "proof_obligation": "live integration test against a sandbox gRPC service with a channel credential",
     "input_edge": "GrpcMethodPath", "output_edge": "GrpcResponseMessage", "format": "grpc_envelope"},
    {"id": "prim:gated:mms_webhook_deliver", "capability": "Deliver a webhook payload via HTTP POST to a subscriber URL",
     "effect": "network_write", "proof_obligation": "live integration test against a sandbox HTTP receiver with a signing secret",
     "input_edge": "GithubWebhookSummary", "output_edge": "WebhookDeliveryResult", "format": "webhook_payload"},
    {"id": "prim:gated:mms_kafka_produce", "capability": "Produce a record to a live Kafka topic",
     "effect": "network_write", "proof_obligation": "live integration test against a sandbox Kafka broker with bootstrap credentials",
     "input_edge": "KafkaProducerRecord", "output_edge": "KafkaProduceResult", "format": "queue_message"},
    {"id": "prim:gated:mms_cloudevents_http_emit", "capability": "Emit a CloudEvent over HTTP to a live sink",
     "effect": "network_write", "proof_obligation": "live integration test against a sandbox CloudEvents sink with an endpoint credential",
     "input_edge": "CloudEventEnvelope", "output_edge": "CloudEventEmitResult", "format": "cloudevents_envelope"},
    {"id": "prim:gated:mms_influxdb_write", "capability": "Write a line-protocol point to a live InfluxDB",
     "effect": "network_write", "proof_obligation": "live integration test against a sandbox InfluxDB with an org token",
     "input_edge": "InfluxLine", "output_edge": "InfluxWriteResult", "format": "timeseries_point"},
    {"id": "prim:gated:mms_prometheus_remote_write", "capability": "Push a sample via Prometheus remote_write to a live receiver",
     "effect": "network_write", "proof_obligation": "live integration test against a sandbox remote_write receiver with a bearer token",
     "input_edge": "PrometheusSample", "output_edge": "RemoteWriteResult", "format": "timeseries_point"},
    {"id": "prim:gated:mms_otlp_span_export", "capability": "Export an OTLP span to a live collector",
     "effect": "network_write", "proof_obligation": "live integration test against a sandbox OTLP collector with an endpoint credential",
     "input_edge": "OtelSpan", "output_edge": "OtlpExportResult", "format": "otel_span"},
]


def _prove_one(spec: dict[str, Any]) -> dict[str, Any]:
    return run_primitive_proof(
        spec["id"], spec["mutator"], spec["fixture"], spec["expected"],
        mutator_args=spec.get("args") or {}, has_inverse=spec.get("inverse"),
    )


def prove_all() -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Run every declared deterministic leaf through the imported executed-proof runner. Returns [(spec, receipt), ...]."""
    return [(s, _prove_one(s)) for s in LEAF_SPECS]


def build_proven_rows() -> list[dict[str, Any]]:
    """Persist-ready rows for leaves whose executed proof PASSED — TYPED via canonicalize_edge (workable == typed)."""
    rows: list[dict[str, Any]] = []
    for spec, receipt in prove_all():
        if receipt["serves_truth"] is not True:
            continue  # a failing / wrong-expected leaf stays candidate and is NOT persisted (the gate is the point)
        rows.append({
            "primitive_id": receipt["primitive_id"],
            "mutator": receipt["mutator"],
            "domain": DOMAIN,
            "format": spec["format"],
            "row_section": "proven_deterministic",
            "candidate": False,
            "serves_truth": True,
            "verification_level": "L7_executed_proof",
            "input_edge": spec["input_edge"],
            "output_edge": spec["output_edge"],
            "input_edge_type_id": canonicalize_edge(spec["input_edge"]),
            "output_edge_type_id": canonicalize_edge(spec["output_edge"]),
            "has_inverse": spec.get("inverse"),
            "proofs": [p["name"] for p in receipt["proofs"] if p["passed"]],
        })
    return rows


def build_gated_rows() -> list[dict[str, Any]]:
    """Gated-effect candidate rows — NEVER proven, NEVER serves_truth; typed so they still declare their edges."""
    rows: list[dict[str, Any]] = []
    for spec in GATED_EFFECT_SPECS:
        rows.append({
            "primitive_id": spec["id"],
            "domain": DOMAIN,
            "format": spec["format"],
            "row_section": "gated_effect_candidate",
            "capability": spec["capability"],
            "candidate": True,
            "serves_truth": False,
            "effect": spec["effect"],
            "proof_obligation": spec["proof_obligation"],
            "input_edge": spec["input_edge"],
            "output_edge": spec["output_edge"],
            "input_edge_type_id": canonicalize_edge(spec["input_edge"]),
            "output_edge_type_id": canonicalize_edge(spec["output_edge"]),
        })
    return rows


def build_manifest(proven: list[dict[str, Any]], gated: list[dict[str, Any]]) -> dict[str, Any]:
    typed = [r for r in proven if r["input_edge_type_id"] and r["output_edge_type_id"]]
    return {
        "record_type": "domain_primitive_shard_manifest",
        "domain": DOMAIN,
        "generator": "scripts/domain_med_message_shapes.py",
        "generated_utc": _FIXED_UTC,
        "formats_covered": sorted({s["format"] for s in LEAF_SPECS}),
        # SEPARATE, honest counts (proven-deterministic vs gated-effect candidate).
        "defined_deterministic_count": len(LEAF_SPECS),
        "proven_deterministic": len(proven),
        "typed": len(typed),
        "gated_effect_candidates": len(gated),
        "gated_effect_by_effect": {e: sum(1 for r in gated if r["effect"] == e)
                                   for e in sorted({r["effect"] for r in gated})},
        "verification_level": "L7_executed_proof",
        "proven_primitive_ids": sorted(r["primitive_id"] for r in proven),
        "gated_effect_primitive_ids": sorted(r["primitive_id"] for r in gated),
        "note": "proven_deterministic rows: serves_truth=true set ONLY by an executed passing proof (run_primitive_proof, "
                "imported from scripts/mutator_registry.py); every row TYPED via canonicalize_edge (imported from "
                "scripts/build_edge_type_retrofit.py). gated_effect_candidate rows: network/effectful sends (execute a "
                "query, POST a request, gRPC call, produce/emit/export) are NEVER proven and stay candidate/"
                "serves_truth=false with an effect + proof_obligation. Synthetic/public message shapes only; SQL builders "
                "are PARAMETRIZED (values bound, never concatenated); NO insurance; NO real PII/PAN/SSN/secrets. Counts "
                "are separate and honest.",
    }


def write_shard() -> dict[str, Any]:
    proven = build_proven_rows()
    gated = build_gated_rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Both sections written to the SAME shard, each row self-labels via row_section.
    all_rows = proven + gated
    OUT_JSONL.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in all_rows), encoding="utf-8")
    manifest = build_manifest(proven, gated)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    proven = prove_all()
    rows = build_proven_rows()
    gated = build_gated_rows()
    ids = [r["primitive_id"] for r in rows]
    typed = [r for r in rows if r["input_edge_type_id"] and r["output_edge_type_id"]]
    roundtrip_specs = [s for s in LEAF_SPECS if s.get("inverse")]
    proven_by_id = {r["primitive_id"]: r for (s, r) in proven}

    # deliberately-wrong leaf must stay candidate (proof gate is real) — and never enter the proven section
    wrong = _prove_one(NEGATIVE_SPEC)
    # a second wrong path: an un-runnable fixture -> execution error -> not promoted
    err = run_primitive_proof("prim:leaf:mms_EXEC_ERROR", "mms_sql_select_table", 12345, "irrelevant")

    manifest = build_manifest(rows, gated)
    valid_effects = {"network_read", "network_write", "model_call", "file_write"}
    target_formats = {"sql_clause", "graphql_message", "grpc_envelope", "webhook_payload", "queue_message",
                      "cloudevents_envelope", "timeseries_point", "otel_span"}

    checks: list[tuple[str, bool]] = [
        (">=25 deterministic leaves declared", len(LEAF_SPECS) >= 25),
        ("unique proven primitive ids", len(set(ids)) == len(ids)),
        (">=25 leaves PROVE serves_truth=true via an executed proof", len(rows) >= 25),
        ("every proven receipt is L7_executed_proof with all sub-proofs passing",
         all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"])
             for (_s, r) in proven if r["serves_truth"] is True)),
        ("EVERY proven row carries non-null input+output edge type ids", len(typed) == len(rows)),
        ("manifest typed == proven_deterministic", manifest["typed"] == manifest["proven_deterministic"]),
        ("all 8 target message-shape formats are covered", set(manifest["formats_covered"]) == target_formats),
        ("roundtrip-inverse pairs actually ran + PASSED a roundtrip proof", all(
            any(p["name"] == "roundtrip_test" and p["passed"] for p in proven_by_id[s["id"]]["proofs"])
            for s in roundtrip_specs)),
        ("domain stamped on every proven row", all(r["domain"] == DOMAIN for r in rows)),
        ("deterministic: re-running yields identical proven rows",
         [json.dumps(r, sort_keys=True) for r in build_proven_rows()] == [json.dumps(r, sort_keys=True) for r in rows]),
        # gated-effect law: EVERY gated row is candidate / serves_truth=false with a valid effect + proof_obligation
        (">=1 gated-effect candidate declared", len(gated) >= 1),
        ("EVERY gated-effect row is candidate + serves_truth=false",
         all(r["candidate"] is True and r["serves_truth"] is False for r in gated)),
        ("EVERY gated-effect row has a valid effect + non-empty proof_obligation",
         all(r["effect"] in valid_effects and isinstance(r["proof_obligation"], str) and r["proof_obligation"]
             for r in gated)),
        ("EVERY gated-effect row is TYPED (input+output edge type ids)",
         all(r["input_edge_type_id"] and r["output_edge_type_id"] for r in gated)),
        ("no gated-effect id leaked into the proven section", not (set(r["primitive_id"] for r in gated) & set(ids))),
        # the proof gate is real
        ("a deliberately-wrong leaf stays CANDIDATE (never promoted)",
         wrong["serves_truth"] is False and wrong["promoted"] is False),
        ("the wrong leaf is NOT persisted as proven", NEGATIVE_SPEC["id"] not in set(ids)),
        ("an un-runnable fixture fails the proof, does not promote",
         err["serves_truth"] is False and err["promoted"] is False),
        ("new mutators registered into the shared registry (add-only seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - domain_med_message_shapes:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - domain_med_message_shapes: {len(rows)} WORKABLE (proven + TYPED) deterministic MESSAGE-SHAPE leaves "
          f"for '{DOMAIN}' (serves_truth=true, L7_executed_proof; typed=={len(rows)}) across 8 shape formats; "
          f"{len(roundtrip_specs)} inverse pairs proven reversible via roundtrip; {len(gated)} network/effectful sends "
          "declared as GATED-EFFECT candidates (serves_truth=false, effect + proof_obligation). A deliberately-wrong "
          "leaf and an un-runnable fixture correctly stay candidate. Synthetic parametrized shapes; no PII/secrets.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        manifest = write_shard()
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return self_test()
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
