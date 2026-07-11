#!/usr/bin/env python3
"""scripts.dev_session_simulation — REAL coding sessions, not single prompts: a developer session is a
BACK-AND-FORTH trajectory (initial ask → clarify → add feature → bug report → REMIX pieces together → tests →
UI polish), and the cost structure that matters is CONTEXT COMPOUNDING — in a pure-LLM session every turn
re-sends the growing history, so turn N pays for turns 1..N-1 again. This module builds deterministic
multi-turn sessions from the scenario axes, replays them under a HARNESS-MODE zoo, and accounts tokens
per TURN — simulated (proxy, anchored to the measured 600-token real generation size) and REAL (actual
multi-turn Ollama conversations where prompt_eval_count visibly grows every turn).

Harness modes (a new mode = a new row):

  * pure_llm     — every turn goes to the model with the FULL conversation history (the compounding baseline).
  * our_harness  — every turn first hits the 0-token lanes: verified RETRIEVAL for build asks, the COMPOSE
                   engines for remix turns, the results CACHE for repeats; only uncovered turns escalate to
                   the model — and an escalated turn sends a COMPACT context (the turn + retrieved
                   signatures), never the whole history, because the harness holds session state itself.

Every session records its per-turn TOOL TRACE (retrieve / compose / cache / llm-escalate) and is persisted as
a developer-example transcript (`dev_session_examples.jsonl`). Turn utterances are realistic templates over
the scenario axes (domains × artifacts × capabilities incl. the UI/UX rows). serves_truth=false throughout.

    PYTHONPATH=. python3 scripts/dev_session_simulation.py --self-test
    PYTHONPATH=. python3 scripts/dev_session_simulation.py --run [--sessions 200]      # simulated at scale
    PYTHONPATH=. python3 scripts/dev_session_simulation.py --run-real [--sessions 2]   # REAL multi-turn calls
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
import os  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

from scripts import build_scenario_corpus as _scen  # noqa: E402  REUSE: the axes (domains/artifacts/capabilities)
from scripts import compose_token_bench as _ctb  # noqa: E402  REUSE: the ONE chars->proxy-token constant
from scripts import pipeline_path_graph as _graph  # noqa: E402  REUSE: run_path (retrieve + compose engines)
from scripts.saas_requirements_bench import _verified_hit  # noqa: E402  REUSE: the one verified-hit gate

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

#: generation size per assistant reply — anchored to the MEASURED real receipts (both cloud models saturated
#: the 600-token cap on every one of 144 real calls), not a guess.
_GEN_TOKENS = 600
_SYSTEM_TOKENS = 120          # fixed system-prompt overhead per LLM call (labelled)
_SIGNATURE_CONTEXT_TOKENS = 160  # compact escalation context: the retrieved signature layer (measured scale)
_EXAMPLES_FILENAME = "dev_session_examples.jsonl"

#: SESSION ARCHETYPES — a zoo of realistic turn-type trajectories (a new archetype = a new row)
SESSION_ARCHETYPES: dict[str, tuple[str, ...]] = {
    "feature_build": ("initial_ask", "add_feature", "refine", "add_feature", "bug_report",
                      "test_ask", "remix", "ui_polish"),
    "debug_heavy": ("initial_ask", "bug_report", "refine", "bug_report", "test_ask", "add_feature"),
    "compose_explore": ("initial_ask", "clarify", "remix", "add_feature", "remix", "repeat_ask"),
    "ui_iteration": ("initial_ask", "ui_polish", "refine", "ui_polish", "add_feature", "repeat_ask",
                     "test_ask"),
    # ── added archetypes (zoo-of-zoos: rows APPENDED below, none above rewritten) ────────────────────────────
    "greenfield_sprint": ("initial_ask", "clarify", "add_feature", "add_feature", "remix", "test_ask",
                          "deploy_ask", "docs_ask"),
    "legacy_refactor": ("refactor_ask", "cleanup_ask", "refine", "compare_ask", "test_ask", "review_ask"),
    "perf_hunt": ("perf_ask", "clarify", "compare_ask", "refine", "scale_ask", "test_ask", "monitor_ask"),
    "security_review": ("security_ask", "bug_report", "refine", "test_ask", "review_ask", "docs_ask"),
    "data_migration": ("migrate_ask", "clarify", "add_feature", "bug_report", "rollback_ask", "test_ask",
                       "deploy_ask"),
    "api_integration": ("integrate_ask", "clarify", "add_feature", "bug_report", "test_ask", "docs_ask",
                        "deploy_ask"),
    "mobile_port": ("port_ask", "clarify", "ui_polish", "bug_report", "refine", "test_ask", "ui_polish"),
    "agent_build": ("agent_ask", "clarify", "integrate_ask", "add_feature", "compare_ask", "remix",
                    "bug_report", "test_ask", "monitor_ask"),
    "incident_response": ("incident_ask", "clarify", "rollback_ask", "bug_report", "test_ask", "monitor_ask",
                          "docs_ask"),
    "prototype_to_prod": ("initial_ask", "add_feature", "cleanup_ask", "security_ask", "scale_ask",
                          "test_ask", "deploy_ask", "monitor_ask", "docs_ask"),
    "docs_pass": ("docs_ask", "clarify", "docs_ask", "refine", "docs_ask", "review_ask"),
    "review_iteration": ("review_ask", "refine", "cleanup_ask", "compare_ask", "test_ask", "review_ask"),
    "dependency_upgrade": ("upgrade_ask", "bug_report", "refine", "rollback_ask", "cleanup_ask", "test_ask"),
    "ab_test_setup": ("compare_ask", "add_feature", "deploy_ask", "monitor_ask", "refine", "test_ask"),
}

#: TURN TEMPLATES — {cap}/{cap2} capabilities, {dom} domain, {art} artifact. Deterministic realistic phrasing.
_TURN_TEMPLATES: dict[str, str] = {
    "initial_ask": "i'm building a {art} for {dom} — start with {cap}",
    "clarify": "to be clear, the {cap} part should work for {dom} teams specifically",
    "add_feature": "great, now add {cap2} to it",
    "refine": "make the {cap} part configurable instead of hardcoded",
    "bug_report": "the {cap} flow throws on empty input, can you fix that",
    "test_ask": "write tests covering the {cap} happy path and the empty-input case",
    "remix": "combine the {cap} piece and the {cap2} piece into one flow",
    "ui_polish": "polish the ui: {cap2} with sensible defaults",
    "repeat_ask": "i'm building a {art} for {dom} — start with {cap}",  # an EXACT repeat (cache candidate)
    # ── added turn types (each appears in >=1 archetype; the no-orphan self-test check enforces it) ──────────
    "perf_ask": "the {cap} endpoint is slow under load, profile and speed it up",
    "security_ask": "security-review the {cap} flow: injection, secrets in logs, and {dom} access control",
    "migrate_ask": "migrate the {dom} data behind {cap} to the new schema with a reversible backfill",
    "integrate_ask": "integrate the {art} with the external {cap2} service — wire {cap} through its api",
    "deploy_ask": "deploy the {art} to staging with {cap} behind a feature flag and a canary",
    "docs_ask": "write docs for the {art}: a {dom} quickstart for {cap} plus an api reference for {cap2}",
    "rollback_ask": "that broke prod, roll {cap} back and add a guard",
    "compare_ask": "should we use {cap} or {cap2} here — pick one and wire it",
    "scale_ask": "the {art} needs to handle 10x {dom} traffic — make {cap} scale horizontally",
    "cleanup_ask": "clean up the {cap} module: dead code, stray todos, and duplicated helpers",
    "upgrade_ask": "bump the {cap2} dependency that {cap} uses to the latest major and fix the breakage",
    "review_ask": "address the review comments on the {cap} change: better names and smaller functions",
    "monitor_ask": "add metrics and alerts around {cap} so {dom} failures page us early",
    "port_ask": "port the {cap} screen of the {art} to mobile, same behavior on both",
    "refactor_ask": "the {art} for {dom} has grown crufty — refactor the {cap} module without changing behavior",
    "incident_ask": "prod is down for {dom} users — the {art} is failing in {cap}, triage it now",
    "agent_ask": "build an llm agent for {dom} that plans, calls {cap} as a tool, and retries on failure",
}
#: turn types whose {cap2} should draw from the UI/UX capability rows
_UI_TURNS = frozenset({"ui_polish"})
#: turn types whose MEASURED capability is {cap2} — ONE definition keeps the {cap2} pool choice and the
#: target mapping coherent (a future _UI_TURNS row gets its pool AND its target from here, never from a
#: second hand-typed literal that can drift)
_CAP2_TARGET_TURNS: frozenset[str] = frozenset({"add_feature"}) | _UI_TURNS
#: the UI/UX capability rows the _UI_TURNS {cap2} pool draws from. Single-source preference: this consumes
#: build_scenario_corpus._UI_CAPABILITIES the moment the axes module grows that name (ownership: that file
#: is edited by its own lane, so the name is deferred to, never redefined over there from here); until then
#: this mirror is DRIFT-GATED by the self-test — every row must resolve in _scen._CAPABILITIES and the pool
#: filter must find ALL of them — so an axes rename goes RED here instead of silently widening the pool.
_UI_CAPABILITIES: tuple[str, ...] = tuple(getattr(_scen, "_UI_CAPABILITIES", (
    "responsive page layout", "dark mode theming", "accessible components", "design token system",
    "reusable component library", "data table with sorting", "drag and drop editor",
    "empty states and loading skeletons", "guided product tour", "form ux with inline errors")))


def build_sessions(n_sessions: int) -> list[dict[str, Any]]:
    """Deterministic session scripts: stride the scenario axes; each turn carries its utterance, the
    capability it targets, and that capability's expected tokens (so coverage stays VERIFIED per turn)."""
    caps = sorted(_scen._CAPABILITIES)  # noqa: SLF001 — single-source axes
    ui_caps = [c for c in caps if c in frozenset(_UI_CAPABILITIES)] or caps
    archetypes = sorted(SESSION_ARCHETYPES)
    sessions: list[dict[str, Any]] = []
    for i in range(n_sessions):
        archetype = archetypes[i % len(archetypes)]
        dom = _scen._DOMAINS[i % len(_scen._DOMAINS)]  # noqa: SLF001
        art = _scen._ARTIFACTS[(i // len(_scen._DOMAINS)) % len(_scen._ARTIFACTS)]  # noqa: SLF001
        cap = caps[i % len(caps)]
        turns: list[dict[str, Any]] = []
        for t, turn_type in enumerate(SESSION_ARCHETYPES[archetype]):
            pool = ui_caps if turn_type in _UI_TURNS else caps
            cap2 = pool[(i + t) % len(pool)]
            if cap2 == cap and len(pool) > 1:  # deterministic collision guard — a turn never asks to add/
                cap2 = pool[(i + t + 1) % len(pool)]  # compare/integrate a capability WITH ITSELF
            target = cap2 if turn_type in _CAP2_TARGET_TURNS else cap
            utterance = _TURN_TEMPLATES[turn_type].format(cap=cap, cap2=cap2, dom=dom, art=art)
            turns.append({"turn_type": turn_type, "utterance": utterance, "capability": target,
                          "expected_tokens": list(_scen._CAPABILITIES[target])})  # noqa: SLF001
        sessions.append({"archetype": archetype, "domain": dom, "artifact": art, "turns": turns, **BOUNDARY})
    return sessions


def _tok(text: str) -> float:
    return len(text) / _ctb._CHARS_PER_TOKEN  # noqa: SLF001 — the ONE chars->token constant


# ── the 0-token harness lanes (REUSE the live engines; no placeholders) ───────────────────────────────────────
def _harness_serve(turn: dict[str, Any], cards: list[dict[str, Any]], index: Any,
                   cache: dict, results_cache: dict) -> dict[str, Any]:
    """Serve one turn through the deterministic lanes: cache -> retrieve (verified) -> compose for remix
    turns. Returns {covered, tool, top_ids}. Uncovered turns are the caller's LLM-escalation signal."""
    q = turn["utterance"]
    if q in results_cache:
        return {"covered": results_cache[q]["covered"], "tool": "cache", "top_ids": results_cache[q]["top_ids"]}
    compose_opt = "edge_chain" if turn["turn_type"] == "remix" else "skip"
    # the STORED semantic lane carries session volume (0.2s/turn at 112K); the full union's grains/
    # hierarchical sub-rows are O(N) per query and belong to offline benches, not the per-turn server
    fixed = {"analyze": "skip", "preprocess": "det_minimal", "expand": "none", "secondary": "none",
             "search": "semantic_embedding", "fuse": "combmnz", "rerank": "none", "compose": compose_opt}
    run = _graph.run_path(q, cards, fixed, index=index, cache=cache)
    by_id = {c.get("primitive_id"): c for c in cards}
    top = [by_id[r["primitive_id"]] for r in run["results"] if r.get("primitive_id") in by_id]
    covered = _verified_hit(top, turn["expected_tokens"])
    tool = ("compose" if compose_opt == "edge_chain" and (run.get("composition") or {}).get("pieces_wired")
            else "retrieve")
    out = {"covered": covered, "tool": tool, "top_ids": [c.get("primitive_id") for c in top[:5]]}
    results_cache[q] = out
    return out


# ── the HARNESS-MODE zoo ──────────────────────────────────────────────────────────────────────────────────────
def simulate_sessions(sessions: list[dict[str, Any]], cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Replay every session under both harness modes with per-turn proxy-token accounting (generation size
    anchored to the measured 600). Writes nothing; the caller persists transcripts + the receipt."""
    from scripts.build_primitive_search_index import build_index  # noqa: PLC0415
    index = build_index(cards)
    run_cache: dict = {}
    transcripts: list[dict[str, Any]] = []
    pure_total = ours_total = 0.0
    escalations = covered_turns = cache_hits = compose_turns = total_turns = 0
    first_turn_costs: list[float] = []
    last_turn_costs: list[float] = []
    for sess in sessions:
        results_cache: dict = {}
        history_tokens = float(_SYSTEM_TOKENS)
        turn_rows: list[dict[str, Any]] = []
        session_pure_costs: list[float] = []
        for turn in sess["turns"]:
            total_turns += 1
            ask = _tok(turn["utterance"])
            # PURE mode: full history re-sent, model generates, reply joins the history
            pure_cost = history_tokens + ask + _GEN_TOKENS
            session_pure_costs.append(pure_cost)
            pure_total += pure_cost
            history_tokens += ask + _GEN_TOKENS
            # OUR harness: deterministic lanes first; only uncovered turns escalate with COMPACT context
            served = _harness_serve(turn, cards, index, run_cache, results_cache)
            if served["tool"] == "cache":
                cache_hits += 1
            if served["tool"] == "compose":
                compose_turns += 1
            if served["covered"]:
                covered_turns += 1
                ours_cost = 0.0
            else:
                escalations += 1
                ours_cost = _SYSTEM_TOKENS + _SIGNATURE_CONTEXT_TOKENS + ask + _GEN_TOKENS
            ours_total += ours_cost
            turn_rows.append({"turn_type": turn["turn_type"], "utterance": turn["utterance"],
                              "tool": ("llm_escalate" if not served["covered"] else served["tool"]),
                              "covered": served["covered"], "top_ids": served["top_ids"],
                              "pure_cost_tokens": round(pure_cost, 1), "ours_cost_tokens": round(ours_cost, 1)})
        transcripts.append({"record_type": "dev_session_example", "archetype": sess["archetype"],
                            "domain": sess["domain"], "artifact": sess["artifact"], "turns": turn_rows,
                            **BOUNDARY})
        if session_pure_costs:
            first_turn_costs.append(session_pure_costs[0])
            last_turn_costs.append(session_pure_costs[-1])
    n = total_turns or 1
    # compounding is WITHIN a session (history resets per session): mean LAST-turn cost vs mean FIRST-turn cost
    compounding = (round((sum(last_turn_costs) / len(last_turn_costs))
                         / (sum(first_turn_costs) / len(first_turn_costs)), 2)
                   if first_turn_costs and sum(first_turn_costs) else 0.0)
    return {"record_type": "dev_session_simulation", "sessions": len(sessions), "turns": total_turns,
            "corpus_cards": len(cards), "gen_tokens_anchor": _GEN_TOKENS,
            "modes": {
                "pure_llm": {"total_proxy_tokens": round(pure_total, 0),
                             "mean_per_turn": round(pure_total / n, 1),
                             "context_compounding_last_vs_first_turn": compounding},
                "our_harness": {"total_proxy_tokens": round(ours_total, 0),
                                "mean_per_turn": round(ours_total / n, 1),
                                "covered_turn_rate": round(covered_turns / n, 4),
                                "llm_escalation_rate": round(escalations / n, 4),
                                "cache_hits": cache_hits, "compose_turns": compose_turns},
            },
            "savings_vs_pure": round(1.0 - ours_total / pure_total, 4) if pure_total else 0.0,
            "transcripts": transcripts,
            "note": "per-TURN accounting; pure mode re-sends the growing history every turn (the compounding "
                    "ratio shows late turns costing multiples of early ones); the harness holds session state "
                    "deterministically, serves covered turns from retrieve/compose/cache for 0 tokens, and "
                    "escalates uncovered turns with a COMPACT signature context. Generation size anchored to "
                    "the measured real 600. serves_truth=false.", **BOUNDARY}


# ── REAL mode: actual multi-turn conversations (context grows for real; counts from the API) ────────────────
def _chat_messages(model: str, messages: list[dict[str, str]], *, num_predict: int = _GEN_TOKENS,
                   timeout_s: float = 180.0) -> dict[str, Any]:
    import urllib.request  # noqa: PLC0415
    payload = json.dumps({"model": model, "stream": False, "messages": messages,
                          "options": {"num_predict": num_predict}}).encode()
    base = os.environ.get("OH_OLLAMA_BASE", "http://127.0.0.1:11434")
    attempts = [(f"{base}/api/chat", {})]
    key = os.environ.get("OLLAMA_API_KEY", "")
    if key:
        attempts.append((f"{os.environ.get('OH_OLLAMA_CLOUD_BASE', 'https://ollama.com')}/api/chat",
                         {"Authorization": f"Bearer {key}"}))
    last = ""
    for url, extra in attempts:
        try:
            req = urllib.request.Request(url, data=payload,
                                         headers={"Content-Type": "application/json", **extra})
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # noqa: S310 — opt-in lane
                data = json.loads(resp.read())
            return {"ok": True, "tokens_in": int(data.get("prompt_eval_count") or 0),
                    "tokens_out": int(data.get("eval_count") or 0),
                    "reply": str((data.get("message") or {}).get("content") or "")}
        except Exception as exc:  # noqa: BLE001
            last = f"{type(exc).__name__}: {exc}"
    return {"ok": False, "tokens_in": 0, "tokens_out": 0, "reply": "", "error": last[:200]}


def run_real_sessions(sessions: list[dict[str, Any]], cards: list[dict[str, Any]], models: list[str],
                      *, transport: Optional[Callable[..., dict[str, Any]]] = None) -> dict[str, Any]:
    """REAL back-and-forth: pure mode maintains the actual messages array (watch prompt_eval_count grow turn
    by turn); our harness only calls on uncovered turns, with a compact 2-message context."""
    from scripts.build_primitive_search_index import build_index  # noqa: PLC0415
    call = transport or _chat_messages
    index = build_index(cards)
    run_cache: dict = {}
    per_model: dict[str, Any] = {}
    for model in models:
        pure_total = ours_total = failures = 0
        session_rows: list[dict[str, Any]] = []
        for sess in sessions:
            results_cache: dict = {}
            messages = [{"role": "system", "content": "You are a senior engineer pair-programming; be concise."}]
            per_turn: list[dict[str, Any]] = []
            for turn in sess["turns"]:
                messages.append({"role": "user", "content": turn["utterance"]})
                r = call(model, messages)
                if not r["ok"]:
                    failures += 1
                    messages.pop()
                    continue
                pure_total += r["tokens_in"] + r["tokens_out"]
                messages.append({"role": "assistant", "content": r["reply"]})
                served = _harness_serve(turn, cards, index, run_cache, results_cache)
                ours_turn = 0
                if not served["covered"]:
                    compact = [{"role": "system",
                                "content": "You are a senior engineer. Relevant primitives: "
                                           + ", ".join(map(str, served["top_ids"]))},
                               {"role": "user", "content": turn["utterance"]}]
                    r2 = call(model, compact)
                    if r2["ok"]:
                        ours_turn = r2["tokens_in"] + r2["tokens_out"]
                    else:
                        failures += 1
                ours_total += ours_turn
                per_turn.append({"turn_type": turn["turn_type"], "pure_tokens_in": r["tokens_in"],
                                 "pure_tokens_out": r["tokens_out"], "covered": served["covered"],
                                 "ours_tokens": ours_turn, "tool": served["tool"]})
            session_rows.append({"archetype": sess["archetype"], "turns": per_turn})
        per_model[model] = {"real_tokens_pure_session": pure_total, "real_tokens_our_harness": ours_total,
                            "real_savings": round(1.0 - ours_total / pure_total, 4) if pure_total else None,
                            "failed_calls": failures, "sessions": session_rows}
    return {"record_type": "real_dev_session_benchmark", "models": models, "sessions": len(sessions),
            "per_model": per_model,
            "note": "REAL multi-turn conversations: pure mode's prompt_eval_count grows every turn (context "
                    "compounding measured, not asserted); the harness calls only on uncovered turns with a "
                    "compact context. Failures recorded, never fabricated.", **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    n_sessions = len(SESSION_ARCHETYPES)  # one session per archetype — the count is computed, never typed
    sessions = build_sessions(n_sessions)
    checks.append(("sessions are deterministic, multi-turn, and span every archetype",
                   sessions == build_sessions(n_sessions)
                   and {s["archetype"] for s in sessions} == set(SESSION_ARCHETYPES)
                   and all(len(s["turns"]) >= 6 for s in sessions)))
    # capability phrases are multi-word and never substrings of each other (verified over the axes), so a
    # target-capability count >= 2 in one utterance is EXACTLY the self-referential degeneracy signal
    # ("should we use X or X here"); pre-guard this failed at t=0 for compare/upgrade/docs/integrate asks.
    checks.append(("no degenerate self-referential turns: cap2 never collapses onto the session cap",
                   all(t["utterance"].count(t["capability"]) < 2 for s in sessions for t in s["turns"])))
    ui_caps_probe = [c for c in sorted(_scen._CAPABILITIES) if c in frozenset(_UI_CAPABILITIES)]  # noqa: SLF001
    checks.append(("the UI {cap2} pool single-sources against the axes: every UI row resolves in "
                   "_CAPABILITIES and the silent or-caps fallback never triggers",
                   set(_UI_CAPABILITIES) <= set(_scen._CAPABILITIES)  # noqa: SLF001
                   and len(ui_caps_probe) == len(_UI_CAPABILITIES) > 1))
    used_turn_types = {turn_type for trajectory in SESSION_ARCHETYPES.values() for turn_type in trajectory}
    checks.append(("no orphan turn templates: every _TURN_TEMPLATES type appears in >=1 archetype (and vice versa)",
                   used_turn_types == set(_TURN_TEMPLATES)))
    checks.append(("zoo scale floors hold: >=14 archetypes, each a realistic 6-12 turn trajectory",
                   len(SESSION_ARCHETYPES) >= 14  # spec floors (thresholds, not mirrored repo-state counts)
                   and all(6 <= len(trajectory) <= 12 for trajectory in SESSION_ARCHETYPES.values())))
    # hermetic corpus: covers auth-ish capabilities so SOME turns hit and others honestly miss
    cards = [{"primitive_id": f"d:{t}", "title": f"{t} component",
              "blackbox": f"Provides {t} with {' '.join(_scen._CAPABILITIES[t][:3])} support.",  # noqa: SLF001
              "input_edge": "In", "output_edge": "Out", **BOUNDARY}
             for t in list(sorted(_scen._CAPABILITIES))[:12]]  # noqa: SLF001
    rec = simulate_sessions(sessions, cards)
    pure, ours = rec["modes"]["pure_llm"], rec["modes"]["our_harness"]
    checks.append(("CONTEXT COMPOUNDING is real: a session's LAST turn costs a multiple of its FIRST",
                   pure["context_compounding_last_vs_first_turn"] > 3.0))
    checks.append(("the harness beats pure back-and-forth (covered turns cost 0, escalations are compact)",
                   ours["total_proxy_tokens"] < pure["total_proxy_tokens"] and 0 < rec["savings_vs_pure"] < 1))
    checks.append(("coverage + escalation are both nonzero (honest mix, nothing waived or faked)",
                   ours["covered_turn_rate"] > 0 and ours["llm_escalation_rate"] > 0))
    checks.append(("repeat turns hit the session cache and remix turns exercise the compose engine",
                   ours["cache_hits"] >= 1 and ours["compose_turns"] >= 1))
    checks.append(("the tool trace exercises ALL four lanes (retrieve/compose/cache/llm_escalate)",
                   {t["tool"] for s in rec["transcripts"] for t in s["turns"]}
                   == {"retrieve", "compose", "cache", "llm_escalate"}))
    checks.append(("simulation is deterministic (byte-identical twice)",
                   json.dumps(simulate_sessions(sessions, cards), sort_keys=True)
                   == json.dumps(simulate_sessions(sessions, cards), sort_keys=True)))
    # REAL mode plumbing, hermetically: a stub transport with GROWING tokens_in proves the wiring
    calls_seen: list[int] = []

    def _stub(model: str, messages: list, **_kw: Any) -> dict[str, Any]:
        tokens_in = sum(len(m["content"]) for m in messages) // 4
        calls_seen.append(tokens_in)
        return {"ok": True, "tokens_in": tokens_in, "tokens_out": 50, "reply": "done: " + messages[-1]["content"][:40]}

    rreal = run_real_sessions(sessions[:2], cards, ["stub-model"], transport=_stub)
    sm = rreal["per_model"]["stub-model"]
    pure_ins = [t["pure_tokens_in"] for s in sm["sessions"] for t in s["turns"]]
    uncovered_real_turns = sum(1 for s in sm["sessions"] for t in s["turns"] if not t["covered"])
    checks.append(("real-mode pure conversations grow their context turn over turn AND the transport call "
                   "count reconciles (one pure call per turn + one compact call per uncovered turn)",
                   len(pure_ins) >= 6 and pure_ins[-1] > pure_ins[0] and sm["failed_calls"] == 0
                   and len(calls_seen) == len(pure_ins) + uncovered_real_turns))
    checks.append(("real-mode harness spends only on uncovered turns and never fabricates",
                   sm["real_tokens_our_harness"] < sm["real_tokens_pure_session"]
                   and all(t["ours_tokens"] == 0 for s in sm["sessions"] for t in s["turns"] if t["covered"])
                   and all(t["ours_tokens"] > 0
                           for s in sm["sessions"] for t in s["turns"] if not t["covered"])))
    checks.append(("receipts are candidate/serves_truth=false",
                   rec["serves_truth"] is False and rreal["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    turn_lengths = sorted(len(trajectory) for trajectory in SESSION_ARCHETYPES.values())
    print(f"\nPASS - dev_session_simulation: {len(SESSION_ARCHETYPES)} session archetypes of real back-and-forth "
          f"({turn_lengths[0]}-{turn_lengths[-1]} turns over {len(_TURN_TEMPLATES)} turn templates: ask/refine/"
          f"bug/test/REMIX/UI-polish plus perf/security/migrate/integrate/deploy/docs/rollback/compare/scale/"
          f"cleanup/upgrade/review/monitor/port/refactor/incident/agent), replayed under the harness-mode zoo — context "
          f"compounding proven in pure mode, the harness serves covered turns for 0 via retrieve/compose/cache "
          f"and escalates compactly, per-turn tool traces persisted as developer examples, real multi-turn "
          f"plumbing verified via injected transport. serves_truth=false.")
    return 0


def _persist(rec: dict[str, Any], receipt_name: str) -> Path:
    out_dir = resource("data") / "dev-intel" / "session_emulation"
    transcripts = rec.pop("transcripts", None)
    if transcripts is not None:
        with (out_dir / _EXAMPLES_FILENAME).open("w", encoding="utf-8") as fh:
            for t in transcripts:
                fh.write(json.dumps(t, sort_keys=True) + "\n")
        rec["examples_written"] = len(transcripts)
        rec["examples_path"] = str(out_dir / _EXAMPLES_FILENAME)
    out = out_dir / receipt_name
    out.write_text(json.dumps(rec, indent=2, sort_keys=True))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true", help="simulated sessions at scale over the real corpus")
    ap.add_argument("--run-real", action="store_true", help="REAL multi-turn Ollama conversations")
    ap.add_argument("--sessions", type=int, default=200)
    ap.add_argument("--models", default=os.environ.get("OH_REAL_GEN_MODELS", "glm-5.2:cloud,kimi-k2.5:cloud"))
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run or args.run_real:
        from scripts import path_graph_bench as _bench  # noqa: PLC0415
        cards = _bench._load_scale_corpus(None)  # noqa: SLF001
        if args.run:
            sessions = build_sessions(args.sessions)
            print(f"simulating {len(sessions)} sessions (~{sum(len(s['turns']) for s in sessions)} turns) "
                  f"over {len(cards)} cards ...")
            rec = simulate_sessions(sessions, cards)
            out = _persist(rec, "dev_session_receipt.json")
            print(json.dumps({k: rec[k] for k in ("sessions", "turns", "modes", "savings_vs_pure")},
                             indent=2, sort_keys=True))
            print(f"\nwritten: {out}")
            return 0
        sessions = build_sessions(args.sessions)
        models = [m.strip() for m in args.models.split(",") if m.strip()]
        print(f"REAL sessions: {len(sessions)} x {len(models)} models, multi-turn ...")
        rec = run_real_sessions(sessions, cards, models)
        out = _persist(rec, "real_dev_session_receipt.json")
        slim = {m: {k: v for k, v in d.items() if k != "sessions"} for m, d in rec["per_model"].items()}
        print(json.dumps(slim, indent=2, sort_keys=True))
        print(f"\nwritten: {out}")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
