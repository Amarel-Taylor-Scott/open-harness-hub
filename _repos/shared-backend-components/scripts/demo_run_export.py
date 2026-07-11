#!/usr/bin/env python3
"""scripts.demo_run_export — assemble ONE unified run-record the demo console animates.

The "view everything in one place" surface. It runs the real end-to-end demo (composing the shipped
modules — graph interrogation, compression, swarm, lift matrix) and reshapes the result into a single
JSON `run record`: an ordered `stages` timeline (the six macro stages + the verification rail), a
`graph` (nodes/edges for visualization), and the headline. `_repos/baltor/frontend/demo-console.html` loads this
JSON and PLAYS it back stage-by-stage with animations — a deterministic replay of a REAL run, not a
faked progress bar.

Corpora: `acme` (the bundled synthetic Acme Billing dataset — works fully offline, the default).
`cfpb` is a LABELED SEAM — the live CFPB connector (`_repos/shared-backend-components/scripts/demo_cfpb_context_pack.py`) runs the
same motion over a public source, but it needs network and is recorded here as available-on-request,
never faked.

CLI:
    python3 _repos/shared-backend-components/scripts/demo_run_export.py --self-test        # offline, deterministic assertions
    python3 _repos/shared-backend-components/scripts/demo_run_export.py --write            # write _repos/baltor/frontend/demo-run.json
    python3 _repos/shared-backend-components/scripts/demo_run_export.py --corpus acme
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
import json
from pathlib import Path
from typing import Any

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _RR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.context_graph import ContextGraph, load_seed
from scripts.demo_full_app import run_demo, CORPORA as DEMO_CORPORA
from scripts.eval.context_lift_matrix import run_matrix, CORPUS_ITEMS
from scripts.source_expansion import expand_source_handle

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
#: where each corpus's run record is written for the console to fetch.
OUT_FILES: dict[str, Path] = {
    "acme": _resource("web/baltor/demo-run.json"),
    "cfpb": _resource("web/baltor/demo-run.cfpb.json"),
}
#: the human-in-the-loop review queue (across all corpora) the reviews.html page reads.
REVIEW_QUEUE_FILE = _resource("web/baltor/review-queue.json")
#: the append-only object version timelines (v1 stale → v2 proposed-pending-review).
VERSION_TIMELINE_FILE = _resource("web/baltor/version-timeline.json")
#: the decisions a steward can record (mirrors steward-review-request.status / the decision schema).
DECISION_OPTIONS: tuple[str, ...] = ("approve", "reject", "needs_more_info")

#: the six macro stages + the rail — the spine the console animates (single source of stage order).
STAGE_SPINE: tuple[str, ...] = (
    "Source Systems", "Reconciliation", "Anti-Fragility",
    "Enhancement", "Optimization", "Consumption", "Continuous Verification rail",
)
#: corpora the console can pick — BOTH run a real, offline, deterministic motion (synthetic data).
#: The LIVE CFPB API (_repos/shared-backend-components/scripts/demo_cfpb_context_pack.py) is a SEPARATE path (needs network), not this.
CORPORA: dict[str, dict[str, Any]] = {
    "acme": {"label": "Acme Billing (synthetic, offline)", "live": False,
             "note": "bundled synthetic engineering KB — fully offline + deterministic"},
    "cfpb": {"label": "CFPB sample (synthetic, offline)", "live": False,
             "note": "bundled SYNTHETIC consumer-finance KB (Reg E vs a stale FAQ) — NOT live CFPB data; "
                     "the live CFPB API connector is a separate path"},
}


def _graph_view(g: ContextGraph) -> dict[str, Any]:
    nodes = [{"id": oid, "type": o.get("object_type"), "title": o.get("title", oid),
              "staleness": (o.get("freshness") or {}).get("staleness", "unknown")}
             for oid, o in g.objects.items()]
    edges = [{"from": r["from_id"], "to": r["to_id"], "type": r["relationship_type"]} for r in g.relationships]
    return {"nodes": sorted(nodes, key=lambda n: n["id"]), "edges": edges}


def _object_detail(g: ContextGraph, oid: str) -> dict[str, Any]:
    """Per-object detail for the clickable graph: the object + its claims + a PRE-COMPUTED gated
    expansion (an allowed example and a denied example). The console only ever shows what the
    `source_expansion` gate ALREADY returned — expansion stays policy-gated, the UI never bypasses it."""
    o = g.objects[oid]
    handles = o.get("source_handles", [])
    primary = handles[0] if handles else ""
    classification = o.get("classification", "internal")
    assertions = [{"predicate": a["predicate"], "value": a.get("value"), "confidence": a.get("confidence")}
                  for a in g.assertions if a["subject_id"] == oid]
    # allowed: real classification (public/internal) → gate grants → real excerpt from disk.
    allow = expand_source_handle(primary, purpose="read", classification=classification, max_tokens=120) if primary else {}
    # denied: simulate a restricted classification → gate refuses → reason, NO raw bytes.
    deny = expand_source_handle(primary, purpose="read", classification="regulated", max_tokens=120) if primary else {}
    return {
        "object_type": o.get("object_type"), "title": o.get("title", oid), "summary": o.get("summary", ""),
        "classification": classification, "freshness": (o.get("freshness") or {}).get("staleness", "unknown"),
        "source_handles": handles, "assertions": assertions,
        "expansion_allowed": {"allowed": allow.get("allowed"), "reason": allow.get("reason"),
                              "compact_preview": allow.get("compact_preview", ""),
                              "raw_excerpt": allow.get("raw_excerpt"),
                              "lineage_summary": allow.get("lineage_summary", "")},
        "expansion_denied": {"allowed": deny.get("allowed"), "reason": deny.get("reason"),
                             "raw_excerpt": deny.get("raw_excerpt")},
    }


def build_run(corpus: str = "acme") -> dict[str, Any]:
    """Assemble the unified run record for `corpus` by running the REAL offline motion.

    Both acme and cfpb run fully offline + deterministic over their bundled synthetic seed (the live
    CFPB API is a separate path). The console animates these recorded stages.
    """
    if corpus not in CORPORA:
        raise ValueError(f"unknown corpus {corpus!r}; choose from {tuple(CORPORA)}")
    meta = CORPORA[corpus]

    demo = run_demo(corpus=corpus)
    g = ContextGraph(load_seed(DEMO_CORPORA[corpus]["seed"]))
    matrix = run_matrix(items=CORPUS_ITEMS[corpus])
    interro, comp, swarm, receipt = demo["interrogation"], demo["compression"], demo["swarm"], demo["receipt"]
    tb = comp["token_budget"]
    contradiction = next((c for c in interro["contradictions"] if c.get("kind") == "assertion"), None)
    cm = matrix["by_model"]["local_mock"]["condition_mean"]
    patch = swarm["consensus"]["context_pack_patch"]
    authority = contradiction["authority"]["subject_id"] if contradiction else (
        interro["authority"]["subject_id"] if interro["authority"] else "n/a")
    auth_val = contradiction["authority"]["value"] if contradiction else interro["answer_value"]
    disagree = ", ".join(f"{x['subject_id']}={x['value']}" for x in (contradiction["conflicting"] if contradiction else []))

    stages = [
        {"id": 0, "title": "Source Systems", "status": "ok",
         "headline": f"ingested {len(g.objects)} context objects from the {meta['label']} corpus",
         "metrics": {"objects": len(g.objects), "source_handles": sum(len(o.get('source_handles', [])) for o in g.objects.values())},
         "source_handles": sorted({h for o in g.objects.values() for h in o.get("source_handles", [])})[:5]},
        {"id": 1, "title": "Reconciliation", "status": "flag" if contradiction else "ok",
         "headline": (f"built the graph; detected a contradiction (authority {authority}={auth_val} vs {disagree})"
                      if contradiction else "built the graph; no contradictions"),
         "metrics": {"edges": len(g.relationships),
                     "contradictions": len(interro["contradictions"]),
                     "authority": authority},
         "source_handles": (contradiction["source_handles"] if contradiction else [])},
        {"id": 2, "title": "Anti-Fragility", "status": "flag" if swarm["review_requests"] else "ok",
         "headline": (f"swarm-verified the stale source → routed {len(swarm['review_requests'])} human review, "
                      f"proposed (not applied) the fix"),
         "metrics": {"risk": swarm["consensus"]["risk_level"],
                     "reviews": len(swarm["review_requests"]),
                     "patch": (f"{patch['from_value']}→{patch['to_value']}" if patch else None),
                     "applied": False},
         "source_handles": [r.get("subject") for r in swarm["review_requests"]]},
        {"id": 3, "title": "Enhancement", "status": "ok",
         "headline": f"interrogated the graph → answer {interro['answer_value']} (authority {authority}), source-cited",
         "metrics": {"answer": interro["answer_value"], "uncertainty": interro["uncertainty"],
                     "swarm_recommended": interro["swarm_recommended"]},
         "source_handles": interro["source_handles"]},
        {"id": 4, "title": "Optimization", "status": "ok",
         "headline": f"compressed the pack {tb['estimated_before']}→{tb['estimated_after']} tokens — every retained item keeps its source handle",
         "metrics": {"tokens_before": tb["estimated_before"], "tokens_after": tb["estimated_after"],
                     "retained": len(comp["retained_refs"]), "dropped": len(comp["dropped_refs"]),
                     "keyphrases": comp["keyphrases"][:5]},
         "source_handles": comp["all_source_handles"][:6]},
        {"id": 5, "title": "Consumption", "status": "ok",
         "headline": f"issued a portable receipt with full lineage (manifest {receipt['lineage_manifest_ref']})",
         "metrics": {"pack_id": demo["pack"]["pack_id"], "receipt_id": receipt["receipt_id"],
                     "lineage_manifest_ref": receipt["lineage_manifest_ref"],
                     "model_route": receipt["model_route"]["selected_adapter"]},
         "source_handles": demo["pack"]["source_handles"][:6]},
        {"id": 6, "title": "Continuous Verification rail", "status": "ok",
         "headline": (f"measured lift: governed pack {cm['context_pack']} vs no-context {cm['no_context']}; "
                      f"raw dump {cm['raw_context']} (underperforms); harness {cm['context_pack_with_harness']}"),
         "metrics": {"condition_means": cm, "best": matrix["summary"]["best_condition"],
                     "raw_underperforms_pack": matrix["summary"]["raw_underperforms_pack"]},
         "source_handles": []},
    ]

    # per-object detail; attach the version timeline (v1→v2 proposed) to the patched object
    detail = {oid: _object_detail(g, oid) for oid in g.objects}
    tgt = DEMO_CORPORA[corpus]["swarm_target"]
    if patch and swarm["review_requests"] and tgt in detail:
        detail[tgt]["versions"] = _version_pair(
            g, tgt, patch, swarm["review_requests"][0]["review_request_id"], receipt["receipt_id"])

    return {
        "kind": "baltor.demo-run", "corpus": corpus, "corpus_label": meta["label"],
        "live": False, "seam": False,
        "headline": demo["headline"],
        "stages": stages,
        "graph": _graph_view(g),
        "object_detail": detail,
        "lift_matrix": {"conditions": matrix["conditions"], "summary": matrix["summary"], "by_model": matrix["by_model"]},
        "receipt": receipt,
        "available_corpora": [{"id": k, **v} for k, v in CORPORA.items()],
        "note": "deterministic replay of a REAL pipeline run — the console animates these recorded stages",
        "created_at": "1970-01-01T00:00:00Z",
    }


def _version_pair(g: ContextGraph, oid: str, patch: dict, review_request_id: str | None,
                  receipt_id: str | None) -> list[dict[str, Any]]:
    """Append-only [v1 (stale, current), v2 (PROPOSED, pending review)] for a patched object.

    Each version conforms to schemas/context-version.schema.json. v2 is a CANDIDATE — not promoted,
    not applied; `current_version_id` (set by the caller) still points at v1 (current is a pointer,
    not a mutation). The receipt is immutable; v2 links the review_request + the proposed patch."""
    o = g.objects[oid]
    handle = (o.get("source_handles") or [""])[0]
    chash = (o.get("provenance") or {}).get("content_hash") or f"sha256:demo-{oid}"
    created = o.get("created_at", "1970-01-01T00:00:00Z")
    v1 = {
        "kind": "baltor.context-version", "context_version_id": f"{oid}-v1",
        "context_object_id": oid, "content_hash": chash, "source_revision": "v1",
        "observed_at": created, "created_at": created, "valid_from": created, "valid_to": None,
        "source_handle": handle, "value": patch["from_value"],
        "status": "stale", "applied": True, "candidate_promoted": True, "is_current": True,
    }
    v2 = {
        "kind": "baltor.context-version", "context_version_id": f"{oid}-v2",
        "context_object_id": oid, "content_hash": f"sha256:proposed-{oid}", "source_revision": "v2-proposed",
        "observed_at": "1970-01-01T00:00:00Z", "created_at": "1970-01-01T00:00:00Z",
        # no valid_from/valid_to: the proposed version is not yet valid (pending review).
        "source_handle": handle, "value": patch["to_value"],
        "status": "proposed", "lifecycle": "pending_review", "applied": False, "candidate_promoted": False,
        "is_current": False, "authority": patch.get("authority"),
        "review_request_id": review_request_id, "proposed_patch": patch, "receipt_ref": receipt_id,
        "policy": {"promotion_allowed": False, "reason": "candidate pending human review (promotion boundary)"},
    }
    return [v1, v2]


def build_version_timeline() -> dict[str, Any]:
    """Append-only version timelines for the patched object in each corpus (v1 stale → v2 proposed)."""
    timelines: list[dict[str, Any]] = []
    for corpus in CORPORA:
        g = ContextGraph(load_seed(DEMO_CORPORA[corpus]["seed"]))
        oid = DEMO_CORPORA[corpus]["swarm_target"]
        demo = run_demo(corpus=corpus)
        patch = demo["swarm"]["consensus"]["context_pack_patch"]
        rid = demo["swarm"]["review_requests"][0]["review_request_id"] if demo["swarm"]["review_requests"] else None
        versions = _version_pair(g, oid, patch, rid, demo["receipt"]["receipt_id"]) if patch else []
        timelines.append({
            "corpus": corpus, "corpus_label": CORPORA[corpus]["label"], "object_id": oid,
            "predicate": patch["predicate"] if patch else None,
            "current_version_id": f"{oid}-v1",   # current still points at v1 — v2 is not promoted
            "versions": versions,
        })
    return {
        "kind": "baltor.version-timeline", "timelines": timelines,
        "note": "append-only; current is a POINTER (still v1); v2 is a candidate pending review — NOT "
                "promoted, NOT applied (promotion boundary); receipts immutable",
        "created_at": "1970-01-01T00:00:00Z",
    }


def build_review_queue() -> dict[str, Any]:
    """The human-in-the-loop queue: the steward-review-requests the swarm routed across ALL corpora,
    each enriched with decision options + the proposed (NOT applied) patch + corpus label. The
    requests come from `context_swarm` (real); decisions are demo-local (no canonical mutation)."""
    reviews: list[dict[str, Any]] = []
    for corpus in CORPORA:
        demo = run_demo(corpus=corpus)
        patch = demo["swarm"]["consensus"]["context_pack_patch"]
        for rr in demo["swarm"]["review_requests"]:
            reviews.append({
                "corpus": corpus, "corpus_label": CORPORA[corpus]["label"],
                "request": rr,                       # validates against steward-review-request.schema.json
                "decision_options": list(DECISION_OPTIONS),
                "proposed_patch": patch,             # applied=false — approval gates the apply
            })
    return {
        "kind": "baltor.review-queue",
        "reviews": reviews,
        "open_count": sum(1 for r in reviews if r["request"].get("status") == "open"),
        "note": "steward reviews routed by the context-object swarm; decisions are demo-local (no "
                "canonical mutation, no server) — applying a fix is a separate human/policy-gated step",
        "created_at": "1970-01-01T00:00:00Z",
    }


def _serialize(run: dict) -> str:
    return json.dumps(run, indent=2, sort_keys=True) + "\n"


def write_all() -> list[str]:
    """(Re)generate every corpus's run record JSON. Returns the relative paths written."""
    out: list[str] = []
    for corpus, path in OUT_FILES.items():
        path.write_text(_serialize(build_run(corpus)), encoding="utf-8")
        out.append(path.relative_to(_REPO).as_posix())
    REVIEW_QUEUE_FILE.write_text(_serialize(build_review_queue()), encoding="utf-8")
    out.append(REVIEW_QUEUE_FILE.relative_to(_REPO).as_posix())
    VERSION_TIMELINE_FILE.write_text(_serialize(build_version_timeline()), encoding="utf-8")
    out.append(VERSION_TIMELINE_FILE.relative_to(_REPO).as_posix())
    return out


