#!/usr/bin/env python3
"""Philippines licensed employment-agency fragile fact watchtower.

This is the concrete pattern for user-owned context such as "Agency X is licensed
to recruit overseas workers." The fact is fragile: licensing status can change,
the harm of a stale answer is high, and an internal note or vendor cache must not
beat the official DMW/POEA source. The module is deterministic and offline for CI;
live fetch/browser work is represented as Teleon capabilities that emit evidence
receipts, not truth.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from typing import Any

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

from scripts.artifact_graph.authority_corroboration import corroborate
from scripts.artifact_graph.source_authority import classify

VALID = "valid"
SUSPENDED = "suspended"
CANCELLED = "cancelled"
UNKNOWN = "unknown"
OFFICIAL_MIN_RANK = 90

OFFICIAL_SOURCES = [
    {
        "source_id": "dmw-poea-online-services",
        "authority_id": "dmw",
        "publisher": "Department of Migrant Workers",
        "source_uri": "https://onlineservices.dmw.gov.ph/OnlineServices/POEAOnline.aspx",
        "source_role": "primary licensing/status registry",
        "live_fetch_strategy": "http_or_browser",
        "latest_probe": {"checked_at": "2026-06-14", "reachable": True, "status": "HTTP 302 -> 200"},
    },
    {
        "source_id": "dmw-advisories",
        "authority_id": "dmw",
        "publisher": "Department of Migrant Workers",
        "source_uri": "https://dmw.gov.ph/",
        "source_role": "department notices and advisories",
        "live_fetch_strategy": "browser_spa",
        "latest_probe": {"checked_at": "2026-06-14", "reachable": "partial", "status": "SPA page loading shell"},
    },
    {
        "source_id": "dole-advisories",
        "authority_id": "dole",
        "publisher": "Department of Labor and Employment",
        "source_uri": "https://www.dole.gov.ph/",
        "source_role": "labor advisories / corroborating authority",
        "live_fetch_strategy": "browser_challenge",
        "latest_probe": {"checked_at": "2026-06-14", "reachable": "requires_browser", "status": "Cloudflare challenge via curl"},
    },
]


def _norm_name(name: str) -> str:
    value = re.sub(r"[^a-z0-9]+", " ", str(name).lower()).strip()
    value = re.sub(r"\b(inc|corp|corporation|llc|ltd|co|agency|services)\b", "", value)
    return re.sub(r"\s+", " ", value).strip()


def _status_key(status: str) -> int:
    order = {CANCELLED: 3, SUSPENDED: 2, VALID: 1, UNKNOWN: 0}
    return order.get(str(status).lower(), 0)


def _hash_records(records: list[dict[str, Any]]) -> str:
    payload = json.dumps(records, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _with_authority(record: dict[str, Any]) -> dict[str, Any]:
    auth = classify(publisher=str(record.get("publisher", "")),
                    source_uri=str(record.get("source_uri", "")),
                    signed=record.get("signed"))
    return {**record, "_authority": auth, "_rank": auth["rank"], "_basis": auth["basis"], "_tier": auth["tier"],
            "_agency_key": _norm_name(record.get("agency_name", ""))}


def _current_registry(records: list[dict[str, Any]]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for rec in records:
        enriched = _with_authority(rec)
        grouped.setdefault(enriched["_agency_key"], []).append(enriched)

    current: dict[str, dict[str, Any]] = {}
    held_out: list[dict[str, Any]] = []
    for agency_key, rows in grouped.items():
        rows.sort(key=lambda r: (r["_rank"], str(r.get("status_date", "")), _status_key(str(r.get("status", "")))), reverse=True)
        winner = rows[0]
        sources_for_status = [
            {
                "source_id": r.get("source_id"),
                "independent_authority_id": r.get("authority_id"),
                "publisher": r.get("publisher"),
                "source_uri": r.get("source_uri"),
                "signed": r.get("signed"),
                "value": r.get("status"),
            }
            for r in rows
        ]
        corr = corroborate(claim_key=f"ph_agency_status:{agency_key}",
                           claim_value=str(winner.get("status")),
                           sources=sources_for_status,
                           min_rank=OFFICIAL_MIN_RANK)
        current[agency_key] = {
            "agency_name": winner.get("agency_name"),
            "license_no": winner.get("license_no"),
            "status": winner.get("status"),
            "valid_until": winner.get("valid_until"),
            "status_date": winner.get("status_date"),
            "authority_tier": winner["_tier"],
            "authority_basis": winner["_basis"],
            "corroboration": corr,
        }
        for row in rows[1:]:
            if row.get("status") != winner.get("status"):
                held_out.append({
                    "agency_name": row.get("agency_name"),
                    "status": row.get("status"),
                    "reason_held_out": f"lower authority or older conflicting source - {row['_basis']}",
                })
    return current, held_out


def _teleon_capability_plan() -> dict[str, Any]:
    return {
        "owner_runtime": "Teleon",
        "truth_owner": "Baltor",
        "deterministic_capabilities": [
            "source.fetch.official_registry_with_receipt",
            "parser.normalize_agency_license_rows",
            "cdc.compare_source_hash",
            "reconcile.license_status_by_authority",
            "context.promote_current_or_hold_out",
        ],
        "llm_assisted_capabilities": [
            {
                "capability": "source_layout_change_explainer",
                "role": "summarize why a government page/parser changed for a human maintainer",
                "output_status": "candidate_evidence",
                "serves_truth": False,
            },
            {
                "capability": "notice_candidate_extractor",
                "role": "draft structured agency/status rows from unstructured advisories before deterministic validation",
                "output_status": "candidate_evidence",
                "serves_truth": False,
            },
        ],
    }


def run(
    *,
    official_records: list[dict[str, Any]],
    context_claims: list[dict[str, Any]],
    source_health: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    current, held_out_sources = _current_registry(official_records)
    held_out_claims: list[dict[str, Any]] = []
    served: list[dict[str, Any]] = []
    verification_tasks: list[dict[str, Any]] = []

    for claim in context_claims:
        agency_key = _norm_name(claim.get("agency_name", ""))
        gov = current.get(agency_key)
        if not gov:
            verification_tasks.append({
                "task_type": "verify_missing_ph_agency_license_status",
                "agency_name": claim.get("agency_name"),
                "reason": "no official current record in the evidence batch",
                "source_candidates": [s["source_id"] for s in OFFICIAL_SOURCES],
            })
            continue
        if str(claim.get("status")).lower() != str(gov.get("status")).lower():
            held_out_claims.append({
                "claim_id": claim.get("claim_id"),
                "agency_name": claim.get("agency_name"),
                "claimed_status": claim.get("status"),
                "governing_status": gov.get("status"),
                "reason_held_out": "user context conflicts with current official licensing status",
                "authority_basis": gov.get("authority_basis"),
            })
        else:
            served.append({
                "claim_id": claim.get("claim_id"),
                "agency_name": gov.get("agency_name"),
                "status": gov.get("status"),
                "license_no": gov.get("license_no"),
                "valid_until": gov.get("valid_until"),
                "confidence": gov["corroboration"]["verdict"],
                "authority_basis": gov.get("authority_basis"),
            })

    source_health = list(source_health or [s["latest_probe"] | {"source_id": s["source_id"]} for s in OFFICIAL_SOURCES])
    for health in source_health:
        if health.get("reachable") not in (True, "partial"):
            verification_tasks.append({
                "task_type": "refresh_official_source_unavailable",
                "source_id": health.get("source_id"),
                "reason": health.get("status") or "source unavailable",
                "serves_truth": False,
            })

    receipt = {
        "fact_base": "ph_licensed_employment_agencies",
        "content_hash": _hash_records(official_records),
        "official_records": len(official_records),
        "served_claims": len(served),
        "held_out_claims": len(held_out_claims),
        "held_out_source_records": len(held_out_sources),
        "verification_tasks": len(verification_tasks),
        "source_health": source_health,
    }
    return {
        "receipt": receipt,
        "current_registry": current,
        "served_context": served,
        "held_out_claims": held_out_claims,
        "held_out_source_records": held_out_sources,
        "verification_tasks": verification_tasks,
        "teleon_capability_plan": _teleon_capability_plan(),
        "serves_truth": False,
    }


_OFFICIAL_FIXTURE = [
    {"source_id": "dmw-registry", "authority_id": "dmw", "agency_name": "Island Recruiters Agency Inc",
     "license_no": "DMW-1001", "status": SUSPENDED, "valid_until": "2026-12-31", "status_date": "2026-06-10",
     "publisher": "Department of Migrant Workers", "source_uri": "https://onlineservices.dmw.gov.ph/OnlineServices/POEAOnline.aspx", "signed": True},
    {"source_id": "dole-advisory", "authority_id": "dole", "agency_name": "Island Recruiters Agency Inc",
     "license_no": "DMW-1001", "status": SUSPENDED, "valid_until": "2026-12-31", "status_date": "2026-06-11",
     "publisher": "Department of Labor and Employment", "source_uri": "https://www.dole.gov.ph/advisories/island-recruiters", "signed": True},
    {"source_id": "vendor-cache", "authority_id": "vendor", "agency_name": "Island Recruiters Agency Inc",
     "license_no": "DMW-1001", "status": VALID, "valid_until": "2026-12-31", "status_date": "2026-01-05",
     "publisher": "RecruiterDB", "source_uri": "https://recruiterdb.example.com/island", "signed": False},
    {"source_id": "dmw-registry", "authority_id": "dmw", "agency_name": "Harbor Placement Co",
     "license_no": "DMW-2002", "status": VALID, "valid_until": "2026-11-30", "status_date": "2026-06-09",
     "publisher": "Department of Migrant Workers", "source_uri": "https://onlineservices.dmw.gov.ph/OnlineServices/POEAOnline.aspx", "signed": True},
]
_CONTEXT_FIXTURE = [
    {"claim_id": "ctx-island-valid", "agency_name": "Island Recruiters Agency Inc", "status": VALID,
     "source_uri": "ctx://customer/wiki/recruiters"},
    {"claim_id": "ctx-harbor-valid", "agency_name": "Harbor Placement Co", "status": VALID,
     "source_uri": "ctx://customer/vendor-list"},
]


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    out = run(official_records=_OFFICIAL_FIXTURE, context_claims=_CONTEXT_FIXTURE)
    island = out["current_registry"][_norm_name("Island Recruiters Agency Inc")]
    harbor = out["current_registry"][_norm_name("Harbor Placement Co")]

    check("DMW online services classify as official authority",
          "official_agency" in island["authority_tier"], str(island))
    check("two independent official sources corroborate the suspended status",
          island["corroboration"]["verdict"] == "multi_source_authoritative"
          and island["corroboration"]["agreeing_independent"] == 2, str(island["corroboration"]))
    check("stale customer context saying valid is held out",
          any(h["claim_id"] == "ctx-island-valid" and h["governing_status"] == SUSPENDED
              for h in out["held_out_claims"]), str(out["held_out_claims"]))
    check("vendor cache valid record is preserved as held-out source evidence",
          any(h["status"] == VALID for h in out["held_out_source_records"]), str(out["held_out_source_records"]))
    check("single official valid source can serve but is marked single-authoritative",
          any(s["claim_id"] == "ctx-harbor-valid" and s["confidence"] == "single_authoritative"
              for s in out["served_context"]), str(out["served_context"]))

    source_down = run(official_records=_OFFICIAL_FIXTURE, context_claims=_CONTEXT_FIXTURE,
                      source_health=[{"source_id": "dole-advisories", "reachable": False, "status": "network challenge"}])
    check("unavailable official source creates a verification task, never a fake clear",
          any(t["task_type"] == "refresh_official_source_unavailable" for t in source_down["verification_tasks"]))
    check("Teleon plan separates deterministic tools from LLM-assisted candidate evidence",
          len(out["teleon_capability_plan"]["deterministic_capabilities"]) >= 4
          and all(x["serves_truth"] is False for x in out["teleon_capability_plan"]["llm_assisted_capabilities"]))
    check("watchtower output is evidence, not served truth", out["serves_truth"] is False)
    check("deterministic output for identical inputs",
          json.dumps(run(official_records=_OFFICIAL_FIXTURE, context_claims=_CONTEXT_FIXTURE), sort_keys=True)
          == json.dumps(run(official_records=_OFFICIAL_FIXTURE, context_claims=_CONTEXT_FIXTURE), sort_keys=True))
    check("receipt includes a CDC content hash",
          len(out["receipt"]["content_hash"]) == 64 and out["receipt"]["held_out_claims"] == 1, str(out["receipt"]))

    print("\n" + ("PASS - ph_employment_agency_watchtower: official DMW/DOLE evidence governs a fragile "
                  "licensed-agency fact base, stale customer/vendor context is held out, multi-source official "
                  "agreement raises confidence, unavailable sources create verification tasks, and Teleon "
                  "deterministic/LLM-assisted capabilities are separated." if not failures
                  else f"{len(failures)} FAILURES: {failures}"))
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PH licensed employment-agency watchtower.")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    print(json.dumps(run(official_records=_OFFICIAL_FIXTURE, context_claims=_CONTEXT_FIXTURE), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
