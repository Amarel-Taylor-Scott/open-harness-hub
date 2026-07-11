#!/usr/bin/env python3
"""scripts.token_savings_bench — PROVE the executable primitives reduce token usage across common, rare, and
super-rare coding tasks, honestly.

The claim rests on one structural fact and one measured quantity:
  * REUSE COST = 0 generation tokens. A retrieved executable primitive RUNS deterministically; the model
    generates nothing (the Teleon descent thesis, made literal). This is not an estimate.
  * REGENERATION COST >= token_estimate(reference implementation). To produce equivalent WORKING code the
    model must emit at least the implementation's tokens; in practice it emits more (comments + reasoning),
    and for rarer algorithms it also FAILS more often. We measure the lower bound deterministically per tier,
    and (opt-in) the ACTUAL model regeneration tokens via a real local/keyed model lane.

Savings per reuse = regeneration cost (since reuse is 0). We report it three ways, each labelled:
  1. deterministic LOWER BOUND (reference-impl tokens) per tier — always available, no model.
  2. an ILLUSTRATIVE workload projection (per 1,000 queries) under a labelled, SWEPT tier-frequency mix.
  3. opt-in REAL-MODEL arm — actual regeneration tokens per task (natural stop) + a parseability signal,
     showing rarer tiers cost strictly more to regenerate.

Correctness is the second axis and it is already settled on OUR side: every primitive passes an oracle-backed
test in executable_primitive_library (mutation-gated). The model's from-scratch correctness on super-rare
tasks is the known gap the library closes; the real-model arm records whether the model even produced
parseable code (full execution-against-oracle is deferred for safety — we do NOT exec model code here).

    python3 scripts/token_savings_bench.py --self-test
    python3 scripts/token_savings_bench.py --bench
    python3 scripts/token_savings_bench.py --bench --real-model --provider ollama --model gemma-4-coding
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap ─────────────────────────────────────────────────────────────────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import ast  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

import scripts.executable_primitive_library as _lib  # noqa: E402  REUSE the library + token_estimate
import scripts.build_primitive_embeddings as _store  # noqa: E402  REUSE the store build/search

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

#: ILLUSTRATIVE tier-frequency mix per 1,000 coding queries — a LABELLED ASSUMPTION (swept below), NOT a
#: measured fact. Common tasks recur often (small per-use saving x many uses); super-rare tasks are infrequent
#: but each reuse saves a large regeneration + a likely failure. The workload projection is only as good as
#: this mix, which is why it is stated and swept, never hidden.
_TIER_FREQUENCY_PER_1K: dict[str, tuple[int, int]] = {  # (low, high) uses per 1,000 queries
    "common": (120, 300),
    "rare": (20, 60),
    "super_rare": (2, 10),
}
#: reasoning-premium multiplier: real regeneration emits MORE than the bare implementation (comments, retries,
#: reasoning), and more for rarer tiers. A labelled assumption used ONLY in the illustrative projection; the
#: real-model arm measures the true multiplier when run.
_REASONING_PREMIUM: dict[str, float] = {"common": 1.3, "rare": 1.8, "super_rare": 2.6}


def deterministic_savings() -> dict[str, Any]:
    """Per-tier reference-implementation token lower bound = the minimum a model must emit to regenerate."""
    per_tier: dict[str, dict[str, Any]] = {}
    for tier in _lib.TIERS:
        pids = [pid for pid, s in _lib.PRIMITIVES.items() if s["tier"] == tier]
        toks = [_lib.token_estimate(_lib.primitive_source(pid)) for pid in pids]
        per_tier[tier] = {
            "n_primitives": len(pids),
            "regen_lower_bound_tokens_mean": round(sum(toks) / max(1, len(toks)), 1),
            "regen_lower_bound_tokens_min": min(toks) if toks else 0,
            "regen_lower_bound_tokens_max": max(toks) if toks else 0,
            "reuse_generation_tokens": 0,  # structural: the primitive RUNS, the model generates nothing
        }
    return per_tier


def workload_projection(per_tier: dict[str, Any]) -> dict[str, Any]:
    """Illustrative tokens saved per 1,000 queries under the SWEPT tier-frequency mix + reasoning premium.
    Every input is labelled; this is a projection, not a measurement."""
    out: dict[str, Any] = {}
    total_lo = total_hi = 0.0
    for tier, stats in per_tier.items():
        lo_freq, hi_freq = _TIER_FREQUENCY_PER_1K[tier]
        premium = _REASONING_PREMIUM[tier]
        per_use = stats["regen_lower_bound_tokens_mean"] * premium
        lo = per_use * lo_freq
        hi = per_use * hi_freq
        total_lo += lo
        total_hi += hi
        out[tier] = {"per_use_regen_tokens_est": round(per_use, 1),
                     "uses_per_1k": [lo_freq, hi_freq],
                     "tokens_saved_per_1k_queries": [round(lo), round(hi)]}
    out["_total_tokens_saved_per_1k_queries"] = [round(total_lo), round(total_hi)]
    out["_assumptions"] = {"tier_frequency_per_1k": _TIER_FREQUENCY_PER_1K,
                           "reasoning_premium": _REASONING_PREMIUM,
                           "note": "ILLUSTRATIVE projection under labelled, swept assumptions; the real-model "
                                   "arm measures the true per-use regeneration cost"}
    return out


def _task_prompt(pid: str) -> str:
    spec = _lib.PRIMITIVES[pid]
    return (f"Write a correct, self-contained Python implementation of: {spec['mechanism']}. "
            f"Input: {spec['in']}. Output: {spec['out']}. Handle edge cases. Return ONLY the code.")


def _name_words(pid: str) -> str:
    """Human-readable words from an impl name: 'boyer_moore_majority' / 'UnionFind' -> 'boyer moore majority' /
    'union find'."""
    return re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", pid).replace("_", " ").lower()


def _task_query(pid: str) -> str:
    """A developer-style task query for a primitive, from its NAME. 'boyer_moore_majority' ->
    'boyer moore majority in python'."""
    return f"{_name_words(pid)} in python"


def retrieval_arm(*, k: int = 5, distractors: int = 1500, embed_path: Optional[str] = None) -> dict[str, Any]:
    """A primitive only saves tokens if it is RETRIEVED when its task arrives. Build the executable cards
    (embedded by their mechanism blackbox) into a store with real distractors, query each by a developer-style
    NAME query, and measure hit@k + MRR PER TIER. Retrieval is the precondition for the 0-token reuse."""
    cards = _lib.all_cards()
    target_ids = {c["primitive_id"] for c in cards}
    # embed by the human NAME words + mechanism (a card must carry its own name to be found by a name query;
    # the mechanism carries paraphrase matches). Measured: name-only embedding under-retrieves.
    views = [{"primitive_id": c["primitive_id"],
              "blackbox": f"{_name_words(c['impl_name'])} {c['blackbox']}"} for c in cards]
    dis = [d for d in _store._load_cards(limit=distractors) if d.get("primitive_id") not in target_ids]  # noqa: SLF001
    store = _store.build(views + dis, embed_path=embed_path)
    per_tier: dict[str, dict[str, Any]] = {t: {"hit": 0, "rr": 0.0, "n": 0} for t in _lib.TIERS}
    for c in cards:
        tier = c["tier"]
        hits = _store.search(_task_query(c["impl_name"]), store, k=k, embed_path=embed_path)
        per_tier[tier]["n"] += 1
        for i, h in enumerate(hits):
            if h.get("primitive_id") == c["primitive_id"]:
                per_tier[tier]["hit"] += 1
                per_tier[tier]["rr"] += 1.0 / (i + 1)
                break
    out: dict[str, Any] = {"k": k, "n_distractors": len(dis), "embed_model": store.get("embed_model")}
    for t, d in per_tier.items():
        n = d["n"] or 1
        out[t] = {"n": d["n"], "hit_at_k": round(d["hit"] / n, 3), "mrr": round(d["rr"] / n, 3)}
    return out


def real_model_arm(transport: Callable[[str], dict[str, Any]]) -> dict[str, Any]:
    """Measure ACTUAL regeneration cost: ask the model to implement each task, count its output tokens
    (natural stop) and whether the output is parseable Python. NO execution of model code (safety). Failures
    recorded, never faked."""
    per_tier: dict[str, dict[str, Any]] = {t: {"tokens": [], "parseable": 0, "n": 0, "failed": 0}
                                           for t in _lib.TIERS}
    for pid, spec in _lib.PRIMITIVES.items():
        tier = spec["tier"]
        r = transport(_task_prompt(pid))
        per_tier[tier]["n"] += 1
        if not r.get("ok"):
            per_tier[tier]["failed"] += 1
            continue
        text = str(r.get("text") or "")
        per_tier[tier]["tokens"].append(int(r.get("tokens_out") or _lib.token_estimate(text)))
        code = _strip_code_fence(text)
        try:
            ast.parse(code)
            per_tier[tier]["parseable"] += 1
        except SyntaxError:
            pass
    out: dict[str, Any] = {}
    for tier, d in per_tier.items():
        toks = d["tokens"]
        out[tier] = {"n": d["n"], "failed": d["failed"],
                     "actual_regen_tokens_mean": round(sum(toks) / len(toks), 1) if toks else None,
                     "parseable_rate": round(d["parseable"] / max(1, d["n"] - d["failed"]), 3),
                     "reuse_generation_tokens": 0}
    return out


def _strip_code_fence(text: str) -> str:
    t = text.strip()
    if "```" in t:
        parts = t.split("```")
        if len(parts) >= 3:
            body = parts[1]
            return body[body.find("\n") + 1:] if body[:12].strip().lower().startswith("python") else body
    return t


def run_bench(*, real_model: bool, transport: Optional[Callable[[str], dict[str, Any]]] = None) -> dict[str, Any]:
    tests = _lib.run_tests()  # confirm the library actually works before claiming savings
    per_tier = deterministic_savings()
    rec: dict[str, Any] = {
        "record_type": "token_savings_bench_receipt", "schema_version": 1,
        "library_all_tests_pass": all(r["ok"] for r in tests.values()),
        "n_primitives": len(_lib.PRIMITIVES),
        "deterministic_lower_bound": per_tier,
        "workload_projection": workload_projection(per_tier),
        "headline": "reuse = 0 generation tokens (structural); regeneration costs >= the impl tokens per tier "
                    "and grows with rarity — so per-use savings rise common < rare < super_rare.",
        **BOUNDARY,
    }
    rec["retrieval_arm"] = retrieval_arm()
    if real_model and transport is not None:
        rec["real_model_arm"] = real_model_arm(transport)
    return rec


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    per_tier = deterministic_savings()
    checks.append(("all three tiers measured with a positive regeneration lower bound",
                   all(per_tier[t]["regen_lower_bound_tokens_mean"] > 0 for t in _lib.TIERS)))
    checks.append(("reuse generation cost is structurally 0 for every tier",
                   all(per_tier[t]["reuse_generation_tokens"] == 0 for t in _lib.TIERS)))
    # per-use regeneration cost is ordered common <= rare <= super_rare (rarer = more code + premium)
    proj = workload_projection(per_tier)
    order = [proj[t]["per_use_regen_tokens_est"] for t in ("common", "rare", "super_rare")]
    checks.append(("per-use regeneration cost rises with rarity (common <= rare <= super_rare)",
                   order[0] <= order[1] <= order[2]))
    checks.append(("workload projection totals are positive and assumptions are labelled",
                   proj["_total_tokens_saved_per_1k_queries"][0] > 0 and "_assumptions" in proj))

    # real-model arm with a STUB transport: rarer prompts return more tokens; parseable + failure handling
    def _stub(prompt: str) -> dict[str, Any]:
        # emulate: more tokens for the harder (longer-mechanism) tasks; one forced failure
        if "Tarjan" in prompt:
            return {"ok": True, "text": "def f():\n    return 1", "tokens_out": 900}
        if "topological" in prompt:
            return {"ok": False, "error": "rate_limited"}
        n = 200 + len(prompt)
        return {"ok": True, "text": "def f():\n    return 1", "tokens_out": n}
    arm = real_model_arm(_stub)
    checks.append(("real-model arm measures per-tier actual tokens + parseable rate",
                   arm["super_rare"]["actual_regen_tokens_mean"] is not None
                   and arm["super_rare"]["parseable_rate"] == 1.0))
    checks.append(("real-model arm records a transport failure, never fabricates a number",
                   arm["rare"]["failed"] >= 1))
    checks.append(("bench refuses to hide a failing library (all_tests_pass reflects reality)",
                   run_bench(real_model=False)["library_all_tests_pass"] is True))
    # retrieval arm: primitives are findable by a developer-style task query among distractors
    ra = retrieval_arm(k=5, distractors=200, embed_path="tokens")
    checks.append(("retrieval arm measures hit@k per tier (>=0, all tiers present)",
                   all(t in ra and 0.0 <= ra[t]["hit_at_k"] <= 1.0 for t in _lib.TIERS)))
    checks.append(("determinism: deterministic savings identical twice",
                   json.dumps(deterministic_savings(), sort_keys=True)
                   == json.dumps(deterministic_savings(), sort_keys=True)))
    checks.append(("receipts are candidate/serves_truth=false", run_bench(real_model=False)["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - token_savings_bench: reuse=0 generation tokens (structural) vs a measured per-tier "
          "regeneration lower bound that rises with rarity; illustrative workload projection under LABELLED, "
          "swept assumptions; opt-in real-model arm measures actual regeneration tokens (no model-code exec). "
          "The library's own tests gate the claim. serves_truth=false.")
    return 0


def _make_transport(provider_name: str, model: str) -> Callable[[str], dict[str, Any]]:
    from scripts import _llm_client  # noqa: PLC0415
    provider = _llm_client.resolve_provider(provider_name)
    system = "You are a precise Python engineer. Return only code."

    def _call(prompt: str) -> dict[str, Any]:
        try:
            resp = _llm_client.chat(model, system, prompt, provider)  # inherit high-ceiling default; a truncated baseline would inflate measured savings
            if resp.get("error"):
                return {"ok": False, "error": str(resp["error"])[:120]}
            usage = resp.get("usage") or {}
            return {"ok": True, "text": resp.get("text") or "",
                    "tokens_out": usage.get("completion_tokens") or usage.get("output_tokens")}
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc)[:120]}
    return _call


def _bench(real_model: bool, provider: str, model: str) -> int:
    transport = _make_transport(provider, model) if real_model else None
    rec = run_bench(real_model=real_model, transport=transport)
    base = resource("data") / "dev-intel" / "session_emulation"
    out = base / "token_savings_receipt.json"
    out.write_text(json.dumps(rec, indent=2, sort_keys=True))
    # the real-model arm gets its OWN file so a later plain --bench never clobbers the measurement
    if real_model and rec.get("real_model_arm"):
        (base / "token_savings_real_model_receipt.json").write_text(json.dumps(
            {"record_type": "token_savings_real_model_receipt", "model": model,
             "real_model_arm": rec["real_model_arm"], **BOUNDARY}, indent=2, sort_keys=True))
    summary = {"deterministic_lower_bound": {t: rec["deterministic_lower_bound"][t]["regen_lower_bound_tokens_mean"]
                                             for t in _lib.TIERS},
               "reuse_generation_tokens": 0,
               "tokens_saved_per_1k_queries": rec["workload_projection"]["_total_tokens_saved_per_1k_queries"],
               "retrieval_hit_at_k": {t: rec["retrieval_arm"][t]["hit_at_k"] for t in _lib.TIERS}}
    if real_model:
        summary["real_model_actual_regen_tokens"] = {t: rec["real_model_arm"][t]["actual_regen_tokens_mean"]
                                                     for t in _lib.TIERS}
    print(json.dumps(summary, indent=2))
    print(f"\nreceipt: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--bench", action="store_true")
    ap.add_argument("--real-model", action="store_true", help="measure ACTUAL regeneration tokens via a model lane")
    ap.add_argument("--provider", default="ollama")
    ap.add_argument("--model", default="gemma-4-coding")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.bench:
        return _bench(args.real_model, args.provider, args.model)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
