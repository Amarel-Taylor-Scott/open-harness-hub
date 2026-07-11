#!/usr/bin/env python3
"""Foundry seeds — feed the pipeline REAL gaps + acquire LOCAL sources + a ledger.

Cycle fuel for the build loop (`_repos/shared-backend-components/context/codex/foundry-build-loop.md`):

  - ``load_areas`` turns the real research queue (``data/research-queue/areas.jsonl``)
    into gap-candidates, mapping its **model-independent** signals (corpus-density
    gap, regulatory velocity, query misses, low coverage) into a gap score and
    treating a high recorded ``confident_hallucination`` as bare-model failure
    evidence — the screen the model can't draw for itself.
  - ``LocalSourceScout`` is an OFFLINE Stage-1 scout over provenance-bearing local
    files (no network) — the acquisition path that works in a sandbox.
  - ``run_cycle`` runs a partition, appends an honest funnel line to
    ``data/foundry-ledger.jsonl`` (promoted, never generated), and records the
    binding blocker so the loop's BRANCH step is data-driven.

Run ``python -m scripts.foundry.seeds --self-test`` (offline) or
``python -m scripts.foundry.seeds --run`` to execute one cycle on the real queue.
"""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any

from scripts.eval.reason_codes import TIER_BY_KEY
from scripts.foundry.contracts import FUNNEL_STAGES, Candidate
from scripts.foundry.pipeline import Foundry, _fixture
from scripts.foundry.sources import SourceStage, is_permissive, normalize_source_kind

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2])
from scripts._repo_paths import resource as _resource
AREAS_PATH = _resource("data") / "research-queue" / "areas.jsonl"
LEDGER_PATH = _resource("data") / "foundry-ledger.jsonl"

_CONFIDENT_HALLUCINATION_FAILURE = 0.5   # ≥ this ⇒ recorded bare-model failure evidence
_QUERY_MISS_SCALE = 8.0                  # normalize query_misses count → [0,1]

# retrievability tier → a starting durability reason (refined later by a live judge)
_TIER_LIFT_REASON = {
    "clean_api": "missing_tool",
    "structured_no_api": "missing_tool",
    "unstructured_addressable": "esoteric_rule",
    "unaddressable_ephemeral": "no_addressable_source",
    "human_only": "accountability_or_license",
}


