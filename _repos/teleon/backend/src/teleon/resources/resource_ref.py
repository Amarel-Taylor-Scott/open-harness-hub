"""src.teleon.resources.resource_ref — builders + guards for the Shared Resource Spine.

Business logic declares WHAT it needs (a logical resource of a kind, under an ownership mode) and references
secrets/keys by ref — it never names a raw table/bucket/path or embeds a raw key. Guards enforce: no raw secret
in a spec, temporary resources require a TTL, persistent resources require owner + retention, and a non-local
provider requires a local_equivalent (offline golden path). Branches on NUMERIC codes from
_repos/shared-backend-components/architecture/shared_resource_spine.json. Pure + deterministic (now injected). No src.baltor import.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import hashlib
import json
import re
from pathlib import Path
from typing import Any

_A = _resource("architecture")
_SPINE = json.loads((_A / "shared_resource_spine.json").read_text(encoding="utf-8"))

#: label -> numeric code (single source: shared_resource_spine.json) — no magic values
OWNERSHIP: dict[str, int] = {m["label"]: m["code"] for m in _SPINE["ownership_modes"]}
KIND: dict[str, int] = {k["label"]: k["code"] for k in _SPINE["resource_kinds"]}
_OWNER_REQUIRES: dict[int, list[str]] = {m["code"]: m.get("requires", []) for m in _SPINE["ownership_modes"]}

EXTERNAL_EXISTING = OWNERSHIP["external_existing"]
MANAGED_PERSISTENT = OWNERSHIP["managed_persistent"]
MANAGED_EPHEMERAL = OWNERSHIP["managed_ephemeral"]
PIPELINE_TEMP = OWNERSHIP["pipeline_temp"]
TENANT_DEDICATED = OWNERSHIP["tenant_dedicated"]
_TEMPORARY = {MANAGED_EPHEMERAL, PIPELINE_TEMP}
_PERSISTENT = {MANAGED_PERSISTENT, TENANT_DEDICATED}

# A raw provider key/secret looks like a known prefix + a long token (built so this module holds no literal key).
_KEY_PREFIXES = ("sk-", "gsk_", "hf_", "AIza", "nvapi-")
_DSN_RE = re.compile(r"(postgres|postgresql|mysql|mongodb|redis|amqp)://[^ \"']+:[^ \"']+@", re.IGNORECASE)


def _string_values(obj: Any) -> list[str]:
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [s for v in obj.values() for s in _string_values(v)]
    if isinstance(obj, list):
        return [s for v in obj for s in _string_values(v)]
    return []


def has_raw_secret(obj: Any) -> bool:
    """True if any string VALUE looks like a raw key or a credentialed connection string (DSN with a password)."""
    blob = " ".join(_string_values(obj))
    if any(re.search(re.escape(p) + r"[A-Za-z0-9_\-]{16,}", blob) for p in _KEY_PREFIXES):
        return True
    return bool(_DSN_RE.search(blob))


def _sid(prefix: str, *parts: str) -> str:
    return f"{prefix}_" + hashlib.blake2b("|".join(parts).encode(), digest_size=10).hexdigest()


def make_secret_ref(ref: str, *, scope: str | None = None, rotation_class: str | None = None) -> dict:
    """A SecretRef carries a secret:// reference, NEVER a value. Refuses anything that looks like a raw key."""
    if not ref.startswith("secret://"):
        raise ValueError("SecretRef.ref must use the secret:// scheme")
    if has_raw_secret({"ref": ref}):
        raise ValueError("SecretRef.ref looks like a raw key, not a reference")
    return {"ref": ref, "scope": scope, "rotation_class": rotation_class}


def make_key_ref(ref: str, *, purpose: str | None = None, rotation_class: str | None = None) -> dict:
    if not ref.startswith("key://"):
        raise ValueError("KeyRef.ref must use the key:// scheme")
    return {"ref": ref, "purpose": purpose, "rotation_class": rotation_class}


