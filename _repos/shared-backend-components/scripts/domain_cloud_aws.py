#!/usr/bin/env python3
"""scripts.domain_cloud_aws — WORKABLE (proven + TYPED) deterministic SHAPE leaves for AWS cloud shapes.

ADD-ONLY parallel path (its OWN shard file). It IMPORTS the shared machinery, never edits it:
  * `run_primitive_proof` / `MUTATOR_REGISTRY` / `_receipt` from `scripts.mutator_registry` — the proof-runner EXECUTES
    each pure mutator against a synthetic fixture and flips serves_truth false->true ONLY on a PASSING executed proof;
  * `canonicalize_edge` from `scripts.build_edge_type_retrofit` — folds each leaf's logical edge labels to canonical
    type_ids so every proven leaf is also TYPED (input_edge_type_id + output_edge_type_id) and can chain.

Covers parse / extract / validate / emit / build-request SHAPES (SYNTHETIC fixtures, NO real secrets/PII/account keys):
  ARN parse/build · S3 URI + virtual-hosted URL parse/build · IAM policy-document shape · IAM action split ·
  DynamoDB key-schema + attribute-value (wire) shape · CloudWatch log-event parse · SQS/SNS message envelope ·
  Terraform aws_* resource-block emit. All mutators operate on the SHAPE only — no live AWS call ever happens here.

DOMAIN LAWS honored: NO insurance primitives (any domain); NO healthcare-clinical work; synthetic/public shapes only
(account ids, ARNs, bucket names are fabricated, never real credentials/secret keys/PII). NETWORK/EFFECTFUL AWS
capabilities (S3 GetObject/PutObject, DynamoDB PutItem/Query, SQS SendMessage, SNS Publish, CloudWatch PutLogEvents,
STS AssumeRole, `terraform apply`) are NEVER run through the proof runner and NEVER serve_truth — they are declared as
GATED EFFECT candidates (candidate=true, serves_truth=false, effect, proof_obligation) in a SEPARATE section of the
shard, with SEPARATE honest counts.

Deterministic + offline: no network, no LLM, no wall-clock, no RNG (fixed literal manifest timestamp; stable string
seeds only). CLI: --self-test | --write.

Register tuple for the shared proof suite (REPORT ONLY — this module does NOT self-register):
    ("_repos/shared-backend-components/scripts/domain_cloud_aws.py", "domain_cloud_aws")
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import re
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

DOMAIN = "cloud_aws"
_FIXED_UTC = "2026-07-03"  # fixed literal timestamp — NO wall-clock (repo law: deterministic + offline)

OUT_DIR = _resource("data") / "dev-intel" / "domain_primitives"
OUT_JSONL = OUT_DIR / "domain_cloud_aws.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_cloud_aws.json"


# ── PURE deterministic mutators, contract (payload, **kwargs) -> (output, receipt). Domain-prefixed (`caw_`) so they
#    never collide with existing registry entries; registered via setdefault (idempotent, never overwrites). ──

# ARN — arn:partition:service:region:account-id:resource (resource may itself contain ':' or '/').
def caw_arn_parse(arn: str, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    parts = arn.split(":", 5)
    if len(parts) != 6 or parts[0] != "arn":
        raise ValueError("not a 6-part ARN")
    out = {"partition": parts[1], "service": parts[2], "region": parts[3], "account": parts[4], "resource": parts[5]}
    return out, _receipt("caw_arn_parse", before=arn, after=out, lossless=True, note="ARN -> {partition,service,region,account,resource}; caw_arn_build restores")


def caw_arn_build(parsed: dict[str, str], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = f"arn:{parsed['partition']}:{parsed['service']}:{parsed['region']}:{parsed['account']}:{parsed['resource']}"
    return out, _receipt("caw_arn_build", before=parsed, after=out, lossless=True, note="{partition,service,region,account,resource} -> ARN string")


def caw_arn_partition(arn: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = arn.split(":", 5)[1]
    return out, _receipt("caw_arn_partition", before=arn, after=out, lossless=False, note="extract ARN partition (aws/aws-cn/aws-us-gov)")


def caw_arn_service(arn: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = arn.split(":", 5)[2]
    return out, _receipt("caw_arn_service", before=arn, after=out, lossless=False, note="extract ARN service namespace")


def caw_arn_region(arn: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = arn.split(":", 5)[3]
    return out, _receipt("caw_arn_region", before=arn, after=out, lossless=False, note="extract ARN region (may be empty for global services)")


def caw_arn_account(arn: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = arn.split(":", 5)[4]
    return out, _receipt("caw_arn_account", before=arn, after=out, lossless=False, note="extract ARN account id (synthetic)")


def caw_arn_resource(arn: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = arn.split(":", 5)[5]
    return out, _receipt("caw_arn_resource", before=arn, after=out, lossless=False, note="extract ARN resource part (may contain ':' or '/')")


def caw_arn_resource_type(arn: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    resource = arn.split(":", 5)[5]
    out = re.split(r"[:/]", resource, maxsplit=1)[0]
    return out, _receipt("caw_arn_resource_type", before=arn, after=out, lossless=False, note="ARN resource type = head token before first ':' or '/'")


def caw_arn_validate_shape(arn: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    parts = arn.split(":", 5)
    valid = len(parts) == 6 and parts[0] == "arn" and bool(parts[2])
    out = {"valid": valid, "service": parts[2] if valid else None}
    return out, _receipt("caw_arn_validate_shape", before=arn, after=out, lossless=False, note="validate ARN shape: 6 colon parts, 'arn' head, non-empty service")


# S3 URI (s3://bucket/key) + virtual-hosted HTTPS URL.
def caw_s3_uri_parse(uri: str, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    if not uri.startswith("s3://"):
        raise ValueError("not an s3:// URI")
    bucket, _, key = uri[len("s3://"):].partition("/")
    out = {"bucket": bucket, "key": key}
    return out, _receipt("caw_s3_uri_parse", before=uri, after=out, lossless=True, note="s3://bucket/key -> {bucket,key}; caw_s3_uri_build restores")


def caw_s3_uri_build(parsed: dict[str, str], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = f"s3://{parsed['bucket']}/{parsed['key']}"
    return out, _receipt("caw_s3_uri_build", before=parsed, after=out, lossless=True, note="{bucket,key} -> s3://bucket/key")


def caw_s3_uri_bucket(uri: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = uri[len("s3://"):].partition("/")[0]
    return out, _receipt("caw_s3_uri_bucket", before=uri, after=out, lossless=False, note="extract S3 bucket from s3:// URI")


def caw_s3_uri_key(uri: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = uri[len("s3://"):].partition("/")[2]
    return out, _receipt("caw_s3_uri_key", before=uri, after=out, lossless=False, note="extract S3 object key from s3:// URI")


_S3_HTTPS_RE = re.compile(r"^https://(?P<bucket>[^.]+)\.s3[.-](?P<region>[^.]+)\.amazonaws\.com/(?P<key>.*)$")


def caw_s3_https_url_parse(url: str, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    m = _S3_HTTPS_RE.match(url)
    if not m:
        raise ValueError("not a virtual-hosted S3 HTTPS URL")
    out = m.groupdict()
    return out, _receipt("caw_s3_https_url_parse", before=url, after=out, lossless=False, note="virtual-hosted S3 HTTPS URL -> {bucket,region,key}")


def caw_s3_bucket_name_validate(name: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    valid = (3 <= len(name) <= 63 and re.fullmatch(r"[a-z0-9][a-z0-9.-]*[a-z0-9]", name) is not None
             and ".." not in name and not re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", name))
    out = {"valid": bool(valid)}
    return out, _receipt("caw_s3_bucket_name_validate", before=name, after=out, lossless=False, note="validate S3 bucket-name SHAPE (len 3-63, lowercase, not an IP)")


# IAM policy document (synthetic; shape only).
def caw_iam_policy_validate_shape(policy_json: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    obj = json.loads(policy_json)
    valid = "Version" in obj and "Statement" in obj
    out = {"valid": valid, "version": obj.get("Version") if valid else None}
    return out, _receipt("caw_iam_policy_validate_shape", before=policy_json, after=out, lossless=False, note="validate IAM policy shape: has Version + Statement")


def caw_iam_policy_statement_count(policy_json: str, **_kw: Any) -> tuple[int, dict[str, Any]]:
    stmt = json.loads(policy_json).get("Statement")
    out = 1 if isinstance(stmt, dict) else (len(stmt) if isinstance(stmt, list) else 0)
    return out, _receipt("caw_iam_policy_statement_count", before=policy_json, after=out, lossless=False, note="count IAM statements (dict->1, list->len)")


def caw_iam_statement_effect(statement_json: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = json.loads(statement_json).get("Effect", "")
    return out, _receipt("caw_iam_statement_effect", before=statement_json, after=out, lossless=False, note="extract IAM statement Effect (Allow/Deny)")


def caw_iam_statement_actions(statement_json: str, **_kw: Any) -> tuple[list[str], dict[str, Any]]:
    a = json.loads(statement_json).get("Action")
    out = [a] if isinstance(a, str) else (list(a) if isinstance(a, list) else [])
    return out, _receipt("caw_iam_statement_actions", before=statement_json, after=out, lossless=False, note="normalize IAM Action (string|list) -> list")


def caw_iam_action_service(action: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = action.split(":", 1)[0]
    return out, _receipt("caw_iam_action_service", before=action, after=out, lossless=False, note="IAM action service prefix (e.g. 's3' from 's3:GetObject')")


def caw_iam_action_operation(action: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = action.split(":", 1)[1] if ":" in action else ""
    return out, _receipt("caw_iam_action_operation", before=action, after=out, lossless=False, note="IAM action operation (e.g. 'GetObject' from 's3:GetObject')")


# DynamoDB key-schema + attribute-value (wire descriptor) shapes.
def caw_ddb_key_schema_parse(schema: list[dict[str, str]], **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    hash_key = next((e["AttributeName"] for e in schema if e.get("KeyType") == "HASH"), "")
    range_key = next((e["AttributeName"] for e in schema if e.get("KeyType") == "RANGE"), "")
    out = {"hash_key": hash_key, "range_key": range_key}
    return out, _receipt("caw_ddb_key_schema_parse", before=schema, after=out, lossless=True, note="DDB KeySchema list -> {hash_key,range_key}; caw_ddb_key_schema_build restores")


def caw_ddb_key_schema_build(parsed: dict[str, str], **_kw: Any) -> tuple[list[dict[str, str]], dict[str, Any]]:
    out = [{"AttributeName": parsed["hash_key"], "KeyType": "HASH"}]
    if parsed.get("range_key"):
        out.append({"AttributeName": parsed["range_key"], "KeyType": "RANGE"})
    return out, _receipt("caw_ddb_key_schema_build", before=parsed, after=out, lossless=True, note="{hash_key,range_key} -> DDB KeySchema list (HASH then RANGE)")


def caw_ddb_attr_value_unwrap(attr: dict[str, Any], **_kw: Any) -> tuple[Any, dict[str, Any]]:
    out = next(iter(attr.values()))
    return out, _receipt("caw_ddb_attr_value_unwrap", before=attr, after=out, lossless=False, note="DDB wire attribute {typedescriptor:value} -> value")


def caw_ddb_item_to_plain(item: dict[str, dict[str, Any]], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {k: next(iter(v.values())) for k, v in item.items()}
    return out, _receipt("caw_ddb_item_to_plain", before=item, after=out, lossless=False, note="DDB wire item -> plain {field:value} map")


# CloudWatch Logs event (synthetic).
def caw_cloudwatch_event_parse(event_json: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = json.loads(event_json)
    return out, _receipt("caw_cloudwatch_event_parse", before=event_json, after=out, lossless=False, note="CloudWatch log event JSON -> {timestamp,message,...}")


def caw_cloudwatch_event_message(event_json: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = json.loads(event_json).get("message", "")
    return out, _receipt("caw_cloudwatch_event_message", before=event_json, after=out, lossless=False, note="extract CloudWatch log event message")


# SQS / SNS message envelope shapes.
def caw_sqs_envelope_wrap(body: Any, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {"MessageBody": body}
    return out, _receipt("caw_sqs_envelope_wrap", before=body, after=out, lossless=True, note="body -> {MessageBody}; caw_sqs_envelope_unwrap restores")


def caw_sqs_envelope_unwrap(env: dict[str, Any], **_kw: Any) -> tuple[Any, dict[str, Any]]:
    out = env["MessageBody"]
    return out, _receipt("caw_sqs_envelope_unwrap", before=env, after=out, lossless=True, note="{MessageBody} -> body")


def caw_sns_message_extract(notification_json: str, **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = json.loads(notification_json).get("Message", "")
    return out, _receipt("caw_sns_message_extract", before=notification_json, after=out, lossless=False, note="extract SNS notification Message field")


# Terraform aws_* resource-block emit (deterministic HCL; attrs sorted for stability).
def caw_tf_aws_resource_emit(block: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    lines = [f'resource "{block["type"]}" "{block["name"]}" {{']
    for k in sorted(block.get("attrs", {})):
        lines.append(f'  {k} = "{block["attrs"][k]}"')
    lines.append("}")
    out = "\n".join(lines)
    return out, _receipt("caw_tf_aws_resource_emit", before=block, after=out, lossless=False, note="{type,name,attrs} -> deterministic Terraform aws_* HCL block (attrs sorted)")


#: new pure mutators to plug into the shared registry (idempotent setdefault — never overwrites an existing entry)
_NEW_MUTATORS = {
    "caw_arn_parse": caw_arn_parse, "caw_arn_build": caw_arn_build, "caw_arn_partition": caw_arn_partition,
    "caw_arn_service": caw_arn_service, "caw_arn_region": caw_arn_region, "caw_arn_account": caw_arn_account,
    "caw_arn_resource": caw_arn_resource, "caw_arn_resource_type": caw_arn_resource_type,
    "caw_arn_validate_shape": caw_arn_validate_shape,
    "caw_s3_uri_parse": caw_s3_uri_parse, "caw_s3_uri_build": caw_s3_uri_build,
    "caw_s3_uri_bucket": caw_s3_uri_bucket, "caw_s3_uri_key": caw_s3_uri_key,
    "caw_s3_https_url_parse": caw_s3_https_url_parse, "caw_s3_bucket_name_validate": caw_s3_bucket_name_validate,
    "caw_iam_policy_validate_shape": caw_iam_policy_validate_shape,
    "caw_iam_policy_statement_count": caw_iam_policy_statement_count,
    "caw_iam_statement_effect": caw_iam_statement_effect, "caw_iam_statement_actions": caw_iam_statement_actions,
    "caw_iam_action_service": caw_iam_action_service, "caw_iam_action_operation": caw_iam_action_operation,
    "caw_ddb_key_schema_parse": caw_ddb_key_schema_parse, "caw_ddb_key_schema_build": caw_ddb_key_schema_build,
    "caw_ddb_attr_value_unwrap": caw_ddb_attr_value_unwrap, "caw_ddb_item_to_plain": caw_ddb_item_to_plain,
    "caw_cloudwatch_event_parse": caw_cloudwatch_event_parse,
    "caw_cloudwatch_event_message": caw_cloudwatch_event_message,
    "caw_sqs_envelope_wrap": caw_sqs_envelope_wrap, "caw_sqs_envelope_unwrap": caw_sqs_envelope_unwrap,
    "caw_sns_message_extract": caw_sns_message_extract, "caw_tf_aws_resource_emit": caw_tf_aws_resource_emit,
}


def register_new_mutators() -> None:
    """Plug the domain's pure mutators into the shared MUTATOR_REGISTRY (registration, not a rewrite). Idempotent."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)


