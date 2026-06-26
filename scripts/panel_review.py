#!/usr/bin/env python3
"""panel_review — a standing MULTI-MODEL EXECUTIVE REVIEW BOARD that cross-reviews our code + product.

Claude (this session) + Kimi-2.7 + GLM-5.2 each review the codebase + product through FIVE executive lenses
(CEO / COO / CTO / CFO / YC partner), then CRITIQUE EACH OTHER'S reviews (adversarial cross-review), so no single
model's blind spot or hallucination drives a conclusion. Every output is a GOVERNED CANDIDATE (serves_truth=false —
a model opinion is a proposal, never trusted truth) and is appended to the append-only `panel_reviews` history stream
(architecture/storage_tier_policy.json) so the board's judgments accumulate over time.

ROUNDS:
  round1  each seat produces a multi-persona review (CEO/COO/CTO/CFO/YC) of the bounded context pack.
  round2  each model receives the OTHER seats' round1 reviews and critiques them (agree/disagree/wrong/missed).
  (synthesis is produced by the orchestrator — the Claude Code session — from round1+round2, see --synthesize.)

The Claude seat is filled by the orchestrator (a file written by the Claude Code session) OR an `anthropic` provider
when keyed; Kimi + GLM are called live via the Ollama Cloud lane. Reuses scripts.external_review (pack, chat, provider,
governance). Legacy-doc archiving is a sibling deterministic step: scripts.archive_legacy_docs.

  --self-test            offline: personas/panel/pack/stream/archiver all wired + governed
  --run [--round 1|2|all]   live: call the api seats for the round(s)
CLI: python3 scripts/panel_review.py --run --round all
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.external_review import build_context_pack, assert_pack_safe, chat, resolve_provider

PANEL_DIR = REPO / "docs" / "reviews" / "panel"

#: the five executive lenses — each a focused review brief. The value of the board is role-diversity.
PERSONAS = {
    "CEO": "the CEO lens: vision, market size, focus vs sprawl, the narrative a buyer/investor hears, the single "
           "existential risk, and 'what must be true' for this to be a billion-dollar company.",
    "COO": "the COO lens: execution + delivery, scope discipline, what is ACTUALLY shipping vs scaffolding, "
           "operational scalability, and the biggest process/throughput bottleneck.",
    "CTO": "the CTO lens: architecture soundness, the top technical risks, scalability + tech debt, build-vs-buy "
           "(what is being reinvented that should be bought), and where the system breaks first under load.",
    "CFO": "the CFO lens: unit economics, cost-to-serve, burn, pricing + revenue model, runway implications, and "
           "whether the cost-descent thesis actually shows up as margin.",
    "YC": "the Y Combinator partner lens: is this a startup or a research project? the wedge, why-now, why-you, "
          "default-alive, 'make something people want', and the one brutal question a partner asks at the interview.",
}

#: the board. api seats are called live; the orchestrator seat is filled by the Claude Code session (or an
#: anthropic provider when a key exists). Kimi + GLM ride the Ollama Cloud lane (.env OH_LLM_*).
PANEL = [
    {"name": "claude-opus", "kind": "orchestrator", "provider": "anthropic", "model": "claude-opus-4-8"},
    {"name": "glm-5.2", "kind": "api", "provider": "ollama", "model": "glm-5.2"},
    {"name": "kimi-k2.7-code", "kind": "api", "provider": "ollama", "model": "kimi-k2.7-code"},
]

ROUND1_SYSTEM = ("You are a multi-disciplinary review board member doing diligence on another team's codebase and "
                 "product. Be specific, critical, file-citing. No flattery, no hedging.")


def round1_user(pack: str) -> str:
    lenses = "\n".join(f"- {k}: {v}" for k, v in PERSONAS.items())
    return ("Review the platform below (Baltor = a context engine; Teleon = a runtime that DESCENDS non-deterministic "
            "capabilities to cheaper/faster/more-deterministic/more-bounded against user preferences; Open Harness Hub "
            "= the open ecosystem). Review it through EACH of these executive lenses:\n" + lenses + "\n\n"
            "For EACH lens, give: the 2 biggest strengths, the 2 most serious risks, and 1 concrete recommendation "
            "(cite files). End with 'TOP PRIORITY:' — your single highest-leverage action across all lenses.\n\n"
            "=== CONTEXT PACK ===\n" + pack + "\n=== END PACK ===")


def round2_user(own_name: str, others: dict[str, str]) -> str:
    blocks = "\n\n".join(f"----- REVIEW BY {n} -----\n{t[:9000]}" for n, t in others.items())
    return (f"You are {own_name}, on a review board. Below are the other board members' reviews of the same platform. "
            "CRITIQUE them: where do you AGREE, where do you DISAGREE, what did they get factually WRONG (e.g. a claim "
            "contradicted by the code), and what did they MISS? Be specific and adversarial — the point is to catch "
            "each other's blind spots and hallucinations. Then give 'REVISED TOP 3:' — the board's three highest-"
            "priority actions after weighing all views.\n\n" + blocks)


def _review_id(round_name: str, seat: str, text: str) -> str:
    return "rev_" + hashlib.sha256(f"{round_name}|{seat}|{text}".encode()).hexdigest()[:16]


def _record(round_name: str, seat: str, model: str, text: str, usage: dict, error) -> dict:
    return {"review_id": _review_id(round_name, seat, text or (error or "")), "round": round_name, "seat": seat,
            "model": model, "chars": len(text or ""), "usage": usage, "error": error,
            "status": "candidate", "serves_truth": False}


def _append_stream(records: list[dict]) -> int:
    """Append the round's review records to the append-only panel_reviews history stream (best-effort)."""
    try:
        from src.teleon.storage.record_store import open_record_store
        store = open_record_store("panel_reviews")
        for r in records:
            store.append(r, idem_key=r["review_id"])
        return store.count()
    except Exception as e:  # noqa: BLE001 — the stream is an index; never block a review on it
        print(f"  (stream append skipped: {e})")
        return -1


