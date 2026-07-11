#!/usr/bin/env python3
"""scripts.check_contextops_extractor_snippets — proof (CONTEXTOPS EXTRACTOR MODE): the nine deterministic
extractor primitives each read a value out of a source into a FactAssertion CANDIDATE tied to a REQUIRED
source_handle, and THE INVARIANT holds in code: an extractor output is ALWAYS a candidate, NEVER served or
canonical truth.

What it proves:
  * the CFPB-reference duration_parser reads "10 business days" → a candidate (value 10, unit business_days) with
    a source_handle and claim_status='candidate', produces='fact_assertion_candidate', promotion_eligible=False;
  * each of the nine primitives (regex/json_path/html_selector/csv_field/markdown_heading/duration_parser/
    date_parser/numeric_parser/source_hash_checker) produces a candidate, every one carrying its source_handle;
  * a candidate that DROPS its source_handle is REJECTED (MissingSourceHandleError);
  * minting anything but claim_status='candidate' / produces='fact_assertion_candidate' is REJECTED
    (CanonicalClaimError) — an extractor can never claim served/canonical truth;
  * candidate ids are content-addressed + deterministic (same inputs → same id, every run; no clock/RNG);
  * a no-match is an explicit NoMatchError, never a fabricated default value.

Deterministic, stdlib-only, offline. CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_contextops_extractor_snippets.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.contextops.extractor_snippets import (  # noqa: E402
    CANDIDATE_CLAIM_TYPE,
    CANDIDATE_STATUS,
    EXTRACTOR_TYPES,
    PRODUCES,
    CanonicalClaimError,
    FactAssertionCandidate,
    MissingSourceHandleError,
    NoMatchError,
    extract_csv_field,
    extract_date,
    extract_duration,
    extract_html_selector,
    extract_json_path,
    extract_markdown_heading,
    extract_numeric,
    extract_regex,
    extract_source_hash,
    run_extractor,
)

_NOW = 1_700_000_000  # injected epoch seconds (no wall-clock)
_HANDLE = "ctx://public/source/ecfr/12-CFR-1005.11#para.c.1.i"


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # ── 1) CFPB REFERENCE: duration_parser on "10 business days" → a candidate with value+unit+handle. ──
    cand = extract_duration("Reg E requires investigation within 10 business days of notice.",
                            fact_key="cfpb.error_resolution.investigation_deadline", source_handle=_HANDLE,
                            extracted_at=_NOW)
    check("duration_parser '10 business days' → value 10", cand.value == 10, str(cand.value))
    check("duration_parser '10 business days' → unit 'business_days'", cand.unit == "business_days", cand.unit)
    check("the extracted candidate carries its source_handle", cand.source_handle == _HANDLE)
    check("the candidate is a CANDIDATE (claim_status='candidate', never served/canonical)",
          cand.claim_status == CANDIDATE_STATUS == "candidate")
    check("the candidate's produces is pinned fact_assertion_candidate",
          cand.produces == PRODUCES == "fact_assertion_candidate")
    check("the candidate's claim_type is the factual shape atomic_fact (never an allegation)",
          cand.claim_type == CANDIDATE_CLAIM_TYPE == "atomic_fact")
    check("the candidate is NOT promotion_eligible (reconciliation/verification decide, not the extractor)",
          cand.promotion_eligible is False)
    check("the candidate serializes a candidate_id + the candidate shape",
          cand.to_dict().get("claim_status") == "candidate" and cand.to_dict().get("candidate_id", "").startswith("fac-"))

    # the FAQ side of the reference conflict: "30 days" → a candidate too (different value/unit). reconciliation,
    # NOT the extractor, decides which wins — the extractor only proposes.
    faq = extract_duration("Our FAQ says we resolve errors within 30 days.",
                           fact_key="cfpb.error_resolution.investigation_deadline",
                           source_handle="ctx://public/source/cfpb-faq/errors", extracted_at=_NOW)
    check("the FAQ '30 days' is ALSO only a candidate (the extractor proposes, never resolves)",
          faq.value == 30 and faq.unit == "days" and faq.claim_status == "candidate")
    check("the two candidates differ (a real conflict for reconciliation, not the extractor, to resolve)",
          (cand.value, cand.unit) != (faq.value, faq.unit))

    # ── 2) RED-TEAM: a candidate that DROPS its source_handle is rejected. ──
    dropped = False
    try:
        FactAssertionCandidate(fact_key="x", extractor_type="duration_parser", value=10, unit="business_days",
                               source_handle="", scope="global_public", extracted_at=_NOW)
    except MissingSourceHandleError:
        dropped = True
    check("RED-TEAM: a candidate without a source_handle is REJECTED (MissingSourceHandleError)", dropped)

    # ── 3) RED-TEAM: minting anything but claim_status='candidate' / produces='fact_assertion_candidate'. ──
    for field_name, bad in (("claim_status", "served"), ("claim_status", "canonical"),
                            ("produces", "canonical_fact"), ("produces", "served_fact"),
                            ("claim_type", "narrative_allegation"), ("promotion_eligible", True)):
        rejected = False
        kwargs = dict(fact_key="x", extractor_type="duration_parser", value=10, unit="business_days",
                      source_handle=_HANDLE, scope="global_public", extracted_at=_NOW)
        kwargs[field_name] = bad
        try:
            FactAssertionCandidate(**kwargs)
        except CanonicalClaimError:
            rejected = True
        check(f"RED-TEAM: {field_name}={bad!r} is REJECTED (never served/canonical truth)", rejected)

    # ── 4) every one of the nine primitives produces a candidate carrying a source_handle. ──
    payloads = {
        "regex": ("balance is $42.50 today", dict(pattern=r"\$(\d+\.\d+)", group=1)),
        "json_path": ('{"limits":{"deadline_days":10}}', dict(path="/limits/deadline_days")),
        "html_selector": ("<html><body><span>10 business days</span></body></html>", dict(tag="span")),
        "csv_field": ("field,deadline\nerror_resolution,10 business days\n", dict(column="deadline")),
        "markdown_heading": ("# Deadline\n10 business days\n", dict(heading="Deadline")),
        "duration_parser": ("within 10 business days", dict()),
        "date_parser": ("effective 2026-01-01 per the rule", dict()),
        "numeric_parser": ("the fee is 35 dollars", dict(unit="usd")),
        "source_hash_checker": ("the exact source bytes", dict(expected_hash="deadbeef")),
    }
    seen_types = set()
    for xtype, (payload, extra) in payloads.items():
        c = run_extractor(xtype, payload, fact_key=f"k.{xtype}", source_handle=_HANDLE, extracted_at=_NOW, **extra)
        seen_types.add(c.extractor_type)
        check(f"primitive {xtype} → a candidate carrying its source_handle",
              c.source_handle == _HANDLE and c.claim_status == "candidate" and c.produces == "fact_assertion_candidate",
              f"got status={c.claim_status} produces={c.produces}")
    check("all nine extractor primitives are exercised", seen_types == set(EXTRACTOR_TYPES),
          str(sorted(set(EXTRACTOR_TYPES) - seen_types)))

    # spot-check a few primitive VALUES are correct (not just well-shaped).
    check("regex captures group 1 ('42.50')",
          extract_regex("balance is $42.50", pattern=r"\$(\d+\.\d+)", group=1, fact_key="k",
                        source_handle=_HANDLE, extracted_at=_NOW).value == "42.50")
    check("json_path walks /limits/deadline_days → 10",
          extract_json_path('{"limits":{"deadline_days":10}}', path="/limits/deadline_days", fact_key="k",
                            source_handle=_HANDLE, extracted_at=_NOW).value == 10)
    check("html_selector reads the first <span> text",
          extract_html_selector("<span>10 business days</span>", tag="span", fact_key="k",
                                source_handle=_HANDLE, extracted_at=_NOW).value == "10 business days")
    check("csv_field reads the named column of row 0",
          extract_csv_field("field,deadline\nx,10 business days\n", column="deadline", fact_key="k",
                            source_handle=_HANDLE, extracted_at=_NOW).value == "10 business days")
    check("markdown_heading reads the body line under the heading",
          extract_markdown_heading("# Deadline\n10 business days\n", heading="Deadline", fact_key="k",
                                   source_handle=_HANDLE, extracted_at=_NOW).value == "10 business days")
    check("date_parser reads a valid ISO date",
          extract_date("effective 2026-01-01", fact_key="k", source_handle=_HANDLE, extracted_at=_NOW).value == "2026-01-01")
    check("numeric_parser reads the first number with its unit",
          extract_numeric("the fee is 35 dollars", unit="usd", fact_key="k", source_handle=_HANDLE,
                          extracted_at=_NOW).value == 35)
    # source_hash_checker: True on a match, False on a mismatch — a boolean candidate, never served truth.
    import hashlib as _hl
    h = _hl.sha256(b"exact bytes").hexdigest()
    match = extract_source_hash(b"exact bytes", expected_hash=h, fact_key="k", source_handle=_HANDLE, extracted_at=_NOW)
    nomatch = extract_source_hash(b"different bytes", expected_hash=h, fact_key="k", source_handle=_HANDLE, extracted_at=_NOW)
    check("source_hash_checker → True when content matches the expected source hash", match.value is True)
    check("source_hash_checker → False when content drifted (candidate, not an error)", nomatch.value is False)

    # ── 5) deterministic: same inputs → same candidate_id, every run; different inputs differ. ──
    a1 = extract_duration("10 business days", fact_key="k", source_handle=_HANDLE, extracted_at=_NOW)
    a2 = extract_duration("10 business days", fact_key="k", source_handle=_HANDLE, extracted_at=_NOW + 999)
    check("candidate_id is content-addressed + deterministic (same value/handle → same id; time excluded)",
          a1.candidate_id == a2.candidate_id and a1.candidate_id.startswith("fac-"))
    diff = extract_duration("30 days", fact_key="k", source_handle=_HANDLE, extracted_at=_NOW)
    check("a different extracted value → a different candidate_id", diff.candidate_id != a1.candidate_id)

    # ── 6) a no-match is an explicit error, never a fabricated value. ──
    nomatch_caught = False
    try:
        extract_duration("no durations here at all", fact_key="k", source_handle=_HANDLE, extracted_at=_NOW)
    except NoMatchError:
        nomatch_caught = True
    check("a no-match raises NoMatchError (never a faked default value)", nomatch_caught)

    ok = not fails
    print(
        f"\n{'PASS — check_contextops_extractor_snippets: the nine deterministic primitives each read a value into a FactAssertion CANDIDATE tied to a REQUIRED source_handle; the CFPB-reference duration_parser reads 10 business_days (the FAQ 30 days is ALSO only a candidate — the extractor proposes, reconciliation resolves); a dropped source_handle is REJECTED; minting served/canonical/promotion-eligible is REJECTED (extractor output is ALWAYS a candidate, never truth); candidate ids are content-addressed + deterministic; a no-match is an explicit error, never a fabricated value.' if ok else f'{len(fails)} FAILURES: {fails}'}"
    )
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: ContextOps deterministic extractor primitives (candidates only).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
