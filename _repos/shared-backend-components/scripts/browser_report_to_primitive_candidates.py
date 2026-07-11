#!/usr/bin/env python3
"""scripts.browser_report_to_primitive_candidates — ADDITIVE: a browser_session_report -> browser_primitive_candidate rows.

Consumes a browser_session_report (from scripts.browser_session_report) and emits one full
browser_primitive_candidate CONTRACT row per opportunity the session implies:

    page_state_classifier · form_field_mapper (per form) · safe_submit_gate (per POST / side-effect form) ·
    success_state_verifier · dom_drift_detector · tab_graph_builder · popup_detector · download_origin_tracker
    (+ api_from_browser_endpoint_candidate when the session referenced API endpoints).

Each candidate carries: evidence_refs back to the CapturedArtifact source_hash, an input_state/output_state,
pre/postconditions, side_effects, required_permissions, a determinism_level (D0 for the deterministic
classifiers/gates, D2 where an LLM assists with a deterministic fallback), fixtures, a verifier_plan string,
and a risk_score. Every row is candidate=true / serves_truth=false — generation is not promotion.

The candidate_id comes from the report's seed (minted by scripts.browser_session_report.browser_candidate_id),
so the report's candidate_primitives index and these full rows always agree — no drift.

    python3 scripts/browser_report_to_primitive_candidates.py --self-test
    python3 scripts/browser_report_to_primitive_candidates.py --demo
    python3 scripts/browser_report_to_primitive_candidates.py --from-report <browser_session_reports.jsonl>
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install, resource  # noqa: E402

_install()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any, Optional  # noqa: E402

from scripts.browser_session_report import (  # noqa: E402  the report builder + the single id authority
    CANDIDATE_TYPES,
    SCHEMA_VERSION,
    browser_candidate_id,
    build_fixture_session_report,
    _make_test_clock,
)

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
CANDIDATE_RECORD_TYPE = "browser_primitive_candidate"
_DATA_SUBDIR = "data/dev-intel/browser_reports"
CANDIDATE_FILENAME = "browser_primitive_candidates.jsonl"

# ── the candidate CONTRACT templates (one per candidate_type) ─────────────────────────────────────────────────────
# input/output STATE + pre/postconditions + permissions + determinism + verifier_plan + a base risk. The evidence
# looked up from the report enriches the form/download/endpoint-specific fields and the final risk_score.
_CANDIDATE_SPECS: dict[str, dict[str, Any]] = {
    "page_state_classifier": {
        "input_state": {"kind": "page_bundle", "reads": ["dom_hash", "readable_text", "forms", "login_wall",
                                                         "downloadable_docs", "api_spec_links"]},
        "output_state": {"kind": "page_state_label", "values": ["not_captured", "login_wall", "form_entry",
                                                                "download_page", "api_portal", "content"]},
        "preconditions": ["page captured (a DOM/text bundle is available)"],
        "postconditions": ["exactly one page_state label emitted", "no navigation or mutation performed"],
        "side_effects": [],
        "required_permissions": ["dom_read"],
        "determinism_level": "D0",
        "verifier_plan": "Replay the bundled DOM fixtures; assert the classifier returns the labelled page_state "
                         "for each. Mutation gate: flip a login_wall fixture -> label must change. Determinism: "
                         "same bundle -> same label twice.",
        "base_risk": 0.10,
    },
    "form_field_mapper": {
        "input_state": {"kind": "form_descriptor", "reads": ["fields[].name", "fields[].type", "action", "method"]},
        "output_state": {"kind": "field_role_map", "note": "each field -> a semantic role or 'unknown'"},
        "preconditions": ["form fields extracted (names + types)"],
        "postconditions": ["every field mapped to a role or 'unknown'", "no form submitted"],
        "side_effects": [],
        "required_permissions": ["dom_read"],
        "determinism_level": "D2",
        "verifier_plan": "Map the fixture form's fields; assert known fields (e.g. *_id, email, password) get the "
                         "expected roles. Mutation gate: rename a field -> its role must change. The LLM path is "
                         "SHADOWED against the deterministic name-pattern mapper; disagreement is a review ticket.",
        "base_risk": 0.30,
    },
    "safe_submit_gate": {
        "input_state": {"kind": "form_submission_intent", "reads": ["action", "method", "side_effect_risk", "mode"]},
        "output_state": {"kind": "gate_decision", "values": ["allow", "block", "require_confirmation"]},
        "preconditions": ["a POST / side-effect form identified", "the session mode is known"],
        "postconditions": ["submission BLOCKED unless mode=side_effect_allowed AND explicit confirmation present",
                           "the gate itself performs NO submission — it only decides"],
        "side_effects": [],
        "required_permissions": ["dom_read", "submit_gate"],
        "determinism_level": "D0",
        "verifier_plan": "Feed the form under mode=read_only -> assert BLOCK; under side_effect_allowed WITHOUT "
                         "confirmation -> assert require_confirmation. Mutation gate: flip the regulated flag -> the "
                         "decision must change; a regulated action must NEVER auto-allow.",
        "base_risk": 0.60,
    },
    "success_state_verifier": {
        "input_state": {"kind": "pre_and_post_page_bundle", "reads": ["baseline_dom_hash", "post_dom", "markers"]},
        "output_state": {"kind": "success_verdict", "values": ["success", "failure", "unknown"]},
        "preconditions": ["a before/after DOM pair or an expected success-marker set"],
        "postconditions": ["verdict grounded in observed post-state markers", "no state mutation performed"],
        "side_effects": [],
        "required_permissions": ["dom_read"],
        "determinism_level": "D2",
        "verifier_plan": "Provide labelled success/failure post-pages; assert the verdict matches. Mutation gate: "
                         "swap the success marker -> the verdict must flip. LLM path shadowed vs a deterministic "
                         "marker matcher.",
        "base_risk": 0.20,
    },
    "dom_drift_detector": {
        "input_state": {"kind": "two_dom_hashes", "reads": ["baseline_dom_hash", "new_dom_hash"]},
        "output_state": {"kind": "drift_report", "fields": ["changed", "severity"]},
        "preconditions": ["a baseline dom_hash recorded for the url"],
        "postconditions": ["changed = (new dom_hash != baseline dom_hash)", "read-only"],
        "side_effects": [],
        "required_permissions": ["dom_read"],
        "determinism_level": "D0",
        "verifier_plan": "Hash-compare identical bundles -> no drift. Mutation gate: alter one byte -> changed=true. "
                         "Determinism: the same DOM hashes byte-identical twice.",
        "base_risk": 0.10,
    },
    "tab_graph_builder": {
        "input_state": {"kind": "captured_artifact_list", "reads": ["url", "links_sample", "domain"]},
        "output_state": {"kind": "tab_graph", "fields": ["nodes", "edges", "openers", "cross_origin_transitions"]},
        "preconditions": [">=2 captured pages with extracted links"],
        "postconditions": ["opener edges ONLY where a parent's links contain the child url (no synthetic edges)",
                           "read-only"],
        "side_effects": [],
        "required_permissions": ["dom_read"],
        "determinism_level": "D0",
        "verifier_plan": "Build the graph from the fixture; assert opener(child)=parent, cross-origin flagged, "
                         "duplicates grouped. Mutation gate: drop a parent's link -> that child's opener becomes null.",
        "base_risk": 0.10,
    },
    "popup_detector": {
        "input_state": {"kind": "tab_graph_transitions", "reads": ["opener", "from_domain", "to_domain", "auth_state"]},
        "output_state": {"kind": "popup_flags", "note": "which child opens are popups (auth/cross-origin shaped)"},
        "preconditions": ["tab transitions available (openers + origins)"],
        "postconditions": ["popup flagged on cross-origin auth-shaped child opens", "read-only"],
        "side_effects": [],
        "required_permissions": ["dom_read"],
        "determinism_level": "D0",
        "verifier_plan": "Feed a cross-origin auth-shaped child -> popup=true; a same-origin nav -> popup=false. "
                         "Mutation gate: change the child origin -> the flag must flip.",
        "base_risk": 0.20,
    },
    "download_origin_tracker": {
        "input_state": {"kind": "download_list", "reads": ["url", "page_origin"]},
        "output_state": {"kind": "download_origin_report", "fields": ["origin", "cross_origin", "trust_tier", "ext"]},
        "preconditions": [">=1 downloadable resource discovered"],
        "postconditions": ["each download tagged with origin + cross_origin + trust_tier", "no file fetched or opened"],
        "side_effects": [],
        "required_permissions": ["dom_read"],
        "determinism_level": "D0",
        "verifier_plan": "Tag the fixture PDF; assert origin=host, cross_origin computed vs the page origin, "
                         "trust_tier via classify_trust_tier. Mutation gate: move the download to a foreign host -> "
                         "cross_origin must flip.",
        "base_risk": 0.30,
    },
    "api_from_browser_endpoint_candidate": {
        "input_state": {"kind": "discovered_endpoint", "reads": ["endpoint_url", "endpoint_kind"]},
        "output_state": {"kind": "api_interface_primitive_seed", "note": "proposes an api_interface_primitive candidate"},
        "preconditions": ["an API endpoint/spec (openapi/graphql/postman) referenced by a captured page"],
        "postconditions": ["proposes an api_interface_primitive candidate (schema + side-effect + auth TBD)",
                           "NO request issued; the seed stays candidate/serves_truth=false until the spec is "
                           "fetched + reviewed"],
        "side_effects": [],
        "required_permissions": ["dom_read", "network_read"],
        "determinism_level": "D2",
        "verifier_plan": "From the discovered openapi/graphql url, assert an api_interface_primitive seed with the "
                         "endpoint + kind. Mutation gate: remove the spec link -> no candidate is produced.",
        "base_risk": 0.40,
    },
}

_EVIDENCE_TO_FIXTURE = {"source_hash": "dom_bundle", "form": "form_action", "download": "download_url",
                        "network": "endpoint", "api_spec": "api_spec", "url": "url", "tab": "tab"}


def _fixtures_from_evidence(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for e in evidence:
        v = e.get("value")
        if not v:
            continue
        kind = _EVIDENCE_TO_FIXTURE.get(e.get("kind", ""), e.get("kind", "ref"))
        key = (kind, v)
        if key in seen:
            continue
        seen.add(key)
        out.append({"kind": kind, "value": v})
    return out


def _clamp(x: float) -> float:
    return round(float(max(0.0, min(1.0, x))), 3)


def _spec_for(seed: dict[str, Any], report: dict[str, Any], forms_by_id: dict[str, Any]) -> dict[str, Any]:
    ctype = seed["candidate_type"]
    tmpl = _CANDIDATE_SPECS[ctype]
    spec: dict[str, Any] = {
        "input_state": dict(tmpl["input_state"]),
        "output_state": dict(tmpl["output_state"]),
        "preconditions": list(tmpl["preconditions"]),
        "postconditions": list(tmpl["postconditions"]),
        "side_effects": list(tmpl["side_effects"]),
        "required_permissions": list(tmpl["required_permissions"]),
        "determinism_level": tmpl["determinism_level"],
        "verifier_plan": tmpl["verifier_plan"],
    }
    risk = float(tmpl["base_risk"])

    if ctype in ("form_field_mapper", "safe_submit_gate") and seed.get("ref_kind") == "form":
        form = forms_by_id.get(seed.get("ref_id"), {})
        spec["input_state"] = {**spec["input_state"], "action": form.get("action", ""),
                               "method": form.get("method", ""), "fields": form.get("fields", []),
                               "side_effect_risk": form.get("side_effect_risk", "read")}
        if ctype == "safe_submit_gate":
            fr = form.get("side_effect_risk", "write")
            risk = {"regulated": 0.90, "write": 0.70}.get(fr, 0.60)
            if fr == "regulated":
                spec["postconditions"] = spec["postconditions"] + [
                    "REGULATED action: always require explicit human confirmation; never auto-allow"]
    if ctype == "download_origin_tracker" and any(d.get("cross_origin") for d in report.get("downloads", [])):
        spec["input_state"] = {**spec["input_state"], "cross_origin_downloads_present": True}
        risk += 0.20
    if ctype == "popup_detector" and report.get("tab_graph", {}).get("popups"):
        risk += 0.10
    if ctype == "api_from_browser_endpoint_candidate" and seed.get("ref_kind") == "network":
        spec["input_state"] = {**spec["input_state"], "endpoint_url": seed.get("ref_id")}

    spec["risk_score"] = _clamp(risk)
    return spec


def report_to_candidates(session_report: dict[str, Any]) -> list[dict[str, Any]]:
    """Expand a browser_session_report's candidate opportunity seeds into full browser_primitive_candidate rows."""
    session_id = session_report.get("session_id", "")
    forms_by_id = {f["form_id"]: f for f in session_report.get("forms", [])}
    session_source_hashes = [t["dom_hash"] for t in session_report.get("tabs", []) if t.get("dom_hash")]
    out: list[dict[str, Any]] = []
    for seed in session_report.get("candidate_primitives", []):
        ctype = seed.get("candidate_type")
        if ctype not in CANDIDATE_TYPES:
            continue
        evidence = list(seed.get("evidence_refs") or [])
        if not any(e.get("kind") == "source_hash" for e in evidence):
            # GUARANTEE provenance back to a CapturedArtifact source_hash for every candidate
            evidence = [{"kind": "source_hash", "value": h} for h in session_source_hashes[:6]] + evidence
        spec = _spec_for(seed, session_report, forms_by_id)
        row = {
            "record_type": CANDIDATE_RECORD_TYPE,
            "schema_version": SCHEMA_VERSION,
            "candidate_id": seed.get("candidate_id")
            or browser_candidate_id(ctype, session_id, ""),   # seed id is authoritative; fallback only if absent
            "candidate_type": ctype,
            "source_session_id": session_id,
            "evidence_refs": evidence,
            **spec,
            "fixtures": _fixtures_from_evidence(evidence),
            **BOUNDARY,
        }
        out.append(row)
    return out


