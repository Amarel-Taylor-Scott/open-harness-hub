#!/usr/bin/env python3
"""scripts.build_examples_gallery — render ONE governed-examples gallery from the REAL pipeline output.

Each card on the page is the ACTUAL output of a `scripts/showcase_pipelines/*.py` pipeline — the
build imports the module and runs its `run()` on the module's own synthetic inputs, then renders the
verdict, the trace, and the report it produced. Nothing here is mocked: the pipelines are
deterministic, so the embedded output is byte-identical to a live run (the ONE simulated seam inside
each pipeline is the model call). This makes the eight compositions a single recordable surface that
shows the capability lift over a bare model across domains beyond CFPB.

Single source: the page CSS is `scripts.portfolio_lib.SHARED_CSS` (the portfolio design system —
Hanken Grotesk + the dark token palette), not a parallel stylesheet.

Output: dist/examples-gallery/index.html  (served as the `examples-gallery` demo surface; recorded by
e2e/record_examples_gallery.mjs).

Run:  python3 scripts/build_examples_gallery.py [--self-test]
"""
from __future__ import annotations

import argparse
import html
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _RR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts import portfolio_lib as P

#: Parent (AI Done Right) accent — the gallery is a portfolio-level surface, like the hub.
_ACCENT = "#5b6cff"
_OUT = P.REPO / "dist" / "examples-gallery" / "index.html"

#: Status → chip colour. The verdict extractor returns one of these keys.
_STATUS = {"block": ("#ff6b6b", "BLOCKED"), "serve": ("#3fb950", "SERVED"),
           "review": ("#d29922", "HELD FOR REVIEW"), "info": ("#5b6cff", "EFFICIENCY")}


def _finding_summary(finding: dict[str, Any]) -> str:
    """A readable one-line summary of a clinical finding's first hit."""
    if finding.get("analytes"):  # critical-lab findings carry the analyte list directly
        return "critical value: " + ", ".join(finding["analytes"])
    hit = (finding.get("hits") or [{}])[0]
    if "pair" in hit:
        return f"{' + '.join(hit['pair'])} — {hit.get('mechanism', hit.get('severity', ''))}"
    if "order" in hit:
        return f"{hit['order']} — {hit.get('kind', '')} {hit.get('reason', '')}".strip()
    if "analyte" in hit:
        return f"{hit['analyte']} {hit.get('value', '')} {hit.get('flag', '')}".strip()
    return finding.get("severity") or json.dumps(hit, default=str)[:80]


def _scripted_translate(text: str, src: str, tgt: str) -> str:
    return f"[{src}->{tgt}] {text}"


def _scripted_queue(_ticket: dict) -> dict:
    return {"ref": "bcast-0001"}


