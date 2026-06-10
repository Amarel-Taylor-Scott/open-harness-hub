"""scripts.portfolio_lib — SINGLE SOURCE for the static portfolio launch websites (content, ports, CSS, renderer, and the
phrase/boundary tables the proofs assert). No-magic-values: build_portfolio_sites, serve_portfolio_sites, the
TryCloudflare launcher, and every check_portfolio_* proof import THIS module; nothing is hand-duplicated.

Boundary copy is consistent with docs/strategy/teleon-baltor-openharnesshub-portfolio.md (the portfolio thesis).
Render output uses ONLY local CSS (embedded) — no external CDN/JS/analytics/secrets. Each page carries delimited
<!--IDENTITY--> and <!--RELATIONSHIP--> zones so the brand-boundary proof can assert a site never appropriates
another brand's signature claim in its IDENTITY zone (cross-links/relationship mentions are allowed).
"""
from __future__ import annotations

import html
import json
from pathlib import Path


def _esc(t: str) -> str:
    """Escape body text WITHOUT touching quotes (apostrophes stay literal so required-phrase checks match).
    Safe because no dynamic string is placed inside a quote-delimited HTML attribute."""
    return html.escape(t, quote=False)


REPO = Path(__file__).resolve().parents[1]
DIST = REPO / "dist" / "portfolio-public"


def _fragile_atlas_section() -> tuple[str, str]:
    """OpenContextHub's fragile-context section, GENERATED from the atlas registry (the single source) so the public
    page can never drift from architecture/fragile_context_atlas.json. Names system TYPES only — never a vendor."""
    tax = json.loads((REPO / "architecture" / "fragile_context_taxonomy.json").read_text(encoding="utf-8"))
    atlas = json.loads((REPO / "architecture" / "fragile_context_atlas.json").read_text(encoding="utf-8"))
    n_domains = len({d["id"] for d in tax["domains"]})
    n_modes = len(tax["fragility_modes"])
    active = {p.get("demo_key"): p for p in atlas["packs"] if p.get("status") == "active"}

    def _ex(k: str) -> str:
        p = active[k]
        return f"{p['title']} serves “{p['served_answer']}” and holds out {p['held_out_examples'][0]['value']}"

    examples = "; ".join(_ex(k) for k in ("cfpb", "sanctions", "tariff"))
    body = ("Companies already feed fragile context into RAG, chatbots, agent memory, enterprise search, and workflow "
            "automations — context that is time-, authority-, jurisdiction-, or conflict-fragile. The fragile context "
            f"atlas maps {n_domains} domains across {n_modes} failure modes; every pack names its source authority, "
            "serves only the supported answer, and holds out the contradiction (never served). Examples: "
            f"{examples}. Reference packs are candidates, not served truth — Baltor governs what becomes verified, "
            "current, and served. Run a Fragile Context Audit to find the fragile surfaces in your own stack.")
    return ("Fragile context atlas", body)

#: portfolio hub + the static launch sites. Ports are the single source (9100 hub, contiguous site ports).
HUB_PORT = 9100
PORTS = {"aidoneright": 9101, "teleon.dev": 9102, "baltor": 9103, "openharnesshub": 9104,
         "opencontexthub": 9105, "openskillshub": 9106, "opentoolshub": 9107}
SITE_ORDER = ["aidoneright", "teleon.dev", "baltor", "opencontexthub", "openskillshub",
              "opentoolshub", "openharnesshub"]
LEGACY_SITE_REDIRECTS = {}

LOCAL_DEMO_DISCLAIMER = ("Local preview — not production hosting. Static portfolio site; the dashboards/demos it "
                         "describes are governed by their own products. This page stores no data and writes no truth.")

# ── signature claims: the phrases ONLY that brand may use as IDENTITY (others may reference them in relationship) ──
SIGNATURE = {
    "aidoneright": ["Infrastructure for governed, self-improving AI systems", "holding company", "portfolio strategy"],
    "teleon.dev": ["self-adaptive capabilities", "purpose-defined compute", "CapabilityTask", "intent-native, eval-gated, self-adaptive compute"],
    "baltor": ["governed context", "source-grounded", "reconciled"],
    "opencontexthub": ["open context artifacts", "context packs", "source-grounded context", "context schema"],
    "openskillshub": ["skill graph", "playbooks", "SKILL.md"],
    "opentoolshub": ["tool graph", "executable tools", "MCP servers"],
    "openharnesshub": ["open harnesses", "rubrics", "conformance packs"],
}

