#!/usr/bin/env python3
"""scripts.capability_seeder — turn DISCOVERED capability candidates into governed, descent-walked seeds.

The side runner (scripts/context_workers/capability_discovery_runner.py) finds candidates from public sources
(skills repos, tools repos, MCP servers, plugins, skills packs). THIS module is the governed intake + the
non-deterministic -> most-deterministic walk for each:

  1. NORMALIZE — source-adapter validation maps a raw discovered row to a CapabilityCandidate.v1 (capability_slot,
     intent, input/output contract, category, source provenance, gap/lift hypotheses, determinism estimates).
  2. SCREEN (the cheap Stage-1 gap/lift screen) — a candidate is ACCEPTED only if it declares a real structural
     gap, a real lift, and a determinism estimate in [0,1]. Rejected candidates are RETAINED (held out, not
     dropped — lossless), with the reason. discovery != trust: everything stays status="candidate".
  3. WALK — build the capability's EVOLUTION GRAPH from its non-deterministic root toward the most-deterministic
     runner it can support: a documented fork to a deterministic runner covering deterministic_coverage_estimate
     of cases, with the residual routed back to the model/agent (lossless). This is the "entire non-det -> most-det
     as possible" walk, per candidate, on the real evolution-graph engine.

Nothing here serves truth, runs a model, or makes a capability active. Deterministic; stdlib only; reads/writes
shared DATA (data/capability-candidates/*). Teleon-layer logic via src.teleon.evolution — never imports src.baltor.

CLI:
    python3 scripts/capability_seeder.py --self-test
    python3 scripts/capability_seeder.py --feed data/capability-candidates/discovered-feed-2026-06-19.json --summary
    python3 scripts/capability_seeder.py --feed <path> --stage      # write staged-candidates.jsonl
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.evolution import CapabilityEvolutionGraph, RunnerNode, plan_descent_to_determinism

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_STAGING_DIR = _REPO / "data" / "capability-candidates"

SCHEMA_VERSION = "CapabilityCandidate.v1"

#: the source kinds the adapters accept (matches the discovered-feed source_kind field).
SOURCE_KINDS = ("anthropic_skill", "github_skills_repo", "github_tools_repo", "mcp_server", "plugin", "skills_pack")
#: capability categories we organize the negative-space corpus around (a stable, bounded vocabulary; widen
#: deliberately as the corpus grows — additive, the named beachhead categories are never removed).
CATEGORIES = (
    "email", "messaging", "research", "scraping", "data-extraction", "document", "code", "devtools",
    "cloud-infra", "database", "legal-statute", "regulation", "federal-register", "financial-data",
    "market-data", "scientific-data", "healthcare", "geo-weather", "productivity", "identity-compliance",
    "media", "other",
)

# ── descent-walk constants (illustrative runner characteristics; named, not magic) ─────────────────────────────
_MODEL_ROOT_DETERMINISM = 0.2        # a model-tier runner is substantially non-deterministic (sampling)
_OPEN_ENDED_ROOT_DETERMINISM = 0.1   # an open-ended agent/research runner is the least deterministic
_MODEL_ROOT_COST = 0.07              # relative per-call cost of a model-tier runner (vs ~0 for a deterministic rule)
_OPEN_ENDED_ROOT_COST = 0.5          # relative per-call cost of an open-ended worker (most expensive)
_DETERMINISTIC_FORK_COST = 0.0       # a distilled deterministic rule is ~free to run
_INHERENTLY_NONDET_CEILING = 0.4     # determinism_ceiling at/below this => the capability is inherently model-bound
_T2_MODEL, _T3_OPEN_ENDED, _T1_DETERMINISTIC = 2, 3, 1  # escalation-ladder tiers (see exploration/ladder.py)


class SeederError(ValueError):
    """Raised on a malformed feed row that an adapter cannot normalize."""


def _content_hash(slot: str, source_name: str, intent: str) -> str:
    """A stable identity hash for dedup across daily discovery runs (capability + source + intent)."""
    blob = "".join((slot.strip().lower(), source_name.strip().lower(), " ".join(intent.split()).lower()))
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def normalize_candidate(raw: dict) -> dict:
    """Source-adapter: validate + normalize one discovered row into a CapabilityCandidate.v1. Raises SeederError
    on a row missing the structural fields an adapter needs (slot/intent/source/category/source_kind)."""
    if not isinstance(raw, dict):
        raise SeederError("candidate row is not an object")
    slot = str(raw.get("capability_slot", "")).strip()
    intent = str(raw.get("intent", "")).strip()
    source_kind = str(raw.get("source_kind", "")).strip()
    source_name = str(raw.get("source_name", "")).strip()
    category = str(raw.get("category", "")).strip()
    if not slot or not intent:
        raise SeederError(f"candidate needs a capability_slot and intent (got {slot!r})")
    if source_kind not in SOURCE_KINDS:
        raise SeederError(f"unknown source_kind {source_kind!r} for {slot!r}; known: {SOURCE_KINDS}")
    if category not in CATEGORIES:
        raise SeederError(f"unknown category {category!r} for {slot!r}; known: {CATEGORIES}")
    if not source_name:
        raise SeederError(f"candidate {slot!r} needs a source_name (provenance)")

    def _clamp01(v) -> float:
        try:
            return max(0.0, min(1.0, float(v)))
        except (TypeError, ValueError):
            return -1.0  # sentinel -> the screen will reject it

    return {
        "schema_version": SCHEMA_VERSION,
        "capability_slot": slot,
        "intent": intent,
        "input_contract": str(raw.get("input_contract", "")).strip(),
        "output_contract": str(raw.get("output_contract", "")).strip(),
        "category": category,
        "source": {"kind": source_kind, "name": source_name, "url": str(raw.get("source_url", "")).strip(),
                   "license": str(raw.get("license", "unknown")).strip() or "unknown",
                   "verify_note": str(raw.get("verify_note", "")).strip()},
        "gap_hypothesis": str(raw.get("gap_hypothesis", "")).strip(),
        "lift_hypothesis": str(raw.get("lift_hypothesis", "")).strip(),
        "determinism_ceiling": _clamp01(raw.get("determinism_ceiling")),
        "deterministic_coverage_estimate": _clamp01(raw.get("deterministic_coverage_estimate")),
        "status": "candidate",            # discovery != trust — never active here
        "serves_truth": False,
        "content_hash": _content_hash(slot, source_name, intent),
    }


def screen(candidate: dict) -> dict:
    """The cheap Stage-1 gap/lift screen. ACCEPT only if the candidate declares a real structural gap, a real
    lift, and a usable determinism estimate. Returns {accepted, reasons} — a REJECT is retained (held out, not
    dropped). This is the negative-space admission bar (a component must let the model do what it can't alone)."""
    reasons: list[str] = []
    if len(candidate.get("gap_hypothesis", "")) < 12:
        reasons.append("no real capability-gap hypothesis (why a bare model fails)")
    if len(candidate.get("lift_hypothesis", "")) < 12:
        reasons.append("no real lift hypothesis (what the component adds)")
    dc, cov = candidate.get("determinism_ceiling", -1.0), candidate.get("deterministic_coverage_estimate", -1.0)
    if not (0.0 <= dc <= 1.0):
        reasons.append("determinism_ceiling not in [0,1]")
    if not (0.0 < cov <= 1.0):
        reasons.append("deterministic_coverage_estimate not in (0,1]")
    if not candidate.get("input_contract") or not candidate.get("output_contract"):
        reasons.append("missing input/output contract")
    return {"accepted": not reasons, "reasons": reasons}


def build_descent_graph(candidate: dict) -> CapabilityEvolutionGraph:
    """Walk the capability from its non-deterministic root toward the most-deterministic runner it can support.

    Root = a model-tier runner (or an open-ended worker for inherently non-deterministic research/agent work),
    coverage 1.0 (it can attempt anything). Then ONE documented fork to a DETERMINISTIC runner (determinism 1.0)
    covering ``deterministic_coverage_estimate`` of cases, cost ~0, with the uncovered residual routed back to the
    root (lossless). determinism_ceiling decides the root KIND (inherently non-det -> open-ended) and is carried as
    context, not faked into the fork. Further forks (e.g. an exact-match template) are added later as real
    distillation produces them — the graph is built to grow."""
    slot = candidate["capability_slot"]
    g = CapabilityEvolutionGraph(slot)
    inherently_nondet = candidate["determinism_ceiling"] <= _INHERENTLY_NONDET_CEILING
    if inherently_nondet and candidate["category"] in ("research",):
        root = RunnerNode(f"{slot}::open_ended@v1", slot, "open_ended", _T3_OPEN_ENDED,
                          _OPEN_ENDED_ROOT_DETERMINISM, 1.0, _OPEN_ENDED_ROOT_COST)
    else:
        root = RunnerNode(f"{slot}::model@v1", slot, "model", _T2_MODEL,
                          _MODEL_ROOT_DETERMINISM, 1.0, _MODEL_ROOT_COST)
    g.add_runner(root)
    # the most-deterministic runner we can support: a deterministic rule covering the estimated fraction.
    cov = candidate["deterministic_coverage_estimate"]
    fork = RunnerNode(f"{slot}::deterministic@v1", slot, "distilled_rule", _T1_DETERMINISTIC, 1.0, cov,
                      _DETERMINISTIC_FORK_COST)
    g.document_fork(root.runner_id, fork,
                    rationale=(f"deterministic extraction covers ~{int(round(cov * 100))}% of cases "
                               f"(ceiling {candidate['determinism_ceiling']}); residual -> {root.kind} root"))
    g.validate()
    return g


def walk_candidate(candidate: dict) -> dict:
    """Normalize-ready candidate -> its descent plan: the evolution graph + the most-deterministic runner within a
    coverage bar + the non-det -> most-det spine. Never serves truth, never activates anything."""
    graph = build_descent_graph(candidate)
    # the most-deterministic runner that still clears a high coverage bar; else the bar at which the fork qualifies.
    plan_full = plan_descent_to_determinism(graph, min_coverage=0.95)
    plan_at_cov = plan_descent_to_determinism(graph, min_coverage=candidate["deterministic_coverage_estimate"])
    return {
        "capability_slot": candidate["capability_slot"],
        "category": candidate["category"],
        "determinism_ceiling": candidate["determinism_ceiling"],
        "deterministic_coverage_estimate": candidate["deterministic_coverage_estimate"],
        "graph": graph.to_dict(),
        "most_deterministic_within_full_coverage": plan_full["chosen_runner"],
        "most_deterministic_runner": plan_at_cov["chosen_runner"],
        "descent_spine": plan_at_cov["descent_spine"],
        "serves_truth": False,
    }


def seed_feed(feed_path: str | Path) -> dict:
    """Load a discovered feed, normalize + screen every row (rejects retained), walk accepted candidates, and
    dedup by content_hash. Returns {accepted, rejected, walked, by_category} — pure, no write (use --stage)."""
    data = json.loads(Path(feed_path).read_text(encoding="utf-8"))
    rows = data.get("candidates", data) if isinstance(data, dict) else data
    accepted, rejected, seen = [], [], set()
    for raw in rows:
        try:
            cand = normalize_candidate(raw)
        except SeederError as e:
            rejected.append({"raw": raw, "reasons": [f"normalize: {e}"]})
            continue
        if cand["content_hash"] in seen:
            continue  # idempotent dedup across overlapping feeds
        seen.add(cand["content_hash"])
        verdict = screen(cand)
        if verdict["accepted"]:
            accepted.append(cand)
        else:
            rejected.append({"candidate": cand, "reasons": verdict["reasons"]})
    walked = [walk_candidate(c) for c in accepted]
    by_category: dict = {}
    for c in accepted:
        by_category[c["category"]] = by_category.get(c["category"], 0) + 1
    return {"accepted": accepted, "rejected": rejected, "walked": walked, "by_category": by_category,
            "feed": str(feed_path), "serves_truth": False}


def stage(feed_path: str | Path, *, out_dir: Path = _STAGING_DIR) -> dict:
    """Write the accepted, walked candidates to JSONL staging (one row per line) — candidate staging, not active
    publication. Returns the staging summary + path. Rejected rows go to a sibling .rejected.jsonl (retained)."""
    result = seed_feed(feed_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    staged_path = out_dir / "staged-candidates.jsonl"
    walked_by_slot = {w["capability_slot"]: w for w in result["walked"]}
    with staged_path.open("w", encoding="utf-8") as fh:
        for c in result["accepted"]:
            row = dict(c)
            row["descent"] = walked_by_slot.get(c["capability_slot"], {})
            fh.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")
    rejected_path = out_dir / "staged-candidates.rejected.jsonl"
    with rejected_path.open("w", encoding="utf-8") as fh:
        for r in result["rejected"]:
            fh.write(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n")
    return {"staged": len(result["accepted"]), "rejected": len(result["rejected"]),
            "staged_path": str(staged_path), "rejected_path": str(rejected_path),
            "by_category": result["by_category"]}


_DEFAULT_FEED = _STAGING_DIR / "discovered-feed-2026-06-19.json"


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # NORMALIZE + SCREEN on a good row.
    good = {"capability_slot": "live-stock-price-quote", "intent": "Fetch a live stock quote.",
            "input_contract": "ticker", "output_contract": "price + timestamp", "category": "financial-data",
            "source_kind": "mcp_server", "source_name": "sapph1re/findata-mcp", "source_url": "https://example",
            "gap_hypothesis": "the model has no real-time market access", "lift_hypothesis": "adds a live data API call",
            "determinism_ceiling": 1.0, "deterministic_coverage_estimate": 1.0}
    cand = normalize_candidate(good)
    ck("normalize produces a CapabilityCandidate.v1 (candidate, never truth)",
       cand["schema_version"] == SCHEMA_VERSION and cand["status"] == "candidate" and cand["serves_truth"] is False
       and cand["content_hash"].startswith("sha256:"))
    ck("a well-formed candidate passes the gap/lift screen", screen(cand)["accepted"] is True)

    # SCREEN rejects (and the runner retains) a thin candidate — lossless.
    thin = dict(good, gap_hypothesis="", lift_hypothesis="")
    ck("a candidate with no gap/lift hypothesis is REJECTED (held out, not dropped)",
       screen(normalize_candidate(thin))["accepted"] is False)
    # bad source_kind / category / missing slot fail loud in normalize.
    for bad, why in ((dict(good, source_kind="random"), "source_kind"),
                     (dict(good, category="banking"), "category"),
                     (dict(good, capability_slot=""), "slot")):
        raised = False
        try:
            normalize_candidate(bad)
        except SeederError:
            raised = True
        ck(f"a row with a bad {why} fails loud in normalize", raised)

    # WALK builds the non-det -> most-det graph: deterministic fork + residual routed, model preserved.
    walk = walk_candidate(cand)
    g = walk["graph"]
    ck("the descent walk roots at a non-deterministic runner and forks to a deterministic one",
       g["root"].endswith("::model@v1") and any(r["kind"] == "distilled_rule" and r["determinism"] == 1.0
                                                 for r in g["runners"]))
    ck("the deterministic fork covers the estimated fraction; the model parent is preserved",
       any(r["kind"] == "distilled_rule" and abs(r["capability_coverage"] - 1.0) < 1e-9 for r in g["runners"])
       and any(r["kind"] == "model" for r in g["runners"]))
    ck("the descent spine walks non-det -> most-det and never serves truth",
       len(walk["descent_spine"]) == 2 and walk["serves_truth"] is False and g["serves_truth"] is False)

    # an inherently non-deterministic research capability roots at an OPEN-ENDED worker.
    research = normalize_candidate(dict(good, capability_slot="autonomous-research-agent", category="research",
                                        intent="Run autonomous research.", determinism_ceiling=0.25,
                                        deterministic_coverage_estimate=0.35, source_name="assafelovic/gpt-researcher"))
    rgraph = build_descent_graph(research).to_dict()
    ck("an inherently non-deterministic research capability roots at an OPEN-ENDED worker",
       rgraph["root"].endswith("::open_ended@v1"))
    ck("even an inherently non-det capability records its deterministic sub-portion as a fork (~35% covered)",
       any(r["kind"] == "distilled_rule" and abs(r["capability_coverage"] - 0.35) < 1e-9 for r in rgraph["runners"]))

    # SEED the REAL discovered feed end-to-end (if present): most accepted, every accepted walked, dedup holds.
    if _DEFAULT_FEED.exists():
        res = seed_feed(_DEFAULT_FEED)
        ck("the real discovered feed seeds >=30 governed candidates across many categories",
           len(res["accepted"]) >= 30 and len(res["by_category"]) >= 7, str(res["by_category"]))
        ck("every accepted candidate is walked into a valid descent graph",
           len(res["walked"]) == len(res["accepted"]) and all(w["graph"]["serves_truth"] is False for w in res["walked"]))
        ck("seeding is idempotent (dedup by content_hash holds on a re-run)",
           len(seed_feed(_DEFAULT_FEED)["accepted"]) == len(res["accepted"]))
        ck("every seeded candidate stays a CANDIDATE (discovery != trust — nothing auto-active)",
           all(c["status"] == "candidate" and c["serves_truth"] is False for c in res["accepted"]))
        # the user's named categories are all represented.
        cats = set(res["by_category"])
        ck("the named categories (federal-register, regulation, legal-statute, financial-data, scraping, email, research) are seeded",
           {"federal-register", "regulation", "legal-statute", "financial-data", "scraping", "email", "research"} <= cats,
           str(sorted(cats)))

    print("\n" + ("PASS - capability_seeder: discovered rows normalize into governed CapabilityCandidate.v1, pass a "
                  "cheap gap/lift SCREEN (rejects retained, not dropped), and each accepted capability is WALKED "
                  "from its non-deterministic root to the most-deterministic runner it can support (a documented "
                  "deterministic fork covering the estimated fraction, residual routed to the preserved model — "
                  "lossless). Everything stays a candidate; nothing serves truth or runs a model."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Seed + descent-walk discovered capability candidates (governed).")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--feed", type=str, help="path to a discovered-feed JSON/JSONL")
    p.add_argument("--summary", action="store_true", help="print the seed summary")
    p.add_argument("--stage", action="store_true", help="write staged-candidates.jsonl")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    feed = a.feed or str(_DEFAULT_FEED)
    if a.stage:
        print(json.dumps(stage(feed), indent=2))
        return 0
    res = seed_feed(feed)
    if a.summary:
        print(f"accepted={len(res['accepted'])} rejected={len(res['rejected'])} by_category={res['by_category']}")
        for w in res["walked"][:10]:
            print(f"  {w['capability_slot']:34} det_ceiling={w['determinism_ceiling']} "
                  f"most_det={w['most_deterministic_runner'].split('::')[-1]} spine={len(w['descent_spine'])}")
        return 0
    print(json.dumps({"accepted": len(res["accepted"]), "rejected": len(res["rejected"]),
                      "by_category": res["by_category"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main() if not ("--self-test" in sys.argv) else _self_test())
