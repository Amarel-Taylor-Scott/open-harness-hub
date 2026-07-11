#!/usr/bin/env python3
"""scripts.input_token_lever — quantify the BIGGEST, least-explored primitive-DB savings lever: INPUT tokens.

Owner thesis (2026-07-09): realistic senior-dev agentic sessions are input-token-dominated — the growing conversation
+ re-read file bodies are re-sent EVERY turn, so a long session over a big working set is millions–billions of INPUT
tokens; single-shot OUTPUT savings are the rounding error. The primitive DB's biggest lever is therefore: replace the
raw bodies of VERIFIED, reusable modules with compact CAPABILITY CARDS (name + typed edges + verified hash + one-line
behavior) that the agent trusts without re-reading, while novel code stays raw. Because context is re-sent per turn,
the saving COMPOUNDS with turn count × verified fraction.

This module measures that structurally (deterministic token-accounting over REAL module sizes; labeled PROXY, never a
live headline — a live agent must still succeed under card context, which `realistic_session_harness.py` tests). It
reports: raw vs card cumulative INPUT tokens, reduction %, the re-read multiplier (#18), and the per-turn curve. This
is the mechanism behind ideation paths #18/#20/#22/#23/#26. serves_truth=false.

    python3 scripts/input_token_lever.py --self-test
    python3 scripts/input_token_lever.py --report --turns 50 --verified-fraction 0.6
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import hashlib  # noqa: E402  (card hash handle — not an id)
import json  # noqa: E402
from typing import Any  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
_CHARS_PER_TOKEN = 4


def _tok(s: str) -> int:
    return max(1, len(s) // _CHARS_PER_TOKEN)


def _real_working_set() -> dict[str, dict[str, Any]]:
    """A working set of REAL module sources tagged verified (reusable, card-eligible) vs novel (must stay raw)."""
    from scripts.automation_directory_forge import WEBHOOK_WORKER_MACRO_SOURCE  # noqa: PLC0415
    from scripts.search_rag_primitive_pack import (SEARCH_ENGINE_SOURCE, LABELER_SOURCE,  # noqa: PLC0415
                                                   RAG_TOOL_SOURCE)
    import scripts.macro_crud_service as mc  # noqa: PLC0415
    verified = {  # verified, reusable modules — card-eligible (agent trusts the card, never re-reads the body)
        "webhook_worker.py": WEBHOOK_WORKER_MACRO_SOURCE, "search_engine.py": SEARCH_ENGINE_SOURCE,
        "labeler.py": LABELER_SOURCE, "rag_tool.py": RAG_TOOL_SOURCE, "crud_service.py": mc._MACRO_CRUD,
    }
    ws = {n: {"src": s, "verified": True} for n, s in verified.items()}
    # novel/business-specific code the DB can't cover — must stay RAW in context every turn
    ws["business_rules.py"] = {"src": "# task-specific business logic\n" + "def rule():\n    return 42\n" * 40,
                               "verified": False}
    ws["app_wiring.py"] = {"src": "# app-specific wiring the agent is actively editing\n" + "x = 1\n" * 60,
                           "verified": False}
    return ws


def _card(name: str, src: str) -> str:
    """A compact capability card for a verified module: name + a couple signatures + hash + one-line. ~1 line."""
    sigs = [ln.strip().rstrip(":") for ln in src.splitlines() if ln.startswith(("def ", "class "))][:3]
    h = hashlib.sha256(src.encode()).hexdigest()[:8]
    return f"# CARD {name} | verified {h} | {' ; '.join(sigs)} | mounted-verbatim-at-runtime"


def account(ws: dict[str, dict[str, Any]], *, turns: int, cards: bool) -> dict[str, Any]:
    """Cumulative INPUT tokens over `turns` turns. Every turn re-sends the whole context (realistic). With cards,
    verified modules are sent as compact cards; novel modules stay raw. Deterministic."""
    per_turn = 0
    for name, meta in ws.items():
        if cards and meta["verified"]:
            per_turn += _tok(_card(name, meta["src"]))
        else:
            per_turn += _tok(meta["src"])
    cumulative = [per_turn * (t + 1) for t in range(turns)]
    return {"per_turn_input_tokens": per_turn, "cumulative": cumulative, "total_input_tokens": per_turn * turns}


def analyze(turns: int = 50, verified_fraction: float | None = None) -> dict[str, Any]:
    ws = _real_working_set()
    if verified_fraction is not None:  # optionally re-tag to hit a target verified fraction (by module count)
        names = list(ws)
        k = round(verified_fraction * len(names))
        for i, n in enumerate(names):
            ws[n]["verified"] = i < k
    raw = account(ws, turns=turns, cards=False)
    card = account(ws, turns=turns, cards=True)
    saved = raw["total_input_tokens"] - card["total_input_tokens"]
    verified_bytes = sum(len(m["src"]) for m in ws.values() if m["verified"])
    total_bytes = sum(len(m["src"]) for m in ws.values())
    return {"record_type": "input_token_lever", "benchmark_kind": "structural_input_accounting", "turns": turns,
            "modules": len(ws), "verified_modules": sum(1 for m in ws.values() if m["verified"]),
            "verified_byte_fraction": round(verified_bytes / max(1, total_bytes), 3),
            "raw_total_input_tokens": raw["total_input_tokens"], "card_total_input_tokens": card["total_input_tokens"],
            "input_tokens_saved": saved,
            "input_reduction_pct": round(100 * saved / max(1, raw["total_input_tokens"]), 1),
            # re-read multiplier (#18): total content bytes sent across turns / unique content bytes
            "re_read_multiplier": turns,
            "curve_saved_by_turn": [raw["cumulative"][t] - card["cumulative"][t] for t in
                                    (0, min(9, turns - 1), min(24, turns - 1), turns - 1)],
            "note": "STRUCTURAL PROXY (chars/4 over real module sizes) — quantifies the INPUT-token lever the DB "
                    "unlocks; a live agent must still SUCCEED under card context (see realistic_session_harness).",
            **BOUNDARY}


def self_test() -> bool:
    """Mutation-gated + REAL (deterministic): (1) card context uses STRICTLY fewer input tokens than raw when there
    are verified modules; (2) the saving COMPOUNDS — savings after T turns strictly increases with T; (3) it scales
    with verified fraction (more verified → more saved); (4) mutation: cards-that-equal-raw yield 0 saving (caught);
    (5) deterministic."""
    a10 = analyze(turns=10)
    a50 = analyze(turns=50)
    assert a10["card_total_input_tokens"] < a10["raw_total_input_tokens"], "cards must reduce input tokens"
    assert a50["input_tokens_saved"] > a10["input_tokens_saved"], "input savings must COMPOUND with turns"
    # (3) more verified fraction -> more saved (at fixed turns)
    lo = analyze(turns=50, verified_fraction=0.3)["input_tokens_saved"]
    hi = analyze(turns=50, verified_fraction=0.9)["input_tokens_saved"]
    assert hi > lo, f"more verified modules must save more input tokens ({hi} vs {lo})"
    # (4) mutation: if cards were the full body (no compression), saving would be 0
    ws = _real_working_set()
    raw = account(ws, turns=50, cards=False)["total_input_tokens"]
    _g = globals()  # patch THIS module's global so account() sees it (works as __main__ or imported)
    _orig_card = _g["_card"]
    _g["_card"] = lambda name, src: src  # broken: "card" == raw body
    broken_saved = raw - account(ws, turns=50, cards=True)["total_input_tokens"]
    _g["_card"] = _orig_card
    assert broken_saved == 0, "mutation gate: a non-compressing card must yield 0 saving"
    # (5) determinism
    assert json.dumps(analyze(turns=25), sort_keys=True) == json.dumps(analyze(turns=25), sort_keys=True)

    print(f"OK input_token_lever self-test: over a {a50['modules']}-module working set "
          f"({a50['verified_modules']} verified, {a50['verified_byte_fraction']:.0%} of bytes), a 50-turn session "
          f"re-sends context 50× — replacing verified bodies with compact CARDS cuts INPUT tokens "
          f"{a50['raw_total_input_tokens']:,}→{a50['card_total_input_tokens']:,} ({a50['input_reduction_pct']}%, "
          f"{a50['input_tokens_saved']:,} saved); savings COMPOUND with turns (10-turn {a10['input_tokens_saved']:,} "
          f"< 50-turn {a50['input_tokens_saved']:,}) and with verified fraction; non-compressing card → 0 (caught); "
          f"deterministic. STRUCTURAL PROXY. serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Quantify the INPUT-token savings lever (card vs raw context re-read).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--turns", type=int, default=50)
    ap.add_argument("--verified-fraction", type=float, default=None)
    args = ap.parse_args()
    if args.self_test:
        raise SystemExit(0 if self_test() else 1)
    if args.report:
        rep = analyze(args.turns, args.verified_fraction)
        out = resource("data/dev-intel/input_token_lever"); out.mkdir(parents=True, exist_ok=True)
        (out / "report.json").write_text(json.dumps(rep, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(rep, indent=2, sort_keys=True))
        return
    ap.print_help()


if __name__ == "__main__":
    main()