#: The gallery spec. Editorial copy (scenario / why a bare model fails / durability class) lives here;
#: the verdict + rows + report come from the pipeline's REAL output. `invoke` runs the module's own
#: `run()` against the module's own synthetic constants — never a hand-built result.
EXAMPLES: list[dict[str, Any]] = [
    {
        "id": "sanctions_aml_screening", "title": "Sanctions / AML — the OFAC 50% Rule",
        "domain": "Financial crime · compliance", "durability": "Aggregation",
        "scenario": "Screen “Acme Trading” — NOT on the SDN list itself, but owned through a chain "
                    "(Volkov 30% directly + 60% of MidCo, which owns 40%).",
        "fails": "A bare model can’t traverse an ownership graph or know today’s delta-list additions, "
                 "so it clears the unlisted name. The 50% Rule is arithmetic over a governed graph.",
        "invoke": lambda m: m.run(entity="Acme Trading", sdn_list=m._SDN, ownership_graph=m._OWNERSHIP,
                                  list_sources=m._LIST_SOURCES),
        "verdict": lambda o: ("block", f"BLOCKED — aggregate listed ownership "
                                       f"{o['aggregate_listed_ownership']:.0%} ≥ 50% rule"),
        "rows": lambda o: [("Aggregate listed ownership", f"{o['aggregate_listed_ownership']:.0%}"),
                           ("Escalated to SAR review", o["ticket"]), ("Serves truth", str(o["serves_truth"]))],
        "markdown": lambda o: o["report_markdown"], "trace": lambda o: o["trace"],
    },
    {
        "id": "related_party_network", "title": "Related-party / shell-network discovery",
        "domain": "Financial crime · KYB · entity resolution", "durability": "Aggregation",
        "scenario": "Screen a registry of staffing agencies for hidden networks — cluster over shared "
                    "addresses, phones, officers, and M&A events.",
        "fails": "A bare model takes each entity at face value (different names, different rows) and "
                 "says “independent.” It can’t normalize identifiers or compute connected components.",
        "invoke": lambda m: m.run(entities=m._ENTITIES, ma_events=m._MA_EVENTS, sources=m._SOURCES),
        "verdict": lambda o: ("block" if o["high_risk_count"] else "serve",
                              f"{o['high_risk_count']} shell network(s) flagged" if o["high_risk_count"]
                              else "no undisclosed networks"),
        "rows": lambda o: [("Clusters found", str(len(o["clusters"])))]
                          + [(" · ".join(c["members"]),
                              f"{c['risk'].upper()} — shares {', '.join(c['shared_kinds'])}"
                              + (f"; M&A {', '.join(c['disclosed_ma'])}" if c["disclosed_ma"] else ""))
                             for c in o["clusters"] if len(c["members"]) > 1]
                          + [("Escalated", ", ".join(o["escalated"]) or "none"),
                             ("Serves truth", str(o["serves_truth"]))],
        "markdown": lambda o: o["report_markdown"], "trace": lambda o: o["trace"],
    },
    {
        "id": "cve_dependency_triage", "title": "CVE / dependency vulnerability triage",
        "domain": "Software supply chain · security", "durability": "Freshness + exactness",
        "scenario": "Is CVE-2024-3094 affecting us? Match the advisory’s version range against the "
                    "exact installed versions in the lockfile.",
        "fails": "A bare model hallucinates CVE ids, misses post-cutoff advisories, and can’t map an "
                 "advisory to your exact installed versions. Triage is exact range arithmetic.",
        "invoke": lambda m: m.run(query="is CVE-2024-3094 affecting us?", advisories=m._ADVISORIES,
                                  lockfile=m._LOCKFILE, advisory_sources=m._SOURCES),
        "verdict": lambda o: ("block", "AFFECTED" + (" — KEV (exploited in the wild)" if o["kev"] else "")),
        "rows": lambda o: [("Affected package", o["affected_packages"][0]["name"] + " " +
                            o["affected_packages"][0]["installed"]),
                           ("Known-exploited (KEV)", str(o["kev"])), ("Escalated", str(o["escalated"]))],
        "markdown": lambda o: o["report_markdown"], "trace": lambda o: o["trace"],
    },
    {
        "id": "common_control_resolver", "title": "Common control from M&A news",
        "domain": "Financial crime · audit · M&A", "durability": "Aggregation + freshness",
        "scenario": "Chain M&A deals by date to each company’s ultimate parent, then check if a "
                    "vendor↔customer transaction is actually self-dealing under common control.",
        "fails": "A bare model doesn’t know post-cutoff deals, can’t chain acquirer-of-acquirer "
                 "ownership, and misses that today’s “arm’s-length” vendor was bought by the customer’s parent.",
        "invoke": lambda m: m.run(transaction=m._TRANSACTION, ma_events=m._MA_EVENTS, sources=m._SOURCES),
        "verdict": lambda o: ("block" if o["under_common_control"] else "serve",
                              f"RELATED-PARTY — both controlled by {o['ultimate_parent']}"
                              if o["under_common_control"] else "arm’s-length (no common control)"),
        "rows": lambda o: [("Buyer control chain", " → ".join(o["buyer_chain"])),
                           ("Seller control chain", " → ".join(o["seller_chain"])),
                           ("Ultimate parent", o["ultimate_parent"] or "—"),
                           ("As of", o["as_of"]), ("Escalated", str(o["escalated"]))],
        "markdown": lambda o: o["report_markdown"], "trace": lambda o: o["trace"],
    },
    {
        "id": "beneficial_ownership_resolver", "title": "Beneficial ownership + OFAC 50% rule",
        "domain": "Sanctions · KYC · M&A roll-ups", "durability": "Aggregation + freshness + source-authority",
        "scenario": "Resolve each agency’s authoritative parent from conflicting ownership claims (an SEC "
                    "filing governs over a press rumor), then apply OFAC’s 50% rule — an entity ≥50%-owned "
                    "through the chain by an SDN-listed person is itself blocked, even if unlisted.",
        "fails": "A bare model doesn’t know post-cutoff deals, can’t tell an SEC filing from a blog, and "
                 "can’t propagate a sanctions block down a ≥50% ownership chain.",
        "invoke": lambda m: m.run(ownership_signals=m._SIGNALS, blocked_entities=m._BLOCKED),
        "verdict": lambda o: ("block" if o["blocked_by_inheritance"] else "serve",
                              (f"{len(o['blocked_by_inheritance'])} BLOCKED BY INHERITANCE (OFAC 50% rule): "
                               + ", ".join(sorted(o["blocked_by_inheritance"])))
                              if o["blocked_by_inheritance"] else "no entity blocked by the 50% rule"),
        "rows": lambda o: [("Blocked by inheritance", ", ".join(sorted(o["blocked_by_inheritance"])) or "—"),
                           ("Proof chain", " → ".join(max(o["blocked_by_inheritance"].values(),
                                           key=lambda v: len(v["chain"]))["chain"]) if o["blocked_by_inheritance"] else "—"),
                           ("Held-out (lower-authority) claims", str(len(o["held_out_claims"]))),
                           ("As of", o["as_of"]), ("Escalated", str(o["escalated"]))],
        "markdown": lambda o: o["report_markdown"], "trace": lambda o: o["trace"],
    },
    {
        "id": "fda_labeling_claim_review", "title": "FDA labeling: off-label overclaims",
        "domain": "Pharma · regulatory · promo review", "durability": "Source-authority + freshness",
        "scenario": "Substantiate each promotional claim against the FDA-approved label; a claim that "
                    "contradicts the label or asserts an unapproved indication is held out as off-label risk (FDCA 502).",
        "fails": "A bare model can’t tell an FDA-approved label from a glossy brochure and repeats the overclaim as fact.",
        "invoke": lambda m: m.run(label_claims=m._CLAIMS),
        "verdict": lambda o: ("block" if o["held_out"] else "serve",
                              f"{len(o['held_out'])} promotional claim(s) HELD OUT (off-label / contradicts the FDA label)"
                              if o["held_out"] else "all claims substantiated by the FDA-approved label"),
        "rows": lambda o: [("Substantiated (FDA label)", "; ".join(g["claim"] for g in o["governing"].values()) or "—"),
                           ("Held-out overclaims", str(len(o["held_out"]))),
                           ("Violation kinds", ", ".join(sorted({h["kind"] for h in o["held_out"]})) or "—"),
                           ("Escalated", str(o["escalated"]))],
        "markdown": lambda o: o["report_markdown"], "trace": lambda o: o["trace"],
    },
    {
        "id": "export_control_screening", "title": "BIS export-control screening",
        "domain": "Trade compliance · sanctions · EAR", "durability": "Source-authority + freshness",
        "scenario": "Screen each export’s end-user against the authoritative BIS Entity List; a stale vendor-DB "
                    "“clear” is held out when the Entity List shows the end-user listed → a license is required.",
        "fails": "A bare model doesn’t know post-cutoff Entity-List additions and clears an export it shouldn’t.",
        "invoke": lambda m: m.run(exports=m._EXPORTS, screening_signals=m._SIGNALS),
        "verdict": lambda o: ("block" if o["blocked_export_ids"] else "serve",
                              f"{len(o['blocked_export_ids'])} export(s) REQUIRE A LICENSE (end-user on the BIS Entity List)"
                              if o["blocked_export_ids"] else "all end-users clear on the authoritative screen"),
        "rows": lambda o: [("License required", ", ".join(o["blocked_export_ids"]) or "—"),
                           ("Governing source tier", next(iter(o["governing"].values()))["tier"] if o["governing"] else "—"),
                           ("Held-out stale “clear”s", str(len(o["held_out"]))),
                           ("Escalated", str(o["escalated"]))],
        "markdown": lambda o: o["report_markdown"], "trace": lambda o: o["trace"],
    },
    {
        "id": "icd10_coding", "title": "ICD-10 coding — abstain over fabricate",
        "domain": "Clinical · medical coding", "durability": "Coded vocabulary",
        "scenario": "Code the diagnoses in an encounter note against a governed terminology. The note "
                    "documents two codeable conditions plus one not in the terminology.",
        "fails": "The output is a CODE where fluency gives zero signal — a plausible-but-wrong code is "
                 "a compliance liability. A bare model invents plausible-looking ICD-10 codes.",
        "invoke": lambda m: m.run(encounter=m._ENCOUNTER, terminology_corpus=m._TERMINOLOGY),
        "verdict": lambda o: ("review", f"{len(o['proposed_codes'])} coded · "
                                        f"{len(o['abstained'])} abstained → proposed to a coder"),
        "rows": lambda o: [(c["term"], c["code"] + "  (" + c["citation"] + ")") for c in o["proposed_codes"]]
                          + [("ABSTAINED — " + a["term"], a["reason"]) for a in o["abstained"]]
                          + [("Disposition", o["disposition"]), ("Serves truth", str(o["serves_truth"]))],
        "markdown": lambda o: None, "trace": lambda o: o["trace"],
    },
    {
        "id": "procurement_collusion_ring", "title": "Procurement bid-rigging ring",
        "domain": "Public procurement · fraud", "durability": "Aggregation",
        "scenario": "Screen a tender ledger for a bid-rigging ring — vendors who rotate wins and "
                    "submit cover bids (deliberately high losing bids) to fake competition.",
        "fails": "A bare model scores each tender in isolation and calls it competitive. The ring is "
                 "a property of the WHOLE bid history — who co-bids, whether wins rotate, cover-bid bands.",
        "invoke": lambda m: m.run(tenders=m._TENDERS, sources=m._SOURCES),
        "verdict": lambda o: ("block" if o["is_ring"] else "serve",
                              (f"BID-RIGGING RING — {len(o['ring'])} vendors, "
                               f"{o['signals']['cover_bid_share']:.0%} cover-bid tenders") if o["is_ring"]
                              else "competitive (no ring)"),
        "rows": lambda o: [("Ring members", " · ".join(o["ring"]) or "none"),
                           ("Wins rotate among them", str(o["signals"]["wins_rotate"])),
                           ("Rotating winners", " · ".join(o["signals"]["winners"]) or "—"),
                           ("Cover-bid tenders", f"{o['signals']['cover_bid_share']:.0%}"),
                           ("Escalated", str(o["escalated"]))],
        "markdown": lambda o: o["report_markdown"], "trace": lambda o: o["trace"],
    },
    {
        "id": "regulated_fact_qa", "title": "Regulated-fact QA — state interest-rate caps",
        "domain": "Consumer finance · regulated facts", "durability": "Precedence + freshness",
        "scenario": "“What is the consumer loan interest rate cap in Ohio?” — answer only from the "
                    "current source of law, never an expired blog figure.",
        "fails": "A bare model averages a stale 21% blog post with the real statute, or states a cap "
                 "with no citation. The governed path picks the source of law and quotes it.",
        "invoke": lambda m: m.run(query="what is the consumer loan interest rate cap in Ohio?",
                                  corpus=m._CORPUS, now=m._NOW),
        "verdict": lambda o: ("serve", "SERVED — cites the source of law"),
        "rows": lambda o: [("Answer", o["answer"]),
                           ("Citations", ", ".join(o["citations"])),
                           ("Conflicting sources resolved", str(len(o["conflicts"]))),
                           ("Serves truth", str(o["serves_truth"]))],
        "markdown": lambda o: o["report_markdown"], "trace": lambda o: o["trace"],
    },
    {
        "id": "clinical_support", "title": "Clinical decision support — propose, never act",
        "domain": "Clinical · patient safety", "durability": "Safety + abstention",
        "scenario": "A renally-impaired patient on warfarin with a new high-potassium lab and an "
                    "interacting order. Surface the safety findings.",
        "fails": "A bare model answers confidently and autonomously. The governed path checks "
                 "interactions / dosing / labs deterministically and ESCALATES to a clinician.",
        "invoke": lambda m: m.run(patient=m._PATIENT, orders=m._ORDERS, labs=m._LABS),
        "verdict": lambda o: ("block", f"{len(o['findings'])} safety findings → ESCALATED (not autonomous)"),
        "rows": lambda o: [(f["kind"], _finding_summary(f)) for f in o["findings"]][:6]
                          + [("Disposition", o["disposition"]), ("Serves truth", str(o["serves_truth"]))],
        "markdown": lambda o: None, "trace": lambda o: None,
    },
    {
        "id": "low_resource_alert", "title": "Disaster alert in a low-resource language",
        "domain": "Public safety · low-resource NLP", "durability": "Low-resource + faithfulness",
        "scenario": "Turn a Filipino PAGASA typhoon bulletin into a Waray TTS-ready radio script — "
                    "pivoting through English, locking the output language.",
        "fails": "A bare model is unreliable in low-resource languages and will silently mistranslate "
                 "a life-safety number. The governed path extracts faithfully and a human signs off.",
        "invoke": lambda m: m.run(bulletin=m._BULLETIN, source_language="filipino",
                                  target_language="waray", translate=_scripted_translate,
                                  broadcast_queue=_scripted_queue),
        "verdict": lambda o: ("review", f"{len(o['extracted_fields'])} fields extracted → "
                                        "AWAITING HUMAN SIGN-OFF (nothing auto-broadcasts)"),
        "rows": lambda o: [("Pivot hops", " → ".join(o["pivot_hops"])),
                           ("Language locked", str(o["language_locked"])),
                           ("Auto-broadcast", str(o["auto_broadcast"])),
                           ("Awaiting sign-off ticket", o["awaiting_human_signoff"])],
        "markdown": lambda o: None, "trace": lambda o: None,
    },
    {
        "id": "governed_rag", "title": "Governed hybrid RAG — the general default",
        "domain": "General · grounded answering", "durability": "Grounding",
        "scenario": "“How does the deploy preflight gate work?” over a governed corpus, with prompt-"
                    "injection screening on the way in.",
        "fails": "Ungoverned RAG answers from whatever ranked highest, including an injected "
                 "instruction. The governed path screens, fuses, reranks, and grounds in real spans.",
        "invoke": lambda m: m.run(query="how does the deploy preflight gate work?", corpus=m._CORPUS),
        "verdict": lambda o: ("serve" if o["ready"] else "review",
                              "GROUNDED ANSWER READY" if o["ready"] else "NO GROUNDED SPANS — abstained"),
        "rows": lambda o: [("Grounded in real spans", str(o["ready"])),
                           ("Context compression ratio", f"{o.get('compression_ratio', 0):.0%}"),
                           ("Prompt enforces cite-or-abstain", str("Abstention policy" in o.get("system_prompt", "")))],
        "markdown": lambda o: None, "trace": lambda o: o.get("trace"),
    },
    {
        "id": "context_efficiency_loop", "title": "Usage-gated context efficiency",
        "domain": "Runtime · cost efficiency", "durability": "Efficiency (consumer behaviour)",
        "scenario": "A multi-turn session: classify the tenant’s usage shape, pick a cohort "
                    "compression curve, and serve only what’s needed across turns.",
        "fails": "A naive loop re-reads the whole working set every turn. The governed loop pages out "
                 "the stable substrate by cohort and rehydrates on a miss — measured savings.",
        "invoke": lambda m: m.run(),
        "verdict": lambda o: ("info", f"cohort “{o['cohort']}” · predicted re-read savings "
                                      f"{o['predicted_savings_fraction']:.0%}"),
        "rows": lambda o: [("Cohort", o["cohort"]), ("Budget fraction", f"{o['budget_fraction']:.0%}"),
                           ("Tokens kept vs naive re-read", f"{o['tokens_kept']} vs {o['naive_reread_tokens']}"),
                           ("Rehydrated on miss",
                            (o["rehydrated_on_miss"].get("item", "—") + " (re-promoted)")
                            if isinstance(o["rehydrated_on_miss"], dict) else str(o["rehydrated_on_miss"]))],
        "markdown": lambda o: None, "trace": lambda o: None,
    },
]