def _stale_files() -> list[str]:
    """Committed artifacts that no longer byte-match their builder — the drift the proof forbids."""
    stale: list[str] = []
    for corpus, path in OUT_FILES.items():
        if not path.exists() or path.read_text(encoding="utf-8") != _serialize(build_run(corpus)):
            stale.append(path.relative_to(_REPO).as_posix())
    if not REVIEW_QUEUE_FILE.exists() or REVIEW_QUEUE_FILE.read_text(encoding="utf-8") != _serialize(build_review_queue()):
        stale.append(REVIEW_QUEUE_FILE.relative_to(_REPO).as_posix())
    if not VERSION_TIMELINE_FILE.exists() or VERSION_TIMELINE_FILE.read_text(encoding="utf-8") != _serialize(build_version_timeline()):
        stale.append(VERSION_TIMELINE_FILE.relative_to(_REPO).as_posix())
    return stale


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    run = build_run("acme")
    titles = [s["title"] for s in run["stages"]]
    check("run record has all 7 stages in spine order", titles == list(STAGE_SPINE), str(titles))
    check("Source stage ingested the 8 demo objects", run["stages"][0]["metrics"]["objects"] == 8)
    check("Reconciliation stage flags the contradiction", run["stages"][1]["status"] == "flag"
          and run["stages"][1]["metrics"]["contradictions"] >= 1)
    check("Anti-Fragility stage routed a review + proposed (not applied) fix",
          run["stages"][2]["metrics"]["reviews"] == 1 and run["stages"][2]["metrics"]["applied"] is False
          and run["stages"][2]["metrics"]["patch"] == "3→5")
    check("Enhancement stage answers 5 with source handles",
          run["stages"][3]["metrics"]["answer"] == 5 and run["stages"][3]["source_handles"])
    check("Optimization stage shows compression (after < before)",
          run["stages"][4]["metrics"]["tokens_after"] < run["stages"][4]["metrics"]["tokens_before"])
    check("Consumption stage carries a lineage_manifest_ref", bool(run["stages"][5]["metrics"]["lineage_manifest_ref"]))
    check("Verification rail shows raw underperforms the pack",
          run["stages"][6]["metrics"]["raw_underperforms_pack"] is True)
    check("graph view has nodes + edges for visualization", len(run["graph"]["nodes"]) == 8 and run["graph"]["edges"])

    # ── clickable-graph object detail (with a PRE-COMPUTED gated expansion per node) ──
    det = run["object_detail"]
    check("object_detail present for every graph node",
          set(det) == {n["id"] for n in run["graph"]["nodes"]}, str(len(det)))
    check("every object_detail carries source_handles", all(d["source_handles"] for d in det.values()))
    adr = det.get("obj-adr-014", {})
    check("allowed expansion returns a real excerpt (ADR mentions 5)",
          adr.get("expansion_allowed", {}).get("allowed") is True
          and "5" in (adr.get("expansion_allowed", {}).get("raw_excerpt") or ""))
    check("denied expansion leaks NO raw + carries a reason",
          adr.get("expansion_denied", {}).get("allowed") is False
          and adr.get("expansion_denied", {}).get("raw_excerpt") is None
          and adr.get("expansion_denied", {}).get("reason") == "classification_restricted")
    check("object_detail includes the ADR's max_retries assertion",
          any(a["predicate"] == "max_retries" and a["value"] == 5 for a in adr.get("assertions", [])))
    check("available_corpora lists acme + cfpb (both offline-real)",
          {c["id"] for c in run["available_corpora"]} == {"acme", "cfpb"})
    check("export is deterministic (byte-identical re-run)", build_run("acme") == run)

    # ── cfpb now runs the SAME real offline motion (no seam) ──
    cf = build_run("cfpb")
    check("cfpb is a real offline run (not a seam)", cf["seam"] is False and cf["live"] is False)
    check("cfpb Source stage ingested its objects", cf["stages"][0]["metrics"]["objects"] >= 7)
    check("cfpb Reconciliation flags the Reg-E-vs-FAQ contradiction",
          cf["stages"][1]["status"] == "flag" and cf["stages"][1]["metrics"]["contradictions"] >= 1)
    check("cfpb Anti-Fragility proposes the 30→10 fix (not applied)",
          cf["stages"][2]["metrics"]["patch"] == "30→10" and cf["stages"][2]["metrics"]["applied"] is False)
    check("cfpb Enhancement answers 10", cf["stages"][3]["metrics"]["answer"] == 10)
    check("cfpb graph has nodes + edges", len(cf["graph"]["nodes"]) >= 7 and cf["graph"]["edges"])
    check("cfpb is deterministic", build_run("cfpb") == cf)

    # ── HITL review queue: steward reviews routed by the swarm across BOTH corpora ──
    rq = build_review_queue()
    check("review queue has >= 2 open reviews (one per corpus)", len(rq["reviews"]) >= 2, str(len(rq["reviews"])))
    for rv in rq["reviews"]:
        rr = rv["request"]
        check(f"review[{rr.get('subject')}] is high_conflict_claim + high risk + owned",
              rr.get("trigger") == "high_conflict_claim" and rr.get("risk") == "high" and bool(rr.get("owner")))
        check(f"review[{rr.get('subject')}] has decision options + a proposed (not applied) patch",
              rv["decision_options"] == ["approve", "reject", "needs_more_info"]
              and rv["proposed_patch"] and rv["proposed_patch"]["applied"] is False)
    fixes = {(rv["proposed_patch"]["from_value"], rv["proposed_patch"]["to_value"]) for rv in rq["reviews"]}
    check("proposed fixes cover acme 3→5 and cfpb 30→10", fixes == {(3, 5), (30, 10)}, str(fixes))
    try:
        from jsonschema import Draft202012Validator
        schema = json.loads((_resource("schemas/governance/steward-review-request.schema.json")).read_text())
        v = Draft202012Validator(schema)
        errs = [e.message for rv in rq["reviews"] for e in v.iter_errors(rv["request"])]
        check("every routed request validates against steward-review-request.schema.json", not errs, "; ".join(errs[:2]))
    except ImportError:
        print("  [skip] jsonschema not installed — review-request schema validation skipped")
    check("review queue is deterministic", build_review_queue() == rq)

    # ── version timelines: v1 (stale, current) → v2 (PROPOSED, pending review, not applied) ──
    vt = build_version_timeline()
    check("version timeline has >= 2 patched objects", len(vt["timelines"]) >= 2, str(len(vt["timelines"])))
    rq_ids = {rv["request"]["review_request_id"] for rv in rq["reviews"]}
    for t in vt["timelines"]:
        vs = t["versions"]
        check(f"{t['object_id']}: exactly v1→v2", len(vs) == 2 and [v["source_revision"] for v in vs] == ["v1", "v2-proposed"])
        v1, v2 = vs
        check(f"{t['object_id']}: v1 is the stale current", v1["status"] == "stale" and v1["is_current"] is True)
        check(f"{t['object_id']}: v2 is PROPOSED + pending review + NOT applied + NOT promoted",
              v2["status"] == "proposed" and v2["lifecycle"] == "pending_review"
              and v2["applied"] is False and v2["candidate_promoted"] is False and v2["is_current"] is False)
        check(f"{t['object_id']}: current pointer still v1 (not a mutation)", t["current_version_id"] == v1["context_version_id"])
        check(f"{t['object_id']}: v2 links a REAL routed review request", v2["review_request_id"] in rq_ids)
    fixes = {(t["versions"][0]["value"], t["versions"][1]["value"]) for t in vt["timelines"]}
    check("timelines cover acme 3→5 and cfpb 30→10", fixes == {(3, 5), (30, 10)}, str(fixes))
    try:
        from jsonschema import Draft202012Validator
        cv = Draft202012Validator(json.loads((_resource("schemas/context-version.schema.json")).read_text()))
        verrs = [e.message for t in vt["timelines"] for v in t["versions"] for e in cv.iter_errors(v)]
        check("every version validates against context-version.schema.json", not verrs, "; ".join(verrs[:2]))
    except ImportError:
        print("  [skip] jsonschema not installed — context-version validation skipped")
    check("version timeline is deterministic", build_version_timeline() == vt)
    # the patched object's detail also carries its versions (for the console panel)
    check("patched object_detail carries its version timeline",
          "versions" in run["object_detail"].get("obj-runbook", {})
          and len(run["object_detail"]["obj-runbook"]["versions"]) == 2)

    # ── DRIFT-CHECK: the committed _repos/baltor/frontend/*.json must byte-match their builders ──
    drifted = _stale_files()
    check("written demo-run*.json are in sync with build_run (no stale artifact)", not drifted,
          f"stale: {drifted} — run `python3 scripts/demo_run_export.py --write`")

    print(f"\n{'PASS — demo_run_export: BOTH acme + cfpb assemble a real offline run record (7 stages + graph + lift matrix + receipt); cfpb answers 10 (Reg E) with the 30→10 fix proposed; committed JSON in sync (drift-checked); deterministic.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Assemble the unified demo run record the console animates.")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--corpus", default="acme", choices=tuple(CORPORA))
    p.add_argument("--write", action="store_true", help="(re)write _repos/baltor/frontend/demo-run*.json for ALL corpora")
    p.add_argument("--check-fresh", action="store_true", help="exit 1 if any committed demo-run*.json is stale")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.check_fresh:
        stale = _stale_files()
        print("STALE: " + ", ".join(stale) if stale else "demo-run*.json are fresh")
        return 1 if stale else 0
    if args.write:
        for f in write_all():
            print(f"wrote {f}")
        return 0
    print(_serialize(build_run(args.corpus)))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