def _slug(text: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", (text or "").lower())).strip("-")[:48] or "area"


def area_to_gap(area: dict) -> dict:
    """Map a research-queue area into a gap dict (model-independent signals dominate)."""
    mi_signals = [
        float(area.get("corpus_density_gap") or 0.0),
        float(area.get("regulatory_velocity") or 0.0),
        min(float(area.get("query_misses") or 0.0) / _QUERY_MISS_SCALE, 1.0),
        1.0 - float(area.get("current_coverage") or 0.0),
    ]
    mi = round(sum(mi_signals) / len(mi_signals), 3)
    ch = float(area.get("confident_hallucination") or 0.0)
    failure = ([{"signal": "confident_hallucination", "value": ch, "why": area.get("why", "")}]
               if ch >= _CONFIDENT_HALLUCINATION_FAILURE else [])
    tier_key = area.get("tier", "")
    return {
        "id": f"gap/{_slug(area.get('area', ''))}",
        "summary": f"{area.get('area', '')} — {area.get('why', '')}".strip(" —"),
        "lift_reason": _TIER_LIFT_REASON.get(tier_key, "esoteric_rule"),
        "model_independent_score": mi,
        "retrievability_tier": int(TIER_BY_KEY.get(tier_key, {}).get("tier", 0)) or None,
        "failure_samples": failure,
        "source_hints": list(area.get("source_hints") or []),
        "industry": [area["industry"]] if area.get("industry") else [],
        "area_signals": {k: area.get(k) for k in
                         ("corpus_density_gap", "regulatory_velocity", "query_misses",
                          "current_coverage", "confident_hallucination", "pays")},
    }


def load_areas(path: str | Path = AREAS_PATH) -> list[Candidate]:
    """Parse areas.jsonl (skipping # comments) into gap-candidates."""
    p = Path(path)
    out: list[Candidate] = []
    if not p.exists():
        return out
    for line in p.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        try:
            area = json.loads(s)
        except json.JSONDecodeError:
            continue
        if isinstance(area, dict) and area.get("area"):
            out.append(Candidate(gap=area_to_gap(area)))
    return out


class LocalSourceScout:
    """Offline Stage-1 scout: match a gap to a provenance-bearing LOCAL file and
    load its rows as the constructor's payload. No network.

    ``registry`` entries: ``{keywords, source_url, author, license, source_kind, path,
    name?, industry?, max_facts?}``. ``path`` is a repo-relative JSONL whose rows
    become ``payload.facts``."""

    def __init__(self, registry: list[dict] | None = None) -> None:
        self.registry = registry or []

    def find(self, gap: dict) -> dict | None:
        haystack = " ".join([
            gap.get("summary", ""), " ".join(gap.get("industry", []) or []),
            " ".join(gap.get("source_hints", []) or []),
        ]).lower()
        for entry in self.registry:
            if not any(kw.lower() in haystack for kw in entry.get("keywords", [])):
                continue
            if not is_permissive(entry.get("license", "")):
                continue
            path = (_resource(entry["path"])) if not Path(entry["path"]).is_absolute() else Path(entry["path"])
            if not path.exists():
                continue
            facts = []
            for ln in path.read_text(encoding="utf-8").splitlines()[: entry.get("max_facts", 500)]:
                ln = ln.strip()
                if ln and not ln.startswith("#"):
                    try:
                        facts.append(json.loads(ln))
                    except json.JSONDecodeError:
                        facts.append({"text": ln})
            if not facts:
                continue
            return {
                "source_url": entry["source_url"], "author": entry["author"],
                "license": entry["license"], "source_kind": normalize_source_kind(entry.get("source_kind", "other")),
                "payload": {"name": entry.get("name") or gap.get("summary", "Local corpus"),
                            "industry": entry.get("industry") or gap.get("industry", []),
                            "capability": ["retrieval"], "facts": facts},
            }
        return None


# No clean non-component local source matches the current (external-regulatory) queue,
# so the default is empty — the real run honestly shows the acquisition wall. The scout
# itself is proven against a temp fixture in the self-test, ready for provenance'd veins.
DEFAULT_LOCAL_SOURCES: list[dict] = []


# --------------------------------------------------------------------------- #
# ledger
# --------------------------------------------------------------------------- #
def _env() -> dict[str, Any]:
    try:
        import sentence_transformers  # noqa: F401
        st = True
    except ImportError:
        st = False
    from scripts.foundry.model_route import from_env
    route = from_env()
    return {"network": False, "sentence_transformers": st,
            "model_route": route.name if route else None}


def _blocked_note(cp: dict, env: dict) -> str | None:
    notes: list[str] = []
    if cp.get("gaps_confirmed", 0) and not cp.get("sources_found", 0):
        notes.append("acquisition: no source acquired (no network / no matching local source) — wire a scout")
    if cp.get("novel", 0) and not cp.get("lift_measured", 0):
        notes.append("measurement: lift unmeasured (no model route / no recorded eval) — routed to review")
    return "; ".join(notes) or None


def append_ledger(path: str | Path, *, kind: str, partition: str, result: dict,
                  date: str, env: dict, ladder_item: str) -> dict:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    cycle = sum(1 for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()) + 1 if p.exists() else 1
    led = result["ledger"]
    line = {
        "date": date, "cycle": cycle, "kind": kind, "partition": partition, "ladder_item": ladder_item,
        "funnel": {s: led.checkpoints.get(s) for s in FUNNEL_STAGES},
        "promoted": led.promoted, "promoted_ids": led.promoted_ids,
        "review": len(result.get("review", [])),
        "blocked": _blocked_note(led.checkpoints, env), "env": env,
        "metric_note": "promoted = cleared the measured-lift gate; never report generated.",
    }
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(line, sort_keys=True, ensure_ascii=True) + "\n")
    return line


