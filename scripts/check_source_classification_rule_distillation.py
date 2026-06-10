#!/usr/bin/env python3
"""scripts.check_source_classification_rule_distillation — APPLIED DISTILLATION: deterministic source classification.

The Determinism Factory applied to the repeated VERIFIED source-classification decision. A source's
(class, scope) is a decision the LLM/heuristics keep making and the validator keeps agreeing with; once that
decision is repeated on verified data it can become a deterministic rule. This proof DEFINES that rule and
proves it classifies a fixture correctly AND ABSTAINS (→ fallback) on an unknown source.

The mined deterministic rules (a ``source_authority_rule`` / classification decision table):

  * cfpb.gov / consumerfinance.gov OFFICIAL API           → class=official_api,        scope=global_public
  * eCFR (ecfr.gov)                                        → class=source_of_law,       scope=global_public
  * customer upload                                        → class=customer_upload,      scope=tenant_private
  * markdown vault (default)                               → class=markdown_vault,       scope=tenant_private
                                                            UNLESS frontmatter opts in (source_scope: global_public)
  * narrative / prose text                                 → class=narrative_allegation (NOT a fact, held out)
  * unknown / unrecognised origin                          → ABSTAIN → fallback (LLM/human review)

ASSERT-EQUIVALENCE (no second authority): the markdown-vault rows of the rule are checked AGAINST the
EXISTING ``MarkdownFolderAdapter`` (``src/baltor/adapters/source/markdown_folder.py``) on its own demo vault —
a note with ``source_scope: global_public`` + ``structured: true`` frontmatter yields global_public promotable
facts, a default note yields tenant_private, and prose yields ``narrative_allegation``. If the rule ever
disagrees with the adapter, this proof FAILS. The rule reproduces the adapter's governance — it never replaces it.

The rule's output is a CLASSIFICATION (routing/governance), not a truth claim — so a narrative is labelled
``narrative_allegation`` (held out), never promoted to a fact, exactly as the existing path does.

Determinism: ``--self-test``, offline, injected ``now``, hashlib ids, no RNG, in-memory fixture (no temp files).
PASS/FAIL lines, exit 0/1.

CLI: PYTHONPATH=. python3 scripts/check_source_classification_rule_distillation.py --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.adapters.source import markdown_folder as MD  # noqa: E402

_NOW = "2026-06-05T00:00:00Z"

# Canonical scope tokens (single source — reused from the existing adapter so they can NEVER drift).
GLOBAL_PUBLIC = MD._GLOBAL_PUBLIC      # "global_public"
TENANT_PRIVATE = MD._TENANT_PRIVATE    # "tenant_private"

# ABSTAIN sentinel — the rule does not guess; it routes to the fallback path.
ABSTAIN = ("__abstain__", "__abstain__")


def _hid(prefix: str, body: dict) -> str:
    return prefix + "-" + hashlib.sha256(json.dumps(body, sort_keys=True, default=str).encode()).hexdigest()[:16]


# ── the mined deterministic source-classification rule (a decision table; PURE, no model, no clock) ──
def classify_source(*, origin: str, content_kind: str = "structured", host: str = "",
                    frontmatter: dict | None = None) -> tuple[str, str]:
    """Classify a source into (class, scope). Returns ``ABSTAIN`` for an unknown origin → fallback.

    ``origin``        — the source origin keyword (official_api | source_of_law | customer_upload |
                        markdown_vault | narrative | …).
    ``content_kind``  — structured | narrative (prose is never a fact, regardless of origin).
    ``host``          — host/url hint (cfpb.gov, consumerfinance.gov, ecfr.gov, …).
    ``frontmatter``   — markdown-vault frontmatter (the opt-in lever for global_public).
    """
    fm = frontmatter or {}
    h = (host or "").lower()

    # narrative / prose is ALWAYS a held-out allegation, never a fact — independent of origin.
    if content_kind == "narrative" or origin == "narrative":
        return ("narrative_allegation", TENANT_PRIVATE)

    # official government APIs → official_api, global_public.
    if origin == "official_api" or any(d in h for d in ("cfpb.gov", "consumerfinance.gov")):
        return ("official_api", GLOBAL_PUBLIC)

    # eCFR (electronic Code of Federal Regulations) → source_of_law, global_public.
    if origin == "source_of_law" or "ecfr.gov" in h or origin == "ecfr":
        return ("source_of_law", GLOBAL_PUBLIC)

    # customer upload → tenant_private (never global).
    if origin == "customer_upload":
        return ("customer_upload", TENANT_PRIVATE)

    # markdown vault: default tenant_private UNLESS the note's frontmatter opts in to global_public.
    if origin == "markdown_vault":
        scope = GLOBAL_PUBLIC if fm.get(MD._SCOPE_KEY) == GLOBAL_PUBLIC else TENANT_PRIVATE
        return ("markdown_vault", scope)

    # unknown origin → ABSTAIN (do not guess) → fallback to LLM/human review.
    return ABSTAIN


@dataclass
class RuleCandidate:
    rule_id: str
    rule_type: str                       # source_authority_rule
    decision_table: list                 # the (matcher → (class, scope)) rows
    fallback_policy: dict
    asserts_equivalence_to: str = "src/baltor/adapters/source/markdown_folder.py"
    active: bool = False

    def to_dict(self) -> dict:
        return {"rule_id": self.rule_id, "rule_type": self.rule_type, "decision_table": self.decision_table,
                "fallback_policy": self.fallback_policy, "asserts_equivalence_to": self.asserts_equivalence_to,
                "active": self.active}


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # ── 1) the rule classifies each fixture source correctly ──────────────────────────────────────
    cases = [
        ("cfpb official API", {"origin": "official_api", "host": "https://api.cfpb.gov/complaints"},
         ("official_api", GLOBAL_PUBLIC)),
        ("consumerfinance.gov API by host alone", {"origin": "unknown", "host": "consumerfinance.gov/data"},
         ("official_api", GLOBAL_PUBLIC)),
        ("eCFR source of law", {"origin": "source_of_law", "host": "https://www.ecfr.gov/current/title-12"},
         ("source_of_law", GLOBAL_PUBLIC)),
        ("eCFR by host alone", {"origin": "unknown", "host": "ecfr.gov/cgi-bin"},
         ("source_of_law", GLOBAL_PUBLIC)),
        ("customer upload", {"origin": "customer_upload", "host": ""},
         ("customer_upload", TENANT_PRIVATE)),
        ("markdown vault default (no opt-in)", {"origin": "markdown_vault", "frontmatter": {"project": "Acme"}},
         ("markdown_vault", TENANT_PRIVATE)),
        ("markdown vault frontmatter opts in to global_public",
         {"origin": "markdown_vault", "frontmatter": {MD._SCOPE_KEY: GLOBAL_PUBLIC}},
         ("markdown_vault", GLOBAL_PUBLIC)),
        ("narrative prose is an allegation, not a fact",
         {"origin": "customer_upload", "content_kind": "narrative"},
         ("narrative_allegation", TENANT_PRIVATE)),
    ]
    for name, kw, expected in cases:
        got = classify_source(**kw)
        check(f"classify: {name}", got == expected, f"got {got}, expected {expected}")

    # ── 2) the rule ABSTAINS (→ fallback) on an unknown origin — it does NOT guess ────────────────
    unknown = classify_source(origin="some_new_connector_we_have_not_seen", host="example.com")
    check("classify: unknown origin ABSTAINS (routes to fallback, never guesses)", unknown == ABSTAIN, str(unknown))

    # ── 3) ASSERT-EQUIVALENCE to the EXISTING MarkdownFolderAdapter (no second authority) ─────────
    #     The adapter's demo vault: reg-e note opts in to global_public + structured; private note default.
    demo = MD._self_demo(now=1_000_000)
    by_note = {n["relpath"]: n for n in demo["notes"]}
    # the opted-in note → global_public per the adapter.
    rege_note = by_note["reg-e-error-resolution.md"]
    rule_rege = classify_source(origin="markdown_vault", frontmatter={MD._SCOPE_KEY: GLOBAL_PUBLIC})
    check("equivalence: opted-in markdown note → global_public matches the adapter",
          rege_note["scope"] == GLOBAL_PUBLIC and rule_rege[1] == GLOBAL_PUBLIC)
    # the default note → tenant_private per the adapter.
    priv_note = by_note["private-meeting-note.md"]
    rule_priv = classify_source(origin="markdown_vault", frontmatter={"project": "Acme"})
    check("equivalence: default markdown note → tenant_private matches the adapter",
          priv_note["scope"] == TENANT_PRIVATE and rule_priv[1] == TENANT_PRIVATE)
    # the adapter labels prose as narrative_allegation (NOT a fact) — the rule's narrative row agrees.
    prose_types = {a["artifact_type"] for a in demo["artifacts"] if a.get("claim_status") == "unverified_allegation"}
    rule_prose = classify_source(origin="markdown_vault", content_kind="narrative")
    check("equivalence: adapter labels prose narrative_allegation; the rule's narrative row agrees",
          "narrative_allegation" in prose_types and rule_prose[0] == "narrative_allegation")
    # the adapter NEVER promotes prose to a fact (held out) — the rule never returns a promotable class for narrative.
    promoted_prose = [a for a in demo["artifacts"]
                      if a.get("artifact_type") == "narrative_allegation" and a.get("promotion_eligible")]
    check("equivalence: no prose is promotion-eligible in the adapter (held out), matching the rule",
          promoted_prose == [] and rule_prose[0] != "atomic_fact")

    # ── 4) the rule output is a CLASSIFICATION (governance/scope), never a truth claim ────────────
    #     A narrative is never elevated to a global_public fact by the rule.
    check("a narrative is never classified global_public by the rule",
          classify_source(origin="markdown_vault", content_kind="narrative")[1] == TENANT_PRIVATE)

    # ── 5) build the M5 RuleCandidate (proposed, equivalence-asserting, with a fallback) ──────────
    table = [
        {"match": "host~cfpb.gov|consumerfinance.gov OR origin=official_api", "class": "official_api", "scope": GLOBAL_PUBLIC},
        {"match": "host~ecfr.gov OR origin=source_of_law", "class": "source_of_law", "scope": GLOBAL_PUBLIC},
        {"match": "origin=customer_upload", "class": "customer_upload", "scope": TENANT_PRIVATE},
        {"match": "origin=markdown_vault (default)", "class": "markdown_vault", "scope": TENANT_PRIVATE},
        {"match": "origin=markdown_vault AND frontmatter.source_scope=global_public", "class": "markdown_vault", "scope": GLOBAL_PUBLIC},
        {"match": "content_kind=narrative", "class": "narrative_allegation", "scope": TENANT_PRIVATE},
    ]
    rule = RuleCandidate(rule_id=_hid("rule", {"k": "source_classification", "table": table}),
                         rule_type="source_authority_rule", decision_table=table,
                         fallback_policy={"on_unknown_origin": "ABSTAIN → LLM/human review (do not guess)"})
    check("the source-classification rule is PROPOSED, not active", rule.active is False)
    check("the rule carries a fallback policy for unknown origins", "on_unknown_origin" in rule.fallback_policy)
    check("the rule asserts equivalence to the existing markdown adapter",
          rule.asserts_equivalence_to == "src/baltor/adapters/source/markdown_folder.py")

    # ── 6) DETERMINISM: a clean re-run reproduces every classification + the rule id ──────────────
    det = (all(classify_source(**kw) == classify_source(**kw) for _, kw, _ in cases)
           and _hid("rule", {"k": "source_classification", "table": table}) == rule.rule_id)
    check("deterministic: classifications + rule id are reproducible", det)

    ok = not fails
    print("\n" + ("PASS — check_source_classification_rule_distillation: the mined deterministic source-classification "
                  "rule labels cfpb.gov/consumerfinance.gov → official_api/global_public, eCFR → source_of_law/"
                  "global_public, customer upload → tenant_private, markdown vault → tenant_private unless frontmatter "
                  "opts in, narrative → narrative_allegation (held out, not a fact); it ABSTAINS (→ fallback) on an "
                  "unknown origin; and its markdown-vault rows are verified EQUIVALENT to the existing "
                  "MarkdownFolderAdapter — reproducing its governance, not replacing it."
                  if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Applied distillation: deterministic source classification (asserts equivalence).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
