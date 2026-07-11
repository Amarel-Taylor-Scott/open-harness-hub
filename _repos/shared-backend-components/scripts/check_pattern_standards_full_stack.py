#!/usr/bin/env python3
"""scripts.check_pattern_standards_full_stack — the master full-stack honesty proof for the pattern system.

It loads every single-source in the standards layer and proves the WHOLE stack hangs together with no
over-claim:

  pattern_registry.json   -> the 25 canonical shapes + maturity
  standard_catalog.json   -> the construction standard per shape (the contract a template/check enforces)
  template_catalog.json   -> the scaffold a standard generates from
  routine_library.json    -> the named blessed operations per shape
  pattern_waivers.json     -> the explicit, time-boxed exceptions
  pattern_maturity_matrix.json -> the compact per-pattern roll-up
  _repos/shared-backend-components/docs/examples/standardized-patterns.md -> the canonical example per shape

It prints a table  PATTERN | STANDARD | TEMPLATE | EXAMPLES | PROOF | STATUS | WAIVERS  and ENFORCES the bar
HONESTLY:

  * maturity in {"standard","enforced"} MUST have a real proof script on disk + docs +
    (examples OR an open opportunity).  No active standard may lack a proof.  This is the hard gate; the
    proof FAILS (exit 1) on a genuine unbacked claim — it is NOT weakened.
  * maturity "candidate" only needs a routine, an opportunity, or a waiver (a lighter bar).
  * a standard CARD (standard_catalog.json) is the strongest form of "has a standard"; a governance /
    cross-cutting pattern graded "standard" by the registry's own rule (a real example + a passing proof)
    but WITHOUT a catalog card yet is surfaced explicitly in STATUS as ``standard (no catalog card)`` —
    that is a REPORTED gap (see registrations_needed.registry_fixes), never a silent pass.  Over-claims
    found here are reported to MAIN for a registry fix; this proof does not edit the registry.
  * the maturity matrix must agree with the registry (no drift between the two roll-ups).

Deterministic + offline (reads JSON/MD + checks path existence; no wall-clock, no RNG, no network).

CLI: python3 _repos/shared-backend-components/scripts/check_pattern_standards_full_stack.py --self-test
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_REGISTRY = _resource("architecture") / "pattern_registry.json"
_STANDARDS = _resource("architecture") / "standard_catalog.json"
_TEMPLATES = _resource("architecture") / "template_catalog.json"
_ROUTINES = _resource("architecture") / "routine_library.json"
_WAIVERS = _resource("architecture") / "pattern_waivers.json"
_MATRIX = _resource("architecture") / "pattern_maturity_matrix.json"
_OPPS = _resource("architecture") / "opportunities.json"
_EXAMPLES_DOC = _resource("docs") / "examples" / "standardized-patterns.md"

CANONICAL_PATTERNS = {
    "source_adapter_pattern", "parser_provider_pattern", "ingestion_sync_pattern", "source_artifact_pattern",
    "durable_command_pattern", "worker_claim_loop_pattern", "processor_harness_pattern",
    "artifact_envelope_pattern", "provider_adapter_pattern", "api_projection_route_pattern",
    "ui_projection_page_pattern", "proof_script_pattern", "documentation_page_pattern",
    "contract_schema_pattern", "capability_catalog_entry_pattern", "optimization_candidate_pattern",
    "reconciliation_decision_pattern", "held_out_warning_pattern", "watchtower_verification_task_pattern",
    "tenant_isolation_pattern", "structured_logging_pattern", "review_pack_pattern",
    "section_maturity_entry_pattern", "dependency_emulator_pattern", "multi_source_fixture_pattern",
}
ACTIVE_MATURITY = {"standard", "enforced"}
_PATTERN_RE = re.compile(r"`([a-z_]+_pattern)`")


def _exists(rel: str) -> bool:
    """Path-existence allowing a registry '#anchor' suffix (the file/dir before '#' must exist)."""
    return (_resource(rel.split("#")[0])).exists()


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def analyze() -> dict:
    """Build the full-stack roll-up (pure; used by both the table and the gate)."""
    reg = _load(_REGISTRY)
    std = _load(_STANDARDS)
    tmpl = _load(_TEMPLATES)
    rout = _load(_ROUTINES)
    wv = _load(_WAIVERS)
    matrix = _load(_MATRIX)
    opps = _load(_OPPS)
    examples_doc = _EXAMPLES_DOC.read_text(encoding="utf-8") if _EXAMPLES_DOC.exists() else ""

    std_by_pat: dict[str, list[dict]] = {}
    for s in std.get("standards", []):
        std_by_pat.setdefault(s.get("pattern_id"), []).append(s)
    tmpl_ids = {t["template_id"] for t in tmpl.get("templates", [])}
    rout_pats = {r.get("pattern_id") for r in rout.get("routines", [])}
    wv_by_pat: dict[str, list[dict]] = {}
    for w in wv.get("waivers", []):
        wv_by_pat.setdefault(w.get("pattern_id"), []).append(w)
    # opportunities that name a pattern (in any free-text field) act as the "open opportunity" escape hatch.
    opp_blob = json.dumps(opps)
    # examples named in the standardized-patterns field guide
    doc_patterns = set(_PATTERN_RE.findall(examples_doc))

    rows: list[dict] = []
    for p in reg.get("patterns", []):
        pid = p.get("pattern_id")
        mat = p.get("maturity")
        cards = std_by_pat.get(pid, [])
        # template via any standard card OR registry template_ids
        tmpl_for = [tid for c in cards for tid in c.get("template_ids", []) if tid in tmpl_ids]
        tmpl_for += [tid for tid in p.get("template_ids", []) if tid in tmpl_ids]
        real_proof = any(_exists(pr) for pr in p.get("required_proofs", []))
        # a pattern is documented if: the registry names a doc that exists, OR it is in the field guide,
        # OR its standard card cites a real .md example doc on disk (all real on-disk documentation).
        card_doc = any((_resource(e)).exists() and e.endswith(".md")
                       for c in cards for e in c.get("examples", []))
        real_docs = any(_exists(d) for d in p.get("required_docs", [])) or pid in doc_patterns or card_doc
        examples_real = any((_resource(e)).exists() for e in p.get("detected_examples", []))
        has_routine = pid in rout_pats
        has_waiver = bool(wv_by_pat.get(pid))
        has_opp = pid in opp_blob
        in_field_guide = pid in doc_patterns

        rows.append({
            "pattern_id": pid,
            "maturity": mat,
            "has_card": bool(cards),
            "templates": sorted(set(tmpl_for)),
            "examples_count": len(p.get("detected_examples", [])),
            "examples_real": examples_real,
            "real_proof": real_proof,
            "real_docs": real_docs,
            "has_routine": has_routine,
            "has_waiver": has_waiver,
            "has_opp": has_opp,
            "in_field_guide": in_field_guide,
        })

    return {
        "rows": rows,
        "matrix": matrix,
        "registry": reg,
    }


def _status(row: dict) -> str:
    mat = row["maturity"]
    if mat in ACTIVE_MATURITY:
        if row["has_card"]:
            return mat  # full-stack standard with a catalog card
        return f"{mat} (no catalog card)"  # registry-graded standard; card is a REPORTED gap
    return mat  # candidate / deprecated


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    data = analyze()
    rows = data["rows"]

    # --- the table ---
    print()
    hdr = f"  {'PATTERN':38} {'STANDARD':10} {'TEMPLATE':10} {'EXAMPLES':8} {'PROOF':6} {'STATUS':24} {'WAIVERS'}"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for r in sorted(rows, key=lambda x: x["pattern_id"]):
        print(f"  {r['pattern_id']:38} "
              f"{('card' if r['has_card'] else '-'):10} "
              f"{(r['templates'][0] if r['templates'] else '-')[:10]:10} "
              f"{r['examples_count']:<8} "
              f"{('yes' if r['real_proof'] else 'NO'):6} "
              f"{_status(r):24} "
              f"{'yes' if r['has_waiver'] else '-'}")
    print()

    # --- structural: exactly the 25 canonical ids present ---
    ids = {r["pattern_id"] for r in rows}
    check("registry covers exactly the 25 canonical pattern ids", ids == CANONICAL_PATTERNS,
          str(sorted(ids ^ CANONICAL_PATTERNS)))

    # --- HARD GATE: every active (standard/enforced) pattern is actually backed ---
    # bar = real proof on disk + docs + (examples OR an open opportunity).  No weakening.
    no_proof, no_docs, no_examples_no_opp = [], [], []
    for r in rows:
        if r["maturity"] in ACTIVE_MATURITY:
            if not r["real_proof"]:
                no_proof.append(r["pattern_id"])
            if not r["real_docs"]:
                no_docs.append(r["pattern_id"])
            if not (r["examples_real"] or r["has_opp"]):
                no_examples_no_opp.append(r["pattern_id"])
    check("no active standard lacks a real proof script on disk", no_proof == [], str(no_proof))
    check("every active standard has docs (required_docs or field-guide entry)", no_docs == [], str(no_docs))
    check("every active standard has real examples or an open opportunity",
          no_examples_no_opp == [], str(no_examples_no_opp))

    # --- HARD GATE: every active pattern has an owner (owner_folder) — no active pattern may lack an owner ---
    reg_by_id = {p["pattern_id"]: p for p in data["registry"].get("patterns", [])}
    no_owner = [r["pattern_id"] for r in rows
                if r["maturity"] in ACTIVE_MATURITY and not reg_by_id.get(r["pattern_id"], {}).get("owner_folder")]
    check("no active pattern lacks an owner_folder", no_owner == [], str(no_owner))

    # --- candidate bar: a candidate needs a routine, an opportunity, OR a waiver (lighter) ---
    weak_candidate = [r["pattern_id"] for r in rows
                      if r["maturity"] == "candidate"
                      and not (r["has_routine"] or r["has_opp"] or r["has_waiver"])]
    check("every candidate pattern has a routine, opportunity, or waiver", weak_candidate == [],
          str(weak_candidate))

    # --- a pattern WITH a catalog card must have a template via that card or an explicit no-template note ---
    # (the card carries template_ids; a card with no template must say so in proof_rules/registry_rules text)
    card_no_template = []
    std = _load(_STANDARDS)
    for s in std.get("standards", []):
        if s.get("status") in ("active", "enforced"):
            tids = [t for t in s.get("template_ids", [])]
            if not tids:
                card_no_template.append(s.get("standard_id"))
    check("every active/enforced standard CARD names a template (or none are template-less)",
          card_no_template == [], str(card_no_template))

    # --- maturity matrix agrees with the registry (no drift) ---
    matrix = data["matrix"].get("patterns", {})
    drift = []
    for r in rows:
        mrow = matrix.get(r["pattern_id"], {})
        if mrow.get("maturity") != r["maturity"]:
            drift.append(f"{r['pattern_id']}: matrix={mrow.get('maturity')} registry={r['maturity']}")
    check("pattern_maturity_matrix maturity matches the registry (no drift)", drift == [], str(drift[:6]))

    # --- honesty echo: surface (do not fail on) the catalog-card gaps so the report is truthful ---
    card_gaps = sorted(r["pattern_id"] for r in rows
                       if r["maturity"] in ACTIVE_MATURITY and not r["has_card"])
    if card_gaps:
        print(f"  [note] {len(card_gaps)} active pattern(s) graded by the registry rule but with NO "
              f"standard_catalog card yet (REPORTED to MAIN as registry_fixes, backed by proof+docs+examples): "
              f"{card_gaps}")

    print(f"\n{'PASS — check_pattern_standards_full_stack: 25 patterns; every active standard is backed by a real proof + docs + examples/opportunity + owner; no matrix drift.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Master full-stack honesty proof for the pattern/standards system.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
