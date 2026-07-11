#!/usr/bin/env python3
"""scripts.research_evidence_primitives — CERTIFIED deterministic primitives for evidence-heavy research
(legal / FOIA / standards / regulatory / procurement / medical-policy) from the Universal Research Primitives
spec. These are the SAME governance thesis as the code registry, applied to evidence: LLM proposes, the
deterministic gate disposes. Source-status tiering == the candidate/truth boundary for sources; the quote gate
== "never headline a proxy" for citations. Each primitive is pure + oracle-tested, and the fixtures ARE the
spec's §15 evaluation tests (metadata never becomes quote-ready; adverse authority not hidden; overstatement
downgraded; theory shifts flagged; proof-gaps map to records). candidate=true / serves_truth=false.

    python3 scripts/research_evidence_primitives.py --self-test
    python3 scripts/research_evidence_primitives.py --certify
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/project_coverage_primitive_pack.py) ───────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import inspect  # noqa: E402
import json  # noqa: E402
from typing import Any, Callable  # noqa: E402

try:
    from src.teleon.experiments.ids import canonical_id  # noqa: E402
except Exception as exc:  # noqa: BLE001
    raise SystemExit(f"research_evidence_primitives requires canonical_id; import failed: {exc}")

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
RE_ID_PREFIX = "prim-research"
RE_RECORD_TYPE = "research_evidence_primitive_candidate"
PACK_FILENAME = "research_evidence_primitive_cards.jsonl"
PACK_DIR_REL = "data/dev-intel/primitive_factory/specialized_packs"


def source_tier(source: dict) -> int:
    """Classify a research source into reliability tier 1-6 (1=quote-ready primary authority ... 6=rejected).
    Deterministic gate mirroring the candidate/truth boundary for evidence."""
    if source.get("rejected") or source.get("nonexistent"):
        return 6
    if source.get("verified_quote") and source.get("local_path") and source.get("primary"):
        return 1
    if source.get("official_standard") and source.get("local_path"):
        return 2
    if source.get("verified_real") and source.get("comparator"):
        return 3
    if source.get("metadata_confirmed") and not source.get("full_text"):
        return 4
    return 5


def quote_ready(tier: int) -> bool:
    """Only tier 1-2 sources may be directly QUOTED in a formal filing (primary text checked)."""
    return tier in (1, 2)


def quote_gate(tier: int) -> dict:
    """THE core rule (spec §15 Test 1): a metadata-only / summary lead (tier 4-6) can NEVER become a filing
    quotation. Returns {allowed, reason}."""
    allowed = tier in (1, 2)
    return {"allowed": allowed,
            "reason": "quote-ready primary/official text" if allowed
            else f"tier {tier} is a research lead only — not quote-ready in a formal filing"}


def overstatement_flag(claim: str, has_quote_ready_support: bool) -> dict:
    """Downgrade a claim that uses ABSOLUTE language without quote-ready support (spec §15 Test 3). Deterministic."""
    absolutes = ("never", "always", "cannot", "can't", "no case", "every ", "all ", "impossible", "guarantee")
    low = (claim or "").lower()
    has_absolute = any(a in low for a in absolutes)
    return {"unsafe": has_absolute and not has_quote_ready_support, "has_absolute": has_absolute}


def adversarial_complete(argument: dict) -> dict:
    """No argument is complete without an OPPOSING point AND a best response (spec §15 Test 2). Returns
    {complete, missing}."""
    missing = [k for k in ("opposing_point", "best_response") if not argument.get(k)]
    return {"complete": len(missing) == 0, "missing": missing}


def theory_shift(charged_theory: str, asserted_theory: str) -> dict:
    """Flag when an asserted theory differs from the CHARGED one — a possible shift to defend against, not the
    original charge (spec §15 Test 4). Deterministic."""
    return {"shift": (charged_theory or "").strip().lower() != (asserted_theory or "").strip().lower()}


def proof_gap_to_records(gap: str) -> list:
    """Map an evidentiary gap to TARGETED records-request categories (spec §15 Test 5), not fishing language."""
    mapping = {
        "no_visible_designation": ["site_plans", "as_builts", "striping_records", "wheel_stop_function_records",
                                   "sign_plans", "dated_photos"],
        "no_posted_restriction": ["sign_inventory", "sign_plan", "dated_photos", "installation_records",
                                  "bulletin_board_contents"],
        "no_actual_notice": ["warning_records", "officer_notes", "bodycam_dashcam", "hotline_contacts"],
    }
    return mapping.get(gap, [])


_PRIMITIVES: list[dict[str, Any]] = [
    {"fn": source_tier, "family": "evidence_gate",
     "fixtures": [(({"verified_quote": True, "local_path": "x", "primary": True},), 1),
                  (({"official_standard": True, "local_path": "s.pdf"},), 2),
                  (({"verified_real": True, "comparator": True},), 3),
                  (({"metadata_confirmed": True, "full_text": False},), 4),
                  (({"summary_only": True},), 5), (({"rejected": True},), 6)]},
    {"fn": quote_ready, "family": "evidence_gate",
     "fixtures": [((1,), True), ((2,), True), ((3,), False), ((4,), False), ((6,), False)]},
    {"fn": quote_gate, "family": "evidence_gate",
     "fixtures": [((1,), {"allowed": True, "reason": "quote-ready primary/official text"}),
                  ((4,), {"allowed": False, "reason": "tier 4 is a research lead only — not quote-ready in a formal filing"})]},
    {"fn": overstatement_flag, "family": "adversarial",
     "fixtures": [(("Wheel stops can never designate parking", False), {"unsafe": True, "has_absolute": True}),
                  (("No case found makes hidden wheel stops enough", True), {"unsafe": False, "has_absolute": True}),
                  (("The lot was unstriped", False), {"unsafe": False, "has_absolute": False})]},
    {"fn": adversarial_complete, "family": "adversarial",
     "fixtures": [(({"opposing_point": "Murray", "best_response": "distinguish"},), {"complete": True, "missing": []}),
                  (({"opposing_point": "Murray"},), {"complete": False, "missing": ["best_response"]}),
                  (({},), {"complete": False, "missing": ["opposing_point", "best_response"]})]},
    {"fn": theory_shift, "family": "framing",
     "fixtures": [(("posted_restrictions", "obstruction"), {"shift": True}),
                  (("posted_restrictions", "posted_restrictions"), {"shift": False})]},
    {"fn": proof_gap_to_records, "family": "records",
     "fixtures": [(("no_visible_designation",), ["site_plans", "as_builts", "striping_records",
                                                 "wheel_stop_function_records", "sign_plans", "dated_photos"]),
                  (("unknown_gap",), [])]},
]


def build_cards() -> list[dict[str, Any]]:
    cards = []
    for spec in _PRIMITIVES:
        fn: Callable = spec["fn"]
        cid = canonical_id(RE_ID_PREFIX, fn.__name__, spec["family"])
        cards.append({"record_type": RE_RECORD_TYPE, "kind": "function", "card_id": cid, "primitive_id": cid,
                      "family": spec["family"], "impl_name": fn.__name__,
                      "title": f"{fn.__name__} — research evidence {spec['family']} primitive",
                      "blackbox": (inspect.getdoc(fn) or "").replace("\n", " ").strip(),
                      "executable_body": inspect.getsource(fn), "import_preamble": "",
                      "classification": "pure_primitive", "certification_target": True,
                      "domains": ["legal_research", "foia", "standards", "regulatory", "evidence_discipline"],
                      "n_fixtures": len(spec["fixtures"]), **BOUNDARY})
    return cards


def certify_all() -> dict[str, Any]:
    from scripts.saas_buildout_decomposer import certify_candidate  # noqa: PLC0415
    results = []
    for spec, card in zip(_PRIMITIVES, build_cards()):
        cert = certify_candidate(card, sample_inputs=[a for a, _e in spec["fixtures"]], fixtures=list(spec["fixtures"]))
        results.append({"name": card["impl_name"], "verdict": cert["verdict"]})
    n_ok = sum(1 for r in results if r["verdict"] == "oracle_correct")
    return {"n": len(results), "n_oracle_correct": n_ok, "all_certified": n_ok == len(results),
            "results": results, **BOUNDARY}


def emit() -> dict[str, Any]:
    out_dir = resource(PACK_DIR_REL)
    out_dir.mkdir(parents=True, exist_ok=True)
    cards = build_cards()
    with (out_dir / PACK_FILENAME).open("w", encoding="utf-8") as fh:
        for c in cards:
            fh.write(json.dumps(c, sort_keys=True) + "\n")
    return {"pack_path": str(out_dir / PACK_FILENAME), "n_cards": len(cards)}


def self_test() -> bool:
    """Mutation-gated: every fixture reproduces (the spec's §15 tests), AND every primitive certifies
    oracle_correct through the EXECUTED gate. Encodes: metadata (tier 4) is NOT quote-ready; an argument without a
    rebuttal is incomplete; an absolute claim without support is unsafe; a differing theory is a shift."""
    total = 0
    for spec in _PRIMITIVES:
        for args, expected in spec["fixtures"]:
            got = spec["fn"](*args)
            assert got == expected, f"{spec['fn'].__name__}{args!r}: {got!r} != {expected!r}"
            total += 1
    # the load-bearing evidence rules (spec §15):
    assert quote_gate(source_tier({"metadata_confirmed": True, "full_text": False}))["allowed"] is False, \
        "Test 1: a metadata-only source must NOT be quote-ready"
    assert adversarial_complete({"opposing_point": "x"})["complete"] is False, "Test 2: no rebuttal -> incomplete"
    assert overstatement_flag("It can never happen", False)["unsafe"] is True, "Test 3: absolute+unsupported unsafe"
    assert theory_shift("posted_restrictions", "obstruction")["shift"] is True, "Test 4: theory shift flagged"
    assert proof_gap_to_records("no_visible_designation"), "Test 5: proof gap -> records categories"
    cert = certify_all()
    assert cert["all_certified"], f"every research primitive must certify oracle_correct: {cert['results']}"
    fams = sorted({s["family"] for s in _PRIMITIVES})
    print(f"OK research_evidence_primitives self-test: {len(_PRIMITIVES)} pure evidence-discipline primitives "
          f"across {len(fams)} families {fams}, {total} oracle fixtures pass (== spec §15 tests), ALL certify "
          f"oracle_correct; source-status gate = candidate/truth boundary for evidence; serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Certified research/evidence-discipline primitives.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--certify", action="store_true")
    ap.add_argument("--emit", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.certify:
        print(json.dumps(certify_all(), indent=2))
        return
    if args.emit:
        print(json.dumps(emit(), indent=2))
        return
    self_test()


if __name__ == "__main__":
    main()
