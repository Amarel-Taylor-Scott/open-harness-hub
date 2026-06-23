"""provider_directory — a repeatable, cost-efficient provider/practice directory freshness pipeline (the HealthLynked
problem). Healthcare-admin vertical: directory data only (name, NPI, specialty, practice, address, phone, website,
status) — NOT insurance.

The descent makes it cheap: deterministic rungs resolve the bulk at ~$0 — NPI Luhn checksum, field normalization, NPI/
fuzzy matching, and a cross-source AGREEMENT confidence — and an LLM is the LAST rung, only for the ambiguous residual.
Governance makes it safe: every proposed change is a serves_truth=false CANDIDATE scored by confidence; high-confidence
agreements auto-update, conflicting/low-confidence ones go to HUMAN REVIEW, missing fields are honestly MISSING (never
fabricated), and every change carries a provenance/audit trail (what changed, why, which sources). Synthetic/public
metadata only.
"""
from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
from functools import lru_cache
from pathlib import Path

_AUTHORITY = Path(__file__).resolve().parents[3] / "architecture" / "provider_source_authority.json"
_FIELDS = ("provider_name", "specialty", "practice_name", "address", "phone", "website", "status")


@lru_cache(maxsize=1)
def _policy() -> dict:
    return json.loads(_AUTHORITY.read_text())


def authority_of(source: str) -> float:
    p = _policy()
    return float(p["sources"].get(source, p["default_weight"]))


# --- deterministic rung 0: NPI validation (real Luhn checksum, prefix 80840) -----------------------------------------
def _npi_check_digit(base9: str) -> int:
    s = "80840" + base9
    total = 0
    for i, ch in enumerate(reversed(s)):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return (10 - (total % 10)) % 10


def validate_npi(npi) -> bool:
    """True iff `npi` is a 10-digit NPI with a valid Luhn check digit (deterministic, free — no API/LLM)."""
    s = str(npi or "").strip()
    return len(s) == 10 and s.isdigit() and _npi_check_digit(s[:9]) == int(s[9])


# --- deterministic rung 1: normalization ------------------------------------------------------------------------------
def normalize_phone(p) -> str | None:
    d = re.sub(r"\D", "", str(p or ""))
    if len(d) == 11 and d[0] == "1":
        d = d[1:]
    return f"{d[:3]}-{d[3:6]}-{d[6:]}" if len(d) == 10 else (str(p or "").strip() or None)


def normalize_address(a) -> str | None:
    a = re.sub(r"\s+", " ", str(a or "").strip())
    for pat, rep in ((r"\bStreet\b", "St"), (r"\bAvenue\b", "Ave"), (r"\bDrive\b", "Dr"), (r"\bSuite\b", "Ste"),
                     (r"\bRoad\b", "Rd"), (r"\bBoulevard\b", "Blvd"), (r"\bParkway\b", "Pkwy")):
        a = re.sub(pat, rep, a, flags=re.I)
    return a or None


def _norm_text(s) -> str | None:
    s = re.sub(r"\s+", " ", str(s or "").strip())
    return s or None


def normalize_field(field: str, value):
    if field == "phone":
        return normalize_phone(value)
    if field == "address":
        return normalize_address(value)
    if field in ("provider_name", "practice_name", "specialty", "website", "status"):
        v = _norm_text(value)
        return v.lower() if (v and field in ("website", "status")) else v
    return _norm_text(value)


# --- deterministic rung 2: matching (NPI exact, then fuzzy on name+address) -------------------------------------------
def _sim(a, b) -> float:
    return SequenceMatcher(None, str(a or "").lower(), str(b or "").lower()).ratio()


def match_records(a: dict, b: dict, *, fuzzy_threshold: float = 0.88) -> dict:
    """How two records match. NPI exact (deterministic, certain) beats a fuzzy name+address match; below the fuzzy
    threshold it's 'ambiguous' (the residual an LLM rung would adjudicate)."""
    if validate_npi(a.get("npi")) and a.get("npi") == b.get("npi"):
        return {"match": True, "method": "npi_exact", "score": 1.0}
    score = round(0.6 * _sim(normalize_field("provider_name", a.get("provider_name")), normalize_field("provider_name", b.get("provider_name")))
                  + 0.4 * _sim(normalize_address(a.get("address")), normalize_address(b.get("address"))), 3)
    if score >= fuzzy_threshold:
        return {"match": True, "method": "fuzzy", "score": score}
    return {"match": score >= 0.7, "method": "ambiguous_needs_llm" if score >= 0.7 else "no_match", "score": score}


