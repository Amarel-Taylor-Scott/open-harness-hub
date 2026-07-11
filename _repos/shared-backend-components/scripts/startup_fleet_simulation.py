#!/usr/bin/env python3
"""scripts.startup_fleet_simulation — THE 100-STARTUPS QUESTION: if 100 startups each build a SaaS/mobile app
in a NEW AND UNIQUE industry, what does the fleet spend on tokens building with OUR SYSTEM (retrieve → reuse →
compose over the primitive corpus; corpus-gap misses generated ONCE, then accreted as candidates) versus PURE
LLM GENERATION (every startup generates every component from scratch)?

Strategy zoo (a new build strategy = a new row):

  * pure_llm_generation — every requirement of every startup is generated: (prompt + generation) tokens ×
                          every startup. Nothing is ever reused across the fleet.
  * our_system_static   — retrieval over the corpus AS-IS: a VERIFIED hit costs 0 LLM tokens (the measured
                          deterministic retrieve+compose lane); a miss falls back to full generation. No
                          corpus accretion — isolates the value of the EXISTING corpus.
  * our_system_flywheel — like static, but every generated miss is APPENDED to the corpus as a CANDIDATE
                          (serves_truth=false, the factory funnel), so later startups HIT what earlier ones
                          paid to generate — cross-startup reuse compounding. The 100th startup builds its
                          shared core almost entirely from reuse.

GROUNDING, not hand-waving: the shared-core hit/miss per requirement is MEASURED once against the REAL corpus
via saas_requirements_bench.measure (verified hits only — an expected concept token must appear in a top-k
card). Unique-industry requirements are always-novel rows (a new industry's specifics cannot be in the corpus
yet). Generation size is a SWEEP over small/typical/complex components — the answer is a BAND, never one
magic number. Identical requirement phrasing across startups is a labelled simplification (the paraphrase
benches — semantic nDCG 0.86 vs lexical 0.60 — bound how much real-world phrasing drift costs).

serves_truth=false — simulated fleet economics are measurements over labelled assumptions, never truth.

    PYTHONPATH=. python3 scripts/startup_fleet_simulation.py --self-test
    PYTHONPATH=. python3 scripts/startup_fleet_simulation.py --run [--startups 100]
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any, Optional  # noqa: E402

from scripts import compose_token_bench as _ctb  # noqa: E402  REUSE: the ONE chars->proxy-token constant
from scripts import saas_requirements_bench as _saas  # noqa: E402  REUSE: suite + verified-hit measurement

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

#: per-component GENERATION size sweep (proxy tokens): small utility / typical component / complex
#: integration. A labelled assumption swept across its plausible range — no single point carries the claim.
_GEN_TOKENS_SWEEP: tuple[int, ...] = (500, 1500, 4000)
#: fixed prompt/context overhead per generation ask (requirement text rides on top, computed per row)
_PROMPT_CONTEXT_TOKENS = 200
_N_STARTUPS_DEFAULT = 100
#: industry-specific requirements per startup — "new and unique industry" means these are ALWAYS novel
_UNIQUE_PER_STARTUP = 15
#: the strategy zoo (a new build strategy = a new row)
STRATEGIES: tuple[str, ...] = ("pure_llm_generation", "our_system_static", "our_system_flywheel")


def _prompt_tokens(query: str) -> float:
    """Proxy tokens to ASK for a component (requirement text + fixed context overhead)."""
    return len(query) / _ctb._CHARS_PER_TOKEN + _PROMPT_CONTEXT_TOKENS  # noqa: SLF001 — single-source constant


def fleet_costs(shared: list[dict[str, Any]], *, n_startups: int, gen_tokens: int,
                unique_per_startup: int = _UNIQUE_PER_STARTUP) -> dict[str, Any]:
    """Token accounting for the whole fleet under every strategy. ``shared`` rows carry {query, hit} — the
    MEASURED verified hit/miss of each shared-core requirement against the real corpus."""
    out: dict[str, Any] = {}
    unique_cost_each = unique_per_startup * (_prompt_tokens("an industry specific requirement") + gen_tokens)
    for strategy in STRATEGIES:
        accreted: set = set()
        per_startup: list[float] = []
        for _i in range(n_startups):
            cost = unique_cost_each  # every strategy pays for genuinely-novel industry specifics
            for req in shared:
                ask = _prompt_tokens(req["query"]) + gen_tokens
                if strategy == "pure_llm_generation":
                    cost += ask
                else:
                    known = req["hit"] or (strategy == "our_system_flywheel" and req["query"] in accreted)
                    if not known:
                        cost += ask
                        if strategy == "our_system_flywheel":
                            accreted.add(req["query"])
            per_startup.append(round(cost, 1))
        total = round(sum(per_startup), 1)
        out[strategy] = {"fleet_total_proxy_tokens": total,
                         "mean_per_startup": round(total / n_startups, 1),
                         "first_startup": per_startup[0], "last_startup": per_startup[-1],
                         "flywheel_decay_first_to_last": round(
                             1.0 - (per_startup[-1] / per_startup[0]), 4) if per_startup[0] else 0.0}
    pure = out["pure_llm_generation"]["fleet_total_proxy_tokens"]
    for strategy in STRATEGIES:
        tot = out[strategy]["fleet_total_proxy_tokens"]
        out[strategy]["savings_vs_pure_llm"] = round(1.0 - tot / pure, 4) if pure else 0.0
    return out


def simulate_fleet(cards: list[dict[str, Any]], suite: list[dict[str, Any]], *,
                   n_startups: int = _N_STARTUPS_DEFAULT, k: int = 5) -> dict[str, Any]:
    """Measure the shared core ONCE against the real corpus (verified hits), then account the fleet across
    the generation-size sweep."""
    measured = _saas.measure(cards, suite, k=k)
    uncovered = {(m["category"], m["query"]) for m in measured["uncovered_requirements"]}
    shared = [{"query": r["query"], "category": r["category"],
               "hit": (r["category"], r["query"]) not in uncovered} for r in suite]
    hit_rate = sum(1 for r in shared if r["hit"]) / len(shared) if shared else 0.0
    sweep = {f"gen_{g}_tokens": fleet_costs(shared, n_startups=n_startups, gen_tokens=g)
             for g in _GEN_TOKENS_SWEEP}
    return {"record_type": "startup_fleet_simulation", "startups": n_startups,
            "shared_requirements": len(shared), "unique_requirements_per_startup": _UNIQUE_PER_STARTUP,
            "measured_shared_hit_rate": round(hit_rate, 4),
            "corpus_cards": len(cards), "k": k,
            "generation_sweep": sweep,
            "assumptions": {"gen_tokens_sweep": list(_GEN_TOKENS_SWEEP),
                            "prompt_context_tokens": _PROMPT_CONTEXT_TOKENS,
                            "identical_phrasing_note":
                                "shared requirements share phrasing across startups (optimistic for reuse); "
                                "the paraphrase benches (semantic nDCG 0.86 vs lexical 0.60) bound real "
                                "phrasing drift; verified hits only — a hit means a top-k card carries the "
                                "requirement's concept token, never 'returned something'."},
            "note": "our-system hits cost 0 LLM tokens (the measured deterministic retrieve+compose lane); "
                    "misses cost full generation, and under the flywheel strategy each miss is paid ONCE "
                    "fleet-wide (accreted as a candidate, factory funnel governs promotion).", **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    # hermetic grounding: a tiny corpus where 2 of 3 shared requirements verifiably HIT and 1 MISSES
    cards = [
        {"primitive_id": "f:oauth", "title": "OAuth login flow handler",
         "blackbox": "Handle the oauth authorization code flow and issue a session token.",
         "input_edge": "AuthCallback", "output_edge": "SessionToken", **BOUNDARY},
        {"primitive_id": "f:stripe", "title": "Subscription billing processor",
         "blackbox": "Create stripe subscription invoices with dunning retries.",
         "input_edge": "SubscriptionChange", "output_edge": "Invoice", **BOUNDARY},
    ]
    suite = [
        {"category": "auth", "requirement": "social login", "query": "let users sign in with google",
         "expected_tokens": ["oauth"]},
        {"category": "billing", "requirement": "subscriptions", "query": "charge customers monthly",
         "expected_tokens": ["stripe", "subscription"]},
        {"category": "search", "requirement": "full-text search", "query": "search all my documents",
         "expected_tokens": ["elasticsearch", "fulltext"]},  # a real corpus gap
    ]
    rec = simulate_fleet(cards, suite, n_startups=3, k=2)
    checks.append(("the shared hit rate is MEASURED (2 of 3 requirements verifiably hit)",
                   abs(rec["measured_shared_hit_rate"] - 2 / 3) < 1e-3))  # receipt rounds to 4 decimals
    g = rec["generation_sweep"][f"gen_{_GEN_TOKENS_SWEEP[0]}_tokens"]
    # (a) ordering: pure > static > flywheel, at every sweep level
    checks.append(("pure LLM generation costs the most; the flywheel costs the least (every sweep level)",
                   all(gg["pure_llm_generation"]["fleet_total_proxy_tokens"]
                       > gg["our_system_static"]["fleet_total_proxy_tokens"]
                       >= gg["our_system_flywheel"]["fleet_total_proxy_tokens"]
                       for gg in rec["generation_sweep"].values())))
    # (b) the flywheel compounds: the LAST startup builds its shared core cheaper than the FIRST;
    #     the static strategy is flat (every startup pays the same misses)
    checks.append(("the flywheel makes the last startup cheaper than the first (compounding reuse)",
                   g["our_system_flywheel"]["last_startup"] < g["our_system_flywheel"]["first_startup"]))
    checks.append(("the static strategy is flat per startup (no accretion) and pure is flat by construction",
                   g["our_system_static"]["first_startup"] == g["our_system_static"]["last_startup"]
                   and g["pure_llm_generation"]["first_startup"] == g["pure_llm_generation"]["last_startup"]))
    # (c) the miss is paid exactly ONCE fleet-wide under the flywheel: total_flywheel == total_static minus
    #     (n-1) repeat payments of the one missed shared requirement
    miss_ask = _prompt_tokens(suite[2]["query"]) + _GEN_TOKENS_SWEEP[0]
    expected_delta = round(2 * miss_ask, 1)  # 3 startups -> 2 repeat payments avoided
    actual_delta = round(g["our_system_static"]["fleet_total_proxy_tokens"]
                         - g["our_system_flywheel"]["fleet_total_proxy_tokens"], 1)
    checks.append(("a corpus-gap miss is paid exactly once fleet-wide under the flywheel (accounting exact)",
                   abs(actual_delta - expected_delta) < 0.5))
    # (d) savings are reported vs pure; unique-industry work is paid by EVERY strategy (nothing hidden)
    checks.append(("savings ratios are computed vs pure and unique-industry work is never waived",
                   0.0 < g["our_system_flywheel"]["savings_vs_pure_llm"] < 1.0
                   and all(v["fleet_total_proxy_tokens"] > 0 for v in g.values())))
    # (e) determinism + governance
    checks.append(("the simulation is deterministic (byte-identical twice)",
                   json.dumps(simulate_fleet(cards, suite, n_startups=3, k=2), sort_keys=True)
                   == json.dumps(simulate_fleet(cards, suite, n_startups=3, k=2), sort_keys=True)))
    checks.append(("receipt is candidate/serves_truth=false", rec["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - startup_fleet_simulation: the 100-startups question answered with MEASURED grounding — "
          "shared-core hits verified against the corpus, misses generated once under the flywheel (exact "
          "accounting proven), unique-industry work always paid, generation size swept (a band, not a magic "
          "number), pure > static >= flywheel at every level, deterministic receipts. serves_truth=false.")
    return 0


def _run(n_startups: int) -> int:
    from scripts import path_graph_bench as _bench  # noqa: PLC0415  REUSE: the corpus loader
    suite = _saas.load_suite()
    if not suite:
        print(f"no suite at {_saas.suite_path()} — write the requirement rows first")
        return 1
    cards = _bench._load_scale_corpus(None)  # noqa: SLF001
    print(f"simulating {n_startups} startups x ({len(suite)} shared + {_UNIQUE_PER_STARTUP} unique) "
          f"requirements over {len(cards)} cards ...")
    rec = simulate_fleet(cards, suite, n_startups=n_startups)
    out = resource("data") / "dev-intel" / "session_emulation" / "startup_fleet_receipt.json"
    out.write_text(json.dumps(rec, indent=2, sort_keys=True))
    print(json.dumps({"measured_shared_hit_rate": rec["measured_shared_hit_rate"],
                      "generation_sweep": {gk: {s: {"fleet_total_proxy_tokens": v["fleet_total_proxy_tokens"],
                                                    "savings_vs_pure_llm": v["savings_vs_pure_llm"]}
                                                for s, v in gv.items()}
                                           for gk, gv in rec["generation_sweep"].items()}},
                     indent=2, sort_keys=True))
    print(f"\nwritten: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true", help="the 100-startups comparison over the real corpus")
    ap.add_argument("--startups", type=int, default=_N_STARTUPS_DEFAULT)
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        return _run(args.startups)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