SITES: dict[str, dict] = {
    "aidoneright": {
        "title": "AI Done Right",
        "accent": "#2563eb",
        "kind": "Holding company · portfolio",
        "category": "Holding company · portfolio · research · brand architecture",
        "one_liner": "Infrastructure for governed, self-improving AI systems.",
        "audience": "Founders, investors, partners, and researchers evaluating the portfolio.",
        "problem": "Governed, self-improving AI needs more than one product — it needs a coordinated runtime, a "
                   "governed-context layer, and an open ecosystem, kept distinct yet aligned.",
        "use_case": "Understand how Teleon, Baltor, and OpenHarnessHub fit together and who owns what.",
        "what_it_is": ["A holding company coordinating a portfolio of governed-AI infrastructure.",
                       "The home of shared research, brand architecture, open standards, and IP coordination."],
        "what_it_is_not": ["Not a product you deploy.", "Not a runtime — it owns no runtime code.",
                           "Not an owner of customer context truth or skill activation."],
        "owns": ["Portfolio strategy", "Shared research", "Brand architecture", "Open standards coordination", "IP coordination"],
        "not_owns": ["Runtime truth", "Customer context truth", "Skill activation"],
        "diagram": "OpenHarnessHub → Teleon → Baltor   ·   AI Done Right coordinates portfolio · IP · research · specs",
        "relationship": "OpenHarnessHub supplies reusable capability parts. Teleon runs and evolves capabilities. "
                        "Baltor governs the context they produce. AI Done Right coordinates the portfolio.",
        "sections": [
            ("Portfolio thesis", "A model is only as good as the context and the runtime behind it. We build the "
             "governed, self-improving infrastructure underneath — coordinated across three focused companies."),
            ("Portfolio companies", "Teleon (the purpose-driven runtime), Baltor (governed context), and "
             "OpenHarnessHub (the open capability ecosystem)."),
        ],
        "cta_primary": ("Explore the portfolio", "#portfolio"),
        "cta_secondary": ("Read the portfolio thesis", "#portfolio"),
        "required_phrases": ["Infrastructure for governed, self-improving AI systems.", "Teleon", "Baltor",
                             "OpenHarnessHub", "portfolio", "OpenHarnessHub → Teleon → Baltor", "does not own"],
        "forbidden_identity": ["self-adaptive capabilities", "governed context", "open capability ecosystem"],
    },
    "teleon.dev": {
        "title": "Teleon",
        "accent": "#6d5ef0",
        "kind": "Teleon.dev · purpose-driven runtime",
        "category": "intent-native, eval-gated, self-adaptive compute",
        "one_liner": "Teleon turns functions, jobs, workers, and automations into self-adaptive capabilities.",
        "audience": "Platform-engineering, AI-infrastructure, DevOps/SRE, and automation teams.",
        "problem": "Cloud work is provisioned by implementation type (functions, jobs, workers), not by purpose — "
                   "so it can't evaluate a better/cheaper implementation or move runtimes safely on evidence.",
        "use_case": "Declare a CapabilityTask once; Teleon selects the runtime, tests candidate implementations "
                    "side-by-side, and promotes only with evidence.",
        "what_it_is": ["Intent-native, eval-gated, self-adaptive compute.",
                       "A purpose-defined runtime built around the CapabilityTask / PurposeTask object."],
        "what_it_is_not": ["Not a generic AI-agent deployment product.", "Not a replacement for Kubernetes.",
                           "Not a replacement for cloud functions.", "Not unbounded self-modifying code."],
        "owns": ["CapabilityTask / PurposeTask runtime", "Runtime selection", "Implementation candidates",
                 "Evidence ledger", "Promotion + policy gates", "Boundary approvals"],
        "not_owns": ["Governed context truth (that is Baltor)", "The open skill registry (that is OpenHarnessHub)"],
        "diagram": "purpose → contract → runtime selection → candidate → evidence → eval-gated promotion / rollback",
        "relationship": "Teleon runs and evolves capabilities. Baltor consumes Teleon through the "
                        "PurposeTaskProviderPort; Teleon returns evidence/candidate/result, never Baltor truth. "
                        "Teleon consumes templates, skills, and eval packs from OpenHarnessHub.",
        "sections": [
            ("Core design", "CapabilityTask stays stable. Implementation evolves. Runtime changes. Evidence "
             "decides. Policy gates promotion. Humans approve boundary expansion."),
            ("Runtime adapters", "local function · managed venv · local job · local worker pool · cloud function · "
             "Kubernetes job · queue worker · browser worker · GPU worker."),
            ("Dashboards", "Teleon Control Tower for staff; the Capability Assurance Portal for customers — one "
             "truth model, two governed views (the dashboard never owns truth)."),
            ("Quickstart & docs", "Engineer path: the CapabilityTask contract and the service-connection handshake "
             "are documented API-first (SERVICE-CONNECTIONS.md, agent-gateway MCP projection); quickstart = declare "
             "one CapabilityTask against the local runtime, read the receipt. Docs ship with the platform handoff."),
        ],
        "cta_primary": ("Define your first CapabilityTask", "#core"),
        "cta_secondary": ("See the runtime adapters", "#runtime"),
        "required_phrases": ["Teleon turns functions, jobs, workers, and automations into self-adaptive capabilities.",
                             "CapabilityTask", "PurposeTask", "CapabilityTask stays stable.", "Implementation evolves.",
                             "Runtime changes.", "Evidence decides.", "Policy gates promotion.",
                             "Humans approve boundary expansion.", "intent-native, eval-gated, self-adaptive compute",
                             "Teleon Control Tower", "Capability Assurance Portal", "Define your first CapabilityTask"],
        "forbidden_identity": ["governed context", "open capability ecosystem", "holding company"],
        "forbidden_anywhere": ["deploy agents in minutes", "Vercel for agents", "deploy AI agents in minutes"],
    },
    "baltor": {
        "title": "Baltor",
        "accent": "#0e7c86",
        "kind": "Baltor.ai · governed context",
        "category": "Governed context for AI systems",
        "one_liner": "Baltor turns messy, stale, conflicting, and unstructured context into safe, reconciled, "
                     "source-grounded AI context.",
        "audience": "Regulated-AI, compliance, risk, legal-operations, and enterprise-copilot teams.",
        "problem": "Agents fail on bad context — stale, conflicting, ungrounded — and have no receipt for what "
                   "they were given.",
        "use_case": "Serve a verified compliance answer with held-out conflicts and a portable receipt (the CFPB demo).",
        "what_it_is": ["Governed context for AI systems — reconciled, source-grounded, with receipts.",
                       "A pipeline from raw source systems to safe, served context."],
        "what_it_is_not": ["Not a generic compute runtime (that is Teleon).",
                           "Not a generic cloud-task orchestrator.", "Not an open skill registry (that is OpenHarnessHub)."],
        "owns": ["Source handles", "Context objects", "Atomic facts", "Reconciliation", "Verification",
                 "Safe consumption", "Receipts"],
        "not_owns": ["Generic compute runtime", "Generic cloud-task orchestration", "Generic open skill registry"],
        "diagram": "Intake → Decomposition → Atomic facts → Conflict detection → Reconciliation → "
                   "Fragility/freshness → Optimization → Consumption → Receipts",
        "relationship": "Baltor governs the context capabilities produce. Baltor uses Teleon through the "
                        "PurposeTaskProviderPort and decides what becomes verified, reconciled, served context. "
                        "Baltor uses governance/verification harnesses from OpenHarnessHub.",
        "sections": [
            ("Pipeline", "Intake → Decomposition → Atomic facts → Conflict detection → Reconciliation → "
             "Fragility/freshness → Optimization → Consumption → Receipts."),
            ("Proof (CFPB demo)", "Offline demo serves Reg E '10 business days,' holds out FAQ '30 days,' and "
             "preserves receipts/source handles."),
            ("Proven on live regulated data", "Live OFAC sanctions (SDN) ingestion: 200 entities pulled live, a "
             "would-be CUBA violation caught and held out, the verified claim served with its receipt "
             "(demo_context_engine_proof --live). The CFPB flow is browser-verified end-to-end: 15 assertions in "
             "real Chrome."),
            ("Built on Teleon", "Baltor uses Teleon through PurposeTaskProviderPort; Teleon returns "
             "evidence/candidate/result, and Baltor decides verified/reconciled/served context."),
        ],
        "cta_primary": ("Run the CFPB guided demo", "#proof"),
        "cta_secondary": ("See the governance pipeline", "#pipeline"),
        "required_phrases": ["Baltor turns messy, stale, conflicting, and unstructured context into safe, reconciled, source-grounded AI context.",
                             "Intake → Decomposition → Atomic facts → Conflict detection → Reconciliation → Fragility/freshness → Optimization → Consumption → Receipts",
                             "Offline demo serves Reg E '10 business days,' holds out FAQ '30 days,' and preserves receipts/source handles.",
                             "PurposeTaskProviderPort", "receipts", "source handles", "Run the CFPB guided demo"],
        "forbidden_identity": ["self-adaptive capabilities", "purpose-defined compute", "open capability ecosystem", "holding company"],
    },
    "opencontexthub": {
        "title": "OpenContextHub", "accent": "#2f8f6b", "kind": "OpenContextHub.io · open context registry",
        "category": "Open context registry · OSS-first",
        "one_liner": "Open context artifacts for AI systems.",
        "audience": "Builders and teams who need reusable, source-grounded context artifacts.",
        "problem": "Reusable context is scattered and ungoverned — there is no open registry of source-grounded "
                   "context packs, schemas, and source-handle maps with clear provenance and visibility.",
        "use_case": "Reuse a public CFPB Reg E context pack with its source-handle map and held-out example.",
        "what_it_is": ["An open registry of source-grounded context artifacts.",
                       "Context packs · schemas · source-handle maps · decomposition examples · native sidecars."],
        "what_it_is_not": ["Not a runtime.", "Not a truth authority.", "Not a private customer data lake.",
                           "Not a replacement for Baltor.", "Not a skill, tool, or harness registry."],
        "owns": ["Context artifacts", "Context packs", "Context schemas", "Source-handle maps",
                 "Decomposition maps", "Native sidecar examples", "Context fixtures"],
        "not_owns": ["Runtime execution", "Truth promotion", "Customer-private context by default"],
        "diagram": "publish → provenance → visibility policy → (reference) → consumed by Teleon · governed by Baltor",
        "relationship": "OpenContextHub publishes reference context artifacts. Baltor governs whether context "
                        "becomes verified, reconciled, current, and served. Teleon consumes context for PurposeTasks.",
        "sections": [
            ("Core rule", "Reference context is not served truth. Baltor governs context before consumption."),
            ("Artifact types", "ContextArtifact · SourceArtifact · ContextPack · ContextManifest · "
             "SourceHandleMap · DecompositionMap · ContextSchema · NativeSidecar · ContextFixture."),
            ("Visibility", "PUBLIC_REFERENCE · PUBLIC_METADATA · GATED_CONTEXT_PACK · CUSTOMER_PRIVATE · "
             "INTERNAL_ONLY · QUARANTINED — public surfaces carry reference/example artifacts only."),
            _fragile_atlas_section(),
        ],
        "cta_primary": ("Browse the context registry", "#artifact"),
        "cta_secondary": ("Run a Fragile Context Audit", "#fragile"),
        "required_phrases": ["Open context artifacts for AI systems.", "context pack", "source-handle",
                             "Reference context is not served truth.", "Baltor governs", "Browse the context registry",
                             "Run a Fragile Context Audit", "fragile context"],
        "forbidden_identity": ["self-adaptive capabilities", "skill graph", "tool graph", "open harnesses"],
    },
    "openskillshub": {
        "title": "OpenSkillsHub", "accent": "#2f7d8f", "kind": "OpenSkillsHub.io · open skill graph",
        "category": "Open skill graph · OSS-first",
        "one_liner": "The searchable skill graph for AI agents.",
        "audience": "Agent builders publishing and reusing playbooks and SKILL.md packages.",
        "problem": "Agent know-how is scattered across repos with no searchable, deduped, provenance-tracked graph.",
        "use_case": "Find a regulatory-deadline-normalization SKILL.md package with provenance and alternatives.",
        "what_it_is": ["A searchable skill graph: playbooks, workflows, and SKILL.md packages.",
                       "Agent instructions with provenance and duplicate detection."],
        "what_it_is_not": ["Not executable tools (that is OpenToolsHub).", "Not eval harnesses (that is OpenHarnessHub).",
                           "Not context truth.", "Not a runtime."],
        "owns": ["Skills", "Playbooks", "Workflows", "SKILL.md packages", "Agent instructions",
                 "Skill provenance / dedup"],
        "not_owns": ["Executable tools", "Eval harnesses", "Context truth"],
        "diagram": "publish skill → provenance / dedup → (candidate) → used by agents · run by Teleon",
        "relationship": "OpenSkillsHub teaches agents HOW. Skills USE tools from OpenToolsHub, are PROVEN by "
                        "OpenHarnessHub, draw context from OpenContextHub, and run via Teleon.",
        "sections": [
            ("Governance rule", "Discovery is not trust. Similarity is not equivalence. A skill is instructions, "
             "not execution; skill output is not truth."),
            ("SKILL.md packages", "Versioned playbooks/workflows with provenance, alternatives/fallbacks, and "
             "sandbox/eval status."),
            ("Feeds the portfolio", "Teleon consumes skills for PurposeTasks; skills invoke OpenToolsHub tools."),
        ],
        "cta_primary": ("Browse the skill graph", "#what"),
        "cta_secondary": ("Read the governance rule", "#governance"),
        "required_phrases": ["The searchable skill graph for AI agents.", "skill graph", "SKILL.md", "playbooks",
                             "Discovery is not trust.", "Browse the skill graph"],
        "forbidden_identity": ["executable tools", "open context artifacts", "open harnesses", "self-adaptive capabilities"],
    },
    "opentoolshub": {
        "title": "OpenToolsHub", "accent": "#8f6f2f", "kind": "OpenToolsHub.io · open tool graph",
        "category": "Open tool graph · OSS-first",
        "one_liner": "The executable tool graph for AI agents.",
        "audience": "Builders publishing and reusing executable tools, MCP servers, APIs, CLIs, and workers.",
        "problem": "Executable capabilities are scattered and ungated — no open graph with visibility, gating, "
                   "and sandbox metadata.",
        "use_case": "Find a sandboxed source-handle generator tool exposed as an MCP server.",
        "what_it_is": ["An executable tool graph: MCP servers, APIs, CLIs, adapters, and workers.",
                       "Tools with visibility/gating and sandbox metadata."],
        "what_it_is_not": ["Not skill reasoning instructions (that is OpenSkillsHub).", "Not context truth.",
                           "Not eval rubrics (that is OpenHarnessHub).", "Not a runtime."],
        "owns": ["Executable tools", "MCP servers", "APIs", "CLIs", "Adapters", "Workers",
                 "Visibility / gating metadata"],
        "not_owns": ["Skill reasoning instructions", "Context truth", "Eval rubrics"],
        "diagram": "publish tool → visibility / gating → sandbox → (candidate) → invoked by skills · orchestrated by Teleon",
        "relationship": "OpenToolsHub gives executable capabilities. Tools are invoked by OpenSkillsHub skills, "
                        "PROVEN by OpenHarnessHub, and orchestrated by Teleon.",
        "sections": [
            ("Governance rule", "Discovery is not trust. A tool is gated and sandboxed before use; tool output "
             "is not truth."),
            ("Tool kinds", "MCP servers · APIs · CLIs · adapters · workers — each with visibility and gating metadata."),
            ("Feeds the portfolio", "Skills invoke these tools; Teleon orchestrates them inside PurposeTasks."),
        ],
        "cta_primary": ("Browse the tool graph", "#tool"),
        "cta_secondary": ("Read the gating model", "#governance"),
        "required_phrases": ["The executable tool graph for AI agents.", "tool graph", "MCP servers",
                             "executable tools", "Discovery is not trust.", "Browse the tool graph"],
        "forbidden_identity": ["skill graph", "open context artifacts", "open harnesses", "self-adaptive capabilities"],
    },
    "openharnesshub": {
        "title": "OpenHarnessHub", "accent": "#d2542f", "kind": "OpenHarnessHub.io · open harness ecosystem",
        "category": "Open harness ecosystem · OSS-first",
        "one_liner": "Open harnesses, rubrics, templates, and evals for agentic infrastructure.",
        "audience": "Evaluators and builders who need reusable proof that capabilities work.",
        "problem": "There is no neutral, reusable place to PROVE that context, skills, and tools actually work.",
        "use_case": "Run a source-handle-preservation harness against a context pack and a candidate implementation.",
        "what_it_is": ["Reusable harnesses, rubrics, fixtures, templates, datasets, and conformance packs that PROVE capabilities work.",
                       "The proof layer of the open ecosystem."],
        "what_it_is_not": ["Not a skill registry (that is OpenSkillsHub).", "Not a tool registry (that is OpenToolsHub).",
                           "Not a context registry (that is OpenContextHub).", "Not a hosted runtime.", "Not a truth authority."],
        "owns": ["Harnesses", "Rubrics", "Eval packs", "Fixtures", "Templates", "Datasets",
                 "Conformance packs", "Benchmark packs"],
        "not_owns": ["Skill registry", "Tool execution", "Context truth"],
        "diagram": "harness / rubric → run vs capability → conformance result → consumed by Teleon",
        "relationship": "OpenHarnessHub PROVES capabilities work. It evaluates context (OpenContextHub), skills "
                        "(OpenSkillsHub), and tools (OpenToolsHub); Teleon uses its evals to gate promotion.",
        "sections": [
            ("Governance rule", "Discovery is not trust. A passing eval is evidence, not a guarantee; missing "
             "coverage blocks promotion."),
            ("Contains", "harnesses · rubrics · eval packs · fixtures · templates · datasets · conformance packs."),
            ("Preferred site", "OpenHarnessHub.io replaces OpenHarnessHub.org as the preferred public site."),
            ("Publish", "Publishers submit components through the publish flow; every submission lands in the "
             "review queue with provenance attached — candidate is not active, and nothing goes live "
             "automatically. Never pay-to-play: promotion is evidence-gated, not purchased."),
        ],
        "cta_primary": ("Browse the harness ecosystem", "#contains"),
        "cta_secondary": ("Read the governance rule", "#governance"),
        "required_phrases": ["Open harnesses, rubrics, templates, and evals for agentic infrastructure.",
                             "harnesses", "rubrics", "conformance", "Discovery is not trust.",
                             "OpenHarnessHub.io replaces OpenHarnessHub.org", "Browse the harness ecosystem"],
        "forbidden_identity": ["skill graph", "tool graph", "open context artifacts", "self-adaptive capabilities", "governed context"],
        "forbidden_anywhere": ["hosted runtime we operate", "fully managed SaaS runtime"],
    },
}

