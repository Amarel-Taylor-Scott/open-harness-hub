#!/usr/bin/env python3
"""scripts.check_local_environment_provider — PROOF (P2): the local-first Environment + Reward provider is real,
offline, deterministic, and governed.

The local provider is the CORRECTNESS INVARIANT + the fallback whenever an external (Repo2RLEnv/Harbor/
OpenEnv-style, docker/network) environment is unavailable. It MEASURES an agent output; it never makes that
output truth.

Asserts:
  A. PORT CONTRACTS: LocalEnvironmentProvider satisfies EnvironmentProviderPort (provider_id + describe/run/
     status); RewardRunner satisfies RewardProviderPort (provider_id + deterministic + score). describe() cards
     match the EnvironmentProviderNode / RewardProviderNode shapes (serves_truth False; local-first, no docker/net).
  B. OFFLINE + DETERMINISTIC: the local provider runs with NO docker/network/secrets; the SAME (request, output,
     now) yields IDENTICAL ids (result/receipt) and a DIFFERENT now yields a different receipt id.
  C. OUTPUT != TRUTH: EnvironmentRunResult.serves_truth is False and the receipt attests the output by HASH
     (input_hash + output_hash + timestamps + policy_checks present), never as a served fact.
  D. REWARD IS DETERMINISTIC + CORRECT: the RewardRunner scores a deterministic_check spec correctly — a correct
     answer (authoritative value present, held-out absent, key present) PASSES; a wrong / held-out-leaking answer
     FAILS; RewardResult.is_truth is False; the score is reproducible for the same (run_result, spec, now).
  E. NO BALTOR IMPORT / NO RAW KEYS: the teleon environment/port modules do not import src.baltor and contain no
     raw API key literals.

Deterministic + offline. stdlib only. Exit 0/1. _REPO = parents[1]; sys.path.insert. No raw keys/secrets.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.environments.local_environment_provider import (  # noqa: E402
    LOCAL_ENVIRONMENT_PROVIDER_ID,
    LocalEnvironmentProvider,
)
from src.teleon.environments.reward_runner import RewardRunner  # noqa: E402
from src.teleon.ports.environment_provider import (  # noqa: E402
    ENVIRONMENT_SERVES_TRUTH,
    EnvironmentProviderPort,
    EnvironmentUnavailableResult,
)
from src.teleon.ports.reward_provider import REWARD_IS_TRUTH, RewardProviderPort  # noqa: E402

_NOW = "2026-01-01T00:00:00Z"
_NOW_2 = "2026-02-02T12:00:00Z"

# teleon modules that must NOT import src.baltor and must carry no raw keys.
_TELEON_FILES = [
    _REPO / "src" / "teleon" / "ports" / "environment_provider.py",
    _REPO / "src" / "teleon" / "ports" / "reward_provider.py",
    _REPO / "src" / "teleon" / "environments" / "reward_runner.py",
    _REPO / "src" / "teleon" / "environments" / "local_environment_provider.py",
    _REPO / "src" / "teleon" / "environments" / "baltor_cfpb_context_governance.py",
]

# crude raw-key detectors (provider key prefixes); env:// refs / the word in prose are fine.
_KEY_PATTERNS = [re.compile(p) for p in (r"sk-[A-Za-z0-9]{16,}", r"AKIA[0-9A-Z]{12,}", r"AIza[0-9A-Za-z_\-]{20,}")]


def _sample_request(run_id: str = "run-local-0001") -> dict:
    return {
        "schema_version": "v1",
        "run_id": run_id,
        "environment_id": LOCAL_ENVIRONMENT_PROVIDER_ID,
        "agent_id": "agent.under-test",
        "tenant_id": "tenant-demo",
        "input_ref": None,
        "input": {"question": "what is 2 + 2?"},
        "max_steps": 4,
        "timeout_ms": 30000,
        "reward_spec_id": "reward.local.demo@v1",
        "require_receipt": True,
    }


def _det_spec() -> dict:
    """A deterministic_check spec: authoritative substring present, held-out absent, source handle present."""
    return {
        "reward_spec_id": "reward.local.demo@v1",
        "kind": "deterministic_check",
        "checks": [
            {"check_id": "value_present", "type": "substring_present", "needle": "four", "weight": 1.0},
            {"check_id": "held_out_absent", "type": "held_out_absent", "needle": "five", "weight": 1.0},
            {"check_id": "handle_present", "type": "key_present", "key": "source_handles", "weight": 1.0},
        ],
        "max_score": 3.0,
        "requires_execution": False,
    }


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    env = LocalEnvironmentProvider()
    rew = RewardRunner()

    # ---- A. port contracts -------------------------------------------------------------
    check("A: LocalEnvironmentProvider satisfies EnvironmentProviderPort (Protocol)",
          isinstance(env, EnvironmentProviderPort))
    check("A: RewardRunner satisfies RewardProviderPort (Protocol)", isinstance(rew, RewardProviderPort))
    check("A: provider exposes provider_id + describe/run/status",
          bool(env.provider_id) and callable(env.describe) and callable(env.run) and callable(env.status))
    check("A: scorer exposes provider_id + deterministic flag + score",
          bool(rew.provider_id) and rew.deterministic is True and callable(rew.score))

    env_card = env.describe()
    for key in ("provider_id", "name", "status", "requires_docker", "requires_network", "local_equivalent", "serves_truth"):
        check(f"A: env describe() card has EnvironmentProviderNode key {key!r}", key in env_card)
    check("A: env card is local-first (no docker, no network)",
          env_card.get("requires_docker") is False and env_card.get("requires_network") is False)
    check("A: env card local_equivalent is itself (the offline fallback)",
          env_card.get("local_equivalent") == LOCAL_ENVIRONMENT_PROVIDER_ID)
    rew_card = rew.describe()
    for key in ("provider_id", "name", "status", "deterministic", "serves_truth"):
        check(f"A: reward describe() card has RewardProviderNode key {key!r}", key in rew_card)

    # ---- B. offline + deterministic ----------------------------------------------------
    req = _sample_request()
    run_a = env.run(req, now=_NOW)
    run_b = env.run(req, now=_NOW)
    res_a, rcpt_a = run_a["result"], run_a["receipt"]
    res_b, rcpt_b = run_b["result"], run_b["receipt"]
    check("B: same (request, now) -> identical receipt_id (deterministic)",
          rcpt_a["receipt_id"] == rcpt_b["receipt_id"], f"{rcpt_a['receipt_id']} vs {rcpt_b['receipt_id']}")
    check("B: same (request, now) -> identical result receipt_id + output_hash",
          res_a["receipt_id"] == res_b["receipt_id"] and rcpt_a["output_hash"] == rcpt_b["output_hash"])
    run_c = env.run(req, now=_NOW_2)
    check("B: different now -> different receipt_id (now is injected, not wall-clock)",
          run_c["receipt"]["receipt_id"] != rcpt_a["receipt_id"])
    check("B: policy_checks assert network_denied + secrets_denied (offline, no secrets)",
          rcpt_a["policy_checks"].get("network_denied") is True
          and rcpt_a["policy_checks"].get("secrets_denied") is True)
    check("B: steps bounded (<= request.max_steps and <= hard ceiling)",
          0 < res_a["steps_taken"] <= req["max_steps"])
    # unavailable degradation path returns (not raises) an EnvironmentUnavailableResult, serves_truth False.
    unavail = env.unavailable(req, reason="candidate needs docker (not available locally)")
    check("B: unavailable() returns EnvironmentUnavailableResult (graceful, consumable=False)",
          isinstance(unavail, EnvironmentUnavailableResult) and unavail.consumable is False)
    check("B: unavailable projection is status=unavailable + serves_truth False",
          unavail.as_run_result()["status"] == "unavailable"
          and unavail.as_run_result()["serves_truth"] is False)

    # ---- C. output != truth + receipt provenance ---------------------------------------
    check("C: EnvironmentRunResult.serves_truth is False (output measured, never served)",
          res_a["serves_truth"] is False and ENVIRONMENT_SERVES_TRUTH is False)
    for key in ("input_hash", "output_hash", "started_at", "completed_at", "policy_checks", "receipt_id"):
        check(f"C: receipt has {key!r}", key in rcpt_a and rcpt_a[key] not in (None, ""))
    check("C: receipt hashes are sha256-prefixed content hashes (tamper-evident, not raw output)",
          str(rcpt_a["input_hash"]).startswith("sha256:") and str(rcpt_a["output_hash"]).startswith("sha256:"))
    check("C: receipt timestamps come from injected now", rcpt_a["started_at"] == _NOW and rcpt_a["completed_at"] == _NOW)

    # ---- D. reward deterministic + correct ---------------------------------------------
    spec = _det_spec()
    good = {"run_id": "run-good", "output": {"answer": "the answer is four", "source_handles": ["ctx://x#y"]}}
    bad_wrong = {"run_id": "run-bad", "output": {"answer": "the answer is six", "source_handles": ["ctx://x#y"]}}
    bad_leak = {"run_id": "run-leak", "output": {"answer": "four, or maybe five", "source_handles": ["ctx://x#y"]}}
    bad_nohandle = {"run_id": "run-nh", "output": {"answer": "four", "source_handles": []}}

    rr_good = rew.score(good, spec, now=_NOW)
    rr_good_2 = rew.score(good, spec, now=_NOW)
    rr_wrong = rew.score(bad_wrong, spec, now=_NOW)
    rr_leak = rew.score(bad_leak, spec, now=_NOW)
    rr_nh = rew.score(bad_nohandle, spec, now=_NOW)

    check("D: correct answer PASSES (score == max_score, passed True)",
          rr_good["passed"] is True and abs(rr_good["score"] - rr_good["max_score"]) < 1e-9)
    check("D: reward is deterministic (same inputs -> identical reward_result_id + score)",
          rr_good["reward_result_id"] == rr_good_2["reward_result_id"] and rr_good["score"] == rr_good_2["score"])
    check("D: WRONG answer FAILS (missing authoritative substring)", rr_wrong["passed"] is False)
    check("D: HELD-OUT-LEAKING answer FAILS (held_out_absent check bites)", rr_leak["passed"] is False)
    leak_bd = next((b for b in rr_leak["breakdown"] if b["check_id"] == "held_out_absent"), {})
    check("D: the failing check on a leak is specifically held_out_absent", leak_bd.get("passed") is False)
    check("D: missing source-handle FAILS the key_present check", rr_nh["passed"] is False)
    check("D: RewardResult.is_truth is False (evidence, not authority)",
          rr_good["is_truth"] is False and REWARD_IS_TRUTH is False)
    check("D: breakdown preserves per-check lineage (a winner has lineage to each check)",
          len(rr_good["breakdown"]) == len(spec["checks"]))
    # an unsupported kind fails closed (test_execution needs an execution-capable provider).
    rr_unsupported = rew.score(good, {**spec, "kind": "test_execution"}, now=_NOW)
    check("D: unsupported RewardSpec.kind fails closed (passed False, is_truth False)",
          rr_unsupported["passed"] is False and rr_unsupported["is_truth"] is False)

    # ---- E. no baltor import / no raw keys ---------------------------------------------
    # Match a real IMPORT STATEMENT (line-start, optional indent) — NOT prose that names the rule
    # ("does NOT import src.baltor" in a docstring is the invariant being documented, not a violation).
    baltor_import = re.compile(r"^[ \t]*(?:import|from)[ \t]+src\.baltor\b", re.MULTILINE)
    for f in _TELEON_FILES:
        text = f.read_text()
        check(f"E: {f.name} does not import src.baltor", not baltor_import.search(text))
        leaked = [p.pattern for p in _KEY_PATTERNS if p.search(text)]
        check(f"E: {f.name} contains no raw API key literal", not leaked, f"matched {leaked}")

    print("\n" + ("PASS — check_local_environment_provider: the local-first environment runs OFFLINE + "
                  "DETERMINISTICALLY (no docker/network/secrets; injected now -> stable content-addressed ids), "
                  "EnvironmentRunResult.serves_truth is False with a hash-based provenance receipt, and the "
                  "RewardRunner scores a deterministic_check spec correctly (correct passes; wrong / held-out-"
                  "leaking / no-handle fail) with is_truth False. No src.baltor import; no raw keys."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_local_environment_provider.py --self-test")
    raise SystemExit(0)