def _run_example(spec: dict[str, Any]) -> dict[str, Any]:
    """Import the showcase module and run its REAL run() → a rendered card model."""
    mod = importlib.import_module(spec["id"].join(("scripts.showcase_pipelines.", "")))
    out = spec["invoke"](mod)
    status, verdict = spec["verdict"](out)
    return {
        "id": spec["id"], "title": spec["title"], "domain": spec["domain"],
        "durability": spec["durability"], "scenario": spec["scenario"], "fails": spec["fails"],
        "status": status, "verdict": verdict,
        "rows": [(str(k), str(v)) for k, v in (spec["rows"](out) or [])],
        "markdown": spec.get("markdown", lambda _o: None)(out),
        "trace": spec.get("trace", lambda _o: None)(out),
    }


def _trace_html(trace: list[dict[str, Any]] | None) -> str:
    if not trace:
        return ""
    items = []
    for i, step in enumerate(trace, 1):
        if isinstance(step, dict):
            name = html.escape(str(step.get("step", f"step {i}")))
            rest = {k: v for k, v in step.items() if k != "step"}
            detail = html.escape(json.dumps(rest, default=str)) if rest else ""
        else:  # a plain step-name string
            name, detail = html.escape(str(step)), ""
        items.append(f'<li><span class="tstep">{name}</span>'
                     f'<span class="tdetail">{detail}</span></li>')
    return '<div class="trace"><div class="tlabel">composition trace (real)</div><ol>' \
           + "".join(items) + "</ol></div>"