def write_candidates(rows: list[dict[str, Any]], out_path: Optional[Path] = None) -> Path:
    out_path = out_path or (resource(_DATA_SUBDIR) / CANDIDATE_FILENAME)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    return out_path


def _validator():
    import jsonschema
    schema = json.loads((resource("schemas") / "browser_primitive_candidate.schema.json").read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(schema)


# ── self-test (offline, deterministic, mutation-gated) ────────────────────────────────────────────────────────────
def self_test() -> int:
    checks: list[tuple[str, bool]] = []

    report = build_fixture_session_report(clock=_make_test_clock(), mode="read_only")
    cands = report_to_candidates(report)
    by_type: dict[str, list[dict[str, Any]]] = {}
    for c in cands:
        by_type.setdefault(c["candidate_type"], []).append(c)

    checks.append((">=8 candidate TYPES produced from the fixture report",
                   len(by_type) >= 8))
    checks.append(("all candidate types are from the canonical set",
                   set(by_type) <= set(CANDIDATE_TYPES)))
    checks.append(("every candidate is candidate-only (serves_truth=false)",
                   all(c["candidate"] is True and c["serves_truth"] is False for c in cands)))
    checks.append(("every candidate has evidence_refs back to a CapturedArtifact source_hash",
                   all(any(e.get("kind") == "source_hash" for e in c["evidence_refs"]) for c in cands)))
    checks.append(("every candidate carries a non-empty verifier_plan + fixtures + risk_score in [0,1]",
                   all(isinstance(c["verifier_plan"], str) and c["verifier_plan"]
                       and c["fixtures"] and 0.0 <= c["risk_score"] <= 1.0 for c in cands)))

    # safe_submit_gate present for the POST /submit-claim form, and it is regulated + D0 + high risk
    gates = by_type.get("safe_submit_gate", [])
    post_gate = next((g for g in gates if g["input_state"].get("method") == "post"), None)
    checks.append(("safe_submit_gate present for the POST form (regulated, D0, risk>=0.9)",
                   post_gate is not None
                   and post_gate["input_state"].get("side_effect_risk") == "regulated"
                   and post_gate["determinism_level"] == "D0"
                   and post_gate["risk_score"] >= 0.9
                   and any("never auto-allow" in p for p in post_gate["postconditions"])))

    # determinism levels: D0 for classifiers/gates, D2 where LLM-assisted
    checks.append(("determinism levels correct (classifiers/gates D0; mapper/verifier/api D2)",
                   by_type["page_state_classifier"][0]["determinism_level"] == "D0"
                   and by_type["dom_drift_detector"][0]["determinism_level"] == "D0"
                   and by_type["tab_graph_builder"][0]["determinism_level"] == "D0"
                   and by_type["form_field_mapper"][0]["determinism_level"] == "D2"
                   and by_type["success_state_verifier"][0]["determinism_level"] == "D2"))
    checks.append(("api_from_browser_endpoint_candidate produced (network present) + D2",
                   by_type.get("api_from_browser_endpoint_candidate")
                   and by_type["api_from_browser_endpoint_candidate"][0]["determinism_level"] == "D2"))
    checks.append(("form_field_mapper emitted PER form (>=2 forms in the fixture)",
                   len(by_type.get("form_field_mapper", [])) >= 2))
    checks.append(("candidate_id is the report's seed id (single authority; starts with bpc-)",
                   all(c["candidate_id"].startswith("bpc-") for c in cands)
                   and {c["candidate_id"] for c in cands} == {s["candidate_id"]
                                                              for s in report["candidate_primitives"]}))

    # determinism — same report expands identically; a fresh fixture report expands identically end-to-end
    checks.append(("deterministic: report_to_candidates is pure (identical twice)",
                   json.dumps(cands, sort_keys=True) == json.dumps(report_to_candidates(report), sort_keys=True)))
    report2 = build_fixture_session_report(clock=_make_test_clock(), mode="read_only")
    checks.append(("deterministic end-to-end: fresh fixture -> identical candidates",
                   json.dumps(cands, sort_keys=True) == json.dumps(report_to_candidates(report2), sort_keys=True)))

    # MUTATION gate: a plain content page (no POST/side-effect form) -> NO safe_submit_gate, but a classifier IS emitted
    from scripts.browser_session_report import ARTIFACT_RECORD_TYPE, build_session_report
    plain_art = {"record_type": ARTIFACT_RECORD_TYPE, "url": "https://plain.example.com/", "captured": True,
                 "source_hash": "sha256:plain", "trust_tier": "T4",
                 "extracted": {"readable_text": "just an article", "links_sample": [], "forms": [],
                               "side_effect_controls": [], "downloadable_docs": [], "api_spec_links": []}}
    plain_cands = report_to_candidates(build_session_report([plain_art], clock=_make_test_clock(), mode="read_only"))
    plain_types = {c["candidate_type"] for c in plain_cands}
    checks.append(("mutation gate: no POST/side-effect form -> NO safe_submit_gate (classifier still emitted)",
                   "safe_submit_gate" not in plain_types and "page_state_classifier" in plain_types))

    # SCHEMA conformance for every candidate row
    schema_ok = True
    try:
        v = _validator()
        for c in cands:
            v.validate(c)
    except Exception as exc:  # noqa: BLE001
        schema_ok = False
        print(f"  [..] candidate schema validation error: {type(exc).__name__}: {exc}")
    checks.append(("every candidate validates against browser_primitive_candidate.schema.json", schema_ok))

    # write round-trip to a TEMP path (no repo data-dir pollution during proofs)
    import tempfile
    tmp = Path(tempfile.mkdtemp()) / CANDIDATE_FILENAME
    write_candidates(cands, tmp)
    wrote_ok = tmp.exists() and len(tmp.read_text().splitlines()) == len(cands)
    checks.append(("write round-trip (jsonl append) works", wrote_ok))

    ok = all(v for _, v in checks)
    for name, v in checks:
        print(f"  [{'ok' if v else 'XX'}] {name}")
    print(("PASS" if ok else "FAIL") + " - browser_report_to_primitive_candidates: browser_session_report -> "
          f"{len(cands)} browser_primitive_candidate rows across {len(by_type)} types (safe_submit_gate on the "
          "POST form, D0 gates/classifiers + D2 LLM-assisted), evidence-linked to source_hash, candidate-only "
          "(serves_truth=false), deterministic + schema-valid.")
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="browser_session_report -> browser_primitive_candidate rows (candidate-only).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--demo", action="store_true", help="expand the bundled fixture report and print a type summary")
    ap.add_argument("--from-report", metavar="JSONL", help="a browser_session_reports.jsonl (one report per line)")
    ap.add_argument("--out", metavar="JSONL", help="output path (default the browser_reports data dir)")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    if args.demo:
        import datetime as _dt
        clock = lambda: _dt.datetime.now(_dt.timezone.utc).timestamp()  # noqa: E731
        cands = report_to_candidates(build_fixture_session_report(clock=clock, mode="read_only"))
        summary: dict[str, int] = {}
        for c in cands:
            summary[c["candidate_type"]] = summary.get(c["candidate_type"], 0) + 1
        print(json.dumps({"n_candidates": len(cands), "by_type": summary}, indent=2, sort_keys=True))
        return 0
    if args.from_report:
        reports = [json.loads(ln) for ln in Path(args.from_report).read_text().splitlines() if ln.strip()]
        rows: list[dict[str, Any]] = []
        for rep in reports:
            rows.extend(report_to_candidates(rep))
        out = write_candidates(rows, Path(args.out) if args.out else None)
        print(f"expanded {len(reports)} report(s) -> {len(rows)} candidate rows -> {out}")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
