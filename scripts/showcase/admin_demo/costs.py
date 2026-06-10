"""Deterministic run-cost estimates for the Baltor admin demo."""
from __future__ import annotations

from typing import Any

CPU_WORKER_USD_PER_1K_CHARS = 0.0008
SMALL_MODEL_USD_PER_1K_CHARS = 0.0025
MEDIUM_MODEL_USD_PER_1K_CLAIMS = 0.012
SEARCH_REFRESH_USD_PER_JOB = 0.011
ARCHIVE_USD_PER_SOURCE = 0.002
LOCAL_STORAGE_USD_PER_MB_MONTH = 0.00003


def _round_usd(value: float) -> float:
    return round(max(value, 0.0), 4)


def estimate_admin_run_cost(result: dict[str, Any], *, source_bytes: int = 0) -> dict[str, Any]:
    """Estimate demo economics from deterministic run outputs.

    The numbers are deliberately conservative planning estimates, not billing.
    They make the product behavior concrete: deterministic and local work should
    be cheap, while search/model-heavy verification is metered and budgeted.
    """
    summary = result.get("summary") if isinstance(result.get("summary"), dict) else {}
    characters = int(summary.get("characters") or 0)
    claims = int(summary.get("claims") or 0)
    updates = int(summary.get("worker_updates") or len(result.get("updates") or []))
    sources = int(summary.get("sources") or len(result.get("sources") or []))
    kb_chars = max(characters / 1000.0, 0.001)
    mb_sources = max(source_bytes / 1_000_000.0, characters / 1_000_000.0)

    deterministic = _round_usd(kb_chars * CPU_WORKER_USD_PER_1K_CHARS)
    small_model = _round_usd(kb_chars * SMALL_MODEL_USD_PER_1K_CHARS)
    medium_model = _round_usd((claims / 1000.0) * MEDIUM_MODEL_USD_PER_1K_CLAIMS)
    refresh = _round_usd(updates * SEARCH_REFRESH_USD_PER_JOB)
    archive = _round_usd(sources * ARCHIVE_USD_PER_SOURCE)
    storage = _round_usd(mb_sources * LOCAL_STORAGE_USD_PER_MB_MONTH)
    total = _round_usd(deterministic + small_model + medium_model + refresh + archive + storage)

    return {
        "currency": "USD",
        "estimate_kind": "demo_planning",
        "estimated_total_usd": total,
        "budget_ceiling_usd": 5.0,
        "budget_used_pct": round((total / 5.0) * 100, 2),
        "cost_per_claim_usd": _round_usd(total / claims) if claims else 0.0,
        "cost_per_source_usd": _round_usd(total / sources) if sources else total,
        "line_items": [
            {
                "key": "deterministic_workers",
                "label": "Deterministic workers",
                "amount_usd": deterministic,
                "basis": f"{characters:,} characters parsed, chunked, diffed, and graphed",
            },
            {
                "key": "small_model_lanes",
                "label": "Small-model lanes",
                "amount_usd": small_model,
                "basis": "candidate summaries, entities, and claim extraction",
            },
            {
                "key": "medium_model_lanes",
                "label": "Medium-model lanes",
                "amount_usd": medium_model,
                "basis": f"{claims:,} claims normalized and checked for reconciliation",
            },
            {
                "key": "search_refresh",
                "label": "Search/tool refresh",
                "amount_usd": refresh,
                "basis": f"{updates:,} queued verification or refresh jobs",
            },
            {
                "key": "archive_capture",
                "label": "Archive capture",
                "amount_usd": archive,
                "basis": f"{sources:,} source snapshots prepared for provenance",
            },
            {
                "key": "storage",
                "label": "Artifact storage",
                "amount_usd": storage,
                "basis": f"{mb_sources:.3f} MB source and run artifacts for one month",
            },
        ],
        "guardrails": [
            "Use deterministic and local-model lanes before frontier verification.",
            "Batch nonurgent search/model work when latency is not customer-visible.",
            "Stop or require approval before a run crosses the tenant budget ceiling.",
            "Compile expensive Hermes/OpenClaw discoveries into cheaper deterministic workers.",
        ],
    }
