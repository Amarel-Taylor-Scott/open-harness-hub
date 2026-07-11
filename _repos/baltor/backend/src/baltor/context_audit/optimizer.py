"""src.baltor.context_audit.optimizer — apply a ContextAuditReport LOSSLESSLY (the Context Optimizer).

The Context Auditor PROPOSES a manifest; this is where Baltor DISPOSES — it applies the manifest to produce an
OPTIMIZED context view for the downstream LLM call: near-duplicates dropped, conflicts resolved to the
authoritative/newest source (the losers superseded, the winner annotated as contested), bloated tool loads and
stale sources flagged in place.

Distillation is never replacement (_repos/shared-backend-components/docs/codex/lossless-distillation.md): the raw bundle, every dropped and
superseded source, and full lineage are PRESERVED and exactly rehydratable; nothing in the input is mutated or
deleted; the optimized view is a derived layer, not truth. Deterministic, offline, stdlib-only — composes the
Context Auditor's own ranking helpers (no re-implementation).
"""
from __future__ import annotations

import copy
from typing import Any

from .context_auditor import _authority, _keep_drop, _tokens


def apply_manifest(sources: list[dict[str, Any]], report: dict[str, Any]) -> dict[str, Any]:
    """Apply `report` (a ContextAuditReport) to `sources`, returning a lossless optimized-context envelope.
    Never mutates `sources`."""
    raw = copy.deepcopy(sources)                  # the preserved, rehydratable original bundle
    by_id = {s["id"]: s for s in sources}
    drop_ids: set[str] = set()
    supersede_ids: set[str] = set()
    dropped: list[dict[str, Any]] = []
    superseded: list[dict[str, Any]] = []
    quarantined: list[dict[str, Any]] = []
    quarantine_ids: set[str] = set()
    annot: dict[str, dict[str, Any]] = {}         # kept-source id → audit annotations (info travels WITH it)

    for issue in report.get("issues", []):
        t = issue.get("type")
        ids = [i for i in issue.get("sources", []) if i in by_id]
        if t == "duplicate_context" and len(ids) == 2:
            keep, drop = _keep_drop(by_id[ids[0]], by_id[ids[1]])
            if drop["id"] not in drop_ids:
                drop_ids.add(drop["id"])
                dropped.append({"id": drop["id"], "kept": keep["id"], "reason": "near-duplicate (retained in raw)"})
        elif t == "conflicting_context" and len(ids) >= 2:
            grp = sorted((by_id[i] for i in ids),
                         key=lambda s: (-_authority(s), int(s.get("age_days", 0)), str(s["id"])))
            winner, losers = grp[0], grp[1:]
            ann = annot.setdefault(winner["id"], {})
            ann.setdefault("contested_by", []).extend(s["id"] for s in losers)
            ann.setdefault("superseded_values", []).extend(
                s["claim_value"] for s in losers if s.get("claim_value") is not None)
            for s in losers:
                if s["id"] not in supersede_ids:
                    supersede_ids.add(s["id"])
                    superseded.append({"id": s["id"], "by": winner["id"],
                                       "reason": "lower authority/older; superseded (retained in raw, never deleted)"})
        elif t == "tool_bloat" and ids:
            annot.setdefault(ids[0], {})["tool_bloat"] = issue.get("reason")
        elif t == "stale_context" and ids:
            annot.setdefault(ids[0], {})["stale"] = issue.get("reason")
        elif t == "context_poisoning" and ids:
            if ids[0] not in quarantine_ids:
                quarantine_ids.add(ids[0])
                quarantined.append({"id": ids[0],
                                    "reason": "untrusted source flagged for instruction-override (heuristic); "
                                              "QUARANTINED — removed from the view, retained in raw, never deleted"})

    removed = drop_ids | supersede_ids | quarantine_ids
    optimized: list[dict[str, Any]] = []
    for s in sources:
        if s["id"] in removed:
            continue
        o = copy.deepcopy(s)
        if s["id"] in annot:
            o["_audit"] = annot[s["id"]]          # the contested/bloat/stale flag survives in the optimized view
        optimized.append(o)

    original_tokens = sum(_tokens(s) for s in sources)
    optimized_tokens = sum(_tokens(s) for s in optimized)
    return {
        "optimized": optimized,
        "raw": raw,                               # preserved original — rehydratable, never mutated/deleted
        "dropped": dropped,
        "superseded": superseded,
        "quarantined": quarantined,
        "original_tokens": original_tokens,
        "optimized_tokens": optimized_tokens,
        # Baltor DISPOSES (applies the manifest)…
        "applied": True,
        # …but LOSSLESSLY: raw + every dropped/superseded source + lineage retained and exactly rehydratable.
        "lossless": True,
        "rehydratable": True,
    }


def rehydrate(optimized_context: dict[str, Any]) -> list[dict[str, Any]]:
    """Reverse the optimization — return the exact original raw bundle (proves the apply was lossless)."""
    return copy.deepcopy(optimized_context["raw"])
