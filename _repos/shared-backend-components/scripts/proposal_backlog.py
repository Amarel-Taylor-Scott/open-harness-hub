#!/usr/bin/env python3
"""scripts.proposal_backlog — turn loop findings into structured, PRIORITIZED proposals when auto-applying is uncomfortable.

The improvement loop must NOT auto-apply everything. When a change is owner-gated (brand/pricing/structure/strategy),
high-blast-radius, low-reversibility, or low-confidence, the loop is "uncomfortable" implementing it directly — so it
files a PROPOSAL / PLAN / OPPORTUNITY / POTENTIAL / RISK here, scored + prioritized for the owner/agent to pick up.
Trivial + reversible fixes still auto-apply (the autofix flywheel); everything riskier becomes a ranked backlog item
with a clear rationale + next steps. DEVELOPMENT plane (data/dev-intel/); serves_truth=false (candidates until acted on).

  --self-test   offline: comfort gate, scoring, dedup, prioritized backlog render
  --distill [N] turn the last N loop findings into proposals (dedup) + refresh the prioritized backlog
  --prioritize  re-rank + write data/dev-intel/proposals-prioritized.md
CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/proposal_backlog.py --distill 40
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
LEDGER = _resource("data") / "dev-intel" / "proposals.jsonl"
PRIORITIZED = _resource("data") / "dev-intel" / "proposals-prioritized.md"
FINDINGS = _resource("data") / "dev-intel" / "findings.jsonl"

KINDS = ("opportunity", "proposal", "plan", "potential", "risk")
COMFORT = ("auto", "propose", "owner_gated")   # auto = safe to apply directly; propose = queue; owner_gated = needs owner

#: ACTION phrases (not bare mentions) that mean a brand/pricing/structure CHANGE -> owner_gated, never auto.
#: (Bare words like "pricing"/"strategy" appear in normal reviews, so we require an action phrase to avoid false flags.)
_OWNER_GATED = ("rebrand", "rename the", "rename teleon", "rename baltor", "change the pric", "pricing tier",
                "pricing model", "trademark", "the brand name", "new brand", "monetization model", "new domain",
                "restructure the portfolio", "change the name")
_HIGH_RISK = ("delete", "migrate", "migration", "breaking", "schema change", "rewrite", "refactor everything",
              "drop ", "remove the", "split the monolith", "restructure", "untrack", "overwrite")
_TRIVIAL = ("typo", "comment", "docstring", "add a test", "add tests", "rename a local", "wording", "clarify the doc",
            "archive ", "dead code", "unused import")


@dataclass(frozen=True)
class Proposal:
    title: str
    kind: str = "opportunity"          # one of KINDS
    source: str = "loop"               # loop | model | research | agent
    value: int = 3                     # 1..5 expected impact
    effort: int = 3                    # 1..5 (higher = more work)
    risk: int = 3                      # 1..5 (higher = riskier / bigger blast radius)
    reversibility: int = 3             # 1..5 (higher = easier to undo)
    confidence: float = 0.6            # 0..1 (verified? corroborated?)
    comfort: str = "propose"           # auto | propose | owner_gated
    rationale: str = ""
    next_steps: str = ""
    refs: tuple = ()
    status: str = "proposed"           # proposed | prioritized | accepted | rejected | done
    serves_truth: bool = False

    def pid(self) -> str:
        return "prop_" + hashlib.sha256(self.title.encode()).hexdigest()[:16]

    def score(self) -> float:
        """Priority: higher = do sooner. Value + confidence + reversibility lift it; effort + risk lower it."""
        return round((self.value * self.confidence * (1 + self.reversibility / 5)) / (self.effort * self.risk), 4)


def assess_comfort(text: str) -> dict:
    """Decide how comfortable the loop is applying this directly, from the finding text. Returns
    {comfort, kind, risk, reversibility, confidence, reasons}."""
    t = (text or "").lower()
    reasons = []
    comfort, risk, rev, conf, kind = "propose", 3, 3, 0.6, "opportunity"
    if any(k in t for k in _OWNER_GATED):
        comfort, kind = "owner_gated", "proposal"
        reasons.append("touches owner-gated surface (brand/pricing/structure/strategy)")
    elif any(k in t for k in _HIGH_RISK):
        comfort, risk, rev = "propose", 4, 2
        reasons.append("high blast-radius / low reversibility")
    elif any(k in t for k in _TRIVIAL):
        comfort, risk, rev, conf, kind = "auto", 1, 5, 0.8, "opportunity"
        reasons.append("trivial + reversible")
    else:
        reasons.append("default: propose for review (not clearly trivial)")
    if "plan" in t or "roadmap" in t or "multi-step" in t:
        kind = "plan"
    if "risk" in t or "denial" in t or "brutal truth" in t:
        kind = "risk"
    return {"comfort": comfort, "kind": kind, "risk": risk, "reversibility": rev, "confidence": conf, "reasons": reasons}


#: Truly OWNER-ONLY items the loop CANNOT complete even via best practices — an EXTERNAL action, a fact only the owner
#: has, or real spend/legal. Everything ELSE (incl. design / structure / strategy / pricing / naming) the autonomous
#: loop NOW resolves by best practices + guiding principles (owner standing authorization 2026-06-21), recording the
#: warrant. Irreducible items still get a best-effort DRAFT (template + recommendation) + a clear flag — never a no-op.
_IRREDUCIBLE = ("sign a design partner", "design partner", "paid pilot", "send ", "email ", "outreach", "publish to",
                "raise size", "wire ", "payment", "billing", "trademark", "legal filing", "incorporat",
                "founder's personal", "your credentials", "real customer", "real money", "go live with billing")


def is_irreducible(text: str) -> bool:
    """True ONLY for items needing an external action / a fact only the owner has / real spend or legal — the loop
    drafts the best-effort artifact but cannot complete these. Everything else is best-practice-resolvable now."""
    return any(k in (text or "").lower() for k in _IRREDUCIBLE)


def propose(p: Proposal) -> dict:
    """Append a proposal (idempotent by title-hash). Returns the record."""
    rec = asdict(p)
    rec["pid"] = p.pid()
    rec["score"] = p.score()
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    if LEDGER.exists() and any(json.loads(ln).get("pid") == rec["pid"] for ln in LEDGER.read_text(encoding="utf-8").splitlines() if ln.strip()):
        return rec
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec


def load() -> list[dict]:
    if not LEDGER.exists():
        return []
    return [json.loads(ln) for ln in LEDGER.read_text(encoding="utf-8").splitlines() if ln.strip()]


def distill_findings(limit: int = 40) -> int:
    """Turn the last ``limit`` loop findings into proposals (comfort-assessed, deduped). Returns # new proposals."""
    if not FINDINGS.exists():
        return 0
    rows = [json.loads(ln) for ln in FINDINGS.read_text(encoding="utf-8").splitlines() if ln.strip()][-limit:]
    n = 0
    for r in rows:
        opp = (r.get("opportunities") or "").strip()
        if not opp or r.get("error"):
            continue
        first = next((ln.strip("# *-").strip() for ln in opp.splitlines() if len(ln.strip()) > 12), "")[:120]
        if not first:
            continue
        title = f"[{r.get('kind','?')}:{str(r.get('target','')).split(':')[-1][:40]}] {first}"
        a = assess_comfort(opp)
        before = len(load())
        propose(Proposal(title=title, kind=a["kind"], source=f"model:{r.get('model','?')}", comfort=a["comfort"],
                         risk=a["risk"], reversibility=a["reversibility"], confidence=a["confidence"],
                         rationale="; ".join(a["reasons"]), next_steps="(see the finding)", refs=(str(r.get("target", "")),)))
        n += (len(load()) - before)
    return n