register_new_mutators()


# ── proven-deterministic leaves: each a REAL SHAPE capability with a synthetic fixture + expected (+ inverse where a
#    roundtrip holds). spec fields: id, mutator, fixture, expected, args?, inverse?, format, input_edge, output_edge ──
LEAF_SPECS: list[dict[str, Any]] = [
    # ARN
    {"id": "prim:leaf:caw_arn_parse", "mutator": "caw_arn_parse", "format": "aws_arn",
     "fixture": "arn:aws:s3:::my-bucket/data.csv",
     "expected": {"partition": "aws", "service": "s3", "region": "", "account": "", "resource": "my-bucket/data.csv"},
     "inverse": "caw_arn_build", "input_edge": "AwsArn", "output_edge": "AwsArnParts"},
    {"id": "prim:leaf:caw_arn_build", "mutator": "caw_arn_build", "format": "aws_arn",
     "fixture": {"partition": "aws", "service": "iam", "region": "", "account": "123456789012", "resource": "role/App"},
     "expected": "arn:aws:iam::123456789012:role/App",
     "inverse": "caw_arn_parse", "input_edge": "AwsArnParts", "output_edge": "AwsArn"},
    {"id": "prim:leaf:caw_arn_partition", "mutator": "caw_arn_partition", "format": "aws_arn",
     "fixture": "arn:aws-cn:s3:::bucket", "expected": "aws-cn", "input_edge": "AwsArn", "output_edge": "ArnPartition"},
    {"id": "prim:leaf:caw_arn_service", "mutator": "caw_arn_service", "format": "aws_arn",
     "fixture": "arn:aws:sqs:us-east-1:123456789012:MyQueue", "expected": "sqs",
     "input_edge": "AwsArn", "output_edge": "ArnService"},
    {"id": "prim:leaf:caw_arn_region", "mutator": "caw_arn_region", "format": "aws_arn",
     "fixture": "arn:aws:sqs:us-east-1:123456789012:MyQueue", "expected": "us-east-1",
     "input_edge": "AwsArn", "output_edge": "ArnRegion"},
    {"id": "prim:leaf:caw_arn_account", "mutator": "caw_arn_account", "format": "aws_arn",
     "fixture": "arn:aws:sqs:us-east-1:123456789012:MyQueue", "expected": "123456789012",
     "input_edge": "AwsArn", "output_edge": "ArnAccountId"},
    {"id": "prim:leaf:caw_arn_resource", "mutator": "caw_arn_resource", "format": "aws_arn",
     "fixture": "arn:aws:iam::123456789012:user/JohnDoe", "expected": "user/JohnDoe",
     "input_edge": "AwsArn", "output_edge": "ArnResource"},
    {"id": "prim:leaf:caw_arn_resource_type", "mutator": "caw_arn_resource_type", "format": "aws_arn",
     "fixture": "arn:aws:dynamodb:us-east-1:123456789012:table/Music", "expected": "table",
     "input_edge": "AwsArn", "output_edge": "ArnResourceType"},
    {"id": "prim:leaf:caw_arn_validate_shape", "mutator": "caw_arn_validate_shape", "format": "aws_arn",
     "fixture": "arn:aws:lambda:us-west-2:123456789012:function:proc",
     "expected": {"valid": True, "service": "lambda"}, "input_edge": "AwsArn", "output_edge": "ValidationResult"},

    # S3 URI + HTTPS URL
    {"id": "prim:leaf:caw_s3_uri_parse", "mutator": "caw_s3_uri_parse", "format": "s3_uri",
     "fixture": "s3://my-bucket/reports/q1.csv", "expected": {"bucket": "my-bucket", "key": "reports/q1.csv"},
     "inverse": "caw_s3_uri_build", "input_edge": "S3Uri", "output_edge": "S3UriParts"},
    {"id": "prim:leaf:caw_s3_uri_build", "mutator": "caw_s3_uri_build", "format": "s3_uri",
     "fixture": {"bucket": "logs-bucket", "key": "2026/07/app.log"}, "expected": "s3://logs-bucket/2026/07/app.log",
     "inverse": "caw_s3_uri_parse", "input_edge": "S3UriParts", "output_edge": "S3Uri"},
    {"id": "prim:leaf:caw_s3_uri_bucket", "mutator": "caw_s3_uri_bucket", "format": "s3_uri",
     "fixture": "s3://data-lake/raw/x.parquet", "expected": "data-lake", "input_edge": "S3Uri", "output_edge": "S3Bucket"},
    {"id": "prim:leaf:caw_s3_uri_key", "mutator": "caw_s3_uri_key", "format": "s3_uri",
     "fixture": "s3://data-lake/raw/x.parquet", "expected": "raw/x.parquet", "input_edge": "S3Uri", "output_edge": "S3ObjectKey"},
    {"id": "prim:leaf:caw_s3_https_url_parse", "mutator": "caw_s3_https_url_parse", "format": "s3_uri",
     "fixture": "https://my-bucket.s3.us-west-2.amazonaws.com/reports/q1.csv",
     "expected": {"bucket": "my-bucket", "region": "us-west-2", "key": "reports/q1.csv"},
     "input_edge": "S3HttpsUrl", "output_edge": "S3UrlParts"},
    {"id": "prim:leaf:caw_s3_bucket_name_validate", "mutator": "caw_s3_bucket_name_validate", "format": "s3_uri",
     "fixture": "my-valid-bucket", "expected": {"valid": True}, "input_edge": "S3BucketName", "output_edge": "ValidationResult"},

    # IAM policy document
    {"id": "prim:leaf:caw_iam_policy_validate_shape", "mutator": "caw_iam_policy_validate_shape", "format": "iam_policy_document",
     "fixture": '{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "s3:GetObject", "Resource": "*"}]}',
     "expected": {"valid": True, "version": "2012-10-17"}, "input_edge": "IamPolicyJson", "output_edge": "ValidationResult"},
    {"id": "prim:leaf:caw_iam_policy_statement_count", "mutator": "caw_iam_policy_statement_count", "format": "iam_policy_document",
     "fixture": '{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Action": "s3:GetObject"}, {"Effect": "Deny", "Action": "s3:DeleteObject"}]}',
     "expected": 2, "input_edge": "IamPolicyJson", "output_edge": "Count"},
    {"id": "prim:leaf:caw_iam_statement_effect", "mutator": "caw_iam_statement_effect", "format": "iam_policy_document",
     "fixture": '{"Effect": "Deny", "Action": "s3:DeleteBucket", "Resource": "*"}', "expected": "Deny",
     "input_edge": "IamStatementJson", "output_edge": "IamEffect"},
    {"id": "prim:leaf:caw_iam_statement_actions", "mutator": "caw_iam_statement_actions", "format": "iam_policy_document",
     "fixture": '{"Effect": "Allow", "Action": ["s3:GetObject", "s3:PutObject"], "Resource": "*"}',
     "expected": ["s3:GetObject", "s3:PutObject"], "input_edge": "IamStatementJson", "output_edge": "IamActionList"},
    {"id": "prim:leaf:caw_iam_action_service", "mutator": "caw_iam_action_service", "format": "iam_policy_document",
     "fixture": "dynamodb:PutItem", "expected": "dynamodb", "input_edge": "IamAction", "output_edge": "IamActionService"},
    {"id": "prim:leaf:caw_iam_action_operation", "mutator": "caw_iam_action_operation", "format": "iam_policy_document",
     "fixture": "dynamodb:PutItem", "expected": "PutItem", "input_edge": "IamAction", "output_edge": "IamActionOperation"},

    # DynamoDB key-schema + attribute value
    {"id": "prim:leaf:caw_ddb_key_schema_parse", "mutator": "caw_ddb_key_schema_parse", "format": "dynamodb_shape",
     "fixture": [{"AttributeName": "pk", "KeyType": "HASH"}, {"AttributeName": "sk", "KeyType": "RANGE"}],
     "expected": {"hash_key": "pk", "range_key": "sk"},
     "inverse": "caw_ddb_key_schema_build", "input_edge": "DdbKeySchema", "output_edge": "DdbKeys"},
    {"id": "prim:leaf:caw_ddb_key_schema_build", "mutator": "caw_ddb_key_schema_build", "format": "dynamodb_shape",
     "fixture": {"hash_key": "userId", "range_key": "createdAt"},
     "expected": [{"AttributeName": "userId", "KeyType": "HASH"}, {"AttributeName": "createdAt", "KeyType": "RANGE"}],
     "inverse": "caw_ddb_key_schema_parse", "input_edge": "DdbKeys", "output_edge": "DdbKeySchema"},
    {"id": "prim:leaf:caw_ddb_attr_value_unwrap", "mutator": "caw_ddb_attr_value_unwrap", "format": "dynamodb_shape",
     "fixture": {"S": "hello"}, "expected": "hello", "input_edge": "DdbAttributeValue", "output_edge": "PlainValue"},
    {"id": "prim:leaf:caw_ddb_item_to_plain", "mutator": "caw_ddb_item_to_plain", "format": "dynamodb_shape",
     "fixture": {"id": {"S": "u1"}, "count": {"N": "5"}}, "expected": {"id": "u1", "count": "5"},
     "input_edge": "DdbItem", "output_edge": "PlainRecord"},

    # CloudWatch Logs event
    {"id": "prim:leaf:caw_cloudwatch_event_parse", "mutator": "caw_cloudwatch_event_parse", "format": "cloudwatch_log_event",
     "fixture": '{"timestamp": 1633024800000, "message": "ERROR db timeout"}',
     "expected": {"timestamp": 1633024800000, "message": "ERROR db timeout"},
     "input_edge": "CloudWatchLogEventJson", "output_edge": "CloudWatchLogEvent"},
    {"id": "prim:leaf:caw_cloudwatch_event_message", "mutator": "caw_cloudwatch_event_message", "format": "cloudwatch_log_event",
     "fixture": '{"timestamp": 1633024800000, "message": "user u1 logged in"}', "expected": "user u1 logged in",
     "input_edge": "CloudWatchLogEventJson", "output_edge": "LogMessage"},

    # SQS / SNS message envelope
    {"id": "prim:leaf:caw_sqs_envelope_wrap", "mutator": "caw_sqs_envelope_wrap", "format": "sqs_sns_message",
     "fixture": "order-123 shipped", "expected": {"MessageBody": "order-123 shipped"},
     "inverse": "caw_sqs_envelope_unwrap", "input_edge": "MessageBody", "output_edge": "SqsMessageEnvelope"},
    {"id": "prim:leaf:caw_sqs_envelope_unwrap", "mutator": "caw_sqs_envelope_unwrap", "format": "sqs_sns_message",
     "fixture": {"MessageBody": "payload-x"}, "expected": "payload-x",
     "inverse": "caw_sqs_envelope_wrap", "input_edge": "SqsMessageEnvelope", "output_edge": "MessageBody"},
    {"id": "prim:leaf:caw_sns_message_extract", "mutator": "caw_sns_message_extract", "format": "sqs_sns_message",
     "fixture": '{"Type": "Notification", "MessageId": "abc", "Message": "hello world"}', "expected": "hello world",
     "input_edge": "SnsNotificationJson", "output_edge": "SnsMessage"},

    # Terraform aws_* resource block
    {"id": "prim:leaf:caw_tf_aws_resource_emit", "mutator": "caw_tf_aws_resource_emit", "format": "terraform_aws_resource",
     "fixture": {"type": "aws_s3_bucket", "name": "data", "attrs": {"bucket": "my-data", "acl": "private"}},
     "expected": 'resource "aws_s3_bucket" "data" {\n  acl = "private"\n  bucket = "my-data"\n}',
     "input_edge": "TerraformResourceSpec", "output_edge": "TerraformHcl"},
]