def _read_seat_file(round_dir: Path, seat: str) -> str | None:
    f = round_dir / f"{seat}.md"
    return f.read_text(encoding="utf-8") if f.exists() else None


def run_round1() -> dict:
    pack, manifest = build_context_pack()
    bad = assert_pack_safe(pack, manifest)
    if bad:
        print("REFUSED — pack failed governance:", bad); return {"error": bad}
    rdir = PANEL_DIR / "round1"; rdir.mkdir(parents=True, exist_ok=True)
    records, texts = [], {}
    for seat in PANEL:
        name = seat["name"]
        if seat["kind"] == "orchestrator":
            existing = _read_seat_file(rdir, name)
            status = "present (orchestrator-written)" if existing else "PENDING — write docs/reviews/panel/round1/%s.md" % name
            print(f"seat {name}: {status}")
            if existing:
                texts[name] = existing
            continue
        prov = resolve_provider(seat["provider"])
        if not prov["key"]:
            print(f"seat {name}: SKIP (no key for {seat['provider']})"); continue
        print(f"seat {name}: calling {seat['model']} (round1, multi-persona) ...", flush=True)
        res = chat(seat["model"], ROUND1_SYSTEM, round1_user(pack), prov)
        if res["error"]:
            print(f"  ERROR: {res['error'][:200]}")
        else:
            print(f"  ok: {len(res['text'])} chars")
            header = f"# Panel round 1 — {name} ({seat['model']})\n\n> CANDIDATE · serves_truth=false · CEO/COO/CTO/CFO/YC lenses\n\n"
            (rdir / f"{name}.md").write_text(header + res["text"], encoding="utf-8")
            texts[name] = res["text"]
        records.append(_record("round1", name, seat["model"], res["text"], res["usage"], res["error"]))
    n = _append_stream(records)
    print(f"round1: {len([t for t in texts.values()])} reviews · panel_reviews stream now holds {n} records")
    return {"texts": texts, "records": records}


