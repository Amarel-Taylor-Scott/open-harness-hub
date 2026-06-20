#!/usr/bin/env python3
"""scripts.security.tenant_catalog — tenant isolation policy + store resolver + security metadata.

A TenantPolicy declares HOW a tenant's data is physically isolated (shared_row → schema → database →
storage account → whole deployment) and its security envelope (KMS key + version, residency, retention,
PII policy). Every write resolves its concrete store ref through TenantStoreResolver — never a hardcoded
global table — so a ``database_per_tenant`` tenant can be PROVEN to never write into a shared tenant-data
table, and two isolated tenants always resolve to different refs.

Security metadata (KMS key ref/version, classification, residency, retention, legal hold, access-policy
hash) is attached to EVERY artifact and is kept SEPARATE from the content hash: rotating a key or changing
a retention policy changes the security metadata but NOT the artifact's content_hash (so it is treated as
re-encryption / re-tagging, never as a semantic reprocess).

No real KMS — fake ``kms://…`` refs locally; metadata + contracts + proofs only.

CLI: imported by check_tenant_isolation_policy.py and check_artifact_security_metadata.py.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

ISOLATION_MODES = (
    "shared_row", "schema_per_tenant", "database_per_tenant",
    "storage_account_per_tenant", "deployment_per_tenant",
)

#: logical tables that hold tenant-specific artifacts (must carry tenant_id; must be isolated per policy).
TENANT_DATA_TABLES = frozenset({
    "source_artifacts", "derived_artifacts", "facts", "allegations", "conclusions",
    "emotion_signals", "context_packs", "receipts", "embeddings", "pipeline_runs", "step_runs",
})


class CrossTenantWriteError(Exception):
    """Raised when a write would violate the tenant's isolation policy."""


@dataclass
class TenantPolicy:
    tenant_id: str
    isolation_mode: str = "shared_row"
    data_plane_ref: str = "shared"          # logical data plane (db/cluster) ref
    queue_ref: str = "shared.queue"
    object_store_ref: str = "shared-store"
    vector_store_ref: str = "shared-vectors"
    kms_key_ref: str = ""                    # filled by default_kms() if empty
    kms_key_version: str = "1"
    data_residency: str = "us"
    retention_policy_id: str = "default-retention"
    pii_policy_id: str = "default-pii"
    allowed_processors: list[str] = field(default_factory=list)  # empty = all allowed
    allowed_llm_providers: list[str] = field(default_factory=list)  # empty = all allowed (subject to allow_external_api)
    allow_external_api: bool = True  # if False, only local/private providers may be routed to
    allow_cross_tenant_tables: bool = False

    def __post_init__(self) -> None:
        if not self.kms_key_ref:
            self.kms_key_ref = default_kms(self.tenant_id)

    def allows_processor(self, processor_ref: str) -> bool:
        return (not self.allowed_processors) or processor_ref in self.allowed_processors

    def allows_llm_provider(self, provider_id: str, *, external: bool) -> bool:
        if external and not self.allow_external_api:
            return False
        return (not self.allowed_llm_providers) or provider_id in self.allowed_llm_providers

    def security_policy_hash(self) -> str:
        """Hash of the SECURITY envelope (isolation/residency/retention/pii/key version) — drives the
        run fingerprint's security dimension. Distinct from any artifact content hash."""
        return _sha({
            "isolation_mode": self.isolation_mode, "data_residency": self.data_residency,
            "retention_policy_id": self.retention_policy_id, "pii_policy_id": self.pii_policy_id,
            "kms_key_ref": self.kms_key_ref, "kms_key_version": self.kms_key_version,
        })


def default_kms(tenant_id: str) -> str:
    return f"kms://local/{tenant_id}/cmk"


def _sha(obj) -> str:
    return "sha256:" + hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()[:24]


def policy_errors(p: TenantPolicy) -> list[str]:
    """Validate a policy against the isolation rules. Empty list = valid."""
    errs: list[str] = []
    if p.isolation_mode not in ISOLATION_MODES:
        errs.append(f"unknown isolation_mode {p.isolation_mode!r}")
    if not p.tenant_id:
        errs.append("tenant_id is required (every tenant-specific table includes tenant_id)")
    if p.isolation_mode == "database_per_tenant":
        if p.allow_cross_tenant_tables:
            errs.append("database_per_tenant must not allow cross-tenant tables")
        if p.tenant_id not in p.data_plane_ref:
            errs.append("database_per_tenant requires a tenant-specific data_plane_ref")
    if p.isolation_mode == "storage_account_per_tenant" and p.tenant_id not in p.object_store_ref:
        errs.append("storage_account_per_tenant requires a tenant-specific object_store_ref")
    if p.isolation_mode == "deployment_per_tenant":
        if p.tenant_id not in p.queue_ref:
            errs.append("deployment_per_tenant requires a tenant-specific queue_ref")
        if p.tenant_id not in p.data_plane_ref:
            errs.append("deployment_per_tenant requires a tenant-specific data_plane_ref")
    if p.allow_cross_tenant_tables and p.isolation_mode != "shared_row":
        errs.append("cross-tenant tables are only meaningful under shared_row")
    return errs