# system font stack — no external fonts/CDN.
SHARED_CSS = """
:root{--bg:#0d1117;--panel:#161b22;--ink:#e6edf3;--muted:#9aa7b4;--line:#283039;--accent:__ACCENT__}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:linear-gradient(180deg,#0b0e14,#0d1117 40%);color:var(--ink);
 font-family:"Hanken Grotesk","Inter",-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;line-height:1.55}
.wrap{max-width:1040px;margin:0 auto;padding:0 24px}
header.top{border-bottom:1px solid var(--line);padding:18px 0;position:sticky;top:0;backdrop-filter:blur(8px);
 background:rgba(13,17,23,.72);z-index:5}
.brand{display:flex;align-items:center;gap:12px;font-weight:700;letter-spacing:.2px}
.dot{width:14px;height:14px;border-radius:4px;background:var(--accent);box-shadow:0 0 18px var(--accent)}
.kind{color:var(--muted);font-weight:500;font-size:13px;margin-left:auto}
.hero{padding:72px 0 36px}
.hero h1{font-size:clamp(30px,5vw,52px);line-height:1.08;margin:0 0 16px;letter-spacing:-.5px}
.hero p.lead{font-size:clamp(17px,2.4vw,22px);color:var(--ink);max-width:760px;margin:0 0 28px}
.pill{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:6px 14px;color:var(--muted);
 font-size:13px;margin-bottom:22px}
.cta{display:inline-flex;gap:10px;flex-wrap:wrap}
.btn{display:inline-block;padding:12px 20px;border-radius:10px;text-decoration:none;font-weight:600;font-size:15px}
.btn.primary{background:var(--accent);color:#06121f}
.btn.secondary{border:1px solid var(--line);color:var(--ink)}
section{padding:30px 0;border-top:1px solid var(--line)}
h2{font-size:22px;margin:0 0 14px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:22px}
@media(max-width:720px){.grid2{grid-template-columns:1fr}}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:20px}
.card h3{margin:0 0 10px;font-size:16px}
ul.clean{list-style:none;padding:0;margin:0}ul.clean li{padding:7px 0 7px 22px;position:relative;color:var(--ink)}
ul.clean li::before{content:"";position:absolute;left:0;top:14px;width:8px;height:8px;border-radius:2px;background:var(--accent)}
ul.no li::before{background:#6b7480}
.diagram{background:#0a0d13;border:1px dashed var(--line);border-radius:12px;padding:18px;color:var(--muted);
 font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:14px;overflow-x:auto}
.rel{color:var(--muted)}
.portfolio{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
@media(max-width:720px){.portfolio{grid-template-columns:1fr 1fr}}
.portfolio a{display:block;border:1px solid var(--line);border-radius:12px;padding:14px;text-decoration:none;color:var(--ink)}
.portfolio a:hover{border-color:var(--accent)}
.portfolio small{color:var(--muted)}
.disclaimer{color:var(--muted);font-size:13px;border:1px solid var(--line);border-radius:10px;padding:12px 14px;background:#0a0d13}
.preview{color:var(--muted);font-size:13px;margin-top:10px}
footer{border-top:1px solid var(--line);padding:26px 0 60px;color:var(--muted);font-size:14px}
footer a{color:var(--ink)}
"""