def run_round2() -> dict:
    r1 = PANEL_DIR / "round1"
    all_r1 = {s["name"]: _read_seat_file(r1, s["name"]) for s in PANEL}
    all_r1 = {k: v for k, v in all_r1.items() if v}
    if len(all_r1) < 2:
        print("round2 needs >=2 round1 reviews; run round1 first."); return {"error": "insufficient round1"}
    rdir = PANEL_DIR / "round2"; rdir.mkdir(parents=True, exist_ok=True)
    records = []
    for seat in PANEL:
        name = seat["name"]
        others = {n: t for n, t in all_r1.items() if n != name}
        if seat["kind"] == "orchestrator":
            print(f"seat {name}: cross-critique is orchestrator-written (docs/reviews/panel/round2/{name}.md)")
            continue
        prov = resolve_provider(seat["provider"])
        if not prov["key"]:
            print(f"seat {name}: SKIP (no key)"); continue
        print(f"seat {name}: calling {seat['model']} (round2, cross-critique of {list(others)}) ...", flush=True)
        res = chat(seat["model"], ROUND1_SYSTEM, round2_user(name, others), prov)
        if res["error"]:
            print(f"  ERROR: {res['error'][:200]}")
        else:
            print(f"  ok: {len(res['text'])} chars")
            header = f"# Panel round 2 (cross-critique) — {name} ({seat['model']})\n\n> CANDIDATE · serves_truth=false\n\n"
            (rdir / f"{name}.md").write_text(header + res["text"], encoding="utf-8")
        records.append(_record("round2", name, seat["model"], res["text"], res["usage"], res["error"]))
    n = _append_stream(records)
    print(f"round2: cross-critiques done · panel_reviews stream now holds {n} records")
    return {"records": records}


def _self_test() -> int:
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)
    ck("five executive personas are defined (CEO/COO/CTO/CFO/YC)", set(PERSONAS) == {"CEO", "COO", "CTO", "CFO", "YC"})
    ck("the panel has Claude + Kimi + GLM seats", {s["name"] for s in PANEL} >= {"claude-opus", "glm-5.2", "kimi-k2.7-code"})
    ck("exactly one orchestrator (Claude) seat + >=2 api seats", sum(1 for s in PANEL if s["kind"] == "orchestrator") == 1 and sum(1 for s in PANEL if s["kind"] == "api") >= 2)
    pack, manifest = build_context_pack()
    ck("the context pack is built + passes secrets governance", not assert_pack_safe(pack, manifest))
    ck("round1 prompt embeds all five lenses", all(k in round1_user("X") for k in PERSONAS))
    ck("round2 prompt asks for cross-critique (agree/disagree/wrong/missed)", all(w in round2_user("x", {"y": "z"}).lower() for w in ("agree", "disagree", "wrong", "miss")))
    ck("review_id is deterministic (same input -> same id; idempotent stream)", _review_id("round1", "glm-5.2", "t") == _review_id("round1", "glm-5.2", "t"))
    ck("records are candidates (serves_truth=false)", _record("round1", "x", "m", "t", {}, None)["serves_truth"] is False)
    # the panel_reviews stream is a declared history stream with an idempotency key
    try:
        from src.teleon.storage.record_store import stream_spec
        spec = stream_spec("panel_reviews")
        ck("panel_reviews is a declared history stream with an idempotency key", spec["tier"] == "history" and spec.get("idempotency_key") == "review_id")
    except Exception as e:  # noqa: BLE001
        ck("panel_reviews stream is declared", False, str(e))
    try:
        import scripts.archive_legacy_docs  # noqa: F401
        ck("the legacy-doc archiver is importable (sibling loop step)", True)
    except Exception as e:  # noqa: BLE001
        ck("the legacy-doc archiver is importable", False, str(e))
    print("\n" + ("PASS - panel_review --self-test: a Claude+Kimi+GLM board reviews through CEO/COO/CTO/CFO/YC lenses, "
                  "cross-critiques each other, lands candidates (serves_truth=false) into the append-only panel_reviews "
                  "history stream. Run --run --round all to convene it."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    rnd = "all"
    for i, a in enumerate(argv):
        if a == "--round" and i + 1 < len(argv): rnd = argv[i + 1]
    if "--self-test" in argv:
        return _self_test()
    if "--run" in argv:
        if rnd in ("1", "all"):
            run_round1()
        if rnd in ("2", "all"):
            run_round2()
        return 0
    print("usage: panel_review.py --self-test | --run [--round 1|2|all]")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