def run_cycle(*, areas_path: str | Path = AREAS_PATH, ledger_path: str | Path = LEDGER_PATH,
              now_s: float | None = None) -> list[dict]:
    """One cycle: a labeled synthetic demonstration line + the real research-queue line."""
    date = time.strftime("%Y-%m-%d", time.gmtime(now_s))
    env = _env()
    lines: list[dict] = []

    # If a model route is configured (e.g. OLLAMA_API_KEY), wire LIVE measurement +
    # gap-probe + real embeddings into each partition — otherwise offline defaults run.
    from scripts.foundry.model_route import from_env as _route_from_env, wire as _wire_route
    route = _route_from_env()

    # A) synthetic demonstration — proves the FULL path (recorded eval ⇒ a real promotion)
    fdemo, seeds_demo = _fixture()
    if route:
        _wire_route(fdemo, route)
    demo = fdemo.run_partition(seeds_demo, partition="fixture-esg-csddd")
    lines.append(append_ledger(ledger_path, kind="synthetic_demo", partition="fixture-esg-csddd",
                               result=demo, date=date, env=env,
                               ladder_item="demonstration: full path incl. promotion (recorded eval)"))

    # B) the REAL research queue — honest about where the sandbox blocks
    real_seeds = load_areas(areas_path)
    freal = Foundry(sources=SourceStage(LocalSourceScout(DEFAULT_LOCAL_SOURCES)))
    if route:
        _wire_route(freal, route)
    real = freal.run_partition(real_seeds, partition="research-queue")
    lines.append(append_ledger(ledger_path, kind="real", partition="research-queue",
                               result=real, date=date, env=env,
                               ladder_item="P-C run real partition from data/research-queue/areas.jsonl"))
    return lines


# --------------------------------------------------------------------------- #
# self-test (offline)
# --------------------------------------------------------------------------- #
def enqueue_partitions(*, areas_path: str | Path = AREAS_PATH, queue=None, with_fixture: bool = False) -> int:
    """Put one partition job per research-queue area onto the queue (the web tier / cron does
    this; workers drain it). Closes the enqueue → worker → store loop. Returns jobs enqueued."""
    from scripts.foundry.queues import from_env as queue_from_env

    q = queue if queue is not None else queue_from_env()
    n = 0
    if with_fixture:   # a guaranteed-promoting partition for smoke-testing the worker
        from scripts.foundry.pipeline import _fixture
        q.enqueue({"partition": "fixture-esg-csddd", "kind": "synthetic_demo",
                   "gaps": [c.gap for c in _fixture()[1]]})
        n += 1
    for cand in load_areas(areas_path):
        gap = cand.gap
        q.enqueue({"partition": gap.get("id", "area").replace("gap/", ""), "kind": "real", "gaps": [gap]})
        n += 1
    return n