# --- the confidence formula ------------------------------------------------------------------------------------------
def field_confidence(existing, observations: dict, *, authority_fn=authority_of) -> dict:
    """observations: {source: reported_value (normalized)}. Confidence that a field should change to a NEW value:
    agreement = (authority weight backing the winning value) / (total authority reporting the field), scaled by coverage
    (how much authoritative evidence exists). A competing value with real weight => conflict. `authority_fn` supplies the
    per-source weight — defaulting to the physician sources, overridden per profession (the same logic, any directory)."""
    if not observations:
        return {"value": existing, "confidence": 0.0, "supporting_sources": [], "change": False, "conflict": False}
    groups: dict = {}
    for src, val in observations.items():
        groups.setdefault(val, []).append(src)
    total_w = sum(authority_fn(s) for s in observations)
    weight = {v: sum(authority_fn(s) for s in srcs) for v, srcs in groups.items()}
    winner = max(weight, key=lambda v: (weight[v], str(v)))
    win_w = weight[winner]
    coverage = min(1.0, total_w / _policy().get("coverage_full_weight", 1.8))
    agreement = win_w / total_w if total_w else 0.0
    competing = max((w for v, w in weight.items() if v != winner), default=0.0)
    conflict = total_w > 0 and (competing / total_w) >= 0.25
    return {"value": winner, "confidence": round(agreement * coverage, 2), "supporting_sources": sorted(groups[winner]),
            "change": winner != existing and winner is not None, "conflict": conflict}


def decide_action(change_detected: bool, overall: float, conflict: bool) -> tuple:
    p = _policy()
    if not change_detected:
        return "no_change", "Record confirmed as accurate against the sources checked."
    if conflict:
        return "human_review", "Sources conflict on a field; manual verification recommended (safe auto-update declined)."
    if overall < p["human_review_band"]:
        return "human_review", "Overall confidence below the review band; manual verification recommended."
    if overall >= p["auto_update_threshold"]:
        return "auto_update", "Updated fields confirmed by multiple reliable sources above the auto-update threshold."
    return "human_review", "Confidence between the review band and auto-update threshold; manual review recommended."


def resolve_record(record: dict, source_observations: dict, *, fields=_FIELDS, authority_fn=authority_of) -> dict:
    """The per-record pipeline — profession-AGNOSTIC. record: the current directory record. source_observations:
    {source: {field: value}} collected from trusted sources (live fetch is honest-offline elsewhere; this resolves
    provided/synthetic observations deterministically). `fields` + `authority_fn` parameterize it per profession (the same
    logic serves physicians, lawyers, engineers, …). Returns the structured recommendation + an audit trail. serves_truth=false."""
    changes, field_confs, any_conflict, audit = [], [], False, []
    for f in fields:
        existing = normalize_field(f, record.get(f))
        obs = {src: normalize_field(f, v[f]) for src, v in source_observations.items() if v.get(f) is not None}
        if not obs:                                  # honest-MISSING: no source reports it -> claim nothing
            continue
        fc = field_confidence(existing, obs, authority_fn=authority_fn)
        audit.append({"field": f, "old_value": record.get(f), "winning_value": fc["value"],
                      "supporting_sources": fc["supporting_sources"], "confidence": fc["confidence"],
                      "conflict": fc["conflict"], "changed": fc["change"]})
        if fc["change"]:
            changes.append({"field": f, "old_value": record.get(f), "new_value": fc["value"],
                            "confidence_score": fc["confidence"], "supporting_sources": fc["supporting_sources"]})
            field_confs.append(fc["confidence"])
            any_conflict = any_conflict or fc["conflict"]
    change_detected = bool(changes)
    overall = round(min(field_confs), 2) if field_confs else 1.0      # conservative: the weakest changed field gates
    action, reason = decide_action(change_detected, overall, any_conflict)
    return {"provider_id": record.get("provider_id"), "npi": record.get("npi"), "npi_valid": validate_npi(record.get("npi")),
            "change_detected": change_detected, "changes": changes, "overall_confidence": overall,
            "recommended_action": action, "reason": reason, "audit_trail": audit, "serves_truth": False}


