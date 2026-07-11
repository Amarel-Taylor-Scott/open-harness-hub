"""src.baltor.context_audit.context_object_adapter — run the Context Auditor over REAL governed context.

Maps Baltor context-graph objects (the seed-graph / ContextGraph object shape: context_object_id · object_type ·
title · summary · claim · source_handles · freshness) → Context Auditor sources, so the auditor governs ACTUAL
corpus context (sanctions / CFPB / acme-billing …), not just a hand-crafted fixture.

General + deterministic + offline; never mutates the input:
  * structured ``key = value`` claims become claim_key/claim_value (so the auditor's conflict detector fires on
    REAL structured assertions; prose claims are left as text — the auditor defers prose/semantic conflict to
    the reconciliation engine context_graph.find_contradictions, by design);
  * ``freshness.staleness == 'stale'`` maps to an age past the freshness budget (so the staleness detector
    fires from REAL freshness metadata);
  * context documents map to the ``retrieved_doc`` kind (untrusted-but-governed corpus context).

The auditor's output stays evidence, not truth; this adapter only reshapes inputs.
"""
from __future__ import annotations

import re
from typing import Any

from .context_auditor import DEFAULT_TTL_DAYS, audit

_CLAIM_KV = re.compile(r"^\s*(?P<k>[^=]+?)\s*=\s*(?P<v>.+?)\s*$")
_STALE_AGE = DEFAULT_TTL_DAYS + 1  # a 'stale' object maps just past the default TTL → flagged stale, deterministically


def from_context_objects(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Map context-graph objects → Context Auditor sources (deterministic; does not mutate `objects`)."""
    out: list[dict[str, Any]] = []
    for o in objects:
        oid = o.get("context_object_id") or o.get("id") or o.get("title") or ""
        text = " ".join(str(o[k]) for k in ("title", "summary", "claim") if o.get(k)).strip()
        src: dict[str, Any] = {
            "id": oid,
            "kind": "retrieved_doc",                 # governed corpus context (untrusted-but-sourced)
            "text": text,
            "token_estimate": max(1, len(text) // 4),
            "source_handles": list(o.get("source_handles") or []),
        }
        fr = o.get("freshness") or {}
        src["age_days"] = _STALE_AGE if str(fr.get("staleness")).lower() == "stale" else 0
        claim = o.get("claim")
        if isinstance(claim, str):
            m = _CLAIM_KV.match(claim)
            if m:
                key = re.sub(r"[^a-z0-9_.]", "", m.group("k").strip().lower().replace(" ", "_"))
                if key:
                    src["claim_key"] = key
                    src["claim_value"] = m.group("v").strip()
        out.append(src)
    return out


def audit_context_graph(seed: dict[str, Any]) -> dict[str, Any]:
    """Audit a context-graph corpus end-to-end: run the Context Auditor over its objects, then FOLD the
    reconciliation engine's semantic/prose contradictions (context_graph.find_contradictions) into the manifest
    as conflicting_context — covering the prose/semantic conflict the auditor's structured claim_key heuristic
    cannot see, while DEFERRING-not-DUPLICATING (a conflict the auditor already flagged is not re-added). Returns
    the merged manifest (audit() shape + composed_find_contradictions=True). Deterministic; `seed` is not mutated."""
    from scripts.context_graph import ContextGraph  # lazy: src.baltor → scripts (shared substrate); graph-only

    rep = audit(from_context_objects(seed.get("objects") or []))
    already = {sid for it in rep["issues"] if it["type"] == "conflicting_context" for sid in it["sources"]}
    folded: list[dict[str, Any]] = []
    for c in ContextGraph(seed).find_contradictions():
        if c.get("kind") != "assertion" or not c.get("conflicting"):
            continue
        auth = c.get("authority") or {}
        ids = [i for i in ([auth.get("subject_id")] + [x.get("subject_id") for x in c["conflicting"]]) if i]
        if any(i in already for i in ids):                 # defer-not-duplicate
            continue
        values = sorted({str(auth.get("value"))} | {str(x.get("value")) for x in c["conflicting"]})
        folded.append({
            "type": "conflicting_context", "severity": "high", "sources": ids,
            "reason": (f"reconciliation engine: predicate {c.get('predicate')!r} disagrees across sources "
                       f"(values {values}) — semantic/graph contradiction, NOT a truth verdict"),
            "action": (f"surface the resolved authority {auth.get('subject_id')}={auth.get('value')!r}; supersede "
                       f"the others (LOSSLESS — retained; the reconciliation engine decides truth)"),
            "detector": "find_contradictions",
        })
    _rank = {"high": 3, "medium": 2, "low": 1}
    rep["issues"] = sorted(rep["issues"] + folded, key=lambda x: (-_rank.get(x["severity"], 0), x["type"], x["sources"]))
    rep["method"] = rep.get("method", "") + " + reconciliation-engine contradictions (find_contradictions; deferred-not-duplicated)"
    rep["composed_find_contradictions"] = True
    return rep