def _li(items: list[str], cls: str = "clean") -> str:
    return f'<ul class="{cls}">' + "".join(f"<li>{_esc(x)}</li>" for x in items) + "</ul>"


def _cross_links(current_id: str) -> str:
    cards = []
    for sid in SITE_ORDER:
        s = SITES[sid]
        here = " (you are here)" if sid == current_id else ""
        cards.append(f'<a href="../{sid}/index.html"><strong>{_esc(s["title"])}</strong>{here}<br>'
                     f'<small>{_esc(s["kind"])}</small></a>')
    return '<div class="portfolio">' + "".join(cards) + "</div>"


def render_site(site_id: str) -> str:
    s = SITES[site_id]
    cta1_label, cta1_href = s["cta_primary"]
    cta2_label, cta2_href = s["cta_secondary"]
    sections_html = "".join(
        f'<section id="{_esc(h.lower().split(" ")[0])}"><h2>{_esc(h)}</h2>'
        f'<p>{_esc(b)}</p></section>' for h, b in s["sections"])
    css = SHARED_CSS.replace("__ACCENT__", s["accent"])
    footer_links = " · ".join(f'<a href="../{t}/index.html">{_esc(SITES[t]["title"])}</a>' for t in SITE_ORDER)
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<link rel="icon" href="data:,">
<title>{_esc(s['title'])} — {_esc(s['one_liner'])}</title>
<style>{css}</style>
</head><body>
<header class="top"><div class="wrap brand"><span class="dot"></span>{_esc(s['title'])}
<span class="kind">{_esc(s['kind'])}</span></div></header>
<main class="wrap">
<!--IDENTITY-->
<div class="hero">
  <span class="pill">{_esc(s['kind'])}</span>
  <h1>{_esc(s['one_liner'])}</h1>
  <p class="rel" style="margin:-6px 0 14px;font-size:15px">Category: {_esc(s.get('category', s['kind']))}</p>
  <p class="lead">{_esc(s['problem'])}</p>
  <div class="cta">
    <a class="btn primary" href="{_esc(cta1_href)}">{_esc(cta1_label)}</a>
    <a class="btn secondary" href="{_esc(cta2_href)}">{_esc(cta2_label)}</a>
  </div>
  <p class="preview">Preview build — temporary URL, not production hosting.</p>
