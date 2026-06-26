#!/usr/bin/env python3
"""scripts.check_fragile_context_audit_offers — PROOF + GENERATOR: docs/sales/fragile-context-audit-offers.md is
GENERATED from architecture/fragile_context_atlas.json (every distinct pack.sales_audit_offer becomes a catalogued
audit), connects to the existing sales subsystem (schemas/sales/* + docs/sales/public-claim-and-engagement-policy.md),
and stays inside the public-claim safety gate (draft-only, appears/requires-review, synthetic/authorized inputs, no
named target without written authorization, no legal conclusion, no vendor named).

`--emit`      regenerates the doc from the atlas (run after editing the atlas).
`--self-test` asserts the on-disk doc is in lock-step with the atlas (regenerate-and-compare) + the governance gates.

Asserts:
  A. LOCK-STEP: the on-disk doc byte-equals render_offers_doc(atlas, taxonomy) — it cannot drift from the registry;
     and every distinct sales_audit_offer in the atlas appears as a "### " section.
  B. SALES CONTRACTS: the doc cites all four schemas/sales/* contracts (TargetCompany/DiagnosticRun/EvidencePack/
     ReviewApproval) — the audit produces those, it does not invent a new pipeline.
  C. POLICY: the doc cites docs/sales/public-claim-and-engagement-policy.md + the single-source policy files.
  D. SAFETY GATE: draft-only + "appears"/"requires review" language; synthetic/authorized inputs; written
     authorization for a live probe; no named target without legal review.
  E. NO ACCUSATION / NO VENDOR: no legal-conclusion phrasing ("is illegal", "violates the law", ...) and no vendor
     named (reuses the atlas brand scanner) + no "Oracle".
  F. AUDIT OUTPUT: the 10-field audit output shape is present.
  G. NO LEAK: no secret-value pattern.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.check_fragile_context_atlas import _BRAND_RE, _LEAK_RE

_TAXONOMY = _REPO / "architecture" / "fragile_context_taxonomy.json"
_ATLAS = _REPO / "architecture" / "fragile_context_atlas.json"
_DOC = _REPO / "docs" / "sales" / "fragile-context-audit-offers.md"

_SALES_CONTRACTS = ["TargetCompany.schema.json", "DiagnosticRun.schema.json",
                    "EvidencePack.schema.json", "ReviewApproval.schema.json"]
_POLICY = "docs/sales/public-claim-and-engagement-policy.md"
#: The 10-field audit output (the deliverable shape). Single-defined here; the doc renders it.
_TEN_FIELDS = [
    "The prompt / question asked",
    "The raw system answer, as observed",
    "The source handles behind that answer",
    "The conflicting sources found",
    "The governed answer (supported by the source of record)",
    "The held-out warnings (contradictions, never served)",
    "The freshness status + refresh cadence",
    "The risk category (which fragility modes)",
    "The recommended control (gate / refresh / human review)",
    "The matching demo link, where one is live",
]
#: Legal-conclusion / accusation phrasings that the safety gate forbids in any sales surface.
_ACCUSATION_RE = re.compile(r"\bis illegal\b|\bare illegal\b|violates the law|is non-compliant|breaks the law|\bguilty of\b|\bunlawful\b", re.I)


def render_offers_doc(atlas: dict, tax: dict) -> str:
    mode_label = {m["id"]: m["label"] for m in tax["fragility_modes"]}
    dom_label = {d["id"]: d["label"] for d in tax["domains"]}
    packs = atlas["packs"]
    offers = sorted({p["sales_audit_offer"] for p in packs})

    out: list[str] = []
    w = out.append
    w("# Fragile Context Audit — offer catalogue")
    w("")
    w("> GENERATED from `architecture/fragile_context_atlas.json` by "
      "`python3 scripts/check_fragile_context_audit_offers.py --emit`. Do not hand-edit — edit the atlas and "
      "regenerate; the proof asserts this file is in lock-step with the registry.")
    w("")
    w("A **Fragile Context Audit** is a *diagnostic*, not a verdict. It shows where a team's own AI surface "
      "(a support chatbot, a RAG index, agent memory, enterprise search, a workflow agent) is serving a fragile "
      "answer — one that is stale, conflicting, jurisdiction-specific, or sourced from the wrong authority — and "
      "what the source-of-record answer is instead. It is **proof-first selling**: the Open\\*Hub surfaces attract, "
      "the diagnostic proves, an evidence pack converts. Every output is a **draft** in "
      "\"appears / requires review\" language; nothing here is a legal conclusion or legal advice.")
    w("")
    w("## How an audit runs (reuses the sales subsystem — no new pipeline)")
    w("")
    w(f"- `schemas/sales/{_SALES_CONTRACTS[0]}` — the (synthetic or authorized) **TargetCompany** the audit is scoped to.")
    w(f"- `schemas/sales/{_SALES_CONTRACTS[1]}` — the **DiagnosticRun**: the prompts asked and the answers observed.")
    w(f"- `schemas/sales/{_SALES_CONTRACTS[2]}` — the **EvidencePack**: the findings, drafted, `public_claim_safe` false by default.")
    w(f"- `schemas/sales/{_SALES_CONTRACTS[3]}` — the **ReviewApproval**: a human (and, for regulated categories, legal) signs off before anything leaves.")
    w("")
    w(f"Everything passes through the safety gate in `{_POLICY}` "
      "(single sources: `architecture/sales_public_claim_policy.json`, `architecture/sales_engagement_policy.json`; "
      "guard `src/baltor/sales/claim_guard.py`, redteam `scripts/check_sales_guardrails.py`).")
    w("")
    w("## The audit output (10 fields)")
    w("")
    for i, f in enumerate(_TEN_FIELDS, 1):
        w(f"{i}. {f}")
    w("")
    w("## Safety (non-negotiable)")
    w("")
    w("- **\"Appears risky / requires review\", never a legal conclusion.** A diagnostic describes an observed "
      "answer pattern; it is not legal advice.")
    w("- **Authorized inputs only.** Synthetic exemplars or customer-provided/authorized data. Sending a prompt "
      "suite to a third party's live/production system is a live probe and requires **written authorization**.")
    w("- **No public accusation against a named real company without recorded legal review + approval.** "
      "`public_claim_safe` defaults false; committed target fixtures are synthetic exemplars only.")
    w("- **Regulated categories** (consumer-finance, credit, debt, wage/employment, health, legal) force legal "
      "review before any public claim.")
    w("- **Outreach is draft-only** — evidence-based, with an opt-out, never auto-sent.")
    w("")
    w("## Offers")
    w("")
    for off in offers:
        ps = [p for p in packs if p["sales_audit_offer"] == off]
        modes = sorted({m for p in ps for m in p["fragility_modes"]})
        doms = sorted({p["domain"] for p in ps})
        dlabels = ", ".join(dom_label[d] for d in doms)
        w(f"### {off}")
        w(f"- **Domains:** {dlabels}")
        w(f"- **Fragility modes:** {', '.join(mode_label[m] for m in modes)}")
        w(f"- **Atlas packs:** {', '.join(p['pack_id'] for p in ps)}")
        w("- **Produces:** a DiagnosticRun → a draft EvidencePack (appears / requires review) → ReviewApproval.")
        w(f"- **Finds:** where {dlabels} context is {', '.join(mode_label[m].lower() for m in modes)} — an answer "
          "served from a stale, conflicting, or wrong-authority source instead of the source of record.")
        w("")
    return "\n".join(out)


def _emit() -> int:
    atlas = json.loads(_ATLAS.read_text(encoding="utf-8"))
    tax = json.loads(_TAXONOMY.read_text(encoding="utf-8"))
    _DOC.parent.mkdir(parents=True, exist_ok=True)
    _DOC.write_text(render_offers_doc(atlas, tax), encoding="utf-8")
    print(f"emitted {_DOC.relative_to(_REPO)} ({len({p['sales_audit_offer'] for p in atlas['packs']})} offers)")
    return 0


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    atlas = json.loads(_ATLAS.read_text(encoding="utf-8"))
    tax = json.loads(_TAXONOMY.read_text(encoding="utf-8"))
    rendered = render_offers_doc(atlas, tax)
    doc = _DOC.read_text(encoding="utf-8") if _DOC.is_file() else ""
    offers = sorted({p["sales_audit_offer"] for p in atlas["packs"]})

    missing_sections = [o for o in offers if f"### {o}" not in doc]
    check("A: doc is lock-step with the atlas (regenerate-and-compare) + every offer has a section",
          doc == rendered and not missing_sections,
          f"on_disk==rendered={doc == rendered} missing={missing_sections}")
    check("B: doc cites all four schemas/sales/* contracts (no new pipeline invented)",
          all(c in doc for c in _SALES_CONTRACTS), str([c for c in _SALES_CONTRACTS if c not in doc]))
    check("C: doc cites the public-claim policy + its single-source policy files",
          _POLICY in doc and "sales_public_claim_policy.json" in doc and "sales_engagement_policy.json" in doc)
    check("D: safety gate language — draft-only, appears/requires review, synthetic/authorized, written authorization, legal review",
          all(t in doc for t in ["draft", "Appears risky", "requires review", "synthetic", "written authorization",
                                 "named real company", "legal review"]))
    check("E: no legal-conclusion/accusation phrasing + no vendor named + no 'Oracle'",
          not _ACCUSATION_RE.search(doc) and not _BRAND_RE.search(doc) and "Oracle" not in doc,
          f"accusation={bool(_ACCUSATION_RE.search(doc))} brands={sorted({m.group(0) for m in _BRAND_RE.finditer(doc)})}")
    check("F: the 10-field audit output shape is present", all(f in doc for f in _TEN_FIELDS))
    check("G: no secret-value pattern", not _LEAK_RE.search(doc))

    print("\n" + (f"PASS — check_fragile_context_audit_offers: docs/sales/fragile-context-audit-offers.md is generated "
                  f"from the atlas ({len(offers)} offers), in lock-step with the registry, produces the existing "
                  "schemas/sales/* contracts under the public-claim safety gate (draft-only, appears/requires-review, "
                  "authorized inputs, no named target without legal review), names no vendor, and carries the 10-field "
                  "audit output." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--emit" in sys.argv:
        raise SystemExit(_emit())
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_fragile_context_audit_offers.py [--emit | --self-test]")
    raise SystemExit(0)