def make_resource_ref(*, logical_name: str, kind_code: int, ownership_code: int,
                      binding_ref: str | None = None, tenant_id: str | None = None) -> dict:
    if kind_code not in KIND.values():
        raise ValueError(f"unknown resource kind_code {kind_code}")
    if ownership_code not in OWNERSHIP.values():
        raise ValueError(f"unknown ownership_code {ownership_code}")
    return {"resource_ref": f"res://{logical_name}", "logical_name": logical_name, "kind_code": kind_code,
            "ownership_code": ownership_code, "binding_ref": binding_ref, "tenant_id": tenant_id}


def make_data_resource_spec(*, logical_name: str, kind_code: int, ownership_code: int, provider: str = "local",
                            local_equivalent: str | None = None, ttl_seconds: int | None = None,
                            owner: str | None = None, retention_class: str | None = None,
                            secret_ref: str | None = None, key_ref: str | None = None,
                            data_classification: str | None = None, tenant_id: str | None = None) -> dict:
    return {"spec_id": _sid("dres", logical_name, str(kind_code), str(ownership_code), provider),
            "logical_name": logical_name, "kind_code": kind_code, "ownership_code": ownership_code,
            "provider": provider, "local_equivalent": local_equivalent, "ttl_seconds": ttl_seconds,
            "owner": owner, "retention_class": retention_class, "secret_ref": secret_ref, "key_ref": key_ref,
            "data_classification": data_classification, "tenant_id": tenant_id}


def validate_resource_spec(spec: dict) -> tuple[bool, list[str]]:
    """Enforce the Shared Resource Spine rules. Returns (ok, reasons). Never raises on bad input — it reports."""
    reasons: list[str] = []
    if has_raw_secret(spec):
        reasons.append("raw_secret_in_resource_spec")  # use secret_ref/key_ref, never inline credentials
    if not spec.get("logical_name"):
        reasons.append("resource_requires_logical_name")
    own = spec.get("ownership_code")
    if own not in OWNERSHIP.values():
        reasons.append("unknown_ownership_mode")
    if spec.get("kind_code") not in KIND.values():
        reasons.append("unknown_resource_kind")
    for req in _OWNER_REQUIRES.get(own, []):
        if not spec.get(req):
            reasons.append(f"ownership_requires_{req}")
    if own in _TEMPORARY and not spec.get("ttl_seconds"):
        reasons.append("temporary_resource_requires_ttl")
    if own in _PERSISTENT:
        if not spec.get("owner"):
            reasons.append("persistent_resource_requires_owner")
        if not spec.get("retention_class"):
            reasons.append("persistent_resource_requires_retention")
    if spec.get("provider") and spec.get("provider") != "local" and not spec.get("local_equivalent"):
        reasons.append("cloud_resource_requires_local_equivalent")
    # secret/key fields, if present, must be refs not raw values
    for fld, scheme in (("secret_ref", "secret://"), ("key_ref", "key://")):
        v = spec.get(fld)
        if v and not str(v).startswith(scheme):
            reasons.append(f"{fld}_must_use_{scheme.rstrip(':/')}_scheme")
    return (not reasons), sorted(set(reasons))


def provision_receipt(spec: dict, *, now: str, outcome: str = "provisioned", binding_id: str | None = None,
                      local_fallback_used: bool = False, reasons: list[str] | None = None) -> dict:
    own = spec.get("ownership_code")
    return {"schema_version": "ResourceProvisionReceipt",
            "receipt_id": _sid("rprcpt", spec["spec_id"], now, outcome),
            "spec_id": spec["spec_id"], "resource_ref": f"res://{spec['logical_name']}",
            "binding_id": binding_id, "outcome": outcome, "provider": spec.get("provider", "local"),
            "ownership_code": own, "ttl_seconds": spec.get("ttl_seconds"),
            "cleanup_required": own in _TEMPORARY, "local_fallback_used": local_fallback_used,
            "reasons": reasons or [], "created_at": now}


__all__ = ["make_resource_ref", "make_secret_ref", "make_key_ref", "make_data_resource_spec",
           "validate_resource_spec", "provision_receipt", "has_raw_secret",
           "OWNERSHIP", "KIND", "EXTERNAL_EXISTING", "MANAGED_PERSISTENT", "MANAGED_EPHEMERAL",
           "PIPELINE_TEMP", "TENANT_DEDICATED"]