def _self_test() -> int:
    import tempfile

    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # area → gap mapping
    strong = {"area": "PH AML thresholds", "industry": "financial-crime", "tier": "unstructured_addressable",
              "corpus_density_gap": 0.9, "regulatory_velocity": 0.9, "query_misses": 6, "current_coverage": 0.1,
              "confident_hallucination": 0.9, "why": "base models fabricate the new threshold"}
    g = area_to_gap(strong)
    check("model-independent score in (0,1]", 0.0 < g["model_independent_score"] <= 1.0, str(g["model_independent_score"]))
    check("high confident_hallucination ⇒ failure evidence", bool(g["failure_samples"]))
    check("tier mapped to lift_reason", g["lift_reason"] == "esoteric_rule")
    check("retrievability tier resolved", g["retrievability_tier"] == 3)

    with tempfile.TemporaryDirectory() as tmp:
        # load_areas (with a comment line + a blank)
        ap = Path(tmp) / "areas.jsonl"
        ap.write_text("# comment\n\n" + json.dumps(strong) + "\n"
                      + json.dumps({"area": "weak one", "tier": "clean_api", "corpus_density_gap": 0.1,
                                    "regulatory_velocity": 0.1, "query_misses": 0, "current_coverage": 0.9,
                                    "confident_hallucination": 0.1}) + "\n", encoding="utf-8")
        seeds = load_areas(ap)
        check("load_areas skips comments/blanks → 2 gaps", len(seeds) == 2, str(len(seeds)))

        # enqueue: one partition job per area (+ optional fixture) onto the queue
        from scripts.foundry.worker import InMemoryQueue
        q = InMemoryQueue()
        n = enqueue_partitions(areas_path=ap, queue=q, with_fixture=True)
        check("enqueue_partitions: a job per area + the fixture", n == len(seeds) + 1 and len(q) == n, f"n={n} depth={len(q)}")
        check("enqueued jobs carry gaps", (q.pull() or {}).get("gaps") is not None)

        # LocalSourceScout finds a permissive local source + loads facts
        src_file = Path(tmp) / "aml.jsonl"
        src_file.write_text(json.dumps({"code": "AML-1", "rule": "structuring"}) + "\n"
                            + json.dumps({"code": "AML-2", "rule": "smurfing"}) + "\n", encoding="utf-8")
        scout = LocalSourceScout([{
            "keywords": ["aml"], "source_url": "https://amlc.gov.ph/x", "author": "AMLC",
            "license": "CC0-1.0", "source_kind": "regulation", "path": str(src_file), "name": "PH AML rules",
        }])
        found = scout.find(g)
        check("scout matches gap + loads facts", bool(found) and len(found["payload"]["facts"]) == 2, str(found))
        check("scout rejects non-permissive license",
              LocalSourceScout([{"keywords": ["aml"], "source_url": "u", "author": "a",
                                 "license": "All Rights Reserved", "path": str(src_file)}]).find(g) is None)

        # mini real-shaped run: real source mined → draft built → held at measurement (honest, no model)
        freal = Foundry(sources=SourceStage(scout))
        res = freal.run_partition([Candidate(gap=g)], partition="t")
        cp = res["ledger"].checkpoints
        check("gap confirmed on real signals", cp.get("gaps_confirmed") == 1, str(cp))
        check("local source acquired", cp.get("sources_found") == 1, str(cp))
        check("real source mined into a draft", cp.get("drafts_built", 0) >= 1, str(cp))
        check("no eval ⇒ unmeasured ⇒ 0 promoted (honest)", cp.get("promoted") == 0)
        check("held for review (not culled)", len(res["review"]) >= 1)

        # ledger append writes a valid honest line
        lp = Path(tmp) / "ledger.jsonl"
        line = append_ledger(lp, kind="real", partition="t", result=res, date="2026-05-28",
                             env={"network": False, "sentence_transformers": False, "model_route": False},
                             ladder_item="test")
        check("ledger line has funnel + blocked note", "funnel" in line and line["blocked"], str(line.get("blocked")))
        check("ledger file written", lp.exists() and lp.read_text().strip())

    print(f"\n{'all seeds self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Foundry seeds — real research-queue cycle + ledger.")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--run", action="store_true", help="run one real cycle and append to the ledger")
    p.add_argument("--enqueue", action="store_true", help="enqueue one partition job per research-queue area")
    p.add_argument("--with-fixture", action="store_true", help="(with --enqueue) also enqueue the fixture partition")
    p.add_argument("--areas", default=str(AREAS_PATH))
    p.add_argument("--ledger", default=str(LEDGER_PATH))
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.enqueue:
        from scripts.foundry.queues import from_env as queue_from_env
        q = queue_from_env()
        n = enqueue_partitions(areas_path=args.areas, queue=q, with_fixture=args.with_fixture)
        print(json.dumps({"enqueued": n, "queue": type(q).__name__,
                          "depth": q.depth() if hasattr(q, "depth") else None}))
        return 0
    if args.run:
        lines = run_cycle(areas_path=args.areas, ledger_path=args.ledger)
        for ln in lines:
            print(json.dumps(ln, indent=2, sort_keys=True))
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
