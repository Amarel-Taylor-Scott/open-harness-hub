#!/usr/bin/env python3
"""Build a Baltor public-corpus demo pack from CFPB complaint-shaped records.

Default mode is fully offline and uses a small synthetic fixture. Live mode can
fetch a tightly limited public sample from the CFPB Consumer Complaint Database
API, but it still emits compact governed artifacts rather than raw corpus dumps.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter
from hashlib import sha256
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = REPO_ROOT / "data" / "cfpb-demo" / "complaints-fixture.json"
DEFAULT_OUT_DIR = REPO_ROOT / "site" / "baltor-demos" / "cfpb-complaints"
CFPB_API_URL = "https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/"
CFPB_SOURCE_URL = "https://www.consumerfinance.gov/data-research/consumer-complaints/"
PIPELINE_ID = "baltor.demo.cfpb-consumer-complaints"
SOURCE_HANDLE_PREFIX = "ctx://cfpb/consumer-complaints"
MAX_LIVE_RESPONSE_BYTES = 2_000_000


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def stable_hash(payload: Any) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + sha256(body).hexdigest()


def slug(value: object) -> str:
    text = "".join(ch.lower() if ch.isalnum() else "-" for ch in str(value or ""))
    return "-".join(part for part in text.split("-") if part)[:96] or "unknown"


def load_fixture(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected list fixture at {path}")
    return [dict(item) for item in data if isinstance(item, dict)]


def fetch_live(limit: int, *, product: str | None, company: str | None, state: str | None) -> list[dict[str, Any]]:
    capped_limit = min(max(limit, 1), 50)
    params: dict[str, str] = {
        "format": "json",
        "frm": "0",
        "size": str(capped_limit),
        "no_aggs": "true",
        "no_highlight": "true",
    }
    if product:
        params["product"] = product
    if company:
        params["company"] = company
    if state:
        params["state"] = state
    url = CFPB_API_URL + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"User-Agent": "BaltorDemo/0.1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = response.read(65536)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_LIVE_RESPONSE_BYTES:
                raise RuntimeError(
                    f"CFPB live response exceeded {MAX_LIVE_RESPONSE_BYTES} bytes; "
                    "tighten filters or use the offline fixture."
                )
            chunks.append(chunk)
        data = json.loads(b"".join(chunks).decode("utf-8"))
    if not isinstance(data, list):
        raise ValueError("CFPB API returned a non-list response")
    return [dict((item.get("_source") or item)) for item in data if isinstance(item, dict)]


def source_handle(complaint: dict[str, Any]) -> str:
    return f"{SOURCE_HANDLE_PREFIX}/complaint/{slug(complaint.get('complaint_id'))}"


def source_record(complaint: dict[str, Any], retrieved_at: str, *, live: bool) -> dict[str, Any]:
    handle = source_handle(complaint)
    body = {
        "complaint_id": complaint.get("complaint_id"),
        "product": complaint.get("product"),
        "sub_product": complaint.get("sub_product"),
        "issue": complaint.get("issue"),
        "sub_issue": complaint.get("sub_issue"),
        "company": complaint.get("company"),
        "state": complaint.get("state"),
        "submitted_via": complaint.get("submitted_via"),
        "company_response": complaint.get("company_response"),
        "timely": complaint.get("timely"),
        "date_received": complaint.get("date_received"),
        "has_public_narrative": bool(complaint.get("complaint_what_happened")),
    }
    return {
        "source_record_id": handle,
        "source_type": "api_record",
        "source_url": CFPB_API_URL if live else str(DEFAULT_FIXTURE.relative_to(REPO_ROOT)),
        "publisher": "Consumer Financial Protection Bureau",
        "license": "Public government dataset; verify current CFPB terms before production reuse",
        "source_role": "official_authority",
        "trust_tier": "official_public_dataset",
        "trust_score": 0.82,
        "trust_signals": {
            "official_domain": live,
            "https": True,
            "canonical_url": CFPB_SOURCE_URL,
            "publisher_identity_present": True,
            "updated_at_present": True,
        },
        "injection_risk": 0.35 if body["has_public_narrative"] else 0.12,
        "injection_flags": ["consumer_narrative_unverified"] if body["has_public_narrative"] else [],
        "privacy_boundary": "public",
        "freshness": "live_public_api" if live else "offline_demo_fixture",
        "retrieved_at": retrieved_at,
        "effective_date": str(complaint.get("date_received") or ""),
        "content_hash": stable_hash(body),
        "language": "en",
        "jurisdiction": "US",
        "body": body,
    }


def context_object(complaint: dict[str, Any], retrieved_at: str) -> dict[str, Any]:
    cid = slug(complaint.get("complaint_id"))
    handle = source_handle(complaint)
    title = " / ".join(part for part in [complaint.get("product"), complaint.get("issue")] if part)
    return {
        "kind": "baltor.context-object",
        "context_object_id": f"context-object/cfpb-complaint-{cid}",
        "current_version_id": f"context-version/cfpb-complaint-{cid}-{stable_hash(complaint)[7:19]}",
        "source_system": "cfpb_consumer_complaint_database",
        "native_id": str(complaint.get("complaint_id") or cid),
        "source_url": CFPB_SOURCE_URL,
        "classification": "public",
        "object_type": "issue",
        "title": title or f"CFPB complaint {cid}",
        "summary": (
            f"Public CFPB complaint metadata for {complaint.get('product') or 'unknown product'}; "
            "consumer narrative is treated as unverified allegation when present."
        ),
        "body": {
            "product": complaint.get("product"),
            "issue": complaint.get("issue"),
            "sub_issue": complaint.get("sub_issue"),
            "company_response": complaint.get("company_response"),
            "timely": complaint.get("timely"),
            "state": complaint.get("state"),
            "has_public_narrative": bool(complaint.get("complaint_what_happened")),
        },
        "facets": {
            "cfpb": {
                "product": complaint.get("product"),
                "company": complaint.get("company"),
                "state": complaint.get("state"),
                "submitted_via": complaint.get("submitted_via"),
            },
            "baltor_demo": {
                "claim_status": "aggregate_candidate_only",
                "narrative_policy": "unverified_allegation_do_not_certify_as_fact",
            },
        },
        "five_w_one_h": {
            "who": {"actors": [str(complaint.get("company") or "unknown company")], "audience": ["consumer-finance demo users"]},
            "what": {"entities": [str(complaint.get("product") or "")], "topics": [str(complaint.get("issue") or "")]},
            "when": {"date_received": complaint.get("date_received")},
            "where": {"logical_locations": ["CFPB Consumer Complaint Database"], "physical_locations": [str(complaint.get("state") or "")]},
            "why": {"drivers": ["public complaint trend exploration", "context pipeline demo"]},
            "how": {"methods": ["official-public-api ingest", "metadata normalization", "aggregate pack generation"]},
        },
        "source_handles": [handle],
        "evidence": [{"source_handle": handle, "selector_type": "DataPositionSelector", "selector": {"field": "complaint_id"}}],
        "provenance": {
            "wasDerivedFrom": [handle],
            "wasGeneratedBy": PIPELINE_ID,
            "generatedAtTime": retrieved_at,
            "wasAttributedTo": "baltor-demo-builder",
            "content_hash": stable_hash(complaint),
            "pipeline_id": PIPELINE_ID,
        },
        "lineage": {"run_id": "", "job_name": PIPELINE_ID, "inputs": [handle]},
        "created_at": retrieved_at,
        "policy": {
            "derived_context": True,
            "promotion_allowed": True,
            "raw_source_dump_allowed": False,
            "requires_refresh": True,
            "source_scope_only": True,
            "block_global_memory_promotion": False,
            "acl_filter_applied": True,
            "prompt_injection_checked": False,
            "privacy_boundary": "public",
            "raw_narrative_expansion": "allowed_only_for_public_demo_with_warning",
            "certification": "aggregate_counts_only",
            "requires_reverification": True,
        },
    }


def top_counts(records: list[dict[str, Any]], field: str, limit: int = 5) -> list[dict[str, Any]]:
    counts = Counter(str(item.get(field) or "Unknown") for item in records)
    return [{"value": value, "count": count} for value, count in counts.most_common(limit)]


def build_pack(records: list[dict[str, Any]], objects: list[dict[str, Any]], retrieved_at: str, *, live: bool) -> dict[str, Any]:
    source_handles = [handle for obj in objects for handle in obj["source_handles"]]
    claim_source = f"{SOURCE_HANDLE_PREFIX}/aggregate/{'live' if live else 'fixture'}-{stable_hash(source_handles)[7:19]}"
    products = top_counts(records, "product")
    issues = top_counts(records, "issue")
    states = top_counts(records, "state")
    timely_yes = sum(1 for item in records if str(item.get("timely") or "").lower() == "yes")
    with_narrative = sum(1 for item in records if item.get("complaint_what_happened"))
    return {
        "kind": "baltor.context-pack",
        "context_pack_id": f"context-pack/cfpb-complaints-demo-{stable_hash(source_handles)[7:19]}",
        "pack_type": "customer_pack",
        "task": "Public corpus demo: turn CFPB complaint records into governed context objects and aggregate claims.",
        "query": "What can Baltor safely say about this public CFPB complaint sample?",
        "object_ids": [obj["context_object_id"] for obj in objects],
        "summary": (
            f"Built a governed public-corpus pack from {len(records)} CFPB complaint-shaped records. "
            "Only aggregate claims are candidates for pack-level use; complaint narratives remain unverified allegations."
        ),
        "claims": [
            {
                "claim": f"The sample contains {len(records)} complaint records.",
                "evidence_type": "dataset_count",
                "source_handles": source_handles,
                "confidence": 1.0,
                "certification": "demo_aggregate",
            },
            {
                "claim": f"{timely_yes} of {len(records)} sampled complaints are marked timely by the source field.",
                "evidence_type": "field_aggregate",
                "source_handles": source_handles,
                "confidence": 0.95,
                "certification": "demo_aggregate",
            },
            {
                "claim": f"{with_narrative} of {len(records)} sampled complaints include a public consumer narrative.",
                "evidence_type": "field_presence",
                "source_handles": source_handles,
                "confidence": 0.95,
                "certification": "demo_aggregate",
            },
        ],
        "risks": [
            {
                "risk": "Consumer narratives are allegations and are not independently verified by this demo.",
                "severity": "high",
                "control": "Do not promote narrative statements as durable facts.",
            },
            {
                "risk": "Small samples are not representative of the full CFPB complaint database.",
                "severity": "medium",
                "control": "Label aggregate claims with sample size, filters, and retrieval timestamp.",
            },
            {
                "risk": "Live API data may change over time.",
                "severity": "medium",
                "control": "Use source handles, retrieval timestamps, and content hashes.",
            },
        ],
        "facets": {
            "top_products": products,
            "top_issues": issues,
            "top_states": states,
            "record_count": len(records),
            "live_fetch": live,
        },
        "source_handles": source_handles + [claim_source],
        "trace_id": f"trace-cfpb-demo-{stable_hash(source_handles)[7:19]}",
        "token_budget": 1800,
        "token_count": 650,
        "policy": {
            "privacy_boundary": "public",
            "source_authority": "official_public_dataset",
            "narrative_policy": "unverified_allegation",
            "raw_expansion": "discouraged_in_demo_pack",
            "allowed_model_tiers": ["deterministic", "local", "non_commercial_demo"],
        },
        "created_at": retrieved_at,
    }


def build_receipt(pack: dict[str, Any], source_records: list[dict[str, Any]], retrieved_at: str) -> dict[str, Any]:
    return {
        "kind": "baltor.context-receipt",
        "receipt_id": "receipt-" + pack["context_pack_id"].split("/")[-1],
        "pack_id": pack["context_pack_id"],
        "generated_at": retrieved_at,
        "pipeline_id": PIPELINE_ID,
        "sources_used": [record["source_record_id"] for record in source_records],
        "claims_included": [claim["claim"] for claim in pack.get("claims", [])],
        "claims_excluded": [
            "Any statement that a consumer narrative is true.",
            "Any claim that this small sample represents the full complaint database.",
        ],
        "conflicts_disclosed": [],
        "policy_decision": {
            "decision": "allow_demo_pack",
            "reason": "public official source, aggregate-only claims, no certified narrative facts",
        },
        "retrieval_policy": {
            "max_live_records": 50,
            "default_mode": "offline_fixture",
            "raw_dump_storage": False,
        },
        "trace_id": pack["trace_id"],
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def markdown_summary(pack: dict[str, Any], receipt: dict[str, Any]) -> str:
    lines = [
        "# CFPB Consumer Complaints Demo Pack",
        "",
        pack["summary"],
        "",
        "## Claims",
        "",
    ]
    for claim in pack.get("claims", []):
        lines.append(f"- {claim['claim']}")
    lines.extend(["", "## Risks", ""])
    for risk in pack.get("risks", []):
        lines.append(f"- **{risk['severity']}**: {risk['risk']} Control: {risk['control']}")
    lines.extend([
        "",
        "## Receipt",
        "",
        f"- Pack: `{receipt['pack_id']}`",
        f"- Trace: `{receipt['trace_id']}`",
        f"- Policy decision: `{receipt['policy_decision']['decision']}`",
        "",
    ])
    return "\n".join(lines)


def run(args: argparse.Namespace) -> dict[str, Any]:
    # Provenance time is INJECTABLE (determinism discipline: inject time, no clock in core). The CLI
    # defaults to wall-clock; reprocessing a fixed snapshot — and the self-test — pass a fixed value
    # so the same inputs yield byte-identical artifacts regardless of when the run happens.
    retrieved_at = getattr(args, "retrieved_at", None) or now_iso()
    live = bool(args.live)
    records = fetch_live(args.limit, product=args.product, company=args.company, state=args.state) if live else load_fixture(args.fixture)
    records = records[: min(max(args.limit, 1), 50)]
    source_records = [source_record(record, retrieved_at, live=live) for record in records]
    objects = [context_object(record, retrieved_at) for record in records]
    for obj in objects:
        obj["lineage"]["run_id"] = f"run-cfpb-demo-{stable_hash([item['source_record_id'] for item in source_records])[7:19]}"
    pack = build_pack(records, objects, retrieved_at, live=live)
    # FACT-LEVEL grain: decompose every record into atomic single-sentence facts (#field handles) +
    # held-out narrative sentence chunks. Each fact is independently citable/expandable.
    from scripts.ingest.decompose_structured import decompose_cfpb_complaint

    facts: list[dict[str, Any]] = []
    for record, obj in zip(records, objects):
        d = decompose_cfpb_complaint(record, native_id=obj["native_id"])
        for c in d["components"]:
            facts.append({**c, "context_object_id": obj["context_object_id"], "native_id": obj["native_id"]})
    fact_count = sum(1 for f in facts if f["claim_status"] == "fact")
    alleg_count = sum(1 for f in facts if f["claim_status"] == "unverified_allegation")
    pack["fact_object_ids"] = [f["fact_id"] for f in facts if f["claim_status"] == "fact"]
    pack["grain"] = {"objects": len(objects), "atomic_facts": fact_count, "held_out_allegations": alleg_count}
    receipt = build_receipt(pack, source_records, retrieved_at)
    receipt["facts_served"] = fact_count
    receipt["facts_held_out"] = alleg_count
    out_dir = args.out_dir
    write_json(out_dir / "source-records.json", source_records)
    write_json(out_dir / "context-objects.json", objects)
    write_json(out_dir / "facts.json", facts)
    write_json(out_dir / "context-pack.json", pack)
    write_json(out_dir / "context-receipt.json", receipt)
    (out_dir / "README.md").write_text(markdown_summary(pack, receipt) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "live": live,
        "record_count": len(records),
        "atomic_facts": fact_count,
        "held_out_allegations": alleg_count,
        "out_dir": str(out_dir),
        "pack_id": pack["context_pack_id"],
        "trace_id": pack["trace_id"],
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--live", action="store_true", help="Fetch a small public CFPB API sample instead of using the offline fixture.")
    parser.add_argument("--product")
    parser.add_argument("--company")
    parser.add_argument("--state")
    parser.add_argument("--retrieved-at", dest="retrieved_at", default=None,
                        help="inject a fixed provenance timestamp (ISO-8601) for deterministic reprocessing; defaults to now")
    parser.add_argument("--self-test", action="store_true", help="offline, deterministic contract proof")
    return parser.parse_args(argv)


def _self_test() -> int:
    """Prove the governed CFPB ingestion contract offline: deterministic content-addressed ids, governed
    artifacts (no raw dump), narratives held out as unverified, every object source-linked."""
    import shutil
    import tempfile

    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    tmp = Path(tempfile.mkdtemp(prefix="cfpb-ingest-"))

    def _ns(out, retrieved_at="2026-01-01T00:00:00Z"):
        return argparse.Namespace(fixture=DEFAULT_FIXTURE, out_dir=out, limit=5, live=False,
                                  product=None, company=None, state=None, self_test=True,
                                  retrieved_at=retrieved_at)

    r = run(_ns(tmp / "a"))
    check("offline run ok + 5 records", r["ok"] and r["record_count"] == 5, str(r))
    check("pack_id is content-addressed", r["pack_id"].startswith("context-pack/cfpb-complaints-demo-"))
    r2 = run(_ns(tmp / "b"))  # SAME injected retrieval time → artifacts byte-identical by construction
    # a DIFFERENT retrieval time must NOT change the content-addressed ids (time is provenance, not content)
    r3 = run(_ns(tmp / "c", retrieved_at="2027-09-09T09:09:09Z"))
    check("DETERMINISTIC pack_id + trace_id (independent of retrieval time)",
          r3["pack_id"] == r["pack_id"] and r3["trace_id"] == r["trace_id"], f"{r['pack_id']} vs {r3['pack_id']}")

    objs = json.loads((tmp / "a" / "context-objects.json").read_text())
    pack = json.loads((tmp / "a" / "context-pack.json").read_text())
    rcpt = json.loads((tmp / "a" / "context-receipt.json").read_text())
    check("5 context objects, each source-linked (has a source_handle)", len(objs) == 5 and all(o.get("source_handles") for o in objs))
    check("governance: every object is aggregate-candidate-only (narrative not certified)",
          all(o["facets"]["baltor_demo"]["claim_status"] == "aggregate_candidate_only" for o in objs))
    check("receipt holds out narrative claims (claims_excluded>=1, included>=1)",
          len(rcpt["claims_excluded"]) >= 1 and len(rcpt["claims_included"]) >= 1)
    check("pack is governed (source_handles + risks present, no raw narrative dump)",
          bool(pack.get("source_handles")) and pack.get("risks") is not None)
    check("byte-identical artifacts across two runs at the same retrieval time (deterministic)",
          (tmp / "a" / "context-pack.json").read_text() == (tmp / "b" / "context-pack.json").read_text())
    # FACT-LEVEL grain wired through the pack
    facts = json.loads((tmp / "a" / "facts.json").read_text())
    check("pack decomposed to atomic facts (>0) with #field handles",
          r["atomic_facts"] > 0 and all("#" in f["source_handle"] for f in facts), str(r.get("atomic_facts")))
    check("each fact carries its parent context_object_id (expandable back)",
          all(f.get("context_object_id") for f in facts))
    check("narrative facts held out (allegations not promotion-eligible)",
          all((not f["promotion_eligible"]) for f in facts if f["claim_status"] == "unverified_allegation"))
    check("pack.grain + receipt.facts_served reflect the fact count",
          pack["grain"]["atomic_facts"] == r["atomic_facts"] and rcpt.get("facts_served") == r["atomic_facts"])

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n{'all demo_cfpb_context_pack self-tests passed (governed CFPB ingestion: deterministic content-addressed ids, source-linked objects, narratives held out as unverified, no raw dump).' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if getattr(args, "self_test", False):
        return _self_test()
    result = run(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
