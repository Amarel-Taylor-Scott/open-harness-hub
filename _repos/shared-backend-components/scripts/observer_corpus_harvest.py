#!/usr/bin/env python3
"""scripts.observer_corpus_harvest — the dev-plane DRIVER that RUNS the consented-session corpus flywheel.

It wires the PRODUCT modules (_repos/teleon/backend/src/teleon/observer: consent gate #0 + corpus stages 2-4) to the dev-plane
sinks, so a consented session actually produces outputs future users benefit from:

    consent gate (deny -> skip)  ->  retain + redact  ->  mine  ->  { research-queue entries , candidate
    components }  ->  the INGEST SECURITY GATE scans each component (>=high -> quarantined)  ->  written to
    the research queue (data/research-queue/areas.jsonl) + the discovery feed (data/dev-intel/
    discovered_pipeline.jsonl), candidate-only, where the promotion boundary governs tenant-visibility.

Clean layering: the dev plane (this script) consumes the product modules + the dev-plane security scanner;
the product modules never import the dev plane. serves_truth=false; nothing is retained or emitted without
consent; everything emitted is a governed CANDIDATE.

CLI:
    python3 _repos/shared-backend-components/scripts/observer_corpus_harvest.py --self-test
    python3 _repos/shared-backend-components/scripts/observer_corpus_harvest.py --transcript PATH --subject ada --type human \
            --purpose tool_extraction --scope acme/widgets   # harvest one consented session
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

from src.teleon.observer.consent import ConsentStore, gate_retention
from src.teleon.observer.corpus import mine_session, retain_session, standardize_candidate
from scripts.security.skill_scanner import scan_text  # the ingest security gate (dev-plane)

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
DEFAULT_CONSENT_LEDGER = _resource("data") / "dev-intel" / "observer-consent.jsonl"
DEFAULT_AREAS = _resource("data") / "research-queue" / "areas.jsonl"
DEFAULT_FEED = _resource("data") / "dev-intel" / "discovered_pipeline.jsonl"


def _append_jsonl(path: Path, rows: list[dict]) -> int:
    if not rows:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    return len(rows)


def _research_row(r: dict, *, subject_id: str, session_id: str) -> dict:
    """A mined research signal -> a research-queue area row (the research_queue.process_area shape)."""
    return {"area": r.get("area") or "ai_development_pattern", "industry": "ai_development",
            "use_case": (r.get("note") or "")[:140], "tier": "unstructured_addressable",
            "confidence": r.get("confidence", 0.0), "serves_truth": False,
            "source": "consented_session_mining",
            "provenance": {"subject_id": subject_id, "session_id": session_id}}


def harvest_session(messages: list[dict], *, subject_id: str, subject_type: str, purpose: str, scope: str,
                    store: ConsentStore, session_id: str = "", now: float | None = None,
                    areas_path: Path = DEFAULT_AREAS, feed_path: Path = DEFAULT_FEED) -> dict:
    """Run ONE session through the flywheel. Returns a summary. Emits nothing unless consent allows."""
    decision = gate_retention(store, subject_id, purpose=purpose, scope=scope, now=now)
    if not decision.allowed:
        return {"session_id": session_id, "consented": False, "reason": decision.reason,
                "research": 0, "components": 0, "quarantined": 0}

    retained = retain_session(store, session_id=session_id, subject_id=subject_id, subject_type=subject_type,
                              purpose=purpose, scope=scope, messages=messages, now=now)
    mined = mine_session(messages)

    # research-queue entries
    research_rows = [_research_row(r, subject_id=subject_id, session_id=session_id) for r in mined["research"]]
    n_research = _append_jsonl(areas_path, research_rows)

    # candidate components — each scanned by the INGEST SECURITY GATE before it enters the feed
    feed_rows: list[dict] = []
    quarantined = 0
    for cand in mined["components"]:
        rec = standardize_candidate(cand, subject_id=subject_id, session_id=session_id)
        scan = scan_text(f"{rec['name']} {rec.get('evidence', '')}")
        rec["security_scan"] = {"verdict": scan.verdict, "severity": scan.severity,
                                "findings": [f["rule"] for f in scan.findings]}
        if scan.verdict == "unsafe":           # >=high -> quarantine (candidate-only, never promoted)
            rec["status"] = "quarantined"
            quarantined += 1
        rec["serves_truth"] = False
        feed_rows.append(rec)
    n_components = _append_jsonl(feed_path, feed_rows)

    return {"session_id": session_id, "consented": True, "redactions": (retained or {}).get("redactions", 0),
            "research": n_research, "components": n_components, "quarantined": quarantined}


# --------------------------------------------------------------------------- self-test (hermetic)
def _self_test() -> int:
    import tempfile
    from src.teleon.observer.consent import ConsentRecord
    fails: list[str] = []

    def ck(name: str, ok: bool) -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
        if not ok:
            fails.append(name)

    now = 1_000_000_000.0
    session = [
        {"role": "user", "content": "let me write a csv parser from scratch; key sk-ABCDEF1234567890"},
        {"role": "assistant", "content": "creating parse_csv() — utils.csv.read_rows already exists"},
    ]
    with tempfile.TemporaryDirectory() as d:
        areas, feed = Path(d) / "areas.jsonl", Path(d) / "feed.jsonl"

        # no consent -> nothing emitted
        store = ConsentStore()
        out = harvest_session(session, subject_id="ada", subject_type="human", purpose="tool_extraction",
                              scope="acme/x", store=store, session_id="s1", now=now, areas_path=areas, feed_path=feed)
        ck("no consent -> nothing harvested (consented=False, 0 written)",
           out["consented"] is False and out["research"] == 0 and out["components"] == 0)
        ck("no consent -> no files written", not areas.exists() and not feed.exists())

        # consent -> research + candidate components emitted, candidate-only
        store.grant(ConsentRecord("ada", "human", ("tool_extraction",), scope="acme/*",
                                  retention_days=30, granted_at=now))
        out = harvest_session(session, subject_id="ada", subject_type="human", purpose="tool_extraction",
                              scope="acme/widgets", store=store, session_id="s1", now=now + 1,
                              areas_path=areas, feed_path=feed)
        ck("consent -> harvested (consented=True)", out["consented"] is True)
        ck("emitted >=1 candidate component to the feed", out["components"] >= 1 and feed.exists())
        fed = [json.loads(l) for l in feed.read_text().splitlines() if l.strip()]
        ck("every emitted component is a governed candidate (serves_truth=false, scanned)",
           all(r.get("serves_truth") is False and "security_scan" in r for r in fed))
        ck("redaction ran on the retained session (>=1 secret stripped)", out["redactions"] >= 1)

    if fails:
        print(f"FAIL - observer_corpus_harvest: {len(fails)} failure(s)")
        return 1
    print("PASS - observer_corpus_harvest: consent-gated end-to-end (deny->nothing), redacted retain, mined "
          "research-queue entries + INGEST-SCANNED candidate components, candidate-only/serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Drive the consented-session corpus flywheel (dev-plane harvester).")
    ap.add_argument("--transcript", help="a session transcript to harvest (Claude Code / Codex JSONL or text)")
    ap.add_argument("--subject", default="", help="the consenting subject id")
    ap.add_argument("--type", default="human", help="subject type: human | agent | pipeline")
    ap.add_argument("--purpose", default="tool_extraction", help="the consented purpose")
    ap.add_argument("--purposes", default="", help="grant: comma-separated purposes (tool_extraction,research_queue,component_standardization)")
    ap.add_argument("--scope", default="*", help="the consented scope (project glob)")
    ap.add_argument("--days", type=int, default=90, help="grant: retention window in days")
    ap.add_argument("--grant", action="store_true", help="record consent for --subject (gate #0; off by default)")
    ap.add_argument("--revoke", action="store_true", help="revoke --subject's consent (optionally just --purpose)")
    ap.add_argument("--list-consent", action="store_true", help="list active consent records")
    ap.add_argument("--self-test", action="store_true", help="run the hermetic offline proof")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()

    # ---- consent management (the operator surface for gate #0) ----
    if args.grant or args.revoke or args.list_consent:
        from src.teleon.observer.consent import ConsentRecord
        store = ConsentStore(DEFAULT_CONSENT_LEDGER)
        if args.list_consent:
            for r in store.active_records():
                print(json.dumps(r.to_json()))
            return 0
        if not args.subject:
            ap.error("--grant/--revoke require --subject")
        if args.grant:
            purposes = tuple(p.strip() for p in (args.purposes or args.purpose).split(",") if p.strip())
            store.grant(ConsentRecord(args.subject, args.type, purposes, scope=args.scope, retention_days=args.days))
            print(f"granted: {args.subject} ({args.type}) purposes={purposes} scope={args.scope} days={args.days}")
        else:
            n = store.revoke(args.subject, purpose=(args.purpose if args.purposes == "" and args.purpose else None))
            print(f"revoked {n} record(s) for {args.subject}")
        return 0

    if not (args.transcript and args.subject):
        ap.error("provide --transcript and --subject (or --grant/--revoke/--list-consent/--self-test)")
    from src.teleon.observer.capture import from_transcript
    store = ConsentStore(DEFAULT_CONSENT_LEDGER)
    out = harvest_session(from_transcript(args.transcript), subject_id=args.subject, subject_type=args.type,
                          purpose=args.purpose, scope=args.scope, store=store,
                          session_id=Path(args.transcript).stem, now=time.time())
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