def prioritize() -> Path:
    """Rank proposals by score (highest first), grouped by comfort, and write the prioritized backlog markdown."""
    props = sorted(load(), key=lambda p: -p.get("score", 0))
    groups = {"owner_gated": [], "propose": [], "auto": []}
    for p in props:
        groups.setdefault(p.get("comfort", "propose"), []).append(p)
    lines = ["# Prioritized proposal backlog (development plane; serves_truth=false)", "",
             f"{len(props)} proposals. The loop FILES these when it's uncomfortable applying directly; you prioritize.", "",
             "Score = value x confidence x reversibility / (effort x risk). Higher = do sooner.", ""]
    titles = {"owner_gated": "## ⛔ Owner decision required (brand/pricing/structure/strategy)",
              "propose": "## 🟡 Proposed — review then apply (riskier / not trivial)",
              "auto": "## 🟢 Auto-eligible (trivial + reversible — the autofix/agent can apply)"}
    for g in ("owner_gated", "propose", "auto"):
        if not groups[g]:
            continue
        lines.append(titles[g])
        for p in groups[g][:25]:
            lines.append(f"- **[{p.get('score')}]** ({p.get('kind')}) {p.get('title')}  ·  _{p.get('rationale','')}_")
        if len(groups[g]) > 25:
            lines.append(f"  … (+{len(groups[g]) - 25} more)")
        lines.append("")
    PRIORITIZED.parent.mkdir(parents=True, exist_ok=True)
    PRIORITIZED.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return PRIORITIZED


