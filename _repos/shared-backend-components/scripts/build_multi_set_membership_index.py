#!/usr/bin/env python3
"""scripts.build_multi_set_membership_index — the MULTI-SET membership registry ("author once, reference many").

A *set* is a curated family/pack/route-portfolio (one of the primitive FAMILIES a factory run produces). A
*cross-cutting member* is a reusable primitive that is authored ONCE and referenced by MANY sets at once — a
schema_validation gate, an audit_receipt, a dedupe pass, an idempotency_wrapper, etc. The relation "this member
belongs to these sets" is the multi-set relation, and it is exactly what lets the factory avoid re-authoring the
same wrapper inside every family: the member lives in one place; each set holds a REFERENCE.

This pack makes that relation machine-readable and deterministic. Membership is NOT hand-listed per (member, set)
pair (that would drift the moment a set is added). Instead every set declares its STAGE CAPABILITIES (intake,
extract, normalize, dedupe, entity, embed, index, verify, govern, route, cdc, package, guardrail, redact) and every
member declares which stages it serves; membership = the set's capabilities ∩ the member's stages is non-empty (a
UNIVERSAL member marked "*" serves every set). Add a set or a member and the whole index recomputes — no magic
per-pair table to maintain.

Emits three JSONL surfaces + a computed manifest:
  (1) set_records.jsonl          — one row per set (family) with the member families it references;
  (2) cross_cutting_members.jsonl — one row per reusable member with the LIST of sets it belongs to (the multi-set
                                    relation) + an author_once_reference_many note;
  (3) membership_edges.jsonl     — one (member_family -> set) edge per membership, the normalized edge list.

All rows candidate=true / serves_truth=false (a membership index is structure, never a truth claim). Offline +
deterministic (no network/RNG/wall-clock in rows; manifest date from --date). Regenerate via --write; never
hand-edit the pack (the checker recomputes the content hash and goes red on edits). CLI: --self-test | --write
[--date YYYY-MM-DD].
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PACK_DIR = _resource("catalog") / "knowledge-packs" / "data" / "multi-set-membership-index"
BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

#: author-once-reference-many is the whole point — stated once, stamped on every member row.
AUTHOR_ONCE_NOTE = (
    "author_once_reference_many: this member is defined in ONE place and REFERENCED by every set listed in "
    "member_of_sets; sets never re-author it. Editing the member updates all referencing sets at once."
)

# ── The stage-capability vocabulary. Sets declare which stages they run; members declare which stages they serve;
#    membership is the intersection. Single source of the tags so a set and a member can never use a private tag. ──
STAGE_TAGS: tuple[str, ...] = (
    "intake",     # acquire/import records into the pipeline
    "extract",    # pull structured data out of a surface (html/pdf/email/repo)
    "normalize",  # shape raw content into a normalized object
    "dedupe",     # collapse duplicates / cluster near-matches
    "entity",     # entity linking / canonicalization / reference resolution
    "embed",      # embedding prep / vectorization
    "index",      # index-record construction / metadata filtering
    "verify",     # validation / proof / promotion gating
    "govern",     # source governance / provenance / lineage
    "route",      # routing / model ranking / selection / policy dispatch
    "cdc",        # change-data-capture / drift / snapshot receipts
    "package",    # packaging / deployment / reproducible build
    "guardrail",  # guardrail control / rate limit / auth / policy intersection
    "redact",     # pii scrub / redaction
)

# ── The sets: one curated family per row (the families a factory run produces). Each declares its stage
#    capabilities. Keep insertion order stable — it is the deterministic row order. ──
SETS: dict[str, dict[str, Any]] = {
    "record_import":            {"intent": "bulk-import external records into staged rows", "tags": ["intake", "normalize", "dedupe", "verify", "govern", "cdc", "index"]},
    "browser_table_extract":    {"intent": "extract tabular rows from a rendered web surface", "tags": ["extract", "intake", "normalize", "verify", "govern"]},
    "opportunity_ingest":       {"intent": "ingest opportunity/lead records with entity resolution", "tags": ["intake", "normalize", "entity", "dedupe", "verify", "govern", "cdc"]},
    "workflow_template_convert":{"intent": "convert a workflow definition into a portable template", "tags": ["normalize", "package", "verify"]},
    "manifest_validate":        {"intent": "validate a file/package manifest against its contract", "tags": ["verify", "govern", "package"]},
    "vector_index_build":       {"intent": "build a vector index over an embedded corpus", "tags": ["embed", "index", "dedupe", "verify"]},
    "programming_dictionary":   {"intent": "assemble a normalized programming-term dictionary", "tags": ["normalize", "index", "verify", "embed"]},
    "public_api_route":         {"intent": "expose a governed public API route with policy", "tags": ["route", "guardrail", "verify", "govern"]},
    "compliance_mapping":       {"intent": "map records onto a compliance/standards framework", "tags": ["normalize", "entity", "verify", "govern", "cdc"]},
    "support_ticket_triage":    {"intent": "triage inbound support tickets to a route/queue", "tags": ["intake", "route", "normalize", "redact", "verify", "embed"]},
    "standards_mapping":        {"intent": "map terms onto a canonical standards taxonomy", "tags": ["normalize", "entity", "verify", "govern"]},
    "calendar_automation":      {"intent": "automate calendar events from intake signals", "tags": ["intake", "normalize", "route", "verify"]},
    "incident_summarize":       {"intent": "summarize an incident stream into a report", "tags": ["intake", "normalize", "verify", "redact"]},
    "guardrail_gateway":        {"intent": "gate traffic through guardrail + routing policy", "tags": ["guardrail", "route", "verify", "govern"]},
    "api_request_policy":       {"intent": "apply request policy (rate/auth/shape) to API calls", "tags": ["route", "guardrail", "verify"]},
    "job_ingest":               {"intent": "ingest job postings with entity + dedupe", "tags": ["intake", "normalize", "dedupe", "entity", "verify", "govern"]},
    "algorithm_catalog":        {"intent": "catalog algorithms into a searchable index", "tags": ["normalize", "index", "verify", "embed"]},
    "email_document_parse":     {"intent": "parse email/document attachments into records", "tags": ["extract", "intake", "normalize", "redact", "verify", "govern"]},
    "marketplace_listing":      {"intent": "package a component into a marketplace listing", "tags": ["package", "normalize", "verify", "index", "embed"]},
    "file_manifest":            {"intent": "build a governed file manifest for a bundle", "tags": ["verify", "govern", "package", "index"]},
    "source_discovery":         {"intent": "discover candidate source surfaces to intake", "tags": ["intake", "extract", "govern", "verify", "route", "embed"]},
    "repo_scan":                {"intent": "scan a code repository for indexable structure", "tags": ["extract", "intake", "index", "verify", "govern"]},
}

# ── The cross-cutting members: authored ONCE, referenced by MANY sets. Each declares the stages it serves; "*" =
#    UNIVERSAL (serves every set). Membership is computed by intersection — never hand-listed per set. ──
_UNIVERSAL = ["*"]
MEMBERS: dict[str, dict[str, Any]] = {
    # ── universal spine: every set references these regardless of stage ──
    "schema_validation":   {"role": "validate a row against its schema/contract before anything downstream", "tags": _UNIVERSAL},
    "idempotency_wrapper": {"role": "make a stage safely re-runnable (same input -> same effect, no double-write)", "tags": _UNIVERSAL},
    "audit_receipt":       {"role": "emit a signed receipt of what a stage did (inputs/outputs/outcome)", "tags": _UNIVERSAL},
    "receipt_emit":        {"role": "append a structured receipt to the run ledger", "tags": _UNIVERSAL},
    "content_hash":        {"role": "canonical sha256 of a normalized body for identity + drift detection", "tags": _UNIVERSAL},
    "canonical_id":        {"role": "mint a stable location-derived id (prefix-sha) for a produced object", "tags": _UNIVERSAL},
    "provenance":          {"role": "record where a value came from (source handle + read depth)", "tags": _UNIVERSAL},
    "retry_wrapper":       {"role": "bounded retry with backoff around a fallible stage", "tags": _UNIVERSAL},
    "cost_gate":           {"role": "block a stage that would exceed its cost/token budget", "tags": _UNIVERSAL},
    # ── acquisition / extraction ──
    "source_adapter":      {"role": "adapt an external surface to the pipeline's intake port", "tags": ["intake", "extract"]},
    "source_governance":   {"role": "gate a source on authority/licence/consent before it is trusted", "tags": ["govern"]},
    "quarantine_gate":     {"role": "hold a suspect row out of the flow until it clears review", "tags": ["intake", "verify", "govern"]},
    "dead_letter":         {"role": "route an unprocessable item to a dead-letter queue", "tags": ["intake", "route"]},
    "buffering":           {"role": "buffer/batch intake items for downstream throughput", "tags": ["intake", "route"]},
    "cache_wrapper":       {"role": "cache a deterministic stage's output keyed by input hash", "tags": ["intake", "extract", "embed", "index", "route"]},
    "schema_detection":    {"role": "detect the schema/shape of an incoming payload", "tags": ["extract", "intake"]},
    "format_detection":    {"role": "detect the wire format (json/csv/html/pdf) of a source", "tags": ["extract", "intake"]},
    "deterministic_parse": {"role": "parse a structured surface with zero model tokens", "tags": ["extract", "normalize"]},
    "parse_tokenize":      {"role": "tokenize raw text for downstream structuring", "tags": ["extract", "normalize"]},
    # ── normalization / mapping ──
    "normalization":       {"role": "shape raw content into the normalized object schema", "tags": ["normalize"]},
    "schema_bridge":       {"role": "bridge one schema's fields onto another's", "tags": ["normalize", "verify"]},
    "schema_resolution":   {"role": "resolve which schema version a row conforms to", "tags": ["normalize", "verify"]},
    "schema_migration":    {"role": "migrate a row from an old schema to the current one (lossless)", "tags": ["normalize", "package"]},
    "reconciliation":      {"role": "reconcile conflicting field values across sources", "tags": ["normalize", "entity"]},
    "labeling":            {"role": "assign labels/dimension values to a normalized row", "tags": ["normalize", "verify"]},
    "lossless_mapping":    {"role": "map fields A->B while preserving the raw layer + lineage", "tags": ["normalize", "package"]},
    "lossless_transform":  {"role": "transform a row reversibly (raw + intermediates retained)", "tags": ["normalize", "package"]},
    "serialization":       {"role": "serialize a row to a canonical byte form", "tags": ["package", "normalize"]},
    # ── dedupe / entity ──
    "dedupe":              {"role": "collapse exact duplicates during a row merge", "tags": ["dedupe"]},
    "dedupe_cluster":      {"role": "cluster near-duplicate rows into a canonical group", "tags": ["dedupe"]},
    "content_fingerprint": {"role": "compute a similarity fingerprint for near-dup detection", "tags": ["dedupe"]},
    "lsh_blocking":        {"role": "LSH blocking to shrink the pairwise dedupe/entity space", "tags": ["dedupe", "entity"]},
    "entity_linking":      {"role": "link a row's mentions to canonical entities", "tags": ["entity"]},
    "entity_canonicalization": {"role": "choose the canonical form of a linked entity", "tags": ["entity"]},
    "reference_resolution":{"role": "resolve cross-row references to entity ids", "tags": ["entity"]},
    # ── embedding / index ──
    "embedding_prep":      {"role": "prepare text for embedding (chunk/clean/dim-check)", "tags": ["embed"]},
    "object_embedding":    {"role": "compute the object embedding for vector search", "tags": ["embed"]},
    "corpus_stats_profiler": {"role": "profile corpus stats used by embed/verify decisions", "tags": ["verify", "embed"]},
    "index_record":        {"role": "build the index record that makes a row searchable", "tags": ["index"]},
    "metadata_filter_contract": {"role": "declare the metadata filters a query may use on the index", "tags": ["index", "route"]},
    "template_registry_lookup": {"role": "look up a shared template to fill instead of authoring anew", "tags": ["package", "normalize"]},
    # ── verification / proof / promotion ──
    "data_contract":       {"role": "the typed input/output contract a stage must honor", "tags": ["verify"]},
    "constraint_validation": {"role": "check domain constraints beyond shape", "tags": ["verify"]},
    "proof_obligation":    {"role": "the obligation a candidate must discharge to be promoted", "tags": ["verify"]},
    "proof_obligation_generator": {"role": "generate the proof obligations for a candidate", "tags": ["verify"]},
    "rule_trace":          {"role": "trace which deterministic rules fired on a row", "tags": ["verify"]},
    "receipt_verification":{"role": "verify a receipt's signature + field completeness", "tags": ["verify"]},
    "promotion_gate":      {"role": "the gate a candidate passes to become promotion-ready", "tags": ["verify"]},
    "promotion_boundary":  {"role": "enforce candidate-load-ready != tenant-visible", "tags": ["verify"]},
    "lift_measurement":    {"role": "measure pipeline lift over the bare model", "tags": ["verify"]},
    "benchmark_adapter":   {"role": "run a route against paired-arm benchmark fixtures", "tags": ["verify"]},
    "review_routing":      {"role": "route a risky row to the right review queue", "tags": ["verify", "route"]},
    "negative_memory":     {"role": "record + suppress a known failure class", "tags": ["route", "verify"]},
    # ── governance / lineage / redaction ──
    "claim_lineage":       {"role": "trace a claim back to its source evidence", "tags": ["govern", "verify"]},
    "lineage_map":         {"role": "the map from derived layer back to raw + losers", "tags": ["govern"]},
    "jurisdiction_context_binder": {"role": "bind a row to the jurisdiction context that governs it", "tags": ["govern", "verify"]},
    "pii_scrub":           {"role": "scrub PII from a payload before it flows on", "tags": ["redact"]},
    "redaction":           {"role": "redact sensitive spans while preserving structure", "tags": ["redact"]},
    "lossless_distillation": {"role": "distill to a derived layer while preserving raw + held-out + rollback", "tags": ["package", "verify"]},
    # ── routing / policy / guardrail ──
    "route_selection":     {"role": "select the serving route for a request", "tags": ["route"]},
    "route_portfolio":     {"role": "the ordered portfolio of routes a step may take", "tags": ["route"]},
    "model_ranking":       {"role": "rank candidate models for a task", "tags": ["route"]},
    "model_ranker_lane":   {"role": "a ranker lane that scores models on held-out tasks", "tags": ["route"]},
    "guardrail_control":   {"role": "enforce a guardrail policy on inputs/outputs", "tags": ["guardrail"]},
    "rate_limit":          {"role": "throttle calls to stay under a rate budget", "tags": ["guardrail", "route"]},
    "auth_verify":         {"role": "verify caller auth before dispatch", "tags": ["route", "guardrail"]},
    "policy_intersection": {"role": "intersect org + tenant + request policies", "tags": ["guardrail", "govern"]},
    "policy_hash":         {"role": "hash the effective policy for receipt binding", "tags": ["guardrail", "govern"]},
    # ── cdc / drift / snapshot ──
    "cdc":                 {"role": "capture a change to a governed fact", "tags": ["cdc"]},
    "cdc_event":           {"role": "the change event emitted on a fact update", "tags": ["cdc"]},
    "cdc_emitter":         {"role": "emit CDC events downstream on commit", "tags": ["cdc"]},
    "drift_detection":     {"role": "detect drift between a row and its source", "tags": ["cdc", "verify"]},
    "drift_monitor":       {"role": "monitor a served route for post-promotion drift", "tags": ["cdc", "verify"]},
    "snapshot_receipt":    {"role": "receipt pinning the snapshot a row was derived from", "tags": ["cdc", "verify"]},
    "rollback_target":     {"role": "the champion state a promotion can revert to", "tags": ["package", "cdc"]},
    # ── packaging / deployment / build ──
    "packaging":           {"role": "package a proven route for a runtime target", "tags": ["package"]},
    "deployment_package":  {"role": "the deployment bundle (image/iac/helm) for a route", "tags": ["package"]},
    "artifact_assembly":   {"role": "assemble the output bundle from its parts", "tags": ["package"]},
    "runtime_wrapper":     {"role": "wrap a component for a runtime (local/docker/cloud/mcp)", "tags": ["package"]},
    "reproducible_build":  {"role": "produce a byte-reproducible build from pinned inputs", "tags": ["package"]},
    "config_fingerprint":  {"role": "fingerprint the config so formatting changes are not new versions", "tags": ["package", "verify"]},
    "version_pinning":     {"role": "pin the input versions a build consumed", "tags": ["package", "verify"]},
    "pipeline_composition":{"role": "compose members output_edge->input_edge into a pipeline", "tags": ["package", "route"]},
}


def _sets_for(tags: list[str]) -> list[str]:
    """Compute the sets a member belongs to: universal ("*") -> all sets; else capability intersection."""
    if "*" in tags:
        return list(SETS.keys())
    member_tags = set(tags)
    return [name for name, spec in SETS.items() if member_tags & set(spec["tags"])]


def _membership() -> dict[str, list[str]]:
    """member_family -> ordered list of sets it belongs to (the multi-set relation)."""
    return {member: _sets_for(spec["tags"]) for member, spec in MEMBERS.items()}


def _member_rows() -> list[dict[str, Any]]:
    membership = _membership()
    rows = []
    for member, spec in MEMBERS.items():
        sets = membership[member]
        rows.append({
            "record_type": "cross_cutting_member",
            "member_family": member,
            "role": spec["role"],
            "universal": spec["tags"] == _UNIVERSAL,
            "stages_served": (list(STAGE_TAGS) if spec["tags"] == _UNIVERSAL else list(spec["tags"])),
            "member_of_sets": sets,
            "set_count": len(sets),
            "author_once_reference_many": AUTHOR_ONCE_NOTE,
            **BOUNDARY,
        })
    return rows


def _set_rows() -> list[dict[str, Any]]:
    membership = _membership()
    rows = []
    for name, spec in SETS.items():
        members = [m for m in MEMBERS if name in membership[m]]
        rows.append({
            "record_type": "set_record",
            "set": name,
            "intent": spec["intent"],
            "stage_capabilities": list(spec["tags"]),
            "member_families": members,
            "member_count": len(members),
            "note": "sets REFERENCE members (author-once-reference-many); they never re-author them.",
            **BOUNDARY,
        })
    return rows


def _edge_rows() -> list[dict[str, Any]]:
    """Normalized (member_family -> set) edge list — the flattened membership relation."""
    membership = _membership()
    rows = []
    for member in MEMBERS:
        for s in membership[member]:
            rows.append({
                "record_type": "membership_edge",
                "member_family": member,
                "set": s,
                "relation": "member_of",
                **BOUNDARY,
            })
    return rows


JSONL_BUILDERS: dict[str, Callable[[], list[dict[str, Any]]]] = {
    "set_records.jsonl": _set_rows,
    "cross_cutting_members.jsonl": _member_rows,
    "membership_edges.jsonl": _edge_rows,
}


def build_pack() -> dict[str, list[dict[str, Any]]]:
    return {name: builder() for name, builder in JSONL_BUILDERS.items()}


def build_manifest(pack: dict[str, list[dict[str, Any]]], *, date: str) -> dict[str, Any]:
    row_counts = {name: len(rows) for name, rows in pack.items()}
    members = pack["cross_cutting_members.jsonl"]
    universal = [r["member_family"] for r in members if r["universal"]]
    max_reuse = max((r["set_count"] for r in members), default=0)
    canonical = "\n".join(
        json.dumps(row, sort_keys=True, ensure_ascii=False)
        for name in sorted(pack) for row in pack[name]
    )
    return {
        "record_type": "multi_set_membership_index_manifest",
        "pack_id": "multi-set-membership-index",
        "generator": "scripts/build_multi_set_membership_index.py",
        "generated_utc": date,
        "row_counts": row_counts,
        "total_rows": sum(row_counts.values()),
        "set_count": len(pack["set_records.jsonl"]),
        "member_count": len(members),
        "edge_count": len(pack["membership_edges.jsonl"]),
        "universal_member_count": len(universal),
        "universal_members": sorted(universal),
        "max_sets_per_member": max_reuse,
        "avg_sets_per_member": round(sum(r["set_count"] for r in members) / len(members), 3) if members else 0,
        "stage_tags": list(STAGE_TAGS),
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        **BOUNDARY,
    }


def write_pack(*, date: str) -> dict[str, Any]:
    pack = build_pack()
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    for name, rows in pack.items():
        (PACK_DIR / name).write_text(
            "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    manifest = build_manifest(pack, date=date)
    (PACK_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    pack = build_pack()
    manifest = build_manifest(pack, date="1970-01-01")
    membership = _membership()
    set_names = set(SETS)
    member_names = set(MEMBERS)

    # every stage tag a set/member uses must be a real tag
    valid_tags = set(STAGE_TAGS)
    set_tags_ok = all(set(s["tags"]) <= valid_tags for s in SETS.values())
    member_tags_ok = all(
        spec["tags"] == _UNIVERSAL or set(spec["tags"]) <= valid_tags for spec in MEMBERS.values())
    # every tag is actually used by at least one set (else a member could map to zero sets)
    used_by_sets = {t for s in SETS.values() for t in s["tags"]}
    member_tags_used = {t for spec in MEMBERS.values() if spec["tags"] != _UNIVERSAL for t in spec["tags"]}

    checks = [
        ("all set stage tags are valid", set_tags_ok),
        ("all member stage tags are valid", member_tags_ok),
        ("every stage tag is served by >=1 set", used_by_sets == valid_tags),
        ("every member stage tag is offered by >=1 set", member_tags_used <= used_by_sets),
        ("MULTI-SET invariant: every member belongs to >=2 sets", all(len(v) >= 2 for v in membership.values())),
        ("universal members belong to ALL sets", all(
            len(membership[m]) == len(SETS) for m, spec in MEMBERS.items() if spec["tags"] == _UNIVERSAL)),
        ("every set references >=1 member", all(r["member_count"] >= 1 for r in pack["set_records.jsonl"])),
        ("set_records reference only known members", all(
            set(r["member_families"]) <= member_names for r in pack["set_records.jsonl"])),
        ("member rows reference only known sets", all(
            set(r["member_of_sets"]) <= set_names for r in pack["cross_cutting_members.jsonl"])),
        ("edges reconcile with membership (count)", len(pack["membership_edges.jsonl"]) == sum(len(v) for v in membership.values())),
        ("edges endpoints are known", all(
            e["member_family"] in member_names and e["set"] in set_names for e in pack["membership_edges.jsonl"])),
        ("set_records member lists are the inverse of edges", all(
            set(r["member_families"]) == {e["member_family"] for e in pack["membership_edges.jsonl"] if e["set"] == r["set"]}
            for r in pack["set_records.jsonl"])),
        ("author_once note stamped on every member", all(
            r["author_once_reference_many"] == AUTHOR_ONCE_NOTE for r in pack["cross_cutting_members.jsonl"])),
        ("boundary held on every row", all(
            row.get("candidate") is True and row.get("serves_truth") is False
            for rows in pack.values() for row in rows)),
        ("manifest counts computed", manifest["set_count"] == len(SETS) and manifest["member_count"] == len(MEMBERS)
            and manifest["edge_count"] == len(pack["membership_edges.jsonl"])),
    ]
    failed = [name for name, ok in checks if not ok]
    if failed:
        print("FAIL - multi_set_membership_index:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - multi_set_membership_index: {manifest['set_count']} sets, {manifest['member_count']} "
          f"cross-cutting members ({manifest['universal_member_count']} universal), {manifest['edge_count']} "
          f"membership edges; every member is authored once and referenced by >=2 sets "
          f"(max {manifest['max_sets_per_member']}, avg {manifest['avg_sets_per_member']}).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--date", default=None)
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    date = args.date or dt.datetime.now(dt.timezone.utc).date().isoformat()
    manifest = write_pack(date=date)
    print(json.dumps({k: v for k, v in manifest.items() if k != "content_sha256"}, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
