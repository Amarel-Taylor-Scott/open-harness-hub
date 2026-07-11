#!/usr/bin/env python3
"""scripts.domain_cloud_azure_k8s — breadth primitives for the `cloud_azure_k8s` domain.

Deterministic Azure + container SHAPE work: Azure resource-id parse/build/validate, Blob URI parse/build/validate,
Docker/ACR image-ref parse/build/validate, Kubernetes manifest build/validate (Deployment/Service/ConfigMap),
manifest<->JSON convert, label-selector + namespaced-name shaping, Helm values flatten/unflatten + `--set` expansion,
container env-list shaping, secret/config-map ENV REFERENCE shaping (references by name+key only — NEVER a secret
value), and Azure storage connection-string parse/emit over a SYNTHETIC (non-real) key. ADD-ONLY parallel path — it
IMPORTS the shared machinery and never edits it:
  * `run_primitive_proof` / `MUTATOR_REGISTRY` / `_receipt` from `scripts.mutator_registry` — the proof-runner
    EXECUTES each mutator against a fixture and flips serves_truth false->true ONLY on a PASSING executed proof
    (fixture-behavior + determinism, plus a roundtrip when the leaf declares an inverse);
  * `canonicalize_edge` from `scripts.build_edge_type_retrofit` — folds each leaf's logical edge labels to canonical
    type_ids so a proven leaf is also TYPED (input_edge_type_id + output_edge_type_id) and can chain.

Repo law honored HONESTLY: serves_truth=true is set ONLY by an executed passing proof of a DETERMINISTIC transform.
NETWORK/EFFECTFUL operations (an actual ARM template deploy, `kubectl apply`/`get`, a Blob download/upload, an ACR
image push, a Key Vault secret read, `az aks get-credentials`, a Helm release install, an Azure validate-API call)
are NEVER run through the proof runner and NEVER serve truth — they are declared as GATED-EFFECT candidates
{candidate:true, serves_truth:false, effect, proof_obligation, input/output edge type ids}. The manifest reports
proven_deterministic, typed, and gated_effect_candidates as SEPARATE counts.

DOMAIN LAWS honored: no insurance; no clinical/health-risk; synthetic/public shapes only — NO real PII/secrets
(the secret/config-map primitives operate on the REFERENCE shape, and the connection-string fixtures use a clearly
synthetic key). Deterministic + offline: no network, no LLM, no wall-clock, no RNG (fixed literal timestamp; stdlib
only).
CLI: --self-test | --write.

Register tuple for the shared proof suite (REPORT ONLY — this module does NOT self-register):
    ("_repos/shared-backend-components/scripts/domain_cloud_azure_k8s.py", "domain_cloud_azure_k8s")
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

DOMAIN = "cloud_azure_k8s"
FAMILY = "cloud_azure_k8s"
_FIXED_UTC = "2026-07-03"  # fixed literal timestamp — NO wall-clock (repo law: deterministic + offline)

OUT_DIR = _resource("data") / "dev-intel" / "domain_primitives"
OUT_JSONL = OUT_DIR / "domain_cloud_azure_k8s.jsonl"
OUT_MANIFEST = OUT_DIR / "manifest_cloud_azure_k8s.json"


# ── PURE deterministic mutators, contract (payload, **kwargs) -> (output, receipt). Family-prefixed `caz_` so they
#    never collide with existing registry entries; registered via setdefault (idempotent, never overwrites). ──

# Azure resource id -----------------------------------------------------------------------------------------
# Canonical form: /subscriptions/{sub}/resourceGroups/{rg}/providers/{ns}/{type}/{name}
def caz_resource_id_parse(rid: str, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    parts = rid.strip("/").split("/")
    out = {
        "subscription_id": parts[1],
        "resource_group": parts[3],
        "provider_namespace": parts[5],
        "resource_type": parts[6],
        "resource_name": parts[7],
    }
    return out, _receipt("caz_resource_id_parse", before=rid, after=out, lossless=True, note="azure resource id text -> parts; caz_resource_id_build restores")


def caz_resource_id_build(d: dict[str, str], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = (f"/subscriptions/{d['subscription_id']}/resourceGroups/{d['resource_group']}"
           f"/providers/{d['provider_namespace']}/{d['resource_type']}/{d['resource_name']}")
    return out, _receipt("caz_resource_id_build", before=d, after=out, lossless=True, note="parts -> azure resource id text; caz_resource_id_parse restores")


def caz_resource_id_validate(rid: str, **_kw: Any) -> tuple[bool, dict[str, Any]]:
    parts = rid.strip("/").split("/")
    out = (len(parts) == 8 and parts[0] == "subscriptions" and parts[2] == "resourceGroups"
           and parts[4] == "providers" and all(parts))
    return out, _receipt("caz_resource_id_validate", before=rid, after=out, lossless=False, note="azure resource id well-formedness -> bool")


# Azure Blob URI --------------------------------------------------------------------------------------------
# Form: https://{account}.blob.core.windows.net/{container}/{blob}
def caz_blob_uri_parse(uri: str, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    rest = uri.split("://", 1)[1]
    host, _, path = rest.partition("/")
    account = host.split(".blob.core.windows.net")[0]
    container, _, blob = path.partition("/")
    out = {"account": account, "container": container, "blob": blob}
    return out, _receipt("caz_blob_uri_parse", before=uri, after=out, lossless=True, note="blob uri -> {account,container,blob}; caz_blob_uri_build restores")


def caz_blob_uri_build(d: dict[str, str], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = f"https://{d['account']}.blob.core.windows.net/{d['container']}/{d['blob']}"
    return out, _receipt("caz_blob_uri_build", before=d, after=out, lossless=True, note="{account,container,blob} -> blob uri; caz_blob_uri_parse restores")


def caz_blob_uri_validate(uri: str, **_kw: Any) -> tuple[bool, dict[str, Any]]:
    out = uri.startswith("https://") and ".blob.core.windows.net/" in uri
    return out, _receipt("caz_blob_uri_validate", before=uri, after=out, lossless=False, note="blob uri well-formedness -> bool")


# Docker / ACR image ref ------------------------------------------------------------------------------------
# Form: [registry[:port]/]repository[:tag][@digest]
def caz_image_ref_parse(ref: str, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    remainder, _, digest = ref.partition("@")
    registry = ""
    name_tag = remainder
    slash = remainder.find("/")
    if slash != -1:
        first = remainder[:slash]
        if "." in first or ":" in first or first == "localhost":
            registry = first
            name_tag = remainder[slash + 1:]
    repo, _, tag = name_tag.partition(":")
    out = {"registry": registry, "repository": repo, "tag": tag, "digest": digest}
    return out, _receipt("caz_image_ref_parse", before=ref, after=out, lossless=True, note="image ref -> {registry,repository,tag,digest}; caz_image_ref_build restores")


def caz_image_ref_build(d: dict[str, str], **_kw: Any) -> tuple[str, dict[str, Any]]:
    ref = d["repository"]
    if d.get("registry"):
        ref = f"{d['registry']}/{ref}"
    if d.get("tag"):
        ref = f"{ref}:{d['tag']}"
    if d.get("digest"):
        ref = f"{ref}@{d['digest']}"
    return ref, _receipt("caz_image_ref_build", before=d, after=ref, lossless=True, note="{registry,repository,tag,digest} -> image ref; caz_image_ref_parse restores")


def caz_image_ref_validate(ref: str, **_kw: Any) -> tuple[bool, dict[str, Any]]:
    remainder = ref.partition("@")[0]
    name_tag = remainder.split("/")[-1]
    repo = name_tag.partition(":")[0]
    out = bool(repo) and " " not in ref
    return out, _receipt("caz_image_ref_validate", before=ref, after=out, lossless=False, note="image ref well-formedness -> bool")


# Kubernetes manifests --------------------------------------------------------------------------------------
def caz_k8s_deployment_build(spec: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    name = spec["name"]
    out = {
        "apiVersion": "apps/v1", "kind": "Deployment",
        "metadata": {"name": name},
        "spec": {
            "replicas": spec["replicas"],
            "selector": {"matchLabels": {"app": name}},
            "template": {
                "metadata": {"labels": {"app": name}},
                "spec": {"containers": [{"image": spec["image"], "name": name}]},
            },
        },
    }
    return out, _receipt("caz_k8s_deployment_build", before=spec, after=out, lossless=False, note="{name,image,replicas} -> Deployment manifest")


def caz_k8s_deployment_validate(m: dict[str, Any], **_kw: Any) -> tuple[bool, dict[str, Any]]:
    try:
        out = (m.get("kind") == "Deployment" and m.get("apiVersion") == "apps/v1"
               and bool(m["metadata"]["name"]) and isinstance(m["spec"]["replicas"], int)
               and len(m["spec"]["template"]["spec"]["containers"]) >= 1)
    except (KeyError, TypeError):
        out = False
    return out, _receipt("caz_k8s_deployment_validate", before=m, after=out, lossless=False, note="Deployment manifest structural check -> bool")


def caz_k8s_service_build(spec: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    name = spec["name"]
    out = {
        "apiVersion": "v1", "kind": "Service",
        "metadata": {"name": name},
        "spec": {"selector": {"app": name}, "ports": [{"port": spec["port"], "targetPort": spec["target_port"]}]},
    }
    return out, _receipt("caz_k8s_service_build", before=spec, after=out, lossless=False, note="{name,port,target_port} -> Service manifest")


def caz_k8s_service_validate(m: dict[str, Any], **_kw: Any) -> tuple[bool, dict[str, Any]]:
    try:
        out = (m.get("kind") == "Service" and m.get("apiVersion") == "v1"
               and bool(m["metadata"]["name"]) and len(m["spec"]["ports"]) >= 1
               and isinstance(m["spec"]["ports"][0]["port"], int))
    except (KeyError, TypeError, IndexError):
        out = False
    return out, _receipt("caz_k8s_service_validate", before=m, after=out, lossless=False, note="Service manifest structural check -> bool")


def caz_k8s_configmap_build(spec: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {"apiVersion": "v1", "kind": "ConfigMap", "metadata": {"name": spec["name"]}, "data": spec["data"]}
    return out, _receipt("caz_k8s_configmap_build", before=spec, after=out, lossless=True, note="{name,data} -> ConfigMap manifest")


def caz_k8s_configmap_validate(m: dict[str, Any], **_kw: Any) -> tuple[bool, dict[str, Any]]:
    try:
        data = m["data"]
        out = (m.get("kind") == "ConfigMap" and m.get("apiVersion") == "v1"
               and bool(m["metadata"]["name"]) and isinstance(data, dict)
               and all(isinstance(k, str) and isinstance(v, str) for k, v in data.items()))
    except (KeyError, TypeError):
        out = False
    return out, _receipt("caz_k8s_configmap_validate", before=m, after=out, lossless=False, note="ConfigMap manifest structural check -> bool")


def caz_k8s_manifest_to_json(m: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = json.dumps(m, sort_keys=True)
    return out, _receipt("caz_k8s_manifest_to_json", before=m, after=out, lossless=True, note="manifest -> canonical json text; caz_k8s_manifest_from_json restores")


def caz_k8s_manifest_from_json(text: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = json.loads(text)
    return out, _receipt("caz_k8s_manifest_from_json", before=text, after=out, lossless=True, note="json text -> manifest")


def caz_k8s_resource_kind(m: dict[str, Any], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = m.get("kind", "")
    return out, _receipt("caz_k8s_resource_kind", before=m, after=out, lossless=False, note="manifest -> kind string")


def caz_k8s_label_selector_emit(labels: dict[str, str], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = ",".join(f"{k}={labels[k]}" for k in sorted(labels))
    return out, _receipt("caz_k8s_label_selector_emit", before=labels, after=out, lossless=True, note="label map -> sorted equality selector; caz_k8s_label_selector_parse restores")


def caz_k8s_label_selector_parse(sel: str, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    out: dict[str, str] = {}
    for pair in sel.split(","):
        if not pair:
            continue
        k, _, v = pair.partition("=")
        out[k] = v
    return out, _receipt("caz_k8s_label_selector_parse", before=sel, after=out, lossless=True, note="equality selector -> label map")


def caz_k8s_namespace_qualify(d: dict[str, str], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = f"{d['namespace']}/{d['name']}"
    return out, _receipt("caz_k8s_namespace_qualify", before=d, after=out, lossless=True, note="{namespace,name} -> namespaced name; caz_k8s_namespaced_name_parse restores")


def caz_k8s_namespaced_name_parse(s: str, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    ns, _, name = s.partition("/")
    out = {"namespace": ns, "name": name}
    return out, _receipt("caz_k8s_namespaced_name_parse", before=s, after=out, lossless=True, note="namespaced name -> {namespace,name}")


# Helm values -----------------------------------------------------------------------------------------------
def caz_helm_values_flatten(d: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out: dict[str, Any] = {}

    def _rec(obj: dict[str, Any], prefix: str) -> None:
        for k in sorted(obj):
            v = obj[k]
            key = f"{prefix}{k}"
            if isinstance(v, dict):
                _rec(v, key + ".")
            else:
                out[key] = v

    _rec(d, "")
    return out, _receipt("caz_helm_values_flatten", before=d, after=out, lossless=True, note="nested helm values -> dot-path flat map; caz_helm_values_unflatten restores")


def caz_helm_values_unflatten(flat: dict[str, Any], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out: dict[str, Any] = {}
    for key in flat:
        parts = key.split(".")
        cur = out
        for p in parts[:-1]:
            cur = cur.setdefault(p, {})
        cur[parts[-1]] = flat[key]
    return out, _receipt("caz_helm_values_unflatten", before=flat, after=out, lossless=True, note="dot-path flat map -> nested helm values")


def caz_helm_set_to_values(expr: str, **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    path, _, value = expr.partition("=")
    parts = path.split(".")
    out: dict[str, Any] = {}
    cur = out
    for p in parts[:-1]:
        cur = cur.setdefault(p, {})
    cur[parts[-1]] = value
    return out, _receipt("caz_helm_set_to_values", before=expr, after=out, lossless=False, note="helm --set 'a.b=c' expression -> nested values")


# Container env + secret/config-map REFERENCE shapes (references only — NO secret values) --------------------
def caz_env_list_emit(d: dict[str, str], **_kw: Any) -> tuple[list[dict[str, str]], dict[str, Any]]:
    out = [{"name": k, "value": d[k]} for k in sorted(d)]
    return out, _receipt("caz_env_list_emit", before=d, after=out, lossless=True, note="env map -> k8s container env list; caz_env_list_parse restores")


def caz_env_list_parse(items: list[dict[str, str]], **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    out = {e["name"]: e["value"] for e in items}
    return out, _receipt("caz_env_list_parse", before=items, after=out, lossless=True, note="k8s container env list -> env map")


def caz_secret_ref_build(d: dict[str, str], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    # SHAPE only: references a secret by name+key; carries NO secret value.
    out = {"name": d["env_name"], "valueFrom": {"secretKeyRef": {"name": d["secret_name"], "key": d["secret_key"]}}}
    return out, _receipt("caz_secret_ref_build", before=d, after=out, lossless=True, note="{env_name,secret_name,secret_key} -> secretKeyRef env shape (reference only); caz_secret_ref_parse restores")


def caz_secret_ref_parse(ref: dict[str, Any], **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    skr = ref["valueFrom"]["secretKeyRef"]
    out = {"env_name": ref["name"], "secret_name": skr["name"], "secret_key": skr["key"]}
    return out, _receipt("caz_secret_ref_parse", before=ref, after=out, lossless=True, note="secretKeyRef env shape -> {env_name,secret_name,secret_key}")


def caz_configmap_ref_build(d: dict[str, str], **_kw: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    out = {"name": d["env_name"], "valueFrom": {"configMapKeyRef": {"name": d["configmap_name"], "key": d["configmap_key"]}}}
    return out, _receipt("caz_configmap_ref_build", before=d, after=out, lossless=True, note="{env_name,configmap_name,configmap_key} -> configMapKeyRef env shape; caz_configmap_ref_parse restores")


def caz_configmap_ref_parse(ref: dict[str, Any], **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    cmr = ref["valueFrom"]["configMapKeyRef"]
    out = {"env_name": ref["name"], "configmap_name": cmr["name"], "configmap_key": cmr["key"]}
    return out, _receipt("caz_configmap_ref_parse", before=ref, after=out, lossless=True, note="configMapKeyRef env shape -> {env_name,configmap_name,configmap_key}")


# Azure storage connection string (SYNTHETIC key only — shape parse/emit) ------------------------------------
def caz_conn_string_parse(s: str, **_kw: Any) -> tuple[dict[str, str], dict[str, Any]]:
    out: dict[str, str] = {}
    for pair in s.split(";"):
        if not pair:
            continue
        k, _, v = pair.partition("=")
        out[k] = v
    return out, _receipt("caz_conn_string_parse", before=s, after=out, lossless=True, note="azure storage connection string -> key/value map (synthetic key)")


def caz_conn_string_emit(d: dict[str, str], **_kw: Any) -> tuple[str, dict[str, Any]]:
    out = ";".join(f"{k}={d[k]}" for k in sorted(d))
    return out, _receipt("caz_conn_string_emit", before=d, after=out, lossless=True, note="key/value map -> sorted connection string; caz_conn_string_parse restores")


#: new pure mutators to plug into the shared registry (idempotent setdefault — never overwrites an existing entry)
_NEW_MUTATORS = {
    "caz_resource_id_parse": caz_resource_id_parse, "caz_resource_id_build": caz_resource_id_build,
    "caz_resource_id_validate": caz_resource_id_validate,
    "caz_blob_uri_parse": caz_blob_uri_parse, "caz_blob_uri_build": caz_blob_uri_build,
    "caz_blob_uri_validate": caz_blob_uri_validate,
    "caz_image_ref_parse": caz_image_ref_parse, "caz_image_ref_build": caz_image_ref_build,
    "caz_image_ref_validate": caz_image_ref_validate,
    "caz_k8s_deployment_build": caz_k8s_deployment_build, "caz_k8s_deployment_validate": caz_k8s_deployment_validate,
    "caz_k8s_service_build": caz_k8s_service_build, "caz_k8s_service_validate": caz_k8s_service_validate,
    "caz_k8s_configmap_build": caz_k8s_configmap_build, "caz_k8s_configmap_validate": caz_k8s_configmap_validate,
    "caz_k8s_manifest_to_json": caz_k8s_manifest_to_json, "caz_k8s_manifest_from_json": caz_k8s_manifest_from_json,
    "caz_k8s_resource_kind": caz_k8s_resource_kind,
    "caz_k8s_label_selector_emit": caz_k8s_label_selector_emit, "caz_k8s_label_selector_parse": caz_k8s_label_selector_parse,
    "caz_k8s_namespace_qualify": caz_k8s_namespace_qualify, "caz_k8s_namespaced_name_parse": caz_k8s_namespaced_name_parse,
    "caz_helm_values_flatten": caz_helm_values_flatten, "caz_helm_values_unflatten": caz_helm_values_unflatten,
    "caz_helm_set_to_values": caz_helm_set_to_values,
    "caz_env_list_emit": caz_env_list_emit, "caz_env_list_parse": caz_env_list_parse,
    "caz_secret_ref_build": caz_secret_ref_build, "caz_secret_ref_parse": caz_secret_ref_parse,
    "caz_configmap_ref_build": caz_configmap_ref_build, "caz_configmap_ref_parse": caz_configmap_ref_parse,
    "caz_conn_string_parse": caz_conn_string_parse, "caz_conn_string_emit": caz_conn_string_emit,
}


def register_new_mutators() -> None:
    """Plug the domain's pure mutators into the shared MUTATOR_REGISTRY (registration, not a rewrite). Idempotent."""
    for name, fn in _NEW_MUTATORS.items():
        MUTATOR_REGISTRY.setdefault(name, fn)