class TenantStoreResolver:
    """Resolves every logical store/table to a CONCRETE, isolation-correct ref for one tenant.
    There is no hardcoded global facts table: callers must go through here."""

    def __init__(self, policy: TenantPolicy) -> None:
        self.policy = policy

    def table_ref(self, logical_table: str) -> str:
        p = self.policy
        m = p.isolation_mode
        if m == "shared_row":
            return f"shared:{logical_table}"           # one table, rows tagged by tenant_id
        if m == "schema_per_tenant":
            return f"schema:{p.tenant_id}:{logical_table}"
        if m == "database_per_tenant":
            return f"db:{p.tenant_id}:{logical_table}"  # isolated DB — never shared:
        if m == "storage_account_per_tenant":
            return f"db:{p.tenant_id}:{logical_table}"  # tables tenant-scoped; blobs via object_ref
        if m == "deployment_per_tenant":
            return f"deploy:{p.tenant_id}:{logical_table}"
        raise CrossTenantWriteError(f"unknown isolation_mode {m!r}")

    def object_ref(self, key: str) -> str:
        p = self.policy
        if p.isolation_mode == "storage_account_per_tenant":
            return f"{p.object_store_ref}/{key}"
        return f"{p.object_store_ref}/{p.tenant_id}/{key}"  # shared store, tenant-prefixed

    def queue(self) -> str:
        return self.policy.queue_ref

    def vector_ref(self, key: str) -> str:
        return f"{self.policy.vector_store_ref}/{self.policy.tenant_id}/{key}"


def _ref_tenant(ref: str) -> str | None:
    """Extract the tenant segment from an isolated ref (schema:/db:/deploy:<tenant>:table)."""
    parts = ref.split(":")
    if len(parts) >= 3 and parts[0] in ("schema", "db", "deploy"):
        return parts[1]
    return None


def assert_isolated_write(policy: TenantPolicy, target_ref: str, row: dict, *, logical_table: str = "") -> None:
    """Guard EVERY write. Raises CrossTenantWriteError on an isolation violation:
      * a tenant-data row missing tenant_id (shared_row tables must tag tenant_id);
      * a database_per_tenant write aimed at a shared: ref (must use the isolated DB);
      * a write whose ref encodes a DIFFERENT tenant than the policy (cross-tenant write)."""
    table = logical_table or target_ref.split(":")[-1]
    if table in TENANT_DATA_TABLES and "tenant_id" not in row:
        raise CrossTenantWriteError(f"tenant-data write to {table} missing tenant_id")
    if policy.isolation_mode == "database_per_tenant" and not policy.allow_cross_tenant_tables:
        if target_ref.startswith("shared:"):
            raise CrossTenantWriteError(
                f"database_per_tenant tenant {policy.tenant_id!r} may not write to shared table {target_ref!r}")
    ref_tenant = _ref_tenant(target_ref)
    if ref_tenant is not None and ref_tenant != policy.tenant_id and not policy.allow_cross_tenant_tables:
        raise CrossTenantWriteError(
            f"cross-tenant write: policy={policy.tenant_id!r} target encodes {ref_tenant!r}")
    if "tenant_id" in row and row["tenant_id"] != policy.tenant_id and not policy.allow_cross_tenant_tables:
        raise CrossTenantWriteError(f"row tenant_id {row['tenant_id']!r} != policy {policy.tenant_id!r}")


# ── security metadata (attached to every artifact; SEPARATE from content_hash) ──

def access_policy_hash(policy: TenantPolicy, classification: str, pii: bool) -> str:
    return _sha({"tenant_id": policy.tenant_id, "isolation_mode": policy.isolation_mode,
                 "pii_policy_id": policy.pii_policy_id, "data_residency": policy.data_residency,
                 "classification": classification, "pii": pii,
                 "allowed_processors": sorted(policy.allowed_processors)})


def security_metadata(policy: TenantPolicy, *, classification: str = "internal",
                      pii: bool = False, legal_hold: bool = False) -> dict:
    """The security envelope stamped on an artifact. Contains the key VERSION (so rotation is visible)
    but is never folded into the artifact's content_hash."""
    return {
        "tenant_id": policy.tenant_id,
        "classification": classification,
        "pii": pii,
        "encryption_mode": "envelope",          # envelope-encrypted under the tenant CMK (fake locally)
        "kms_key_ref": policy.kms_key_ref,
        "kms_key_version": policy.kms_key_version,
        "data_residency": policy.data_residency,
        "retention_policy_id": policy.retention_policy_id,
        "legal_hold": legal_hold,
        "access_policy_hash": access_policy_hash(policy, classification, pii),
    }


SECURITY_REQUIRED_KEYS = ("tenant_id", "classification", "kms_key_ref", "kms_key_version",
                          "retention_policy_id", "data_residency")


def security_complete(meta: dict) -> bool:
    return all(meta.get(k) not in (None, "") for k in SECURITY_REQUIRED_KEYS)


def rotate_key(meta: dict) -> dict:
    """Bump the KMS key version (re-encryption). Returns NEW security metadata; the caller must NOT
    touch the artifact's content_hash — rotation is re-encryption, not a content change."""
    out = dict(meta)
    out["kms_key_version"] = str(int(meta.get("kms_key_version", "1")) + 1)
    return out