</div>
<section id="what">
  <h2>What it is &amp; what it owns</h2>
  <div class="grid2">
    <div class="card"><h3>What it is</h3>{_li(s['what_it_is'])}</div>
    <div class="card"><h3>What it owns</h3>{_li(s['owns'])}</div>
  </div>
</section>
<!--/IDENTITY-->
<section id="boundary">
  <h2>What it is not &amp; what it does not own</h2>
  <div class="grid2">
    <div class="card"><h3>What it is not</h3>{_li(s['what_it_is_not'], 'clean no')}</div>
    <div class="card"><h3>What it does not own</h3>{_li(s['not_owns'], 'clean no')}</div>
  </div>
</section>
<section id="audience"><h2>Who it is for</h2><p>{_esc(s['audience'])}</p>
  <p class="rel">Use case: {_esc(s['use_case'])}</p></section>
{sections_html}
<!--RELATIONSHIP-->
<section id="portfolio"><h2>How it fits the portfolio</h2>
  <div class="diagram">{_esc(s['diagram'])}</div>
  <p class="rel" style="margin-top:14px">{_esc(s['relationship'])}</p>
  {_cross_links(site_id)}
</section>
<!--/RELATIONSHIP-->
<section id="preview"><div class="disclaimer">{_esc(LOCAL_DEMO_DISCLAIMER)}</div></section>
</main>
<footer><div class="wrap">Part of the AI Done Right portfolio: {footer_links}.</div></footer>
</body></html>
"""


def render_hub() -> str:
    css = SHARED_CSS.replace("__ACCENT__", "#5b6cff")
    cards = "".join(
        f'<a href="../{sid}/index.html"><strong>{_esc(SITES[sid]["title"])}</strong><br>'
        f'<small>{_esc(SITES[sid]["one_liner"])}</small></a>' for sid in SITE_ORDER)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex">
<link rel="icon" href="data:,">
<title>AI Done Right — Portfolio Hub</title><style>{css}</style></head><body>
<header class="top"><div class="wrap brand"><span class="dot"></span>AI Done Right
<span class="kind">portfolio hub</span></div></header>
<main class="wrap"><div class="hero"><h1>Infrastructure for governed, self-improving AI systems.</h1>
<p class="lead">OpenHarnessHub → Teleon → Baltor. One coordinated portfolio.</p></div>
<section><h2>The static launch sites</h2><div class="portfolio">{cards}</div></section>
<section id="preview"><div class="disclaimer">{_esc(LOCAL_DEMO_DISCLAIMER)}</div></section>
</main><footer><div class="wrap">AI Done Right portfolio hub · local preview.</div></footer></body></html>
"""


def dist_path(site_id: str) -> Path:
    return DIST / site_id / "index.html"


def identity_zone(htmltext: str) -> str:
    a = htmltext.find("<!--IDENTITY-->")
    b = htmltext.find("<!--/IDENTITY-->")
    return htmltext[a:b] if (a >= 0 and b > a) else ""


__all__ = ["SITES", "SITE_ORDER", "PORTS", "HUB_PORT", "SIGNATURE", "LEGACY_SITE_REDIRECTS", "SHARED_CSS", "LOCAL_DEMO_DISCLAIMER",
           "render_site", "render_hub", "dist_path", "identity_zone", "DIST", "REPO"]