def _self_test() -> int:
    import tempfile
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)

    # COMFORT GATE
    ck("owner-gated change (rebrand/pricing-tier) -> owner_gated (never auto)", assess_comfort("we should change the pricing tiers")["comfort"] == "owner_gated")
    ck("a passing MENTION of pricing/strategy is NOT owner_gated (no false flag)", assess_comfort("this module's docstring mentions the pricing strategy in passing")["comfort"] != "owner_gated")
    ck("high-blast-radius (migrate/rewrite) -> propose, not auto", assess_comfort("migrate the schema and rewrite the loader")["comfort"] == "propose")
    ck("trivial + reversible (typo/docstring) -> auto-eligible", assess_comfort("fix a typo in the docstring")["comfort"] == "auto")
    ck("unclear change -> defaults to propose (not auto)", assess_comfort("the descent could be better somehow")["comfort"] == "propose")

    # SCORING + dedup + render in a temp ledger
    with tempfile.TemporaryDirectory() as d:
        global LEDGER, PRIORITIZED
        _L, _P = LEDGER, PRIORITIZED
        try:
            LEDGER = Path(d) / "proposals.jsonl"; PRIORITIZED = Path(d) / "prioritized.md"
            hi = Proposal(title="cheap high-value reversible win", value=5, effort=1, risk=1, reversibility=5, confidence=0.9, comfort="auto")
            lo = Proposal(title="expensive risky rewrite", value=3, effort=5, risk=5, reversibility=1, confidence=0.4, comfort="propose")
            og = Proposal(title="rename the product", kind="proposal", comfort="owner_gated")
            ck("a cheap reversible high-value item scores higher than an expensive risky one", hi.score() > lo.score(), f"{hi.score()} vs {lo.score()}")
            propose(hi); propose(lo); propose(og); propose(hi)  # last is a dup
            ck("proposals are recorded + idempotent (dedup by title)", len(load()) == 3)
            ck("proposals are governed candidates (serves_truth=false)", all(p["serves_truth"] is False for p in load()))
            prioritize()
            md = PRIORITIZED.read_text()
            ck("prioritized backlog groups by comfort (owner/propose/auto) + ranks by score",
               "Owner decision required" in md and "Auto-eligible" in md and "cheap high-value" in md)
        finally:
            LEDGER, PRIORITIZED = _L, _P
    ck("five backlog kinds supported (opportunity/proposal/plan/potential/risk)", set(KINDS) == {"opportunity", "proposal", "plan", "potential", "risk"})
    ck("is_irreducible flags external/owner-only (design partner) but NOT design/strategy (best-practice-resolvable now)",
       is_irreducible("sign a design partner + paid pilot") and not is_irreducible("rename the product / lock the one-liner"))
    print("\n" + ("PASS - proposal_backlog: a comfort gate (owner_gated/propose/auto) routes findings — trivial+reversible "
                  "auto, riskier/owner-gated become SCORED, PRIORITIZED proposals (plans/opportunities/risks) for review. "
                  "Idempotent, grouped backlog, serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    if "--distill" in argv:
        i = argv.index("--distill")
        lim = int(argv[i + 1]) if i + 1 < len(argv) and argv[i + 1].isdigit() else 40
        n = distill_findings(lim)
        p = prioritize()
        print(f"distilled {n} new proposal(s) from the last {lim} findings -> {p.relative_to(REPO)} ({len(load())} total)")
        return 0
    if "--prioritize" in argv:
        print(f"wrote {prioritize().relative_to(REPO)} ({len(load())} proposals)")
        return 0
    print("usage: proposal_backlog.py --self-test | --distill [N] | --prioritize")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
