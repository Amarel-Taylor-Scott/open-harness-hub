#!/usr/bin/env python3
"""Knowledge-pack factory — turn discovered capability gaps into catalog KPs.

Reads gap candidates (data/capability-gaps/*.jsonl) and emits, for each:
  * a VALID catalog knowledge-pack manifest (_repos/shared-backend-components/catalog/knowledge-packs/esoteric/)
    carrying the declared `retrieval` type, provenance to the authoritative
    source, valid-vocab industry/capability/modality, and a seed file ref;
  * a seed content file (data/esoteric-packs/) that is EITHER real, stable,
    public facts (REAL_SEEDS, hand-verified) OR an honest ingestion contract
    (schema + source + status=ingestion_target + example) — NEVER fabricated
    authoritative facts.

The capability lift of a KP is its grounding in an authoritative source with a
declared retrieval method; volatile corpora (live CVE feed, sanctions list,
tax tables) are populated later via governed ingestion from the declared source.

Usage:
  python3 -m scripts.factory.knowledge_pack_factory --emit            # all candidates
  python3 -m scripts.factory.knowledge_pack_factory --emit --min-priority 0.7
  python3 -m scripts.factory.knowledge_pack_factory --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import time
from pathlib import Path

import yaml

ROOT = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2])
GAPS_DIR = _resource("data") / "capability-gaps"
OUT_KP = _resource("catalog") / "knowledge-packs" / "esoteric"
OUT_SEED = _resource("data") / "esoteric-packs"
VOCAB = _resource("vocabularies") / "industries.yaml"

# domain/cluster keyword -> candidate industry tags (intersected with the live vocab)
DOMAIN_INDUSTRY = [
    (("healthcare", "pharma", "drug", "clinical", "genom", "bio", "device", "dea", "fda"), ["healthcare", "pharma"]),
    (("finance", "aml", "sanction", "tax", "market", "dora", "mifid", "fatca", "boi", "ofac"), ["finance", "compliance"]),
    (("custom", "trade", "hts", "tariff", "cbam"), ["trade", "supply_chain"]),
    (("esg", "supply", "reach", "pfas"), ["esg", "supply_chain"]),
    (("privacy", "data-protection"), ["privacy", "compliance"]),
    (("law", "legal", "stark", "fraud"), ["legal", "compliance"]),
    (("security", "cve", "cwe", "crypto", "tls", "stig", "cis", "kev"), ["security", "cyber"]),
    (("network", "rfc", "iana", "protocol"), ["infrastructure", "cyber"]),
    (("aerospace", "avionic", "do-178", "arinc"), ["aviation"]),
    (("nuclear", "energy", "nuclide"), ["energy"]),
    (("civil", "structural", "material", "chemistry", "electronic", "opcode", "automotive", "obd"), ["manufacturing"]),
    (("trade-skill", "trades", "refrigerant", "boiler", "lockout", "811", "utilit"), ["construction", "infrastructure"]),
    (("benefit", "liheap", "hud", "section8", "va-", "disability"), ["government"]),
    (("logistic", "maritime", "trucking", "fmcsa", "dangerous-goods", "port"), ["transportation", "maritime"]),
    (("agricultur", "food", "fsis", "pesticide"), ["agriculture", "food"]),
    (("education", "licensure", "credential"), ["education"]),
    (("public-health", "emergency", "ics", "nims", "osha", "safety"), ["compliance", "government"]),
    (("insurance", "claims", "xactimate"), ["insurance"]),
]

# Real, stable, public facts (hand-verified) for high-lift packs. Everything else
# gets an honest ingestion contract. NEVER put volatile/fabricated facts here.
REAL_SEEDS: dict[str, list[dict]] = {
    "nvd-cve-cwe-cvss-vectors": [
        {"kind": "cwe", "id": "CWE-787", "name": "Out-of-bounds Write", "note": "CWE Top-25 #1 class"},
        {"kind": "cwe", "id": "CWE-79", "name": "Improper Neutralization of Input During Web Page Generation (XSS)"},
        {"kind": "cwe", "id": "CWE-89", "name": "SQL Injection"},
        {"kind": "cwe", "id": "CWE-416", "name": "Use After Free"},
        {"kind": "cwe", "id": "CWE-78", "name": "OS Command Injection"},
        {"kind": "cwe", "id": "CWE-22", "name": "Path Traversal"},
        {"kind": "cwe", "id": "CWE-352", "name": "Cross-Site Request Forgery (CSRF)"},
        {"kind": "cvss_metric", "id": "AV", "name": "Attack Vector", "values": ["N", "A", "L", "P"]},
        {"kind": "note", "text": "Live CVE records (id, CPE ranges, CVSS base vector) ingested from the NVD 2.0 feed; CWE list is stable."},
    ],
    "ofac-50-percent-rule-ownership-aggregation": [
        {"kind": "rule", "id": "50pct", "text": "An entity is itself blocked if one or more blocked persons own 50% or more in the AGGREGATE, directly or indirectly."},
        {"kind": "rule", "id": "indirect", "text": "Indirect ownership multiplies down the chain (e.g., A owns 60% of X, X owns 60% of Y => A indirectly owns 36% of Y)."},
        {"kind": "rule", "id": "not-listed", "text": "Being absent from the SDN list does NOT mean an entity is clear; apply the 50% aggregation."},
        {"kind": "note", "text": "Live SDN/Consolidated list ingested from OFAC; this seed states the deterministic aggregation rule."},
    ],
    "811-one-call-utility-locate-rules": [
        {"kind": "apwa_color", "color": "red", "marks": "Electric power lines, cables, conduit, lighting"},
        {"kind": "apwa_color", "color": "yellow", "marks": "Gas, oil, steam, petroleum, gaseous materials"},
        {"kind": "apwa_color", "color": "orange", "marks": "Communication, alarm/signal, cables, conduit"},
        {"kind": "apwa_color", "color": "blue", "marks": "Potable water"},
        {"kind": "apwa_color", "color": "green", "marks": "Sewers and drain lines"},
        {"kind": "apwa_color", "color": "purple", "marks": "Reclaimed water, irrigation, slurry"},
        {"kind": "apwa_color", "color": "pink", "marks": "Temporary survey markings"},
        {"kind": "apwa_color", "color": "white", "marks": "Proposed excavation"},
        {"kind": "note", "text": "APWA Uniform Color Code is fixed/national; notice windows and tolerance zones vary by state statute (ingestion target)."},
    ],
    "ics-nims-emergency-management-procedures": [
        {"kind": "ics_form", "id": "ICS-201", "purpose": "Incident Briefing"},
        {"kind": "ics_form", "id": "ICS-202", "purpose": "Incident Objectives"},
        {"kind": "ics_form", "id": "ICS-204", "purpose": "Assignment List (per division/group)"},
        {"kind": "ics_form", "id": "ICS-214", "purpose": "Activity Log"},
        {"kind": "rule", "id": "span-of-control", "text": "Recommended span of control is 1:3 to 1:7 (optimal 1:5)."},
        {"kind": "rule", "id": "unified-command", "text": "Unified Command is used when an incident crosses jurisdictions/agencies."},
    ],
    "dea-controlled-substance-scheduling-and-limits": [
        {"kind": "schedule", "id": "I", "def": "No accepted medical use, high abuse potential", "examples": ["heroin", "LSD", "MDMA (federal)"]},
        {"kind": "schedule", "id": "II", "def": "High abuse potential, accepted medical use; no refills (new Rx required)", "examples": ["oxycodone", "fentanyl", "adderall"]},
        {"kind": "schedule", "id": "III", "def": "Moderate abuse potential; up to 5 refills in 6 months", "examples": ["buprenorphine", "ketamine"]},
        {"kind": "schedule", "id": "IV", "def": "Low abuse potential; up to 5 refills in 6 months", "examples": ["alprazolam", "tramadol"]},
        {"kind": "schedule", "id": "V", "def": "Lowest abuse potential", "examples": ["pregabalin", "cough preparations <200mg codeine/100mL"]},
        {"kind": "note", "text": "Federal schedules per 21 CFR 1308; state schedules and rescheduling actions are ingestion targets."},
    ],
    "tls-cipher-suites-and-jwa-algorithms": [
        {"kind": "tls13_suite", "code": "0x1301", "name": "TLS_AES_128_GCM_SHA256", "aead": True},
        {"kind": "tls13_suite", "code": "0x1302", "name": "TLS_AES_256_GCM_SHA384", "aead": True},
        {"kind": "tls13_suite", "code": "0x1303", "name": "TLS_CHACHA20_POLY1305_SHA256", "aead": True},
        {"kind": "jwa", "alg": "ES256", "note": "ECDSA P-256 + SHA-256"},
        {"kind": "jwa", "alg": "PS256", "note": "RSASSA-PSS + SHA-256 (preferred over RS256)"},
        {"kind": "note", "text": "Full IANA TLS + JOSE registries ingested from IANA; this seed lists stable TLS1.3 code points."},
    ],
}


def _valid_industries() -> set[str]:
    data = yaml.safe_load(VOCAB.read_text(encoding="utf-8"))
    items = data[list(data)[0]]
    out = set()
    for it in items:
        out.add(it["id"])
        for sub in it.get("sub", []) or []:
            out.add(sub["id"])
    return out


def _industries(candidate: dict, valid: set[str]) -> list[str]:
    hay = (candidate.get("domain", "") + " " + candidate.get("pack_name", "") + " " + candidate.get("cluster", "")).lower()
    tags: list[str] = []
    for keys, inds in DOMAIN_INDUSTRY:
        if any(k in hay for k in keys):
            tags.extend(inds)
    tags = [t for t in dict.fromkeys(tags) if t in valid]
    return tags or ["cross_industry"]


def load_candidates() -> list[dict]:
    out, seen = [], set()
    for f in sorted(GAPS_DIR.glob("*.jsonl")):
        for line in f.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                c = json.loads(line)
            except json.JSONDecodeError:
                continue
            name = c.get("pack_name")
            if name and name not in seen and "offline-cluster" not in c.get("cluster", ""):
                seen.add(name)
                out.append(c)
    return out


def _seed_rows(candidate: dict) -> list[dict]:
    name = candidate["pack_name"]
    if name in REAL_SEEDS:
        return REAL_SEEDS[name]
    # honest ingestion contract — schema + source + status, no fabricated facts
    return [{
        "_status": "ingestion_target",
        "_source": candidate.get("public_source", ""),
        "_retrieval": candidate.get("retrieval_type", ""),
        "_gap": candidate.get("gap", ""),
        "example_query": candidate.get("example_query", ""),
        "_note": "Populated via governed ingestion from the declared source; seed declares structure + provenance, not fabricated facts.",
    }]


def build_manifest(candidate: dict, valid: set[str]) -> tuple[dict, list[dict], str]:
    name = candidate["pack_name"]
    retrieval = candidate.get("retrieval_type", "rag_vector")
    rows = _seed_rows(candidate)
    seeded = name in REAL_SEEDS
    today = time.strftime("%Y-%m-%d")
    pretty = name.replace("-", " ").title()
    manifest = {
        "id": f"knowledge-pack/{name}",
        "type": "knowledge-pack",
        "version": "0.1.0",
        "name": f"{pretty}",
        "description": (
            f"Capability-lift knowledge pack for an esoteric area LLMs handle poorly. "
            f"Gap: {candidate.get('gap', '').strip()} "
            f"Grounded in {candidate.get('public_source', 'an authoritative source')} via {retrieval} retrieval. "
            f"Lift: {candidate.get('lift_rationale', '').strip()}"
        ),
        "authors": [{"name": "OpenHubForAI capability-gap factory"}],
        "license": "CC-BY-4.0",
        "industry": _industries(candidate, valid),
        "capability": ["retrieval", "verification"],
        "modality": ["structured", "text"],
        "lifecycle": "experimental",
        "trust_boundary": "external",
        "freshness": "volatile",
        "tags": ["capability-lift", "esoteric", "knowledge-pack", retrieval,
                 "seeded" if seeded else "ingestion-target"],
        "created": today,
        "updated": today,
        "attribution": {
            "source_url": candidate.get("public_source", ""),
            "source_kind": "other",
            "author": candidate.get("public_source", ""),
            "license": "see-source",
        },
        "content_types": ["fact_table", "reference_doc"],
        "retrieval": [retrieval] if retrieval in
            {"rag_vector", "regex", "keyword", "exact_id", "classifier", "graph"} else ["rag_vector"],
        "files": [{
            "path": f"data/esoteric-packs/{name}.jsonl",
            "format": "jsonl",
            "content_type": "fact_table",
            "schema": "capability-gap seed (real facts where stable; else ingestion contract)",
        }],
        "indexing": {"bm25": True, "dense": {"model": "all-MiniLM-L6-v2"}},
        "provenance": {
            "sources": [candidate.get("public_source", "")],
            "collected_through": today,
            "collected_by": "capability-gap factory",
        },
    }
    return manifest, rows, name


def emit(min_priority: float = 0.0, dry_run: bool = False) -> dict:
    valid = _valid_industries()
    candidates = load_candidates()
    OUT_KP.mkdir(parents=True, exist_ok=True)
    OUT_SEED.mkdir(parents=True, exist_ok=True)
    written, seeded = [], 0
    for c in candidates:
        if float(c.get("priority", 1.0)) < min_priority:
            continue
        manifest, rows, name = build_manifest(c, valid)
        if name in REAL_SEEDS:
            seeded += 1
        if not dry_run:
            (OUT_KP / f"{name}.yaml").write_text(
                yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True), encoding="utf-8")
            (OUT_SEED / f"{name}.jsonl").write_text(
                "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
        written.append(name)
    return {"candidates": len(candidates), "emitted": len(written),
            "with_real_seeds": seeded, "ingestion_contracts": len(written) - seeded,
            "out_dir": str(OUT_KP.relative_to(ROOT))}


def _self_test() -> int:
    valid = _valid_industries()
    assert "healthcare" in valid and "finance" in valid
    cands = load_candidates()
    assert len(cands) >= 40, f"expected the discovered corpus, got {len(cands)}"
    m, rows, name = build_manifest(cands[0], valid)
    assert m["type"] == "knowledge-pack" and m["retrieval"] and m["content_types"]
    assert all(i in valid or i == "cross_industry" for i in m["industry"]), m["industry"]
    rep = emit(dry_run=True)
    print(json.dumps({"ok": True, "valid_industries": len(valid), **rep,
                      "sample_id": m["id"], "sample_industry": m["industry"],
                      "sample_retrieval": m["retrieval"]}, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Generate catalog knowledge packs from discovered capability gaps.")
    p.add_argument("--emit", action="store_true")
    p.add_argument("--min-priority", type=float, default=0.0)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.emit:
        print(json.dumps(emit(min_priority=args.min_priority), indent=2))
        return 0
    p.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