register_new_mutators()


# Reusable manifest fixtures (built once, referenced by both build-expected and validate-fixture specs).
_DEPLOY_MANIFEST = {
    "apiVersion": "apps/v1", "kind": "Deployment",
    "metadata": {"name": "web"},
    "spec": {
        "replicas": 3,
        "selector": {"matchLabels": {"app": "web"}},
        "template": {"metadata": {"labels": {"app": "web"}},
                     "spec": {"containers": [{"image": "nginx:1.25", "name": "web"}]}},
    },
}
_SERVICE_MANIFEST = {
    "apiVersion": "v1", "kind": "Service", "metadata": {"name": "web"},
    "spec": {"selector": {"app": "web"}, "ports": [{"port": 80, "targetPort": 8080}]},
}
_CONFIGMAP_MANIFEST = {
    "apiVersion": "v1", "kind": "ConfigMap", "metadata": {"name": "app-config"}, "data": {"LOG_LEVEL": "info"},
}


# ── the leaf primitives: each a REAL capability with a concrete fixture + expected (+ inverse where roundtrip holds).
# spec fields: id, mutator, fixture, expected, args?, inverse?, capability, input_edge, output_edge ──
LEAF_SPECS: list[dict[str, Any]] = [
    # Azure resource id
    {"id": "prim:caz:resource_id_parse", "mutator": "caz_resource_id_parse",
     "fixture": "/subscriptions/sub-0000/resourceGroups/rg-demo/providers/Microsoft.Compute/virtualMachines/vm-web",
     "expected": {"subscription_id": "sub-0000", "resource_group": "rg-demo",
                  "provider_namespace": "Microsoft.Compute", "resource_type": "virtualMachines",
                  "resource_name": "vm-web"},
     "capability": "parse", "input_edge": "AzureResourceId", "output_edge": "AzureResourceParts"},
    {"id": "prim:caz:resource_id_build", "mutator": "caz_resource_id_build",
     "fixture": {"subscription_id": "sub-0000", "resource_group": "rg-demo",
                 "provider_namespace": "Microsoft.Compute", "resource_type": "virtualMachines",
                 "resource_name": "vm-web"},
     "expected": "/subscriptions/sub-0000/resourceGroups/rg-demo/providers/Microsoft.Compute/virtualMachines/vm-web",
     "inverse": "caz_resource_id_parse", "capability": "emit",
     "input_edge": "AzureResourceParts", "output_edge": "AzureResourceId"},
    {"id": "prim:caz:resource_id_validate", "mutator": "caz_resource_id_validate",
     "fixture": "/subscriptions/sub-0000/resourceGroups/rg-demo/providers/Microsoft.Storage/storageAccounts/acct",
     "expected": True, "capability": "validate", "input_edge": "AzureResourceId", "output_edge": "Boolean"},

    # Azure Blob URI
    {"id": "prim:caz:blob_uri_parse", "mutator": "caz_blob_uri_parse",
     "fixture": "https://synthacct.blob.core.windows.net/mycontainer/path/to/blob.json",
     "expected": {"account": "synthacct", "container": "mycontainer", "blob": "path/to/blob.json"},
     "capability": "parse", "input_edge": "BlobUri", "output_edge": "BlobParts"},
    {"id": "prim:caz:blob_uri_build", "mutator": "caz_blob_uri_build",
     "fixture": {"account": "synthacct", "container": "mycontainer", "blob": "path/to/blob.json"},
     "expected": "https://synthacct.blob.core.windows.net/mycontainer/path/to/blob.json",
     "inverse": "caz_blob_uri_parse", "capability": "emit", "input_edge": "BlobParts", "output_edge": "BlobUri"},
    {"id": "prim:caz:blob_uri_validate", "mutator": "caz_blob_uri_validate",
     "fixture": "https://synthacct.blob.core.windows.net/mycontainer/blob.json", "expected": True,
     "capability": "validate", "input_edge": "BlobUri", "output_edge": "Boolean"},

    # Docker / ACR image ref
    {"id": "prim:caz:image_ref_parse", "mutator": "caz_image_ref_parse",
     "fixture": "myregistry.azurecr.io/team/app:1.2.3",
     "expected": {"registry": "myregistry.azurecr.io", "repository": "team/app", "tag": "1.2.3", "digest": ""},
     "capability": "parse", "input_edge": "ImageRef", "output_edge": "ImageRefParts"},
    {"id": "prim:caz:image_ref_build", "mutator": "caz_image_ref_build",
     "fixture": {"registry": "myregistry.azurecr.io", "repository": "team/app", "tag": "1.2.3", "digest": ""},
     "expected": "myregistry.azurecr.io/team/app:1.2.3", "inverse": "caz_image_ref_parse",
     "capability": "emit", "input_edge": "ImageRefParts", "output_edge": "ImageRef"},
    {"id": "prim:caz:image_ref_validate", "mutator": "caz_image_ref_validate",
     "fixture": "myregistry.azurecr.io/team/app:1.2.3", "expected": True,
     "capability": "validate", "input_edge": "ImageRef", "output_edge": "Boolean"},

    # Kubernetes Deployment
    {"id": "prim:caz:k8s_deployment_build", "mutator": "caz_k8s_deployment_build",
     "fixture": {"name": "web", "image": "nginx:1.25", "replicas": 3}, "expected": _DEPLOY_MANIFEST,
     "capability": "emit", "input_edge": "DeploymentSpec", "output_edge": "K8sManifest"},
    {"id": "prim:caz:k8s_deployment_validate", "mutator": "caz_k8s_deployment_validate",
     "fixture": _DEPLOY_MANIFEST, "expected": True, "capability": "validate",
     "input_edge": "K8sManifest", "output_edge": "Boolean"},

    # Kubernetes Service
    {"id": "prim:caz:k8s_service_build", "mutator": "caz_k8s_service_build",
     "fixture": {"name": "web", "port": 80, "target_port": 8080}, "expected": _SERVICE_MANIFEST,
     "capability": "emit", "input_edge": "ServiceSpec", "output_edge": "K8sManifest"},
    {"id": "prim:caz:k8s_service_validate", "mutator": "caz_k8s_service_validate",
     "fixture": _SERVICE_MANIFEST, "expected": True, "capability": "validate",
     "input_edge": "K8sManifest", "output_edge": "Boolean"},

    # Kubernetes ConfigMap
    {"id": "prim:caz:k8s_configmap_build", "mutator": "caz_k8s_configmap_build",
     "fixture": {"name": "app-config", "data": {"LOG_LEVEL": "info"}}, "expected": _CONFIGMAP_MANIFEST,
     "capability": "emit", "input_edge": "ConfigMapSpec", "output_edge": "K8sManifest"},
    {"id": "prim:caz:k8s_configmap_validate", "mutator": "caz_k8s_configmap_validate",
     "fixture": _CONFIGMAP_MANIFEST, "expected": True, "capability": "validate",
     "input_edge": "K8sManifest", "output_edge": "Boolean"},

    # Manifest <-> JSON + kind
    {"id": "prim:caz:k8s_manifest_to_json", "mutator": "caz_k8s_manifest_to_json",
     "fixture": {"apiVersion": "v1", "kind": "ConfigMap", "metadata": {"name": "cfg"}},
     "expected": '{"apiVersion": "v1", "kind": "ConfigMap", "metadata": {"name": "cfg"}}',
     "inverse": "caz_k8s_manifest_from_json", "capability": "convert",
     "input_edge": "K8sManifest", "output_edge": "ManifestJson"},
    {"id": "prim:caz:k8s_manifest_from_json", "mutator": "caz_k8s_manifest_from_json",
     "fixture": '{"apiVersion": "v1", "kind": "ConfigMap", "metadata": {"name": "cfg"}}',
     "expected": {"apiVersion": "v1", "kind": "ConfigMap", "metadata": {"name": "cfg"}},
     "capability": "convert", "input_edge": "ManifestJson", "output_edge": "K8sManifest"},
    {"id": "prim:caz:k8s_resource_kind", "mutator": "caz_k8s_resource_kind",
     "fixture": _DEPLOY_MANIFEST, "expected": "Deployment", "capability": "parse",
     "input_edge": "K8sManifest", "output_edge": "ResourceKind"},

    # Label selector
    {"id": "prim:caz:k8s_label_selector_emit", "mutator": "caz_k8s_label_selector_emit",
     "fixture": {"app": "web", "tier": "frontend"}, "expected": "app=web,tier=frontend",
     "inverse": "caz_k8s_label_selector_parse", "capability": "emit",
     "input_edge": "LabelMap", "output_edge": "LabelSelector"},
    {"id": "prim:caz:k8s_label_selector_parse", "mutator": "caz_k8s_label_selector_parse",
     "fixture": "app=web,tier=frontend", "expected": {"app": "web", "tier": "frontend"},
     "capability": "parse", "input_edge": "LabelSelector", "output_edge": "LabelMap"},

    # Namespaced name
    {"id": "prim:caz:k8s_namespace_qualify", "mutator": "caz_k8s_namespace_qualify",
     "fixture": {"namespace": "prod", "name": "web-svc"}, "expected": "prod/web-svc",
     "inverse": "caz_k8s_namespaced_name_parse", "capability": "emit",
     "input_edge": "NamespacedParts", "output_edge": "NamespacedName"},
    {"id": "prim:caz:k8s_namespaced_name_parse", "mutator": "caz_k8s_namespaced_name_parse",
     "fixture": "prod/web-svc", "expected": {"namespace": "prod", "name": "web-svc"},
     "capability": "parse", "input_edge": "NamespacedName", "output_edge": "NamespacedParts"},

    # Helm values
    {"id": "prim:caz:helm_values_flatten", "mutator": "caz_helm_values_flatten",
     "fixture": {"image": {"repository": "nginx", "tag": "1.25.0"}, "replicaCount": 3, "service": {"port": 80}},
     "expected": {"image.repository": "nginx", "image.tag": "1.25.0", "replicaCount": 3, "service.port": 80},
     "inverse": "caz_helm_values_unflatten", "capability": "convert",
     "input_edge": "HelmValues", "output_edge": "HelmFlatValues"},
    {"id": "prim:caz:helm_values_unflatten", "mutator": "caz_helm_values_unflatten",
     "fixture": {"image.repository": "nginx", "image.tag": "1.25.0", "replicaCount": 3, "service.port": 80},
     "expected": {"image": {"repository": "nginx", "tag": "1.25.0"}, "replicaCount": 3, "service": {"port": 80}},
     "capability": "convert", "input_edge": "HelmFlatValues", "output_edge": "HelmValues"},
    {"id": "prim:caz:helm_set_to_values", "mutator": "caz_helm_set_to_values",
     "fixture": "image.tag=1.4.2", "expected": {"image": {"tag": "1.4.2"}}, "capability": "convert",
     "input_edge": "HelmSetExpr", "output_edge": "HelmValues"},

    # Container env list
    {"id": "prim:caz:env_list_emit", "mutator": "caz_env_list_emit",
     "fixture": {"LOG_LEVEL": "info", "PORT": "8080"},
     "expected": [{"name": "LOG_LEVEL", "value": "info"}, {"name": "PORT", "value": "8080"}],
     "inverse": "caz_env_list_parse", "capability": "emit", "input_edge": "EnvMap", "output_edge": "EnvVarList"},
    {"id": "prim:caz:env_list_parse", "mutator": "caz_env_list_parse",
     "fixture": [{"name": "LOG_LEVEL", "value": "info"}, {"name": "PORT", "value": "8080"}],
     "expected": {"LOG_LEVEL": "info", "PORT": "8080"}, "capability": "parse",
     "input_edge": "EnvVarList", "output_edge": "EnvMap"},

    # Secret / ConfigMap ENV REFERENCE shapes (references only — no secret value)
    {"id": "prim:caz:secret_ref_build", "mutator": "caz_secret_ref_build",
     "fixture": {"env_name": "DB_PASSWORD", "secret_name": "db-secret", "secret_key": "password"},
     "expected": {"name": "DB_PASSWORD", "valueFrom": {"secretKeyRef": {"name": "db-secret", "key": "password"}}},
     "inverse": "caz_secret_ref_parse", "capability": "emit",
     "input_edge": "SecretRefSpec", "output_edge": "SecretRefManifest"},
    {"id": "prim:caz:secret_ref_parse", "mutator": "caz_secret_ref_parse",
     "fixture": {"name": "DB_PASSWORD", "valueFrom": {"secretKeyRef": {"name": "db-secret", "key": "password"}}},
     "expected": {"env_name": "DB_PASSWORD", "secret_name": "db-secret", "secret_key": "password"},
     "capability": "parse", "input_edge": "SecretRefManifest", "output_edge": "SecretRefSpec"},
    {"id": "prim:caz:configmap_ref_build", "mutator": "caz_configmap_ref_build",
     "fixture": {"env_name": "LOG_LEVEL", "configmap_name": "app-config", "configmap_key": "log_level"},
     "expected": {"name": "LOG_LEVEL", "valueFrom": {"configMapKeyRef": {"name": "app-config", "key": "log_level"}}},
     "inverse": "caz_configmap_ref_parse", "capability": "emit",
     "input_edge": "ConfigMapRefSpec", "output_edge": "ConfigMapRefManifest"},
    {"id": "prim:caz:configmap_ref_parse", "mutator": "caz_configmap_ref_parse",
     "fixture": {"name": "LOG_LEVEL", "valueFrom": {"configMapKeyRef": {"name": "app-config", "key": "log_level"}}},
     "expected": {"env_name": "LOG_LEVEL", "configmap_name": "app-config", "configmap_key": "log_level"},
     "capability": "parse", "input_edge": "ConfigMapRefManifest", "output_edge": "ConfigMapRefSpec"},

    # Azure storage connection string (synthetic key)
    {"id": "prim:caz:conn_string_parse", "mutator": "caz_conn_string_parse",
     "fixture": "DefaultEndpointsProtocol=https;AccountName=synthacct;AccountKey=SYNTHETIC_KEY_NOT_REAL;EndpointSuffix=core.windows.net",
     "expected": {"DefaultEndpointsProtocol": "https", "AccountName": "synthacct",
                  "AccountKey": "SYNTHETIC_KEY_NOT_REAL", "EndpointSuffix": "core.windows.net"},
     "capability": "parse", "input_edge": "ConnStringText", "output_edge": "ConnStringMap"},
    {"id": "prim:caz:conn_string_emit", "mutator": "caz_conn_string_emit",
     "fixture": {"DefaultEndpointsProtocol": "https", "AccountName": "synthacct",
                 "AccountKey": "SYNTHETIC_KEY_NOT_REAL", "EndpointSuffix": "core.windows.net"},
     "expected": "AccountKey=SYNTHETIC_KEY_NOT_REAL;AccountName=synthacct;DefaultEndpointsProtocol=https;EndpointSuffix=core.windows.net",
     "inverse": "caz_conn_string_parse", "capability": "emit",
     "input_edge": "ConnStringMap", "output_edge": "ConnStringText"},
]