#: deliberately-wrong leaf — the proof gate MUST leave it candidate (never persisted as proven-deterministic)
NEGATIVE_SPEC: dict[str, Any] = {
    "id": "prim:leaf:caw_WRONG_expected", "mutator": "caw_arn_service", "format": "aws_arn",
    "fixture": "arn:aws:s3:::bucket", "expected": "WRONG", "input_edge": "AwsArn", "output_edge": "ArnService"}


# ── GATED-EFFECT candidates: NETWORK / EFFECTFUL AWS capabilities. NEVER run through the proof runner, NEVER
#    serve_truth. Each declares effect + proof_obligation (a live integration test with a credential) + typed edges. ──
GATED_EFFECT_SPECS: list[dict[str, Any]] = [
    {"id": "prim:gated:caw_s3_get_object", "capability": "S3 GetObject — read an object body from a bucket",
     "effect": "network_read", "proof_obligation": "live integration test against a sandbox S3 bucket with an AWS credential",
     "input_edge": "S3Uri", "output_edge": "S3ObjectBody", "format": "s3_uri"},
    {"id": "prim:gated:caw_s3_put_object", "capability": "S3 PutObject — write an object body to a bucket",
     "effect": "network_write", "proof_obligation": "live integration test against a sandbox S3 bucket with an AWS credential",
     "input_edge": "S3PutRequest", "output_edge": "S3PutResult", "format": "s3_uri"},
    {"id": "prim:gated:caw_dynamodb_put_item", "capability": "DynamoDB PutItem — write an item to a table",
     "effect": "network_write", "proof_obligation": "live integration test against a sandbox DynamoDB table with an AWS credential",
     "input_edge": "DdbItem", "output_edge": "DdbPutResult", "format": "dynamodb_shape"},
    {"id": "prim:gated:caw_dynamodb_query", "capability": "DynamoDB Query — read items by key condition",
     "effect": "network_read", "proof_obligation": "live integration test against a sandbox DynamoDB table with an AWS credential",
     "input_edge": "DdbQueryRequest", "output_edge": "DdbQueryResult", "format": "dynamodb_shape"},
    {"id": "prim:gated:caw_sqs_send_message", "capability": "SQS SendMessage — enqueue a message to a queue",
     "effect": "network_write", "proof_obligation": "live integration test against a sandbox SQS queue with an AWS credential",
     "input_edge": "SqsMessageEnvelope", "output_edge": "SqsSendResult", "format": "sqs_sns_message"},
    {"id": "prim:gated:caw_sns_publish", "capability": "SNS Publish — publish a message to a topic",
     "effect": "network_write", "proof_obligation": "live integration test against a sandbox SNS topic with an AWS credential",
     "input_edge": "SnsMessage", "output_edge": "SnsPublishResult", "format": "sqs_sns_message"},
    {"id": "prim:gated:caw_cloudwatch_put_log_events", "capability": "CloudWatch Logs PutLogEvents — ship log events to a stream",
     "effect": "network_write", "proof_obligation": "live integration test against a sandbox CloudWatch log stream with an AWS credential",
     "input_edge": "CloudWatchLogEvent", "output_edge": "PutLogEventsResult", "format": "cloudwatch_log_event"},
    {"id": "prim:gated:caw_sts_assume_role", "capability": "STS AssumeRole — obtain temporary credentials for a role ARN",
     "effect": "network_read", "proof_obligation": "live integration test against AWS STS with a base credential",
     "input_edge": "AwsArn", "output_edge": "StsCredentials", "format": "aws_arn"},
    {"id": "prim:gated:caw_terraform_apply", "capability": "terraform apply — provision aws_* resources against a live account",
     "effect": "network_write", "proof_obligation": "live integration test in a sandbox AWS account with credentials + state backend",
     "input_edge": "TerraformHcl", "output_edge": "TerraformApplyResult", "format": "terraform_aws_resource"},
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
        "generator": "scripts/domain_cloud_aws.py",
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
                "scripts/build_edge_type_retrofit.py). gated_effect_candidate rows: network/effectful AWS calls are NEVER "
                "proven and stay candidate/serves_truth=false with an effect + proof_obligation. Synthetic/public shapes "
                "only; NO insurance; NO real credentials/PII. Counts are separate and honest.",
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
    err = run_primitive_proof("prim:leaf:caw_EXEC_ERROR", "caw_arn_parse", object(), "irrelevant")

    manifest = build_manifest(rows, gated)
    valid_effects = {"network_read", "network_write", "model_call", "file_write"}

    checks: list[tuple[str, bool]] = [
        (">=25 deterministic leaves declared", len(LEAF_SPECS) >= 25),
        ("unique proven primitive ids", len(set(ids)) == len(ids)),
        (">=25 leaves PROVE serves_truth=true via an executed proof", len(rows) >= 25),
        ("every proven receipt is L7_executed_proof with all sub-proofs passing",
         all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"])
             for (_s, r) in proven if r["serves_truth"] is True)),
        ("EVERY proven row carries non-null input+output edge type ids", len(typed) == len(rows)),
        ("manifest typed == proven_deterministic", manifest["typed"] == manifest["proven_deterministic"]),
        ("all 7 target formats are covered", set(manifest["formats_covered"]) == {
            "aws_arn", "s3_uri", "iam_policy_document", "dynamodb_shape", "cloudwatch_log_event",
            "sqs_sns_message", "terraform_aws_resource"}),
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
        print("FAIL - domain_cloud_aws:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - domain_cloud_aws: {len(rows)} WORKABLE (proven + TYPED) deterministic SHAPE leaves for "
          f"'{DOMAIN}' (serves_truth=true, L7_executed_proof; typed=={len(rows)}) across 7 AWS shape formats; "
          f"{len(roundtrip_specs)} inverse pairs proven reversible via roundtrip; {len(gated)} network/effectful AWS "
          "capabilities declared as GATED-EFFECT candidates (serves_truth=false, effect + proof_obligation). "
          "A deliberately-wrong leaf and an un-runnable fixture correctly stay candidate. Synthetic shapes; no secrets.")
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