_INACTIVE_STATES = {"inactive", "retired", "deceased", "closed", "not practicing", "left practice"}


def find_duplicates(records: list, *, fuzzy_threshold: float = 0.9) -> list:
    """Cluster records that refer to the SAME provider, using the SHARED entity resolver (the 'person' ruleset:
    typo-robust comparators + identifier override + blocking) instead of the simple seed matcher. Returns the duplicate
    clusters (provider_ids, size >= 2) — the merge-review candidates. Deterministic, ~$0."""
    from src.teleon.resolution.entity_resolver import resolve_entities   # vertical -> resolution (correct layering)
    mapped = [{**r, "name": r.get("name") or r.get("provider_name")} for r in records]   # the resolver keys on 'name'
    return [c for c in resolve_entities(mapped, "person")["entities"] if len(c) >= 2]


def detect_inactive(record: dict, source_observations: dict) -> dict:
    """Inactive/retired signal: an AUTHORITATIVE source (weight >= 0.6) reports a non-active status. Evidence-bearing,
    never asserted — a candidate for review. serves_truth=false."""
    ev = [{"source": s, "status": st, "authority": authority_of(s)}
          for s, v in source_observations.items()
          for st in [str(v.get("status") or "").strip().lower()]
          if st in _INACTIVE_STATES and authority_of(s) >= 0.6]
    return {"inactive_candidate": bool(ev), "evidence": ev, "serves_truth": False}


def detect_movement(resolved: dict) -> dict:
    """Provider-movement / practice-change signal from a resolved record: did address or practice_name change?"""
    moved = sorted({c["field"] for c in resolved.get("changes", []) if c["field"] in ("address", "practice_name")})
    return {"moved": bool(moved), "fields": moved, "serves_truth": False}


def freshness_run(items: list) -> dict:
    """The repeatable BATCH pipeline (continuous/periodic, not one-time). items: [{record, source_observations}].
    Resolves each record, partitions into the no_change / auto_update / human_review queues (the review dashboard),
    detects duplicates + inactive + movement, and estimates cost from the ACTUAL human-review rate this batch. serves_truth=false."""
    records = [it["record"] for it in items]
    resolved = [resolve_record(it["record"], it.get("source_observations", {})) for it in items]
    queues = {"no_change": [], "auto_update": [], "human_review": []}
    for r in resolved:
        queues[r["recommended_action"]].append(r["provider_id"])
    inactive = [it["record"].get("provider_id") for it in items
                if detect_inactive(it["record"], it.get("source_observations", {}))["inactive_candidate"]]
    moved = [resolved[i]["provider_id"] for i in range(len(items)) if detect_movement(resolved[i])["moved"]]
    n = len(items) or 1
    manual_fraction = len(queues["human_review"]) / n
    return {"n_records": len(items), "queues": {k: len(v) for k, v in queues.items()},
            "review_queue": queues["human_review"], "auto_update_queue": queues["auto_update"],
            "duplicates": find_duplicates(records), "inactive_candidates": inactive, "moved_providers": moved,
            "recommendations": resolved, "cost_estimate_per_1000": cost_per_1000(manual_fraction=manual_fraction),
            "serves_truth": False}


def cost_per_1000(*, llm_fraction: float = 0.05, manual_fraction: float = 0.05, llm_cost: float = 0.002,
                  manual_cost: float = 2.0) -> dict:
    """Cost per 1,000 records under the descent: deterministic steps (NPI/normalize/match/agreement) are ~$0; an LLM runs
    only on the ambiguous residual; humans review only conflicts. Contrast with a naive always-LLM + review-everything baseline."""
    llm = round(1000 * llm_fraction * llm_cost, 2)
    manual = round(1000 * manual_fraction * manual_cost, 2)
    naive = round(1000 * 0.01 + 1000 * manual_cost, 2)                # always-LLM ($0.01/rec) + review every record
    total = round(llm + manual, 2)
    return {"deterministic_cost_usd": 0.0, "llm_cost_usd": llm, "manual_review_cost_usd": manual,
            "total_usd_per_1000": total, "naive_baseline_usd_per_1000": naive,
            "savings_pct_vs_naive": round((1 - total / naive) * 100, 1) if naive else 0.0,
            "note": "deterministic-first; LLM only on the residual; humans review only conflicts.", "serves_truth": False}
