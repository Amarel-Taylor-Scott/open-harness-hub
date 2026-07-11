"""Reusable API/policy primitives for enrichment-style backend flows."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from time import time


@dataclass(frozen=True, slots=True)
class ValidatedCompanyEnrichmentRequest:
    """Validated request edge for company/account enrichment."""

    company_domain: str
    account_id: str
    idempotency_key: str


@dataclass(frozen=True, slots=True)
class AccountState:
    """Small deterministic account snapshot used by policy primitives."""

    account_id: str
    plan: str
    enrichment_enabled: bool


@dataclass(frozen=True, slots=True)
class PolicyDecision:
    """Decision produced by deterministic enrichment policy."""

    account_id: str
    allowed: bool
    reason: str


@dataclass(frozen=True, slots=True)
class DecisionReceipt:
    """Receipt for an idempotent persisted policy decision."""

    receipt_path: str
    idempotency_key: str


def validate_company_enrichment_request(payload: dict[str, object]) -> ValidatedCompanyEnrichmentRequest:
    """Validate the JSON request for company enrichment."""

    company_domain = str(payload.get("company_domain") or "").strip().lower()
    account_id = str(payload.get("account_id") or "").strip()
    idempotency_key = str(payload.get("idempotency_key") or "").strip()
    if not company_domain or "." not in company_domain:
        raise ValueError("company_domain is required and must look like a domain")
    if not account_id:
        raise ValueError("account_id is required")
    if not idempotency_key:
        idempotency_key = f"{account_id}:{company_domain}"
    return ValidatedCompanyEnrichmentRequest(
        company_domain=company_domain,
        account_id=account_id,
        idempotency_key=idempotency_key,
    )


def fetch_account_state(request: ValidatedCompanyEnrichmentRequest) -> AccountState:
    """Fetch account state from the local snapshot edge.

    This primitive is deterministic for the demo: real deployments would bind
    the same edge to a database adapter with a receipt and idempotency policy.
    """

    return AccountState(
        account_id=request.account_id,
        plan="standard",
        enrichment_enabled=True,
    )


def apply_enrichment_policy(
    request: ValidatedCompanyEnrichmentRequest,
    account: AccountState,
    artifacts: dict[str, object],
) -> PolicyDecision:
    """Apply the deterministic enrichment policy."""

    table_count = int(artifacts.get("table_count") or 0)
    allowed = account.enrichment_enabled and table_count > 0
    reason = "ok" if allowed else "no_tables_or_enrichment_disabled"
    return PolicyDecision(account_id=request.account_id, allowed=allowed, reason=reason)


def persist_policy_decision(
    decision: PolicyDecision,
    idempotency_key: str,
    store_path: Path,
) -> DecisionReceipt:
    """Persist a policy decision with an idempotency key."""

    store_path.mkdir(parents=True, exist_ok=True)
    safe_key = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in idempotency_key)
    path = store_path / f"{safe_key}.json"
    path.write_text(json.dumps({
        "account_id": decision.account_id,
        "allowed": decision.allowed,
        "reason": decision.reason,
        "idempotency_key": idempotency_key,
        "written_at": int(time()),
    }, indent=2, sort_keys=True), encoding="utf-8")
    return DecisionReceipt(receipt_path=str(path), idempotency_key=idempotency_key)


def emit_api_response(
    request: ValidatedCompanyEnrichmentRequest,
    decision: PolicyDecision,
    receipt: DecisionReceipt,
    artifacts: dict[str, object],
) -> dict[str, object]:
    """Emit a JSON-compatible API response."""

    return {
        "account_id": request.account_id,
        "company_domain": request.company_domain,
        "policy_status": "allowed" if decision.allowed else "blocked",
        "policy_reason": decision.reason,
        "receipt": receipt.receipt_path,
        "artifacts": artifacts,
        "audit": {
            "idempotency_key": receipt.idempotency_key,
            "serves_truth": False,
        },
    }