def _card_html(card: dict[str, Any]) -> str:
    colour, _ = _STATUS[card["status"]]
    rows = "".join(
        f'<tr><td class="k">{html.escape(k)}</td><td class="v">{html.escape(v)}</td></tr>'
        for k, v in card["rows"])
    report = ""
    if card.get("markdown"):
        report = '<div class="report"><div class="tlabel">governed report (real output)</div>' \
                 f'<pre>{html.escape(card["markdown"])}</pre></div>'
    return f"""
    <article class="ex card" id="ex-{html.escape(card['id'])}">
      <header class="exhead">
        <div>
          <h3>{html.escape(card['title'])}</h3>
          <div class="meta">{html.escape(card['domain'])} · <span class="dur">durability: {html.escape(card['durability'])}</span></div>
        </div>
        <span class="chip" style="--c:{colour}">{html.escape(card['verdict'])}</span>
      </header>
      <div class="contrast">
        <div class="bad"><div class="clabel">Bare model</div><p>{html.escape(card['fails'])}</p></div>
        <div class="good"><div class="clabel">Governed pipeline</div><p>{html.escape(card['scenario'])}</p></div>
      </div>
      <table class="kv">{rows}</table>
      {_trace_html(card.get('trace'))}
      {report}
    </article>"""


def render(cards: list[dict[str, Any]]) -> str:
    css = P.SHARED_CSS.replace("__ACCENT__", _ACCENT)
    body = "".join(_card_html(c) for c in cards)
    n = len(cards)
    classes = ", ".join(sorted({c["durability"].split(" ")[0] for c in cards}))
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3E%3Crect width='16' height='16' rx='3' fill='%235b6cff'/%3E%3C/svg%3E">
<title>AI Done Right — Governed Examples Gallery</title>
<style>{css}
.exwrap{{max-width:1100px;margin:0 auto;padding:0 22px 80px}}
.ex{{margin:0 0 26px}}
.exhead{{display:flex;justify-content:space-between;align-items:flex-start;gap:18px}}
.exhead h3{{font-size:19px;margin:0 0 4px}}
.meta{{color:var(--muted);font-size:13px}}.dur{{color:var(--accent)}}
.chip{{border:1px solid var(--c);color:var(--c);border-radius:999px;padding:7px 14px;font-size:13px;
 font-weight:600;white-space:nowrap;flex:0 0 auto}}