#: deliberately-wrong leaf — the proof gate MUST leave it candidate (never persisted as proven)
NEGATIVE_SPEC: dict[str, Any] = {
    "id": "prim:caz:WRONG_expected", "mutator": "caz_resource_id_build",
    "fixture": {"subscription_id": "s", "resource_group": "r", "provider_namespace": "n",
                "resource_type": "t", "resource_name": "x"},
    "expected": "/WRONG/does/not/match", "input_edge": "AzureResourceParts", "output_edge": "AzureResourceId"}


# ── GATED-EFFECT candidates: network / cloud / model operations. NEVER proven, NEVER serves_truth=true. ──
# Each declares {candidate, serves_truth:false, effect, proof_obligation, edge type ids} per repo law.
GATED_EFFECT_SPECS: list[dict[str, Any]] = [
    {"id": "prim:caz:arm_deploy_template", "capability": "deploy", "effect": "network_write",
     "description": "Deploy an ARM/Bicep template to an Azure resource group via the Resource Manager API.",
     "input_edge": "ArmTemplate", "output_edge": "DeploymentResult"},
    {"id": "prim:caz:arm_validate_via_api", "capability": "validate", "effect": "network_read",
     "description": "Validate an ARM template against the live Azure Resource Manager validate endpoint.",
     "input_edge": "ArmTemplate", "output_edge": "ValidationResult"},
    {"id": "prim:caz:kubectl_apply_manifest", "capability": "deploy", "effect": "network_write",
     "description": "Apply a Kubernetes manifest to a live cluster (kubectl apply).",
     "input_edge": "K8sManifest", "output_edge": "ApplyResult"},
    {"id": "prim:caz:kubectl_get_pods", "capability": "fetch", "effect": "network_read",
     "description": "List pods in a namespace from a live cluster (kubectl get pods).",
     "input_edge": "NamespaceName", "output_edge": "PodList"},
    {"id": "prim:caz:blob_download", "capability": "fetch", "effect": "network_read",
     "description": "Download a blob's bytes from Azure Blob Storage by URI.",
     "input_edge": "BlobUri", "output_edge": "Bytes"},
    {"id": "prim:caz:blob_upload", "capability": "publish", "effect": "network_write",
     "description": "Upload bytes to an Azure Blob Storage container.",
     "input_edge": "Bytes", "output_edge": "BlobUri"},
    {"id": "prim:caz:acr_push_image", "capability": "publish", "effect": "network_write",
     "description": "Push a built container image to an Azure Container Registry.",
     "input_edge": "ImageRef", "output_edge": "PushReceipt"},
    {"id": "prim:caz:keyvault_get_secret", "capability": "fetch", "effect": "network_read",
     "description": "Read a secret value from Azure Key Vault by reference (live credential required).",
     "input_edge": "SecretRefSpec", "output_edge": "SecretValue"},
    {"id": "prim:caz:aks_get_credentials", "capability": "fetch", "effect": "network_read",
     "description": "Fetch AKS cluster kubeconfig credentials (az aks get-credentials).",
     "input_edge": "AzureResourceId", "output_edge": "Kubeconfig"},
    {"id": "prim:caz:helm_install_release", "capability": "deploy", "effect": "network_write",
     "description": "Install/upgrade a Helm release into a live cluster with resolved values.",
     "input_edge": "HelmValues", "output_edge": "ReleaseResult"},
    {"id": "prim:caz:lint_manifest_via_model", "capability": "validate", "effect": "model_call",
     "description": "Ask an LLM to lint/explain a Kubernetes manifest (advisory, never truth).",
     "input_edge": "K8sManifest", "output_edge": "LintReport"},
    {"id": "prim:caz:write_manifest_to_file", "capability": "publish", "effect": "file_write",
     "description": "Persist a rendered manifest to a local file path (effectful side write).",
     "input_edge": "ManifestJson", "output_edge": "FilePath"},
]