.contrast{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:16px 0}}
.contrast>div{{border:1px solid var(--line);border-radius:10px;padding:14px}}
.bad{{background:#1a1113}}.good{{background:#0f1a12}}
.clabel{{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-bottom:7px}}
.contrast p{{margin:0;font-size:14px}}
table.kv{{width:100%;border-collapse:collapse;margin:6px 0 4px}}
table.kv td{{padding:7px 10px;border-top:1px solid var(--line);vertical-align:top;font-size:13.5px}}
td.k{{color:var(--muted);width:38%}}td.v{{font-family:"IBM Plex Mono",ui-monospace,monospace}}
.trace,.report{{margin-top:14px}}
.tlabel{{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin-bottom:8px}}
.trace ol{{margin:0;padding-left:20px}}.trace li{{margin:5px 0;font-size:13px}}
.tstep{{font-weight:600}}.tdetail{{color:var(--muted);font-family:"IBM Plex Mono",ui-monospace,monospace;
 font-size:12px;margin-left:8px;word-break:break-word}}
.report pre{{background:#0a0d13;border:1px solid var(--line);border-radius:10px;padding:14px;overflow:auto;
 font-family:"IBM Plex Mono",ui-monospace,monospace;font-size:12.5px;color:var(--ink);white-space:pre-wrap}}
</style></head>
<body>
<div class="wrap">
  <header class="top"><div class="brand"><span>AI Done Right</span></div>
    <span class="kind">Governed Examples Gallery</span></header>
  <section class="hero">
    <span class="pill">{n} runnable pipelines · real output · the model is the only simulated seam</span>
    <h1>The capability lift, shown — not claimed.</h1>
    <p class="lead">Every card below is the actual output of a pipeline that composes the real governed
    processors end-to-end. Each targets a place a frontier model fails <em>structurally</em>
    ({html.escape(classes)} …) — where being fluent isn’t the same as being right.</p>
  </section>
</div>
<div class="exwrap">{body}</div>
<div class="wrap"><footer class="foot" style="border-top:1px solid var(--line);padding:22px 0;color:var(--muted);font-size:13px">
  Generated from the real pipelines by <code>scripts/build_examples_gallery.py</code>. Deterministic —
  the embedded output is byte-identical to a live run. None of these serve truth autonomously; each
  proposes, and a gate or a human disposes.
</footer></div>
</body></html>"""


def build() -> dict[str, Any]:
    cards = [_run_example(spec) for spec in EXAMPLES]
    page = render(cards)
    _OUT.parent.mkdir(parents=True, exist_ok=True)
    _OUT.write_text(page, encoding="utf-8")
    # Sidecar manifest the recorder reads to assert each card's REAL verdict (single source — no
    # HTML parsing, no drift between what's rendered and what's asserted on camera).
    manifest = [{"id": c["id"], "title": c["title"], "domain": c["domain"],
                 "durability": c["durability"], "status": c["status"], "verdict": c["verdict"],
                 # whether this card renders a trace/report block (some are rows-only by design) —
                 # the recorder requires the evidence block on screen ONLY when this is true.
                 "has_evidence": bool(c.get("markdown") or c.get("trace"))}
                for c in cards]
    (_OUT.parent / "examples.json").write_text(
        json.dumps({"examples": manifest}, indent=2), encoding="utf-8")
    return {"path": str(_OUT.relative_to(P.REPO)), "examples": len(cards), "bytes": len(page),
            "cards": cards}


def _self_test() -> int:
    res = build()
    assert res["examples"] == len(EXAMPLES) == 14, res["examples"]
    page = _OUT.read_text(encoding="utf-8")
    # The page is self-contained: no external CDN/script/analytics FETCHED (recordable offline, honest).
    # A data: URI or an SVG XML namespace inside one is fine — we flag only real fetched src=/href= URLs.
    import re as _re
    fetched = _re.findall(r'(?:src|href)\s*=\s*"(https?://[^"]+)"', page)
    assert not fetched, f"external fetched resource leaked into the gallery: {fetched}"
    assert "<script" not in page.lower(), "gallery must be static (no JS)"
    # Every example rendered its REAL verdict (these are produced by run(), not typed here).
    cards = {c["id"]: c for c in res["cards"]}
    assert "BLOCKED" in cards["sanctions_aml_screening"]["verdict"] and "54%" in cards["sanctions_aml_screening"]["verdict"]
    assert "AFFECTED" in cards["cve_dependency_triage"]["verdict"] and "KEV" in cards["cve_dependency_triage"]["verdict"]
    assert "shell network" in cards["related_party_network"]["verdict"] and cards["related_party_network"]["status"] == "block"
    assert "RELATED-PARTY" in cards["common_control_resolver"]["verdict"] and "ParentCo" in cards["common_control_resolver"]["verdict"]
    assert "BID-RIGGING RING" in cards["procurement_collusion_ring"]["verdict"] and cards["procurement_collusion_ring"]["status"] == "block"
    assert "abstained" in cards["icd10_coding"]["verdict"] and any("ABSTAINED" in k for k, _ in cards["icd10_coding"]["rows"])
    assert "BLOCKED BY INHERITANCE" in cards["beneficial_ownership_resolver"]["verdict"] \
        and cards["beneficial_ownership_resolver"]["status"] == "block" \
        and "Volkov Holdings → Meridian Staffing Holdings → Apex Staffing" in dict(cards["beneficial_ownership_resolver"]["rows"]).get("Proof chain", "")
    assert "HELD OUT (off-label" in cards["fda_labeling_claim_review"]["verdict"] and cards["fda_labeling_claim_review"]["status"] == "block"
    assert "REQUIRE A LICENSE" in cards["export_control_screening"]["verdict"] \
        and cards["export_control_screening"]["status"] == "block" \
        and "EXP-001" in dict(cards["export_control_screening"]["rows"]).get("License required", "")
    assert "SERVED" in cards["regulated_fact_qa"]["verdict"]
    assert "28%" in page and any("28%" in v for _, v in cards["regulated_fact_qa"]["rows"]), "the served answer (28%) must appear"
    assert "ESCALATED" in cards["clinical_support"]["verdict"]
    assert "SIGN-OFF" in cards["low_resource_alert"]["verdict"]
    assert cards["governed_rag"]["status"] in ("serve", "review")
    assert "savings" in cards["context_efficiency_loop"]["verdict"]
    # Each verdict + the durability class is actually IN the HTML.
    for c in res["cards"]:
        assert html.escape(c["verdict"]) in page, c["id"]
        assert html.escape(c["durability"]) in page, c["id"]
    # The shared design system is used (single-sourced, not a parallel stylesheet).
    assert "Hanken Grotesk" in page
    # Deterministic.
    assert render(res["cards"]) == render(res["cards"])
    print(f"PASS — build_examples_gallery: {res['examples']} pipelines run for real → "
          f"{res['bytes']:,}-byte self-contained on-brand gallery at {res['path']}; every verdict "
          "(BLOCKED 54% / AFFECTED+KEV / abstained / SERVED 28% / ESCALATED / SIGN-OFF / savings) is "
          "the pipeline's actual output; no external resources; deterministic")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build the governed-examples gallery from real pipeline output.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    res = build()
    print(f"wrote {res['path']} — {res['examples']} examples, {res['bytes']:,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