def _prove_one(spec: dict[str, Any]) -> dict[str, Any]:
    return run_primitive_proof(
        spec["id"], spec["mutator"], spec["fixture"], spec["expected"],
        mutator_args=spec.get("args") or {}, has_inverse=spec.get("inverse"),
    )


def prove_all() -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Run every declared leaf through the imported executed-proof runner. Returns [(spec, receipt), ...]."""
    return [(s, _prove_one(s)) for s in LEAF_SPECS]


def build_proven_rows() -> list[dict[str, Any]]:
    """Persist-ready rows for leaves whose executed proof PASSED — TYPED via canonicalize_edge (workable == typed)."""
    rows: list[dict[str, Any]] = []
    for spec, receipt in prove_all():
        if receipt["serves_truth"] is not True:
            continue  # a failing / wrong-expected leaf stays candidate and is NOT persisted (the gate is the point)
        rows.append({
            "record_type": "proven_deterministic_primitive",
            "primitive_id": receipt["primitive_id"],
            "mutator": receipt["mutator"],
            "domain": DOMAIN,
            "family": FAMILY,
            "capability": spec["capability"],
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
    """Gated-effect candidates — NEVER proven, serves_truth=false, each carries effect + proof_obligation + edges."""
    rows: list[dict[str, Any]] = []
    for spec in GATED_EFFECT_SPECS:
        rows.append({
            "record_type": "gated_effect_candidate",
            "primitive_id": spec["id"],
            "domain": DOMAIN,
            "family": FAMILY,
            "capability": spec["capability"],
            "description": spec["description"],
            "candidate": True,
            "serves_truth": False,
            "effect": spec["effect"],
            "proof_obligation": "live integration test with credential",
            "input_edge": spec["input_edge"],
            "output_edge": spec["output_edge"],
            "input_edge_type_id": canonicalize_edge(spec["input_edge"]),
            "output_edge_type_id": canonicalize_edge(spec["output_edge"]),
        })
    return rows


def build_manifest(proven: list[dict[str, Any]], gated: list[dict[str, Any]]) -> dict[str, Any]:
    typed = [r for r in proven if r["input_edge_type_id"] and r["output_edge_type_id"]]
    return {
        "record_type": "domain_primitive_manifest",
        "domain": DOMAIN,
        "family": FAMILY,
        "generator": "scripts/domain_cloud_azure_k8s.py",
        "generated_utc": _FIXED_UTC,
        "surfaces_covered": ["azure_resource_id", "azure_blob_uri", "docker_acr_image_ref",
                             "k8s_deployment", "k8s_service", "k8s_configmap", "k8s_manifest_json",
                             "k8s_label_selector", "k8s_namespaced_name", "helm_values", "container_env",
                             "secret_ref_shape", "configmap_ref_shape", "azure_connection_string"],
        "defined_leaf_count": len(LEAF_SPECS),
        # SEPARATE, honest counts (repo law):
        "proven_deterministic": len(proven),
        "typed": len(typed),
        "gated_effect_candidates": len(gated),
        "verification_level": "L7_executed_proof",
        "proven_primitive_ids": sorted(r["primitive_id"] for r in proven),
        "gated_effect_primitive_ids": sorted(r["primitive_id"] for r in gated),
        "note": "serves_truth=true is set ONLY by an executed passing proof (run_primitive_proof, imported from "
                "scripts/mutator_registry.py). Every proven row is TYPED via canonicalize_edge (imported from "
                "scripts/build_edge_type_retrofit.py). NETWORK/EFFECTFUL Azure/k8s ops (ARM deploy, kubectl apply/get, "
                "blob up/download, ACR push, Key Vault read, aks get-credentials, helm install, model lint, file "
                "write) are declared as gated-effect candidates (serves_truth=false, effect + proof_obligation) and "
                "are NEVER run through the proof runner. Secret/config-map primitives shape REFERENCES only (name+key) "
                "and connection-string fixtures use a synthetic key — no real secret values.",
    }


def write_pack() -> dict[str, Any]:
    proven = build_proven_rows()
    gated = build_gated_rows()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # Separate sections of the shard: a section marker line, then proven rows, then gated-effect candidate rows.
    lines: list[str] = []
    lines.append(json.dumps({"record_type": "shard_section", "section": "proven_deterministic",
                             "count": len(proven)}, sort_keys=True))
    lines += [json.dumps(r, ensure_ascii=False, sort_keys=True) for r in proven]
    lines.append(json.dumps({"record_type": "shard_section", "section": "gated_effect_candidates",
                             "count": len(gated)}, sort_keys=True))
    lines += [json.dumps(r, ensure_ascii=False, sort_keys=True) for r in gated]
    OUT_JSONL.write_text("".join(ln + "\n" for ln in lines), encoding="utf-8")
    manifest = build_manifest(proven, gated)
    OUT_MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    proven_receipts = prove_all()
    proven = build_proven_rows()
    gated = build_gated_rows()
    ids = [r["primitive_id"] for r in proven]
    typed = [r for r in proven if r["input_edge_type_id"] and r["output_edge_type_id"]]
    roundtrip_specs = [s for s in LEAF_SPECS if s.get("inverse")]
    proven_by_id = {r["primitive_id"]: r for (_s, r) in proven_receipts}

    # deliberately-wrong leaf must stay candidate (proof gate is real, not a rubber stamp) — and never enter rows
    wrong = _prove_one(NEGATIVE_SPEC)
    # a second wrong path: an un-runnable fixture -> execution error -> not promoted
    err = run_primitive_proof("prim:caz:EXEC_ERROR", "caz_resource_id_parse", object(), "irrelevant")

    manifest = build_manifest(proven, gated)
    checks: list[tuple[str, bool]] = [
        (">=25 leaves declared", len(LEAF_SPECS) >= 25),
        ("unique primitive ids across proven+gated",
         len(set(ids) | {r["primitive_id"] for r in gated}) == len(proven) + len(gated)),
        (">=25 leaves PROVE serves_truth=true via an executed proof", len(proven) >= 25),
        ("every proven receipt is L7_executed_proof with all sub-proofs passing",
         all(r["verification_level"] == "L7_executed_proof" and all(p["passed"] for p in r["proofs"])
             for (_s, r) in proven_receipts if r["serves_truth"] is True)),
        ("EVERY proven row carries non-null input+output edge type ids", len(typed) == len(proven)),
        ("manifest typed == proven_deterministic", manifest["typed"] == manifest["proven_deterministic"]),
        ("roundtrip-inverse pairs actually ran + PASSED a roundtrip proof", all(
            any(p["name"] == "roundtrip_test" and p["passed"] for p in proven_by_id[s["id"]]["proofs"])
            for s in roundtrip_specs)),
        ("every surface family present in proven mutators", all(
            any(tok in r["mutator"] for r in proven)
            for tok in ("resource_id", "blob_uri", "image_ref", "deployment", "service", "configmap",
                        "manifest", "label_selector", "namespace", "helm", "env_list", "secret_ref",
                        "conn_string"))),
        ("domain+family stamped on every proven row",
         all(r["domain"] == DOMAIN and r["family"] == FAMILY for r in proven)),
        ("deterministic: re-running yields identical proven rows",
         [json.dumps(r, sort_keys=True) for r in build_proven_rows()] == [json.dumps(r, sort_keys=True) for r in proven]),
        ("a deliberately-wrong leaf stays CANDIDATE (never promoted)",
         wrong["serves_truth"] is False and wrong["promoted"] is False),
        ("the wrong leaf is NOT persisted", NEGATIVE_SPEC["id"] not in set(ids)),
        ("an un-runnable fixture fails the proof, does not promote",
         err["serves_truth"] is False and err["promoted"] is False),
        # gated-effect law: every gated row is candidate/serves_truth=false with an effect + proof_obligation + edges
        (">=1 gated-effect candidate declared", len(gated) >= 1),
        ("EVERY gated row is candidate=true, serves_truth=false",
         all(r["candidate"] is True and r["serves_truth"] is False for r in gated)),
        ("EVERY gated row carries a known effect + a proof_obligation",
         all(r["effect"] in ("network_read", "network_write", "model_call", "file_write")
             and r["proof_obligation"] == "live integration test with credential" for r in gated)),
        ("EVERY gated row is TYPED (non-null input+output edge type ids)",
         all(r["input_edge_type_id"] and r["output_edge_type_id"] for r in gated)),
        ("no gated id ever appears in the proven set", set(r["primitive_id"] for r in gated).isdisjoint(set(ids))),
        ("an actual cloud/network CALL is NEVER proven (all effect ids stay candidate)",
         all(r["serves_truth"] is False for r in gated)),
        ("new mutators registered into the shared registry (add-only seam)",
         all(m in MUTATOR_REGISTRY for m in _NEW_MUTATORS)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - domain_cloud_azure_k8s:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - domain_cloud_azure_k8s: {len(proven)} proven-deterministic + TYPED leaves "
          f"(serves_truth=true, L7_executed_proof; typed={len(typed)}=={len(proven)}) across Azure resource-id/"
          f"blob-uri/image-ref + k8s Deployment/Service/ConfigMap/manifest-json/selectors/namespaced-name + Helm "
          f"values + container env + secret/configmap REFERENCE shapes + synthetic connection strings; "
          f"{len(roundtrip_specs)} inverse pairs proven reversible via roundtrip; {len(gated)} gated-effect "
          "candidates (ARM/kubectl/blob/ACR/KeyVault/AKS/helm/model/file — serves_truth=false, effect+proof_"
          "obligation, honestly NOT proven); a deliberately-wrong leaf and an un-runnable fixture correctly stay "
          "candidate.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        manifest = write_pack()
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return self_test()
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
